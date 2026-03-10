import pygame

from scripts.utils import move, load_image
from scripts.bin import


scale = 0.15

images = {
    'idle': load_image('Kris.png', scale=scale),
    'jumping': load_image('Kris 2.png', scale=scale)
}
images_divided = {}
for state, img in images.items():
    images_divided[state] = pygame.transform.scale(img, (img.get_width() / 2, img.get_height() / 2))

launch_sound = pygame.mixer.Sound('./assets/launch_jump.mp3')


class Frog():
    """
    The frog controlled by the player.
    """
    def __init__(self, center_x, bottom):
        self.state = 'idle'
        self.images = images
        self.image = self.images[self.state]
        self.base_size = self.image.get_size() # (60, 50)
        self.size = self.base_size
        self.rect = pygame.FRect(center_x - self.size[0] / 2, bottom - self.size[1], *self.size)
        self.jumping = False
        self.velocity = 0
        self.init_pos = self.rect.center
        self.time = 0
        self.angle = 0
        self.power = 0
        self.plat_mov = False
        self.platform = None

        def divide_size(self):
            rect = self.rect.copy()
            self.rect.width /= 2
            self.rect.height /= 2
            self.rect.bottom = rect.bottom
            self.rect.centerx = rect.centerx
            self.images = images_divided
            self.image = self.images[self.state]

        def collide(self, obj):
            # check for collision between a bin
            return self.rect.colliderect(obj.rect)

        def launch(self, power, angle):
            # start a new jump
            launch_sound.play()
            self.launch = True
            self.init_pos = self.rect.center
            self.time = 0
            self.angle = angle
            self.power = power
            self.plat_mov = False
            self.set_state('launch')

        def set_state(self, state):
            # set animation state
            self.state = state
            self.image = self.images[self.state]

        def update(self, dt, platforms, g):
            """
            Update the frog's position and check for collisions.
            """
            if self.jumping:
                # calculate new coordinates during a jump
                self.time += dt / 100
                self.rect.center = move(self.init_pos, self.angle, self.power, self.time, g)

                # check for collisions with platforms
                for platform in platforms:
                    if self.collide(platform):
                        self.rect.bottom = platform.rect.top
                        self.jumping = False
                        self.set_state('idle')
                        platform.touch()
                        # stick to the platform if's is a log
                        if type(platform) is Log:
                            self.plat_mov = True
                            self.platform = platform

            elif self.plat_mov:
                # move accordingly to the log
                self.rect.bottom = self.platform.rect.top
                self.rect.x += self.platform.speed * self.platform.direction

            else:
                # stay on the ground
                self.rect.y += 5
                for platform in platforms:
                    if self.collide(platform):
                        self.rect.bottom = platform.rect.top

        def render(self, surf, scroll):
            surf.blit(self.image, (self.rect.x - scroll, self.rect.y + 3))





