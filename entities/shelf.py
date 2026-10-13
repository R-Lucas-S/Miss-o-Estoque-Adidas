from pathlib import Path

import pygame

from missao_estoque.settings import SHELF_VISUAL_HEIGHT


class Shelf:
    """Prateleira reutilizavel: visual e área solida ficam separados."""

    _image = None

    def __init__(self, x, floor_top, width=170, height=SHELF_VISUAL_HEIGHT, solid=False):
        self.rect = pygame.Rect(x, floor_top - height, width, height)
        self.solid_rect = pygame.Rect(x, floor_top - 60, width, 60) if solid else None
        self.image = pygame.transform.scale(self._load_image(), (width, height))

    @classmethod
    def _load_image(cls):
        if cls._image is None:
            path = Path(__file__).resolve().parents[1] / "missao_estoque" / "assets" / "environment" / "shelves" / "shelf_dark_transparent_v2.png"
            cls._image = pygame.image.load(str(path)).convert_alpha()
        return cls._image

    def draw(self, surface, camera):
        surface.blit(self.image, camera.apply_rect(self.rect))
