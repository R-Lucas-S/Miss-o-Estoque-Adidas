import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data.questions import QUESTION_BANK, QUESTIONS_BY_LEVEL
from scenes.quiz import Quiz
from scenes.tutorial import Tutorial
from systems.mission_guidance import draw_mission_guidance


class PreviewProgress:
    selected_character = "player_default"
    hints_enabled = True
    tutorial_completed = False

    def complete_tutorial(self):
        self.tutorial_completed = True


class TutorialQuizGuidanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1280, 720))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_question_bank_has_30_unique_complete_questions(self):
        self.assertEqual(len(QUESTION_BANK), 30)
        self.assertEqual(len({question["id"] for question in QUESTION_BANK}), 30)
        for question in QUESTION_BANK:
            self.assertEqual(len(question["options"]), 4)
            self.assertIn(question["correct"], question["options"])
            self.assertTrue(question["tags"])
            self.assertTrue(question["explanation"])

    def test_quiz_shuffle_keeps_correct_answer_and_avoids_session_duplicates(self):
        Quiz.recent_ids.clear()
        quiz = Quiz("level5", question_count=5, completion_scene=None)
        ids = [question["id"] for question in quiz.questions]
        self.assertEqual(len(ids), len(set(ids)))
        for question in quiz.questions:
            self.assertEqual(question["options"][question["answer"]], question["correct"])
        first_ids = set(ids)
        quiz.reset()
        self.assertFalse(first_ids & {question["id"] for question in quiz.questions})

    def test_every_level_has_contextual_questions(self):
        for level in ("tutorial", "level1", "level2", "level3", "level4", "level5"):
            self.assertGreaterEqual(len(QUESTIONS_BY_LEVEL[level]), 3)

    def test_tutorial_starts_with_movement_and_requires_real_displacement(self):
        tutorial = Tutorial(PreviewProgress())
        self.assertEqual(tutorial.state, tutorial.MOVE)
        tutorial._check_progress()
        self.assertEqual(tutorial.state, tutorial.MOVE)
        tutorial.player.rect.x += 70
        tutorial._check_progress()
        self.assertEqual(tutorial.state, tutorial.JUMP)

    def test_guidance_panel_renders_with_hints_disabled(self):
        Box = type("Box", (), {})
        box = Box()
        box.stored = False
        scene_type = type("Level1", (), {})
        scene = scene_type()
        scene.boxes = [box]
        scene.carried_box = None
        scene.completed = False
        scene.message = ""
        scene.progress = PreviewProgress()
        scene.progress.hints_enabled = False
        scene.cutscene = type("Cutscene", (), {"active": False})()
        draw_mission_guidance(pygame.display.get_surface(), scene)


if __name__ == "__main__":
    unittest.main()
