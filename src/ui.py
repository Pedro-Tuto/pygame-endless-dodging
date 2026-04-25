import pygame
import sys
from src.constants import preto


def text_objects(text, font):
    """Cria uma superfície de texto e seu retângulo."""
    textoSuperficie = font.render(text, True, preto)
    return textoSuperficie, textoSuperficie.get_rect()


def button(display, msg, x, y, w, h, ic, ac, action=None):
    """
    Desenha um botão e retorna a action se ele for clicado,
    ou None caso contrário.
    
    Mudança em relação ao original: em vez de chamar funções
    diretamente, retorna a action string para o chamador decidir.
    """
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()

    if x + w > mouse[0] > x and y + h > mouse[1] > y:
        pygame.draw.rect(display, ac, (x, y, w, h))
        if click[0] == 1 and action is not None:
            return action
    else:
        pygame.draw.rect(display, ic, (x, y, w, h))

    textoPequeno = pygame.font.Font("freesansbold.ttf", 50)
    textoSuperficie, textoRetangulo = text_objects(msg, textoPequeno)
    textoRetangulo.center = ((x + (w / 2)), (y + (h / 2)))
    display.blit(textoSuperficie, textoRetangulo)

    return None
