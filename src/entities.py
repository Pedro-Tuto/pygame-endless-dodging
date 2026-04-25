import pygame
import random
from src.constants import largura_passaro, branco, LARGURA, ALTURA


class Bird:
    """Representa o pássaro controlado pelo jogador."""

    def __init__(self, x, y, image):
        self.x = x
        self.y = y
        self.image = image

    def draw(self, surface):
        surface.blit(self.image, (self.x, self.y))

    def move_left(self):
        self.x -= 30

    def move_right(self):
        self.x += 30


class Obstacle:
    """Representa um obstáculo que cai do topo da tela."""

    def __init__(self):
        self.width  = 200
        self.height = 100
        self.speed  = 7
        self.color  = branco
        self.x = random.randrange(0, LARGURA)
        self.y = -600

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, [self.x, self.y, self.width, self.height])

    def move(self):
        self.y += self.speed

    def is_off_screen(self):
        return self.y > ALTURA

    def reset(self):
        self.y = 0 - self.height
        self.x = random.randrange(0, LARGURA)

    def collides_with(self, bird):
        """Retorna True se o obstáculo colidiu com o pássaro."""
        if bird.y < self.y + self.height:
            if bird.x + largura_passaro > self.x and bird.x < self.x + self.width:
                return True
        return False
