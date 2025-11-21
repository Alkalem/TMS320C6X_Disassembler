from .constants import C62X, C64X, C64XP, C67X, C67XP, C674X

from dataclasses import dataclass
from enum import StrEnum, IntEnum, Enum, auto
from typing import Any, List, Tuple, Optional

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

    def __contains__(self, value: object) -> bool:
        if type(value) == type(self) and bool(value.value & self.value):
            return True
        if isinstance(value, int): 
            return bool(int(value) & self.value)
        return False

class RW(Enum):
    none = auto()
    read = auto()
    write = auto()
    read_write = auto()

    def __contains__(self, value: object) -> bool:
        # A bit hacky, but does the trick, i.e. r/w is in rw.
        return type(value) == type(self) and value.name in self.name

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

class _ControlRegister(IntEnum):
    _isa_: ISA
    _rw_: RW
    _crhi_mask_: int
    _is_supervisor_only_: bool

    def __new__(cls, value:int, isa:ISA, rw:RW, mask:int,
            is_supervisor_only:bool):
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj._isa_ = isa
        obj._rw_ = rw
        obj._crhi_mask_ = mask
        obj._is_supervisor_only_ = is_supervisor_only
        return obj
    
    @property
    def isa(self) -> ISA:
        return self._isa_
    
    @property
    def rw(self) -> RW:
        return self._rw_
    
    @property
    def crhi_mask(self) -> int:
        return self._crhi_mask_
    
    @property
    def is_supervisor_only(self) -> bool:
        return self._is_supervisor_only_

class ControlRegister(_ControlRegister):
    AMR    = (0b00000, ISA.C62X, RW.read_write, 0x10, False)
    CSR    = (0b00001, ISA.C62X, RW.read_write, 0x10, False)
    IFR    = (0b00010 | 0x20, ISA.C62X, RW.read, 0x1d, False)
    ISR    = (0b00010, ISA.C62X, RW.write, 0x10, False)
    ICR    = (0b00011, ISA.C62X, RW.write, 0x10, False)
    IER    = (0b00100, ISA.C62X, RW.read_write, 0x10, False)
    ISTP   = (0b00101, ISA.C62X, RW.read_write, 0x10, False)
    IRP    = (0b00110, ISA.C62X, RW.read_write, 0x10, False)
    NRP    = (0b00111, ISA.C62X, RW.read_write, 0x10, False)
    TSCL   = (0b01010, ISA.C64XP, RW.read_write, 0x1f, False)
    TSCH   = (0b01011, ISA.C64XP, RW.read, 0x1f, False)
    ILC    = (0b01101, ISA.C64XP, RW.read_write, 0x1f, False)
    RILC   = (0b01110, ISA.C64XP, RW.read_write, 0x1f, False)
    REP    = (0b01111, ISA.C64XP, RW.read_write, 0x1f, False)
    PCE1   = (0b10000, ISA.C62X, RW.read, 0xf, False)
    DNUM   = (0b10001, ISA.C64XP, RW.read, 0x1f, False)
    FADCR  = (0b10010, ISA.C67X, RW.read_write, 0x1f, False)
    FAUCR  = (0b10011, ISA.C67X, RW.read_write, 0x1f, False)
    FMCR   = (0b10100, ISA.C67X, RW.read_write, 0x1f, False)
    # mostly c64x+ control register extensions from here on
    SSR    = (0b10101, ISA.C64XP, RW.read_write, 0x1f, False)
    GPLYA  = (0b10110, ISA.C64XP, RW.read_write, 0x1f, False)
    GPLYB  = (0b10111, ISA.C64XP, RW.read_write, 0x1f, False)
    GFPGFR = (0b11000, ISA.C64X, RW.read_write, 0x1f, False)
    DIER   = (0b11001, ISA.C64XP, RW.read_write, 0x1f, False) # removed in c66x
    TSR    = (0b11010, ISA.C64XP, RW.read_write, 0x1f, False)
    ITSR   = (0b11011, ISA.C64XP, RW.read_write, 0x1f, False)
    NTSR   = (0b11100, ISA.C64XP, RW.read_write, 0x1f, False)
    EFR    = (0b11101 | 0x20, ISA.C64XP, RW.read, 0x1f, False)
    ECR    = (0b11101, ISA.C64XP, RW.write, 0x1f, False)
    IERR   = (0b11111, ISA.C64XP, RW.read_write, 0x1f, False)

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
