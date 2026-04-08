
import pygame

from scripts.utils import load_image

scale = 0.4

# load assets
sprite_sheet = load_image('wood-ui.png', scale=scale)
sprite_sheet.set_colorkey('white')

charging_hud = []

# extract power hud images from the sprite sheet
for i in range(5):
    img = sprite_sheet.subsurface(pygame.Rect(0, i * 87 * scale, sprite_sheet.get_size()[0], 76 * scale))
    charging_hud.append(img)

charging_hud.reverse()


class PowerHud():
    """
    Show the current power level during jump charging.
    """
    def __init__(self):
        self.image = charging_hud[0]
        self.rect = self.image.get_rect()
        self.rect.topleft = (25, 25)
        self.index = 0

    def set(self, index):
        self.index = index
        self.image = charging_hud[self.index]

    def reset(self):
        self.index = 0
        self.image = charging_hud[0]

    def render(self, surf):
        surf.blit(self.image, self.rect)


class ScoreHud():
    """
    The score counter displayed at the top of the screen.
    """
    def __init__(self, width):
        self.score = 0
        self.font = pygame.font.Font('assets/ComicNeue-Bold.ttf', 50)
        self.center = (width // 2, 100)

    def reset(self):
        self.score = 0

    def update(self, scroll):
        self.score += scroll

    def render(self, surf, offset):
        text = self.font.render(str(self.score), True, 'black')
        surf.blit(text, (self.center[0] - text.get_size()[0] // 2, self.center[1] - text.get_size()[1] // 2 + offset))
