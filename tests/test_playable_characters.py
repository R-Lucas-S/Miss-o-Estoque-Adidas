import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from data.playable_characters import CHARACTER_IDS, PLAYABLE_CHARACTERS, character_definition
from entities.player import Player
from systems.animation import AnimationPlayer
from systems.progress import Progress
from scenes.character_select import CharacterSelect


class PlayableCharacterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    def test_all_character_assets_exist_and_render_gameplay_states(self):
        required = (
            "idle", "walk", "run", "jump", "fall", "land",
            "carry_idle", "carry_walk", "carry_jump", "carry_fall", "carry_land",
            "scan", "interact", "celebrate", "clap", "thinking", "push_cart",
            "special_cross", "special_tap", "special_adjust",
        )
        for character_id in CHARACTER_IDS:
            self.assertTrue(PLAYABLE_CHARACTERS[character_id]["sheet"].is_file())
            animation = AnimationPlayer((81, 110), character_id)
            for state in required:
                animation.set(state)
                animation.last_frame_at = 0
                animation.update(.65)
                frame = animation.image("right")
                self.assertEqual(frame.get_height(), 110)
                self.assertGreaterEqual(frame.get_width(), 81)
                if PLAYABLE_CHARACTERS[character_id]["layout"] == "grid_6x4":
                    expected = round(110 * PLAYABLE_CHARACTERS[character_id]["visual_scale"])
                    self.assertGreaterEqual(frame.get_bounding_rect(min_alpha=8).height, expected - 2)

    def test_every_character_uses_same_hitbox_and_ground_anchor(self):
        floor = pygame.Rect(0, 500, 800, 220)
        for character_id in CHARACTER_IDS:
            player = Player(character_id)
            player.rect.bottom = floor.top
            player.velocity_y = 0
            player.update(floor, 800)
            self.assertEqual(player.rect.size, (56, 92))
            self.assertEqual(player.rect.bottom, floor.top)

    def test_generated_characters_never_shrink_or_disappear_between_frames(self):
        checked_states = (
            "idle", "walk", "carry_idle", "carry_walk",
            "special_cross", "special_tap", "special_adjust",
        )
        for character_id in ("luiza", "andrew_lessa"):
            animation = AnimationPlayer((81, 110), character_id)
            expected = round(110 * PLAYABLE_CHARACTERS[character_id]["visual_scale"])
            for state in checked_states:
                for direction in ("right", "left"):
                    for frame in animation.frames[state][direction]:
                        bounds = frame.get_bounding_rect(min_alpha=8)
                        self.assertGreaterEqual(bounds.height, expected - 2, (character_id, state))
                        self.assertGreater(bounds.width, 20, (character_id, state))

    def test_carrying_a_box_preserves_character_scale(self):
        for character_id in ("luiza", "andrew_lessa"):
            animation = AnimationPlayer((81, 110), character_id)
            idle_height = animation.frames["idle"]["right"][0].get_bounding_rect(min_alpha=160).height
            for state in (
                "carry_idle", "carry_walk", "carry_jump", "carry_fall", "carry_land",
            ):
                for frame in animation.frames[state]["right"]:
                    carry_height = frame.get_bounding_rect(min_alpha=160).height
                    self.assertLessEqual(
                        abs(carry_height - idle_height),
                        3,
                        (character_id, state, idle_height, carry_height),
                    )

    def test_animation_timing_is_equivalent_at_30_and_60_fps(self):
        at_30 = AnimationPlayer((81, 110), "luiza")
        at_60 = AnimationPlayer((81, 110), "luiza")
        at_30.set("walk")
        at_60.set("walk")
        for _ in range(30):
            at_30.update(1.0, 1 / 30)
        for _ in range(60):
            at_60.update(1.0, 1 / 60)
        self.assertEqual(at_30.frame_index, at_60.frame_index)
        self.assertAlmostEqual(at_30.animation_elapsed_ms, at_60.animation_elapsed_ms, delta=1.0)

    def test_animation_clamps_large_frame_spikes(self):
        animation = AnimationPlayer((81, 110), "andrew_lessa")
        animation.set("walk")
        animation.update(1.0, .5)
        self.assertEqual(animation.frame_index, 0)
        self.assertLessEqual(animation.animation_elapsed_ms, animation.MAX_ELAPSED_MS)

    def test_blocked_input_does_not_play_walk(self):
        floor = pygame.Rect(0, 500, 800, 220)
        player = Player("player_default")
        player.rect.bottom = floor.top
        player.on_ground = True
        obstacle = pygame.Rect(player.rect.right, player.rect.top, 40, player.rect.height)
        player.move_direction = 1
        player.update(floor, 800, (obstacle,))
        self.assertEqual(player.actual_delta_x, 0)
        self.assertFalse(player.is_moving)
        self.assertEqual(player.state, "idle")

    def test_direction_input_interrupts_idle_special_even_when_blocked(self):
        floor = pygame.Rect(0, 500, 800, 220)
        player = Player("luiza")
        player.rect.bottom = floor.top
        player.on_ground = True
        player.state = "idle_special"
        player.special_name = "special_cross"
        player.special_started_at = pygame.time.get_ticks()
        player.animation.set("special_cross")
        obstacle = pygame.Rect(player.rect.right, player.rect.top, 40, player.rect.height)
        player.move_direction = 1
        player.update(floor, 800, (obstacle,))
        self.assertEqual(player.state, "idle")

    def test_selected_character_defaults_and_validation(self):
        progress = Progress.__new__(Progress)
        progress.data = Progress._default_data()
        progress.pending_result = None
        progress._save = lambda: None
        self.assertEqual(progress.selected_character, "player_default")
        progress.select_character("luiza")
        self.assertEqual(progress.selected_character, "luiza")
        progress.select_character("unknown")
        self.assertEqual(progress.selected_character, "player_default")

    def test_confirming_each_character_updates_without_crashing(self):
        class PreviewProgress:
            selected_character = "player_default"
            data = {"has_selected_character": False}

            def select_character(self, character_id):
                self.selected_character = character_id
                self.data["has_selected_character"] = True

        progress = PreviewProgress()
        scene = CharacterSelect(progress)
        scene.enter()
        for index, character_id in enumerate(CHARACTER_IDS):
            scene.selected = index
            scene._confirm()
            scene.previews[character_id].last_frame_at = 0
            self.assertIsNone(scene.update(None))
            self.assertEqual(progress.selected_character, character_id)
            scene.confirmed_at = None

    def test_every_character_uses_one_consistent_animation_canvas(self):
        for character_id in CHARACTER_IDS:
            animation = AnimationPlayer((81, 110), character_id)
            sizes = {
                frame.get_size()
                for directions in animation.frames.values()
                for frames in directions.values()
                for frame in frames
            }
            self.assertEqual(len(sizes), 1, character_id)

    def test_idle_specials_finish_instead_of_looping_for_ten_seconds(self):
        for character_id in CHARACTER_IDS:
            animation = AnimationPlayer((81, 110), character_id)
            animation.set("special_adjust")
            for _ in range(100):
                animation.update(1.0, .05)
            self.assertTrue(animation.finished, character_id)

    def test_footsteps_use_explicit_left_and_right_contact_frames(self):
        for character_id in CHARACTER_IDS:
            animation = AnimationPlayer((81, 110), character_id)
            self.assertEqual(animation.footstep_frames["walk"], (0, 2))
            self.assertEqual(animation.footstep_frames["carry_walk"], (0, 2))

    def test_walk_timing_matches_distance_travelled(self):
        floor = pygame.Rect(0, 500, 1200, 220)
        for character_id in CHARACTER_IDS:
            player = Player(character_id)
            player.rect.bottom = floor.top
            player.on_ground = True
            player.move_direction = 1
            player.update(floor, 1200)
            walk_multiplier = player._animation_speed_multiplier()
            frames = len(player.animation.frames["walk"]["right"])
            cycle_ms = player.animation.DURATIONS["walk"] * frames / walk_multiplier
            distance = abs(player.actual_delta_x) * 60 * cycle_ms / 1000
            self.assertAlmostEqual(distance, player.WALK_CYCLE_DISTANCE, delta=1.0)

            player.update(floor, 1200, carrying=True)
            carry_multiplier = player._animation_speed_multiplier()
            frames = len(player.animation.frames["carry_walk"]["right"])
            cycle_ms = player.animation.DURATIONS["carry_walk"] * frames / carry_multiplier
            distance = abs(player.actual_delta_x) * 60 * cycle_ms / 1000
            self.assertAlmostEqual(distance, player.CARRY_CYCLE_DISTANCE, delta=1.0)

    def test_display_names_match_the_character_selection(self):
        expected = {
            "player_default": "Daniel",
            "luiza": "Luiza",
            "andrew_lessa": "Andrew",
        }
        for character_id, name in expected.items():
            self.assertEqual(character_definition(character_id)["name"], name)


if __name__ == "__main__":
    unittest.main()
