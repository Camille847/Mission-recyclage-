import pygame
pygame.init()

from random import random, randint, choice

from scripts.utils import get_angle, smooth, move, clamp, play
from scripts.waste import WasteManager, WASTE_TYPES
from scripts.collectibles import BlueBin, YellowBin, BrownBin, GreenBin, BIN_CLASSES
from scripts.Kris import Kris
from scripts.menu import Menu
from scripts.client import Client, TextInput, blit_center

WIDTH  = 800
HEIGHT = 600
SIZE   = (WIDTH, HEIGHT)

menu_music   = './assets/menu_music.mp3'
ingame_music = './assets/ingame_music.mp3'
wrong_sound  = pygame.mixer.Sound('./assets/death_frog.mp3')   # son erreur de tri

background = pygame.image.load('assets/background.png')

BINS_PER_LEVEL   = 4    # nombre de poubelles présentes simultanément
SCORE_PER_CORRECT = 100  # points par bon tri
PENALTY_WRONG     = 50   # pénalité par mauvais tri
MAX_LIVES         = 3    # vies du joueur


class Game:
    """
    Classe principale du jeu Mission Recyclage.
    Structure calquée sur La Rainette : même event loop, mêmes états.
    """

    def __init__(self):
        self.width  = WIDTH
        self.height = HEIGHT
        self.window = pygame.display.set_mode(SIZE, pygame.FULLSCREEN | pygame.SCALED)
        pygame.display.set_caption('Mission Recyclage')
        self.clock   = pygame.time.Clock()
        self.running = False

        self.in_game   = False
        self.game_over = False

        self.mouse_pos      = (0, 0)
        self.mouse_pressed  = False   # True la frame du clic
        self.mouse_held     = False   # True tant que maintenu
        self.mouse_released = False   # True la frame du relâchement
        self.events         = []

        self.score = 0
        self.lives = MAX_LIVES
        self.font_score = pygame.font.Font('assets/ComicNeue-Bold.ttf', 36)
        self.font_lives = pygame.font.Font('assets/ComicNeue-Bold.ttf', 28)

        self.collectibles: list = []   # poubelles actives
        self.waste_manager = WasteManager(self)

        ground_y = HEIGHT - 80
        self.kris = Kris(self, bottom=ground_y)

        self.ground_y = ground_y

        self.menu = Menu(self)
        play(menu_music)

        self.client = Client('mission_recyclage')
        self.message       = ''
        self.message_timer = 0
        self.text_input    = TextInput(
            (WIDTH / 2, HEIGHT - 75),
            self.set_username,
            'pseudo'
        )
        if self.client.registered:
            self.text_input.text = self.client.username
            self.text_input.resize()

        self._preview_dots = 12


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
        play(ingame_music)
        self._spawn_bins()

    def retry(self):
        self._reset()
        self.in_game = True

    def to_menu(self):
        play(menu_music)
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
        self.collectibles.clear()
        self.waste_manager.clear()
        self.kris = Kris(self, bottom=self.ground_y)
        self._spawn_bins()


    def _spawn_bins(self):
        """Place BINS_PER_LEVEL poubelles réparties sur la droite de l'écran."""
        self.collectibles.clear()
        colors  = list(BIN_CLASSES.keys())
        chosen  = colors[:]
        # une poubelle de chaque couleur présente parmi les 4
        spacing = (WIDTH - WIDTH * 0.35) / BINS_PER_LEVEL
        x_start = WIDTH * 0.38

        for i, color in enumerate(chosen):
            BinClass = BIN_CLASSES[color]
            # on crée un faux objet "platform" minimal pour satisfaire Collectible.__init__
            bin_obj = _make_bin(BinClass, self, x_start + i * spacing, self.ground_y)
            self.collectibles.append(bin_obj)


    def on_correct_bin(self, waste):
        self.score += SCORE_PER_CORRECT

    def on_wrong_bin(self, waste, bin_obj):
        wrong_sound.play()
        self.lives -= 1
        self.score  = max(0, self.score - PENALTY_WRONG)
        self.menu.new_message()   # rappel de tri affiché à l'écran
        if self.lives <= 0:
            self._trigger_game_over()

    def _trigger_game_over(self):
        self.game_over = True
        self.in_game   = False
        self.menu.new_message()
        if self.client.connected and self.client.registered:
            self.client.thread(self._score_thread, args=(self.score,))


    def update(self):
        dt_ms = self.clock.tick(60)
        dt    = dt_ms / 1000.0   # secondes
        pygame.display.set_caption(f'Mission Recyclage – {int(self.clock.get_fps())} fps')

        self.events         = pygame.event.get()
        self.mouse_pressed  = False
        self.mouse_released = False

        for event in self.events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.mouse_pressed = True
                self.mouse_held    = True

                # Gestion TextInput menu
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

        self.window.blit(background, (0, 0))

        pygame.draw.rect(self.window, (60, 40, 20),
                         (0, self.ground_y, WIDTH, HEIGHT - self.ground_y))

        # ── Jeu actif ─────────────────────────────────────────────────────────
        if self.in_game and not self.game_over:

            # Poubelles
            for c in self.collectibles:
                c.render(self.window, scroll=0)

            if self.kris.charging and self.kris.power > 0:
                t = 0.0
                for _ in range(self._preview_dots):
                    t += 0.04
                    px, py = move(
                        (self.kris.rect.right, self.kris.rect.centery),
                        self.kris.angle,
                        self.kris.power,
                        t,
                        800   # même gravité que waste.py
                    )
                    if 0 < px < WIDTH and 0 < py < HEIGHT + 100:
                        pygame.draw.circle(self.window, (255, 80, 80), (int(px), int(py)), 3)

            self.kris.update(dt, self.mouse_pos,
                             self.mouse_held, self.mouse_released)
            self.kris.render(self.window, scroll=0)

            self.waste_manager.update(scroll=0, dt=dt)
            self.waste_manager.render(self.window, scroll=0)

            self._render_hud()

            if self.menu.death_surf and self.menu.death_rect:
                self.window.blit(self.menu.death_surf, self.menu.death_rect)

        elif self.game_over:
            for c in self.collectibles:
                c.render(self.window, scroll=0)
            self._render_hud()
            self.menu.update_game_over()
            self.menu.render_game_over(self.window)

        # ── Menu principal ────────────────────────────────────────────────────
        else:
            self.menu.update_main()
            self.menu.render_main(self.window)

            # Leaderboard / TextInput
            if self.message_timer > 0:
                self.message_timer -= dt_ms
                if self.message_timer <= 0:
                    self.message = ''
                else:
                    font = self.text_input.font
                    surf, _ = font.render(self.message, 'red', size=20)
                    blit_center(self.window, surf, (WIDTH / 2, 285))

            self.text_input.update(self.events)
            self.text_input.render(self.window)

        pygame.display.flip()


    def _render_hud(self):
        # Score
        score_surf = self.font_score.render(f'Score : {self.score}', True, (255, 220, 40))
        self.window.blit(score_surf, (10, 10))

        # Vies (cœurs texte)
        hearts = '❤ ' * self.lives + '🖤 ' * (MAX_LIVES - self.lives)
        lives_surf = self.font_lives.render(f'Vies : {self.lives}/{MAX_LIVES}', True, (220, 80, 80))
        self.window.blit(lives_surf, (10, 52))

    # ── Run ───────────────────────────────────────────────────────────────────

    def run(self):
        self.running = True
        while self.running:
            self.update()
        pygame.quit()



class _FakePlatform:
    """Shim minimal pour satisfaire Collectible.__init__ qui attend un platform."""
    def __init__(self, cx, bottom):
        self.rect       = pygame.Rect(cx - 40, bottom - 10, 80, 10)
        self.collectible = None


def _make_bin(BinClass, game, cx, ground_y):
    plat = _FakePlatform(cx, ground_y)
    return BinClass(plat, game)



if __name__ == '__main__':
    game = Game()
    game.run()