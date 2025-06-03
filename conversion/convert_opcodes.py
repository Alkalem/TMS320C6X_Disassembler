import json
from sys import argv
from typing import Iterator, List, Any, Optional
from collections.abc import Mapping
import re

if len(argv) < 3:
    print(f'Usage: {__file__} <in-path> <out-path>')
    print('\tConvert binutils instruction opcodes to JSON')
    exit()

in_path = argv[1]
with open(in_path, 'r') as file:
    formats_lines = file.readlines()

def INSNE(name:str, e:str, unit:str, format:str, type:str, isa:int, 
        flags:int, fixed:List[dict], ops:List[dict],
        vars:List[dict]) -> Optional[dict]:
    return {
        'name': name,
        'unit': unit,
        'format': format,
        'type': type,
        'isa': isa,
        'flags': flags,
        'fixed': fixed,
        'ops': ops,
        'vars': vars
    }
def INSN(name:str, unit:str, format:str, type:str, isa:int, 
        flags:int, fixed:List[dict], ops:List[dict],
        vars:List[dict]) -> Optional[dict]:
    return INSNE(name, 'ign', unit, format, type,
            isa, flags, fixed, ops, vars)
INSNUE = INSNE
INSNU = INSN

def RAN(id:str, min:int, max:int):
    if type(min) == str: min = int(min, 0)
    if type(max) == str: max = int(max, 0)
    return {'id':id, 'min':min, 'max':max}
def FIX(id:str, value:int):
    if type(value) == str: value = int(value, 0)
    return RAN(id, value, value)
def FIXN(*a): return tuple(a)
FIX0 = FIX1 = FIX2 = FIX3 = FIX4 = FIXN

def ENC(id:str, method:str, op:int):
    return {'id':id, 'method':method, 'op':op}
def ENCN(*a): return tuple(a)
ENC0 = ENC1 = ENC2 = ENC3 = ENCN
ENC4 = ENC5 = ENC6 = ENC7 = ENCN

def OPN(*a): return tuple(a)
OP0 = OP1 = OP2 = OP3 = OP4 = OPN

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

class MapStr(Mapping):
    def __len__(self) -> int: return 0
    def __iter__(self) -> Iterator: return iter([])
    def __contains__(self, key: object):
        return key not in globals()
    def __getitem__(self, key: Any):
        if not self.__contains__(key): raise KeyError(key)
        # if key[0] == 'O' and key[1] != 'P': return tuple()
        return str(key)

opcodes = list()
while len(formats_lines) > 0:
    line = formats_lines.pop(0).strip()
    if not line.startswith('INSN'): continue
    opcode_string = line
    while not line.endswith(')'):
        line = formats_lines.pop(0).strip()
        opcode_string += line
    # fix illegal python names before eval
    opcode_string = re.sub(r' (\b\d[\da-z_]+\b)', 
            lambda m: ' "'+m.group(1)+'"', opcode_string)
    opcode_string = re.sub(r'\band\b', 
            ' "and"', opcode_string)
    opcode_string = re.sub(r'\bnot\b', 
            ' "not"', opcode_string)
    opcode_string = re.sub(r'\bor\b', 
            ' "or"', opcode_string)
    # opcode_string = opcode_string.replace('or', '"or"')
    opcode = eval(opcode_string, globals(), MapStr())
    if not opcode: continue
    opcodes.append(opcode)

out_path = argv[2]
with open(out_path, 'w') as file:
    json.dump(opcodes, file, indent=4)
