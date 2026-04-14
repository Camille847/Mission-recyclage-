import pygame
import random
pygame.init()

from scripts.utils import move
from scripts.waste import WasteManager
from scripts.bin import BIN_CLASSES
from scripts.Kris import Kris
from scripts.menu import Menu
from scripts.client import Client, TextInput, blit_center

WIDTH  = 800
HEIGHT = 600
SIZE   = (WIDTH, HEIGHT)

def load_bg(path, size):
    return pygame.transform.smoothscale(
        pygame.image.load(path).convert_alpha(),
        size
    )


LEVEL_BACKGROUNDS_PATHS = [
    'assets/decor/Décor Matin.png',
    'assets/decor/Décor Cafét.png',
    'assets/decor/Décor Nuit.png',
]

MAX_LEVEL = len(LEVEL_BACKGROUNDS_PATHS)

BINS_PER_LEVEL    = 4
SCORE_PER_CORRECT = 100
PENALTY_WRONG     = 50
MAX_LIVES         = 3
MAX_CORRECT       = 5  # segments par barre = MAX_WASTE dans bin.py

BAR_COLORS = {
    'blue':   (70,  130, 210),
    'yellow': (230, 200,  40),
    'brown':  (140,  90,  40),
    'green':  ( 50, 170,  60),
}
BAR_ORDER = ['blue', 'yellow', 'brown', 'green']

GRAVITY = 800

# Délai entre chaque apparition de poubelle au niveau nuit (en ms) — doublé
NIGHT_SPAWN_INTERVAL = 4000


class Game:

    def __init__(self):
        self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption('Mission Recyclage')
        self.width, self.height = self.window.get_size()
        self.level_backgrounds = [load_bg(p, (self.width, self.height)) for p in LEVEL_BACKGROUNDS_PATHS]
        self.clock   = pygame.time.Clock()
        self.running = False

        self.in_game   = False
        self.game_over = False

        self.mouse_pos      = (0, 0)
        self.mouse_pressed  = False
        self.mouse_held     = False
        self.mouse_released = False
        self.events         = []

        self.score = 0
        self.lives = MAX_LIVES

        self.correct_per_color = {c: 0 for c in BAR_ORDER}

        self.level        = 0
        self.selected_level = 0
        self.bins_filled  = 0
        self.background = self.level_backgrounds[self.level]

        self._level_msg_timer = 0
        self._level_msg       = ''
        self._level_names     = ['Matin', 'Cafét', 'Soir']

        self.font_score = pygame.font.SysFont('arial', 26, bold=True)
        self.font_level = pygame.font.SysFont('arial', 32, bold=True)
        self.font_msg   = pygame.font.SysFont('arial', 42, bold=True)

        self.collectibles: list = []
        self.waste_manager = WasteManager(self)

        # Ground levels per level (to account for different decor heights)
        self.ground_ys = [self.height - 80, self.height - 80, self.height - 100]
        self.ground_y = self.ground_ys[self.level]

        self.kris = Kris(self, bottom=self.ground_y)
        self.menu = Menu(self)
        
        # Bouton menu principal pendant le jeu
        from scripts.menu import Button
        self.in_game_menu_button = Button(self.width - 100, 20, "Menu", danger=False)
        self.in_game_menu_button.rect.width = 80
        self.in_game_menu_button.rect.height = 30
        self.in_game_menu_button.rect.right = self.width - 20
        self.in_game_menu_button.rect.top = 75
        self.in_game_menu_button.font = pygame.font.SysFont('arial', 16, bold=True)
        self.in_game_menu_button.rendered_text = self.in_game_menu_button.font.render(self.in_game_menu_button.text, True, (245, 245, 245))
        self.in_game_menu_button.text_rect = self.in_game_menu_button.rendered_text.get_rect(center=self.in_game_menu_button.rect.center)
        self.in_game_menu_button._shadow_rect = self.in_game_menu_button.rect.move(2, 3)

        self.client = Client('mission_recyclage')
        self.message       = ''
        self.message_timer = 0
        self.text_input    = TextInput(
            (self.width / 2, self.height - 75),
            self.set_username,
            'pseudo'
        )
        if self.client.registered:
            self.text_input.text = self.client.username
            self.text_input.resize()

        self.game_completed = False

        # File d'attente pour le spawn séquentiel au niveau nuit
        self._pending_bins: list = []   # liste de (color, x)
        self._spawn_timer: float = 0    # ms restantes avant prochain spawn

    def set_username(self, username):
        if self.client.registered:
            res = self.client.setUsername(username)
        else:
            res = self.client.register(username)
        if 'error' in res:
            self.message       = res['error']
            self.message_timer = 10000

    def _score_thread(self, score):
        high = self.client.getMinScore()
        if score > high:
            err = self.client.sendScore(score)
            if err:
                print(err)

    def play(self):
        self.level = self.selected_level
        self.background = self.level_backgrounds[self.level]
        self.ground_y = self.ground_ys[self.level]
        self.in_game = True
        self.mouse_pressed  = False
        self.mouse_held     = False
        self.mouse_released = False
        self._spawn_bins()

    def retry(self):
        self._reset()
        self.in_game = True

    def to_menu(self):
        self._reset()
        self.game_completed = False
        self.menu.show_menu_bg = True
        self.in_game = False

    def quit(self):
        self.running = False

    def _reset(self):
        self.mouse_pressed  = False
        self.mouse_held     = False
        self.mouse_released = False
        self.game_over      = False
        self.score          = 0
        self.lives          = MAX_LIVES
        self.correct_per_color = {c: 0 for c in BAR_ORDER}
        self.level          = self.selected_level
        self.bins_filled    = 0
        self.background     = self.level_backgrounds[self.level]
        self.ground_y       = self.ground_ys[self.level]
        self._level_msg_timer = 0
        self._level_msg       = ''
        self._pending_bins    = []
        self._spawn_timer     = 0
        self.collectibles.clear()
        self.waste_manager.clear()
        self.kris = Kris(self, bottom=self.ground_y)
        self._spawn_bins()

    # ------------------------------------------------------------------
    # Spawn des poubelles
    # ------------------------------------------------------------------

    def _spawn_bins(self):
        self.collectibles.clear()
        self._pending_bins = []
        self._spawn_timer  = 0

        colors = list(BIN_CLASSES.keys())

        if self.level == 1:
            positions = [350, 600, 850, 1100]

        elif self.level == 2:
            # Niveau nuit : les poubelles spawent hors écran à droite,
            # espacées pour ne jamais se chevaucher à l'apparition
            positions = [self.width + 80 + i * 60 for i in range(BINS_PER_LEVEL)]

        else:
            # Niveaux autres (matin) : positions aléatoires en évitant Kris
            min_x = int(self.width * 0.3)
            max_x = int(self.width - 100)
            min_dist_to_kris = 150
            min_dist_between = 120

            positions = []
            kris_x = self.kris.rect.centerx

            for i in range(BINS_PER_LEVEL):
                attempts = 0
                while attempts < 100:
                    x = random.randint(min_x, max_x)
                    if abs(x - kris_x) < min_dist_to_kris:
                        attempts += 1
                        continue
                    too_close = any(abs(x - px) < min_dist_between for px in positions)
                    if not too_close:
                        positions.append(x)
                        break
                    attempts += 1
                else:
                    x = min_x + i * (max_x - min_x) // BINS_PER_LEVEL
                    positions.append(x)

        if self.level == 2:
            # Spawn séquentiel : prépare la file, spawne la première immédiatement
            pairs = list(zip(colors, positions))
            random.shuffle(pairs)
            self._pending_bins = pairs
            self._spawn_next_bin()
        else:
            for i, color in enumerate(colors):
                x = positions[i]
                BinClass = BIN_CLASSES[color]
                bin_obj = _make_bin(BinClass, self, x, self.ground_y)
                self.collectibles.append(bin_obj)

    def _spawn_next_bin(self):
        """Retire la prochaine entrée de la file et crée la poubelle."""
        if not self._pending_bins:
            return
        color, x = self._pending_bins.pop(0)
        BinClass = BIN_CLASSES[color]
        bin_obj  = _make_bin(BinClass, self, x, self.ground_y)
        self.collectibles.append(bin_obj)
        if self._pending_bins:
            self._spawn_timer = NIGHT_SPAWN_INTERVAL

    # ------------------------------------------------------------------

    def _advance_level(self):
        next_level = self.level + 1
        if next_level >= MAX_LEVEL:
            self.game_completed = True
            self.in_game = False
            self.menu.show_menu_bg = False
            self.menu.in_level_select = False
            self.menu.in_rules = False
            return

        self.level       = next_level
        self.bins_filled = 0
        self.correct_per_color = {c: 0 for c in BAR_ORDER}
        self.background  = self.level_backgrounds[self.level]
        self.ground_y    = self.ground_ys[self.level]
        name = self._level_names[self.level]
        self._level_msg       = f'Niveau {self.level + 1} – {name} !'
        self._level_msg_timer = 2500
        self.waste_manager.clear()
        self._spawn_bins()

    def on_bin_filled(self):
        self.bins_filled += 1
        if self.bins_filled >= BINS_PER_LEVEL:
            self._advance_level()

    def on_correct_bin(self, waste):
        self.score += SCORE_PER_CORRECT
        color = waste.bin_color
        if color in self.correct_per_color:
            self.correct_per_color[color] = min(
                self.correct_per_color[color] + 1, MAX_CORRECT
            )

    def on_wrong_bin(self, waste, bin_obj):
        self.lives -= 1
        self.score  = max(0, self.score - PENALTY_WRONG)
        self.menu.new_message()

    def _trigger_game_over(self):
        self.game_over = True
        self.in_game   = False
        self.menu.new_message()
        if self.client.connected and self.client.registered:
            self.client.thread(self._score_thread, args=(self.score,))

    def update(self):
        dt_ms = self.clock.tick(60)
        dt    = dt_ms / 1000.0

        pygame.display.set_caption(f'Mission Recyclage – {int(self.clock.get_fps())} fps')

        self.events         = pygame.event.get()
        self.mouse_pressed  = False
        self.mouse_released = False

        for event in self.events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.mouse_pressed = True
                self.mouse_held    = True
                if not self.in_game and not self.game_over:
                    if self.text_input.hovered:
                        self.text_input.focus = True
                    elif self.text_input.focus:
                        self.text_input.exit()

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.mouse_released = True
                self.mouse_held     = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.quit()
                elif event.key == pygame.K_r and self.in_game:
                    self._reset()
                    self.in_game = True
                elif event.key == pygame.K_n and self.in_game:
                    self._advance_level()

            elif event.type == pygame.QUIT:
                self.quit()

        self.mouse_pos = pygame.mouse.get_pos()

        if self.in_game or self.game_over:
            if self.game_over:
                self.window.fill((100, 100, 100))
            else:
                self.window.blit(self.background, (0, 0))
        else:
            self.window.blit(self.level_backgrounds[0], (0, 0))

        if self.in_game and not self.game_over:
            # ---- Spawn séquentiel (niveau nuit uniquement) ----
            if self.level == 2 and self._pending_bins:
                self._spawn_timer -= dt_ms
                if self._spawn_timer <= 0:
                    self._spawn_next_bin()

            for c in self.collectibles:
                c.render(self.window, scroll=0)

            self.kris.update(dt, self.mouse_pos, self.mouse_held, self.mouse_released)
            for c in self.collectibles:
                c.update(dt)
            self.kris.render(self.window, scroll=0)

            # Trajectoire simulée
            if self.kris.charging and self.kris.power > 0:
                ipos = (self.kris.rect.right, self.kris.rect.centery)
                step = 0.016
                t = step
                point_count = 0

                while t < 10:
                    x, y = move(ipos, self.kris.angle, self.kris.power, t, GRAVITY)
                    t += step
                    if x < 0 or x > self.width + 100:
                        break
                    if y > self.ground_y:
                        break
                    if point_count % 2 == 0:
                        pygame.draw.circle(self.window, (255, 0, 0), (int(x), int(y)), 3)
                    point_count += 1

            self.waste_manager.update(scroll=0, dt=dt)
            self.waste_manager.render(self.window, scroll=0)

            self._render_hud()

            if self.menu.death_surf and self.menu.death_rect:
                 self.window.blit(self.menu.death_surf, self.menu.death_rect)
             
             # Bouton menu pendant le jeu
            if self.in_game_menu_button.update(self.mouse_pos, self.mouse_pressed):
                 self.to_menu()

            if self._level_msg_timer > 0:
                 self._level_msg_timer -= dt_ms
                 self._render_level_message()

        elif self.game_over:
            for c in self.collectibles:
                c.render(self.window, scroll=0)
            self._render_hud()
            self.menu.update_game_over()
            self.menu.render_game_over(self.window)

        else:
            if self.game_completed:
                self.menu.update_victory()
                self.menu.render_victory(self.window)

            elif self.menu.in_rules:
                self.menu.update_rules()
                self.menu.render_rules(self.window)

            elif self.menu.in_level_select:
                self.menu.update_level_select()
                self.menu.render_level_select(self.window)

            else:
                self.menu.update_main()
                self.menu.render_main(self.window)

            if self.menu.in_rules:
                self.menu.render_rules(self.window)
            elif self.menu.in_level_select:
                self.menu.render_level_select(self.window)
            elif self.game_completed:
                self.menu.render_victory(self.window)
            else:
                self.menu.render_main(self.window)

            if self.message_timer > 0:
                self.message_timer -= dt_ms
                if self.message_timer <= 0:
                    self.message = ''
                else:
                    font = self.text_input.font
                    surf, _ = font.render(self.message, 'red', size=20)
                    blit_center(self.window, surf, (self.width / 2, 285))

        pygame.display.flip()

    def _render_hud(self):
        score_surf = self.font_score.render(f'Score : {self.score}', True, (255, 220, 40))
        self.window.blit(score_surf, (10, 8))

        seg_w   = 22
        seg_h   = 10
        seg_gap = 3
        bar_gap = 10
        bx      = 10
        by      = 38

        for i, color_name in enumerate(BAR_ORDER):
            color = BAR_COLORS[color_name]
            count = self.correct_per_color[color_name]
            x = bx + i * (MAX_CORRECT * (seg_w + seg_gap) + bar_gap)
            for s in range(MAX_CORRECT):
                rx = x + s * (seg_w + seg_gap)
                rect = pygame.Rect(rx, by, seg_w, seg_h)
                if s < count:
                    pygame.draw.rect(self.window, color, rect, border_radius=3)
                    lighter = tuple(min(c + 60, 255) for c in color)
                    highlight = pygame.Rect(rx + 2, by + 1, seg_w - 4, 3)
                    pygame.draw.rect(self.window, lighter, highlight, border_radius=2)
                else:
                    pygame.draw.rect(self.window, (30, 30, 30), rect, border_radius=3)
                pygame.draw.rect(self.window, (20, 20, 20), rect, 1, border_radius=3)

        name = self._level_names[self.level]
        level_surf = self.font_level.render(f'Niveau {self.level + 1} – {name}', True, (200, 240, 200))
        self.window.blit(level_surf, (self.width - level_surf.get_width() - 12, 8))

        prog_surf = self.font_level.render(
             f'Poubelles : {self.bins_filled}/{BINS_PER_LEVEL}', True, (200, 240, 200)
         )
        self.window.blit(prog_surf, (self.width - prog_surf.get_width() - 12, 34))
         
         # Dessiner le bouton menu
        self.in_game_menu_button.render(self.window)

    def _render_level_message(self):
        surf   = self.font_msg.render(self._level_msg, True, (255, 240, 80))
        shadow = self.font_msg.render(self._level_msg, True, (60, 40, 0))
        cx, cy = self.width // 2, self.height // 2 - 60
        self.window.blit(shadow, shadow.get_rect(center=(cx + 3, cy + 3)))
        self.window.blit(surf,   surf.get_rect(center=(cx, cy)))

    def run(self):
        self.running = True
        while self.running:
            self.update()
        pygame.quit()


class _FakePlatform:
    def __init__(self, cx, bottom):
        self.rect        = pygame.Rect(cx - 40, bottom, 80, 10)
        self.collectible = None


def _make_bin(BinClass, game, cx, ground_y):
    plat = _FakePlatform(cx, ground_y)
    return BinClass(plat, game)


if __name__ == '__main__':
    game = Game()
    game.run()