from pathlib import Path

import pygame

from missao_estoque.settings import BOX_VISUAL_HEIGHT, BOX_VISUAL_WIDTH
from systems.ui_theme import get_font


class Box:
    """Caixa que pode ser carregada pelo jogador e guardada no estoque."""

    COLOR = (195, 126, 65)
    WIDTH = BOX_VISUAL_WIDTH
    HEIGHT = BOX_VISUAL_HEIGHT
    GROUND = "ground"
    CARRIED = "carried"
    DELIVERED = "delivered"

    _images = {}

    PRODUCT_DATA = {
        "tennis": {"name": "TÊNIS", "reference": "TN-001", "size": "40", "destination": "tennis"},
        "clothing": {"name": "ROUPAS", "reference": "RP-014", "size": "M", "destination": "clothing"},
        "accessories": {"name": "ACESSÓRIOS", "reference": "AC-008", "size": "-", "destination": "accessories"},
    }

    def __init__(self, x, floor_top, box_type="clothing", category=None, product_data=None):
        # A ancora da hitbox e a base do piso; assim a base visual do PNG
        # (cujo alpha já termina na ultima linha) toca o chao em todas as fases.
        self.rect = pygame.Rect(x, 0, self.WIDTH + 16, self.HEIGHT + 4)
        self.rect.bottom = floor_top
        self.box_type = box_type
        self.category = category
        self.product = dict(self.PRODUCT_DATA.get(box_type, {"name": category or box_type.upper(), "reference": "-", "size": "-", "destination": category}))
        if product_data:
            self.product.update(product_data)
        self.destination = category or self.product["destination"]
        self.mistakes = 0
        self.score_value = 100
        self.status = self.GROUND
        self.carried = False
        self.stored = False
        self.image = self._load_image(box_type, self.rect.size)
        self.label_font = get_font(11, "mono", bold=True)
        self.detail_font = get_font(9, "mono")

    @classmethod
    def _load_image(cls, box_type, size):
        cache_key = (box_type, size)
        if cache_key not in cls._images:
            path = Path(__file__).resolve().parents[1] / "missao_estoque" / "assets" / "boxes" / box_type / f"{box_type}.png"
            image = pygame.image.load(str(path)).convert_alpha()
            cls._images[cache_key] = pygame.transform.scale(image, size)
        return cls._images[cache_key]

    def is_near(self, player_rect):
        return self.rect.colliderect(player_rect.inflate(45, 25))

    def set_status(self, status):
        self.status = status
        self.carried = status == self.CARRIED
        self.stored = status == self.DELIVERED

    def follow_player(self, player):
        """Usa a ancora de maos do Player quando estiver disponível."""
        if hasattr(player, "carry_anchor"):
            self.rect.midbottom = player.carry_anchor()
        else:
            self.rect.midbottom = (player.centerx, player.top + 12)

    def draw(self, surface, camera, highlight=False):
        draw_rect = camera.apply_rect(self.rect)
        if highlight:
            glow = pygame.Surface(draw_rect.inflate(10, 10).size, pygame.SRCALPHA)
            pygame.draw.rect(glow, (255, 218, 110, 38), glow.get_rect(), 2, border_radius=5)
            surface.blit(glow, glow.get_rect(center=draw_rect.center))
        surface.blit(self.image, draw_rect)
        reference = self.label_font.render(self.product["reference"], True, (25, 25, 25))
        size = self.detail_font.render(self.product["size"], True, (25, 25, 25))
        surface.blit(reference, reference.get_rect(center=(draw_rect.centerx, draw_rect.centery - 6)))
        surface.blit(size, size.get_rect(center=(draw_rect.centerx, draw_rect.centery + 7)))
