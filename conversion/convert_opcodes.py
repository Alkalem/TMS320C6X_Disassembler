import json
from sys import argv
from typing import Iterator, List, Any, Optional
from collections.abc import Mapping
import re

from ..constants import *

if len(argv) < 3:
    print(f'Usage: {__file__} <in-path> <out-path>')
    print('\tConvert binutils instruction opcodes to JSON')
    exit()

in_path = argv[1]
with open(in_path, 'r') as file:
    formats_lines = file.readlines()

C64X_AND_C67X = C64X | C67X

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
