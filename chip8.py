import pygame
from pygame.locals import *


def wait():
    """ Waiting for User to press key
    """
    while True:
        pressed_keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                import sys; sys.exit()
            if event.type == pygame.KEYDOWN and \
                any(
                    True if pressed_keys[x] else False for x in filter(lambda i: i in KEYS, pressed_keys)
                ):
                return next(filter(lambda i: i in KEYS and pressed_keys[i], pressed_keys))


class Chip8:

    KEYS = {
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
        pygame.K_d: 0xa,
        pygame.K_f: 0xb,
        pygame.K_z: 0xc,
        pygame.K_x: 0xd,
        pygame.K_c: 0xe,
        pygame.K_v: 0xf
    }
    KEYS.update({v: k for k, v in KEYS.items()})

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
            'v': [0 for _ in range(16)],
            'i': 0,
            "delay": 0,
            "sound": 0,
            "pc": 0x200,
            "sp": 0xEA0,
            "memory": [0 for _ in range(4096)],
            "display": [[0 for _ in range(64)] for _ in range(32)]
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
            0xE: {0xE: self._EX9E, 0X1: self._EXA1},
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
            }
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
        for address in range(0x200, code_len+0x200):
            self.state["memory"][address] = code[address - 0x200]

    def get_memory(self):
        return self.state["memory"]

    def get_display(self):
        return self.state["display"]

    def fetch_next_opcode(self, pressed_keys):
        opcode =  self.state["memory"][self.state["pc"]] << 0x8 | self.state["memory"][self.state["pc"] + 1]
        self.state["pc"] += 2
        print(f"{self.state['pc']:04x} {opcode >> 0x8:02x} {opcode & 0xff:02x}")
        print(f"State: pc: {self.state['pc']} i: {self.state['i']} v: {self.state['v']}")
        self.opcode_switch(opcode, pressed_keys)
        # reduce timers if set
        if self.state["delay"] > 0: self.state["delay"] -= 1
        if self.state["sound"] > 0: self.state["delay"] -= 1

    def opcode_switch(self, opcode, pressed_keys):
        self.opcode = opcode
        self.pressed_keys = pressed_keys
        first_nibble = (opcode & 0xf000) >> 0xc
        print(f"First nibble: {first_nibble}")
        if first_nibble == 0xf:
            function = self.opcode_map.get(opcode & 0x00ff)
        elif first_nibble in [0x0, 0x8, 0xE]:
            function = self.opcode_map.get(opcode & 0x000f)
        else:
            function = self.opcode_map.get(first_nibble)
        if function:
            pass
        else:
            print(f"{self.opcode} not implemented.")

    def _00E0(self):
        """ Clear the Screen
        """
        for y in range(32):
            for x in range(64):
                self.state['display'][y][x] = 0
    
    def _00EE(self):
        pass
    
    def _1NNN(self):
        pass

    def _2NNN(self):
        pass

    def _3XNN(self):
        pass

    def _4XNN(self):
        pass

    def _5XY0(self):
        pass

    def _6XNN(self):
        """ Store number NN in register VX
        """
        x = (self.opcode & 0x0f00) >> 0x8
        self.state["v"][x] = self.opcode & 0x00ff

    def _7XNN(self):
        """Add the value NN to register VX
        """
        x = (self.opcode & 0x0f00) >> 0x8
        self.state["v"][x] += (self.opcode & 0x00ff)
        self.state["v"][x] %= 256

    def _8XY0(self):
        """Store the value of register VY in register VX
        """
        x = (self.opcode & 0x0f00) >> 0x8
        y = (self.opcode & 0x00f0) >> 0x4
        self.state["v"][x] = self.state["v"][y]

    def _8XY1(self):
        pass

    def _8XY2(self):
        pass

    def _8XY3(self):
        pass

    def _8XY4(self):
        """
        """

    def _8XY5(self):
        pass

    def _8XY6(self):
        pass

    def _8XY7(self):
        pass

    def _8XYE(self):
        pass

    def _9XY0(self):
        pass

    def _ANNN(self):
        pass

    def _BNNN(self):
        pass

    def _CXNN(self):
        pass

    def _DXYN(self):
        pass

    def _EX9E(self):
        pass

    def _EXA1(self):
        pass

    def _FX07(self):
        pass

    def _FX0A(self):
        pass

    def _FX15(self):
        pass

    def _FX18(self):
        pass

    def _FX1E(self):
        pass

    def _FX29(self):
        pass

    def _FX33(self):
        pass

    def _FX55(self):
        pass

    def _FX65(self):
        pass