from .constants import FETCH_PACKET_SIZE, WORD_SIZE, C64XP, \
        EXECUTION_PACKET_LIMIT, HEADER_MASK, HEADER_KEY, HEADER_PBITS_MASK, \
        HEADER_FIELD_MASK, HEADER_LAYOUT_OFFSET, HEADER_EXPANSION_OFFSET, \
        TIC6X_FLAG_MACRO, TIC6X_FLAG_SIDE_B_ONLY, TIC6X_FLAG_SIDE_T2_ONLY, \
        TIC6X_FLAG_INSN16_B15PTR, TIC6X_FLAG_INSN16_NORS, \
        TIC6X_FLAG_INSN16_BSIDE, TIC6X_FLAG_INSN16_SPRED, \
        TIC6X_FLAG_INSN16_MEM_MODE
from ._operands import OPERANDS, OperandForm, RW
from .types import Endianness, ISA, Register, ControlRegister, AddressingMode, \
        ConditionType, Operand, FuncUnit, DataSide, UnitInfo, Instruction, \
        ImmediateOperand, RegisterOperand, RegisterPairOperand, \
        ControlRegisterOperand, MemoryOperand, FuncUnitsOperand, Header

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
    offset:int

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

class _Context:
    sploop_ii:int = 0

_SizeField = namedtuple('SizeField', ('value', 'size'))


def _format_decoder(obj:dict):
    if {'name', 'bit_width', 'key', 'mask', 'fields'}.issubset(obj.keys()):
        return _InstructionFormat(obj['name'], int(obj['bit_width']),
                int(obj['key'], 0), int(obj['mask'], 0), obj['fields'])
    elif {'name', 'pos', 'width', 'offset'}.issubset(obj.keys()):
        return _Field(obj['name'], obj['pos'], obj['width'], obj['offset'])


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
        format_names = {format.name for format in self.instruction_formats}
        with open(basepath / 'opcodes.json') as file:
            opcodes:List[_Opcode] = json.load(
                file, object_hook=lambda obj: Namespace(**obj))
            for opcode in opcodes:
                if opcode.flags & TIC6X_FLAG_MACRO:
                    continue # ignore assembly macros
                if not opcode.isa & self.isa:
                    continue # ignore unsupported ISA
                format = opcode.format
                if format not in format_names:
                    format = opcode.unit+'_'+opcode.format
                    assert format in format_names
                if format in self.instruction_maps:
                    self.instruction_maps[format].append(opcode)

    def disasm(self, data:bytes, address:int, count:int=-1):
        if address % FETCH_PACKET_SIZE == 0x1e:
            raise ValueError('Invalid address for disassembly.')
        context = _Context()
        if self.fetch_packet_header_based:
            return self.__disasm_header_based(data, address, context, count)
        else:
            return self.__disasm_headerless(data, address, context, count)

    def __disasm_header_based(self, data:bytes, address:int, 
            context:_Context, count:int=-1):
        remaining = data
        current_address = address
        skipped = address % FETCH_PACKET_SIZE
        while len(remaining) >= FETCH_PACKET_SIZE and count != 0:
            packet_size = FETCH_PACKET_SIZE - skipped
            fetch_packet = remaining[:packet_size]
            remaining = remaining[packet_size:]
            
            header_enc = int.from_bytes(fetch_packet[-WORD_SIZE:], 
                    self.endianness) # type: ignore
            has_header = (header_enc & HEADER_MASK) == HEADER_KEY
            if has_header:
                layout = (header_enc >> HEADER_LAYOUT_OFFSET) & HEADER_FIELD_MASK
                header = self.__decode_header(layout, 
                        (header_enc >> HEADER_EXPANSION_OFFSET) & HEADER_FIELD_MASK,
                        header_enc & HEADER_PBITS_MASK)
                offset = 0
                header_enc >>= skipped//2
                if skipped & 2:
                    if not layout >> (skipped//WORD_SIZE):
                        raise ValueError('Address in the middle of instruction.')
                    if self.endianness == Endianness.BIG:
                        raise ValueError('Next instruction in logical order missing.')
                    encoded = int.from_bytes(fetch_packet[:2],
                            self.endianness) # type: ignore
                    yield self.__decode_compact(
                        encoded,
                        header,
                        bool(header_enc & 1),
                        current_address,
                        context
                    )
                    count -= 1
                    if count == 0: break
                    offset = 2
                    header_enc >>= 1
                layout >>= (skipped+2)//WORD_SIZE
                for _ in range((skipped+2)//WORD_SIZE, 7):
                    encoded = int.from_bytes(
                            fetch_packet[offset:offset+WORD_SIZE], 
                            self.endianness) # type: ignore
                    compact = layout & 1
                    if compact:
                        first = encoded & 0xFFFF
                        second = encoded >> 16
                        yield self.__decode_compact(
                            first,
                            header,
                            bool(header_enc & 1),
                            current_address+offset,
                            context
                        )
                        yield self.__decode_compact(
                            second,
                            header,
                            bool(header_enc & 2),
                            current_address+offset+2,
                            context
                        )
                    else:
                        instr = self.__decode(encoded,
                                current_address+offset, context)
                        instr.header = header
                        yield instr

                    count -= 1
                    if count == 0: break
                    layout >>= 1
                    header_enc >>= 2
                    offset += WORD_SIZE
                
                if count != 0:
                    yield Instruction.init_header(
                        current_address+offset,
                        header)
                    count -= 1
            else:
                for instr in self.__disasm_headerless(fetch_packet, current_address, context, count):
                    yield instr
                count -= EXECUTION_PACKET_LIMIT - (skipped//WORD_SIZE)
            current_address += packet_size
            skipped = 0
        # stop due to missing header or exhausted count

    def __disasm_headerless(self, data:bytes, address:int, 
            context:_Context, count:int=-1):
        remaining = data
        current_address = address
        if self.endianness == Endianness.LITTLE:
            byteorder = 'little'
        else:
            byteorder = 'big'
        while len(remaining) >= WORD_SIZE and count != 0:
            current_data = remaining[:WORD_SIZE]
            remaining = remaining[WORD_SIZE:]
            
            encoded = int.from_bytes(current_data, byteorder)
            instr = self.__decode(encoded, current_address, context)
            yield instr
            current_address += WORD_SIZE
            count -= 1

    def __decode_compact(self, encoded:int, header:Header,
            parallel:bool, address:int, context:_Context) -> Instruction:
        encoded_expanded = encoded
        encoded_expanded |= int(header.saturating) << 16
        encoded_expanded |= int(header.branching) << 17
        encoded_expanded |= int(header.data_size) << 18
        invalid = Instruction.invalid(address, 2, parallel, header)
        return self.__decode_core(encoded_expanded, address, 16, invalid, 
                context, parallel, header)

    def __decode(self, encoded:int, address:int, 
            context:_Context) -> Instruction:
        invalid = Instruction.invalid(address, WORD_SIZE, bool(encoded & 1), None)
        return self.__decode_core(encoded, address, 32, invalid, context)

    def __decode_core(self, encoded:int, address:int, width:int,
            invalid:Instruction, context:_Context, parallel:bool=False,
            header:Optional[Header]=None) -> Instruction:
        instr = invalid
        for format in self.instruction_formats:
            if format.bit_width != width: continue
            if encoded & format.mask == format.key:
                # print('unit', format.name)
                fields = dict()
                for field in format.fields:
                    if field.id in fields:
                        fields[field.id] = self.__compose_field(field, encoded,
                                fields[field.id])
                    else:
                        fields[field.id] = self.__decode_field(field, encoded)

                for opcode in self.instruction_maps[format.name]:
                    if not all({ self.__matches_fixed(fields, fixed)
                            for fixed in opcode.fixed}):
                        continue
                    # print(opcode.name, opcode)
                    vars = [
                        self.__decode_var_field(var, fields)
                        for var in opcode.vars
                    ]

                    parallel |= self.__decode_parallel(fields)
                    condition = self.__decode_condition(fields, opcode.flags)
                    if condition in (ConditionType.BREAKPOINT,
                            ConditionType.RESERVED): continue
                    cross_path = self.__decode_cross_path(fields)
                    unit_info = self.__decode_unit(
                        opcode.unit,
                        opcode.flags,
                        cross_path,
                        vars)
                    operands = self.__decode_operands(
                            opcode.ops, opcode.flags, unit_info, 
                            vars, address, header, context)
                    instr = Instruction(
                        address, width//8, condition, unit_info, operands, opcode.name, parallel, header)
                    if 'sploop' in opcode.name:
                        assert isinstance(operands[0], ImmediateOperand)
                        context.sploop_ii = operands[0].value
        return instr
    
    def __decode_header(self, layout:int, encoded:int, pbits:int) -> Header:
        return Header(
            layout,
            bool(encoded & 0x40),
            bool(encoded & 0x20),
            (encoded >> 2) & 0x7,
            bool(encoded & 2),
            bool(encoded & 1),
            pbits
        )

    def __decode_field(self, field:_Field, encoded:int) -> _SizeField:
        mask = (1<<field.width) - 1
        return _SizeField(((encoded>>field.pos) & mask) << field.offset, 
                field.width)
    
    def __compose_field(self, field:_Field, encoded:int, 
                part:_SizeField) -> _SizeField:
        new_part = self.__decode_field(field, encoded)
        return _SizeField(part.value|new_part.value, part.size+new_part.size)
    
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
            case 'mem_offset_minus_one'|'mem_offset_minus_one_noscale':
                value += 1
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
            fields:Dict[str, _SizeField], flags:int) -> ConditionType:
        if flags & TIC6X_FLAG_INSN16_SPRED:
            COMPACT_CONDITIONS = (
                ConditionType.A0, ConditionType.NOT_A0,
                ConditionType.B0, ConditionType.NOT_B0
            )
            if 'cc' in fields:
                condition_value = fields['cc'].value
            elif 's' in fields and 'z' in fields:
                condition_value = fields['s'].value << 1 | fields['z'].value
            else:
                assert False, 'invalid compact predicate encoding'
            return COMPACT_CONDITIONS[condition_value]
        condition_value = 0
        if 'creg' in fields:
            assert 'z' in fields
            condition_value = (fields['creg'].value<<1) | fields['z'].value
        return ConditionType(condition_value)
    
    def __decode_cross_path(self, fields:Dict[str, _SizeField]) -> bool:
        return 'x' in fields and bool(fields['x'].value)

    def __decode_unit(self, unit:str, flags:int, cross_path:bool, 
            vars:List[_Variable]) -> UnitInfo:
        if unit == 'nfu': return UnitInfo(FuncUnit.NFU, None, False)
        func_unit_side = 2 if flags & TIC6X_FLAG_SIDE_B_ONLY else 0
        func_unit_data_side = 2 if flags & TIC6X_FLAG_SIDE_T2_ONLY else 0
        func_unit_cross = cross_path
        have_areg = False

        for var in vars:
            match var.method:
                case 'fu':
                    func_unit_side = 2 if var.value else 1
                case 'data_fu':
                    func_unit_data_side = 2 if var.value else 1
                case 'rside':
                    func_unit_data_side = 2 if var.value else 1
                case 'areg':
                    have_areg = True

        assert func_unit_side in [2,1]
        assert not (func_unit_data_side and cross_path)
        assert not (func_unit_data_side and unit != 'd')

        if have_areg and not func_unit_data_side:
            assert not cross_path
            func_unit_cross = func_unit_side == 1 

        unit_bases = {
            'l': FuncUnit.L1.value, 
            's': FuncUnit.S1.value, 
            'd': FuncUnit.D1.value, 
            'm': FuncUnit.M1.value
        }
        unit_value = unit_bases[unit] + ((func_unit_side & 2) >> 1)
        func_unit = FuncUnit(unit_value)
        
        match func_unit_data_side:
            case 0: data_side = None
            case 1: data_side = DataSide.T1
            case 2: data_side = DataSide.T2

        if flags & TIC6X_FLAG_INSN16_BSIDE and func_unit_side == 1:
            func_unit_cross = True

        return UnitInfo(func_unit, data_side, func_unit_cross)
    
    def __decode_operands(self, ops:List[str], flags:int,
            unit_info:UnitInfo, vars:List[_Variable], address:int,
            header:Optional[Header], context:_Context) -> List[Operand]:
        assert all([var.value is not None for var in vars])
        high_registers = header is not None and header.high_register_set
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
                    if (var := self.__get_operand_var(vars, i, ('fstg', 'fcyc'))):
                        STGCYC_BITS_LOOKUP = (
                            (1, 1, 6, 0),
                            (2, 2, 5, 1),
                            (3, 4, 4, 2),
                            (5, 8, 3, 3),
                            (9, 14, 2, 4)
                        )
                        if not context.sploop_ii: 
                            # Skip second operand if sploop initiation interval (ii) unknown.
                            if var.method == 'fcyc': continue
                            current_operand = ImmediateOperand(var.value)
                        else:
                            for (ii_low, ii_high, 
                                    fstg_bits, fcyc_bits) in STGCYC_BITS_LOOKUP:
                                if ii_low <= context.sploop_ii <= ii_high: break
                            else:
                                assert False, f'Invalid initiation interval.'
                            if var.method == 'fstg':
                                fstg_value = 0
                                for fstg_bit in reversed(range(fstg_bits)):
                                    fstg_value <<= 1
                                    fstg_value |= (var.value>>(5-fstg_bit)) & 1
                                current_operand = ImmediateOperand(fstg_value)
                            else:
                                fcyc_mask = (1 << fcyc_bits) - 1
                                current_operand = ImmediateOperand(
                                        var.value & fcyc_mask)
                        # Fields fstg and fcyc should be decoded as two values.
                        # This requires knowledge about the ii field from the
                        # sploop instruction which is currently not supported.
                case OperandForm.link_const:
                    if (var := self.__get_operand_var(vars, i, ('ulcst_dpr_byte', 'ucst', 
                            'lcst_high16', 'lcst_low16', 'scst'))):
                        current_operand = ImmediateOperand(var.value)
                    elif (var := self.__get_operand_var(vars, i, 
                            ('pcrel', 'pcrel_half', 'pcrel_half_unsigned'))):
                        fp_address = address - (address % FETCH_PACKET_SIZE)
                        current_operand = ImmediateOperand(fp_address + var.value)
                case (OperandForm.reg|OperandForm.reg_bside|OperandForm.xreg
                        |OperandForm.reg_nors|OperandForm.reg_bside_nors
                        |OperandForm.dreg|OperandForm.treg):
                    if (var := self.__get_operand_var(vars, i, ('reg', 'reg_shift'))):
                        reg_base = self.__decode_reg_base(operand_info.form,
                                unit_info, high_registers)
                        current_operand = RegisterOperand(Register(reg_base + var.value))
                        # unit for treg mode must be from t variable 
                        if (operand_info.form == OperandForm.treg 
                                and 't' not in vars):
                            current_operand = None 
                case OperandForm.areg:
                    if (var := self.__get_operand_var(vars, i, ('areg',))):
                        register = Register.B15 if var.value else Register.B14
                        current_operand = RegisterOperand(register)
                case (OperandForm.regpair|OperandForm.xregpair
                        |OperandForm.dregpair|OperandForm.tregpair):
                    if (var := self.__get_operand_var(vars, i, ('reg', 'reg_shift'))):
                        assert var.value&1 == 0, 'register pairs must start at even register'
                        reg_base = self.__decode_reg_base(operand_info.form,
                                unit_info, high_registers)
                        reg_high = Register(reg_base + var.value + 1)
                        reg_low = Register(reg_base + var.value)
                        current_operand = RegisterPairOperand(reg_high, reg_low)
                        # unit for treg mode must be from t variable 
                        if (operand_info.form == OperandForm.treg 
                                and 't' not in vars):
                            current_operand = None 
                    elif (var := self.__get_operand_var(vars, i, ('regpair_msb'))
                    ) and operand_info.form == OperandForm.regpair:
                        if unit_info.side == 2:
                            reg_base = Register.B0.value 
                        else: 
                            reg_base = Register.A0.value
                        reg_high = Register(reg_base + var.value | 0x1)
                        reg_low = Register(reg_base + (var.value | 0x1) - 1)
                        current_operand = RegisterPairOperand(reg_high, reg_low)
                case OperandForm.mem_deref:
                    # only used by c64x+ exclusive atomic instructions (ll, sl, cmtl)
                    if (var := self.__get_operand_var(vars, i, ('reg',))):
                        current_operand = MemoryOperand(
                            AddressingMode.POS_OFFSET,
                            Register(Register.A0.value + var.value),
                            0,
                            False
                        )
                case OperandForm.ctrl:
                    crhi = self.__get_operand_var(vars, i, ('crhi',))
                    crlo = self.__get_operand_var(vars, i, ('crlo',))
                    assert crlo is not None and crhi is not None
                    ctrl = None
                    if crlo.value in ControlRegister:
                        ctrl = ControlRegister(crlo.value)
                        # there are a few special cases:
                        if crlo == 0x02 and operand_info.rw == RW.read:
                            ctrl = ControlRegister.IFR
                        if crlo == 0x1d and operand_info.rw == RW.read:
                            ctrl = ControlRegister.EFR
                        # The register DIER is removed in C66X
                        # if ctrl == ControlRegister.DIER and ISA.C66X:
                        #     ctrl = None
                        if ctrl is not None and (
                            ((crhi.value & ctrl.crhi_mask) == 0)
                            or (self.isa not in ctrl.isa)
                            or (operand_info.rw not in ctrl.rw)
                        ):
                            ctrl = None
                    if ctrl is not None:
                        current_operand = ControlRegisterOperand(ctrl)
                # c64x 16-bit encoding, header and types are not fully supported yet
                case (OperandForm.mem_short|OperandForm.mem_ndw):
                    base_reg, offset, mode = None, None, None
                    offset_var, mode_var = None, None
                    scaled = False
                    # 1. Decode register base
                    high_registers &= not flags & TIC6X_FLAG_INSN16_NORS
                    reg_base = self.__decode_reg_base(
                            operand_info.form, unit_info, high_registers)
                    if (var := self.__get_operand_var(vars, i, ('reg_ptr',))):
                        reg_side = Register.B0 if unit_info.side == 2 else Register.A0
                        assert 0<= var.value < 4
                        base_reg = Register(reg_side + (0x4 | var.value))
                    elif (var := self.__get_operand_var(vars, i, ('reg', 'reg_shift'))):
                        base_reg = Register(reg_base +  var.value)
                    elif (header and flags & TIC6X_FLAG_INSN16_B15PTR):
                        assert unit_info.side == 2
                        base_reg = Register.B15
                    # 2. Determine addressing mode
                    if (var := self.__get_operand_var(vars, i, ('mem_mode',))):
                        mode_var = var.value
                    elif header is not None:
                        mode_var = TIC6X_FLAG_INSN16_MEM_MODE(flags)
                    if mode_var is not None:
                        mode = AddressingMode(mode_var & ~4)
                    # 3. Detect explicit scaling
                    if (var := self.__get_operand_var(vars, i, ('scaled',))):
                        scaled = bool(var.value)
                    # 4. Decode offset
                    if (var := self.__get_operand_var(vars, i, (
                        'mem_offset_minus_one',
                        'mem_offset_minus_one_noscale',
                        'mem_offset',
                        'mem_offset_noscale'
                    ))) and mode_var is not None:
                        offset_var = var.value
                        if (header and 'noscale' not in var.method):
                            scaled = True
                        offset_is_reg = (mode_var & 4) != 0
                        if offset_is_reg:
                            offset = Register(reg_base + offset_var)
                            if operand_info.form != OperandForm.mem_ndw:
                                scaled = True
                        else:
                            offset = offset_var
                            if operand_info.form != OperandForm.mem_ndw:
                                scaled = False
                                offset *= operand_info.size
                    if (mode is not None 
                            and base_reg is not None 
                            and offset is not None):
                        current_operand = MemoryOperand(mode,base_reg,offset, scaled)
                case OperandForm.mem_long:
                    base = self.__get_operand_var(vars, i, ('areg',))
                    offset = self.__get_operand_var(vars, i, 
                            ('ulcst_dpr_byte', 'ulcst_dpr_half', 'ulcst_dpr_word'))
                    if base and offset:
                        base_reg = Register.B15 if base.value else Register.B14
                        current_operand = MemoryOperand(
                            AddressingMode.POS_OFFSET,
                            base_reg,
                            offset.value * operand_info.size,
                            False
                        )
                case OperandForm.func_unit:
                    if (var := self.__get_operand_var(vars, i, ('spmask',))):
                        masked_units = set()
                        units = (
                            FuncUnit.L1, FuncUnit.L2,
                            FuncUnit.S1, FuncUnit.S2,
                            FuncUnit.D1, FuncUnit.D2,
                            FuncUnit.M1, FuncUnit.M2
                        )
                        for bit, unit in enumerate(units):
                            if (var.value >> bit) & 1:
                                masked_units.add(unit)
                        current_operand = FuncUnitsOperand(masked_units)
            
            if current_operand:
                operands.append(current_operand)
                continue
            print('not implemented', operand_info.form)
        return operands
    
    def __get_operand_var(self, vars:List[_Variable], 
            op:int, methods:Sequence[str]) -> Optional[_Variable]:
        for var in vars:
            if var.op != op: continue
            if var.method in methods:
                return var
        return None
    
    def __decode_reg_base(self, operand_form:OperandForm, unit_info:UnitInfo,
            high_registers:bool=False) -> int:
        if (
            unit_info.side == 2
            and operand_form in (OperandForm.reg, OperandForm.xreg, 
                OperandForm.reg_nors, OperandForm.regpair, OperandForm.xregpair,
                OperandForm.mem_short, OperandForm.mem_ndw)
        ) or (
            operand_form in (OperandForm.reg_bside, OperandForm.reg_bside_nors)
        ) or (
            unit_info.data_side == 2
            and operand_form in (OperandForm.dreg, OperandForm.treg,
                OperandForm.dregpair, OperandForm.tregpair)
        ):
            reg_base = Register.B0.value
        else: 
            reg_base = Register.A0.value
        if (
            operand_form in (OperandForm.xreg, OperandForm.xregpair)
            and unit_info.cross_path
        ):
            reg_base ^= Register.B0.value
        # Compact encoding high register halve
        if (
            high_registers
            and operand_form not in (OperandForm.reg_nors,
                OperandForm.reg_bside_nors)
        ):
            reg_base += 16
        return reg_base
