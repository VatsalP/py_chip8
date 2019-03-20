"""
Chip 8 interpreter
"""
import random

from typing import BinaryIO, Tuple, List

import pygame
from pygame.locals import *

import scenes

# constants
SIZE = WIDTH, HEIGHT = 64, 32
MODIFIER = 10
BLACK = 0, 0, 0
WHITE = 0xFF, 0xFF, 0xFF


class Chip8State:
    def __init__(
        self,
        v: List[int],
        i: int,
        delay: int,
        sound: int,
        pc: int,
        sp: int,
        memory: List[int],
    ):
        self.v = v
        self.i = i
        self.delay = delay
        self.sound = sound
        self.pc = pc
        self.sp = sp
        self.memory = memory

    def set_font(self, font_list: List[List[int]]):
        i = 0
        for sprite in font_list:
            for byte in sprite:
                self.memory[i] = byte
                i += 1

    def map_code_to_mem(self, code: bytes):
        for address in range(0x200, len(code)):
            self.memory[address] = code[address - 0x200]


class Chip8:

    _font_list = [
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

    def __init__(self, chip_file: BinaryIO):
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
        self.chip_state = Chip8State(
            v=[0 for _ in range(16)],
            i=0,
            delay=0,
            sound=0,
            pc=0x200,
            sp=0xEA0,
            memory=[0 for _ in range(4096)],
        )
        self.chip_state.set_font(self._font_list)
        self.chip_state.map_code_to_mem(self.chip_file)

    def opcode_switch(self, type_of: int, code: Tuple[bytes]):
        if type_of == 0:
            second_nibble = code[0] & 0xF
            if second_nibble == 0xE:
                if code[1] & 0xF == 0x0:
                    print("CLS")
                else:
                    print("RET")
            else:
                print(f"SYS {code[0] & 0xf}{code[1]}")

        # jump suppresses error condition if addr lesser
        # than 0x200
        elif type_of == 0x1:
            addr = (code[0] & 0xf) >> 0xff + code[1]
            self.chip_state.pc = addr if addr >= 0x200 else self.chip_state.pc

        elif type_of == 0x2:
            addr = (code[0] & 0xf) >> 0xff + code[1]
            self.chip_state.sp += 1
            self.chip_state.memory[self.chip_state.sp] = self.chip_state.pc
            self.chip_state.pc = addr

        elif type_of == 0x3:
            print(f"SE V{code[0] & 0xf}, {code[1]}")
        elif type_of == 0x4:
            print(f"SNE V{code[0] & 0xf}, {code[1]}")
        elif type_of == 0x5:
            print(f"SE V{code[0] & 0xf}, V{code[1] >> 4}")

        elif type_of == 0x6:
            self.chip_state.v[code[0] & 0xf] = code[1]

        elif type_of == 0x7:
            self.chip_state.v[code[0] & 0xf] += code[1]
            self.chip_state.v[code[0] & 0xf] %= 256

        elif type_of == 0x8:
            last_nibble = code[1] & 0xf
            if last_nibble == 0x0:
                self.chip_state.v[code[0] & 0xf] = self.chip_state.v[code[1] >> 4]

            elif last_nibble == 0x1:
                self.chip_state.v[code[0] & 0xf] = self.chip_state.v[code[0] | 0xf] & \
                    self.chip_state.v[code[1] >> 4]
            
            elif last_nibble == 0x2:
                self.chip_state.v[code[0] & 0xf] = self.chip_state.v[code[0] & 0xf] & \
                    self.chip_state.v[code[1] >> 4]

            elif last_nibble == 0x3:
                self.chip_state.v[code[0] & 0xf] = self.chip_state.v[code[0] ^ 0xf] & \
                    self.chip_state.v[code[1] >> 4]

            elif last_nibble == 0x4:
                self.chip_state.v[code[0] & 0xf] += self.chip_state.v[code[1] >> 4]
                if self.chip_state.v[code[0] & 0xf] > 255:
                    self.chip_state.v[0xf] = 0x1
                    self.chip_state.v[code[0] & 0xf] %= 256
                else:
                    self.chip_state.v[0xf] = 0x0
                
            elif last_nibble == 0x5:
                self.chip_state.v[code[0] & 0xf] -= self.chip_state.v[code[0] >> 4]
                if self.chip_state.v[code[0] & 0xf] < 0:
                    self.chip_state.v[0xf] = 0x1
                    self.chip_state.v[code[0] & 0xf] += 256
                else:
                    self.chip_state.v[0xf] = 0x0

            # check if working
            elif last_nibble == 0x6:
                self.chip_state.v[0xf] = self.chip_state.v[code[1] >> 4] & 0x1
                self.chip_state.v[code[0] & 0xf] = self.chip_state.v[code[1] >> 4] >> 1

            elif last_nibble == 0x7:
                self.chip_state.v[code[0] & 0xf] = self.chip_state.v[code[0] >> 4] - \
                    self.chip_state.v[code[0] & 0xf]
                if self.chip_state.v[code[0] & 0xf] < 0:
                    self.chip_state.v[0xf] = 0x1
                    self.chip_state.v[code[0] & 0xf] += 256
                else:
                    self.chip_state.v[0xf] = 0x0

            # check if working
            elif last_nibble == 0xE:
                self.chip_state.v[0xf] = self.chip_state.v[code[1] >> 4] >> 7
                self.chip_state.v[code[0] & 0xf] = self.chip_state.v[code[1] >> 4] << 1

        elif type_of == 0x9:
            print(f"SNE V{code[0] & 0xf}, V{code[1] >> 4}")
        elif type_of == 0xA:
            print(f"LD I, {code[0] & 0xf}{code[1]}")

        elif type_of == 0xB:
            addr = ((code[0] & 0xf) >> 0xff + code[1]) + self.chip_state.v[0]
            self.chip_state.pc = addr if addr >= 0x200 else self.chip_state.pc

        elif type_of == 0xC:
            mask = code[1]
            random_num = random.randint(0, 255) & mask
            self.chip_state.v[code[0] & 0xf] = random_num

        elif type_of == 0xD:
            print(f"DRW V{code[0] & 0xf}, V{code[1] >> 4}, {code[1] & 0xf}")
        elif type_of == 0xE:
            if code[1] == 0x9E:
                print(f"SKP V{code[0] & 0xf}")
            elif code[1] == 0xA1:
                print(f"SKNP V{code[0] & 0xf}")
        elif type_of == 0xF:
            if code[1] == 0x07:
                print(f"LD V{code[0] & 0xf}, DT")
            elif code[1] == 0x0A:
                print(f"LD V{code[0] & 0xf}, K")
            elif code[1] == 0x15:
                print(f"LD DT, V{code[0] & 0xf}")
            elif code[1] == 0x18:
                print(f"LD ST, V{code[0] & 0xf}")
            elif code[1] == 0x1E:
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
        code = code_first, code_second = (
            self.chip_state.memory[pc],
            self.chip_state.memory[pc + 1],
        )
        # extract first nibble from code
        first_nibble = code_first >> 4
        print(f"{pc+0x200:04x} {code_first:02x} {code_second:02x} ", end="")
        self.opcode_switch(first_nibble, code)


def graphic_grid(size: Tuple[int], modifier: int) -> List[Tuple[int]]:
    grid = []
    for i in range(64):
        for j in range(32):
            grid.append((i * modifier, j * modifier, modifier, modifier))
    return grid


def main(chip_program: str):
    with open(chip_program, "rb") as chip_file:
        chip8 = Chip8(chip_file)
        grid_rect = graphic_grid(SIZE, MODIFIER)

        # initialize screen
        pygame.init()
        screen = pygame.display.set_mode((WIDTH * MODIFIER, HEIGHT * MODIFIER))
        pygame.display.set_caption("Chip8 Interpreter")
        pygame.mouse.set_visible(0)
        background = pygame.Surface(screen.get_size())
        background = background.convert()
        clock = pygame.time.Clock()
        font = pygame.font.SysFont("monospace", 24)

        # Title screen
        active_scene = scenes.TitleScene()
        active_scene.render(screen, background, font, clock)

        # Change to boot screen
        active_scene.switch_scene(scenes.BootScene(pygame.time.get_ticks(), chip8))
        active_scene = active_scene.next

        # Event loop
        while active_scene != None:
            pressed_keys = pygame.key.get_pressed()
            filtered_events = []
            for event in pygame.event.get():
                quit_attempt = False
                if event.type == pygame.QUIT:
                    quit_attempt = True
                if quit_attempt:
                    active_scene.terminate()
                else:
                    filtered_events.append(event)

            active_scene.process_input(filtered_events, pressed_keys)
            active_scene.update()
            active_scene.render(background, grid_rect, font, clock)
            active_scene = active_scene.next

            screen.blit(background, (0, 0))
            pygame.display.flip()
            clock.tick(60)


if __name__ == "__main__":
    from sys import argv

    if len(argv) == 2:
        main(argv[1])
    else:
        print("Please supply chip 8 program.")
