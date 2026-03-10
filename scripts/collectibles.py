import pygame
from scripts.utils import load_image


blue_bin_image = load_image('Poubelle Bleue.png', scale=0.5)
yellow_bin_image = load_image('Poubelle Jaune.png', scale=0.5)
brown_bin_image = load_image('Poubelle Maron.png', scale=0.5)
brown_bin_image = load_image('Poubelle Maron.png', scale=0.5)
green_bin_image = load_image('Poubelle Verte.png', scale=0.5)


class Collectible:
    """
    An object that can be collected by the frog.
    """
    def __init__(self, platform, game, image):
        self.game = game
        self.image = image
        self.size = self.image.get_size()
        self.rect = pygame.Rect(platform.rect.centerx - self.size[0] / 2, platform.rect.top - self.size[1], *self.size)
        self.platform = platform
        self.platform.collectible = self

    def effect(self):
        pass

    @staticmethod
    def counter_effect(game):
        pass

    def remove(self):
        self.platform.collectible = None
        self.game.collectibles.remove(self)

    def render(self, surf, scroll):
        surf.blit(self.image, (self.rect.x - scroll, self.rect.y))

