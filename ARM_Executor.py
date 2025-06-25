#!/usr/bin/env python3
"""
ARM Executor - Composition Approach
Combines your existing ARMDecoder with execution capabilities
"""

import sys
import os

# Import your existing ARMDecoder
try:
    from main import ARMDecoder
except ImportError:
    print("Error: Could not import ARMDecoder from main.py")
    print("Please ensure your main.py file is in the same directory")
    sys.exit(1)

class ARMExecutor:
    """
    ARM Executor using composition approach.
    Uses your existing ARMDecoder for decoding, adds execution engine.
    """
    
    def __init__(self):
        # Use your existing decoder for all decoding operations
        self.decoder = ARMDecoder()
        
        # PROCESSOR STATE MANAGEMENT
        self.registers = [0] * 16              # R0-R15 (32-bit each)
        self.flags = {'N': 0, 'Z': 0, 'C': 0, 'V': 0}  # CPSR flags
        self.memory = [0] * 4096               # 16KB memory (4096 words)
        
        # EXECUTION STATE
        self.pc = 0                            # Program counter
        self.running = True                    # Execution status
        self.cycle_count = 0                   # Instructions executed
        self.max_cycles = 10000                # Safety limit
        self.instructions = []                 # Loaded program
        
        # DEBUGGING
        self.debug_mode = True
        self.step_mode = False
    
    # =================================================================
    # PROGRAM LOADING (delegate to your decoder)
    # =================================================================
    
    def load_program(self, filename):
        """Load program using your existing decoder methods"""
        print(f"Loading program: {filename}")
        
        try:
            if filename.endswith('.txt'):
                self.instructions = self.decoder.read_hex_text_file(filename)
            else:
                self.instructions = self.decoder.read_machine_code_file(filename)
            
            if self.instructions:
                print(f"✅ Loaded {len(self.instructions)} instructions")
                return True
            else:
                print("❌ No instructions loaded")
                return False
                
        except Exception as e:
            print(f"❌ Error loading program: {e}")
            return False
    
    def disassemble_program(self):
        """Show program disassembly using your decoder"""
        print("\n" + "="*60)
        print("PROGRAM DISASSEMBLY")
        print("="*60)
        
        for i, instruction in enumerate(self.instructions):
            address = i * 4
            # Use your decoder for disassembly
            decoded = self.decoder.decode_instruction(instruction, address)
            print(f"0x{address:04X}: 0x{instruction:08X}  {decoded}")
        print()
    
    # =================================================================
    # PROCESSOR STATE MANAGEMENT
    # =================================================================
    
    def get_register(self, reg_num):
        """Get register value with bounds checking"""
        if 0 <= reg_num <= 15:
            return self.registers[reg_num] & 0xFFFFFFFF
        else:
            raise ValueError(f"Invalid register number: {reg_num}")
    
    def set_register(self, reg_num, value):
        """Set register value with bounds checking"""
        if 0 <= reg_num <= 15:
            self.registers[reg_num] = value & 0xFFFFFFFF
            # Special handling for PC (R15)
            if reg_num == 15:
                self.pc = self.registers[15]
        else:
            raise ValueError(f"Invalid register number: {reg_num}")
    
    def update_flags(self, result, operand1=None, operand2=None, is_subtraction=False):
        """Update CPSR flags based on operation result"""
        # Ensure result is 32-bit
        result_32bit = result & 0xFFFFFFFF
        
        # Zero flag: Set if result is zero
        self.flags['Z'] = 1 if result_32bit == 0 else 0
        
        # Negative flag: Set if bit 31 is set
        self.flags['N'] = 1 if (result_32bit & 0x80000000) != 0 else 0
        
        # Carry and Overflow flags (if operands provided)
        if operand1 is not None and operand2 is not None:
            if is_subtraction:
                # Carry set if no borrow (operand1 >= operand2)
                self.flags['C'] = 1 if operand1 >= operand2 else 0
            else:
                # Carry set if result overflows 32 bits
                self.flags['C'] = 1 if result > 0xFFFFFFFF else 0
            
            # Overflow flag (signed overflow detection)
            op1_sign = (operand1 >> 31) & 1
            op2_sign = (operand2 >> 31) & 1
            result_sign = (result_32bit >> 31) & 1
            
            if is_subtraction:
                self.flags['V'] = 1 if (op1_sign != op2_sign) and (op1_sign != result_sign) else 0
            else:
                self.flags['V'] = 1 if (op1_sign == op2_sign) and (op1_sign != result_sign) else 0
    
    def check_condition(self, condition_code):
        """Check if condition code is satisfied"""
        if condition_code == 0b1110:    # AL - Always
            return True
        elif condition_code == 0b0000:  # EQ - Equal
            return self.flags['Z'] == 1
        elif condition_code == 0b0001:  # NE - Not equal
            return self.flags['Z'] == 0
        elif condition_code == 0b0010:  # CS/HS - Carry set
            return self.flags['C'] == 1
        elif condition_code == 0b0011:  # CC/LO - Carry clear
            return self.flags['C'] == 0
        elif condition_code == 0b0100:  # MI - Minus/negative
            return self.flags['N'] == 1
        elif condition_code == 0b0101:  # PL - Plus/positive
            return self.flags['N'] == 0
        elif condition_code == 0b1010:  # GE - Greater or equal
            return self.flags['N'] == self.flags['V']
        elif condition_code == 0b1011:  # LT - Less than
            return self.flags['N'] != self.flags['V']
        else:
            print(f"Warning: Unimplemented condition code {condition_code:04b}")
            return True  # Default to execute
    
    # =================================================================
    # INSTRUCTION EXECUTION METHODS
    # =================================================================
    
    def get_operand2_value(self, fields):
        """Get value of operand2 (immediate or register)"""
        if fields['immediate']:
            # Immediate value with rotation
            imm = fields['operand2'] & 0xFF
            rotate = (fields['operand2'] >> 8) & 0xF
            if rotate > 0:
                # Rotate right by 2*rotate bits
                rotate_amount = 2 * rotate
                imm = ((imm >> rotate_amount) | (imm << (32 - rotate_amount))) & 0xFFFFFFFF
            return imm
        else:
            # Register value (simplified - no shifts for now)
            rm = fields['operand2'] & 0xF
            return self.get_register(rm)
    
    def execute_mov(self, fields):
        """Execute MOV instruction"""
        rd = fields['rd']
        operand2_value = self.get_operand2_value(fields)
        
        # Set destination register
        self.set_register(rd, operand2_value)
        
        # Update flags if S bit is set
        if fields['s_bit']:
            self.update_flags(operand2_value)
        
        if self.debug_mode:
            reg_name = self.decoder.registers.get(rd, f'R{rd}')
            print(f"    -> {reg_name} = 0x{operand2_value:08X}")
    
    def execute_add(self, fields):
        """Execute ADD instruction"""
        rd = fields['rd']
        rn = fields['rn']
        
        rn_value = self.get_register(rn)
        operand2_value = self.get_operand2_value(fields)
        
        result = rn_value + operand2_value
        self.set_register(rd, result)
        
        # Update flags if S bit is set
        if fields['s_bit']:
            self.update_flags(result, rn_value, operand2_value, False)
        
        if self.debug_mode:
            rd_name = self.decoder.registers.get(rd, f'R{rd}')
            rn_name = self.decoder.registers.get(rn, f'R{rn}')
            print(f"    -> {rd_name} = {rn_name}({rn_value}) + {operand2_value} = 0x{result & 0xFFFFFFFF:08X}")
    
    def execute_sub(self, fields):
        """Execute SUB instruction"""
        rd = fields['rd']
        rn = fields['rn']
        
        rn_value = self.get_register(rn)
        operand2_value = self.get_operand2_value(fields)
        
        result = rn_value - operand2_value
        self.set_register(rd, result)
        
        # Update flags if S bit is set
        if fields['s_bit']:
            self.update_flags(result, rn_value, operand2_value, True)
        
        if self.debug_mode:
            rd_name = self.decoder.registers.get(rd, f'R{rd}')
            rn_name = self.decoder.registers.get(rn, f'R{rn}')
            print(f"    -> {rd_name} = {rn_name}({rn_value}) - {operand2_value} = 0x{result & 0xFFFFFFFF:08X}")
    
    def execute_cmp(self, fields):
        """Execute CMP instruction"""
        rn = fields['rn']
        
        rn_value = self.get_register(rn)
        operand2_value = self.get_operand2_value(fields)
        
        # CMP performs subtraction but doesn't store result
        result = rn_value - operand2_value
        
        # CMP always updates flags
        self.update_flags(result, rn_value, operand2_value, True)
        
        if self.debug_mode:
            rn_name = self.decoder.registers.get(rn, f'R{rn}')
            print(f"    -> Compare {rn_name}({rn_value}) with {operand2_value}")
            print(f"       Flags: N:{self.flags['N']} Z:{self.flags['Z']} C:{self.flags['C']} V:{self.flags['V']}")
    
    def execute_branch(self, instruction, fields):
        """Execute branch instructions"""
        # Extract 24-bit signed offset
        offset = instruction & 0xFFFFFF
        if offset & 0x800000:  # Sign extend
            offset = offset - 0x1000000
        
        # Calculate branch target (word-aligned, +8 for pipeline)
        branch_target = self.pc + (offset * 4) + 8
        
        # Check if it's BL (Branch with Link)
        l_bit = (instruction >> 24) & 0x1
        if l_bit:
            # Save return address in LR (R14)
            self.set_register(14, self.pc + 4)
            if self.debug_mode:
                print(f"    -> LR = 0x{self.pc + 4:08X} (return address)")
        
        # Update PC
        self.pc = branch_target & 0xFFFFFFFF
        
        if self.debug_mode:
            branch_type = "BL" if l_bit else "B"
            print(f"    -> {branch_type} to 0x{self.pc:08X}")
    
    def execute_and(self, fields):
        """Execute AND instruction"""
        rd = fields['rd']
        rn = fields['rn']
        
        rn_value = self.get_register(rn)
        operand2_value = self.get_operand2_value(fields)
        
        result = rn_value & operand2_value
        self.set_register(rd, result)
        
        # Update flags if S bit is set
        if fields['s_bit']:
            self.update_flags(result)
        
        if self.debug_mode:
            rd_name = self.decoder.registers.get(rd, f'R{rd}')
            rn_name = self.decoder.registers.get(rn, f'R{rn}')
            print(f"    -> {rd_name} = {rn_name}(0x{rn_value:08X}) AND 0x{operand2_value:08X} = 0x{result & 0xFFFFFFFF:08X}")
    
    def execute_orr(self, fields):
        """Execute ORR instruction"""
        rd = fields['rd']
        rn = fields['rn']
        
        rn_value = self.get_register(rn)
        operand2_value = self.get_operand2_value(fields)
        
        result = rn_value | operand2_value
        self.set_register(rd, result)
        
        # Update flags if S bit is set
        if fields['s_bit']:
            self.update_flags(result)
        
        if self.debug_mode:
            rd_name = self.decoder.registers.get(rd, f'R{rd}')
            rn_name = self.decoder.registers.get(rn, f'R{rn}')
            print(f"    -> {rd_name} = {rn_name}(0x{rn_value:08X}) OR 0x{operand2_value:08X} = 0x{result & 0xFFFFFFFF:08X}")
    
    def execute_eor(self, fields):
        """Execute EOR (XOR) instruction"""
        rd = fields['rd']
        rn = fields['rn']
        
        rn_value = self.get_register(rn)
        operand2_value = self.get_operand2_value(fields)
        
        result = rn_value ^ operand2_value
        self.set_register(rd, result)
        
        # Update flags if S bit is set
        if fields['s_bit']:
            self.update_flags(result)
        
        if self.debug_mode:
            rd_name = self.decoder.registers.get(rd, f'R{rd}')
            rn_name = self.decoder.registers.get(rn, f'R{rn}')
            print(f"    -> {rd_name} = {rn_name}(0x{rn_value:08X}) XOR 0x{operand2_value:08X} = 0x{result & 0xFFFFFFFF:08X}")
    
    def execute_mvn(self, fields):
        """Execute MVN (Move NOT) instruction"""
        rd = fields['rd']
        operand2_value = self.get_operand2_value(fields)
        
        result = ~operand2_value
        self.set_register(rd, result)
        
        # Update flags if S bit is set
        if fields['s_bit']:
            self.update_flags(result)
        
        if self.debug_mode:
            rd_name = self.decoder.registers.get(rd, f'R{rd}')
            print(f"    -> {rd_name} = NOT 0x{operand2_value:08X} = 0x{result & 0xFFFFFFFF:08X}")

    def execute_data_processing(self, instruction, fields):
        """Execute data processing instructions"""
        opcode = fields['opcode']
        
        if opcode == 0b1101:    # MOV
            self.execute_mov(fields)
        elif opcode == 0b0100:  # ADD
            self.execute_add(fields)
        elif opcode == 0b0010:  # SUB
            self.execute_sub(fields)
        elif opcode == 0b1010:  # CMP
            self.execute_cmp(fields)
        elif opcode == 0b0000:  # AND
            self.execute_and(fields)
        elif opcode == 0b1100:  # ORR
            self.execute_orr(fields)
        elif opcode == 0b0001:  # EOR (XOR)
            self.execute_eor(fields)
        elif opcode == 0b1111:  # MVN
            self.execute_mvn(fields)
        else:
            print(f"❌ Unimplemented data processing opcode: {opcode:04b}")
            return False
        
        return True
    
    def execute_instruction(self, instruction):
        """Execute a single instruction"""
        # Use your decoder to extract fields
        fields = self.decoder.extract_instruction_fields(instruction)
        condition = fields['condition']
        type_bits = fields['type_bits']
        
        # Check condition
        if not self.check_condition(condition):
            if self.debug_mode:
                cond_name = self.decoder.conditions.get(condition, f'COND{condition:04b}')
                print(f"    -> Condition {cond_name} not met, skipping")
            return True  # Skip but continue execution
        
        # Execute based on instruction type
        if type_bits in [0b000, 0b001]:  # Data processing
            return self.execute_data_processing(instruction, fields)
        elif type_bits == 0b101:  # Branch
            self.execute_branch(instruction, fields)
            return True
        else:
            print(f"❌ Unimplemented instruction type: {type_bits:03b}")
            return False
    
    # =================================================================
    # PROGRAM EXECUTION
    # =================================================================
    
    def print_state(self):
        """Print current processor state"""
        print(f"\n--- Cycle {self.cycle_count} State ---")
        print(f"PC: 0x{self.pc:04X}")
        
        # Print non-zero registers
        print("Registers:", end="")
        shown_any = False
        for i in range(16):
            if self.registers[i] != 0:
                reg_name = self.decoder.registers.get(i, f'R{i}')
                print(f" {reg_name}:0x{self.registers[i]:08X}", end="")
                shown_any = True
        if not shown_any:
            print(" (all zero)")
        else:
            print()
        
        # Print flags
        active_flags = []
        if self.flags['N']: active_flags.append('N')
        if self.flags['Z']: active_flags.append('Z')
        if self.flags['C']: active_flags.append('C')
        if self.flags['V']: active_flags.append('V')
        
        if active_flags:
            print(f"Flags: {' '.join(active_flags)}")
        else:
            print("Flags: (none set)")
    
    def run_program(self, debug=True, step_by_step=False):
        """Run the loaded program"""
        if not self.instructions:
            print("❌ No program loaded")
            return
        
        print("\n" + "="*60)
        print("STARTING PROGRAM EXECUTION")
        print("="*60)
        
        self.debug_mode = debug
        self.step_mode = step_by_step
        self.pc = 0
        self.cycle_count = 0
        self.running = True
        
        # Show initial state
        if debug:
            self.print_state()
        
        while self.running and self.cycle_count < self.max_cycles:
            # Check if PC is within bounds
            instruction_index = self.pc // 4
            if instruction_index >= len(self.instructions):
                print(f"\n✅ Program ended - PC beyond instruction memory")
                break
            
            # Fetch instruction
            instruction = self.instructions[instruction_index]
            
            if debug:
                print(f"\nPC: 0x{self.pc:04X} | Cycle {self.cycle_count + 1}")
                # Use your decoder for disassembly
                decoded = self.decoder.decode_instruction(instruction, self.pc)
                print(f"Executing: 0x{instruction:08X} -> {decoded}")
            
            # Execute instruction
            old_pc = self.pc
            success = self.execute_instruction(instruction)
            
            if not success:
                print(f"❌ Execution failed at PC: 0x{self.pc:04X}")
                break
            
            # Update PC if not modified by instruction (e.g., branch)
            if self.pc == old_pc:
                self.pc += 4
            
            self.cycle_count += 1
            
            if debug:
                self.print_state()
            
            if step_by_step:
                input("Press Enter to continue...")
            
            # Check for termination conditions
            if instruction == 0xE1A0F00E:  # MOV PC, LR
                print(f"\n✅ Program returned (MOV PC, LR)")
                break
        
        # Execution summary
        if self.cycle_count >= self.max_cycles:
            print(f"\n⚠️ Execution stopped - maximum cycles ({self.max_cycles}) reached")
        
        print(f"\n" + "="*60)
        print(f"EXECUTION COMPLETE")
        print(f"Total cycles: {self.cycle_count}")
        print("="*60)
        
        if debug:
            self.print_state()


# =================================================================
# USAGE EXAMPLES AND TESTING
# =================================================================

def test_basic_execution():
    """Test basic instruction execution"""
    print("Testing Basic ARM Execution")
    print("="*40)
    
    executor = ARMExecutor()
    
    # Create simple test program
    test_program = [
        0xE3A01005,  # MOV R1, #5
        0xE3A02003,  # MOV R2, #3
        0xE0813002,  # ADD R3, R1, R2
        0xE1530001,  # CMP R3, R1
        0xE1A0F00E   # MOV PC, LR (return)
    ]
    
    executor.instructions = test_program
    
    print("Test program:")
    executor.disassemble_program()
    
    print("Executing...")
    executor.run_program(debug=True)


def main():
    """Main function with command line interface"""
    if len(sys.argv) < 2:
        print("ARM Executor - Composition Approach")
        print("="*40)
        print("Usage:")
        print("  python arm_executor.py <program.txt>     # Run program")
        print("  python arm_executor.py test              # Run test")
        print("  python arm_executor.py step <program>    # Step-by-step execution")
        return
    
    if sys.argv[1] == "test":
        test_basic_execution()
        return
    
    # Create executor
    executor = ARMExecutor()
    
    # Load program
    filename = sys.argv[1] if sys.argv[1] != "step" else sys.argv[2]
    step_mode = (sys.argv[1] == "step")
    
    if not executor.load_program(filename):
        return
    
    # Show disassembly
    executor.disassemble_program()
    
    # Run program
    executor.run_program(debug=True, step_by_step=step_mode)


if __name__ == "__main__":
    main()