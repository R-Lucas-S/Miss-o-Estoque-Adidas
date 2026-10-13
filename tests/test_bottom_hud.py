import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from missao_estoque.settings import BOTTOM_HUD_HEIGHT, GAMEPLAY_GROUND_Y, GAME_VIEW_HEIGHT, SCREEN_HEIGHT, SCREEN_WIDTH
from systems.bottom_hud import BottomHUD


class BottomHUDTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_gameplay_ground_leaves_margin_before_hud(self):
        self.assertEqual(GAME_VIEW_HEIGHT, SCREEN_HEIGHT - BOTTOM_HUD_HEIGHT)
        self.assertEqual(GAME_VIEW_HEIGHT - GAMEPLAY_GROUND_Y, 70)

    def test_hud_renders_and_accepts_metric_updates(self):
        surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        hud = BottomHUD()
        hud.started_at -= hud.ENTER_MS
        base = (
            {"key": "score", "label": "PONTOS", "value": 0, "display": "0"},
            {"key": "combo", "label": "COMBO", "value": 0, "display": "x0"},
        )
        hud.draw(surface, "MISSAO 1  -  RECEBIMENTO", ("CAIXAS", "0 / 3", (80, 210, 140), 0), base)
        changed = (
            {"key": "score", "label": "PONTOS", "value": 100, "display": "100"},
            {"key": "combo", "label": "COMBO", "value": 1, "display": "x1"},
        )
        hud.draw(surface, "MISSAO 1  -  RECEBIMENTO", ("CAIXAS", "1 / 3", (80, 210, 140), 1 / 3), changed, ("ITEM CORRETO", (80, 230, 145)))
        # Forca o meio do pulso, quando a escala fica diferente de 1.0.
        pulse_now = pygame.time.get_ticks()
        hud.pulses["score"] = pulse_now - hud.PULSE_MS // 2
        hud.pulses["combo"] = pulse_now - hud.PULSE_MS // 2
        hud.draw(surface, "MISSAO 1  -  RECEBIMENTO", ("CAIXAS", "1 / 3", (80, 210, 140), 1 / 3), changed)
        self.assertEqual(hud.point_delta, 100)
        self.assertGreater(surface.get_at((SCREEN_WIDTH // 2, GAME_VIEW_HEIGHT + 20)).a, 0)


if __name__ == "__main__":
    unittest.main()
