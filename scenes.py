"""
Holds Scenes =)
"""
from random import randint
from typing import BinaryIO, Tuple, List

import pygame
from pygame.locals import *

import chip8


class SceneBase:
    def __init__(self):
        self.next = self

    def process_input(self, events, pressed_keys):
        self.pressed_keys = pressed_keys

    def update(self):
        pass

    def render(self, surface: pygame.Surface):
        pass

    def switch_scene(self, next_scene: "SceneBase"):
        self.next = next_scene

    def terminate(self):
        self.switch_scene(None)


class TitleScene(SceneBase):
    def __init__(self):
        SceneBase.__init__(self)

    def render(
        self,
        screen: pygame.Surface,
        background: pygame.Surface,
        font: pygame.font.Font,
        clock: pygame.time.Clock,
    ):
        background.fill(chip8.BLACK)
        text = font.render("Chip 8 Interpreter by vatsalp", 1, chip8.WHITE)
        textpos = text.get_rect(
            centery=background.get_height() / 2, centerx=background.get_width() / 2
        )
        background.blit(text, textpos)
        screen.blit(background, (0, 0))
        pygame.display.flip()
        current_time = pygame.time.get_ticks()
        exit_time = current_time + 1 * 10 ** 3
        boot_screen = True
        while boot_screen:
            current_time = pygame.time.get_ticks()
            if current_time >= exit_time:
                boot_screen = False
            clock.tick(5)


class BootScene(SceneBase):
    def __init__(self, time: int, chip8: chip8.Chip8):
        SceneBase.__init__(self)
        # we do this scene for 2 secs
        self.exit_time = time + 1 * 10 ** 3
        self.chip8 = chip8

    def render(self, background: pygame.Surface, grid_rect: List[Tuple[int]], *args):
        # bit of fun eh
        for rect in grid_rect:
            color = randint(0, 10), randint(0, 10), randint(0, 102)
            pygame.draw.rect(background, color, rect, 0)
        text = args[0].render("Loading...", 1, chip8.WHITE)
        textpos = text.get_rect(
            centery=background.get_height() / 2, centerx=background.get_width() / 2
        )
        background.blit(text, textpos)
        curr_time = pygame.time.get_ticks()
        if curr_time >= self.exit_time:
            background.fill(chip8.BLACK)
            self.switch_scene(Chip8Scene(self.chip8))


class Chip8Scene(SceneBase):
    def __init__(self, chip8: chip8.Chip8):
        SceneBase.__init__(self)
        self.chip8 = chip8

    def update(self):
        self.chip8.fetch_next_opcode(self.pressed_keys)

    def render(self, background: pygame.Surface, grid_rect: List[Tuple[int]], *args):
        display = self.chip8.get_display()
        for i, pixel in enumerate(display):
            if pixel:
                pygame.draw.rect(background, chip8.WHITE, grid_rect[i], 0)
            else:
                pygame.draw.rect(background, chip8.BLACK, grid_rect[i], 0)
