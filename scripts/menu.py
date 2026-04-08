import pygame
import random
import math

def _font(size):
    return pygame.font.Font(None, size)

COLOR_BG_TOP = (210, 225, 215)   # vert gris très doux
COLOR_BG_BOT = (190, 210, 200)   # vert pastel naturel

COLOR_PANEL = (255, 255, 255, 120)

BTN_DEFAULT = (120, 160, 130)     # vert doux désaturé
BTN_HOVER   = (100, 140, 110)
BTN_CLICK   = (80, 110, 90)

BTN_DANGER        = (180, 110, 100)   # rouge doux (pas agressif)
BTN_DANGER_HOVER  = (160, 90, 80)

BTN_TEXT = (245, 245, 245)

TITLE_COLOR  = (70, 90, 80)     # gris vert foncé (nature)
TITLE_SHADOW = (30, 40, 35)

SUBTITLE_COLOR = (100, 120, 110)
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
        self.game  = game
        self._tick = 0   # compteur pour animations

        title_font = _font(56)
        self.title_surf  = title_font.render('Mission', True, TITLE_COLOR)
        self.title_rect  = self.title_surf.get_rect(center=(game.width / 2, 85))

        title2_font = _font(46)
        self.title2_surf = title2_font.render('Recyclage !', True, TITLE_COLOR)
        self.title2_rect = self.title2_surf.get_rect(center=(game.width // 2, 160))

        self.title_shadow_surf  = title_font.render('Mission',        True, TITLE_SHADOW)
        self.title2_shadow_surf = title2_font.render('Recyclage !', True, TITLE_SHADOW)

        sub_font = _font(18)
        self.sub_surf = sub_font.render('Trie les déchets, sauve la planète !', True, SUBTITLE_COLOR)
        self.sub_rect = self.sub_surf.get_rect(center=(game.width / 2, 215))

        go_font = _font(76)
        self.game_over_surf = go_font.render('Game Over', True, GAMEOVER_COLOR)
        self.game_over_rect = self.game_over_surf.get_rect(center=(game.width / 2, 95))

        cx = game.width // 2
        cy = game.height // 2
        self.play_button  = Button(cx, cy - 15,  'Jouer')
        self.retry_button = Button(cx, cy - 60,  'Rejouer')
        self.menu_button  = Button(cx, cy,        'Menu')
        self.quit_button  = Button(cx, cy + 60,   'Quitter', danger=True)

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



        self._bg = pygame.Surface((game.width, game.height))
        for y in range(game.height):
            t = y / game.height
            r = int(COLOR_BG_TOP[0] * (1 - t) + COLOR_BG_BOT[0] * t)
            g = int(COLOR_BG_TOP[1] * (1 - t) + COLOR_BG_BOT[1] * t)
            b = int(COLOR_BG_TOP[2] * (1 - t) + COLOR_BG_BOT[2] * t)

            noise = random.randint(-3, 3)
            pygame.draw.line(self._bg, (r + noise, g + noise, b + noise), (0, y), (game.width, y))

        self.bg_mountain = pygame.image.load("assets/decor/mountain.png").convert_alpha()
        self.bg_tree = pygame.image.load("assets/decor/tree.png").convert_alpha()
        self.bg_herbe = pygame.image.load("assets/decor/herbe.png").convert_alpha()
        self.bg_fleur_rose = pygame.image.load("assets/decor/fleur_rose.png").convert_alpha()
        self.bg_rocher = pygame.image.load("assets/decor/rocher.png").convert_alpha()
        self.bg_gros_arbre = pygame.image.load("assets/decor/gros_arbre.png").convert_alpha()

        ground_y = int(self.game.height * 0.65)

        # 🌸 4-5 fleurs max
        self.decor_flowers = [
            (120, ground_y + 25),
            (300, ground_y + 35),
            (500, ground_y + 20),
            (700, ground_y + 30),
            (900, ground_y + 25),
        ]

        # 🪨 4 rochers max
        self.decor_rocks = [
            (200, ground_y + 30),
            (450, ground_y + 35),
            (650, ground_y + 28),
            (850, ground_y + 32),
        ]

    def new_message(self):
        msg  = random.choice(self.death_messages)
        surf = self.death_font.render(msg, True, (255, 240, 180))
        self.death_surf = surf
        self.death_rect = surf.get_rect(center=(self.game.width / 2, self.game.height - 80))

    def _draw_bg(self, surf):
        w, h = surf.get_size()

        # -----------------------------
        # ciel
        # -----------------------------
        surf.fill((200, 220, 210))

        # -----------------------------
        # montagne
        # -----------------------------
        mountain_height = int(h * 0.75)
        mountain = pygame.transform.scale(self.bg_mountain, (w, mountain_height))
        mountain_y = int(h * 0.25)
        surf.blit(mountain, (0, mountain_y))

        # -----------------------------
        # sol (important pour ancrer)
        # -----------------------------
        ground_y = int(h * 0.65)
        pygame.draw.rect(surf, (170, 200, 180), (0, ground_y, w, h - ground_y))

        # -----------------------------
        # HERBE (base visuelle)
        # -----------------------------
        grass_h = int(h * 0.08)
        grass_w = int(grass_h * 2)
        grass = pygame.transform.scale(self.bg_herbe, (grass_w, grass_h))

        for x in range(0, w, grass_w - 10):
            surf.blit(grass, (x, ground_y - 5))

        # -----------------------------
        # FLEURS (PAS EN LIGNE)
        # -----------------------------
        flower_h = int(h * 0.06)
        flower = pygame.transform.scale(self.bg_fleur_rose, (flower_h, flower_h))

        for x, y in self.decor_flowers:
            surf.blit(flower, (x, y))

        # -----------------------------
        # ROCHERS (mélangés)
        # -----------------------------
        rock_h = int(h * 0.09)
        rock = pygame.transform.scale(self.bg_rocher, (int(rock_h * 1.3), rock_h))

        for x, y in self.decor_rocks:
            surf.blit(rock, (x, y))

        # -----------------------------
        # ARBRES (CORRIGÉS)
        # -----------------------------
        tree_h = int(h * 0.42)
        tree_w = int(tree_h * 0.7)
        tree = pygame.transform.scale(self.bg_gros_arbre, (tree_w, tree_h))

        # aligné avec le bas de la montagne (donc h)
        tree_y = mountain_y +14  # ajuste entre +5 et +12 selon ton sprite

        # bien sur les côtés
        surf.blit(tree, (-10, tree_y))  # gauche
        surf.blit(tree, (w - tree_w + 10, tree_y))  # droite

    def _draw_title(self, surf):
        surf.blit(self.title_shadow_surf,  self.title_rect.move(3, 4))
        surf.blit(self.title2_shadow_surf,  (self.title2_rect.x + 3, self.title2_rect.y + 3))
        bob = int(math.sin(self._tick * 0.05) * 3)
        surf.blit(self.title_surf,  self.title_rect.move(0, bob))
        surf.blit(self.title2_surf, self.title2_rect)
        surf.blit(self.sub_surf,    self.sub_rect)

    def _draw_panel(self, surf, rect, alpha=35):
        """Panneau blanc semi-transparent derrière les boutons."""
        panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        panel.fill((255, 255, 255, alpha))
        pygame.draw.rect(panel, (255, 255, 255, 60),
                         panel.get_rect(), 2, border_radius=18)
        surf.blit(panel, rect.topleft)

    def update_main(self):
        if self.play_button.update(self.game.mouse_pos, self.game.mouse_pressed):
            self.game.play()
        if self.quit_button.update(self.game.mouse_pos, self.game.mouse_pressed):
            self.game.quit()

    def update_game_over(self):
        if self.retry_button.update(self.game.mouse_pos, self.game.mouse_pressed):
            self.game.retry()
            return
        if self.menu_button.update(self.game.mouse_pos, self.game.mouse_pressed):
            self.game.to_menu()
        if self.quit_button.update(self.game.mouse_pos, self.game.mouse_pressed):
            self.game.quit()

    def render_main(self, surf):
        self._draw_bg(surf)
        self._draw_title(surf)

        self.play_button.render(surf)
        self.quit_button.render(surf)

    def render_game_over(self, surf):
        self._draw_bg(surf)

        bob = int(math.sin(self._tick * 0.05) * 3)
        surf.blit(self.game_over_surf, self.game_over_rect.move(0, bob))

        if self.death_surf:
            pad = 12
            box = self.death_rect.inflate(pad * 2, pad * 2)
            self._draw_panel(surf, box, alpha=60)
            surf.blit(self.death_surf, self.death_rect)

        top_btn = min(self.retry_button.rect.y, self.menu_button.rect.y, self.quit_button.rect.y)
        bot_btn = max(self.retry_button.rect.bottom, self.menu_button.rect.bottom, self.quit_button.rect.bottom)
        panel_rect = pygame.Rect(self.game.width // 2 - 120, top_btn - 12,
                                 240, bot_btn - top_btn + 24)
        self._draw_panel(surf, panel_rect)

        self.retry_button.render(surf)
        self.menu_button.render(surf)
        self.quit_button.render(surf)