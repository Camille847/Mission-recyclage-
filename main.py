import pygame
import sys
import random
from scripts.waste import Waste
from scripts.bin import Bin
from scripts.utils import get_angle

# Initialisation
pygame.init()
WIDTH, HEIGHT = 1200, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
FPS = 60
GRAVITY = 0.5

# Types de déchets disponibles
WASTE_TYPES = ['banane', 'bouteille', 'canette', 'papier']

# Création des 4 poubelles
bins = [
    Bin(250, 550, 'bleue'),
    Bin(450, 550, 'jaune'),
    Bin(650, 550, 'marron'),
    Bin(850, 550, 'verte')
]

# État du jeu
current_waste = Waste(150, 450, random.choice(WASTE_TYPES))
charging = False
charging_time = 0
power = 0
POWER_MIN, POWER_MAX = 5, 25
score = 0
font = pygame.font.Font(None, 36)

# Charger un décor de fond
background = pygame.image.load('assets/decors/matin.png')
background = pygame.transform.scale(background, (WIDTH, HEIGHT))

running = True
while running:
    dt = clock.tick(FPS)
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN and not current_waste.launched:
            charging = True
            charging_time = 0

        if event.type == pygame.MOUSEBUTTONUP and charging and not current_waste.launched:
            charging = False
            power = POWER_MIN + (POWER_MAX - POWER_MIN) * min(charging_time / 1000, 1)
            angle = get_angle(mouse_pos, current_waste.rect.center)
            current_waste.launch(power, angle)

    # Chargement de la puissance
    if charging and not current_waste.launched:
        charging_time += dt
        power_ratio = min(charging_time / 1000, 1)
        power = POWER_MIN + (POWER_MAX - POWER_MIN) * power_ratio

    # Mise à jour du déchet
    current_waste.update(dt, GRAVITY)

    # Vérifier les collisions
    if current_waste.launched:
        # Si le déchet sort de l'écran
        if current_waste.rect.y > HEIGHT or current_waste.rect.x > WIDTH + 200:
            current_waste = Waste(150, 450, random.choice(WASTE_TYPES))

        # Collision avec une poubelle
        for bin in bins:
            if current_waste.rect.colliderect(bin.rect):
                if current_waste.correct_bin[current_waste.type] == bin.type:
                    score += 10
                    print(f"✓ Bon tri ! +10 pts (total: {score})")
                else:
                    score -= 5
                    print(f"✗ Mauvais tri ! -5 pts (total: {score})")

                current_waste = Waste(150, 450, random.choice(WASTE_TYPES))
                break

    # Dessin
    screen.blit(background, (0, 0))

    # Dessiner les poubelles
    for bin in bins:
        bin.render(screen)

    # Dessiner le déchet
    current_waste.render(screen)

    # Jauge de puissance
    if charging:
        pygame.draw.rect(screen, (255, 0, 0), (50, 50, 200 * (power / POWER_MAX), 20))

    # Score
    score_surface = font.render(f"Score: {score}", True, (0, 0, 0))
    screen.blit(score_surface, (10, 10))

    pygame.display.flip()

pygame.quit()
sys.exit()