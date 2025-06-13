from dataclasses import dataclass
from enum import StrEnum, IntEnum, Enum, auto
from typing import List, Tuple, Optional

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

    def __str__(self) -> str:
        return self.name

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

    def __str__(self) -> str:
        return self.name

class AdressingMode(IntEnum):
    NEG_OFFSET = 0
    POS_OFFSET = 1
    PREDECREMENT = 8
    PREINCREMENT = 9
    POSTDECREMENT = 10
    POSTINCREMENT = 11

class _ConditionEnum(IntEnum):
    _branch_: Optional[bool]
    _register_: Optional[Register]

    def __new__(cls, value:int, branch:Optional[bool], 
            register:Optional[Register]):
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj._branch_ = branch
        obj._register_ = register
        return obj

    @property
    def branch(self) -> Optional[bool]:
        return self._branch_
    
    @property
    def register(self) -> Optional[Register]:
        return self._register_
    
    def __str__(self) -> str:
        if self.branch is None:
            return ''
        else:
            reg = self.register.name if self.register else 'x'
            return f'[{reg}]' if self.branch else f'[!{reg}]'

class ConditionType(_ConditionEnum):
    UNCONDITIONAL = (0, None, None)
    BREAKPOINT = (1, True, None)
    B0 = (2, True, Register.B0)
    NOT_B0 = (3, False, Register.B0)
    B1 = (4, True, Register.B1)
    NOT_B1 = (5, False, Register.B1)
    B2 = (6, True, Register.B2)
    NOT_B2 = (7, False, Register.B2)
    A1 = (8, True, Register.A1)
    NOT_A1 = (9, False, Register.A1)
    A2 = (10, True, Register.A2)
    NOT_A2 = (11, False, Register.A2)
    RESERVED = (12, None, None)

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
    
    def __str__(self) -> str:
        match self.type:
            case OperandType.CONST:
                assert type(self.value) == int
                if abs(self.value) > 9:
                    return hex(self.value)
                return str(self.value)
            case OperandType.REGISTER|OperandType.CONTROL_REGISTER:
                return str(self.value)
            case OperandType.REGISTER_PAIR:
                return f'{self.value[0].name}:{self.value[1].name}'
            case OperandType.ADDRESS:
                base = str(self.value[1])
                offset = str(self.value[2])
                match self.value[0]:
                    case AdressingMode.NEG_OFFSET:
                        format = '*-{}({})'
                    case AdressingMode.POS_OFFSET:
                        format = '*-{}({})'
                    case AdressingMode.PREDECREMENT:
                        format = '*--{}({})'
                    case AdressingMode.PREINCREMENT:
                        format = '*++{}({})'
                    case AdressingMode.POSTDECREMENT:
                        format = '*{}--({})'
                    case AdressingMode.POSTINCREMENT:
                        format = '*{}++({})'
                return format.format(base, offset)
            case _:
                return 'unknown'

@dataclass
class Instruction:
    condition:ConditionType
    unit:str
    cross_path:bool
    operands:List[Operand]
    opcode:str
    parallel:bool

    def __str__(self) -> str:
        operand_str = ', '.join([str(operand) for operand in self.operands])
        condition_str = f'{self.condition} ' if str(self.condition) else ''
        return f'{condition_str}{self.opcode} {self.unit} {operand_str}'
