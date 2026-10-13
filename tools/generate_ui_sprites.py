"""Gera icones PNG locais para a interface pixel-art."""
from pathlib import Path
import math
import pygame


OUT = Path(__file__).resolve().parents[1] / "missao_estoque" / "assets" / "ui" / "icons"


def star(filled):
    image = pygame.Surface((64, 64), pygame.SRCALPHA)
    points = []
    for index in range(10):
        angle = -math.pi / 2 + index * math.pi / 5
        length = 28 if index % 2 == 0 else 13
        points.append((round(32 + math.cos(angle) * length), round(32 + math.sin(angle) * length)))
    pygame.draw.polygon(image, (255, 201, 42) if filled else (66, 79, 94), points)
    pygame.draw.polygon(image, (255, 237, 143) if filled else (137, 150, 162), points, 3)
    return image


def lock():
    image = pygame.Surface((64, 64), pygame.SRCALPHA)
    pygame.draw.arc(image, (151, 160, 169), (17, 7, 30, 34), 0, math.pi, 6)
    pygame.draw.rect(image, (116, 127, 138), (10, 29, 44, 27), border_radius=5)
    pygame.draw.rect(image, (183, 191, 197), (10, 29, 44, 27), 3, border_radius=5)
    pygame.draw.circle(image, (39, 48, 57), (32, 41), 4)
    pygame.draw.rect(image, (39, 48, 57), (30, 41, 4, 8), border_radius=2)
    return image


pygame.init()
OUT.mkdir(parents=True, exist_ok=True)
pygame.image.save(star(True), OUT / "star_filled.png")
pygame.image.save(star(False), OUT / "star_empty.png")
pygame.image.save(lock(), OUT / "lock_blocked.png")
pygame.quit()
