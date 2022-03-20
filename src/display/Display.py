import pygame
from pygame.locals import *

class Display():
    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode((640, 320));
        self.screen.fill((0, 0, 0))


    def clear_display(self):
        self.display = [0] * 2048
        self.update_display()

    def update_display(self):
        for x in range(64):
            for y in range(32):
                if self.display[x * 32 + y] == 1:
                    self.draw_pixel(x, y)
                else:
                    self.clear_pixel(x, y)
                
        pygame.display.update()

    def draw_pixel(self, x, y):
        pygame.draw.rect(self.screen, (255, 255, 255), Rect((x % 64) * 10, (y % 64) * 10, 10, 10))

    def clear_pixel(self, x, y):
        pygame.draw.rect(self.screen, (0, 0, 0), Rect((x % 64) * 10, (y % 64) * 10, 10, 10))

