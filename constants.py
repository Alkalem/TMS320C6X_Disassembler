from enum import Enum, StrEnum, IntEnum, auto

WORD_SIZE = 4

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

C62X  = 0x01
C64X  = 0x02
C64XP = 0x04
C67X  = 0x08
C67XP = 0x10
C674X = 0x20

TIC6X_FLAG_MACRO	= 0x0001
TIC6X_FLAG_FIRST	= 0x0002
TIC6X_FLAG_MCNOP	= 0x0004
TIC6X_FLAG_NO_MCNOP	= 0x0008
TIC6X_FLAG_LOAD		= 0x0010
TIC6X_FLAG_STORE	= 0x0020
TIC6X_FLAG_UNALIGNED	= 0x0040
TIC6X_FLAG_SIDE_B_ONLY	= 0x0080
TIC6X_FLAG_SIDE_T2_ONLY	= 0x0100
TIC6X_FLAG_NO_CROSS	= 0x0200
TIC6X_FLAG_CALL		= 0x0400
TIC6X_FLAG_RETURN	= 0x0800
TIC6X_FLAG_SPLOOP	= 0x1000
TIC6X_FLAG_SPKERNEL	= 0x2000
TIC6X_FLAG_SPMASK	= 0x4000
def TIC6X_FLAG_PREFER(x:int): return x << 15 
TIC6X_FLAG_INSN16_SPRED    = 0x00100000
TIC6X_FLAG_INSN16_NORS     = 0x00200000
TIC6X_FLAG_INSN16_BSIDE    = 0x00400000
TIC6X_FLAG_INSN16_B15PTR   = 0x00800000

def TIC6X_FLAG_INSN16_MEM_MODE(n:int): return ((n) << 16)
NEGATIVE      = 0
POSITIVE      = 1
REG_NEGATIVE  = 4
REG_POSITIVE  = 5
PREDECR       = 8
PREINCR       = 9
POSTDECR      = 10
POSTINCR      = 11
