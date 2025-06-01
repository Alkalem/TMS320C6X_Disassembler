import json
from sys import argv
from typing import Iterator, List, Any, Optional
from collections.abc import Mapping

if len(argv) < 3:
    print(f'Usage: {__file__} <in-path> <out-path>')
    print(f'\tConvert binutils instruction formats to JSON')
    exit()

in_path = argv[1]
with open(in_path, 'r') as file:
    formats_lines = file.readlines()

def FMT(name:str, bit_width:int, key:int, 
        mask:int, fields:List[dict]) -> Optional[dict]:
    if bit_width == 32:
        return {
            'name': name,
            'key': hex(key),
            'mask': hex(mask),
            'fields': fields
        }
    
def FLD(name:str, pos:int, width:int):
    return {'name':name, 'pos':pos, 'width':width}

CONDITIONAL_FIELDS = (
    FLD('p', 0, 1), FLD('creg', 29, 3), FLD('z', 28, 1)
)
NONCONDITIONAL_FIELDS = (FLD('p', 0, 1),)
SIDE_FIELDS = (FLD('s', 0, 1),)

def CFLDS(*a): return CONDITIONAL_FIELDS + tuple(a)
CFLDS1 = CFLDS2 = CFLDS3 = CFLDS4 = CFLDS
CFLDS5 = CFLDS6 = CFLDS7 = CFLDS8 = CFLDS
def NFLDS(*a): return NONCONDITIONAL_FIELDS + tuple(a)
NFLDS1 = NFLDS2 = NFLDS3 = NFLDS4 = NFLDS
NFLDS5 = NFLDS6 = NFLDS7 = NFLDS
def SFLDS(*a): return SIDE_FIELDS + tuple(a)
SFLDS1 = SFLDS2 = SFLDS3 = SFLDS4 = SFLDS
SFLDS5 = SFLDS6 = SFLDS7 = SFLDS
def FLDS(*a): return tuple(a)
FLDS1 = FLDS2 = FLDS3 = FLDS4 = FLDS5 = FLDS

SAT = BR = DSZ = lambda _: 0
def IGNORED(*a): return None
BFLD = BFLD1 = BFLD2 = BFLD3 = BFLD4 = COMPFLD = IGNORED

class MapStr(Mapping):
    def __len__(self) -> int: return 0
    def __iter__(self) -> Iterator: return iter([])
    def __contains__(self, key: object):
        return key not in globals()
    def __getitem__(self, key: Any):
        if not self.__contains__(key): raise KeyError(key)
        return str(key)

instruction_formats = list()
while len(formats_lines) > 0:
    line = formats_lines.pop(0).strip()
    if not line.startswith('FMT('): continue
    format_string = line
    while not line.endswith(')'):
        line = formats_lines.pop(0).strip()
        format_string += line
    format = eval(format_string, globals(), MapStr())
    if not format: continue
    instruction_formats.append(format)

out_path = argv[2]
with open(out_path, 'w') as file:
    json.dump(instruction_formats, file, indent=4)
