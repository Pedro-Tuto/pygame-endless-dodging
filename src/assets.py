import pygame


def load_assets():
    """Carrega e retorna todos os assets do jogo (imagens e sons)."""
    assets = {}

    # Imagens
    assets['bird_img'] = pygame.image.load(r"src\images\bird.png")

    # Sons
    assets['crash_sound'] = pygame.mixer.Sound(r"src\sounds\crash1.mp3")
    assets['swoosh']      = pygame.mixer.Sound(r"src\sounds\Swoosh.mp3")
    assets['title']       = pygame.mixer.Sound(r"src\sounds\sandman.mp3")

    # Música de fundo (carregada no mixer separado)
    pygame.mixer.music.load(r"src\sounds\toto.mp3")

    return assets
