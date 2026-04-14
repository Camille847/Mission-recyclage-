import pygame
import random
import math
from scripts.utils import play

def load_bg(path, size):
    return pygame.transform.smoothscale(
        pygame.image.load(path).convert_alpha(),
        size
    )

def _font(size):
    return pygame.font.Font(None, size)

COLOR_BG_TOP = (200, 200, 200)   # gris clair
COLOR_BG_BOT = (150, 150, 150)   # gris foncé

COLOR_PANEL = (255, 255, 255, 120)

BTN_DEFAULT = (120, 160, 130)     # vert doux désaturé
BTN_HOVER   = (100, 140, 110)
BTN_CLICK   = (80, 110, 90)

BTN_DANGER        = (180, 110, 100)   # rouge doux (pas agressif)
BTN_DANGER_HOVER  = (160, 90, 80)

BTN_TEXT = (245, 245, 245)

TITLE_COLOR  = (0, 0, 0)     # noir
TITLE_SHADOW = (40, 40, 40)     # gris sombre

SUBTITLE_COLOR = (0, 0, 0)
GAMEOVER_COLOR    = (220, 80, 80)
LEAF_COLOR        = (80, 200, 100, 160)


def _leaf_points(cx, cy, size, angle_deg):
    """Calcule les points d'une feuille stylisée (losange allongé)."""
    a = math.radians(angle_deg)
    pts = []
    for da, r in [(0, size), (90, size * 0.35), (180, size), (270, size * 0.35)]:
        aa = a + math.radians(da)
        pts.append((cx + r * math.cos(aa), cy + r * math.sin(aa)))
    return pts


class Button:
    """Bouton arrondi avec ombre, hover et click."""

    def __init__(self, centerx, y, text, danger=False):
        self.text      = text
        self.danger    = danger
        self.is_hovered = False
        self.is_clicked = False

        self.col_base  = BTN_DANGER      if danger else BTN_DEFAULT
        self.col_hover = BTN_DANGER_HOVER if danger else BTN_HOVER
        self.col_click = (100, 10, 10)   if danger else BTN_CLICK
        self.color     = self.col_base

        self.font = _font(24)
        self.rendered_text  = self.font.render(self.text, True, BTN_TEXT)

        w, h = 160,38
        self.rect      = pygame.Rect(centerx - w // 2, y, w, h)
        self.text_rect = self.rendered_text.get_rect(center=self.rect.center)

        self._shadow_rect = self.rect.move(3, 4)

    def update(self, mouse_pos, click):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        self.color = self.col_base
        if self.is_hovered:
            self.color = self.col_hover
        self.is_clicked = self.is_hovered and click
        if self.is_clicked:
            self.color = self.col_click
        return self.is_clicked

    def render(self, surface):
        pygame.draw.rect(surface, (0, 0, 0, 40), self._shadow_rect, border_radius=10)
        pygame.draw.rect(surface, self.color, self.rect, border_radius=14)
        surface.blit(self.rendered_text, self.text_rect)

class Menu:
        """Menu principal et écran Game Over du jeu Mission Recyclage."""

        def __init__(self, game):
            self.show_menu_bg = True
            self.game = game
            self._tick = 0  # compteur pour animations

            # 🎵 Musique du menu
            if not pygame.mixer.music.get_busy():
                play("assets/music/music.mp3", 0.5)

            # -----------------------------
            # TITRES
            # -----------------------------
            title_font = _font(150)
            self.title_surf = title_font.render("Mission", True, TITLE_COLOR)
            self.title_rect = self.title_surf.get_rect(center=(game.width / 2, 85))

            title2_font = _font(120)
            self.title2_surf = title2_font.render("Recyclage !", True, TITLE_COLOR)
            self.title2_rect = self.title2_surf.get_rect(center=(game.width // 2, 200))

            self.title_shadow_surf = title_font.render("Mission", True, TITLE_SHADOW)
            self.title2_shadow_surf = title2_font.render("Recyclage !", True, TITLE_SHADOW)

            sub_font = _font(60)
            self.sub_surf = sub_font.render(
                "Trie les déchets, sauve la planète !", True, SUBTITLE_COLOR
            )
            self.sub_rect = self.sub_surf.get_rect(center=(game.width / 2, 300))

            # -----------------------------
            # GAME OVER
            # -----------------------------
            go_font = _font(76)
            self.game_over_surf = go_font.render("Game Over", True, (0, 0, 0))
            self.game_over_rect = self.game_over_surf.get_rect(center=(game.width / 2, 95))

            # -----------------------------
            # BOUTONS
            # -----------------------------
            cx = game.width // 2
            cy = game.height // 2
            self.niveaux_button = Button(cx, cy - 15, "Niveaux")
            self.retry_button = Button(cx, cy - 60, "Rejouer")

            self.regle_button = Button(cx, cy - 80, "Règles")
            self.rules_back_button = Button(0, 0, "Retour")
            self.rules_back_button.rect.bottomright = (self.game.width - 20, self.game.height - 20)
            self.rules_back_button.text_rect = self.rules_back_button.rendered_text.get_rect(
                center=self.rules_back_button.rect.center)
            self.rules_back_button._shadow_rect = self.rules_back_button.rect.move(3, 4)
            self.in_rules = False

            self.menu_button = Button(cx, cy, "Menu")
            self.quit_button = Button(cx, cy + 60, "Quitter", danger=True)

            # Boutons pour la sélection de niveau
            spacing = 55

            self.matin_button = Button(cx, cy - spacing, "Matin")
            self.cafe_button = Button(cx, cy, "Café")
            self.soir_button = Button(cx, cy + spacing, "Soir")
            self.back_button = Button(cx, cy + spacing + 60, "Retour")

            self.in_level_select = False

            # Bouton pour l'écran de victoire
            self.victory_button = Button(cx, cy + 150, "Menu Principal")

            # -----------------------------
            # MESSAGES GAME OVER
            # -----------------------------
            self.death_font = _font(28)
            self.death_messages = [
                "Plastique → poubelle jaune !",
                "Le verre va dans la verte !",
                "Papier et carton : poubelle bleue !",
                "Les restes organiques ? La marron !",
                "Vise bien avant de lancer !",
                "Attention au tri sélectif !",
            ]
            self.death_surf = None
            self.death_rect = None

            # -----------------------------
            # BACKGROUND (gradient)
            # -----------------------------
            self._bg = pygame.Surface((game.width, game.height))
            for y in range(game.height):
                t = y / game.height
                r = int(COLOR_BG_TOP[0] * (1 - t) + COLOR_BG_BOT[0] * t)
                g = int(COLOR_BG_TOP[1] * (1 - t) + COLOR_BG_BOT[1] * t)
                b = int(COLOR_BG_TOP[2] * (1 - t) + COLOR_BG_BOT[2] * t)

                noise = random.randint(-3, 3)
                pygame.draw.line(
                    self._bg,
                    (r + noise, g + noise, b + noise),
                    (0, y),
                    (game.width, y),
                )

            # -----------------------------
            # IMAGES
            # -----------------------------
            self.bg_mountain = pygame.image.load("assets/decor/mountain.png").convert_alpha()
            self.bg_tree = pygame.image.load("assets/decor/tree.png").convert_alpha()
            self.bg_herbe = pygame.image.load("assets/decor/herbe.png").convert_alpha()
            self.bg_fleur_rose = pygame.image.load("assets/decor/fleur_rose.png").convert_alpha()
            self.bg_rocher = pygame.image.load("assets/decor/rocher.png").convert_alpha()
            self.bg_gros_arbre = pygame.image.load("assets/decor/gros_arbre.png").convert_alpha()

            # Charger l'image de Kris pour le menu
            self.kris_image = pygame.image.load("assets/personnage/Kris.png").convert_alpha()
            self.kris_image = pygame.transform.scale(self.kris_image, (int(self.kris_image.get_width() * 0.15), int(self.kris_image.get_height() * 0.15)))  # Plus petite
            self.morning_bg = load_bg('assets/decor/Décor Matin.png', (game.width, game.height))
            self.rules_image = load_bg("assets/personnage/regles.png", (game.width, game.height))
            self.niveau_image = load_bg("assets/decor/niveau.png", (game.width, game.height))
            self.bravo_image = load_bg("assets/decor/Bravo.png", (game.width, game.height))
            self.game_over_bg = load_bg("assets/decor/Game over.png", (game.width, game.height))
            ground_y = int(self.game.height * 0.65)

            self.decor_flowers = [
                (120, ground_y + 25),
                (300, ground_y + 35),
                (500, ground_y + 20),
                (700, ground_y + 30),
                (900, ground_y + 25),
            ]

            self.decor_rocks = [
                (200, ground_y + 30),
                (450, ground_y + 35),
                (650, ground_y + 28),
                (850, ground_y + 32),
            ]

        def draw(self, screen):
            pass

        def new_message(self):
            msg = random.choice(self.death_messages)
            bigger_font = _font(48)
            surf = bigger_font.render(msg, True, (255, 240, 180))
            self.death_surf = surf
            self.death_rect = surf.get_rect(
                center=(self.game.width / 2, self.game.height - 80)
            )

        def _draw_bg(self, surf):
            w, h = surf.get_size()

            # Afficher le décor du matin
            surf.blit(self.morning_bg, (0, 0))

            # Kris qui danse
            kris_x = w // 2 + int(math.sin(self._tick * 0.08) * 15)  # Mouvement latéral
            kris_y = h - 100 + int(math.sin(self._tick * 0.12) * 20)  # Saut plus ample
            rotation = math.sin(self._tick * 0.06) * 10  # Rotation plus prononcée
            rotated_kris = pygame.transform.rotate(self.kris_image, rotation)
            rect = rotated_kris.get_rect(center=(kris_x, kris_y))
            surf.blit(rotated_kris, rect)


        def _draw_title(self, surf):
            surf.blit(self.title_shadow_surf, self.title_rect.move(3, 4))
            surf.blit(self.title2_shadow_surf, (self.title2_rect.x + 3, self.title2_rect.y + 3))

            bob = int(math.sin(self._tick * 0.05) * 3)
            surf.blit(self.title_surf, self.title_rect.move(0, bob))
            surf.blit(self.title2_surf, self.title2_rect)
            surf.blit(self.sub_surf, self.sub_rect)

        def _draw_panel(self, surf, rect, alpha=35):
            """Panneau blanc semi-transparent derrière les boutons."""
            panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            panel.fill((255, 255, 255, alpha))
            pygame.draw.rect(panel, (255, 255, 255, 60), panel.get_rect(), 2, border_radius=18)
            surf.blit(panel, rect.topleft)

        def update_main(self):
            self._tick += 1  # Pour l'animation des toiles
            if self.niveaux_button.update(self.game.mouse_pos, self.game.mouse_pressed):
                self.in_level_select = True
                pygame.mixer.music.stop()

            if self.regle_button.update(self.game.mouse_pos, self.game.mouse_pressed):
                self.in_rules = True
                pygame.mixer.music.stop()


            if self.quit_button.update(self.game.mouse_pos, self.game.mouse_pressed):
                self.game.quit()

        def update_level_select(self):
            self._tick += 1  # Pour l'animation des toiles
            if self.matin_button.update(self.game.mouse_pos, self.game.mouse_pressed):
                self.game.selected_level = 0
                pygame.mixer.music.stop()
                self.show_menu_bg = False
                self.game.play()
            if self.cafe_button.update(self.game.mouse_pos, self.game.mouse_pressed):
                self.game.selected_level = 1
                pygame.mixer.music.stop()
                self.show_menu_bg = False
                self.game.play()
            if self.soir_button.update(self.game.mouse_pos, self.game.mouse_pressed):
                self.game.selected_level = 2
                pygame.mixer.music.stop()
                self.show_menu_bg = False
                self.game.play()
            if self.back_button.update(self.game.mouse_pos, self.game.mouse_pressed):
                self.in_level_select = False
                if not pygame.mixer.music.get_busy():
                    play("assets/music/music.mp3", 0.5)

        def update_game_over(self):
            self._tick += 1  # Pour l'animation des toiles
            if self.retry_button.update(self.game.mouse_pos, self.game.mouse_pressed):
                pygame.mixer.music.stop()
                self.game.retry()
                return

            if self.menu_button.update(self.game.mouse_pos, self.game.mouse_pressed):
                play("assets/music/music.mp3", 0.5)
                self.game.to_menu()

            if self.quit_button.update(self.game.mouse_pos, self.game.mouse_pressed):
                self.game.quit()

        def update_victory(self):
            if self.victory_button.update(self.game.mouse_pos, self.game.mouse_pressed):
                play("assets/music/music.mp3", 0.5)
                self.game.to_menu()

        def render_main(self, surf):
            if self.show_menu_bg:
                self._draw_bg(surf)
            self._draw_title(surf)

            self.regle_button.render(surf)
            self.niveaux_button.render(surf)
            self.quit_button.render(surf)

        def render_game_over(self, surf):
            # Afficher l'image Game over.png comme fond
            surf.blit(self.game_over_bg, (0, 0))


            if self.death_surf:
                surf.blit(self.death_surf, self.death_rect)


            self.retry_button.render(surf)
            self.menu_button.render(surf)
            self.quit_button.render(surf)

        def render_level_select(self, surf):
            # Utiliser l'image niveau.png comme fond
            surf.blit(self.niveau_image, (0, 0))

            # Boutons des niveaux
            self.matin_button.render(surf)
            self.cafe_button.render(surf)
            self.soir_button.render(surf)

            # Bouton Retour
            self.back_button.render(surf)

        def render_victory(self, surf):
            # Afficher l'image Bravo.png
            surf.blit(self.bravo_image, (0, 0))

            # Bouton Menu Principal
            self.victory_button.render(surf)

        def _draw_old_bg(self, surf):
            w, h = surf.get_size()

            # Fond gris dégradé
            for y in range(h):
                t = y / h
                gray = int(200 * (1 - t) + 150 * t)
                pygame.draw.line(surf, (gray, gray, gray), (0, y), (w, y))

            # Toiles d'araignée
            web_color = (100, 100, 100)
            # Toile centrale
            center_x, center_y = w // 2, h // 2
            radius = min(w, h) // 3  # Plus gros
            rotation = self._tick * 0.0001  # Rotation encore plus lente
            for r in range(30, radius, 30):  # Espacement plus grand
                pygame.draw.circle(surf, web_color, (center_x, center_y), r, 1)
            for angle in range(0, 360, 30):  # Plus de rayons
                rad = math.radians(angle + rotation)
                end_x = center_x + radius * math.cos(rad)
                end_y = center_y + radius * math.sin(rad)
                pygame.draw.line(surf, web_color, (center_x, center_y), (end_x, end_y), 1)

            # Autres toiles
            for i in range(3):
                cx = random.randint(100, w - 100)
                cy = random.randint(100, h - 100)
                r = random.randint(50, 100)  # Plus gros
                pygame.draw.circle(surf, web_color, (cx, cy), r, 1)
                rot = rotation * (0.5 + i * 0.2)  # Différentes vitesses
                for a in range(0, 360, 45):  # Plus de rayons
                    rad = math.radians(a + rot)
                    ex = cx + r * math.cos(rad)
                    ey = cy + r * math.sin(rad)
                    pygame.draw.line(surf, web_color, (cx, cy), (ex, ey), 1)

            # Cartons (boîtes en carton) - Plus gros et non chevauchements
            box_color = (139, 69, 19)  # marron
            box_outline = (101, 67, 33)
            boxes = [
                (30, h - 250, 120, 90),  # Ajusté pour éviter chevauchement
                (w - 200, h - 350, 150, 105),
                (200, h - 180, 90, 75),
                (w - 350, 50, 135, 98),
            ]
            for bx, by, bw, bh in boxes:
                pygame.draw.rect(surf, box_color, (bx, by, bw, bh))
                pygame.draw.rect(surf, box_outline, (bx, by, bw, bh), 2)
                # Lignes pour simuler le carton
                pygame.draw.line(surf, box_outline, (bx + 15, by), (bx + 15, by + bh), 1)
                pygame.draw.line(surf, box_outline, (bx + bw - 15, by), (bx + bw - 15, by + bh), 1)

        def update_rules(self):
            if self.rules_back_button.update(self.game.mouse_pos, self.game.mouse_pressed):
                self.in_rules = False
                if not pygame.mixer.music.get_busy():
                    play("assets/music/music.mp3", 0.5)

        def render_rules(self, surf):
            surf.blit(self.rules_image, (0, 0))
            self.rules_back_button.render(surf)