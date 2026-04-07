import math
import pygame
import random

from scripts.utils import load_image, get_angle
from scripts.waste import WasteManager, WASTE_TYPES, _waste_images

scale = 0.15

# ─── Assets ───────────────────────────────────────────────────────────────────
images = {
    'idle':     load_image('../assets/personnage/Kris.png',   scale=scale),
    'throwing': load_image('../assets/personnage/Kris 2.png', scale=scale),
}

launch_sound = pygame.mixer.Sound('./assets/launch_jump.mp3')

# ─── Constantes de lancer ─────────────────────────────────────────────────────
MIN_POWER   = 100
MAX_POWER   = 700
POWER_SPEED = 300
GRAVITY     = 800


class Kris:
    """
    Personnage joueur positionné à gauche de l'écran.

    Contrôles :
      - Clic gauche enfoncé  → charge la puissance (jauge visible)
      - Relâcher le clic     → lance le déchet vers la position de la souris
      - L'angle est calculé automatiquement depuis Kris vers la souris.
    """

    CHARGE_COLOR_LOW  = (80,  200,  80)
    CHARGE_COLOR_HIGH = (220,  60,  60)
    CHARGE_BAR_W      = 60
    CHARGE_BAR_H      = 8

    def __init__(self, game, bottom: float):
        self.game  = game
        self.waste_manager: WasteManager = game.waste_manager

        self.images = images
        self.state  = 'idle'
        self.image  = self.images[self.state]

        size = self.image.get_size()
        center_x = game.width * 0.10
        self.rect = pygame.FRect(
            center_x - size[0] / 2,
            bottom - size[1],
            *size
        )

        self.current_waste = self._pick_waste()

        self.charging = False
        self.power    = 0.0
        self.angle    = 0.0

        self._bob_t  = 0.0
        self._base_y = self.rect.y

    # ── Interne ───────────────────────────────────────────────────────────────

    def _pick_waste(self) -> str:
        return random.choice(list(WASTE_TYPES.keys()))

    def _set_state(self, state: str):
        self.state = state
        self.image = self.images[state]

    def _lerp_color(self, t: float):
        r = int(self.CHARGE_COLOR_LOW[0] + (self.CHARGE_COLOR_HIGH[0] - self.CHARGE_COLOR_LOW[0]) * t)
        g = int(self.CHARGE_COLOR_LOW[1] + (self.CHARGE_COLOR_HIGH[1] - self.CHARGE_COLOR_LOW[1]) * t)
        b = int(self.CHARGE_COLOR_LOW[2] + (self.CHARGE_COLOR_HIGH[2] - self.CHARGE_COLOR_LOW[2]) * t)
        return (r, g, b)

    # ── API publique ──────────────────────────────────────────────────────────

    def update(self, dt: float, mouse_pos: tuple, mouse_down: bool, mouse_released: bool):
        self.angle = get_angle(self.rect.center, mouse_pos)

        # ── Charge ────────────────────────────────────────────────────────────
        if mouse_down and not mouse_released:
            if not self.charging:
                self.charging = True
                self.power    = MIN_POWER
                self._set_state('throwing')
            else:
                self.power = min(self.power + POWER_SPEED * dt, MAX_POWER)

        # ── Lancer ────────────────────────────────────────────────────────────
        if mouse_released and self.charging:
            self._launch()

        # ── Idle bob ──────────────────────────────────────────────────────────
        if not self.charging:
            self._set_state('idle')
            self._bob_t += dt
            self.rect.y = self._base_y + math.sin(self._bob_t * 3) * 2

    def _launch(self):
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

    # ── Rendu ─────────────────────────────────────────────────────────────────

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