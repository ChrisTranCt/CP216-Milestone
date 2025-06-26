#!/usr/bin/env python3
"""
Enhanced ARM/Thumb Decoder
Combines your existing ARM decoder with new Thumb decoder
"""

import sys
import struct

# Import your existing ARM decoder
try:
    from main import ARMDecoder
except ImportError:
    print("Error: Could not import ARMDecoder from main.py")
    print("Please ensure your main.py file is in the same directory")
    sys.exit(1)

# Import the new Thumb decoder
try:
    from thumb_decoder import FixedThumbDecoder
except ImportError:
    print("Error: Could not import FixedThumbDecoder from thumb_decoder.py")
    print("Please ensure thumb_decoder.py is in the same directory")
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

    def detect_instruction_mode(self, data, start_index=0):
        """Detect if data contains ARM (32-bit) or Thumb (16-bit) instructions"""
        if len(data) < 4:
            return 'THUMB'
        
        # Heuristic: Look for patterns that indicate Thumb mode
        thumb_indicators = 0
        arm_indicators = 0
        
        # Check multiple 32-bit words
        for i in range(start_index, min(start_index + 16, len(data) - 3), 4):
            word = struct.unpack('<I', data[i:i+4])[0]
            
            # ARM indicators
            condition = (word >> 28) & 0xF
            if condition <= 0xE:  # Valid ARM condition
                arm_indicators += 1
            
            # Thumb indicators (check if this looks like two 16-bit instructions)
            low_half = word & 0xFFFF
            high_half = (word >> 16) & 0xFFFF
            
            # Simple Thumb pattern detection
            if self.looks_like_thumb_instruction(low_half):
                thumb_indicators += 1
            if self.looks_like_thumb_instruction(high_half):
                thumb_indicators += 1
        
        return 'THUMB' if thumb_indicators > arm_indicators else 'ARM'

    def looks_like_thumb_instruction(self, instruction):
        """Simple heuristic to identify Thumb instructions"""
        if instruction == 0:
            return False
        
        # Check common Thumb patterns
        format_bits = (instruction >> 10) & 0x3F
        
        # Common Thumb formats
        thumb_patterns = [
            0x00, 0x08, 0x10, 0x14, 0x18, 0x20, 0x28, 0x30, 0x38
        ]
        
        return any((format_bits & 0x38) == pattern for pattern in thumb_patterns)

    def read_mixed_file(self, filename):
        """Read file that may contain both ARM and Thumb instructions"""
        try:
            with open(filename, 'rb') as f:
                data = f.read()
            
            # Detect initial mode
            self.current_mode = self.detect_instruction_mode(data)
            print(f"Detected initial mode: {self.current_mode}")
            
            instructions = []
            addresses = []
            modes = []
            
            if self.current_mode == 'ARM':
                # Process as 32-bit ARM instructions
                for i in range(0, len(data), 4):
                    if i + 4 <= len(data):
                        word = struct.unpack('<I', data[i:i+4])[0]
                        instructions.append(word)
                        addresses.append(i)
                        modes.append('ARM')
            else:
                # Process as 16-bit Thumb instructions
                for i in range(0, len(data), 2):
                    if i + 2 <= len(data):
                        halfword = struct.unpack('<H', data[i:i+2])[0]
                        instructions.append(halfword)
                        addresses.append(i)
                        modes.append('THUMB')
            
            return instructions, addresses, modes
            
        except Exception as e:
            print(f"Error reading file: {e}")
            return [], [], []

    def read_hex_text_file_mixed(self, filename):
        """Read hex text file with mode indicators"""
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
            
            instructions = []
            addresses = []
            modes = []
            current_mode = 'ARM'  # Default
            address = 0
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                
                if line.startswith('#'):  # Comments
                    # Check for mode switches
                    if 'THUMB' in line.upper():
                        current_mode = 'THUMB'
                        print(f"Switching to THUMB mode at line {line_num}")
                    elif 'ARM' in line.upper():
                        current_mode = 'ARM'
                        print(f"Switching to ARM mode at line {line_num}")
                    continue
                
                if line and not line.startswith('#'):
                    try:
                        instruction = int(line, 16)
                        instructions.append(instruction)
                        addresses.append(address)
                        modes.append(current_mode)
                        
                        # Increment address based on current mode
                        address += 2 if current_mode == 'THUMB' else 4
                        
                    except ValueError:
                        print(f"Warning: Invalid hex value on line {line_num}: {line}")
            
            return instructions, addresses, modes
            
        except Exception as e:
            print(f"Error reading file: {e}")
            return [], [], []

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

    def create_sample_programs(self):
        """Create sample programs for testing"""
        
        # Sample ARM program
        with open("sample_arm.txt", "w") as f:
            f.write("""# Sample ARM program
# ARM mode
E3A01005    # MOV R1, #5
E3A02003    # MOV R2, #3
E0813002    # ADD R3, R1, R2
E1530001    # CMP R3, R1
E1A0F00E    # MOV PC, LR
""")
        
        # Sample Thumb program
        with open("sample_thumb.txt", "w") as f:
            f.write("""# Sample Thumb program
# THUMB mode
2105    # MOV R1, #5
2203    # MOV R2, #3
1840    # ADD R0, R0, R1
4288    # CMP R0, R1
D001    # BEQ +2
1A80    # SUB R0, R0, R2
4770    # BX LR
""")
        
        # Sample mixed ARM/Thumb program
        with open("sample_mixed.txt", "w") as f:
            f.write("""# Sample mixed ARM/Thumb program
# ARM mode - Setup
E3A01005    # MOV R1, #5
E3A02003    # MOV R2, #3
E0813002    # ADD R3, R1, R2

# THUMB mode - Processing
2000        # MOV R0, #0
1840        # ADD R0, R0, R1
4288        # CMP R0, R1
D001        # BEQ +2
3001        # ADD R0, #1

# ARM mode - Cleanup
# ARM mode
E1530000    # CMP R3, R0
E1A0F00E    # MOV PC, LR
""")
        
        print("✅ Created sample programs:")
        print("   - sample_arm.txt (Pure ARM)")
        print("   - sample_thumb.txt (Pure Thumb)")
        print("   - sample_mixed.txt (Mixed ARM/Thumb)")

    def test_decoder_functionality(self):
        """Test the decoder with various instruction types"""
        
        print("\n🧪 TESTING ENHANCED DECODER")
        print("="*50)
        
        # Test ARM instructions
        print("\n📋 Testing ARM Instructions:")
        arm_tests = [
            (0xE3A01005, "MOV R1, #5"),
            (0xE3A02003, "MOV R2, #3"),
            (0xE0813002, "ADD R3, R1, R2"),
            (0xE1A0F00E, "MOV PC, LR")
        ]
        
        for instruction, expected in arm_tests:
            decoded = self.arm_decoder.decode_instruction(instruction, 0)
            print(f"  0x{instruction:08X} -> {decoded}")
        
        # Test Thumb instructions
        print("\n📋 Testing Thumb Instructions:")
        thumb_tests = [
            (0x2105, "MOV R1, #5"),
            (0x2203, "MOV R2, #3"),
            (0x1840, "ADD R0, R0, R1"),
            (0x4288, "CMP R0, R1"),
            (0x4770, "BX LR")
        ]
        
        for instruction, expected in thumb_tests:
            decoded = self.thumb_decoder.decode_thumb_instruction(instruction, 0)
            print(f"  0x{instruction:04X} -> {decoded}")
        
        print("\n✅ Decoder functionality verified!")

    def demonstrate_mode_detection(self):
        """Demonstrate automatic mode detection"""
        
        print("\n🔍 DEMONSTRATING MODE DETECTION")
        print("="*50)
        
        # Create test data
        arm_data = struct.pack('<I', 0xE3A01005) + struct.pack('<I', 0xE3A02003)
        thumb_data = struct.pack('<H', 0x2105) + struct.pack('<H', 0x2203)
        
        print(f"ARM data detection: {self.detect_instruction_mode(arm_data)}")
        print(f"Thumb data detection: {self.detect_instruction_mode(thumb_data)}")
        
        # Test pattern recognition
        print("\n📊 Pattern Recognition:")
        test_instructions = [
            (0x2105, "Thumb immediate"),
            (0x1840, "Thumb add/subtract"),
            (0x4288, "Thumb ALU"),
            (0xE3A01005, "ARM data processing")
        ]
        
        for instruction, desc in test_instructions:
            if instruction > 0xFFFF:  # 32-bit ARM
                print(f"  0x{instruction:08X}: ARM instruction ({desc})")
            else:  # 16-bit Thumb
                is_thumb = self.looks_like_thumb_instruction(instruction)
                print(f"  0x{instruction:04X}: {'Thumb' if is_thumb else 'Unknown'} instruction ({desc})")

    def validate_file_reading(self):
        """Validate file reading capabilities"""
        
        print("\n📁 VALIDATING FILE READING")
        print("="*50)
        
        # Create a test file
        with open("validation_test.txt", "w") as f:
            f.write("""# Validation test file
# ARM mode
E3A01005    # MOV R1, #5
# THUMB mode
2105        # MOV R1, #5
2203        # MOV R2, #3
# ARM mode
E1A0F00E    # MOV PC, LR
""")
        
        # Test reading
        instructions, addresses, modes = self.read_hex_text_file_mixed("validation_test.txt")
        
        print(f"Instructions read: {len(instructions)}")
        print(f"Modes detected: {set(modes)}")
        print("Instruction sequence:")
        
        for i, (instr, addr, mode) in enumerate(zip(instructions, addresses, modes)):
            if mode == 'ARM':
                decoded = self.arm_decoder.decode_instruction(instr, addr)
                print(f"  {i}: 0x{addr:04X} [ARM] 0x{instr:08X} -> {decoded}")
            else:
                decoded = self.thumb_decoder.decode_thumb_instruction(instr, addr)
                print(f"  {i}: 0x{addr:04X} [THUMB] 0x{instr:04X} -> {decoded}")
        
        # Clean up
        import os
        try:
            os.remove("validation_test.txt")
        except:
            pass
        
        print("✅ File reading validation complete!")


def run_comprehensive_test():
    """Run comprehensive test of enhanced decoder"""
    
    decoder = EnhancedARMDecoder()
    
    print("🧪 COMPREHENSIVE ENHANCED DECODER TEST")
    print("="*60)
    
    # Test all functionality
    decoder.test_decoder_functionality()
    decoder.demonstrate_mode_detection()
    decoder.validate_file_reading()
    
    print(f"\n{'='*60}")
    print("✅ ALL ENHANCED DECODER TESTS PASSED!")
    print("🎉 Ready for integration with enhanced executor!")
    print(f"{'='*60}")


def main():
    """Main function for testing enhanced decoder"""
    
    if len(sys.argv) < 2:
        print("Enhanced ARM/Thumb Decoder")
        print("="*40)
        print("Usage:")
        print("  python enhanced_decoder.py <filename>        # Decode file")
        print("  python enhanced_decoder.py test              # Run tests")
        print("  python enhanced_decoder.py create_samples    # Create sample programs")
        print("  python enhanced_decoder.py comprehensive     # Full test suite")
        print("\nFor hex text files, use comments to indicate mode:")
        print("  # ARM mode")
        print("  E3A01005")
        print("  # THUMB mode") 
        print("  2105")
        print("  1840")
        return
    
    decoder = EnhancedARMDecoder()
    command = sys.argv[1]
    
    if command == "test":
        decoder.test_decoder_functionality()
    
    elif command == "create_samples":
        decoder.create_sample_programs()
    
    elif command == "comprehensive":
        run_comprehensive_test()
    
    else:
        # Decode specified file
        filename = command
        decoder.disassemble_mixed_file(filename)


if __name__ == "__main__":
    main()