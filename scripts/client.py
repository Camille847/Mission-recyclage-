import pygame
import pygame.freetype
import threading

try:
    import requests
    from pickle import dumps, loads
    from re import compile, match
    from cryptography.fernet import Fernet
    _DEPS_OK = True
except ImportError:
    _DEPS_OK = False


def blit_center(surface, source, center):
    surface.blit(source, (
        center[0] - source.get_width()  / 2,
        center[1] - source.get_height() / 2,
    ))


class TextInput:
    def __init__(self, pos, callback, placeholder):
        try:
            self.font = pygame.freetype.Font('assets/ComicNeue-Bold.ttf', size=32)
        except:
            self.font = pygame.freetype.SysFont('arial', size=32)
        self.center      = pos
        self.callback    = callback
        self.placeholder = placeholder
        self.text        = ''
        self.focus       = False
        self.hovered     = False
        self.rect        = None
        self.resize()

    def exit(self):
        self.focus = False
        self.callback(self.text)

    def resize(self):
        if self.text:
            _, text_rect = self.font.render(self.text, 'black')
        else:
            _, text_rect = self.font.render(self.placeholder, 'lightgray')
        width  = max(text_rect.width  + 30, 220)
        height = max(text_rect.height + 20,  60)
        self.rect = pygame.Rect(
            self.center[0] - width  / 2,
            self.center[1] - height / 2,
            width, height,
        )

    def update(self, events):
        self.hovered = self.rect.collidepoint(pygame.mouse.get_pos())
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
            text, _ = self.font.render(
                self.text,
                'black' if self.focus else 'yellow'
            )
        else:
            text, _ = self.font.render(self.placeholder, 'lightgray')

        bg_color = 'lightgray' if self.focus else ('gray' if self.hovered else 'darkgray')
        pygame.draw.rect(surf, bg_color, self.rect, border_radius=25)
        blit_center(surf, text, self.center)


class Client:
    def __init__(self, game: str):
        self.game       = game
        self.connected  = False
        self.registered = False
        self.username   = None
        self.uuid       = None
        self.url        = ''
        self.regex      = None
        self.config     = {}

        # Si les dépendances ou les fichiers de config manquent, on joue hors-ligne
        if not _DEPS_OK:
            print('[Client] Dépendances manquantes, mode hors-ligne.')
            return

        try:
            from pickle import loads
            from re import compile
            from cryptography.fernet import Fernet

            key = b'DfOaFLRVToUyjSRRo0ZqeVAu3Bksp_z9bp-uFpgvfsU='

            def readFile(file):
                with open(file, 'rb') as f:
                    data = f.read()
                cipher = Fernet(key)
                data = cipher.decrypt(data)
                return loads(data)

            self.config = readFile('config/config.dat')
            self.url    = self.config['URL']
            self.regex  = compile(self.config['REGEX'])

            try:
                import requests
                response = requests.get(self.url + '/get/' + self.game, timeout=3)
                self.connected = response.ok and 'error' not in response.json()
            except Exception as e:
                print(f'[Client] Serveur inaccessible : {e}')
                self.connected = False

            data          = readFile('config/data.dat')
            self.uuid     = data['uuid']
            self.username = data['username']

            if self.uuid is not None and self.username:
                self.registered = True

        except Exception as e:
            print(f'[Client] Config introuvable, mode hors-ligne : {e}')

    @staticmethod
    def thread(func, args=()):
        t = threading.Thread(target=func, args=args, daemon=True)
        t.start()

    def isValidName(self, string):
        if string is None or self.regex is None:
            return False
        from re import match
        return bool(match(self.regex, string))

    def save(self):
        if not _DEPS_OK:
            return
        try:
            from pickle import dumps
            from cryptography.fernet import Fernet
            import os
            os.makedirs('config', exist_ok=True)
            key = b'DfOaFLRVToUyjSRRo0ZqeVAu3Bksp_z9bp-uFpgvfsU='
            cipher = Fernet(key)
            data = cipher.encrypt(dumps({'uuid': self.uuid, 'username': self.username}))
            with open('config/data.dat', 'wb') as f:
                f.write(data)
        except Exception as e:
            print(f'[Client] Impossible de sauvegarder : {e}')

    def register(self, username, registered=False):
        if not self.connected:
            return {'error': 'not connected to server'}
        if not self.isValidName(username):
            return {'error': 'invalid username'}
        try:
            import requests
            response = requests.post(
                url=self.config['URL_ROOT'] + '/register',
                json={'username': username, 'uuid': self.uuid if registered else None,
                      'key': self.config['ACCESS_KEY']},
            )
            data = response.json()
            if 'error' in data:
                return data
            if not registered:
                self.uuid       = data['uuid']
                self.registered = True
            self.username = username
            self.save()
            return {}
        except Exception as e:
            return {'error': str(e)}

    def setUsername(self, username):
        if username == self.username:
            return {}
        return self.register(username, registered=True)

    def getMinScore(self):
        if not self.connected:
            return -1
        try:
            import requests
            payload  = 'mode=high:' + self.username if self.registered else 'mode=high'
            response = requests.get(self.url + '/get/' + self.game + '?' + payload)
            return int(response.text)
        except:
            return -1

    def sendScore(self, score: int):
        if self.connected and self.registered and isinstance(score, int):
            try:
                import requests
                data     = {'uuid': self.uuid, 'score': score, 'key': self.config['ACCESS_KEY']}
                response = requests.post(self.url + '/edit/' + self.game, json=data)
                result   = response.json()
                if 'error' in result:
                    return result['error']
            except Exception as e:
                return str(e)
        return ''