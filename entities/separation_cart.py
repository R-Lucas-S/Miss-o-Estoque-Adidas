from pathlib import Path

import pygame

from missao_estoque.settings import CART_VISUAL_HEIGHT, CART_VISUAL_WIDTH
from systems.ui_theme import get_font


class SeparationCart:
    """Carrinho visual da separação; o pedido continua sendo a fonte dos dados."""

    _image = None

    def __init__(self, x, floor_top):
        self.rect = pygame.Rect(x, floor_top - CART_VISUAL_HEIGHT, CART_VISUAL_WIDTH, CART_VISUAL_HEIGHT)
        self.floor_top = floor_top
        self.font = get_font(16, "ui", bold=True)
        self.image = self._load_image(self.rect.size)

    @classmethod
    def _load_image(cls, size):
        if cls._image is None:
            path = Path(__file__).resolve().parents[1] / "missao_estoque" / "assets" / "environment" / "carts" / "picking_cart_a104.png"
            source = pygame.image.load(str(path)).convert_alpha()
            cls._image = pygame.transform.scale(source, size)
        return cls._image

    def accepts(self, player_rect):
        return self.rect.inflate(38, 35).colliderect(player_rect)

    def slot_position(self, index):
        return self.rect.left + 55 + index * 43, self.floor_top - 25

    def draw(self, surface, camera, filled_count, active=False, completed=False, offset_x=0):
        rect = camera.apply_rect(self.rect.move(offset_x, 0))
        frame = (255, 220, 90) if active else (95, 169, 190)
        if completed:
            frame = (80, 210, 140)
        surface.blit(self.image, rect)
        if active or completed:
            glow = pygame.Surface(rect.inflate(-18, -40).size, pygame.SRCALPHA)
            pygame.draw.rect(glow, (*frame, 46), glow.get_rect(), 2, border_radius=4)
            surface.blit(glow, glow.get_rect(center=(rect.centerx + 18, rect.centery + 9)))
