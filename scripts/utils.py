import pygame
from math import cos, sin, atan2

def lerp(color1, color2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(color1, color2))

def clamp(value, min_value, max_value):
    return min(max(value, min_value), max_value)

def load_image(name, size=None, scale=1):
    img = pygame.image.load('assets/' + name)
    if size is None:
        size = img.get_size()
    if scale != 1:
        size = (size[0] * scale, size[1] * scale)
    img = pygame.transform.scale(img, size)
    return img

def get_angle(pos1, pos2):
    dx = pos1[0] - pos2[0]
    dy = pos1[1] - pos2[1]
    angle = atan2(-dy, dx)
    return angle

def move(ipos, angle, power, t, g):
    x = ipos[0] + cos(angle) * power * t
    y = ipos[1] - sin(angle) * power * t + g / 2 * t ** 2
    return x, y

def smooth(val, target, dt, slowness=1):
    val += (target - val) / slowness * min(dt / 1000, slowness)
    return val

def play(music, volume=1.):
    pygame.mixer.music.stop()
    pygame.mixer.music.load(music)
    pygame.mixer.music.set_volume(volume)
    pygame.mixer.music.play(-1)
