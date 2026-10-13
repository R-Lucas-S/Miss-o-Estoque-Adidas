from pathlib import Path

import pygame


class DecorativeProp:
    """Prop visual em camada de fundo: sem fisica, colisão ou interação."""

    REGIONS = {
        "forklift": pygame.Rect(45, 35, 790, 510),
        "pallet": pygame.Rect(900, 165, 590, 390),
        "desk": pygame.Rect(100, 575, 790, 420),
        "plant": pygame.Rect(990, 555, 420, 445),
    }
    _sheet = None
    _images = {}

    def __init__(self, kind, x, floor_top, scale=0.18, layer="back"):
        self.kind = kind
        self.x = x
        self.floor_top = floor_top
        self.layer = layer
        self.image = self._load_image(kind, scale)

    @classmethod
    def _load_image(cls, kind, scale):
        key = (kind, scale)
        if key not in cls._images:
            if cls._sheet is None:
                path = Path(__file__).resolve().parents[1] / "missao_estoque" / "assets" / "environment" / "props" / "warehouse_props.png"
                cls._sheet = pygame.image.load(str(path)).convert_alpha()
            sprite = cls._sheet.subsurface(cls.REGIONS[kind]).copy()
            size = (round(sprite.get_width() * scale), round(sprite.get_height() * scale))
            cls._images[key] = pygame.transform.scale(sprite, size)
        return cls._images[key]

    def draw(self, surface, camera):
        rect = self.image.get_rect(bottomleft=(camera.apply_x(self.x), self.floor_top))
        surface.blit(self.image, rect)
