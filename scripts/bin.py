import pygame
import math
from scripts.utils import load_image


blue_bin_image   = load_image('assets/poubelles/BlueBin.png',   scale=0.18)
yellow_bin_image = load_image('assets/poubelles/YellowBin.png', scale=0.17)
brown_bin_image  = load_image('assets/poubelles/BrownBin.png',  scale=0.18)
green_bin_image  = load_image('assets/poubelles/GreenBin.png',  scale=0.18)

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

# Vitesse d'approche au niveau nuit (pixels / seconde)
NIGHT_BIN_SPEED = 22

# Espacement minimum entre deux poubelles (en pixels entre leurs centres)
NIGHT_BIN_SPACING = 90


class Collectible:
    bin_color   = None
    gauge_color = (200, 200, 200)

    def __init__(self, platform, game, image):
        self.game  = game
        self.image = image
        self.size  = self.image.get_size()
        OFFSET_Y = 8

        self.rect = self.image.get_rect(
            midbottom=(platform.rect.centerx, platform.rect.bottom + OFFSET_Y)
        )
        self.platform             = platform
        self.platform.collectible = self
        self.waste_count          = 0
        self.direction            = 1
        self.tick                 = 0
        self.blink                = True
        self.dance_offset         = 0
        self.initial_x            = self.rect.centerx

        # Position flottante pour éviter la troncature entière de pygame.Rect
        self.float_x = float(self.rect.x)

    def update(self, dt):
        self.tick += 1

        if self.game.level == 1:  # Cafét — oscillation autour de la position initiale
            self.float_x = self.initial_x - self.image.get_width() / 2 + math.sin(self.tick * 0.05) * 30
            self.rect.x  = int(self.float_x)

        elif self.game.level == 2:  # Nuit — file indienne vers Kris
            kris_cx = self.game.kris.rect.centerx
            bin_cx  = self.rect.centerx

            # Vérifie si une autre poubelle est trop proche devant (entre cette
            # poubelle et Kris, c'est-à-dire à gauche puisqu'elles viennent de droite)
            blocked = False
            for other in self.game.collectibles:
                if other is self:
                    continue
                other_cx = other.rect.centerx
                # "devant" = plus proche de Kris = plus à gauche
                if other_cx < bin_cx and (bin_cx - other_cx) < NIGHT_BIN_SPACING:
                    blocked = True
                    break

            dx = kris_cx - bin_cx
            if abs(dx) > 2 and not blocked:
                direction = 1 if dx > 0 else -1
                self.float_x += NIGHT_BIN_SPEED * dt * direction
                self.rect.x   = int(self.float_x)

            # Légère oscillation verticale
            self.dance_offset = math.sin(self.tick * 0.1) * 3

            # Clignotement
            self.blink = (self.tick % 20) < 10

            # Contact avec Kris → game over
            if self.rect.colliderect(self.game.kris.rect):
                self.game._trigger_game_over()

        else:
            self.dance_offset = 0
            self.blink = True

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
        draw_x = self.rect.x - scroll
        draw_y = self.rect.y + self.dance_offset

        if self.blink:
            surf.blit(self.image, (draw_x, draw_y))
        else:
            temp_surf = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
            temp_surf.blit(self.image, (0, 0))
            temp_surf.set_alpha(100)
            surf.blit(temp_surf, (draw_x, draw_y))


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