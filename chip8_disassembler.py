"""
Disassembler for Chip 8 programs
"""
from typing import BinaryIO, Tuple

class Chip8Disassembler:

    def __init__(self, chip_file: BinaryIO):
        """Chip8 disassembler

        Chip file is BinaryIO stream
        """
        self.chip_file = chip_file.read()
    
    def disassemble(self):
        """Used to disassemble the read chip 8 file

        According references Chip 8 has 36 different instructions i.e. opcodes
        
        All opcodes are 2 bytes long and are stored in network byte order/big endian/most significant byte first xd
        """
        for i in range(0, len(self.chip_file), 2):
            # increment of 2 since each opcode is 2 byte long
            self.opcode(i)

    def opcode_switch(self, type_of: int, code: Tuple[bytes]):
        if type_of == 0:
            second_nibble = code[0] & 0xf
            if second_nibble == 0xe:
                if code[1] & 0xf == 0x0: print("CLS")
                else: print("RET")
            else: print(f"SYS {code[0] & 0xf}{code[1]}")
        elif type_of == 0x1: print(f"JP {code[0] & 0xf}{code[1]}")
        elif type_of == 0x2: print(f"CALL {code[0] & 0xf}{code[1]}")
        elif type_of == 0x3: print(f"SE V{code[0] & 0xf}, {code[1]}")
        elif type_of == 0x4: print(f"SNE V{code[0] & 0xf}, {code[1]}")
        elif type_of == 0x5: print(f"SE V{code[0] & 0xf}, V{code[1] >> 4}")
        elif type_of == 0x6: print(f"LD V{code[0] & 0xf}, {code[1]}")
        elif type_of == 0x7: print(f"ADD V{code[0] & 0xf}, {code[1]}")
        elif type_of == 0x8: 
            last_nibble = code[1] & 0xf
            if last_nibble == 0x0:
                print(f"LD V{code[0] & 0xf}, V{code[1] >> 4}")
            elif last_nibble == 0x1:
                print(f"OR V{code[0] & 0xf}, V{code[1] >> 4}")
            elif last_nibble == 0x2:
                print(f"AND V{code[0] & 0xf}, V{code[1] >> 4}")
            elif last_nibble == 0x3:
                print(f"XOR V{code[0] & 0xf}, V{code[1] >> 4}")
            elif last_nibble == 0x4:
                print(f"ADD V{code[0] & 0xf}, V{code[1] >> 4}")
            elif last_nibble == 0x5:
                print(f"SUB V{code[0] & 0xf}, V{code[1] >> 4}")
            elif last_nibble == 0x6:
                print(f"SHR V{code[0] & 0xf}, V{code[1] >> 4}")
            elif last_nibble == 0x7:
                print(f"SUBN V{code[0] & 0xf}, V{code[1] >> 4}")
            elif last_nibble == 0xE:
                print(f"SHL V{code[0] & 0xf}, V{code[1] >> 4}")
        elif type_of == 0x9: print(f"SNE V{code[0] & 0xf}, V{code[1] >> 4}")
        elif type_of == 0xa: print(f"LD I, {code[0] & 0xf}{code[1]}")
        elif type_of == 0xb: print(f"JP V0, {code[0] & 0xf}{code[1]}")
        elif type_of == 0xc: print(f"RND V{code[0] & 0xf}, {code[1]}")
        elif type_of == 0xd: print(f"DRW V{code[0] & 0xf}, V{code[1] >> 4}, {code[1] & 0xf}")
        elif type_of == 0xe:
            if code[1] == 0x9e:
                print(f"SKP V{code[0] & 0xf}")
            elif code[1] == 0xa1:
                print(f"SKNP V{code[0] & 0xf}")
        elif type_of == 0xf:
            if code[1] == 0x07:
                print(f"LD V{code[0] & 0xf}, DT")
            elif code[1] == 0x0a:
                print(f"LD V{code[0] & 0xf}, K")
            elif code[1] == 0x15:
                print(f"LD DT, V{code[0] & 0xf}")
            elif code[1] == 0x18:
                print(f"LD ST, V{code[0] & 0xf}")
            elif code[1] == 0x1e:
                print(f"ADD I, V{code[0] & 0xf}")
            elif code[1] == 0x29:
                print(f"LD I, V{code[0] & 0xf}")
            elif code[1] == 0x33:
                print(f"LD BCD, V{code[0] & 0xf}")
            elif code[1] == 0x55:
                print(f"LD [I], V{code[0] & 0xf}")
            elif code[1] == 0x65:
                print(f"LD V{code[0] & 0xf}, [I]")


    def opcode(self, pc: int):
        code = code_first, code_second = self.chip_file[pc], self.chip_file[pc+1]
        # extract first nibble from code
        first_nibble = code_first >> 4
        print(f"{pc+0x200:04x} {code_first:02x} {code_second:02x} ", end = '')
        self.opcode_switch(first_nibble, code)


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2:
        with open(sys.argv[1], 'rb') as chip_file:
            Chip8Disassembler(chip_file).disassemble()
