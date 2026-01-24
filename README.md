# TMS320C6x Disassembler

A pure python disassembler for the TMS320C6x family, currently supported up to ISA C674. Disassembles to python instruction objects for a configured ISA version.

*This project is based on the TI C6X Disassembler included in libopcodes. The conversion scripts of this project are intended to parse opcode definitions from this source and convert them to JSON.*

## Usage

To make use of this library, create a Disassembler object for your ISA version. For an address and instruction bytes the disassembler returns a generator of instructions. The disassembly can optionally be limited to a number of (32-bit) words.

Please note that from version C64x+ the ISA supports header-based fetch packets. If such a version is specified, the disassembler requires input data up to the end of a fetch packet to be disassemble any instruction in the fetch packet. This is necessary because distinguishing between compact and regular instructions is only possible using the header (or the absence of one). Additionally, header information may be relevant for regular instructions (see protected loads).

Example:
```python
from tms320c6x_disassembler import Disassembler
from tms320c6x_disassembler.types import ISA

disassembler = Disassembler(ISA.C67XP)
instr = disassembler.disasm(bytes.fromhex('00000028'), 0x80)
str(next(instr)) # '00000080: mvk .S1 0, A0'

hb_disassembler = Disassembler(ISA.C674)
instr = disassembler.disasm(bytes.fromhex('00000028'), 0x80)
assert len(instr) == 0 # header word missing from input
```

## Contributing

Contributions are welcome. Please feel free to submit a pull request.
