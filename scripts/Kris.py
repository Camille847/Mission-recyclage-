import math
import pygame
import random

from scripts.utils import load_image, get_angle
from scripts.waste import WasteManager, WASTE_TYPES, _waste_images

scale = 0.08

# Charger les deux images
_img_idle     = load_image('assets/personnage/Kris.png',   scale=scale)
_img_throwing = load_image('assets/personnage/Kris 2.png', scale=scale)

# Forcer la même hauteur pour éviter la superposition au changement d'état
# On prend la hauteur max et on redimensionne en gardant les proportions
_target_h = max(_img_idle.get_height(), _img_throwing.get_height())

def _resize_to_height(img, h):
    w = img.get_width()
    orig_h = img.get_height()
    new_w = int(w * h / orig_h)
    return pygame.transform.scale(img, (new_w, h))

_img_idle     = _resize_to_height(_img_idle,     _target_h)
_img_throwing = _resize_to_height(_img_throwing, _target_h)

images = {
    'idle':     _img_idle,
    'throwing': _img_throwing,
}

try:
    launch_sound = pygame.mixer.Sound('assets/launch_jump.mp3')
except:
    launch_sound = None

# ─── Constantes de lancer ─────────────────────────────────────────────────────
MIN_POWER   = 100
MAX_POWER   = 1200
GRAVITY     = 800


class Kris:
    CHARGE_COLOR_LOW  = (220,  60,  60)
    CHARGE_COLOR_HIGH = (220,  60,  60)
    CHARGE_BAR_W      = 60
    CHARGE_BAR_H      = 8

    def __init__(self, game, bottom: float):
        self.game  = game
        self.waste_manager: WasteManager = game.waste_manager

        self.images = images
        self.state  = 'idle'
        self.image  = self.images[self.state]

        # On utilise l'image idle pour définir le rect de base
        size = _img_idle.get_size()
        center_x = game.width * 0.10
        self.rect = pygame.Rect(
            center_x - size[0] / 2,
            bottom - size[1],   # ancrage bas constant
            size[0],
            size[1]
        )
        self._bottom = bottom  # on mémorise le bas pour ancrer correctement

        self.current_waste = self._pick_waste()

        self.charging = False
        self.power    = 0.0
        self.angle    = 0.0

        self._bob_t  = 0.0
        self._base_y = self.rect.y

    def _pick_waste(self) -> str:
        return random.choice(list(WASTE_TYPES.keys()))

    def _set_state(self, state: str):
        self.state = state
        self.image = self.images[state]
        # Recalcule le rect en gardant le bas et le centre X constants
        new_w = self.image.get_width()
        new_h = self.image.get_height()
        self.rect = pygame.Rect(
            self.rect.centerx - new_w // 2,
            self._bottom - new_h,
            new_w,
            new_h
        )

    def _lerp_color(self, t: float):
        r = int(self.CHARGE_COLOR_LOW[0] + (self.CHARGE_COLOR_HIGH[0] - self.CHARGE_COLOR_LOW[0]) * t)
        g = int(self.CHARGE_COLOR_LOW[1] + (self.CHARGE_COLOR_HIGH[1] - self.CHARGE_COLOR_LOW[1]) * t)
        b = int(self.CHARGE_COLOR_LOW[2] + (self.CHARGE_COLOR_HIGH[2] - self.CHARGE_COLOR_LOW[2]) * t)
        return (r, g, b)

    def update(self, dt: float, mouse_pos: tuple, mouse_down: bool, mouse_released: bool):

        if mouse_down and not mouse_released:
            if not self.charging:
                self.charging = True
                self._set_state('throwing')

            mouse_x, mouse_y = mouse_pos

            px = self.rect.centerx
            py = self.rect.centery

            dx = mouse_x - px
            dy = mouse_y - py

            distance = math.sqrt(dx ** 2 + dy ** 2)

            MAX_PULL = 150
            distance = min(distance, MAX_PULL)

            self.angle = math.atan2(-dy, dx)

            ratio = distance / MAX_PULL
            self.power = MIN_POWER + ratio * (MAX_POWER - MIN_POWER)

        if mouse_released and self.charging:
            self._launch()

        if not self.charging:
            self._set_state('idle')
            self._bob_t += dt
            # bob vertical : on déplace uniquement _base_y en Y
            bob_offset = int(math.sin(self._bob_t * 3) * 2)
            self.rect.y = int((self._bottom - self.rect.height) + bob_offset)

    def _launch(self):
        if launch_sound:
            launch_sound.play()

        origin_x = self.rect.right
        origin_y = self.rect.centery

        self.waste_manager.launch(
            self.current_waste,
            origin_x, origin_y,
            angle=self.angle,
            power=self.power,
            gravity=GRAVITY,
        )

        self.charging      = False
        self.power         = 0.0
        self.current_waste = self._pick_waste()
        self._set_state('idle')

    def render(self, surf: pygame.Surface, scroll: int = 0):
        surf.blit(self.image, (self.rect.x - scroll, self.rect.y))
        self._render_next_waste(surf, scroll)

        if self.charging:
            self._render_charge_bar(surf, scroll)

    def _render_next_waste(self, surf: pygame.Surface, scroll: int):
        icon = _waste_images.get(self.current_waste)
        if icon:
            ix = int(self.rect.centerx - icon.get_width() / 2) - scroll
            iy = int(self.rect.top - icon.get_height() - 6)
            surf.blit(icon, (ix, iy))

    def _render_charge_bar(self, surf: pygame.Surface, scroll: int):
        t = (self.power - MIN_POWER) / (MAX_POWER - MIN_POWER)
        t = max(0.0, min(1.0, t))

        bar_x = int(self.rect.centerx - self.CHARGE_BAR_W / 2) - scroll
        bar_y = int(self.rect.top - self.CHARGE_BAR_H - 28)

        pygame.draw.rect(surf, (50, 50, 50),
                         (bar_x, bar_y, self.CHARGE_BAR_W, self.CHARGE_BAR_H))
        fill_w = int(self.CHARGE_BAR_W * t)
        if fill_w > 0:
            pygame.draw.rect(surf, self._lerp_color(t),
                             (bar_x, bar_y, fill_w, self.CHARGE_BAR_H))
        pygame.draw.rect(surf, (200, 200, 200),
                         (bar_x, bar_y, self.CHARGE_BAR_W, self.CHARGE_BAR_H), 1)
