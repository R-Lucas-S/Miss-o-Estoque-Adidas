from pathlib import Path

import pygame


_images = {}


def _image(name, size):
    key = (name, size)
    if key not in _images:
        path = Path(__file__).resolve().parents[1] / "missao_estoque" / "assets" / "ui" / "icons" / name
        source = pygame.image.load(str(path)).convert_alpha()
        _images[key] = pygame.transform.scale(source, size)
    return _images[key]


def draw_star(surface, center, radius, filled):
    image = _image("star_filled.png" if filled else "star_empty.png", (radius * 2, radius * 2))
    surface.blit(image, image.get_rect(center=center))


def draw_lock(surface, rect, locked=True):
    if locked:
        image = _image("lock_blocked.png", rect.size)
        surface.blit(image, rect)
    else:
        pygame.draw.rect(surface, (80, 220, 145), rect, border_radius=3)


def draw_check(surface, center, size=12, color=(80, 230, 145)):
    x, y = center
    pygame.draw.lines(surface, color, False, ((x - size, y), (x - size // 3, y + size // 2), (x + size, y - size // 2)), 4)
