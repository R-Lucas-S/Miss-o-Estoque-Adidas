import json

from systems.runtime import IS_FROZEN, user_data_dir


class Progress:
    """Save local, recordes e desbloqueios da campanha."""

    LEVEL_KEYS = ("1", "2", "3", "4", "5")

    def __init__(self):
        filename = "save_demo.json" if IS_FROZEN else "progress.json"
        self.path = user_data_dir() / filename
        self.data = self._default_data()
        self.pending_result = None
        self._load()

    @staticmethod
    def _default_data():
        return {
            "selected_character": "player_default",
            "has_selected_character": False,
            "tutorial_completed": False,
            "hints_enabled": True,
            "display": {"fullscreen": False},
            "highest_unlocked_level": 1,
            "audio": {
                "master_volume": 0.70,
                "music_volume": 0.30,
                "sfx_volume": 0.45,
                "music_enabled": True,
                "sfx_enabled": True,
                "muted": False,
            },
            "levels": {key: {"completed": False, "stars": 0, "best_score": 0, "best_accuracy": 0, "quiz_best": 0} for key in Progress.LEVEL_KEYS},
        }

    @property
    def audio_settings(self):
        return dict(self.data["audio"])

    def update_audio_settings(self, settings):
        self.data["audio"].update(settings)
        self._save()

    @property
    def fullscreen_enabled(self):
        return bool(self.data.get("display", {}).get("fullscreen", False))

    def set_fullscreen_enabled(self, enabled):
        self.data.setdefault("display", {})["fullscreen"] = bool(enabled)
        self._save()

    @property
    def tutorial_completed(self):
        return bool(self.data["tutorial_completed"])

    def complete_tutorial(self):
        self.data["tutorial_completed"] = True
        self._save()

    @property
    def hints_enabled(self):
        return bool(self.data.get("hints_enabled", True))

    def set_hints_enabled(self, enabled):
        self.data["hints_enabled"] = bool(enabled)
        self._save()

    @property
    def selected_character(self):
        from data.playable_characters import PLAYABLE_CHARACTERS
        value = self.data.get("selected_character", "player_default")
        return value if value in PLAYABLE_CHARACTERS else "player_default"

    def select_character(self, character_id):
        from data.playable_characters import PLAYABLE_CHARACTERS
        if character_id not in PLAYABLE_CHARACTERS:
            character_id = "player_default"
        self.data["selected_character"] = character_id
        self.data["has_selected_character"] = True
        self._save()

    def level_unlocked(self, level):
        return self.tutorial_completed and level <= self.data["highest_unlocked_level"]

    def level_data(self, level):
        return self.data["levels"].get(str(level), self._default_data()["levels"].get(str(level), self._default_data()["levels"]["1"]))

    @staticmethod
    def calculate_stars(result):
        if not result.get("completed"):
            return 0
        accuracy = result.get("accuracy", 0) / 100
        quiz_total = result.get("quiz_total", 0)
        quiz_ratio = 1 if quiz_total == 0 else result.get("quiz_correct", 0) / quiz_total
        errors = result.get("errors", 0)
        if accuracy >= .90 and quiz_ratio >= .80 and errors <= 1:
            return 3
        if accuracy >= .75 and quiz_ratio >= .50 and errors <= 2:
            return 2
        return 1

    def record_result(self, level, result):
        result = dict(result)
        result.setdefault("level", level)
        result["stars"] = self.calculate_stars(result)
        saved = self.level_data(level)
        is_record = result["score"] > saved["best_score"] or result["stars"] > saved["stars"]
        saved["completed"] = True
        saved["stars"] = max(saved["stars"], result["stars"])
        saved["best_score"] = max(saved["best_score"], result["score"])
        saved["best_accuracy"] = max(saved["best_accuracy"], result["accuracy"])
        saved["quiz_best"] = max(saved["quiz_best"], result.get("quiz_correct", 0))
        self.data["levels"][str(level)] = saved
        self.data["highest_unlocked_level"] = max(self.data["highest_unlocked_level"], min(level + 1, 6))
        result["new_record"] = is_record
        self.pending_result = result
        self._save()
        return result

    def take_pending_result(self):
        result = self.pending_result
        self.pending_result = None
        return result

    def reset(self):
        self.data = self._default_data()
        self.pending_result = None
        self._save()

    def _save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
        except OSError:
            pass

    def _load(self):
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(loaded, dict):
                return
            defaults = self._default_data()
            defaults.update({key: value for key, value in loaded.items() if key not in ("levels", "audio", "display")})
            if isinstance(loaded.get("audio"), dict):
                defaults["audio"].update(loaded["audio"])
            if isinstance(loaded.get("display"), dict):
                defaults["display"].update(loaded["display"])
            for key, value in loaded.get("levels", {}).items():
                if key in defaults["levels"] and isinstance(value, dict):
                    defaults["levels"][key].update(value)
            self.data = defaults
        except (OSError, ValueError, TypeError):
            pass
