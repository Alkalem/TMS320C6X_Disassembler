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

WORD_SIZE = 4
FETCH_PACKET_SIZE = 8 * WORD_SIZE
EXECUTION_PACKET_LIMIT = 8

C62X  = 0x01
C64X  = 0x02
C64XP = 0x04
C67X  = 0x08
C67XP = 0x10
C674X = 0x20

HEADER_MASK = 0xF000_0000
HEADER_KEY = 0xE000_0000
HEADER_FIELD_MASK = 0x7F
HEADER_PBITS_MASK = 0x3FFF
HEADER_LAYOUT_OFFSET = 21
HEADER_EXPANSION_OFFSET = 14

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
def TIC6X_PREFER_VAL(x:int): return (x & 0x8000) >> 15 
def TIC6X_FLAG_PREFER(x:int): return x << 15 
TIC6X_FLAG_INSN16_SPRED    = 0x00100000
TIC6X_FLAG_INSN16_NORS     = 0x00200000
TIC6X_FLAG_INSN16_BSIDE    = 0x00400000
TIC6X_FLAG_INSN16_B15PTR   = 0x00800000

def TIC6X_FLAG_INSN16_MEM_MODE(n:int): 
    return ((n) >> 16) & 0xf
