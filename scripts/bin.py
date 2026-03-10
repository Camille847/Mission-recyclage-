import pygame
from random import random, choice
from scripts.utils import load_image


# load assets
log_image = load_image('log.png', (60, 30), scale=1.1)


bin_images = [
    load_image('Poubelle Bleue.png', (90, 40), scale=1.2),
    load_image('Poubelle Jaune.png', (90, 40), scale=1.2),
    load_image('rock1.png Maron', (90, 40), scale=1.2),
    load_image('rock2.png Verte', (90, 40), scale=1.2)
]

class Platform():
    """
    The base class for all platforms.
    """
    def __init__(self, game, center_x, bottom, image):
        self.game = game
        self.image = image
        self.rect = self.image.get_frect(centerx=center_x, bottom=bottom)
        self.color = 'grey'
        self.force = 0
        self.collectible = None
        self.offset = 10
        self.floating = True

    def remove(self):
        self.game.platforms.remove(self)

    def touch(self):
        pass

    def push(self):
        self.force = 5

    def in_screen(self, scroll):
        return self.rect.right - scroll < self.game.width and self.rect.left - scroll > 0

    def float(self, scroll):
        indices = range(
            max(0, int((self.rect.left - scroll) / self.game.water.spacing)),
            min(self.game.water.num_points, int((self.rect.right - scroll) / self.game.water.spacing))
        )
        y = sum(self.game.water.points[i] for i in indices) / len(indices)

        if self.force > 0:
            self.rect.bottom = y + self.force
            self.force -= 0.2
            if self.force <= 0:
                self.force = 0
        else:
            self.rect.bottom = y

    def update(self):
        pass

    def render(self, surf, scroll):
        pos = (self.rect.x - scroll, self.rect.y)
        if self.image:
            surf.blit(self.image, pos)
        else:
            pygame.draw.rect(surf, self.color, pos)



class Rock(Platform):
    """
    The biggest solid platform.
    """
    def __init__(self, game, center_x, bottom):
        img = choice(rock_images)
        super().__init__(game, center_x, bottom, img)
        self.color = 'darkgrey'


class Lilypad(Platform):
    """
    A platform that sinks into the water when the frog touches it for too long.
    """
    def __init__(self, game, center_x, bottom):
        img = choice(lilypad_images)
        super().__init__(game, center_x, bottom, img)
        self.color = 'forestgreen'
        self.timer = 2000
        self.sinking = False
        self.touched = False

    def sink(self):
        # start sinking into the water
        self.sinking = True
        self.touched = False
        self.floating = False

    def touch(self):
        self.touched = True

    def update(self):
        if self.touched:
            # wait 2 seconds before sinking
            self.timer -= self.game.dt
            if self.timer <= 0:
                self.sink()
        if self.sinking:
            # sink into the water
            if self.rect.top < self.game.height:
                self.rect.y += 7
            else:
                self.remove()


class Log(Platform):
    """
    A moving platform.
    """
    def __init__(self, game, center_x, bottom):
        super().__init__(game, center_x, bottom, log_image)
        self.color = 'brown'
        self.direction = 1 if random() > 0.5 else -1
        self.position = self.rect.centerx
        self.speed = (0.5 + random()) * 0.8

    def update(self):
        # infinitely move the platform
        self.rect.x += self.speed * self.direction
        if self.rect.right > self.position + 100 or self.rect.left < self.position - 100:
            self.direction *= -1

