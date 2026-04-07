import pygame
import random
import math

def _font(size):
    return pygame.font.SysFont('arial', size, bold=True)


COLOR_BG_TOP      = (135, 206,  235)   # bleu ciel doux
COLOR_BG_BOT      = (144,  238,  144) # vert clair,lumineux
COLOR_PANEL       = (255, 255, 255, 150)  # blanc doux, semi-transparent
COLOR_PANEL_BORDER = (200, 200, 200) # léger contour pour délimiter

BTN_DEFAULT       = (56,  168,  77) #vert joyeux
BTN_HOVER         = (34,  139,  54) #vert plus foncé
BTN_CLICK         = (20,   90,  35)  #vert sombre
BTN_DANGER        = (255, 99, 71) # rouge tomate doux
BTN_DANGER_HOVER  = (200,  50,  30)
BTN_TEXT          = (255, 255, 255) #blanc

TITLE_COLOR       = (255, 215, 50)   # jaune recyclage
TITLE_SHADOW      = (80, 50, 10)
SUBTITLE_COLOR    = (160, 255, 140)
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

        self.font = _font(32)
        self.rendered_text  = self.font.render(self.text, True, BTN_TEXT)

        w, h = 200, 46
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
        pygame.draw.rect(surface, (0, 0, 0, 80), self._shadow_rect, border_radius=14)
        pygame.draw.rect(surface, self.color, self.rect, border_radius=14)
        highlight = pygame.Rect(self.rect.x + 4, self.rect.y + 3, self.rect.width - 8, 4)
        pygame.draw.rect(surface, (*[min(c + 60, 255) for c in self.color[:3]],), highlight, border_radius=4)
        surface.blit(self.rendered_text, self.text_rect)


class Menu:
    """Menu principal et écran Game Over du jeu Mission Recyclage."""

    def __init__(self, game):
        self.game  = game
        self._tick = 0   # compteur pour animations

        title_font = _font(82)
        self.title_surf  = title_font.render('Mission', True, TITLE_COLOR)
        self.title_rect  = self.title_surf.get_rect(center=(game.width / 2, 85))

        title2_font = _font(68)
        self.title2_surf = title2_font.render('♻ Recyclage !', True, TITLE_COLOR)
        self.title2_rect = self.title2_surf.get_rect(center=(game.width / 2, 160))

        self.title_shadow_surf  = title_font.render('Mission',        True, TITLE_SHADOW)
        self.title2_shadow_surf = title2_font.render('♻ Recyclage !', True, TITLE_SHADOW)

        sub_font = _font(22)
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

        self._leaves = [
            (50,  60,  28, 30),
            (game.width - 60, 80,  22, 130),
            (30,  game.height - 80, 20, 50),
            (game.width - 45, game.height - 70, 26, 160),
            (game.width // 2 - 220, 140, 16, 10),
            (game.width // 2 + 230, 150, 18, 170),
        ]

        self._bg = pygame.Surface((game.width, game.height))
        for y in range(game.height):
            t = y / game.height
            r = int(COLOR_BG_TOP[0] * (1 - t) + COLOR_BG_BOT[0] * t)
            g = int(COLOR_BG_TOP[1] * (1 - t) + COLOR_BG_BOT[1] * t)
            b = int(COLOR_BG_TOP[2] * (1 - t) + COLOR_BG_BOT[2] * t)
            pygame.draw.line(self._bg, (r, g, b), (0, y), (game.width, y))

    def new_message(self):
        msg  = random.choice(self.death_messages)
        surf = self.death_font.render(msg, True, (255, 240, 180))
        self.death_surf = surf
        self.death_rect = surf.get_rect(center=(self.game.width / 2, self.game.height - 80))

    def _draw_bg(self, surf):
        surf.blit(self._bg, (0, 0))
        self._tick += 1
        for i, (lx, ly, size, angle) in enumerate(self._leaves):
            wobble = math.sin(self._tick * 0.03 + i) * 5
            pts = _leaf_points(lx, ly + wobble, size, angle)
            leaf_surf = pygame.Surface((surf.get_width(), surf.get_height()), pygame.SRCALPHA)
            pygame.draw.polygon(leaf_surf, (80, 200, 100, 140), pts)
            surf.blit(leaf_surf, (0, 0))

    def _draw_title(self, surf):
        surf.blit(self.title_shadow_surf,  self.title_rect.move(3, 4))
        surf.blit(self.title2_shadow_surf, self.title2_rect.move(3, 4))
        bob = int(math.sin(self._tick * 0.05) * 3)
        surf.blit(self.title_surf,  self.title_rect.move(0, bob))
        surf.blit(self.title2_surf, self.title2_rect.move(0, bob))
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

        panel_rect = pygame.Rect(self.game.width // 2 - 120,
                                 self.play_button.rect.y - 16,
                                 240, 90)
        self._draw_panel(surf, panel_rect)

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