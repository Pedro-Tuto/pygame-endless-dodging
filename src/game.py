import pygame
import sys
from src.constants import (
    LARGURA, ALTURA,
    verde, verde_claro, vermelho, vermelho_claro,
    azul_claro, roxo, largura_passaro
)
from src.assets import load_assets
from src.ui import button, text_objects
from src.entities import Bird, Obstacle


class Game:
    """Gerencia o estado e o loop principal do jogo."""

    def __init__(self):
        pygame.init()
        self.display = pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption('Thrush Rush')
        self.clock = pygame.time.Clock()
        self.pause = False
        self.assets = load_assets()
        pygame.display.set_icon(self.assets['bird_img'])

    # ------------------------------------------------------------------ helpers

    def _draw_text_center(self, text, size=115):
        """Renderiza um texto grande centralizado na tela."""
        font = pygame.font.Font('freesansbold.ttf', size)
        superficie, retangulo = text_objects(text, font)
        retangulo.center = (LARGURA // 2, ALTURA // 2)
        self.display.blit(superficie, retangulo)

    def _draw_score(self, count):
        """Exibe o contador de obstáculos desviados."""
        font = pygame.font.SysFont(None, 100)
        text = font.render('Dibrados: ' + str(count), True, verde)
        self.display.blit(text, (0, 0))

    # ------------------------------------------------------------------ telas

    def game_intro(self):
        """Tela de menu inicial."""
        pygame.mixer.Sound.play(self.assets['title'])
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            self.display.fill(roxo)
            self._draw_text_center("THRUSH RUSH!")

            if button(self.display, "START", 155, 700, 400, 200, verde, verde_claro, 'play') == 'play':
                self.run()
                return

            if button(self.display, "SAIR", 955, 700, 400, 200, vermelho, vermelho_claro, 'quit') == 'quit':
                pygame.quit()
                sys.exit()

            pygame.display.update()
            self.clock.tick(15)

    def crash(self):
        """Tela exibida quando o jogador bate."""
        pygame.mixer.Sound.play(self.assets['crash_sound'])
        self._draw_text_center("VOCÊ BATEU")

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            if button(self.display, "DE NOVO", 155, 700, 400, 200, verde, verde_claro, 'main') == 'main':
                self.run()
                return

            if button(self.display, "SAIR", 955, 700, 400, 200, vermelho, vermelho_claro, 'quit') == 'quit':
                pygame.quit()
                sys.exit()

            pygame.display.update()
            self.clock.tick(15)

    def paused(self):
        """Tela de pausa."""
        while self.pause:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            self._draw_text_center("PAUSADO")

            if button(self.display, "CONTINUAR", 155, 700, 400, 200, verde, verde_claro, 'unpause') == 'unpause':
                self.pause = False

            if button(self.display, "SAIR", 955, 700, 400, 200, vermelho, vermelho_claro, 'quit') == 'quit':
                pygame.quit()
                sys.exit()

            pygame.display.update()
            self.clock.tick(15)

    # ------------------------------------------------------------------ loop principal

    def run(self):
        """Loop principal do jogo."""
        pygame.mixer.Sound.stop(self.assets['title'])
        pygame.mixer.music.play(-1)

        bird     = Bird(x=LARGURA * 0.40, y=ALTURA * 0.70, image=self.assets['bird_img'])
        obstacle = Obstacle()
        dodged   = 0

        while True:
            keys = pygame.key.get_pressed()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                    self.pause = True
                    self.paused()

            if keys[pygame.K_LEFT]:
                bird.move_left()
            elif keys[pygame.K_RIGHT]:
                bird.move_right()

            # Desenho
            self.display.fill(azul_claro)
            obstacle.draw(self.display)
            obstacle.move()
            bird.draw(self.display)
            self._draw_score(dodged)

            # Colisão com bordas
            if bird.x > LARGURA - largura_passaro or bird.x < 0:
                self.crash()
                return

            # Obstáculo saiu da tela: resetar e pontuar
            if obstacle.is_off_screen():
                obstacle.reset()
                dodged += 1
                pygame.mixer.Sound.play(self.assets['swoosh'])
                obstacle.speed += 0.3
                if dodged in range(10, 20):
                    obstacle.width += dodged * 1
                if dodged > 40:
                    obstacle.width = 50

            # Colisão com obstáculo
            if obstacle.collides_with(bird):
                self.crash()
                return

            pygame.display.update()
            self.clock.tick(60)
            print(self.clock.get_fps())