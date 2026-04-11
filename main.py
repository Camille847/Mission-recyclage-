import pygame
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
    'assets/decor/Décor Bakery.png',
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

GRAVITY = 600


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
        self.bins_filled  = 0
        self.background = self.level_backgrounds[self.level]

        self._level_msg_timer = 0
        self._level_msg       = ''
        self._level_names     = ['Matin', 'Bakery', 'Soir']

        self.font_score = pygame.font.SysFont('arial', 26, bold=True)
        self.font_level = pygame.font.SysFont('arial', 22, bold=True)
        self.font_msg   = pygame.font.SysFont('arial', 42, bold=True)

        self.collectibles: list = []
        self.waste_manager = WasteManager(self)

        ground_y = self.height - 80
        self.kris = Kris(self, bottom=ground_y)
        self.ground_y = ground_y

        self.menu = Menu(self)

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
        self.level          = 0
        self.bins_filled    = 0
        self.background     = self.level_backgrounds[self.level]
        self._level_msg_timer = 0
        self._level_msg       = ''
        self.collectibles.clear()
        self.waste_manager.clear()
        self.kris = Kris(self, bottom=self.ground_y)
        self._spawn_bins()

    def _spawn_bins(self):
        self.collectibles.clear()
        colors  = list(BIN_CLASSES.keys())
        spacing = (self.width - self.width * 0.35) / BINS_PER_LEVEL
        x_start = self.width * 0.38
        for i, color in enumerate(colors):
            BinClass = BIN_CLASSES[color]
            bin_obj  = _make_bin(BinClass, self, x_start + i * spacing, self.ground_y)
            self.collectibles.append(bin_obj)

    def _advance_level(self):
        next_level = self.level + 1
        if next_level >= MAX_LEVEL:
            next_level = 0  # Boucle au premier niveau
        self.level       = next_level
        self.bins_filled = 0
        self.correct_per_color = {c: 0 for c in BAR_ORDER}
        self.background  = self.level_backgrounds[self.level]
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

            elif event.type == pygame.QUIT:
                self.quit()

        self.mouse_pos = pygame.mouse.get_pos()

        if self.in_game or self.game_over:
            self.window.blit(self.background, (0, 0))
        else:
            self.window.blit(self.level_backgrounds[0], (0, 0))


        if self.in_game and not self.game_over:
            for c in self.collectibles:
                c.render(self.window, scroll=0)

            self.kris.update(dt, self.mouse_pos, self.mouse_held, self.mouse_released)
            self.kris.render(self.window, scroll=0)

            # Trajectoire : on simule jusqu'à ce que le projectile touche le sol
            # ou sorte de l'écran, avec des points espacés régulièrement
            if self.kris.charging and self.kris.power > 0:
                ipos = (self.kris.rect.right, self.kris.rect.centery)

                step = 0.02  # plus grand = trajectoire plus longue affichée
                t = step
                prev_point = None

                for i in range(12):
                    x, y = move(ipos, self.kris.angle, self.kris.power, t, GRAVITY)
                    t += step

                    if x < 0 or x > self.width + 100:
                        break
                    if y > self.ground_y:
                        break

                    if i % 2 == 0:
                        alpha = int(255 * (1 - t / 60))  # fondu vers la fin
                        radius = 6
                        pygame.draw.circle(self.window, (255, 0, 0), (int(x), int(y)), radius)

            self.waste_manager.update(scroll=0, dt=dt)
            self.waste_manager.render(self.window, scroll=0)

            self._render_hud()

            if self.menu.death_surf and self.menu.death_rect:
                self.window.blit(self.menu.death_surf, self.menu.death_rect)

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
            self.menu.update_main()
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