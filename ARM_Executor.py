#!/usr/bin/env python3
"""
Enhanced ARM/Thumb Executor
Extends your existing ARMExecutor with Thumb execution capabilities
"""

import sys
import os

# Import your existing executor
try:
    from ARM_Executor import ARMExecutor
except ImportError:
    print("Error: Could not import ARMExecutor from ARM_Executor.py")
    print("Please ensure ARM_Executor.py is in the same directory")
    sys.exit(1)

# Import the enhanced decoder
try:
    from enhanced_decoder import EnhancedARMDecoder
except ImportError:
    print("Error: Could not import EnhancedARMDecoder from enhanced_decoder.py")
    print("Please ensure enhanced_decoder.py is in the same directory")
    sys.exit(1)


class EnhancedARMExecutor(ARMExecutor):
    """
    Enhanced ARM/Thumb Executor
    
    Extends your existing ARMExecutor with:
    - Thumb instruction execution
    - ARM/Thumb mode switching
    - Mixed program support
    - Enhanced debugging
    """
    
    def __init__(self):
        # Initialize parent class - all your existing ARM functionality
        super().__init__()
        
        # ENHANCED DECODER
        self.enhanced_decoder = EnhancedARMDecoder()
        
        # MODE MANAGEMENT  
        self.thumb_mode = False           # Current processor mode (False=ARM, True=Thumb)
        self.instruction_size = 4         # Current instruction size (2=Thumb, 4=ARM)
        self.interworking_enabled = True  # ARM/Thumb interworking support
        
        # PROGRAM STATE
        self.instruction_addresses = []   # Address of each instruction
        self.instruction_modes = []       # Mode (ARM/THUMB) for each instruction
        
        # EXECUTION STATISTICS
        self.arm_cycles = 0              # ARM instructions executed
        self.thumb_cycles = 0            # Thumb instructions executed  
        self.mode_switches = 0           # Number of mode changes
        self.branch_predictions = 0      # Branch instructions executed
        
        # DEBUGGING ENHANCEMENTS
        self.show_mode_switches = True   # Show mode change messages
        self.show_instruction_bytes = True  # Show raw instruction encoding
    
    # =================================================================
    # MODE MANAGEMENT
    # =================================================================
    
    def set_processor_mode(self, thumb_mode):
        """Switch between ARM and Thumb modes"""
        if self.thumb_mode != thumb_mode:
            if self.debug_mode and self.show_mode_switches:
                old_mode = "THUMB" if self.thumb_mode else "ARM"
                new_mode = "THUMB" if thumb_mode else "ARM"
                print(f"🔄 Mode switch: {old_mode} → {new_mode} at PC: 0x{self.pc:04X}")
            
            self.mode_switches += 1
        
        self.thumb_mode = thumb_mode
        self.instruction_size = 2 if thumb_mode else 4
        
        # Update PC alignment for mode
        if thumb_mode:
            self.pc &= 0xFFFFFFFE  # Halfword align for Thumb
        else:
            self.pc &= 0xFFFFFFFC  # Word align for ARM
    
    def get_current_mode_string(self):
        """Get current mode as string for debugging"""
        return "THUMB" if self.thumb_mode else "ARM"
    
    def get_next_pc(self):
        """Get next PC value accounting for current instruction size"""
        return self.pc + self.instruction_size
    
    # =================================================================
    # ENHANCED PROGRAM LOADING
    # =================================================================
    
    def load_mixed_program(self, filename):
        """Load program with ARM/Thumb mode detection and handling"""
        print(f"Loading mixed ARM/Thumb program: {filename}")
        
        try:
            if filename.endswith('.txt'):
                instructions, addresses, modes = self.enhanced_decoder.read_hex_text_file_mixed(filename)
            else:
                instructions, addresses, modes = self.enhanced_decoder.read_mixed_file(filename)
            
            if not instructions:
                print("❌ No instructions loaded")
                return False
            
            # Store program data
            self.instructions = instructions
            self.instruction_addresses = addresses
            self.instruction_modes = modes
            
            # Set initial processor mode based on first instruction
            if modes and modes[0] == 'THUMB':
                self.set_processor_mode(True)
                print("🎯 Starting in THUMB mode")
            else:
                self.set_processor_mode(False)
                print("🎯 Starting in ARM mode")
            
            # Statistics
            arm_count = modes.count('ARM')
            thumb_count = modes.count('THUMB')
            
            print(f"✅ Loaded {len(instructions)} instructions")
            print(f"   📊 ARM: {arm_count}, Thumb: {thumb_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading program: {e}")
            return False
    
    def disassemble_mixed_program(self):
        """Show disassembly of mixed ARM/Thumb program"""
        if not self.instructions:
            print("❌ No program loaded")
            return
        
        print(f"\n{'='*70}")
        print("MIXED ARM/THUMB PROGRAM DISASSEMBLY")
        print(f"{'='*70}")
        
        for i, (instruction, address, mode) in enumerate(zip(
            self.instructions, self.instruction_addresses, self.instruction_modes)):
            
            if mode == 'ARM':
                # Use your existing ARM decoder
                decoded = self.enhanced_decoder.arm_decoder.decode_instruction(instruction, address)
                print(f"0x{address:04X}: 0x{instruction:08X}  {decoded:30s} [ARM]")
            else:  # THUMB
                # Use enhanced Thumb decoder
                decoded = self.enhanced_decoder.thumb_decoder.decode_thumb_instruction(instruction, address)
                print(f"0x{address:04X}: 0x{instruction:04X}      {decoded:30s} [THUMB]")
        print()
    
    # =================================================================
    # THUMB INSTRUCTION EXECUTION
    # =================================================================
    
    def execute_thumb_instruction(self, instruction):
        """Execute a single 16-bit Thumb instruction"""
        
        # Extract format classification bits  
        bits_15_13 = (instruction >> 13) & 0x7
        bits_15_12 = (instruction >> 12) & 0xF
        bits_15_11 = (instruction >> 11) & 0x1F
        bits_15_10 = (instruction >> 10) & 0x3F
        bits_15_8 = (instruction >> 8) & 0xFF
        
        # Execute based on instruction format (using same priority as decoder)
        
        # Format 5: Hi register operations/branch exchange
        if bits_15_10 == 0b010001:
            return self.execute_thumb_hi_reg_ops(instruction)
        
        # Format 3: Move/compare/add/subtract immediate
        elif bits_15_13 == 0b001:
            return self.execute_thumb_immediate_ops(instruction)
        
        # Format 2: Add/subtract
        elif bits_15_11 == 0b00011:
            return self.execute_thumb_add_subtract(instruction)
        
        # Format 1: Move shifted register
        elif bits_15_13 == 0b000:
            return self.execute_thumb_move_shifted(instruction)
        
        # Format 4: ALU operations
        elif bits_15_10 == 0b010000:
            return self.execute_thumb_alu_ops(instruction)
        
        # Format 16: Conditional branch
        elif bits_15_12 == 0b1101 and ((instruction >> 8) & 0xF) != 0xF:
            return self.execute_thumb_conditional_branch(instruction)
        
        # Format 18: Unconditional branch
        elif bits_15_11 == 0b11100:
            return self.execute_thumb_unconditional_branch(instruction)
        
        # Format 17: Software Interrupt
        elif bits_15_8 == 0b11011111:
            return self.execute_thumb_swi(instruction)
        
        else:
            if self.debug_mode:
                print(f"❌ Unimplemented Thumb instruction: 0x{instruction:04X}")
            return False
    
    # =================================================================
    # CORE THUMB EXECUTION METHODS
    # =================================================================
    
    def execute_thumb_move_shifted(self, instruction):
        """Execute Format 1: Move shifted register"""
        opcode = (instruction >> 11) & 0x3    # Shift type
        offset = (instruction >> 6) & 0x1F    # Shift amount
        rs = (instruction >> 3) & 0x7         # Source register
        rd = instruction & 0x7                # Destination register
        
        rs_value = self.get_register(rs)
        
        # Special case: MOV (LSL with 0 offset)
        if opcode == 0 and offset == 0:
            result = rs_value
            if self.debug_mode:
                print(f"    -> MOV R{rd}, R{rs}")
        else:
            # Perform shift operation (simplified for basic functionality)
            if opcode == 0:  # LSL
                result = (rs_value << offset) & 0xFFFFFFFF
            elif opcode == 1:  # LSR
                shift_amount = 32 if offset == 0 else offset
                result = rs_value >> shift_amount
            elif opcode == 2:  # ASR
                shift_amount = 32 if offset == 0 else offset
                if rs_value & 0x80000000:  # Negative number
                    result = (rs_value >> shift_amount) | (0xFFFFFFFF << (32 - shift_amount))
                else:
                    result = rs_value >> shift_amount
                result &= 0xFFFFFFFF
            else:
                print(f"❌ Unknown shift operation: {opcode}")
                return False
            
            if self.debug_mode:
                ops = ['LSL', 'LSR', 'ASR']
                print(f"    -> {ops[opcode]} R{rd}, R{rs}, #{offset}")
        
        # Set destination register and update flags
        self.set_register(rd, result)
        self.update_flags(result)  # Thumb move/shift always updates flags
        
        return True
    
    def execute_thumb_add_subtract(self, instruction):
        """Execute Format 2: Add/subtract"""
        opcode = (instruction >> 9) & 0x1     # 0=ADD, 1=SUB
        immediate = (instruction >> 10) & 0x1  # 0=register, 1=immediate
        rn_imm = (instruction >> 6) & 0x7     # Register or 3-bit immediate
        rs = (instruction >> 3) & 0x7         # Source register
        rd = instruction & 0x7                # Destination register
        
        rs_value = self.get_register(rs)
        
        if immediate:
            operand = rn_imm  # 3-bit immediate (0-7)
        else:
            operand = self.get_register(rn_imm)
        
        if opcode:  # SUB
            result = rs_value - operand
            self.update_flags(result, rs_value, operand, True)
            op_name = "SUB"
        else:  # ADD
            result = rs_value + operand
            self.update_flags(result, rs_value, operand, False)
            op_name = "ADD"
        
        self.set_register(rd, result)
        
        if self.debug_mode:
            if immediate:
                print(f"    -> {op_name} R{rd}, R{rs}, #{operand}")
            else:
                print(f"    -> {op_name} R{rd}, R{rs}, R{rn_imm}")
        
        return True
    
    def execute_thumb_immediate_ops(self, instruction):
        """Execute Format 3: Move/compare/add/subtract immediate"""
        opcode = (instruction >> 11) & 0x3   # Operation type
        rd = (instruction >> 8) & 0x7        # Destination register
        imm8 = instruction & 0xFF             # 8-bit immediate
        
        rd_value = self.get_register(rd)
        
        if opcode == 0:  # MOV
            self.set_register(rd, imm8)
            self.update_flags(imm8)
            if self.debug_mode:
                print(f"    -> MOV R{rd}, #{imm8}")
        
        elif opcode == 1:  # CMP
            result = rd_value - imm8
            self.update_flags(result, rd_value, imm8, True)
            if self.debug_mode:
                print(f"    -> CMP R{rd}, #{imm8}")
        
        elif opcode == 2:  # ADD
            result = rd_value + imm8
            self.set_register(rd, result)
            self.update_flags(result, rd_value, imm8, False)
            if self.debug_mode:
                print(f"    -> ADD R{rd}, #{imm8}")
        
        elif opcode == 3:  # SUB
            result = rd_value - imm8
            self.set_register(rd, result)
            self.update_flags(result, rd_value, imm8, True)
            if self.debug_mode:
                print(f"    -> SUB R{rd}, #{imm8}")
        
        return True
    
    def execute_thumb_alu_ops(self, instruction):
        """Execute Format 4: ALU operations"""
        opcode = (instruction >> 6) & 0xF    # ALU operation
        rs = (instruction >> 3) & 0x7        # Source register
        rd = instruction & 0x7               # Destination register
        
        rd_value = self.get_register(rd)
        rs_value = self.get_register(rs)
        
        if opcode == 0:  # AND
            result = rd_value & rs_value
            self.set_register(rd, result)
            self.update_flags(result)
            if self.debug_mode:
                print(f"    -> AND R{rd}, R{rs}")
        
        elif opcode == 1:  # EOR
            result = rd_value ^ rs_value
            self.set_register(rd, result)
            self.update_flags(result)
            if self.debug_mode:
                print(f"    -> EOR R{rd}, R{rs}")
        
        elif opcode == 10:  # CMP
            result = rd_value - rs_value
            self.update_flags(result, rd_value, rs_value, True)
            if self.debug_mode:
                print(f"    -> CMP R{rd}, R{rs}")
        
        elif opcode == 12:  # ORR
            result = rd_value | rs_value
            self.set_register(rd, result)
            self.update_flags(result)
            if self.debug_mode:
                print(f"    -> ORR R{rd}, R{rs}")
        
        else:
            if self.debug_mode:
                print(f"    -> Unimplemented ALU operation: {opcode}")
            return True  # Continue execution for now
        
        return True
    
    def execute_thumb_hi_reg_ops(self, instruction):
        """Execute Format 5: Hi register operations/branch exchange"""
        opcode = (instruction >> 8) & 0x3    # Operation type
        h1 = (instruction >> 7) & 0x1        # Hi reg flag for destination
        h2 = (instruction >> 6) & 0x1        # Hi reg flag for source
        rs_hs = (instruction >> 3) & 0x7     # Source register (low 3 bits)
        rd_hd = instruction & 0x7            # Destination register (low 3 bits)
        
        # Calculate full register numbers (can access R8-R15)
        rs = rs_hs + (h2 << 3)
        rd = rd_hd + (h1 << 3)
        
        rs_value = self.get_register(rs)
        rd_value = self.get_register(rd)
        
        if opcode == 0:  # ADD
            result = rd_value + rs_value
            self.set_register(rd, result)
            # Note: Hi register ADD doesn't update flags
            if self.debug_mode:
                print(f"    -> ADD R{rd}, R{rs}")
        
        elif opcode == 1:  # CMP
            result = rd_value - rs_value
            self.update_flags(result, rd_value, rs_value, True)
            if self.debug_mode:
                print(f"    -> CMP R{rd}, R{rs}")
        
        elif opcode == 2:  # MOV
            self.set_register(rd, rs_value)
            # Note: Hi register MOV doesn't update flags unless Rd is R8-R14
            if self.debug_mode:
                print(f"    -> MOV R{rd}, R{rs}")
        
        elif opcode == 3:  # BX/BLX - Branch and Exchange (mode switch!)
            target_address = rs_value
            
            # Bit 0 determines new mode (0=ARM, 1=Thumb)
            new_thumb_mode = bool(target_address & 0x1)
            target_address &= 0xFFFFFFFE  # Clear bit 0
            
            if h1:  # BLX - Branch with Link and Exchange
                self.set_register(14, self.get_next_pc() | 0x1)  # Set LR with Thumb bit
                if self.debug_mode:
                    print(f"    -> BLX R{rs} (mode switch)")
            else:   # BX - Branch and Exchange
                if self.debug_mode:
                    print(f"    -> BX R{rs} (return/mode switch)")
            
            # Perform mode switch and branch
            self.set_processor_mode(new_thumb_mode)
            self.pc = target_address
            
            self.branch_predictions += 1
        
        return True
    
    def execute_thumb_conditional_branch(self, instruction):
        """Execute Format 16: Conditional branch"""
        cond = (instruction >> 8) & 0xF      # Condition code
        offset8 = instruction & 0xFF          # 8-bit signed offset
        
        # Check condition
        if not self.check_condition(cond):
            if self.debug_mode:
                print(f"    -> Branch condition not met")
            return True
        
        # Sign extend 8-bit to 32-bit
        if offset8 & 0x80:
            offset8 = offset8 - 0x100
        
        # Branch target (halfword aligned + pipeline offset)
        branch_target = self.pc + (offset8 * 2) + 4
        self.pc = branch_target & 0xFFFFFFFE
        
        if self.debug_mode:
            print(f"    -> Branch taken to 0x{self.pc:04X}")
        
        self.branch_predictions += 1
        return True
    
    def execute_thumb_unconditional_branch(self, instruction):
        """Execute Format 18: Unconditional branch"""
        offset11 = instruction & 0x7FF       # 11-bit signed offset
        
        # Sign extend 11-bit to 32-bit
        if offset11 & 0x400:
            offset11 = offset11 - 0x800
        
        # Branch target (halfword aligned + pipeline offset)
        branch_target = self.pc + (offset11 * 2) + 4
        self.pc = branch_target & 0xFFFFFFFE
        
        if self.debug_mode:
            print(f"    -> Branch to 0x{self.pc:04X}")
        
        self.branch_predictions += 1
        return True
    
    def execute_thumb_swi(self, instruction):
        """Execute Format 17: Software Interrupt"""
        imm8 = instruction & 0xFF
        
        if self.debug_mode:
            print(f"    -> SWI #{imm8}")
        
        # For simulation, just print the SWI call
        print(f"📞 Software Interrupt: SWI #{imm8}")
        
        return True
    
    # =================================================================
    # ENHANCED EXECUTION LOOP
    # =================================================================
    
    def run_mixed_program(self, debug=True, step_by_step=False):
        """Run mixed ARM/Thumb program"""
        if not self.instructions:
            print("❌ No program loaded")
            return
        
        print(f"\n{'='*70}")
        print("STARTING MIXED ARM/THUMB EXECUTION")
        print(f"{'='*70}")
        
        self.debug_mode = debug
        self.step_mode = step_by_step
        self.pc = 0
        self.cycle_count = 0
        self.running = True
        
        # Reset statistics
        self.arm_cycles = 0
        self.thumb_cycles = 0
        self.mode_switches = 0
        self.branch_predictions = 0
        
        # Show initial state
        if debug:
            self.print_enhanced_state()
        
        while self.running and self.cycle_count < self.max_cycles:
            # Find current instruction by PC
            current_instruction = None
            current_mode = None
            instruction_index = -1
            
            for i, addr in enumerate(self.instruction_addresses):
                if addr == self.pc:
                    current_instruction = self.instructions[i]
                    current_mode = self.instruction_modes[i]
                    instruction_index = i
                    break
            
            if current_instruction is None:
                print(f"\n✅ Program ended - PC: 0x{self.pc:04X}")
                break
            
            # Ensure we're in correct mode for this instruction
            expected_thumb = (current_mode == 'THUMB')
            if self.thumb_mode != expected_thumb:
                if debug:
                    print(f"⚠️ Mode correction: PC expects {current_mode}")
                self.set_processor_mode(expected_thumb)
            
            if debug:
                print(f"\n📍 PC: 0x{self.pc:04X} | Cycle {self.cycle_count + 1} | Mode: {self.get_current_mode_string()}")
                
                # Show instruction being executed
                if current_mode == 'ARM':
                    decoded = self.enhanced_