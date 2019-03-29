"""
Holds Scenes =)
"""
from random import randint

import pygame
from pygame.locals import *

import main


class SceneBase:
    def __init__(self):
        self.next = self

    def process_input(self, events, pressed_keys):
        self.pressed_keys = pressed_keys

    def update(self):
        pass

    def render(self, surface):
        pass

    def switch_scene(self, next_scene):
        self.next = next_scene

    def terminate(self):
        self.switch_scene(None)


class TitleScene(SceneBase):
    def __init__(self):
        SceneBase.__init__(self)

    def render(
        self,
        screen,
        background,
        font,
        clock
    ):
        background.fill(main.BLACK)
        text = font.render("Chip 8 Interpreter by vatsalp", 1, main.WHITE)
        textpos = text.get_rect(
            centery=background.get_height() / 2, centerx=background.get_width() / 2
        )
        background.blit(text, textpos)
        screen.blit(background, (0, 0))
        pygame.display.flip()
        current_time = pygame.time.get_ticks()
        exit_time = current_time + 0.1 * 10 ** 3
        boot_screen = True
        while boot_screen:
            current_time = pygame.time.get_ticks()
            if current_time >= exit_time:
                boot_screen = False
            clock.tick(5)


class BootScene(SceneBase):
    def __init__(self, time, chip8):
        SceneBase.__init__(self)
        # we do this scene for 2 secs
        self.exit_time = time + 0.1 * 10 ** 3
        self.chip8 = chip8

    def render(self, background, grid_rect, *args):
        # bit of fun eh
        for y in range(32):
            for x in range(64):
                color = randint(0, 10), randint(0, 10), randint(0, 102)
                pygame.draw.rect(background, color, grid_rect[y][x], 0)
        text = args[0].render("Loading...", 1, main.WHITE)
        textpos = text.get_rect(
            centery=background.get_height() / 2, centerx=background.get_width() / 2
        )
        background.blit(text, textpos)
        curr_time = pygame.time.get_ticks()
        if curr_time >= self.exit_time:
            background.fill(main.BLACK)
            self.switch_scene(Chip8Scene(self.chip8))


class Chip8Scene(SceneBase):
    def __init__(self, chip8):
        SceneBase.__init__(self)
        self.chip8 = chip8

    def update(self):
        self.chip8.fetch_next_opcode(self.pressed_keys)

    def render(self, background, grid_rect, *args):
        display = self.chip8.get_display()
        for y in range(32):
            for x in range(64):
                if display[y][x]:
                    pygame.draw.rect(background, main.WHITE, grid_rect[y][x], 0)
                else:
                    pygame.draw.rect(background, main.BLACK, grid_rect[y][x], 0)
