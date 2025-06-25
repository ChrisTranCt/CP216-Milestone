#!/usr/bin/env python3
"""
ARM/Thumb Machine Code Decoder
Reads binary machine code file and decodes ARM instructions
"""

import struct
import sys

class ARMDecoder:
    def __init__(self):  # FIXED: Was missing underscores
        # ARM condition codes
        self.conditions = {
            0b0000: 'EQ',  # Equal
            0b0001: 'NE',  # Not equal
            0b0010: 'CS',  # Carry set
            0b0011: 'CC',  # Carry clear
            0b0100: 'MI',  # Minus/negative
            0b0101: 'PL',  # Plus/positive
            0b0110: 'VS',  # Overflow set
            0b0111: 'VC',  # Overflow clear
            0b1000: 'HI',  # Unsigned higher
            0b1001: 'LS',  # Unsigned lower or same
            0b1010: 'GE',  # Signed greater or equal
            0b1011: 'LT',  # Signed less than
            0b1100: 'GT',  # Signed greater than
            0b1101: 'LE',  # Signed less or equal
            0b1110: 'AL',  # Always (usually omitted)
            0b1111: 'NV'   # Never
        }

        # Register names
        self.registers = {
            0: 'R0', 1: 'R1', 2: 'R2', 3: 'R3',
            4: 'R4', 5: 'R5', 6: 'R6', 7: 'R7',
            8: 'R8', 9: 'R9', 10: 'R10', 11: 'R11',
            12: 'R12', 13: 'SP', 14: 'LR', 15: 'PC'
        }

    def read_machine_code_file(self, filename):
        """Read binary machine code file and return list of 32-bit instructions"""
        try:
            with open(filename, 'rb') as f:
                data = f.read()

            # Check if file size is multiple of 4 bytes
            if len(data) % 4 != 0:
                print(f"Warning: File size ({len(data)} bytes) is not multiple of 4")

            # Unpack 32-bit little-endian words
            instructions = []
            for i in range(0, len(data), 4):
                if i + 4 <= len(data):
                    word = struct.unpack('<I', data[i:i+4])[0]
                    instructions.append(word)

            return instructions

        except FileNotFoundError:
            print(f"Error: File '{filename}' not found")
            return []
        except Exception as e:
            print(f"Error reading file: {e}")
            return []

    def read_hex_text_file(self, filename):
        """Read hex text file (like our program.txt) and return list of 32-bit instructions"""
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()

            instructions = []
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if line and not line.startswith('#'):  # Skip empty lines and comments
                    try:
                        # Convert hex string to integer
                        instruction = int(line, 16)
                        instructions.append(instruction)
                    except ValueError:
                        print(f"Warning: Invalid hex value on line {line_num}: {line}")

            return instructions

        except FileNotFoundError:
            print(f"Error: File '{filename}' not found")
            return []
        except Exception as e:
            print(f"Error reading file: {e}")
            return []

    def extract_instruction_fields(self, instruction):
        """Extract common ARM instruction fields"""
        fields = {}

        # Bits 31-28: Condition field
        fields['condition'] = (instruction >> 28) & 0xF

        # Bits 27-25: Instruction type identifier
        fields['type_bits'] = (instruction >> 25) & 0x7

        # Bits 24-21: Opcode (varies by instruction type)
        fields['opcode'] = (instruction >> 21) & 0xF

        # Bit 20: S bit (set condition codes)
        fields['s_bit'] = (instruction >> 20) & 0x1

        # Bits 19-16: First operand register (Rn)
        fields['rn'] = (instruction >> 16) & 0xF

        # Bits 15-12: Destination register (Rd)
        fields['rd'] = (instruction >> 12) & 0xF

        # Bits 11-0: Operand 2 (immediate or register)
        fields['operand2'] = instruction & 0xFFF

        # Bit 25: Immediate flag (for data processing)
        fields['immediate'] = (instruction >> 25) & 0x1

        return fields

    def decode_data_processing(self, instruction, fields):
        """Decode data processing instructions (ADD, SUB, MOV, etc.)"""
        opcodes = {
            0b0000: 'AND', 0b0001: 'EOR', 0b0010: 'SUB', 0b0011: 'RSB',
            0b0100: 'ADD', 0b0101: 'ADC', 0b0110: 'SBC', 0b0111: 'RSC',
            0b1000: 'TST', 0b1001: 'TEQ', 0b1010: 'CMP', 0b1011: 'CMN',
            0b1100: 'ORR', 0b1101: 'MOV', 0b1110: 'BIC', 0b1111: 'MVN'
        }

        opcode = fields['opcode']
        condition = self.conditions.get(fields['condition'], 'AL')
        mnemonic = opcodes.get(opcode, f'UNK_{opcode:04b}')

        # Add condition suffix (except for AL)
        if condition != 'AL':
            mnemonic += condition

        # Add S suffix if S bit is set
        if fields['s_bit']:
            mnemonic += 'S'

        # Decode operands
        rd = self.registers[fields['rd']]
        rn = self.registers[fields['rn']]

        if fields['immediate']:
            # Immediate operand
            imm = fields['operand2'] & 0xFF
            rotate = (fields['operand2'] >> 8) & 0xF
            # Apply rotation (rotate right by 2*rotate)
            if rotate > 0:
                imm = ((imm >> (2 * rotate)) | (imm << (32 - 2 * rotate))) & 0xFFFFFFFF
            operand2_str = f"#{imm}"
        else:
            # Register operand
            rm = self.registers[fields['operand2'] & 0xF]
            shift = (fields['operand2'] >> 4) & 0xFF
            if shift == 0:
                operand2_str = rm
            else:
                # TODO: Decode shift operations
                operand2_str = f"{rm}, shift"

        # Format instruction based on opcode type
        if opcode in [0b1101, 0b1111]:  # MOV, MVN (single operand)
            return f"{mnemonic} {rd}, {operand2_str}"
        elif opcode in [0b1000, 0b1001, 0b1010, 0b1011]:  # TST, TEQ, CMP, CMN (no destination)
            return f"{mnemonic} {rn}, {operand2_str}"
        else:  # Standard three operand
            return f"{mnemonic} {rd}, {rn}, {operand2_str}"

    def decode_branch(self, instruction, fields):
        """Decode branch instructions"""
        condition = self.conditions.get(fields['condition'], 'AL')

        # Check if it's BL (Branch with Link)
        l_bit = (instruction >> 24) & 0x1
        mnemonic = 'BL' if l_bit else 'B'

        # Add condition suffix (except for AL)
        if condition != 'AL':
            mnemonic += condition

        # Extract 24-bit signed offset
        offset = instruction & 0xFFFFFF
        # Sign extend to 32 bits
        if offset & 0x800000:  # Check sign bit
            offset |= 0xFF000000

        # Multiply by 4 (instructions are word-aligned)
        offset *= 4

        return f"{mnemonic} {offset:+d}"

    def decode_memory(self, instruction, fields):
        """Decode load/store instructions"""
        # Bit 23: U bit (up/down)
        u_bit = (instruction >> 23) & 0x1
        # Bit 22: B bit (byte/word)
        b_bit = (instruction >> 22) & 0x1
        # Bit 21: W bit (write-back)
        w_bit = (instruction >> 21) & 0x1
        # Bit 20: L bit (load/store)
        l_bit = (instruction >> 20) & 0x1

        condition = self.conditions.get(fields['condition'], 'AL')

        # Determine mnemonic
        if l_bit:
            mnemonic = 'LDRB' if b_bit else 'LDR'
        else:
            mnemonic = 'STRB' if b_bit else 'STR'

        # Add condition suffix
        if condition != 'AL':
            mnemonic += condition

        rd = self.registers[fields['rd']]
        rn = self.registers[fields['rn']]

        # Decode addressing mode
        if fields['immediate'] == 0:  # Immediate offset
            offset = instruction & 0xFFF
            if not u_bit:  # Down
                offset = -offset

            if offset == 0:
                addr_str = f"[{rn}]"
            else:
                addr_str = f"[{rn}, #{offset}]"
        else:
            # Register offset (simplified)
            rm = self.registers[instruction & 0xF]
            sign = "+" if u_bit else "-"
            addr_str = f"[{rn}, {sign}{rm}]"

        return f"{mnemonic} {rd}, {addr_str}"

    def decode_instruction(self, instruction, address):
        """Main instruction decoder"""
        fields = self.extract_instruction_fields(instruction)

        # Determine instruction type based on bits 27-25
        type_bits = fields['type_bits']

        if type_bits in [0b000, 0b001]:  # Data processing
            return self.decode_data_processing(instruction, fields)
        elif type_bits == 0b101:  # Branch
            return self.decode_branch(instruction, fields)
        elif type_bits in [0b010, 0b011]:  # Load/Store
            return self.decode_memory(instruction, fields)
        else:
            return f"UNKNOWN (type={type_bits:03b})"

    def disassemble_file(self, filename):
        """Main function to read and decode ARM machine code file"""
        print(f"Reading ARM machine code from: {filename}")
        print("=" * 60)

        # Try reading as hex text file first, then as binary
        if filename.endswith('.txt'):
            instructions = self.read_hex_text_file(filename)
        else:
            instructions = self.read_machine_code_file(filename)

        if not instructions:
            print("No instructions found or file could not be read.")
            return

        print(f"Found {len(instructions)} instructions:")
        print()

        # Decode each instruction
        for i, instruction in enumerate(instructions):
            address = i * 4  # Each instruction is 4 bytes
            decoded = self.decode_instruction(instruction, address)

            print(f"0x{address:04X}: 0x{instruction:08X}  {decoded}")


def main():
    decoder = ARMDecoder()

    # Default to our example file
    filename = "program.txt"

    # Allow command line argument for filename
    if len(sys.argv) > 1:
        filename = sys.argv[1]

    decoder.disassemble_file(filename)


if __name__ == "__main__":  # FIXED: Was missing underscores
    main()