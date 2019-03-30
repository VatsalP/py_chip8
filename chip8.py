import random

import pygame
from pygame.locals import *


class Chip8:

    keys = {
        pygame.K_1: 0x0,
        pygame.K_2: 0x1,
        pygame.K_3: 0x2,
        pygame.K_4: 0x3,
        pygame.K_q: 0x4,
        pygame.K_w: 0x5,
        pygame.K_e: 0x6,
        pygame.K_r: 0x7,
        pygame.K_a: 0x8,
        pygame.K_s: 0x9,
        pygame.K_d: 0xA,
        pygame.K_f: 0xB,
        pygame.K_z: 0xC,
        pygame.K_x: 0xD,
        pygame.K_c: 0xE,
        pygame.K_v: 0xF,
    }
    keys_rev = {v: k for k, v in keys.items()}
    font_list = [
        [0xF0, 0x90, 0x90, 0x90, 0xF0],  # 0
        [0x20, 0x60, 0x20, 0x20, 0x70],  # 1
        [0xF0, 0x10, 0xF0, 0x80, 0xF0],  # 2
        [0xF0, 0x10, 0xF0, 0x10, 0xF0],  # 3
        [0x90, 0x90, 0xF0, 0x10, 0x10],  # 4
        [0xF0, 0x80, 0xF0, 0x10, 0xF0],  # 5
        [0xF0, 0x80, 0xF0, 0x90, 0xF0],  # 6
        [0xF0, 0x10, 0x20, 0x40, 0x40],  # 7
        [0xF0, 0x90, 0xF0, 0x90, 0xF0],  # 8
        [0xF0, 0x90, 0xF0, 0x10, 0xF0],  # 9
        [0xF0, 0x90, 0xF0, 0x90, 0x90],  # a
        [0xE0, 0x90, 0xE0, 0x90, 0xE0],  # b
        [0xF0, 0x80, 0x80, 0x80, 0xF0],  # c
        [0xE0, 0x90, 0x90, 0x90, 0xE0],  # d
        [0xF0, 0x80, 0xF0, 0x80, 0xF0],  # e
        [0xF0, 0x80, 0xF0, 0x80, 0x80],  # f
    ]

    def __init__(self, chip_file):
        """Chip8 interpreter

        Chip file is BinaryIO stream of chip program
        
        Chip 8 Memory layout using wikipedia article as reference:
        4096 (0x1000) total mem
        first 512 (0x200) were for interpreter itself, in our case font will go there
        chip 8 programs start at 0x200
        stack resides at 0xEA0-0xEFF
        and uppermost 256 bytes (0xF00 - 0xFFF) were for display
        256*8 == 64*32 == 2048 bits
        """
        self.chip_file = chip_file.read()
        self.state = {
            "v": [0 for _ in range(16)],
            "i": 0,
            "delay": 0,
            "sound": 0,
            "pc": 0x200,
            "sp": 0xEA0,
            "memory": [0 for _ in range(4096)],
            "display": [[0 for _ in range(64)] for _ in range(32)],
        }
        self.opcode_map = {
            0x0: {0x0: self._00E0, 0xE: self._00EE},
            0x1: self._1NNN,
            0x2: self._2NNN,
            0x3: self._3XNN,
            0x4: self._4XNN,
            0x5: self._5XY0,
            0x6: self._6XNN,
            0x7: self._7XNN,
            0x8: {
                0x0: self._8XY0,
                0x1: self._8XY1,
                0x2: self._8XY2,
                0x3: self._8XY3,
                0x4: self._8XY4,
                0x5: self._8XY5,
                0x6: self._8XY6,
                0x7: self._8XY7,
                0xE: self._8XYE,
            },
            0x9: self._9XY0,
            0xA: self._ANNN,
            0xB: self._BNNN,
            0xC: self._CXNN,
            0xD: self._DXYN,
            0xE: {0xE: self._EX9E, 0x1: self._EXA1},
            0xF: {
                0x07: self._FX07,
                0x0A: self._FX0A,
                0x15: self._FX15,
                0x18: self._FX18,
                0x1E: self._FX1E,
                0x29: self._FX29,
                0x33: self._FX33,
                0x55: self._FX55,
                0x65: self._FX65,
            },
        }
        self.set_font(self.font_list)
        self.map_code_to_mem(self.chip_file, len(self.chip_file))

    def set_font(self, font_list):
        i = 0
        for sprite in font_list:
            for byte in sprite:
                self.state["memory"][i] = byte
                i += 1

    def map_code_to_mem(self, code, code_len):
        for address in range(0x200, code_len + 0x200):
            self.state["memory"][address] = code[address - 0x200]

    def get_memory(self):
        return self.state["memory"]

    def get_display(self):
        return self.state["display"]

    def fetch_next_opcode(self, pressed_keys):
        opcode = (
            self.state["memory"][self.state["pc"]] << 0x8
            | self.state["memory"][self.state["pc"] + 1]
        )
        self.state["pc"] += 2
        print(f"{self.state['pc']:04x} {opcode >> 0x8:02x} {opcode & 0xff:02x}")
        print(
            f"State: pc: {self.state['pc']} i: {self.state['i']} v: {self.state['v']}"
        )
        self.opcode_switch(opcode, pressed_keys)
        # reduce timers if set
        if self.state["delay"] > 0:
            self.state["delay"] -= 1
        if self.state["sound"] > 0:
            self.state["delay"] -= 1

    def opcode_switch(self, opcode, pressed_keys):
        self.opcode = opcode
        self.pressed_keys = pressed_keys
        first_nibble = (opcode & 0xF000) >> 0xC
        if first_nibble == 0xF:
            function = self.opcode_map[first_nibble].get(opcode & 0x00FF)
        elif first_nibble in [0x0, 0x8, 0xE]:
            function = self.opcode_map[first_nibble].get(opcode & 0x000F)
        else:
            function = self.opcode_map.get(first_nibble)
        if function:
            function()
        else:
            print(f"{self.opcode} not implemented.")

    def _00E0(self):
        """ Clear the Screen
        """
        for y in range(32):
            for x in range(64):
                self.state["display"][y][x] = 0

    def _00EE(self):
        """Return from a subroutine
        """
        self.state["sp"] -= 1
        self.state["pc"] = self.state["memory"][self.state["sp"]]

    def _1NNN(self):
        """Jump to address NNN
        """
        addr = self.opcode & 0x0FFF
        self.state["pc"] = addr

    def _2NNN(self):
        """Execute subroutine starting at address NNN
        """
        self.state["memory"][self.state["sp"]] = self.state["pc"]
        self.state["sp"] += 1
        self.state["pc"] = self.opcode & 0x0FFF

    def _3XNN(self):
        """Skip the following instruction if the value of register VX equals NN
        """
        x = (self.opcode & 0x0F00) >> 0x8
        value = self.state["v"][x]
        if value == (self.opcode & 0xFF):
            self.state["pc"] += 2

    def _4XNN(self):
        """
            Skip the following instruction if the value of register VX
            is not equal to NN
        """
        x = (self.opcode & 0x0F00) >> 0x8
        value = self.state["v"][x]
        if value != (self.opcode & 0xFF):
            self.state["pc"] += 2

    def _5XY0(self):
        """
            Skip the following instruction if the value of register VX is equal to the value of register VY
        """
        x = (self.opcode & 0x0F00) >> 0x8
        y = (self.opcode & 0x00F0) >> 0x4
        skip = self.state["v"][x] == self.state["v"][y]
        if skip:
            self.state["pc"] += 2

    def _6XNN(self):
        """ Store number NN in register VX
        """
        x = (self.opcode & 0x0F00) >> 0x8
        self.state["v"][x] = self.opcode & 0x00FF

    def _7XNN(self):
        """Add the value NN to register VX
        """
        x = (self.opcode & 0x0F00) >> 0x8
        self.state["v"][x] += self.opcode & 0x00FF
        self.state["v"][x] %= 256

    def _8XY0(self):
        """Store the value of register VY in register VX
        """
        x = (self.opcode & 0x0F00) >> 0x8
        y = (self.opcode & 0x00F0) >> 0x4
        self.state["v"][x] = self.state["v"][y]

    def _8XY1(self):
        """Set VX to VX OR VY
        """
        x = (self.opcode & 0x0F00) >> 0x8
        y = (self.opcode & 0x00F0) >> 0x4
        self.state["v"][x] |= self.state["v"][y]

    def _8XY2(self):
        """Set VX to VX AND VY
        """
        x = (self.opcode & 0x0F00) >> 0x8
        y = (self.opcode & 0x00F0) >> 0x4
        self.state["v"][x] &= self.state["v"][y]

    def _8XY3(self):
        """Set VX to VX XOR VY
        """
        x = (self.opcode & 0x0F00) >> 0x8
        y = (self.opcode & 0x00F0) >> 0x4
        self.state["v"][x] ^= self.state["v"][y]

    def _8XY4(self):
        """
            Add the value of register VY to register VX

            Set VF to 01 if a carry occurs
            Set VF to 00 if a carry does not occur
        """
        x = (self.opcode & 0x0F00) >> 0x8
        y = (self.opcode & 0x00F0) >> 0x4
        self.state["v"][x] += self.state["v"][y]
        if self.state["v"][x] > 255:
            self.state["v"][0xF] = 1
            self.state["v"][x] %= 256
        else:
            self.state["v"][0xF] = 0

    def _8XY5(self):
        """
            Subtract the value of register VY from register VX

            Set VF to 00 if a borrow occurs
            Set VF to 01 if a borrow does not occur
        """
        x = (self.opcode & 0x0F00) >> 0x8
        y = (self.opcode & 0x00F0) >> 0x4
        self.state["v"][x] -= self.state["v"][y]
        if self.state["v"][x] < 0:
            self.state["v"][0xF] = 0
            self.state["v"][x] += 256
        else:
            self.state["v"][0xF] = 1

    def _8XY6(self):
        """
            Store the value of register VY shifted right one bit in register VX

            Set register VF to the least significant bit prior to the shift
        """
        x = (self.opcode & 0x0F00) >> 0x8
        y = (self.opcode & 0x00F0) >> 0x4
        lsb = self.state["v"][y] & 0x1
        self.state["v"][0xF] = lsb
        self.state["v"][x] = self.state["v"][y] >> 1

    def _8XY7(self):
        """
            Set register VX to the value of VY minus VX

            Set VF to 00 if a borrow occurs
            Set VF to 01 if a borrow does not occur
        """
        x = (self.opcode & 0x0F00) >> 0x8
        y = (self.opcode & 0x00F0) >> 0x4
        self.state["v"][x] = self.state["v"][y] - self.state["v"][x]
        if self.state["v"][x] < 0:
            self.state["v"][0xF] = 0
            self.state["v"][x] += 256
        else:
            self.state["v"][0xF] = 1

    def _8XYE(self):
        """
            Store the value of register VY shifted left one bit in register VX

            Set register VF to the most significant bit prior to the shift
        """
        x = (self.opcode & 0x0F00) >> 0x8
        y = (self.opcode & 0x00F0) >> 0x4
        msb = (self.state["v"][y] & 0xF0) >> 7
        self.state["v"][0xF] = msb
        self.state["v"][x] = self.state["v"][y] << 1
        self.state["v"][x] &= 0xFF

    def _9XY0(self):
        """
            Skip the following instruction if the value of register VX is not equal to the value of register VY
        """
        x = (self.opcode & 0x0F00) >> 0x8
        y = (self.opcode & 0x00F0) >> 0x4
        skip = self.state["v"][x] != self.state["v"][y]
        if skip:
            self.state["pc"] += 2

    def _ANNN(self):
        """Store memory address NNN in register I
        """
        addr = self.opcode & 0xFFF
        self.state["i"] = addr

    def _BNNN(self):
        """Jump to address NNN + V0
        """
        addr = self.opcode & 0x0FFF
        addr += self.state["v"][0]
        self.state["pc"] = addr

    def _CXNN(self):
        """Set VX to a random number with a mask of NN
        """
        x = (self.opcode & 0x0F00) >> 0x8
        mask = self.opcode & 0xFF
        random_num = random.randint(0, 255) & mask
        self.state["v"][x] = random_num

    def _DXYN(self):
        """
            Draw a sprite at position VX, VY with N bytes of sprite
            data starting at the address stored in I
            
            Set VF to 01 if any set pixels are changed to unset,
            and 00 otherwise
        """
        x = (self.opcode & 0x0F00) >> 0x8
        y = (self.opcode & 0x00F0) >> 0x4
        vx, vy = self.state["v"][x], self.state["v"][y]
        n = self.opcode & 0xF
        unset = False
        for y in range(n):
            sprite_byte = self.state["memory"][self.state["i"] + y]
            for x in range(8):
                if (vy + y) >= 32 or (vx + x) >= 64:
                    # out of screen
                    continue
                new_byte = (sprite_byte & (1 << (8 - x - 1))) >> (8 - x - 1)
                old_byte = self.state["display"][vy + y][vx + x]
                if old_byte and not (old_byte ^ new_byte):
                    unset = True
                self.state["display"][vy + y][vx + x] = new_byte ^ old_byte
        self.state["v"][0xF] = 1 if unset else 0

    def _EX9E(self):
        """
            Skip the following instruction if the key corresponding 
            to the hex value currently stored in register VX is pressed
        """
        x = (self.opcode & 0x0F00) >> 0x8
        vx = self.state["v"][x]
        if self.pressed_keys[self.keys_rev[vx]]:
            self.state["pc"] += 2

    def _EXA1(self):
        """
            Skip the following instruction if the key corresponding
            to the hex value currently stored in register VX is not pressed
        """
        x = (self.opcode & 0x0F00) >> 0x8
        vx = self.state["v"][x]
        if not self.pressed_keys[self.keys_rev[vx]]:
            self.state["pc"] += 2

    def _FX07(self):
        """Store the current value of the delay timer in register VX
        """
        x = (self.opcode & 0x0F00) >> 0x8
        self.state["v"][x] = self.state["delay"]

    def _FX0A(self):
        """Wait for a keypress and store the result in register VX
        """
        if not any(self.pressed_keys for key in self.keys.keys()):
            x = (self.opcode & 0x0F00) >> 0x8
            for i in range(0x10):
                if self.pressed_keys[self.keys_rev[i]]:
                    self.state["v"][x] = i
            self.state["pc"] -= 2

    def _FX15(self):
        """Set the delay timer to the value of register VX
        """
        x = (self.opcode & 0x0F00) >> 0x8
        self.state["delay"] = self.state["v"][x]

    def _FX18(self):
        """Set the sound timer to the value of register VX
        """
        x = (self.opcode & 0x0F00) >> 0x8
        self.state["delay"] = self.state["v"][x]

    def _FX1E(self):
        """Add the value stored in register VX to register I
        """
        x = (self.opcode & 0x0F00) >> 0x8
        vx = self.state["v"][x]
        self.state["i"] += vx

    def _FX29(self):
        """
            Set I to the memory address of the sprite data corresponding to the hexadecimal digit stored in register VX
        """
        x = (self.opcode & 0x0F00) >> 0x8
        addr = 5 * self.state["v"][x]
        self.state["i"] = addr

    def _FX33(self):
        """
            Store the binary-coded decimal equivalent of the value
            stored in register VX at addresses I, I+1, and I+2
        """
        i = self.state["i"]
        x = (self.opcode & 0x0F00) >> 0x8
        vx = self.state["v"][x]
        self.state["memory"][i] = vx // 100
        self.state["memory"][i + 1] = (vx % 100) // 10
        self.state["memory"][i + 2] = vx % 10

    def _FX55(self):
        """
            Store the values of registers V0 to VX inclusive in memory starting at address I

            I is set to I + X + 1 after operation
        """
        x = (self.opcode & 0x0F00) >> 0x8
        addr = self.state["i"]
        for i in range(0, x + 1):
            self.state["memory"][addr + i] = self.state["v"][i]
        self.state["i"] = addr + x + 1

    def _FX65(self):
        """
            Fill registers V0 to VX inclusive with the values stored in memory starting at address I
            
            I is set to I + X + 1 after operation
        """
        x = (self.opcode & 0x0F00) >> 0x8
        addr = self.state["i"]
        for i in range(0, x + 1):
            self.state["v"][i] = self.state["memory"][addr + i]
            self.state["v"][i] &= 0xFF
        self.state["i"] = addr + x + 1
