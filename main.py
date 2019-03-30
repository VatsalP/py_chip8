"""
Chip 8 interpreter
"""
import random

import pygame
from pygame.locals import *

import scenes
from chip8 import Chip8

# constants
SIZE = WIDTH, HEIGHT = 64, 32
MODIFIER = 20
BLACK = 0, 0, 0
WHITE = 0xFF, 0xFF, 0xFF



def graphic_grid(size, modifier):
    grid = []
    for j in range(32):
        grid.append([])
        for i in range(64):
            grid[j].append((i * modifier, j * modifier, modifier, modifier))
    return grid


def main(chip_program):
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
        # active_scene = scenes.TitleScene()
        # active_scene.render(screen, background, font, clock)

        # startup chip8
        chip8 = Chip8(chip_file)

        # Change to boot screen
        active_scene = scenes.BootScene(pygame.time.get_ticks(), chip8)
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
