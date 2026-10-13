import json
import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from scenes.level5 import Level5
from systems.progress import Progress


class Level5FlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1280, 720))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.progress = Progress()
        self.progress.data = self.progress._default_data()
        self.progress.path = Path(self.temp_dir.name) / "progress.json"
        self.level = Level5(self.progress)
        self.level.cutscene.finish()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _move_to(self, x):
        self.level.player.rect.centerx = x

    def _complete_validation(self):
        self._move_to(self.level.cart.rect.centerx)
        self.level._interact()
        for _ in self.level.cart_boxes:
            self.level._scan_cart_item()

    def test_correct_order_completes_action_driven_checklist(self):
        self.level.reset(divergence_index=None)
        self.level.cutscene.finish()
        self._complete_validation()
        self.assertTrue(all(self.level.checks[key] for key in ("quantity", "references", "sizes", "scanner")))

        self._move_to(310)
        self.level._interact()
        self._move_to(1580)
        self.level._interact()
        self._move_to(2200)
        self.level._interact()

        self.assertTrue(all(self.level.checks.values()))
        self.assertTrue(self.level.prepared)
        self.assertGreater(self.level.loading_started, 0)

    def test_divergence_blocks_then_can_be_replaced_and_rescanned(self):
        self.level.reset(divergence_index=0)
        self.level.cutscene.finish()
        self._move_to(self.level.cart.rect.centerx)
        self.level._interact()
        self.level._scan_cart_item()
        self.assertTrue(self.level.divergence_detected)
        self.assertFalse(self.level.checks["scanner"])

        self.level.player.rect.center = self.level.correction_box.rect.center
        self.level._interact()
        self.assertIsNotNone(self.level.carried_box)
        self._move_to(self.level.cart.rect.centerx)
        self.level._interact()
        self.assertIsNone(self.level.carried_box)
        for _ in self.level.cart_boxes:
            self.level._scan_cart_item()

        self.assertTrue(self.level.checks["scanner"])
        self.assertTrue(self.level.checks["references"])
        self.assertEqual(self.level.divergences_found, 1)

    def test_early_release_is_blocked_and_counted_as_error(self):
        self.level.reset(divergence_index=None)
        self.level.cutscene.finish()
        self._move_to(2200)
        self.level._interact()
        self.assertFalse(self.level.checks["released"])
        self.assertEqual(self.level.scoring.errors, 1)
        self.assertIn("Organize o carrinho", self.level.message)


class ProgressLevel5Tests(unittest.TestCase):
    def test_old_save_migrates_and_level5_completion_unlocks_final(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "progress.json"
            path.write_text(json.dumps({"tutorial_completed": True, "highest_unlocked_level": 4, "levels": {"4": {"completed": True}}}), encoding="utf-8")
            progress = Progress()
            progress.path = path
            progress.data = progress._default_data()
            progress._load()
            self.assertIn("5", progress.data["levels"])

            result = {"completed": True, "score": 700, "accuracy": 100, "errors": 0, "quiz_correct": 5, "quiz_total": 5}
            progress.record_result(5, result)
            self.assertTrue(progress.level_data(5)["completed"])
            self.assertEqual(progress.data["highest_unlocked_level"], 6)


if __name__ == "__main__":
    unittest.main()
