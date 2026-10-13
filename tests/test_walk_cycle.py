import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data.playable_characters import CHARACTER_IDS
from entities.player import Player
from systems.animation import AnimationPlayer


class WalkCycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    def test_distance_phase_and_position_agree_at_30_60_144_fps(self):
        for cid in CHARACTER_IDS:
            samples = []
            for fps in (30, 60, 144):
                player = Player(cid)
                player.rect.bottom = 500
                player.on_ground = True
                player.move_direction = 1
                for _ in range(fps * 2):
                    player.update(pygame.Rect(0, 500, 3000, 100), 3000, dt_seconds=1 / fps)
                    self.assertTrue(player.on_ground)
                    self.assertEqual(player.hitbox.size, (56, 92))
                samples.append((player.position.x, player.animation.frame_index, player.animation.animation_elapsed_ms))
            for sample in samples[1:]:
                self.assertAlmostEqual(sample[0], samples[0][0], places=5)
                self.assertEqual(sample[1], samples[0][1])
                self.assertAlmostEqual(sample[2], samples[0][2], places=5)

    def test_zero_distance_never_advances_and_contacts_alternate(self):
        animation = AnimationPlayer((81, 110))
        animation.set("walk")
        for _ in range(120):
            animation.update(dt_seconds=1 / 30, distance=0, cycle_distance=160)
        self.assertEqual(animation.frame_index, 0)
        contacts = []
        for _ in range(320):
            animation.update(dt_seconds=1 / 60, distance=1, cycle_distance=160)
            if animation.consume_events():
                contacts.append(animation.frame_index)
        self.assertEqual(contacts, [2, 0, 2, 0])

    def test_flip_is_exact_after_padding_and_baseline_stays_fixed(self):
        for cid in CHARACTER_IDS:
            animation = AnimationPlayer((81, 110), cid)
            for state in ("walk", "carry_walk"):
                for right, left in zip(animation.frames[state]["right"], animation.frames[state]["left"]):
                    self.assertEqual(pygame.image.tobytes(left, "RGBA"), pygame.image.tobytes(pygame.transform.flip(right, True, False), "RGBA"))
                    self.assertLessEqual(abs(right.get_bounding_rect(min_alpha=128).bottom - 110), 1)

    def test_stop_restart_jump_and_carry_keep_physical_anchor(self):
        floor = pygame.Rect(0, 500, 3000, 100)
        for cid in CHARACTER_IDS:
            player = Player(cid)
            player.rect.bottom = 500
            player.on_ground = True
            for carrying in (False, True):
                player.move_direction = 1
                for _ in range(35):
                    player.update(floor, 3000, carrying=carrying, dt_seconds=1 / 60)
                player.move_direction = 0
                player.update(floor, 3000, carrying=carrying, dt_seconds=1 / 60)
                self.assertEqual(player.state, "carry_idle" if carrying else "idle")
                player.move_direction = -1
                player.update(floor, 3000, carrying=carrying, dt_seconds=1 / 60)
                self.assertEqual(player.animation.frame_index, 0)
                player.velocity_y = -15
                player.on_ground = False
                states = set()
                for _ in range(100):
                    player.update(floor, 3000, carrying=carrying, dt_seconds=1 / 60)
                    states.add(player.state)
                    self.assertEqual(player.rect.size, (56, 92))
                    self.assertTrue(player.animation.image("left").get_bounding_rect().width)
                prefix = "carry_" if carrying else ""
                self.assertTrue({prefix + "jump", prefix + "fall", prefix + "land"}.issubset(states))
                self.assertEqual(player.feet_position[1], floor.top)

    def test_slow_motion_changes_animation_but_not_physics(self):
        floor = pygame.Rect(0, 500, 3000, 100)
        normal, slow = Player(), Player()
        slow.animation_slow = True
        for player in (normal, slow):
            player.rect.bottom = 500
            player.on_ground = True
            player.move_direction = 1
            for _ in range(40):
                player.update(floor, 3000, dt_seconds=1 / 60)
        self.assertEqual(normal.rect, slow.rect)
        self.assertNotEqual(normal.animation.frame_index, slow.animation.frame_index)


if __name__ == "__main__":
    unittest.main()
