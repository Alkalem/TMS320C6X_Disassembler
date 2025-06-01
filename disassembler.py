from .constants import WORD_SIZE, Endianness, Register

from dataclasses import dataclass
from typing import Optional, List
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
    name:str
    pos:int
    width:int

@dataclass
class InstructionFormat:
    name:str
    key:int
    mask:int
    fields:List[Field]

def format_decoder(obj:dict):
    if {'name', 'key', 'mask', 'fields'}.issubset(obj.keys()):
        return InstructionFormat(obj['name'], int(obj['key'], 0),
                int(obj['mask'], 0), obj['fields'])

class Disassembler:
    def __init__(self, endian:Endianness=Endianness.LITTLE) -> None:
        self.endianness = endian

        basepath = Path(__file__).resolve().parent
        with open(basepath / 'instruction_formats.json') as file:
            self.instruction_formats:List[InstructionFormat] = json.load(
                file, object_hook=format_decoder)

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
        for format in self.instruction_formats:
            if encoded & format.mask == format.key:
                return format.name
        raise ValueError()
