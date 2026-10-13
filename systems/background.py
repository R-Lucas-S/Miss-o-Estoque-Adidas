"""Funcoes de composicao para cenarios estaticos em pixel art."""

import pygame

from missao_estoque.settings import GAMEPLAY_GROUND_Y, GAME_VIEW_HEIGHT


_cover_cache = {}


def load_world_background(path, world_width, viewport_height, source_ground_y=500):
    """Recorta para o viewport de jogo sem ampliar a escala vertical da arte."""
    key = ("world", str(path), world_width, viewport_height, source_ground_y)
    if key not in _cover_cache:
        source = pygame.image.load(str(path)).convert()
        scaled = pygame.transform.scale(source, (world_width, viewport_height))
        crop_y = max(0, min(viewport_height - GAME_VIEW_HEIGHT, source_ground_y - GAMEPLAY_GROUND_Y))
        _cover_cache[key] = scaled.subsurface((0, crop_y, world_width, GAME_VIEW_HEIGHT)).copy()
    return _cover_cache[key]


def load_framed_background(path, viewport_width, viewport_height, source_ground_y=500):
    """Recorta horizontalmente e verticalmente sem zoom no eixo vertical."""
    key = ("framed", str(path), viewport_width, viewport_height, source_ground_y)
    if key in _cover_cache:
        return _cover_cache[key]
    source = pygame.image.load(str(path)).convert()
    scale = viewport_height / source.get_height()
    fitted_width = round(source.get_width() * scale)
    scaled = pygame.transform.scale(source, (fitted_width, viewport_height))
    crop_x = max(0, (scaled.get_width() - viewport_width) // 2)
    crop_y = max(0, min(viewport_height - GAME_VIEW_HEIGHT, source_ground_y - GAMEPLAY_GROUND_Y))
    result = scaled.subsurface((crop_x, crop_y, viewport_width, GAME_VIEW_HEIGHT)).copy()
    _cover_cache[key] = result
    return result


def load_cover_background(path, world_width, viewport_height):
    """Carrega sem deformar: escala proporcionalmente e recorta o excedente.

    O mapa pode ser mais largo que a tela; por isso o resultado final tem a
    largura do mundo e continua acompanhando a camera horizontal.
    """
    key = (str(path), world_width, viewport_height)
    if key in _cover_cache:
        return _cover_cache[key]

    source = pygame.image.load(str(path)).convert()
    scale = max(world_width / source.get_width(), viewport_height / source.get_height())
    scaled_size = (round(source.get_width() * scale), round(source.get_height() * scale))
    scaled = pygame.transform.scale(source, scaled_size)
    crop_x = max(0, (scaled.get_width() - world_width) // 2)
    crop_y = max(0, (scaled.get_height() - viewport_height) // 2)
    result = scaled.subsurface(pygame.Rect(crop_x, crop_y, world_width, viewport_height)).copy()
    _cover_cache[key] = result
    return result
