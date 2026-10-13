from pathlib import Path
import logging

import pygame

from missao_estoque.settings import (
    AUDIO_AMBIENCE_VOLUME,
    AUDIO_MASTER_VOLUME,
    AUDIO_MUSIC_VOLUME,
    AUDIO_SFX_VOLUME,
)
from systems.runtime import resource_path


AUDIO_ROOT = resource_path("Som")
DEFAULT_AUDIO = {
    "master_volume": AUDIO_MASTER_VOLUME,
    "music_volume": AUDIO_MUSIC_VOLUME,
    "sfx_volume": AUDIO_SFX_VOLUME,
    "music_enabled": True,
    "sfx_enabled": True,
    "muted": False,
}
MUSIC_REGISTRY = {"pixel_adventures": AUDIO_ROOT / "Pixel adventures.mp3"}
SOUND_REGISTRY = {"footstep": AUDIO_ROOT / "1.ogg"}
_audio_manager = None


class SilentAudioManager:
    """Fallback com a mesma API, útil antes da inicialização e sem dispositivo."""

    available = False
    master_volume = DEFAULT_AUDIO["master_volume"]
    music_volume = DEFAULT_AUDIO["music_volume"]
    sfx_volume = DEFAULT_AUDIO["sfx_volume"]
    music_enabled = True
    sfx_enabled = True
    muted = False
    current_music = None

    def play_sound(self, *args, **kwargs):
        return False

    def play_music(self, *args, **kwargs):
        return False

    def duck_music(self, *args, **kwargs):
        return None

    def set_volume(self, category, value, persist=True):
        attribute = {"master": "master_volume", "music": "music_volume", "sfx": "sfx_volume"}.get(category)
        if attribute:
            setattr(self, attribute, max(0.0, min(1.0, float(value))))

    def set_enabled(self, category, enabled, persist=True):
        if category in ("music", "sfx"):
            setattr(self, f"{category}_enabled", bool(enabled))

    def set_muted(self, muted, persist=True):
        self.muted = bool(muted)

    def toggle_muted(self):
        self.set_muted(not self.muted)


_silent_audio = SilentAudioManager()


def set_audio_manager(manager):
    global _audio_manager
    _audio_manager = manager


def get_audio_manager():
    return _audio_manager or _silent_audio


class AudioManager:
    """Serviço central de música e efeitos, com persistência e fallback seguro."""

    def __init__(self, progress=None):
        self.progress = progress
        saved = progress.audio_settings if progress is not None else DEFAULT_AUDIO
        self.master_volume = self._clamp(saved.get("master_volume", AUDIO_MASTER_VOLUME))
        self.music_volume = self._clamp(saved.get("music_volume", AUDIO_MUSIC_VOLUME))
        self.ambience_volume = AUDIO_AMBIENCE_VOLUME
        self.sfx_volume = self._clamp(saved.get("sfx_volume", AUDIO_SFX_VOLUME))
        self.music_enabled = bool(saved.get("music_enabled", True))
        self.sfx_enabled = bool(saved.get("sfx_enabled", True))
        self.muted = bool(saved.get("muted", False))
        self.sounds = {}
        self.music_tracks = {}
        self.current_music = None
        self._missing_assets = set()
        self._music_duck = 1.0
        self.available = self._initialize_mixer()
        self.channels = {}
        if self.available:
            self.channels = {
                "ambience": pygame.mixer.Channel(1),
                "player": pygame.mixer.Channel(2),
                "world": pygame.mixer.Channel(3),
                "ui": pygame.mixer.Channel(4),
            }
        self._load_registry()
        self._apply_music_volume()
        set_audio_manager(self)

    @staticmethod
    def _clamp(value):
        return max(0.0, min(1.0, float(value)))

    def _initialize_mixer(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(44100, -16, 2, 512)
            pygame.mixer.set_num_channels(max(pygame.mixer.get_num_channels(), 5))
            return True
        except pygame.error as error:
            print("[áudio] Mixer indisponível:", error)
            logging.warning("Mixer indisponível: %s", error)
            return False

    def _load_registry(self):
        for name, path in MUSIC_REGISTRY.items():
            self.register_music(name, path)
        for name, path in SOUND_REGISTRY.items():
            self.register_sound(name, path)

    def register_sound(self, name, path):
        if not self.available:
            return False
        asset_path = Path(path)
        if not asset_path.is_file():
            self._warn_missing(asset_path)
            return False
        try:
            self.sounds[name] = pygame.mixer.Sound(str(asset_path))
            return True
        except pygame.error as error:
            self._warn_missing(asset_path, error)
            return False

    def register_music(self, name, path):
        asset_path = Path(path)
        if not asset_path.is_file():
            self._warn_missing(asset_path)
            return False
        self.music_tracks[name] = asset_path
        return True

    def play_sound(self, name, category="world", volume=1.0):
        if not self.available or self.muted or not self.sfx_enabled or name not in self.sounds:
            return False
        base_volume = self.ambience_volume if category == "ambience" else self.sfx_volume
        sound = self.sounds[name]
        sound.set_volume(self._clamp(base_volume * self.master_volume * volume))
        channel = self.channels.get(category, self.channels.get("world"))
        if channel is None:
            return False
        channel.play(sound)
        return True

    def play_music(self, name, fade_ms=900):
        if not self.available or name not in self.music_tracks:
            return False
        if name == self.current_music and pygame.mixer.music.get_busy():
            self._apply_music_volume()
            return True
        try:
            pygame.mixer.music.load(str(self.music_tracks[name]))
            pygame.mixer.music.play(-1, fade_ms=max(0, int(fade_ms)))
            self.current_music = name
            self._apply_music_volume()
            return True
        except pygame.error as error:
            self._warn_missing(self.music_tracks[name], error)
            return False

    def fadeout_music(self, fade_ms=500):
        if self.available:
            pygame.mixer.music.fadeout(max(0, int(fade_ms)))

    def duck_music(self, amount=0.45):
        """Reserva simples para falas/cutscenes: 1.0 normal, 0.0 silencioso."""
        self._music_duck = self._clamp(amount)
        self._apply_music_volume()

    def restore_music(self):
        self._music_duck = 1.0
        self._apply_music_volume()

    def set_volume(self, category, value, persist=True):
        attribute = {"master": "master_volume", "music": "music_volume", "sfx": "sfx_volume"}.get(category)
        if attribute is None:
            return
        setattr(self, attribute, self._clamp(value))
        self._apply_music_volume()
        if persist:
            self._persist()

    def set_enabled(self, category, enabled, persist=True):
        enabled = bool(enabled)
        if category == "music":
            self.music_enabled = enabled
        elif category == "sfx":
            self.sfx_enabled = enabled
            if self.available and not enabled:
                for channel in self.channels.values():
                    channel.stop()
        else:
            return
        self._apply_music_volume()
        if persist:
            self._persist()

    def set_muted(self, muted, persist=True):
        self.muted = bool(muted)
        self._apply_music_volume()
        if self.available and self.muted:
            for channel in self.channels.values():
                channel.stop()
        if persist:
            self._persist()

    def toggle_muted(self):
        self.set_muted(not self.muted)

    def _apply_music_volume(self):
        if self.available:
            enabled = not self.muted and self.music_enabled
            volume = self.master_volume * self.music_volume * self._music_duck if enabled else 0.0
            pygame.mixer.music.set_volume(self._clamp(volume))

    def _persist(self):
        if self.progress is not None:
            self.progress.update_audio_settings({
                "master_volume": self.master_volume,
                "music_volume": self.music_volume,
                "sfx_volume": self.sfx_volume,
                "music_enabled": self.music_enabled,
                "sfx_enabled": self.sfx_enabled,
                "muted": self.muted,
            })

    def _warn_missing(self, path, error=None):
        if path not in self._missing_assets:
            suffix = f" ({error})" if error else ""
            print(f"[áudio] Asset indisponível: {path}{suffix}")
            logging.warning("Asset de áudio indisponível: %s%s", path, suffix)
            self._missing_assets.add(path)
