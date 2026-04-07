import pygame
from scripts.utils import load_image


blue_bin_image   = load_image('assets/poubelles/BlueBin.png',   scale=0.5)
yellow_bin_image = load_image('assets/poubelles/YellowBin.png', scale=0.5)
brown_bin_image  = load_image('assets/poubelles/BrownBin.png',  scale=0.5)
green_bin_image  = load_image('assets/poubelles/GreenBin.png',  scale=0.5)

MAX_WASTE      = 5
GAUGE_WIDTH    = 50
GAUGE_HEIGHT   = 8
GAUGE_OFFSET_Y = 6
GAUGE_BG_COLOR = (60, 60, 60)
GAUGE_BORDER   = (200, 200, 200)

GAUGE_COLORS = {
    'blue':   (70,  130, 210),
    'yellow': (230, 200,  40),
    'brown':  (140,  90,  40),
    'green':  ( 50, 170,  60),
}


class Collectible:
    bin_color   = None
    gauge_color = (200, 200, 200)

    def __init__(self, platform, game, image):
        self.game  = game
        self.image = image
        self.size  = self.image.get_size()
        self.rect  = pygame.Rect(
            platform.rect.centerx - self.size[0] / 2,
            platform.rect.top - self.size[1],
            *self.size
        )
        self.platform             = platform
        self.platform.collectible = self
        self.waste_count          = 0

    def effect(self):
        self.waste_count += 1
        if self.waste_count >= MAX_WASTE:
            self.counter_effect(self.game)
            self.remove()

    @staticmethod
    def counter_effect(game):
        if hasattr(game, 'on_bin_filled'):
            game.on_bin_filled()

    def remove(self):
        self.platform.collectible = None
        if self in self.game.collectibles:
            self.game.collectibles.remove(self)

    def render(self, surf, scroll):
        # scroll est un entier (pas une liste)
        draw_x = self.rect.x - scroll
        draw_y = self.rect.y

        surf.blit(self.image, (draw_x, draw_y))

        gauge_x = draw_x + (self.size[0] - GAUGE_WIDTH) // 2
        gauge_y = draw_y + self.size[1] + GAUGE_OFFSET_Y

        pygame.draw.rect(surf, GAUGE_BG_COLOR,
                         (gauge_x, gauge_y, GAUGE_WIDTH, GAUGE_HEIGHT))
        fill_w = int(GAUGE_WIDTH * self.waste_count / MAX_WASTE)
        if fill_w > 0:
            pygame.draw.rect(surf, self.gauge_color,
                             (gauge_x, gauge_y, fill_w, GAUGE_HEIGHT))
        pygame.draw.rect(surf, GAUGE_BORDER,
                         (gauge_x, gauge_y, GAUGE_WIDTH, GAUGE_HEIGHT), 1)


class BlueBin(Collectible):
    bin_color   = 'blue'
    gauge_color = GAUGE_COLORS['blue']

    def __init__(self, platform, game):
        super().__init__(platform, game, blue_bin_image)

    def effect(self):
        self.game.score_blue = getattr(self.game, 'score_blue', 0) + 1
        super().effect()

    @staticmethod
    def counter_effect(game):
        if hasattr(game, 'on_bin_filled'):
            game.on_bin_filled()


class YellowBin(Collectible):
    bin_color   = 'yellow'
    gauge_color = GAUGE_COLORS['yellow']

    def __init__(self, platform, game):
        super().__init__(platform, game, yellow_bin_image)

    def effect(self):
        self.game.score_yellow = getattr(self.game, 'score_yellow', 0) + 1
        super().effect()

    @staticmethod
    def counter_effect(game):
        if hasattr(game, 'on_bin_filled'):
            game.on_bin_filled()


class BrownBin(Collectible):
    bin_color   = 'brown'
    gauge_color = GAUGE_COLORS['brown']

    def __init__(self, platform, game):
        super().__init__(platform, game, brown_bin_image)

    def effect(self):
        self.game.score_brown = getattr(self.game, 'score_brown', 0) + 1
        super().effect()

    @staticmethod
    def counter_effect(game):
        if hasattr(game, 'on_bin_filled'):
            game.on_bin_filled()


class GreenBin(Collectible):
    bin_color   = 'green'
    gauge_color = GAUGE_COLORS['green']

    def __init__(self, platform, game):
        super().__init__(platform, game, green_bin_image)

    def effect(self):
        self.game.score_green = getattr(self.game, 'score_green', 0) + 1
        super().effect()

    @staticmethod
    def counter_effect(game):
        if hasattr(game, 'on_bin_filled'):
            game.on_bin_filled()


BIN_CLASSES = {
    'blue':   BlueBin,
    'yellow': YellowBin,
    'brown':  BrownBin,
    'green':  GreenBin,
}