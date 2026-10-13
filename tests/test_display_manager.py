import os
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from systems.display_manager import DisplayManager
from systems.progress import Progress


class DisplayManagerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        patcher = patch("systems.progress.user_data_dir", return_value=Path(self.temp.name))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.temp.cleanup)
        self.progress = Progress()

    def test_fullscreen_choice_is_persisted(self):
        display = DisplayManager(self.progress)
        display.set_fullscreen(True)
        self.assertTrue(display.fullscreen)
        self.assertTrue(Progress().fullscreen_enabled)
        display.set_fullscreen(False)

    def test_mouse_coordinates_respect_letterbox_viewport(self):
        display = DisplayManager(self.progress)
        display.window = pygame.Surface((1920, 1200))
        display._update_viewport()
        self.assertEqual(display.viewport, pygame.Rect(0, 60, 1920, 1080))
        self.assertEqual(display.logical_position((960, 600)), (640, 360))


if __name__ == "__main__":
    unittest.main()
