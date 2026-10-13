"""Tokens visuais compartilhados pela interface do jogo."""

from functools import lru_cache
from pathlib import Path

import pygame


FONT_PATH = (
    Path(__file__).resolve().parents[1]
    / "missao_estoque"
    / "assets"
    / "fonts"
    / "PixelifySans.ttf"
)

# Pesos inspirados na referência: titulos blocados, HUD firme e diálogos leves.
ROLE_WEIGHTS = {
    "display": 700,
    "title": 700,
    "ui": 600,
    "body": 400,
    "mono": 500,
}

READABLE_FAMILIES = ("bahnschrift", "segoeui", "arial")


@lru_cache(maxsize=64)
def get_font(size, role="body", bold=False):
    """Combina display pixel-art com corpo legivel e fallback seguro."""
    if role == "body":
        path = None
        for family in READABLE_FAMILIES:
            path = pygame.font.match_font(family, bold=bold)
            if path:
                break
    else:
        path = str(FONT_PATH) if FONT_PATH.is_file() else None
    font = pygame.font.Font(path, size)
    weight = 700 if bold else ROLE_WEIGHTS.get(role, 400)
    font.set_bold(weight >= 700)
    return font
