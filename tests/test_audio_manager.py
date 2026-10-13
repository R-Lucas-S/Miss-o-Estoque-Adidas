import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from missao_estoque.settings import PLAYER_SPRITE_HEIGHT, PLAYER_SPRITE_WIDTH
from systems.animation import AnimationPlayer
from systems.audio_manager import AudioManager


class MemoryProgress:
    def __init__(self):
        self.audio_settings = {
            "master_volume": .7, "music_volume": .3, "sfx_volume": .45,
            "music_enabled": True, "sfx_enabled": True, "muted": False,
        }
        self.saved = None

    def update_audio_settings(self, settings):
        self.audio_settings.update(settings)
        self.saved = dict(settings)


class AudioManagerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_real_assets_are_registered_and_cached(self):
        audio = AudioManager(MemoryProgress())
        self.assertIn("pixel_adventures", audio.music_tracks)
        if audio.available:
            self.assertIn("footstep", audio.sounds)

    def test_volume_mute_and_switches_are_persisted(self):
        progress = MemoryProgress()
        audio = AudioManager(progress)
        audio.set_volume("music", 1.5)
        self.assertEqual(audio.music_volume, 1.0)
        audio.set_enabled("sfx", False)
        audio.set_muted(True)
        self.assertFalse(progress.audio_settings["sfx_enabled"])
        self.assertTrue(progress.audio_settings["muted"])

    def test_walk_emits_steps_only_when_contact_frames_are_entered(self):
        animation = AnimationPlayer((PLAYER_SPRITE_WIDTH, PLAYER_SPRITE_HEIGHT), "player_default")
        animation.set("walk")
        emitted = []
        for _ in range(18):
            animation.update(dt_seconds=.05)
            emitted.extend(animation.consume_events())
        self.assertGreaterEqual(emitted.count("footstep"), 2)
        animation.set("jump")
        animation.update(dt_seconds=.05)
        self.assertEqual(animation.consume_events(), ())


if __name__ == "__main__":
    unittest.main()
