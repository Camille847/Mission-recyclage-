import pygame
from scripts.utils import load_image


blue_bin_image = load_image('Poubelle Bleue.png', scale=0.5)
yellow_bin_image = load_image('Poubelle Jaune.png', scale=0.5)
brown_bin_image = load_image('Poubelle Maron.png', scale=0.5)
green_bin_image = load_image('Poubelle Verte.png', scale=0.5)

MAX_WASTE       = 5          # nombre de déchets avant disparition de la poubelle
GAUGE_WIDTH     = 50         # largeur de la jauge en pixels
GAUGE_HEIGHT    = 8          # hauteur de la jauge en pixels
GAUGE_OFFSET_Y  = 6          # espace entre bas de l'image et la jauge
GAUGE_BG_COLOR  = (60, 60, 60)
GAUGE_BORDER    = (200, 200, 200)


GAUGE_COLORS = {
    'blue': (70, 130, 210),
    'yellow': (230, 200, 40),
    'brown': (140, 90, 40),
    'green': (50, 170, 60),
}


class Collectible:
    """
    Collectible de base dont héritent toutes les poubelles.
    Chaque poubelle possède :
      - une image
      - un compteur de déchets (0 → MAX_WASTE)
      - une jauge visuelle
      - une couleur de correspondance avec les déchets (self.bin_color)
    """

    bin_color = None
    gauge_color = (200, 200, 200)

    def __init__(self, platform, game, image):
        self.game = game
        self.image = image
        self.size = self.image.get_size()
        self.rect = pygame.Rect(
            platform.rect.centerx - self.size[0] / 2,
            platform.rect.top - self.size[1],
            *self.size
        )
        self.platform = platform
        self.platform.collectible = self
        self.waste_count = 0  # compteur de déchets reçus


    def effect(self):
        self.waste_count += 1
        if self.waste_count >= MAX_WASTE:
            self.counter_effect(self.game)
            self.remove()


    @staticmethod
    def counter_effect(game):
        """Surcharger si un effet spécial doit se produire à la disparition."""
        pass

    def remove(self):
        self.platform.collectible = None
        if self in self.game.collectibles:
            self.game.collectibles.remove(self)

    def render(self, surf, scroll):
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


# ─── Poubelle Bleue (papier / carton) ─────────────────────────────────────────
class BlueBin(Collectible):
    bin_color = 'blue'
    gauge_color = GAUGE_COLORS['blue']

    def __init__(self, platform, game):
        super().__init__(platform, game, blue_bin_image)

    def effect(self):
        """Incrémente le compteur bleu du jeu puis appelle la logique commune."""
        self.game.score_blue = getattr(self.game, 'score_blue', 0) + 1
        super().effect()

    @staticmethod
    def counter_effect(game):
        pass


# ─── Poubelle Jaune (plastique / métal) ───────────────────────────────────────
class YellowBin(Collectible):
    bin_color = 'yellow'
    gauge_color = GAUGE_COLORS['yellow']

    def __init__(self, platform, game):
        super().__init__(platform, game, yellow_bin_image)

    def effect(self):
        self.game.score_yellow = getattr(self.game, 'score_yellow', 0) + 1
        super().effect()

    @staticmethod
    def counter_effect(game):
        pass


# ─── Poubelle Marron (déchets organiques) ─────────────────────────────────────
class BrownBin(Collectible):
    bin_color = 'brown'
    gauge_color = GAUGE_COLORS['brown']

    def __init__(self, platform, game):
        super().__init__(platform, game, brown_bin_image)

    def effect(self):
        self.game.score_brown = getattr(self.game, 'score_brown', 0) + 1
        super().effect()

    @staticmethod
    def counter_effect(game):
        pass


# ─── Poubelle Verte (verre) ───────────────────────────────────────────────────
class GreenBin(Collectible):
    bin_color = 'green'
    gauge_color = GAUGE_COLORS['green']

    def __init__(self, platform, game):
        super().__init__(platform, game, green_bin_image)

    def effect(self):
        self.game.score_green = getattr(self.game, 'score_green', 0) + 1
        super().effect()

    @staticmethod
    def counter_effect(game):
        pass



BIN_CLASSES = {
    'blue': BlueBin,
    'yellow': YellowBin,
    'brown': BrownBin,
    'green': GreenBin,
}