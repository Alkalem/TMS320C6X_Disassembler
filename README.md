# TMS320C6x Disassembler

A pure python disassembler for the TMS320C6x family, currently supported up to ISA C674. Disassembles to python instruction objects for a configured ISA version.

*This project is based on the TI C6X Disassembler included in libopcodes. The conversion scripts of this project are intended to parse opcode definitions from this source and convert them to JSON.*

## Usage

To make use of this library, create a Disassembler object for your ISA version. For an address and instruction bytes the disassembler returns a generator of instructions. The disassembly can optionally be limited to a number of (32-bit) words.

Please note that from version C64x+ the ISA supports header-based fetch packets (FPs). If such a version is specified, the disassembler requires knowledge about the last word of the FP to correctly disassembly instructions. Distinguishing between compact and regular instructions is only possible using the header (or the absence of one). Additionally, header information may be relevant for regular instructions (see protected loads). This library assumes no header if data ends in the middle of the FP and no header is specified. You can pass the header bytes (or last FP word in general) as a separate argument.

Example:
```python
from tms320c6x_disassembler import Disassembler
from tms320c6x_disassembler.types import ISA

disassembler = Disassembler(ISA.C67XP)
instr = disassembler.disasm(bytes.fromhex('00000028'), 0x80)
str(next(instr)) # '00000080: mvk .S1 0, A0'

hb_disassembler = Disassembler(ISA.C674X)
instr = hb_disassembler.disasm(bytes.fromhex('6eec'), 0x80)
assert len(instr) == 0 # header word missing for compact instruction

instr = hb_disassembler.disasm(bytes.fromhex('6eec'), 0x80, header=bytes.fromhex('000020e0'))
str(next(instr)) # '00000080: nop  8'
```

## Instruction Definitions

The source of truth for instructions, their encodings and semantics are the CPU and Instruction Set Reference Guides provided by TI. As mentioned above, the JSON definitions of the instructions are generated from header files from libopcodes. In some cases, the definitions in this repository differ from one of these sources.

This project updates the access information of the ADDK instruction. Only a write to the dst register is documented, but instead of reading the constant, this register should also be read. The register is treated as read+write here.

The following changes update the definitions of libobcodes in accordance with the reference guide. First, the flags of non-aligned load/store instructions were updated. All variants of these instructions should have the unaligned flag. Also, LDNDW/STNDW operands were updated to use scaled offsets. Lastly, the access information for BNOP and MVC was corrected to read in all cases. This is taken from the reference guide and seemingly incorrect in libobcodes.

For some instructions, the reference guide is not correct or at least less precise than libopcodes. The formats from libopcodes correct or specialize some formats, like for SPEKERNEL(R) and SPMASK(R). Additionally, libopcodes documents several errors in the reference guide for specific instructions. For example, a missing format for CMPGTU/CMPLTU instructions. In such cases, libopcodes is trusted.

Please also note that access information for memory operands does not document the register accesses in cycle 1 performed during address generation and optional base register update. Similarly, some instructions implicitly read control registers.

## Contributing

Contributions are welcome. Please feel free to submit a pull request. Please refrain from purely AI-driven contributions (keep a human in the loop).
