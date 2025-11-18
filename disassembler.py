from .constants import FETCH_PACKET_SIZE, WORD_SIZE, C64XP, \
        EXECUTION_PACKET_LIMIT, HEADER_MASK, HEADER_KEY, \
        HEADER_FIELD_MASK, HEADER_LAYOUT_OFFSET, HEADER_EXPANSION_OFFSET, \
        TIC6X_FLAG_MACRO, TIC6X_FLAG_SIDE_B_ONLY, TIC6X_FLAG_SIDE_T2_ONLY
from ._operands import OPERANDS, OperandForm, RW
from .types import Endianness, ISA, Register, ControlRegister, AddressingMode, \
        ConditionType, Operand, OperandType, Instruction, \
        ImmediateOperand, RegisterOperand, RegisterPairOperand, \
        ControlRegisterOperand, MemoryOperand

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Sequence
from pathlib import Path
import json
from types import SimpleNamespace as Namespace
from collections import namedtuple

@dataclass
class _Field:
    id:str
    pos:int
    width:int

@dataclass
class _InstructionFormat:
    name:str
    bit_width:int
    key:int
    mask:int
    fields:List[_Field]

@dataclass
class _FixedField:
    id:str
    min:int
    max:int

@dataclass
class _VarField:
    id:str
    method:str
    op:int

@dataclass
class _Variable:
    id:str
    method:str
    op:int
    value:int

@dataclass
class _Opcode:
    name:str
    unit:str
    format:str
    type:str
    isa:int
    flags:int
    fixed:List[_FixedField]
    ops:List[str]
    vars:List[_VarField]

@dataclass
class _UnitInfo:
    side:int
    data_side:int
    cross:bool

@dataclass
class _Expansion:
    protected:bool
    register_set:bool
    data_size:int
    branching:bool
    saturating:bool

_SizeField = namedtuple('SizeField', ('value', 'size'))


def _format_decoder(obj:dict):
    if {'name', 'bit_width', 'key', 'mask', 'fields'}.issubset(obj.keys()):
        return _InstructionFormat(obj['name'], int(obj['bit_width']),
                int(obj['key'], 0), int(obj['mask'], 0), obj['fields'])
    elif {'name', 'pos', 'width'}.issubset(obj.keys()):
        return _Field(obj['name'], obj['pos'], obj['width'])


class Disassembler:
    def __init__(self, endian:Endianness=Endianness.LITTLE, 
            isa:ISA = ISA.C67XP) -> None:
        self.endianness = endian
        self.isa = isa
        # c64x+ compact encoding
        self.fetch_packet_header_based = bool(isa & C64XP) 

        basepath = Path(__file__).resolve().parent
        with open(basepath / 'instruction_formats.json') as file:
            self.instruction_formats:List[_InstructionFormat] = json.load(
                file, object_hook=_format_decoder)
            self.instruction_formats.sort(
                key=lambda f: -f.mask.bit_count())
            self.instruction_maps:Dict[str, List[_Opcode]] = {
                f.name: list()
                for f in self.instruction_formats}
        with open(basepath / 'opcodes.json') as file:
            opcodes:List[_Opcode] = json.load(
                file, object_hook=lambda obj: Namespace(**obj))
            for opcode in opcodes:
                if opcode.flags & TIC6X_FLAG_MACRO:
                    continue # ignore assembly macros
                if not opcode.isa & self.isa:
                    continue # ignore unsupported ISA
                format = opcode.unit+'_'+opcode.format
                if format in self.instruction_maps:
                    self.instruction_maps[format].append(opcode)

    def disasm(self, data:bytes, address:int, count:int=-1):
        if self.fetch_packet_header_based:
            self.__disasm_headerless(data, address, count)
        else:
            self.__disasm_headerless(data, address, count)

    def __disasm_header_based(self, data:bytes, address:int, count:int=-1):
        remaining = data
        current_address = address
        while len(remaining) >= FETCH_PACKET_SIZE and count != 0:
            fetch_packet = remaining[:FETCH_PACKET_SIZE]
            remaining = remaining[FETCH_PACKET_SIZE:]
            
            header = int.from_bytes(fetch_packet[-WORD_SIZE:], 
                    self.endianness) # type: ignore
            has_header = (header & HEADER_MASK) == HEADER_KEY
            if has_header:
                layout = (header >> HEADER_LAYOUT_OFFSET) & HEADER_FIELD_MASK
                expansion = self.__decode_expansion(
                        (header >> HEADER_EXPANSION_OFFSET) & HEADER_FIELD_MASK)
                offset = 0
                for _ in range(7):
                    encoded = int.from_bytes(
                            fetch_packet[offset:offset+WORD_SIZE], 
                            self.endianness) # type: ignore
                    compact = layout & 1
                    if compact:
                        # yield self.__decode_compact(
                        #     encoded & 0xFFFF,
                        #     expansion,
                        #     bool(header & 1),
                        #     current_address+offset
                        # )
                        count -= 1
                        if count == 0: break
                        # yield self.__decode_compact(
                        #     encoded > 16,
                        #     expansion,
                        #     bool(header & 2),
                        #     current_address+offset+2
                        # )
                    else:
                        yield self.__decode(encoded, current_address+offset)

                    count -= 1
                    if count == 0: break
                    layout >>= 1
                    header >>= 2
                    offset += WORD_SIZE
            else:
                for instr in self.__disasm_headerless(fetch_packet, current_address, count):
                    yield instr
                if count < EXECUTION_PACKET_LIMIT: break
                count -= EXECUTION_PACKET_LIMIT
            current_address += FETCH_PACKET_SIZE
        # stop due to missing header or exhausted count

    def __disasm_headerless(self, data:bytes, address:int, count:int=-1):
        remaining = data
        current_address = address
        if self.endianness == Endianness.LITTLE:
            byteorder = 'little'
        else:
            byteorder = 'big'
        while len(remaining) >= WORD_SIZE and count != 0:
            current_data = remaining[:WORD_SIZE]
            remaining = remaining[WORD_SIZE:]
            current_address += WORD_SIZE
            
            encoded = int.from_bytes(current_data, byteorder)
            instr = self.__decode(encoded, address)
            if instr:
                yield instr
            else:
                break
            count -= 1

    def __decode(self, encoded:int, address:int) -> Optional[Instruction]:
        instr = None
        for format in self.instruction_formats:
            if format.bit_width != 32: continue
            if encoded & format.mask == format.key:
                # print('unit', format.name)
                fields = {
                    field.id: self.__decode_field(field, encoded)
                    for field in format.fields
                }

                for opcode in self.instruction_maps[format.name]:
                    if not all({ self.__matches_fixed(fields, fixed)
                            for fixed in opcode.fixed}):
                        continue
                    # print(opcode.name, opcode)
                    vars = {
                        var.id: self.__decode_var_field(var, fields)
                        for var in opcode.vars
                    }

                    parallel = self.__decode_parallel(fields)
                    condition = self.__decode_condition(fields)
                    cross_path = self.__decode_cross_path(fields)
                    unit, unit_info = self.__decode_unit(
                        opcode.unit,
                        opcode.flags,
                        cross_path,
                        vars)
                    operands = self.__decode_operands(opcode.ops, unit_info, 
                            vars, address)
                    instr = Instruction(
                        address, condition, unit, cross_path,
                        operands, opcode.name, parallel)

        if instr: return instr
    
    def __decode_expansion(self, encoded:int) -> _Expansion:
        return _Expansion(
            bool(encoded & 0x40),
            bool(encoded & 0x20),
            (encoded >> 2) & 0x7,
            bool(encoded & 2),
            bool(encoded & 1)
        )

    def __decode_field(self, field:_Field, encoded:int) -> _SizeField:
        mask = (1<<field.width) - 1
        return _SizeField((encoded>>field.pos) & mask, field.width)
    
    def __decode_var_field(self, var:_VarField, 
            fields:Dict[str, _SizeField]) -> _Variable:
        assert var.id in fields
        value = fields[var.id].value
        match var.method:
            case 'cst_s3i': 
                if value == 0: value = 0x10
                if value == 7: value = 0x08
            case 'scst_l3i':
                if value == 0: value = 8
                else: value = self.__decode_signed(fields[var.id])
            case 'scst':
                value = self.__decode_signed(fields[var.id])
            case 'pcrel'|'pcrel_half':
                value = self.__decode_signed(fields[var.id])
                if self.fetch_packet_header_based and var.method == 'pcrel_half':
                    value *= 2
                else:
                    value *= 4
            case 'pcrel_half_unsigned':
                value *= 2
            case 'ucst_minus_one':
                value += 1
            case 'reg_shift':
                value <<= 1
        return _Variable(var.id, var.method, var.op, value)
    
    def __decode_signed(self, field:_SizeField) -> int:
        mask = 1 << (field.size - 1)
        return (field.value ^ mask) - mask
    
    def __matches_fixed(self, fields:Dict[str, _SizeField], 
            fixed:_FixedField) -> bool:
        if fixed.id not in fields: 
            raise ValueError()
        return fixed.min <= fields[fixed.id].value <= fixed.max
    
    def __decode_parallel(self, fields:Dict[str, _SizeField]) -> bool:
        return 'p' in fields and bool(fields['p'].value)
    
    def __decode_condition(self, 
            fields:Dict[str, _SizeField]) -> ConditionType:
        condition_value = (
            fields['creg'].value<<1 if 'creg' in fields else 0
        ) | (
            fields['z'].value if 'z' in fields else 0
        )
        return ConditionType(condition_value)
    
    def __decode_cross_path(self, fields:Dict[str, _SizeField]) -> bool:
        return 'x' in fields and bool(fields['x'].value)

    def __decode_unit(self, unit:str, flags:int, cross_path:bool, 
            vars:Dict[str, _Variable]) -> Tuple[str,_UnitInfo]:
        if unit == 'nfu': return '', _UnitInfo(0,0,False)
        func_unit_side = 2 if flags & TIC6X_FLAG_SIDE_B_ONLY else 0
        func_unit_data_side = 2 if flags & TIC6X_FLAG_SIDE_T2_ONLY else 0
        func_unit_cross = cross_path
        have_areg = False

        for var in vars.values():
            match var.method:
                case 'fu':
                    func_unit_side = 2 if var.value else 1
                case 'data_fu':
                    func_unit_data_side = 2 if var.value else 1
                case 'rside':
                    func_unit_data_side = 2 if var.value else 1
                case 'areg':
                    have_areg = True

        if have_areg and not func_unit_data_side:
            func_unit_cross = func_unit_side == 1 

        match func_unit_data_side:
            case 0: data_str = ''
            case 1: data_str = 'T1'
            case 2: data_str = 'T2'

        return '.{}{:d}{}{}'.format(unit.upper(), func_unit_side, 
                data_str, 'X' if func_unit_cross else ''), \
                _UnitInfo(func_unit_side, func_unit_data_side, func_unit_cross)
    
    def __decode_operands(self, ops:List[str], unit_info:_UnitInfo,
            vars:Dict[str, _Variable], address:int) -> List[Operand]:
        assert all([var.value is not None for var in vars.values()])
        operands = list()
        for i, op in enumerate(ops):
            operand_info = OPERANDS[op]
            current_operand = None
            match operand_info.form:
                # operand constant or fully determined by functional unit
                case OperandForm.b15reg:
                    current_operand = RegisterOperand(Register.B15)
                case OperandForm.zreg:
                    current_operand = RegisterOperand(
                            Register.B0 if unit_info.side == 2 else Register.A0)
                case OperandForm.retreg:
                    current_operand = RegisterOperand(
                            Register.B3 if unit_info.side == 2 else Register.A3)
                case OperandForm.irp:
                    current_operand = ControlRegisterOperand(ControlRegister.IRP)
                case OperandForm.nrp:
                    current_operand = ControlRegisterOperand(ControlRegister.NRP)
                case OperandForm.ilc:
                    current_operand = ControlRegisterOperand(ControlRegister.ILC)
                case OperandForm.hw_const_minus_1:
                    current_operand = ImmediateOperand(-1)
                case OperandForm.hw_const_0:
                    current_operand = ImmediateOperand(0)
                case OperandForm.hw_const_1:
                    current_operand = ImmediateOperand(1)
                case OperandForm.hw_const_5:
                    current_operand = ImmediateOperand(5)
                case OperandForm.hw_const_16:
                    current_operand = ImmediateOperand(16)
                case OperandForm.hw_const_24:
                    current_operand = ImmediateOperand(24)
                case OperandForm.hw_const_31:
                    current_operand = ImmediateOperand(31)

                # operands requiring information encoded in variable fields
                case OperandForm.asm_const:
                    if (var := self.__get_operand_var(vars, i, ('cst_s3i', 'ucst', 
                            'ucst_minus_one', 'scst', 'scst_l3i'))):
                        current_operand = ImmediateOperand(var.value)
                    # fstg and fcyc not handled yet
                case OperandForm.link_const:
                    if (var := self.__get_operand_var(vars, i, ('ulcst_dpr_byte', 'ucst', 
                            'lcst_high16', 'lcst_low16', 'scst'))):
                        current_operand = ImmediateOperand(var.value)
                    elif (var := self.__get_operand_var(vars, i, 
                            ('pcrel', 'pcrel_half', 'pcrel_half_unsigned'))):
                        current_operand = ImmediateOperand(address + var.value)
                # c64x 16-bit encoding, header and types are not supported yet (relevant for reg and regpair)
                case OperandForm.reg|OperandForm.reg_bside|OperandForm.xreg:
                    if (var := self.__get_operand_var(vars, i, ('reg', 'reg_shift'))):
                        if (
                            unit_info.side == 2 
                            or operand_info.form == OperandForm.reg_bside
                        ):
                            reg_base = Register.B0.value
                        else: 
                            reg_base = Register.A0.value
                        if (
                            operand_info.form == OperandForm.xreg
                            and unit_info.cross
                        ):
                            reg_base ^= Register.B0.value
                        current_operand = RegisterOperand(Register(reg_base + var.value))
                case OperandForm.dreg:
                    if (var := self.__get_operand_var(vars, i, ('reg', 'reg_shift'))):
                        if unit_info.data_side == 2:
                            reg_base = Register.B0.value
                        else: 
                            reg_base = Register.A0.value
                        current_operand = RegisterOperand(Register(reg_base + var.value))
                case OperandForm.regpair|OperandForm.xregpair:
                    if (var := self.__get_operand_var(vars, i, ('reg', 'reg_shift'))):
                        assert var.value&1 == 0
                        if (
                            unit_info.side == 2 
                            or operand_info.form == OperandForm.reg_bside
                        ):
                            reg_base = Register.B0.value
                        else: 
                            reg_base = Register.A0.value
                        if (
                            operand_info.form == OperandForm.xreg
                            and unit_info.cross
                        ):
                            reg_base ^= Register.B0.value
                        reg_high = Register(reg_base + var.value + 1)
                        reg_low = Register(reg_base + var.value)
                        current_operand = RegisterPairOperand(reg_high, reg_low)
                    elif (var := self.__get_operand_var(vars, i, ('regpair_msb'))):
                        if unit_info.side == 2:
                            reg_base = Register.B0.value 
                        else: 
                            reg_base = Register.A0.value
                        reg_high = Register(reg_base + var.value | 0x1)
                        reg_low = Register(reg_base + var.value | 0x1 - 1)
                        current_operand = RegisterPairOperand(reg_high, reg_low)
                case OperandForm.dregpair:
                    if (var := self.__get_operand_var(vars, i, ('reg', 'reg_shift'))):
                        assert var.value&1 == 0
                        if unit_info.data_side == 2:
                            reg_base = Register.B0.value
                        else: 
                            reg_base = Register.A0.value
                        reg_high = Register(reg_base + var.value + 1)
                        reg_low = Register(reg_base + var.value)
                        current_operand = RegisterPairOperand(reg_high, reg_low)
                case OperandForm.ctrl:
                    crhi = self.__get_operand_var(vars, i, ('crhi',))
                    crlo = self.__get_operand_var(vars, i, ('crlo',))
                    assert crlo is not None and crhi is not None
                    assert crhi.value == 0, 'control register extension not supported'
                    ctrl = ControlRegister(crlo.value)
                    if crlo == 2 and operand_info.rw == RW.write:
                        ctrl = ControlRegister.ISR
                    current_operand = ControlRegister(ctrl)
                case OperandForm.mem_short:
                    mode_var = self.__get_operand_var(vars, i, ('mem_mode',))
                    offset_var = self.__get_operand_var(vars, i, ('mem_offset',))
                    base_var = self.__get_operand_var(vars, i, ('reg',))
                    assert (mode_var is not None and offset_var is not None 
                            and base_var is not None)
                    if unit_info.side == 2:
                        side = Register.B0.value 
                    else:
                        side = Register.A0.value
                    base = Register(side+base_var.value)
                    mode = AddressingMode(mode_var.value & ~4)
                    if mode_var.value & 4:
                        offset = Register(side+offset_var.value)
                    else:
                        offset = offset_var.value * operand_info.size
                    current_operand = MemoryOperand(mode,base,offset)
                    
            if current_operand:
                operands.append(current_operand)
                continue
            # print('not implemented', operand_info.form)
        return operands
    
    def __get_operand_var(self, vars:Dict[str, _Variable], 
            op:int, methods:Sequence[str]) -> Optional[_Variable]:
        for var in vars.values():
            if var.op != op: continue
            if var.method in methods:
                return var
        return None
