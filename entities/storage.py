from pathlib import Path

import pygame

from missao_estoque.settings import STORAGE_VISUAL_HEIGHT
from systems.ui_theme import get_font


class Storage:
    """Área onde as caixas devem ser organizadas."""

    COLOR = (58, 121, 184)
    _shelf_image = None

    def __init__(self, x, floor_top, label=None, color=None, destination=None, reference=None, size=None):
        self.rect = pygame.Rect(x, floor_top - STORAGE_VISUAL_HEIGHT, 165, STORAGE_VISUAL_HEIGHT)
        self.label = label
        self.destination = destination
        self.reference = reference
        self.size = size
        self.color = color or self.COLOR
        self.stored_boxes = []
        self.image = pygame.transform.scale(self._load_shelf_image(), self.rect.size)
        self.label_font = get_font(20, "ui", bold=True)

    @classmethod
    def _load_shelf_image(cls):
        if cls._shelf_image is None:
            path = Path(__file__).resolve().parents[1] / "missao_estoque" / "assets" / "environment" / "shelves" / "shelf_dark_transparent_v2.png"
            cls._shelf_image = pygame.image.load(str(path)).convert_alpha()
        return cls._shelf_image

    def accepts(self, player_rect):
        return self.rect.colliderect(player_rect.inflate(30, 0))

    def accepts_box(self, box):
        category_ok = self.destination is None or self.destination == box.destination
        reference_ok = self.reference is None or self.reference == box.product["reference"]
        size_ok = self.size is None or self.size == box.product["size"]
        return category_ok and reference_ok and size_ok

    def store(self, box):
        box.set_status(box.DELIVERED)
        column = len(self.stored_boxes) % 3
        row = len(self.stored_boxes) // 3
        box.rect.bottomleft = (self.rect.left + 8 + column * 48, self.rect.bottom - 10 - row * 48)
        self.stored_boxes.append(box)

    def draw(self, surface, camera, highlight=False):
        visual_rect = self.image.get_rect(midbottom=camera.apply_rect(self.rect).midbottom)
        surface.blit(self.image, visual_rect)
        if self.label:
            label = self.label_font.render(self.label, True, (242, 245, 246))
            draw_rect = camera.apply_rect(self.rect)
            plate = pygame.Rect(draw_rect.centerx - 62, draw_rect.top - 30, 124, 26)
            pygame.draw.rect(surface, (17, 27, 36), plate, border_radius=3)
            pygame.draw.rect(surface, self.color, plate, 2, border_radius=3)
            pygame.draw.line(surface, tuple(min(255, value + 35) for value in self.color), (plate.left + 6, plate.top + 4), (plate.right - 6, plate.top + 4), 1)
            surface.blit(label, label.get_rect(center=plate.center))
        if highlight:
            pygame.draw.rect(surface, (255, 220, 90), camera.apply_rect(self.rect), 3, border_radius=4)
