import pygame
import os
from scripts.utils import move

class Waste:
    def __init__(self, start_x, start_y, waste_type):
        """
        waste_type : 'banane', 'bouteille', 'canette', 'papier'
        """
        self.type = waste_type
        # Association déchet -> bonne poubelle
        self.correct_bin = {
            'banane': 'marron',    # déchet compostable
            'bouteille': 'jaune',  # plastique
            'canette': 'jaune',    # métal
            'papier': 'bleue'      # papier/carton
        }

        # Charger l'image
        image_path = os.path.join('assets', 'dechets', f'{waste_type}.png')
        self.image = pygame.image.load(image_path)
        self.image = pygame.transform.scale(self.image, (40, 40))
        self.rect = self.image.get_rect(center=(start_x, start_y))

        self.launched = False
        self.init_pos = (start_x, start_y)
        self.time = 0
        self.angle = 0
        self.power = 0

    def launch(self, power, angle):
        self.launched = True
        self.init_pos = self.rect.center
        self.time = 0
        self.angle = angle
        self.power = power

    def update(self, dt, gravity):
        if self.launched:
            self.time += dt / 100
            new_x, new_y = move(self.init_pos, self.angle, self.power, self.time, gravity)
            self.rect.center = (new_x, new_y)

    def render(self, surf):
        surf.blit(self.image, self.rect)