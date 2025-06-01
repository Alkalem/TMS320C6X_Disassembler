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
