"""
Holds Scenes =)
"""
import pygame
from pygame.locals import *

BLACK = 0, 0, 0
WHITE = 0xFF, 0xFF, 0xF

class SceneBase:
    def __init__(self):
        self.next = self
    
    def process_input(self, events, pressed_keys):
        pass

    def update(self):
        pass

    def render(self, surface):
        pass

    def switch_scene(self, next_scene):
        self.next = next_scene
    
    def terminate(self):
        self.switch_scene(None)

class TitleScreen(SceneBase):

    def __init__(self):
        SceneBase.__init__(self)

    def render(
            self, screen: pygame.Surface,
            background: pygame.Surface,
            font: pygame.font, clock
        ):
        background.fill(BLACK)
        text = font.render("Chip 8 Interpreter by vatsalp", 1, WHITE)
        textpos = text.get_rect(
            centery=background.get_height() / 2, centerx=background.get_width() / 2
        )
        background.blit(text, textpos)
        screen.blit(background, (0, 0))
        pygame.display.flip()
        current_time = pygame.time.get_ticks()
        exit_time = current_time + 3 * 10 ** 3
        boot_screen = True
        while boot_screen:
            for event in pygame.event.get():
                if event.type == QUIT:
                    return
            current_time = pygame.time.get_ticks()
            if current_time >= exit_time:
                boot_screen = False
            clock.tick(5)
        background.fill(BLACK)
        screen.blit(background, (0, 0))
        pygame.display.flip()
    