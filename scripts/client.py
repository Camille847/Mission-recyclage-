import pygame
import pygame.freetype
import threading
import requests
from pickle import dumps, loads
from re import compile, match
from cryptography.fernet import Fernet

key = b'DfOaFLRVToUyjSRRo0ZqeVAu3Bksp_z9bp-uFpgvfsU='


def writeFile(data, file):
    data = dumps(data)
    cipher = Fernet(key)
    data = cipher.encrypt(data)
    with open(file, 'wb') as file:
        file.write(data)


def readFile(file):
    with open(file, 'rb') as file:
        data = file.read()
    cipher = Fernet(key)
    data = cipher.decrypt(data)
    data = loads(data)
    return data


def blit_center(surface, source, center):
    surface.blit(source, (center[0] - source.get_width() / 2, center[1] - source.get_height() / 2))


class TextInput():
    def __init__(self, pos, callback, placeholder):
        self.font = pygame.freetype.Font('./assets/ComicNeue-Bold.ttf', size=32)
        self.center = pos
        self.callback = callback
        self.placeholder = placeholder
        self.text = ''
        self.focus = False
        self.hovered = False
        self.rect = None
        self.resize()

    def exit(self):
        self.focus = False
        self.callback(self.text)

    def resize(self):
        if self.text:
            surf, text_rect = self.font.render(self.text, 'black' if self.focus else 'yellow')
        else:
            text, text_rect = self.font.render(self.placeholder, 'lightgray')
        width = max(text_rect.width + 30, 220)
        height = max(text_rect.height + 20, 60)
        x = self.center[0] - width / 2
        y = self.center[1] - height / 2
        self.rect = pygame.Rect(x, y, width, height)

    def update(self, events):
        if self.rect.collidepoint(pygame.mouse.get_pos()):
            self.hovered = True
        else:
            self.hovered = False
        if self.focus:
            for e in events:
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_BACKSPACE:
                        if self.text:
                            self.text = self.text[:-1]
                            self.resize()
                    elif e.key == pygame.K_RETURN:
                        self.exit()
                    else:
                        self.text += e.unicode
                        self.resize()

    def render(self, surf):
        if self.text:
            text, trect = self.font.render(self.text, 'black' if self.focus else 'yellow')
        else:
            text, trect = self.font.render(self.placeholder, 'lightgray')
        pygame.draw.rect(surf, 'lightgray' if self.focus else ('darkgray' if not self.hovered else 'gray'), self.rect,
                         border_radius=25)
        blit_center(surf, text, self.center)


class Client():
    def __init__(self, game):
        self.game = game

        # load config

        self.config = readFile('config/config.dat')
        self.url = self.config['URL']
        self.regex = compile(self.config['REGEX'])

        # server connection test
        try:
            response = requests.get(self.url + '/get/' + self.game)

            if not response.ok or 'error' in response.json():
                self.connected = False
            else:
                self.connected = True

        except Exception as error:
            print(error)
            self.connected = False

        # load player data / check if registered

        data = readFile('config/data.dat')
        self.uuid = data['uuid']
        self.username = data['username']
        if self.uuid is None or not self.isValidName(self.username):
            self.username = None
            self.registered = False
        else:
            self.registered = True

    @staticmethod
    def thread(func, args=tuple()):
        thread = threading.Thread(target=func, args=args)
        thread.start()

    def isValidName(self, string):
        return bool(match(self.regex, string))

    def save(self):
        data = {'uuid': self.uuid, 'username': self.username}
        writeFile(data, 'config/data.dat')

    def register(self, username, registered=False):
        if self.connected:
            if self.isValidName(username):
                response = requests.post(
                    url=self.config['URL_ROOT'] + '/register',
                    json={'username': username, 'uuid': self.uuid if registered else None,
                          'key': self.config['ACCESS_KEY']}
                )
                data = response.json()
                if 'error' in data:
                    return data
                else:
                    if not registered:
                        self.uuid = data['uuid']
                        self.registered = True
                    self.username = username
                    self.save()
                    return {}
            else:
                return {'error': 'invalid username'}
        else:
            return {'error': 'not connected to server'}

    def setUsername(self, username):
        if username != self.username:
            return self.register(username, registered=True)
        return {}

    def getMinScore(self):
        if self.connected:
            payload = 'mode=high:' + self.username if self.registered else 'mode=high'
            response = requests.get(self.url + '/get/' + self.game + '?' + payload)
            return int(response.text)
        return -1

    def sendScore(self, score):
        if self.connected and self.registered and type(score) == int:
            data = {'uuid': self.uuid, 'score': score, 'key': self.config['ACCESS_KEY']}
            response = requests.post(self.url + '/edit/' + self.game, json=data)
            data = response.json()
            if 'error' in data:
                return data['error']
        return ''
