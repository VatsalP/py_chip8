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
KEYS = {
    pygame.K_0: 0x0,
    pygame.K_1: 0x1,
    pygame.K_2: 0x2,
    pygame.K_3: 0x3,
    pygame.K_4: 0x4,
    pygame.K_5: 0x5,
    pygame.K_6: 0x6,
    pygame.K_7: 0x7,
    pygame.K_8: 0x8,
    pygame.K_9: 0x9,
    pygame.K_a: 0xa,
    pygame.K_b: 0xb,
    pygame.K_c: 0xc,
    pygame.K_d: 0xd,
    pygame.K_e: 0xe,
    pygame.K_f: 0xf
}
KEYS_REVERSED = {v: k for k, v in KEYS.items()}


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
        display: List[List[int]]
    ):
        self.v = v
        self.i = i
        self.delay = delay
        self.sound = sound
        self.pc = pc
        self.sp = sp
        self.memory = memory
        self.display = display

    def set_font(self, font_list: List[List[int]]):
        i = 0
        for sprite in font_list:
            for byte in sprite:
                self.memory[i] = byte
                i += 1

    def map_code_to_mem(self, code: bytes, code_len: int):
        for address in range(0x200, code_len+0x200):
            self.memory[address] = code[address - 0x200]

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
            display=[0 for _ in range(64*32)]
        )
        self.chip_state.set_font(self._font_list)
        self.chip_state.map_code_to_mem(self.chip_file, len(self.chip_file))

    def opcode_switch(self, type_of: int, code: Tuple[bytes], pressed_keys):
        if type_of == 0x0:
            # 0nnn is not implemented

            sub_type_of = (code[0] & 0xf) << 8 | code[1]
            if sub_type_of == 0x0e0:
                # cls
                for i, _ in enumerate(self.chip_state.display):
                    self.chip_state.display[i] = 0
            elif sub_type_of == 0x0ee:
                # ret 
                self.chip_state.sp -= 1
                self.chip_state.pc = self.chip_state.memory[self.chip_state.sp] << 8
                self.chip_state.sp -= 1
                self.chip_state.pc = self.chip_state.memory[self.chip_state.sp]

        elif type_of == 0x1:
            # jump to address jmp nnn
            addr = (code[0] & 0xf) << 8 | code[1]
            self.chip_state.pc = addr

        elif type_of == 0x2:
            # stack thing
            # call nnn
            addr = (code[0] & 0xf) << 8 | code[1]
            self.chip_state.memory[self.chip_state.sp] = self.chip_state.pc & 0x00ff
            self.chip_state.sp += 1
            self.chip_state.memory[self.chip_state.sp] = (self.chip_state.pc & 0x00ff) >> 8
            self.chip_state.sp += 1
            self.chip_state.pc = addr

        elif type_of == 0x3:
            # ske vx, nn
            if self.chip_state.v[code[0] & 0xf] == code[1]:
                self.chip_state.pc += 2

        elif type_of == 0x4:
            # skne vx, nn
            if self.chip_state.v[code[0] & 0xf] != code[1]:
                self.chip_state.pc += 2

        elif type_of == 0x5:
            # ske vx, vy
            if self.chip_state.v[code[0] & 0xf] == self.chip_state.v[code[1] >> 4]:
                self.chip_state.pc += 2

        elif type_of == 0x6:
            # load vx, nn
            self.chip_state.v[code[0] & 0xf] = code[1]

        elif type_of == 0x7:
            # add vx, nn
            self.chip_state.v[code[0] & 0xf] += code[1]
            self.chip_state.v[code[0] & 0xf] %= 256

        elif type_of == 0x8:
            last_nibble = code[1] & 0xf
            if last_nibble == 0x0:
                # load vx, vy
                self.chip_state.v[code[0] & 0xf] = self.chip_state.v[code[1] >> 4]

            elif last_nibble == 0x1:
                # or vx, vy
                self.chip_state.v[code[0] & 0xf] |= self.chip_state.v[code[1] >> 4] 
            
            elif last_nibble == 0x2:
                # and vx, vy
                self.chip_state.v[code[0] & 0xf] &= self.chip_state.v[code[1] >> 4]

            elif last_nibble == 0x3:
                # xor vx, vy
                self.chip_state.v[code[0] & 0xf] ^= self.chip_state.v[code[1] >> 4]

            elif last_nibble == 0x4:
                # add vx, vy
                self.chip_state.v[code[0] & 0xf] += self.chip_state.v[code[1] >> 4]
                if self.chip_state.v[code[0] & 0xf] > 255:
                    self.chip_state.v[0xf] = 0x1
                    self.chip_state.v[code[0] & 0xf] %= 256
                else:
                    self.chip_state.v[0xf] = 0x0
                
            elif last_nibble == 0x5:
                # sub vx, vy - vx -= vy
                # ipdb.set_trace()
                self.chip_state.v[code[0] & 0xf] -= self.chip_state.v[code[1] >> 4]
                if self.chip_state.v[code[0] & 0xf] < 0:
                    self.chip_state.v[0xf] = 0x0
                    self.chip_state.v[code[0] & 0xf] += 256
                else:
                    self.chip_state.v[0xf] = 0x1

            elif last_nibble == 0x6:
                # shr vx, vy
                # bit = self.chip_state.v[code[1] >> 4] & 0x1
                # self.chip_state.v[code[0] & 0xf] = self.chip_state.v[code[1] >> 4] >> 1
                # self.chip_state.v[0xf] = bit
                bit = self.chip_state.v[code[0] & 0xf] & 0x1
                self.chip_state.v[code[0] & 0xf] = self.chip_state.v[code[0] & 0xf] >> 1
                self.chip_state.v[0xf] = bit

            elif last_nibble == 0x7:
                # subn vx, vy - vx = vy - vx
                result = self.chip_state.v[code[1] >> 4] - self.chip_state.v[code[0] & 0xf]
                if result < 0:
                    self.chip_state.v[0xf] = 0x0
                    self.chip_state.v[code[0] & 0xf] = 256 + result 
                else:
                    self.chip_state.v[code[0] & 0xf] = result
                    self.chip_state.v[0xf] = 0x1

            elif last_nibble == 0xE:
                # shl vx, vy
                # self.chip_state.v[0xf] = self.chip_state.v[code[1] >> 4] >> 7
                # self.chip_state.v[code[0] & 0xf] = self.chip_state.v[code[1] >> 4] << 1
                self.chip_state.v[0xf] = self.chip_state.v[code[0] & 0xf] >> 7
                self.chip_state.v[code[0] & 0xf] = 0 

        elif type_of == 0x9:
            # skne vx, vy
            if self.chip_state.v[code[0] & 0xf] != self.chip_state.v[code[1] >> 4]:
                self.chip_state.pc += 2

        elif type_of == 0xA:
            # load i, nnn
            addr = ((code[0] << 8) | code[1]) & 0x0fff
            self.chip_state.i = addr

        elif type_of == 0xB:
            # jmp [i] + nnn
            addr = (((code[0] & 0xf) << 8) | code[1]) + self.chip_state.i
            self.chip_state.pc = addr

        elif type_of == 0xC:
            # rand vx, nn
            mask = code[1]
            random_num = random.randint(0, 255) & mask
            self.chip_state.v[code[0] & 0xf] = random_num

        elif type_of == 0xD:
            # drw vx, vy, n
            vx, vy = self.chip_state.v[code[0] &  0xf], self.chip_state.v[code[1] >> 4]
            n = code[1] & 0xf
            unset = False
            import ipdb; ipdb.set_trace()
            for y in range(n):
                sprite_byte =self.chip_state.memory[
                    self.chip_state.i + y
                ]
                # doubt
                for x in range(8):
                    addr = ((vy+y) * 64) + vx + x
                    if (vy+y) >= 32 or (vx + x) >= 64:
                        # out of screen
                        continue
                    new_byte = (sprite_byte & (1<<(8-x-1))) >> (8-x-1)
                    old_byte = self.chip_state.display[addr]
                    if old_byte and not (old_byte ^ new_byte):
                        unset = True
                    self.chip_state.display[addr] = new_byte ^ old_byte

        elif type_of == 0xE:
            # skips related to key pressed
            if code[1] == 0x9E:
                if pressed_keys[self.chip_state.v[KEYS_REVERSED[code[0] & 0xf]]]:
                    self.chip_state.pc += 2
            elif code[1] == 0xA1:
                if not pressed_keys[self.chip_state.v[KEYS_REVERSED[code[0] & 0xf]]]:
                    self.chip_state.pc += 2

        elif type_of == 0xF:
            if code[1] == 0x07:
                self.chip_state.v[code[0] & 0xf] = self.chip_state.delay
            elif code[1] == 0x0A:
                key = wait()
                self.chip_state.v[code[0] & 0xf] = KEYS[key]
            elif code[1] == 0x15:
                self.chip_state.delay = self.chip_state.v[code[0] & 0xf]
            elif code[1] == 0x18:
                self.chip_state.sound = self.chip_state.v[code[0] & 0xf]
            elif code[1] == 0x1E:
                self.chip_state.i += self.chip_state.v[code[0] & 0xf]
            elif code[1] == 0x29:
                addr = 5 * self.chip_state.v[code[0] & 0xf]
                self.chip_state.i = addr
            elif code[1] == 0x33:
                # bcd vx
                number = self.chip_state.v[code[0] &  0xf]
                bcd = f"{number:03d}"
                i = self.chip_state.i
                self.chip_state.memory[i] = int(bcd[0])
                self.chip_state.memory[i+1] = int(bcd[1])
                self.chip_state.memory[i+2] = int(bcd[2])
            elif code[1] == 0x55:
                # ld [i], vx
                for index in range((code[0] & 0xf) + 1):
                    self.chip_state.memory[self.chip_state.i + index] = self.chip_state.v[index]
                # self.chip_state.i += (code[0] & 0xf) + 1
            elif code[1] == 0x65:
                # load vx, [i]
                for index in range((code[0] & 0xf) + 1):
                    self.chip_state.v[index] = self.chip_state.memory[self.chip_state.i + index]
                # self.chip_state.i += (code[0] & 0xf) + 1

    def fetch_next_opcode(self, pressed_keys):
        code = code_first, _ = (
            self.chip_state.memory[self.chip_state.pc],
            self.chip_state.memory[self.chip_state.pc + 1],
        )
        self.chip_state.pc += 2
        # extract first nibble from code
        first_nibble = code_first >> 4
        print(f"{self.chip_state.pc:04x} {code[0]:02x} {code[1]:02x}")
        print(f"State: pc: {self.chip_state.pc} i: {self.chip_state.i} v: {self.chip_state.v}")
        self.opcode_switch(first_nibble, code, pressed_keys)
        # reduce timers if set
        if self.chip_state.delay > 0: self.chip_state.delay -= 1
        if self.chip_state.sound > 0: self.chip_state.sound -= 1
    
    def get_memory(self):
        return self.chip_state.memory

    def get_display(self):
        return self.chip_state.display


def graphic_grid(size: Tuple[int], modifier: int) -> List[Tuple[int]]:
    grid = []
    for i in range(64):
        for j in range(32):
            grid.append((i * modifier, j * modifier, modifier, modifier))
    return grid


def main(chip_program: str):
    with open(chip_program, "rb") as chip_file:
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

        # startup chip8
        chip8 = `Chip8`(chip_file)

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
