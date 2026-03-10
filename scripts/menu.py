import pygame
import random

font_path = 'assets/ComicNeue-Bold.ttf'


class Button():
    """
    A clickable button with text.
    """
    def __init__(self, centerx, y, text):
        self.text = text
        self.default_color = 'green'
        self.hover_color = 'forestgreen'
        self.click_color = 'darkgreen'
        self.text_color = 'white'
        self.color = self.default_color

        self.is_hovered = False
        self.is_clicked = False

        self.font = pygame.font.Font(font_path, 35)
        self.rendered_text = self.font.render(self.text, True, self.text_color)
        self.size = 180
        self.rect = pygame.Rect(centerx - self.size / 2, y, self.size, 41)
        self.text_rect = self.rendered_text.get_rect(center=self.rect.center)

    def update(self, mouse_pos, click):
        # check if the mouse hovers the button
        self.is_hovered = self.rect.collidepoint(mouse_pos)

        self.color = self.default_color

        if self.is_hovered:
            self.color = self.hover_color

        # check if the button is clicked
        if self.is_hovered and click:
            self.color = self.click_color
            self.is_clicked = True
        else:
            self.is_clicked = False

        # return True if the button has been clicked
        return self.is_clicked

    def render(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=12)
        surface.blit(self.rendered_text, self.text_rect)


class Menu():
    """
    The game menu class. Handle the main menu and game over screen.
    """
    def __init__(self, game):
        self.game = game

        # big game title
        title_font = pygame.font.Font(font_path, 100)
        title_font.bold = True
        self.title_surf = title_font.render('La Rainette', True, 'yellow')
        self.title_rect = self.title_surf.get_rect(center=(game.width / 2, 100))

        game_over_font = pygame.font.Font(font_path, 80)
        self.game_over_surf = game_over_font.render('Game Over', True, 'red')
        self.game_over_rect = self.game_over_surf.get_rect(center=(game.width / 2, 100))

        x = game.width // 2
        y = game.height // 2
        self.play_button  = Button(x, y + 25, "Jouer")
        self.retry_button = Button(x, y - 30, "Rejouer")
        self.menu_button  = Button(x, y + 25, "Menu")
        self.quit_button  = Button(x, y + 80, "Quitter")

        self.death_font = pygame.font.Font(font_path, 36)
        self.death_msg = ""
        self.death_messages = [
            "Tu as coulé !",
            "Tu es mort !",
            "CROA CROAA !",
            "GLOU GLOU GLOU !",
            "Un amateur à l'eau !"
        ]
        self.death_surf = None
        self.death_rect = None

    def new_message(self):
        # randomly pick a death message
        self.death_msg = random.choice(self.death_messages)
        self.death_surf = self.death_font.render(self.death_msg, True, 'Black')
        self.death_rect = self.death_surf.get_rect(center=(self.game.width / 2, self.game.height - 75))

    def update_main(self):
        # update the main menu
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
        surf.blit(self.title_surf, self.title_rect)
        self.play_button.render(surf)
        self.quit_button.render(surf)

    def render_game_over(self, surf):
        surf.blit(self.game_over_surf, self.game_over_rect)
        surf.blit(self.death_surf, self.death_rect)
        self.retry_button.render(surf)
        self.menu_button.render(surf)
        self.quit_button.render(surf)
