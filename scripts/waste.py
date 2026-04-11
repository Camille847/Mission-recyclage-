import pygame
import math
from scripts.utils import load_image, move, get_angle


WASTE_TYPES = {
    'papier':    {'image': 'assets/dechets/Papier.png',    'bin_color': 'blue',   'scale': 0.08},
    'bouteille': {'image': 'assets/dechets/Bouteille.png', 'bin_color': 'yellow', 'scale': 0.08},
    'canette':   {'image': 'assets/dechets/canette.png',   'bin_color': 'yellow', 'scale': 0.08},
    'banane':    {'image': 'assets/dechets/Banane.png',    'bin_color': 'brown',  'scale': 0.08},
}

_waste_images = {}
for _name, _data in WASTE_TYPES.items():
    _waste_images[_name] = load_image(_data['image'], scale=_data['scale'])

GRAVITY        = 800
POWER          = 850
ROTATION_SPEED = 4
FPS            = 60


class Waste:
    def __init__(self, game, waste_type: str,
                 x: float, y: float,
                 angle: float, power: float = POWER, gravity: float = GRAVITY):
        self.game       = game
        self.waste_type = waste_type
        self.bin_color  = WASTE_TYPES[waste_type]['bin_color']

        self._base_image = _waste_images[waste_type]
        self._base_size  = self._base_image.get_size()

        self.origin_x = float(x)
        self.origin_y = float(y)
        self.angle    = float(angle)
        self.power    = float(power)
        self.gravity  = float(gravity)
        self.t        = 0.0

        self.x = self.origin_x
        self.y = self.origin_y

        # rect de collision basé sur l'image NON-rotée (taille fixe)
        self.rect = pygame.Rect(
            int(self.x - self._base_size[0] / 2),
            int(self.y - self._base_size[1] / 2),
            *self._base_size
        )

        self.visual_angle = 0.0
        self.active = True
        self.on_ground = False
        self.ground_index = 0  # Index au moment où le déchet touche le sol

    def update(self, scroll, dt: float = None):
        if not self.active:
            return
        if dt is None:
            dt = 1.0 / FPS

        if not self.on_ground:
            self.t += dt
            self.x, self.y = move(
                (self.origin_x, self.origin_y),
                self.angle, self.power, self.t, self.gravity
            )

            if self.y > self.game.ground_y:
                self.y = self.game.ground_y
                self.on_ground = True
                # Enregistrer le nombre de déchets déjà au sol
                self.ground_index = sum(1 for w in self.game.waste_manager.wastes if w.on_ground and w is not self)

        if not self.on_ground:
            self.visual_angle = (self.visual_angle + ROTATION_SPEED) % 360

        # rect de collision : taille fixe (image de base), centré sur x/y
        self.rect = pygame.Rect(
            int(self.x - self._base_size[0] / 2),
            int(self.y - self._base_size[1] / 2),
            *self._base_size
        )

        if (self.y > self.game.height + 100 or
                self.x < -200 or self.x > self.game.width + 200):
            self.active = False
            return

        if not self.on_ground and self.game.collectibles:
            for collectible in list(self.game.collectibles):
                if self.rect.colliderect(collectible.rect):
                    self._on_hit_bin(collectible)
                    return
        
        # Collision entre déchets au sol
        if self.on_ground:
            for other_waste in list(self.game.waste_manager.wastes):
                if other_waste is self or not other_waste.on_ground:
                    continue
                if self.rect.colliderect(other_waste.rect):
                    # Rebond: repousser l'autre déchet
                    distance = math.sqrt((other_waste.x - self.x)**2 + (other_waste.y - self.y)**2)
                    if distance > 0:
                        # Direction du rebond
                        dx = (other_waste.x - self.x) / distance
                        dy = (other_waste.y - self.y) / distance
                        # Repousser l'autre déchet avec une force
                        push_force = 10
                        other_waste.x += dx * push_force
                        # Garder le déchet au sol (y ne change pas)
                        other_waste.y = self.game.ground_y

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
        
        # Agrandir l'image si le déchet touche le sol
        image = self._base_image
        if self.on_ground:
            w, h = self._base_image.get_size()
            new_w, new_h = int(w * 1.5), int(h * 1.5)
            image = pygame.transform.scale(self._base_image, (new_w, new_h))
        
        # On fait la rotation à la volée uniquement pour l'affichage
        rotated = pygame.transform.rotate(image, -self.visual_angle)
        rot_w, rot_h = rotated.get_size()
        # On centre l'image rotée sur la position réelle du déchet
        draw_x = int(self.x - rot_w / 2) - scroll
        draw_y = int(self.y - rot_h / 2)
        surf.blit(rotated, (draw_x, draw_y))


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
        
        # Compter les déchets au sol
        ground_wastes = sum(1 for w in self.wastes if w.on_ground)
        if ground_wastes >= 15:
            if hasattr(self.game, '_trigger_game_over'):
                self.game._trigger_game_over()

    def render(self, surf, scroll=0):
        for w in self.wastes:
            w.render(surf, scroll)

    def clear(self):
        self.wastes.clear()