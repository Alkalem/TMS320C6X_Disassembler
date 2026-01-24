# Copyright 2025-2026 Benedikt Waibel
# 
# This file is part of the library tms320c6x_disassembler.
# 
# The tms320c6x_disassembler is free software: 
# you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.

from enum import Enum, auto
from dataclasses import dataclass
from typing import Dict

from .types import RW


class OperandForm(Enum):
    asm_const = auto()
    link_const = auto()
    reg = auto()
    reg_nors = auto()
    reg_bside = auto()
    reg_bside_nors = auto()
    xreg = auto()
    dreg = auto()
    areg = auto()
    b15reg = auto()
    treg = auto()
    zreg = auto()
    retreg = auto()
    regpair = auto()
    xregpair = auto()
    dregpair = auto()
    tregpair = auto()
    irp = auto()
    nrp = auto()
    ilc = auto()
    ctrl = auto()
    mem_short = auto()
    mem_ndw = auto()
    mem_long = auto()
    mem_deref = auto()
    func_unit = auto()
    hw_const_minus_1 = auto()
    hw_const_0 = auto()
    hw_const_1 = auto()
    hw_const_5 = auto()
    hw_const_16 = auto()
    hw_const_24 = auto()
    hw_const_31 = auto()

@dataclass
class OperandInfo:
    form:OperandForm
    size:int
    rw:RW
    low_first:int
    low_last:int
    high_first:int
    high_last:int

OPERANDS:Dict[str, OperandInfo] = {
    'OACST': OperandInfo(OperandForm.asm_const, 0, RW.none, 0, 0, 0, 0),
    'OLCST': OperandInfo(OperandForm.link_const, 0, RW.none, 0, 0, 0, 0),
    'OHWCSTM1': OperandInfo(OperandForm.hw_const_minus_1, 0, RW.none, 0, 0, 0, 0),
    'OHWCST0': OperandInfo(OperandForm.hw_const_0, 0, RW.none, 0, 0, 0, 0),
    'OHWCST1': OperandInfo(OperandForm.hw_const_1, 0, RW.none, 0, 0, 0, 0),
    'OHWCST5': OperandInfo(OperandForm.hw_const_5, 0, RW.none, 0, 0, 0, 0),
    'OHWCST16': OperandInfo(OperandForm.hw_const_16, 0, RW.none, 0, 0, 0, 0),
    'OHWCST24': OperandInfo(OperandForm.hw_const_24, 0, RW.none, 0, 0, 0, 0),
    'OHWCST31': OperandInfo(OperandForm.hw_const_31, 0, RW.none, 0, 0, 0, 0),
    'OFULIST': OperandInfo(OperandForm.func_unit, 0, RW.none, 0, 0, 0, 0),
    'ORIRP1': OperandInfo(OperandForm.irp, 4, RW.read, 1, 1, 0, 0),
    'ORNRP1': OperandInfo(OperandForm.nrp, 4, RW.read, 1, 1, 0, 0),
    'OWREG1': OperandInfo(OperandForm.reg, 4, RW.write, 1, 1, 0, 0),
    'OWREG1Z': OperandInfo(OperandForm.zreg, 4, RW.write, 1, 1, 0, 0),
    'OWREG1NORS': OperandInfo(OperandForm.reg_nors, 4, RW.write, 1, 1, 0, 0),
    'ORREG1B': OperandInfo(OperandForm.reg_bside, 4, RW.write, 1, 1, 0, 0),
    'ORREG1BNORS': OperandInfo(OperandForm.reg_bside_nors, 4, RW.write, 1, 1, 0, 0),
    'OWRETREG1': OperandInfo(OperandForm.retreg, 4, RW.write, 1, 1, 0, 0),
    'ORREG1': OperandInfo(OperandForm.reg, 4, RW.read, 1, 1, 0, 0),
    'ORDREG1': OperandInfo(OperandForm.dreg, 4, RW.read, 1, 1, 0, 0),
    'ORTREG1': OperandInfo(OperandForm.treg, 4, RW.read, 1, 1, 0, 0),
    'ORWREG1': OperandInfo(OperandForm.reg, 4, RW.read_write, 1, 1, 0, 0),
    'ORB15REG1': OperandInfo(OperandForm.b15reg, 4, RW.read, 1, 1, 0, 0),
    'OWB15REG1': OperandInfo(OperandForm.b15reg, 4, RW.write, 1, 1, 0, 0),
    'ORAREG1': OperandInfo(OperandForm.areg, 4, RW.read, 1, 1, 0, 0),
    'ORXREG1': OperandInfo(OperandForm.xreg, 4, RW.read, 1, 1, 0, 0),
    'ORREG12': OperandInfo(OperandForm.reg, 4, RW.read, 1, 2, 0, 0),
    'ORREG14': OperandInfo(OperandForm.reg, 4, RW.read, 1, 4, 0, 0),
    'ORXREG14': OperandInfo(OperandForm.xreg, 4, RW.read, 1, 4, 0, 0),
    'OWREG2': OperandInfo(OperandForm.reg, 4, RW.write, 2, 2, 0, 0),
    'OWREG4': OperandInfo(OperandForm.reg, 4, RW.write, 4, 4, 0, 0),
    'OWREG9': OperandInfo(OperandForm.reg, 4, RW.write, 9, 9, 0, 0),
    'OWDREG5': OperandInfo(OperandForm.dreg, 4, RW.write, 5, 5, 0, 0),
    'OWTREG5': OperandInfo(OperandForm.treg, 4, RW.write, 5, 5, 0, 0),
    'OWREGL1': OperandInfo(OperandForm.regpair, 5, RW.write, 1, 1, 1, 1),
    'ORREGL1': OperandInfo(OperandForm.regpair, 5, RW.read, 1, 1, 1, 1),
    'OWREGD1': OperandInfo(OperandForm.regpair, 8, RW.write, 1, 1, 1, 1),
    'OWREGD12': OperandInfo(OperandForm.regpair, 8, RW.write, 1, 1, 2, 2),
    'OWREGD4': OperandInfo(OperandForm.regpair, 8, RW.write, 4, 4, 4, 4),
    'ORREGD1': OperandInfo(OperandForm.regpair, 8, RW.read, 1, 1, 1, 1),
    'OWREGD45': OperandInfo(OperandForm.regpair, 8, RW.write, 4, 4, 5, 5),
    'OWREGD67': OperandInfo(OperandForm.regpair, 8, RW.write, 6, 6, 7, 7),
    'ORDREGD1': OperandInfo(OperandForm.dregpair, 8, RW.read, 1, 1, 1, 1),
    'ORTREGD1': OperandInfo(OperandForm.tregpair, 8, RW.read, 1, 1, 1, 1),
    'OWDREGD5': OperandInfo(OperandForm.dregpair, 8, RW.write, 5, 5, 5, 5),
    'OWTREGD5': OperandInfo(OperandForm.tregpair, 8, RW.write, 5, 5, 5, 5),
    'ORREGD12': OperandInfo(OperandForm.regpair, 8, RW.read, 1, 1, 2, 2),
    'ORXREGD12': OperandInfo(OperandForm.xregpair, 8, RW.read, 1, 1, 2, 2),
    'ORREGD1234': OperandInfo(OperandForm.regpair, 8, RW.read, 1, 2, 3, 4),
    'ORXREGD1324': OperandInfo(OperandForm.xregpair, 8, RW.read, 1, 3, 2, 4),
    'OWREGD910': OperandInfo(OperandForm.regpair, 8, RW.write, 9, 9, 10, 10),
    'ORCREG1': OperandInfo(OperandForm.ctrl, 4, RW.read, 1, 1, 0, 0),
    'OWCREG1': OperandInfo(OperandForm.ctrl, 4, RW.write, 1, 1, 0, 0),
    'OWILC1': OperandInfo(OperandForm.ilc, 4, RW.write, 1, 1, 0, 0),
    'ORMEMDW': OperandInfo(OperandForm.mem_deref, 4, RW.read, 3, 3, 0, 0),
    'OWMEMDW': OperandInfo(OperandForm.mem_deref, 4, RW.write, 3, 3, 0, 0),
    'ORMEMSB': OperandInfo(OperandForm.mem_short, 1, RW.read, 3, 3, 0, 0),
    'OWMEMSB': OperandInfo(OperandForm.mem_short, 1, RW.write, 3, 3, 0, 0),
    'ORMEMLB': OperandInfo(OperandForm.mem_long, 1, RW.read, 3, 3, 0, 0),
    'OWMEMLB': OperandInfo(OperandForm.mem_long, 1, RW.write, 3, 3, 0, 0),
    'ORMEMSH': OperandInfo(OperandForm.mem_short, 2, RW.read, 3, 3, 0, 0),
    'OWMEMSH': OperandInfo(OperandForm.mem_short, 2, RW.write, 3, 3, 0, 0),
    'ORMEMLH': OperandInfo(OperandForm.mem_long, 2, RW.read, 3, 3, 0, 0),
    'OWMEMLH': OperandInfo(OperandForm.mem_long, 2, RW.write, 3, 3, 0, 0),
    'ORMEMSW': OperandInfo(OperandForm.mem_short, 4, RW.read, 3, 3, 0, 0),
    'OWMEMSW': OperandInfo(OperandForm.mem_short, 4, RW.write, 3, 3, 0, 0),
    'ORMEMLW': OperandInfo(OperandForm.mem_long, 4, RW.read, 3, 3, 0, 0),
    'OWMEMLW': OperandInfo(OperandForm.mem_long, 4, RW.write, 3, 3, 0, 0),
    'ORMEMSD': OperandInfo(OperandForm.mem_short, 8, RW.read, 3, 3, 0, 0),
    'OWMEMSD': OperandInfo(OperandForm.mem_short, 8, RW.write, 3, 3, 0, 0),
    'ORMEMND': OperandInfo(OperandForm.mem_ndw, 8, RW.read, 3, 3, 0, 0),
    'OWMEMND': OperandInfo(OperandForm.mem_ndw, 8, RW.write, 3, 3, 0, 0),
}
