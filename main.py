
import pygame
pygame.init()

from math import pi
from random import random, randint, choice



from scripts.menu import Menu

background = pygame.image.load('assets/background.png')
menu_music = './assets/menu_music.mp3'
ingame_music = './assets/ingame_music.mp3'
death_sound = pygame.mixer.Sound('./assets/death_frog.mp3')

 def quit(self):
        self.running = False

    def set_username(self, username):
        if self.client.registered:
            res = self.client.setUsername(username)
        else:
            res = self.client.register(username)
        if 'error' in res:
            self.message = res['error']
            self.message_timer = 10000

    def score_thread(self, score):
        high_score = self.client.getMinScore()
        if score > high_score:
            response = self.client.sendScore(score)
            if response:
                print(response)

    def play(self):
        # start the game
        self.in_game = True
        play(ingame_music)

    def retry(self):
        # start a new game
        self.reset()
        self.in_game = True

    def to_menu(self):
        # return to the menu after game over screen
        play(menu_music)
        self.reset()
        self.in_game = False

    def reset(self):
        # reset the game variables and environment to prepare the next one
        self.mouse_pressed = False
        self.game_over = False
        for c in self.active_bonuses:
            if c is not None:
                c.counter_effect(self)
        self.water.reset()
        self.platforms = [ Rock(self, WIDTH / 3, self.water.top) ]
        self.frog = Frog(WIDTH / 3, self.platforms[0].rect.top)
        self.particles.clear()
        self.collectibles.clear()
        self.fishes.clear()
        self.scroll = 0
        self.power = 0
        self.charging = False
        self.charging_time = 0
        self.score_hud.reset()
        self.active_bonuses.clear()

    def update(self):
        """
        Update and render the game.
        """
        self.dt = self.clock.tick(60)
        pygame.display.set_caption('La Rainette - Fps: ' + str(int(self.clock.get_fps())))

        # parse events
        self.events = pygame.event.get()
        for event in self.events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.mouse_pressed = True
                # start charging jump power when the mouse is pressed
                if event.button == 1 and self.in_game and not self.frog.jumping:
                    self.charging = True
                if event.button == 1 and not self.in_game and not self.game_over:
                    if self.text_input.hovered:
                        if not self.text_input.focus:
                            self.text_input.focus = True
                    elif self.text_input.focus:
                        self.text_input.exit()

            elif event.type == pygame.MOUSEBUTTONUP:
                self.mouse_pressed = False
                # make the frog jump on mouse release
                if event.button == 1 and self.in_game and self.charging and not self.frog.jumping:
                    self.frog.jump(self.power, self.angle)
                    self.power_hud.reset()
                    self.charging = False
                    self.charging_time = 0
                    self.power = 0

            # some keyboard shortcuts
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.reset()
                elif event.key == pygame.K_ESCAPE:
                    self.quit()

            elif event.type == pygame.QUIT:
                self.quit()

        self.mouse_pos = pygame.mouse.get_pos()

        # draw the background and update the water
        self.window.blit(background, (0, 0))
        self.water.update()
        self.water.render(self.window)

        # update and render the platforms
        if self.in_game or self.game_over:
            for tile in self.platforms:
                if tile.floating:
                    if tile.in_screen(self.scroll):
                        tile.float(self.scroll)
                    else:
                        tile.rect.bottom = self.water.top
                    tile.rect.y += tile.offset
                    # move the bonus
                    if tile.collectible:
                        tile.collectible.rect.bottom = tile.rect.top + 5
                        tile.collectible.rect.centerx = tile.rect.centerx
                tile.update()
                tile.render(self.window, self.scroll)
                # remove off-screen platforms
                if tile.rect.right - self.scroll < -100:
                    tile.remove()

        prev = self.platforms[-1]

        # in game events
        if self.in_game and not self.game_over:
            # create a new platform
            if WIDTH - prev.rect.right + self.scroll > 200:
                platform = choice([Rock, Log, Lilypad])
                dist = randint(180, 280)
                self.platforms.append(platform(self, prev.rect.right + dist, self.water.top))
                # add a bonus
                if self.score_hud.score > 2000 and len(self.active_bonuses) < 3 and not self.collectibles and random() < 0.18:
                    c = None
                    while c in self.active_bonuses or c is None:
                        c = choice(collectibles)
                    self.collectibles.append(c(self.platforms[-1], self))

            # calculate jumping angle
            position = (self.frog.rect.centerx - self.scroll, self.frog.rect.centery)
            self.angle = get_angle(self.mouse_pos, position)

            # update jump preview
            if self.power > 0:
                t = 0
                ipos = self.frog.rect.center
                # simulate the frog jump over time
                for i in range(10):
                    t += 0.4
                    x, y = move(ipos, self.angle, self.power, t, self.g)
                    pygame.draw.circle(self.window, 'red', (x - self.scroll, y), 2)

            # increase the frog charging power and update the hud
            if self.charging:
                self.charging_time += self.dt
                ratio = min(self.charging_time / 1600, 1)
                self.power = self.power_min + (self.power_max - self.power_min) * (ratio ** 1.4)
                self.power_hud.set(clamp(int(ratio * 5), 0, 4))
                self.power_hud.render(self.window)

            # update and render the frog
            self.frog.update(self.dt, self.platforms, self.g)
            self.frog.render(self.window, self.scroll)

            # update scrolling accordingly to the frog movement
            prev_scroll = self.scroll
            self.scroll = int(smooth(self.scroll, self.frog.rect.centerx - WIDTH // 3, self.dt, self.camera_slowness))

            # update the score
            if self.frog.jumping:
                diff = self.scroll - prev_scroll
                if diff > 0:
                    self.score_hud.update(diff)

            # check if the frog falls into water and handle game over transition
            if self.frog.rect.bottom >= self.water.top:
                self.game_over = True
                self.in_game = False
                self.menu.new_message()
                self.charging = False
                if self.client.connected and self.client.registered:
                    self.client.thread(self.score_thread, args=(self.score_hud.score,))
                death_sound.play()
                # add water particles
                self.water.splash(int((self.frog.rect.centerx - self.scroll) // self.water.spacing), -16)
                for i in range(50):
                    p_angle = (5 * pi/ 12) + (random() * (2*pi/12))
                    p_speed = randint(40, 50)
                    self.particles.append(SplashParticle(self.frog.rect.centerx, self.water.top, p_angle, p_speed))

            # update and render bonuses
            for c in self.collectibles:
                if self.frog.collide(c):
                    self.active_bonuses.append(type(c))
                    c.effect()
                    c.remove()
                else:
                    c.render(self.window, self.scroll)

        # spawn a fish
        if random() < 0.002:
            pos = (prev.rect.right + 200, randint(self.water.top + 30, HEIGHT - 20))
            self.fishes.append(Fish(pos))

        # update and render the fishes
        for f in self.fishes:
            f.update()
            if not f.alive:
                self.fishes.remove(f)
            else:
                f.render(self.window, self.scroll)

        # update and render water particles
        for p in self.particles:
            p.update(self.dt)
            p.render(self.window, self.scroll)
            if p.rect.bottom > self.water.top:
                self.particles.remove(p)

        # display the score
        if self.in_game or self.game_over:
            self.score_hud.render(self.window, 100 if self.game_over else 0)

        # update the menus
        if not self.in_game:
            if self.game_over:
                self.menu.update_game_over()
                self.menu.render_game_over(self.window)
            else:
                self.menu.update_main()
                self.menu.render_main(self.window)
                if self.message_timer > 0:
                    self.message_timer -= self.dt
                    if self.message_timer <= 0:
                        self.message = ''
                    else:
                        blit_center(self.window, self.text_input.font.render(self.message, 'black', size=20)[0], (WIDTH / 2, 285))

                self.text_input.update(self.events)
                self.text_input.render(self.window)

        pygame.display.flip()

    def run(self):
        self.running = True
        while self.running:
            self.update()
        pygame.quit()

if __name__ == '__main__':
    game = Game()
    game.run()
