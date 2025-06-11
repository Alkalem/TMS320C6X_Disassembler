from dataclasses import dataclass
from enum import StrEnum, IntEnum, Enum, auto
from typing import List, Tuple

class Endianness(StrEnum):
    LITTLE = 'little'
    BIG = 'big'

class Register(IntEnum):
    A0 = 0
    A1 = 1
    A2 = 2
    A3 = 3
    A4 = 4
    A5 = 5
    A6 = 6
    A7 = 7
    A8 = 8
    A9 = 9
    A10 = 10
    A11 = 11
    A12 = 12
    A13 = 13
    A14 = 14
    A15 = 15
    B0 = 16
    B1 = 17
    B2 = 18
    B3 = 19
    B4 = 20
    B5 = 21
    B6 = 22
    B7 = 23
    B8 = 24
    B9 = 25
    B10 = 26
    B11 = 27
    B12 = 28
    B13 = 29
    B14 = 30
    B15 = 31

class ControlRegister(IntEnum):
    AMR = 0
    CSR = 1
    IFR = 2 # read access
    ISR = 32|2 # write access
    ICR = 3
    IER = 4
    ISTP = 5
    IRP = 6
    NRP = 7
    TSCL = 10 # c64x
    TSCH = 11 # c64x
    ILC = 13 # c64x
    RILC = 14 # c64x
    REP = 15 # c64x
    PCE1 = 16
    DNUM = 17 # c64x
    FADCR = 18
    FAUCR = 19
    FMCR = 20
    # c64x control register extensions from here on
    SSR = 21
    GPLYA = 22
    GPLYB = 23
    GFPGFR = 24
    DIER = 25
    TSR = 26
    ITSR = 27
    NTSR = 28
    EFR = 29 # read access
    ECR = 32|29 # write access
    IERR = 31

class AdressingMode(IntEnum):
    NEG_OFFSET = 0
    POS_OFFSET = 1
    PREDECREMENT = 8
    PREINCREMENT = 9
    POSTDECREMENT = 10
    POSTINCREMENT = 11

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
    CONTROL_REGISTER = auto()
    ADDRESS = auto()
    #TODO: complete type list
    UNKNOWN = auto()

@dataclass
class Operand:
    type:OperandType
    value:(int|Register|Tuple[Register,Register]|ControlRegister
            |Tuple[AdressingMode,Register,Register|int])

@dataclass
class Instruction:
    condition:ConditionType
    unit:str
    cross_path:bool
    operands:List[Operand]
    opcode:str
    parallel:bool

