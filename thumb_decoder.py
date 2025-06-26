# ================================================================
# FILE: thumb_decoder.py (NEW MODULE)
# ================================================================
#!/usr/bin/env python3
"""
Thumb Decoder Module
Provides 16-bit Thumb instruction decoding capabilities
"""

class FixedThumbDecoder:
    """Thumb instruction decoder with corrected format detection"""
    
    def __init__(self):
        # Thumb register names (same as ARM)
        self.registers = {
            0: 'R0', 1: 'R1', 2: 'R2', 3: 'R3',
            4: 'R4', 5: 'R5', 6: 'R6', 7: 'R7',
            8: 'R8', 9: 'R9', 10: 'R10', 11: 'R11',
            12: 'R12', 13: 'SP', 14: 'LR', 15: 'PC'
        }
        
        # Condition codes for conditional branches
        self.conditions = {
            0b0000: 'EQ', 0b0001: 'NE', 0b0010: 'CS', 0b0011: 'CC',
            0b0100: 'MI', 0b0101: 'PL', 0b0110: 'VS', 0b0111: 'VC',
            0b1000: 'HI', 0b1001: 'LS', 0b1010: 'GE', 0b1011: 'LT',
            0b1100: 'GT', 0b1101: 'LE', 0b1110: 'AL', 0b1111: 'NV'
        }

    def decode_thumb_instruction(self, instruction, address=0):
        """Main Thumb instruction decoder - fixed format detection"""
        # [Implementation from the previous artifact]
        pass

# ================================================================
# FILE: enhanced_decoder.py (NEW MODULE) 
# ================================================================
#!/usr/bin/env python3
"""
Enhanced ARM/Thumb Decoder
Combines ARM and Thumb decoding capabilities
"""

import sys
import struct

# Import your existing ARM decoder
try:
    from main import ARMDecoder
except ImportError:
    print("Error: Could not import ARMDecoder from main.py")
    sys.exit(1)

# Import the new Thumb decoder
try:
    from thumb_decoder import FixedThumbDecoder
except ImportError:
    print("Error: Could not import FixedThumbDecoder from thumb_decoder.py")
    sys.exit(1)


class EnhancedARMDecoder:
    """Enhanced decoder supporting both ARM and Thumb modes"""
    
    def __init__(self):
        # Use composition - your existing code unchanged!
        self.arm_decoder = ARMDecoder()           # Your existing ARM decoder
        self.thumb_decoder = FixedThumbDecoder()  # New Thumb decoder
        
        # Mode tracking
        self.current_mode = 'ARM'
        self.mode_history = []

    def disassemble_mixed_file(self, filename):
        """Disassemble file with both ARM and Thumb instructions"""
        print(f"Reading mixed ARM/Thumb code from: {filename}")
        print("=" * 60)
        
        if filename.endswith('.txt'):
            instructions, addresses, modes = self.read_hex_text_file_mixed(filename)
        else:
            instructions, addresses, modes = self.read_mixed_file(filename)
        
        if not instructions:
            print("No instructions found.")
            return
        
        print(f"Found {len(instructions)} instructions")
        print()
        
        for i, (instruction, address, mode) in enumerate(zip(instructions, addresses, modes)):
            if mode == 'ARM':
                # Use your existing ARM decoder - no changes needed!
                decoded = self.arm_decoder.decode_instruction(instruction, address)
                print(f"0x{address:04X}: 0x{instruction:08X}  {decoded} [ARM]")
            else:  # THUMB
                # Use new Thumb decoder
                decoded = self.thumb_decoder.decode_thumb_instruction(instruction, address)
                print(f"0x{address:04X}: 0x{instruction:04X}      {decoded} [THUMB]")

    def read_hex_text_file_mixed(self, filename):
        """Read hex text file with mode indicators"""
        # [Implementation for reading mixed mode files]
        pass

# ================================================================
# FILE: usage_example.py (EXAMPLE OF HOW TO USE)
# ================================================================
#!/usr/bin/env python3
"""
Example of how to use the enhanced decoder
"""

from enhanced_decoder import EnhancedARMDecoder

def main():
    # Create enhanced decoder (uses both your ARM decoder and new Thumb decoder)
    decoder = EnhancedARMDecoder()
    
    # Test with your existing ARM programs (should work unchanged)
    print("Testing existing ARM program:")
    decoder.disassemble_mixed_file("your_existing_arm_program.txt")
    
    # Test with new Thumb programs
    print("\nTesting new Thumb program:")
    decoder.disassemble_mixed_file("thumb_program.txt")
    
    # Test with mixed ARM/Thumb programs
    print("\nTesting mixed program:")
    decoder.disassemble_mixed_file("mixed_program.txt")

if __name__ == "__main__":
    main()

# ================================================================
# WHAT STAYS THE SAME
# ================================================================

# main.py - YOUR EXISTING FILE - NO CHANGES NEEDED!
# - ARMDecoder class stays exactly the same
# - All your existing ARM decoding logic unchanged
# - Your existing test programs still work

# ARM_Executor.py - YOUR EXISTING FILE - NO CHANGES NEEDED!  
# - ARMExecutor class stays exactly the same
# - All your existing ARM execution logic unchanged
# - Your existing execution tests still work

# ================================================================
# WHAT'S NEW
# ================================================================

# thumb_decoder.py - NEW MODULE
# - FixedThumbDecoder class for 16-bit Thumb instructions
# - Completely separate from your ARM code
# - Can be developed and tested independently

# enhanced_decoder.py - NEW MODULE  
# - EnhancedARMDecoder that uses BOTH decoders
# - Handles mode detection and switching
# - Provides unified interface for mixed programs

# enhanced_executor.py - NEW MODULE (coming next)
# - EnhancedARMExecutor that can execute both ARM and Thumb
# - Inherits from your existing ARMExecutor
# - Adds Thumb execution capabilities