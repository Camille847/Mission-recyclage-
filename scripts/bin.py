import pygame
import os

class Bin:
    def __init__(self, x, y, bin_type):
        """
        bin_type : 'bleue', 'jaune', 'marron', 'verte'
        """
        self.type = bin_type
        # Charger l'image correspondante
        image_path = os.path.join('assets', 'poubelles', f'{bin_type}.png')
        self.image = pygame.image.load(image_path)
        self.image = pygame.transform.scale(self.image, (80, 120))
        self.rect = self.image.get_rect(center=(x, y))

    def render(self, surf):
        surf.blit(self.image, self.rect)
