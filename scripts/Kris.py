import pygame
import random

from scripts.utils import move, load_image, get_angle
from scripts.waste import WasteManager, WASTE_TYPES

scale = 0.15

# ─── Assets ───────────────────────────────────────────────────────────────────
images = {
    'idle':     load_image('../assets/personnage/Kris.png',   scale=scale),
    'throwing': load_image('../assets/personnage/Kris 2.png', scale=scale),
}

launch_sound = pygame.mixer.Sound('./assets/launch_jump.mp3')

# ─── Constantes de lancer ─────────────────────────────────────────────────────
MIN_POWER   = 100   # puissance minimale (px/s)
MAX_POWER   = 700   # puissance maximale (px/s)
POWER_SPEED = 300   # px/s² — vitesse de charge par seconde
GRAVITY     = 800   # px/s² — doit correspondre à waste.py


class Kris:
    """
    Personnage joueur positionné à gauche de l'écran.

    Contrôles :
      - Clic gauche enfoncé  → charge la puissance (jauge visible)
      - Relâcher le clic     → lance le déchet vers la position de la souris
      - L'angle est calculé automatiquement depuis Kris vers la souris.

    Le déchet à lancer est choisi aléatoirement parmi WASTE_TYPES.
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
        # Kris est fixe à gauche, centré horizontalement sur ~10 % de l'écran
        center_x = game.width * 0.10
        self.rect = pygame.FRect(
            center_x - size[0] / 2,
            bottom - size[1],
            *size
        )

        # Déchet courant à lancer
        self.current_waste = self._pick_waste()

        # État du lancer
        self.charging  = False   # clic enfoncé
        self.power     = 0.0     # puissance accumulée (px/s)
        self.angle     = 0.0     # angle vers la souris (radians)

        # Petite animation de rebond en idle
        self._bob_t    = 0.0
        self._base_y   = self.rect.y

    # ── Interne ───────────────────────────────────────────────────────────────

    def _pick_waste(self) -> str:
        """Choisit un déchet aléatoire parmi ceux disponibles."""
        return random.choice(list(WASTE_TYPES.keys()))

    def _set_state(self, state: str):
        self.state = state
        self.image = self.images[state]

    def _lerp_color(self, t: float):
        """Interpolation de couleur vert→rouge selon la charge (0→1)."""
        r = int(self.CHARGE_COLOR_LOW[0] + (self.CHARGE_COLOR_HIGH[0] - self.CHARGE_COLOR_LOW[0]) * t)
        g = int(self.CHARGE_COLOR_LOW[1] + (self.CHARGE_COLOR_HIGH[1] - self.CHARGE_COLOR_LOW[1]) * t)
        b = int(self.CHARGE_COLOR_LOW[2] + (self.CHARGE_COLOR_HIGH[2] - self.CHARGE_COLOR_LOW[2]) * t)
        return (r, g, b)

    # ── API publique ──────────────────────────────────────────────────────────

    def update(self, dt: float, mouse_pos: tuple, mouse_down: bool, mouse_released: bool):
        """
        dt             : delta-time en secondes
        mouse_pos      : (x, y) position souris à l'écran
        mouse_down     : True si le bouton gauche est maintenu enfoncé
        mouse_released : True la frame où le bouton gauche vient d'être relâché
        """
        # Calcul de l'angle Kris → souris en permanence
        self.angle = get_angle(self.rect.center, mouse_pos)

        # ── Charge ────────────────────────────────────────────────────────────
        if mouse_down:
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
            self.rect.y = self._base_y + pygame.math.Vector2(0, 0).y  # flat, pas de sin ici
            # petit rebond visuel optionnel :
            import math
            self.rect.y = self._base_y + math.sin(self._bob_t * 3) * 2

    def _launch(self):
        """Lance le déchet courant et prépare le suivant."""
        launch_sound.play()

        # Point de lancement = main droite de Kris (bord droit, milieu vertical)
        origin_x = self.rect.right
        origin_y = self.rect.centery

        self.waste_manager.launch(
            self.current_waste,
            origin_x, origin_y,
            angle=self.angle,
            power=self.power,
            gravity=GRAVITY,
        )

        # Réinitialisation
        self.charging     = False
        self.power        = 0.0
        self.current_waste = self._pick_waste()
        self._set_state('idle')

    # ── Rendu ─────────────────────────────────────────────────────────────────

    def render(self, surf: pygame.Surface, scroll: int = 0):
        # Sprite de Kris
        surf.blit(self.image, (self.rect.x - scroll, self.rect.y))

        # Affichage du déchet suivant (icône miniature au-dessus de Kris)
        self._render_next_waste(surf, scroll)

        # Jauge de puissance pendant la charge
        if self.charging:
            self._render_charge_bar(surf, scroll)

    def _render_next_waste(self, surf: pygame.Surface, scroll: int):
        """Petite icône du déchet à venir, au-dessus de la tête de Kris."""
        from scripts.waste import _waste_images
        icon = _waste_images.get(self.current_waste)
        if icon:
            ix = int(self.rect.centerx - icon.get_width() / 2) - scroll
            iy = int(self.rect.top - icon.get_height() - 6)
            surf.blit(icon, (ix, iy))

    def _render_charge_bar(self, surf: pygame.Surface, scroll: int):
        """Jauge de puissance colorée au-dessus de l'icône de déchet."""
        t = (self.power - MIN_POWER) / (MAX_POWER - MIN_POWER)
        t = max(0.0, min(1.0, t))

        bar_x = int(self.rect.centerx - self.CHARGE_BAR_W / 2) - scroll
        bar_y = int(self.rect.top - self.CHARGE_BAR_H - 28)

        # Fond
        pygame.draw.rect(surf, (50, 50, 50),
                         (bar_x, bar_y, self.CHARGE_BAR_W, self.CHARGE_BAR_H))
        # Remplissage
        fill_w = int(self.CHARGE_BAR_W * t)
        if fill_w > 0:
            pygame.draw.rect(surf, self._lerp_color(t),
                             (bar_x, bar_y, fill_w, self.CHARGE_BAR_H))
        # Bordure
        pygame.draw.rect(surf, (200, 200, 200),
                         (bar_x, bar_y, self.CHARGE_BAR_W, self.CHARGE_BAR_H), 1)