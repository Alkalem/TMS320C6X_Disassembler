from .constants import C62X, C64X, C64XP, C67X, C67XP, C674X

from dataclasses import dataclass
from enum import StrEnum, IntEnum, Enum, auto
from typing import List, Tuple, Optional

class Endianness(StrEnum):
    LITTLE = 'little'
    BIG = 'big'

class ISA(IntEnum):
    C62X = C62X
    C64X = C62X | C64X
    C64XP = C62X | C64X | C64XP
    C67X = C62X | C67X
    C67XP = C62X | C67X | C67XP
    C674X = C62X | C64X | C64XP | C67X | C67XP | C674X

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
    A16 = 16
    A17 = 17
    A18 = 18
    A19 = 19
    A20 = 20
    A21 = 21
    A22 = 22
    A23 = 23
    A24 = 24
    A25 = 25
    A26 = 26
    A27 = 27
    A28 = 28
    A29 = 29
    A30 = 30
    A31 = 31
    B0 = 32
    B1 = 33
    B2 = 34
    B3 = 35
    B4 = 36
    B5 = 37
    B6 = 38
    B7 = 39
    B8 = 40
    B9 = 41
    B10 = 42
    B11 = 43
    B12 = 44
    B13 = 45
    B14 = 46
    B15 = 47
    B16 = 48
    B17 = 49
    B18 = 50
    B19 = 51
    B20 = 52
    B21 = 53
    B22 = 54
    B23 = 55
    B24 = 56
    B25 = 57
    B26 = 58
    B27 = 59
    B28 = 60
    B29 = 61
    B30 = 62
    B31 = 63

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

class AddressingMode(IntEnum):
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
    IMMEDIATE = auto()
    REGISTER = auto()
    REGISTER_PAIR = auto()
    CONTROL_REGISTER = auto()
    MEMORY = auto()
    #TODO: complete type list
    UNKNOWN = auto()

@dataclass
class Operand:
    @property
    def kind(self) -> OperandType:
        raise NotImplementedError('abstract operand')
            
@dataclass
class ImmediateOperand(Operand):
    value: int

    @property
    def kind(self) -> OperandType:
        return OperandType.IMMEDIATE
    
    def __str__(self) -> str:
        if abs(self.value) > 9:
            return hex(self.value)
        return str(self.value)
    
@dataclass
class RegisterOperand(Operand):
    register: Register
    
    @property
    def kind(self) -> OperandType:
        return OperandType.REGISTER
    
    def __str__(self) -> str:
        return str(self.register)
    
@dataclass
class RegisterPairOperand(Operand):
    high: Register
    low: Register

    @property
    def kind(self) -> OperandType:
        return OperandType.REGISTER_PAIR
    
    def __str__(self) -> str:
        return f'{self.high}:{self.low}'
    
@dataclass
class ControlRegisterOperand(Operand):
    register: ControlRegister

    @property
    def kind(self) -> OperandType:
        return OperandType.CONTROL_REGISTER
    
    def __str__(self) -> str:
        return str(self.register)
    
@dataclass
class MemoryOperand(Operand):
    mode: AddressingMode
    base: Register
    offset: int|Register

    @property
    def kind(self) -> OperandType:
        return OperandType.MEMORY
    
    def __str__(self) -> str:
        match self.mode:
            case AddressingMode.NEG_OFFSET:
                format = '*-{}({})'
            case AddressingMode.POS_OFFSET:
                format = '*+{}({})'
            case AddressingMode.PREDECREMENT:
                format = '*--{}({})'
            case AddressingMode.PREINCREMENT:
                format = '*++{}({})'
            case AddressingMode.POSTDECREMENT:
                format = '*{}--({})'
            case AddressingMode.POSTINCREMENT:
                format = '*{}++({})'
        return format.format(self.base, self.offset)



@dataclass
class Instruction:
    address:int
    size:int
    condition:ConditionType
    unit:str
    cross_path:bool
    operands:List[Operand]
    opcode:str
    parallel:bool
    __INVALID_OPCODE = "invalid opcode"

    def __str__(self) -> str:
        operand_str = ', '.join([str(operand) for operand in self.operands])
        condition_str = f'{self.condition} ' if str(self.condition) else ''
        return f'{self.address:08x}: {condition_str}{self.opcode} {self.unit} {operand_str}'
    
    @staticmethod
    def invalid(address:int, size:int, parallel:bool):
        return Instruction(address,
            size,
            ConditionType.RESERVED,
            "", False, [], 
            Instruction.__INVALID_OPCODE,
            parallel
        )

    def is_invalid(self) -> bool:
        return self.opcode == Instruction.__INVALID_OPCODE
