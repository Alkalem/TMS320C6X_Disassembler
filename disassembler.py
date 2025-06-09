from .constants import WORD_SIZE, Endianness, Register
from .constants import TIC6X_FLAG_MACRO, TIC6X_FLAG_SIDE_B_ONLY, \
        TIC6X_FLAG_SIDE_T2_ONLY
from .operands import OPERANDS, OperandForm

from dataclasses import dataclass
from enum import IntEnum, Enum, auto
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json
from types import SimpleNamespace as Namespace
from collections import namedtuple

class ConditionType(IntEnum):
    UNCONDITIONAL = 0
    BREAKPOINT = 1
    B0 = 2
    NOT_B0 = 3
    B1 = 4
    NOT_B1 = 5
    B2 = 6
    NOT_B2 = 7
    A1 = 8
    NOT_A1 = 9
    A2 = 10
    NOT_A2 = 11
    RESERVED = 12
    @classmethod
    def _missing_(cls, value):
        return cls.RESERVED

class OperandType(Enum):
    CONST = auto()
    REGISTER = auto()
    REGISTER_PAIR = auto()
    #TODO: complete type list
    UNKNOWN = auto()

@dataclass
class Operand:
    type:OperandType
    value:int|Register|Tuple[Register,Register]

@dataclass
class Instruction:
    condition:ConditionType
    unit:str
    cross_path:bool
    operands:List[Operand]
    opcode:str
    parallel:bool

@dataclass
class Field:
    id:str
    pos:int
    width:int

@dataclass
class InstructionFormat:
    name:str
    key:int
    mask:int
    fields:List[Field]

@dataclass
class FixedField:
    id:str
    min:int
    max:int

@dataclass
class VarField:
    id:str
    method:str
    op:int
    value:Optional[int]

@dataclass
class Opcode:
    name:str
    unit:str
    format:str
    type:str
    isa:int
    flags:int
    fixed:List[FixedField]
    ops:List[str]
    vars:List[VarField]

@dataclass
class UnitInfo:
    side:int
    data_side:int
    cross:bool

MaskedField = namedtuple('MaskedField', ('value', 'mask'))


def format_decoder(obj:dict):
    if {'name', 'key', 'mask', 'fields'}.issubset(obj.keys()):
        return InstructionFormat(obj['name'], int(obj['key'], 0),
                int(obj['mask'], 0), obj['fields'])
    elif {'name', 'pos', 'width'}.issubset(obj.keys()):
        return Field(obj['name'], obj['pos'], obj['width'])


class Disassembler:
    def __init__(self, endian:Endianness=Endianness.LITTLE) -> None:
        self.endianness = endian
        self.fetch_packet_header_based = False # c64x encoding

        basepath = Path(__file__).resolve().parent
        with open(basepath / 'instruction_formats.json') as file:
            self.instruction_formats:List[InstructionFormat] = json.load(
                file, object_hook=format_decoder)
            self.instruction_formats.sort(
                key=lambda f: -f.mask.bit_count())
            self.instruction_maps:Dict[str, List[Opcode]] = {
                f.name: list()
                for f in self.instruction_formats}
        with open(basepath / 'opcodes.json') as file:
            opcodes:List[Opcode] = json.load(
                file, object_hook=lambda obj: Namespace(**obj))
            for opcode in opcodes:
                if opcode.flags & TIC6X_FLAG_MACRO:
                    continue # ignore assembly macros
                format = opcode.unit+'_'+opcode.format
                if format in self.instruction_maps:
                    self.instruction_maps[format].append(opcode)

    def disasm(self, data:bytes, address:int, count:int=-1):
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
            yield instr
            count -= 1

    def __decode(self, encoded:int, address:int) -> Instruction:
        instr = None
        for format in self.instruction_formats:
            if encoded & format.mask == format.key:
                print('unit', format.name)
                fields = {
                    field.id: self.__decode_field(field, encoded)
                    for field in format.fields
                }

                for opcode in self.instruction_maps[format.name]:
                    if not all({ self.__matches_fixed(fields, fixed)
                            for fixed in opcode.fixed}):
                        continue
                    print(opcode.name, opcode)
                    var_fields = {
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
                        var_fields)
                    operands = self.__decode_operands(opcode.ops, unit_info, 
                            var_fields, address)
                    instr = Instruction(
                        condition, unit, cross_path,
                        operands, opcode.name, parallel)

        if instr: return instr
        raise ValueError()
    
    def __decode_field(self, field:Field, encoded:int) -> MaskedField:
        mask = (1<<field.width) - 1
        return MaskedField((encoded>>field.pos) & mask, mask)
    
    def __decode_var_field(self, var:VarField, 
            fields:Dict[str, MaskedField]) -> VarField:
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
        return VarField(var.id, var.method, var.op, value)
    
    def __decode_signed(self, field:MaskedField) -> int:
        return (field.value ^ field.mask) - field.mask
    
    def __matches_fixed(self, fields:Dict[str, MaskedField], 
            fixed:FixedField) -> bool:
        if fixed.id not in fields: 
            raise ValueError()
        return fixed.min <= fields[fixed.id].value <= fixed.max
    
    def __decode_parallel(self, fields:Dict[str, MaskedField]) -> bool:
        return 'p' in fields and bool(fields['p'].value)
    
    def __decode_condition(self, 
            fields:Dict[str, MaskedField]) -> ConditionType:
        condition_value = (
            fields['creg'].value<<1 if 'creg' in fields else 0
        ) | (
            fields['z'].value if 'z' in fields else 0
        )
        return ConditionType(condition_value)
    
    def __decode_cross_path(self, fields:Dict[str, MaskedField]) -> bool:
        return 'x' in fields and bool(fields['x'].value)

    def __decode_unit(self, unit:str, flags:int, cross_path:bool, 
            vars:Dict[str, VarField]) -> Tuple[str,UnitInfo]:
        if unit == 'nfu': return '', UnitInfo(0,0,False)
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
                UnitInfo(func_unit_side, func_unit_data_side, func_unit_cross)
    
    def __decode_operands(self, ops:List[str], unit_info:UnitInfo,
            vars:Dict[str, VarField], address:int) -> List[Operand]:
        operands = list()
        for i, op in enumerate(ops):
            operand_info = OPERANDS[op]
            current_operand = None
            match operand_info.form:
                case OperandForm.b15reg:
                    current_operand = Operand(OperandType.REGISTER, Register.B15)
                case OperandForm.zreg:
                    current_operand = Operand(OperandType.REGISTER, 
                            Register.B0 if unit_info.side == 2 else Register.A0)
                case OperandForm.retreg:
                    current_operand = Operand(OperandType.REGISTER, 
                            Register.B3 if unit_info.side == 2 else Register.A3)
                case OperandForm.hw_const_minus_1:
                    current_operand = Operand(OperandType.CONST, -1)
                case OperandForm.hw_const_0:
                    current_operand = Operand(OperandType.CONST, 0)
                case OperandForm.hw_const_1:
                    current_operand = Operand(OperandType.CONST, 1)
                case OperandForm.hw_const_5:
                    current_operand = Operand(OperandType.CONST, 5)
                case OperandForm.hw_const_16:
                    current_operand = Operand(OperandType.CONST, 16)
                case OperandForm.hw_const_24:
                    current_operand = Operand(OperandType.CONST, 24)
                case OperandForm.hw_const_31:
                    current_operand = Operand(OperandType.CONST, 31)
            if current_operand:
                operands.append(current_operand)
                continue
            for var in vars.values():
                assert var.value is not None
                if var.op != i: continue

                match var.method:
                    case (
                            'cst_s3i'|'ucst'|'ulcst_dpr_byte'|'ulcst_dpr_half'
                            |'ulcst_dpr_word'|'lcst_low16'|'lcst_high16'
                            |'scst'|'scst_l3i'
                            |'ucst_minus_one'
                    ):
                        match operand_info.form:
                            case OperandForm.asm_const|OperandForm.link_const:
                                current_operand = Operand(OperandType.CONST, var.value)
                            case OperandForm.mem_long:
                                assert var.value >= 0
                                raise NotImplementedError('mem_long const offset')
                    case 'pcrel'|'pcrel_half'|'pcrel_half_unsigned':
                        assert operand_info.form == OperandForm.link_const
                        current_operand = Operand(OperandType.CONST, 
                                address + var.value)
                    case 'regpair_msb':
                        assert operand_info.form == OperandForm.regpair
                        if unit_info.side == 2:
                            reg_base = Register.B0.value 
                        else: 
                            reg_base = Register.A0.value
                        reg_high = Register(reg_base + var.value | 0x1)
                        reg_low = Register(reg_base + var.value | 0x1 - 1)
                        current_operand = Operand(OperandType.REGISTER_PAIR, 
                                (reg_high, reg_low))
                    case 'reg_shift'|'reg':
                        # c64x 16-bit encoding, header and types are not supported yet
                        match operand_info.form:
                            case (
                                OperandForm.reg|OperandForm.reg_bside
                                |OperandForm.xreg
                            ):
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
                                current_operand = Operand(OperandType.REGISTER,
                                        Register(reg_base + var.value))
                            case OperandForm.dreg:
                                if unit_info.data_side == 2:
                                    reg_base = Register.B0.value
                                else: 
                                    reg_base = Register.A0.value
                                current_operand = Operand(OperandType.REGISTER,
                                        Register(reg_base + var.value))
                            case OperandForm.regpair|OperandForm.xregpair:
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
                                current_operand = Operand(OperandType.REGISTER_PAIR,
                                        (reg_high, reg_low))
                            case OperandForm.dregpair:
                                assert var.value&1 == 0
                                if unit_info.data_side == 2:
                                    reg_base = Register.B0.value
                                else: 
                                    reg_base = Register.A0.value
                                reg_high = Register(reg_base + var.value + 1)
                                reg_low = Register(reg_base + var.value)
                                current_operand = Operand(OperandType.REGISTER_PAIR,
                                        (reg_high, reg_low))
                            case _:
                                raise NotImplementedError('operand form for register')
                                

            if current_operand:
                operands.append(current_operand)
                continue
            print('not implemented', operand_info.form)
        return operands
