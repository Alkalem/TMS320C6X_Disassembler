from .constants import WORD_SIZE, Register

from dataclasses import dataclass
from typing import Optional, List

@dataclass
class Instruction:
    condition_reg:Optional[Register]
    condition_zero:Optional[bool]
    cross_path:Optional[bool]
    operands:List[int]
    opcode:int
    side:bool
    parallel:bool


class Disassembler:
    def __init__(self) -> None:
        self.little_endian = True

    def disasm(self, data:bytes, address:int, count:int=-1):
        remaining = data
        current_address = address
        while len(remaining) >= WORD_SIZE and count != 0:
            current_data = remaining[:WORD_SIZE]
            remaining = remaining[WORD_SIZE:]
            current_address += WORD_SIZE
            
            encoded = int.from_bytes(current_data, 
                    'little' if self.little_endian else 'big')
            yield Instruction(None, None, False, [], 0, False, False)
            count -= 1
