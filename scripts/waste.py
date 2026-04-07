import pygame
import math
from scripts.utils import move, get_angle

# --- CONFIGURATION ---
# Assure-toi que les dossiers existent : assets/dechets/
WASTE_TYPES = {
    'papier': {'path': 'assets/dechets/Papier.png', 'bin_color': 'blue', 'scale': 0.12},
    'bouteille': {'path': 'assets/dechets/Bouteille.png', 'bin_color': 'yellow', 'scale': 0.12},
    'canette': {'path': 'assets/dechets/canette.png', 'bin_color': 'yellow', 'scale': 0.12},
    'banane': {'path': 'assets/dechets/Banane.png', 'bin_color': 'brown', 'scale': 0.12},
}

GRAVITY = 800
POWER = 500
ROTATION_SPEED = 4


class Waste(pygame.sprite.Sprite):
    """
    Un déchet lancé avec une trajectoire physique réelle.
    """

    def __init__(self, game, waste_type, x, y, angle, power=POWER, gravity=GRAVITY):
        super().__init__()
        self.game = game
        self.waste_type = waste_type

        # Récupération des infos du type
        data = WASTE_TYPES.get(waste_type, WASTE_TYPES['papier'])
        self.bin_color = data['bin_color']

        # Chargement et redimensionnement de l'image
        try:
            full_img = pygame.image.load(data['path']).convert_alpha()
            w, h = full_img.get_size()
            self._base_image = pygame.transform.scale(full_img, (int(w * data['scale']), int(h * data['scale'])))
        except Exception as e:
            print(f"Erreur chargement image {waste_type}: {e}")
            self._base_image = pygame.Surface((30, 30))
            self._base_image.fill((255, 0, 255))  # Rose flash si erreur

        self.image = self._base_image
        self.rect = self.image.get_rect(center=(x, y))
        self.mask = pygame.mask.from_surface(self.image)

        # Variables de position physique (float pour la précision)
        self.origin_x = float(x)
        self.origin_y = float(y)
        self.x, self.y = self.origin_x, self.origin_y

        self.angle = float(angle)
        self.power = float(power)
        self.gravity = float(gravity)
        self.t = 0.0  # Temps écoulé depuis le lancer

        self.visual_angle = 0.0
        self.active = True

    def update(self, dt):
        if not self.active:
            return

        self.t += dt

        # Calcul de la nouvelle position via utils.move
        self.x, self.y = move(
            (self.origin_x, self.origin_y),
            self.angle,
            self.power,
            self.t,
            self.gravity
        )

        # Rotation pour l'effet visuel
        self.visual_angle = (self.visual_angle + ROTATION_SPEED) % 360
        self.image = pygame.transform.rotate(self._base_image, -self.visual_angle)

        # Mise à jour du rectangle de collision (centré sur x, y)
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))

        # Suppression si hors de l'écran (avec marge de sécurité)
        if (self.y > self.game.height + 100 or
                self.x < -100 or
                self.x > self.game.width + 100):
            self.kill()
            self.active = False


class WasteManager:
    """
    Le cerveau qui gère tous les déchets pour Rayane.
    """

    def __init__(self, game):
        self.game = game
        self.waste_group = pygame.sprite.Group()

    def launch(self, waste_type, x, y, angle, power=POWER):
        """Lance un déchet avec un angle précis."""
        new_waste = Waste(self.game, waste_type, x, y, angle, power)
        self.waste_group.add(new_waste)
        return new_waste

    def launch_toward(self, waste_type, origin_x, origin_y, target_x, target_y, power=POWER):
        """Calcule l'angle vers une cible (ex: souris) et lance."""
        angle = get_angle((origin_x, origin_y), (target_x, target_y))
        return self.launch(waste_type, origin_x, origin_y, angle, power)

    def update(self, dt):
        """Met à jour les positions et gère les collisions avec les poubelles."""
        self.waste_group.update(dt)

        # Vérification des collisions entre tes déchets et les poubelles de Sylia
        for waste in self.waste_group:
            # On suppose que game.collectibles contient les instances de Bin
            hit_bins = pygame.sprite.spritecollide(waste, self.game.collectibles, False, pygame.sprite.collide_mask)

            for bin_obj in hit_bins:
                self._handle_collision(waste, bin_obj)

    def _handle_collision(self, waste, bin_obj):
        """Logique de score quand on touche une poubelle."""
        if waste.bin_color == bin_obj.bin_color:
            # C'est la bonne poubelle !
            bin_obj.effect()  # On déclenche l'animation de la poubelle
            if hasattr(self.game, 'on_correct_bin'):
                self.game.on_correct_bin(waste)
        else:
            # Mauvaise poubelle...
            if hasattr(self.game, 'on_wrong_bin'):
                self.game.on_wrong_bin(waste, bin_obj)

        # Dans les deux cas, le déchet disparaît après l'impact
        waste.kill()

    def draw(self, surf, scroll=0):
        """Affiche les déchets en tenant compte du défilement (scroll)."""
        for waste in self.waste_group:
            # On ajuste la position d'affichage selon le scroll du décor
            draw_pos = (waste.rect.x - scroll, waste.rect.y)
            surf.blit(waste.image, draw_pos)

    def clear(self):
        """Nettoie tout (utile pour un Game Over)."""
        self.waste_group.empty()