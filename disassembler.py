from .constants import WORD_SIZE, Endianness, Register
from .constants import TIC6X_FLAG_MACRO

from dataclasses import dataclass
from typing import Optional, List, Dict
from pathlib import Path
import json
from types import SimpleNamespace as Namespace


@dataclass
class Instruction:
    condition_reg:Optional[Register]
    condition_zero:Optional[bool]
    cross_path:Optional[bool]
    operands:List[int]
    opcode:int
    side:bool
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


def format_decoder(obj:dict):
    if {'name', 'key', 'mask', 'fields'}.issubset(obj.keys()):
        return InstructionFormat(obj['name'], int(obj['key'], 0),
                int(obj['mask'], 0), obj['fields'])
    elif {'name', 'pos', 'width'}.issubset(obj.keys()):
        return Field(obj['name'], obj['pos'], obj['width'])


class Disassembler:
    def __init__(self, endian:Endianness=Endianness.LITTLE) -> None:
        self.endianness = endian

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
            instr = self.__decode(encoded)
            yield instr
            # yield Instruction(None, None, False, [], 0, False, False)
            count -= 1

    def __decode(self, encoded:int) -> str:
        instr = "?"
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
        if instr: return instr
        raise ValueError()
    
    def __decode_field(self, field:Field, encoded:int) -> int:
        mask = (1<<field.width) - 1
        return (encoded>>field.pos) & mask
    
    def __matches_fixed(self, fields:Dict[str, int], 
            fixed:FixedField) -> bool:
        if fixed.id not in fields: 
            raise ValueError()
        return fixed.min <= fields[fixed.id] <= fixed.max

