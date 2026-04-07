import pygame
import math
from scripts.utils import load_image, move, get_angle


WASTE_TYPES = {
    'papier':    {'image': 'assets/dechets/Papier.png',    'bin_color': 'blue',   'scale': 0.12},
    'bouteille': {'image': 'assets/dechets/Bouteille.png', 'bin_color': 'yellow', 'scale': 0.12},
    'canette':   {'image': 'assets/dechets/canette.png',   'bin_color': 'yellow', 'scale': 0.12},
    'banane':    {'image': 'assets/dechets/Banane.png',    'bin_color': 'brown',  'scale': 0.12},
}

_waste_images = {}
for _name, _data in WASTE_TYPES.items():
    _waste_images[_name] = load_image(_data['image'], scale=_data['scale'])

GRAVITY        = 800
POWER          = 500
ROTATION_SPEED = 4
FPS            = 60


class Waste:
    def __init__(self, game, waste_type: str,
                 x: float, y: float,
                 angle: float, power: float = POWER, gravity: float = GRAVITY):
        self.game      = game
        self.waste_type = waste_type
        self.bin_color  = WASTE_TYPES[waste_type]['bin_color']

        self._base_image = _waste_images[waste_type]
        self.image       = self._base_image
        self.size        = self.image.get_size()

        self.origin_x = float(x)
        self.origin_y = float(y)
        self.angle    = float(angle)
        self.power    = float(power)
        self.gravity  = float(gravity)
        self.t        = 0.0

        self.x = self.origin_x
        self.y = self.origin_y

        self.rect = pygame.Rect(
            int(self.x - self.size[0] / 2),
            int(self.y - self.size[1] / 2),
            *self.size
        )
        self.visual_angle = 0.0
        self.active = True

    def update(self, scroll, dt: float = None):
        if not self.active:
            return
        if dt is None:
            dt = 1.0 / FPS

        self.t += dt
        self.x, self.y = move(
            (self.origin_x, self.origin_y),
            self.angle, self.power, self.t, self.gravity
        )

        self.visual_angle = (self.visual_angle + ROTATION_SPEED) % 360
        self.image = pygame.transform.rotate(self._base_image, -self.visual_angle)
        self.size  = self.image.get_size()

        self.rect = pygame.Rect(
            int(self.x - self.size[0] / 2),
            int(self.y - self.size[1] / 2),
            *self.size
        )

        if (self.y > self.game.height + 100 or
                self.x < -200 or self.x > self.game.width + 200):
            self.active = False
            return

        for collectible in self.game.collectibles:
            if self.rect.colliderect(collectible.rect):
                self._on_hit_bin(collectible)
                return

    def _on_hit_bin(self, bin_obj):
        self.active = False
        if self.bin_color == bin_obj.bin_color:
            bin_obj.effect()
            if hasattr(self.game, 'on_correct_bin'):
                self.game.on_correct_bin(self)
        else:
            if hasattr(self.game, 'on_wrong_bin'):
                self.game.on_wrong_bin(self, bin_obj)

    def render(self, surf, scroll):
        if not self.active:
            return
        draw_x = int(self.x - self.size[0] / 2) - scroll
        draw_y = int(self.y - self.size[1] / 2)
        surf.blit(self.image, (draw_x, draw_y))


class WasteManager:
    def __init__(self, game):
        self.game   = game
        self.wastes: list[Waste] = []

    def launch(self, waste_type: str, x: float, y: float,
               angle: float, power: float = POWER,
               gravity: float = GRAVITY) -> Waste:
        w = Waste(self.game, waste_type, x, y, angle, power, gravity)
        self.wastes.append(w)
        return w

    def launch_toward(self, waste_type: str,
                      origin_x: float, origin_y: float,
                      target_x: float, target_y: float,
                      power: float = POWER, gravity: float = GRAVITY) -> Waste:
        angle = get_angle((origin_x, origin_y), (target_x, target_y))
        return self.launch(waste_type, origin_x, origin_y, angle, power, gravity)

    def update(self, scroll=0, dt: float = None):
        for w in self.wastes:
            w.update(scroll, dt)
        self.wastes = [w for w in self.wastes if w.active]

    def render(self, surf, scroll=0):
        for w in self.wastes:
            w.render(surf, scroll)

    def clear(self):
        self.wastes.clear()