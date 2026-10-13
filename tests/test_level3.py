import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from missao_estoque.settings import LEVEL3_FLOOR_TOP, SCREEN_HEIGHT, SCREEN_WIDTH
from scenes.level3 import Level3


class PreviewProgress:
    def record_result(self, level, result):
        return result


class Level3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.level = Level3(PreviewProgress())
        self.level.cutscene.active = False

    def _stand_near(self, target):
        self.level.player.rect.centerx = target.rect.centerx
        self.level.player.rect.bottom = self.level.floor.top

    def test_all_characters_share_ground_anchor(self):
        self.assertEqual(self.level.floor.top, LEVEL3_FLOOR_TOP)
        self.level.player.rect.bottom = self.level.floor.top
        self.assertEqual(self.level.player.rect.bottom, LEVEL3_FLOOR_TOP)
        for npc in self.level.npcs:
            self.assertEqual(npc.rect.bottom, LEVEL3_FLOOR_TOP)
            self.assertLessEqual(max(npc.feet_offsets), 2)

    def test_repeated_divergence_check_cannot_farm_score_combo_or_accuracy(self):
        box = next(box for box in self.level.boxes if box.is_divergence)
        self._stand_near(box)
        self.level.interact()
        first = (self.level.scoring.score, self.level.scoring.combo, self.level.accuracy, self.level.confirmed_divergences)
        for _ in range(10):
            self.level.interact()
        self.assertEqual(first, (50, 0, 100, 1))
        self.assertEqual((self.level.scoring.score, self.level.scoring.combo, self.level.accuracy, self.level.confirmed_divergences), first)
        self.assertTrue(box.discovery_score_awarded)

    def test_each_box_has_independent_check_state_and_reset_clears_it(self):
        first, second = [box for box in self.level.boxes if box.is_divergence][:2]
        self._stand_near(first)
        self.level.interact()
        self.assertEqual(first.check_state, "checked_divergent")
        self.assertEqual(second.check_state, "unchecked")
        self.level.reset()
        self.assertTrue(all(box.check_state == "unchecked" for box in self.level.boxes))
        self.assertTrue(all(not box.discovery_score_awarded for box in self.level.boxes))

    def test_correction_reward_is_unique(self):
        box = next(box for box in self.level.boxes if box.is_divergence)
        self._stand_near(box)
        self.level.interact()
        self.level.interact()
        destination = next(storage for storage in self.level.storages if storage.destination == box.destination)
        self._stand_near(destination)
        self.level.interact()
        score_after_correction = self.level.scoring.score
        combo_after_correction = self.level.scoring.combo
        self.level.carried_box = box
        self.level.interact()
        self.assertEqual(self.level.scoring.score, score_after_correction)
        self.assertEqual(self.level.scoring.combo, combo_after_correction)
        self.assertEqual(box.check_state, "corrected")
        self.assertTrue(box.correction_score_awarded)


if __name__ == "__main__":
    unittest.main()
