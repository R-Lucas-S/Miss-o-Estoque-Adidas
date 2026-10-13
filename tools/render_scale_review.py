"""Renderiza quadros estaticos das fases para revisao visual de escala."""

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import pygame

from missao_estoque.settings import SCREEN_HEIGHT, SCREEN_WIDTH
from scenes.level1 import Level1
from scenes.level2 import Level2
from scenes.level3 import Level3
from scenes.level4 import Level4
from scenes.level5 import Level5
from scenes.tutorial import Tutorial
from scenes.character_select import CharacterSelect
from scenes.menu import Menu
from scenes.mission_map import MissionMap
from scenes.quiz import Quiz
from scenes.results import Results
from systems.animation import AnimationPlayer
from systems.ui_theme import get_font


class PreviewProgress:
    pending_result = None

    def __init__(self):
        self.selected_character = "player_default"
        self.data = {"has_selected_character": False}

    def select_character(self, character_id):
        self.selected_character = character_id
        self.data["has_selected_character"] = True

    def complete_tutorial(self):
        return None

    def record_result(self, level, result):
        return result

    @property
    def tutorial_completed(self):
        return True

    def level_unlocked(self, level):
        return level <= 5

    def level_data(self, level):
        return {"completed": level < 3, "stars": 3 if level == 1 else 2, "best_score": 1250}

    def take_pending_result(self):
        result = self.pending_result
        self.pending_result = None
        return result


def main():
    pygame.init()
    pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    output = PROJECT_ROOT / "artifacts" / "scale_pass"
    output.mkdir(parents=True, exist_ok=True)
    surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    preview_progress = PreviewProgress()
    menu = Menu(preview_progress)
    menu.draw(surface)
    pygame.image.save(surface, output / "menu_review.png")
    menu.page = "como_jogar"
    menu.draw(surface)
    pygame.image.save(surface, output / "menu_controls_review.png")
    selection = CharacterSelect(preview_progress)
    selection.enter()
    selection.draw(surface)
    pygame.image.save(surface, output / "character_select_review.png")
    selection.selected = 1
    selection.changed_at = pygame.time.get_ticks() - selection.TRANSITION_MS
    selection.draw(surface)
    pygame.image.save(surface, output / "character_select_luiza_review.png")
    mission_map = MissionMap(preview_progress)
    mission_map.draw(surface)
    pygame.image.save(surface, output / "mission_map_review.png")
    quiz = Quiz("level5", question_count=3, completion_scene="mission_map")
    quiz.questions = [__import__("data.questions", fromlist=["QUIZ_LEVEL_5"]).QUIZ_LEVEL_5[0]]
    quiz.draw(surface)
    pygame.image.save(surface, output / "quiz_review.png")
    preview_progress.pending_result = {
        "level": 5, "stars": 3, "score": 12450, "accuracy": 100,
        "errors": 0, "max_combo": 4, "quiz_correct": 3, "quiz_total": 3,
        "objectives_completed": 4, "elapsed_seconds": 138, "new_record": True,
        "scanner_uses": 4, "order_id": "A-104", "divergences_found": 1,
    }
    results = Results(preview_progress)
    results.enter()
    results.draw(surface)
    pygame.image.save(surface, output / "results_review.png")
    tutorial = Tutorial(preview_progress)
    tutorial.cutscene.active = False
    tutorial.bottom_hud.started_at -= 300
    tutorial.draw(surface)
    pygame.image.save(surface, output / "tutorial_scale_review.png")
    for number, scene_type in enumerate((Level1, Level2, Level3, Level4, Level5), 1):
        scene = scene_type(PreviewProgress())
        scene.cutscene.active = False
        scene.bottom_hud.started_at -= 300
        scene.player.rect.bottom = scene.floor.top
        scene.camera.x = 0
        scene.draw(surface)
        pygame.image.save(surface, output / f"level{number}_scale_review.png")
        if number == 1:
            scene.comms.show("marcelli", "Boa leitura da etiqueta. Continue nesse ritmo.", force=True)
            scene.draw(surface)
            pygame.image.save(surface, output / "level1_text_review.png")
        if number == 5:
            scene.player.rect.x = 1450
            scene.player.rect.bottom = scene.floor.top
            scene.camera.x = 950
            scene.draw(surface)
            pygame.image.save(surface, output / "level5_door_scale_review.png")
    for character_id in ("player_default", "luiza", "andrew_lessa"):
        preview_progress.selected_character = character_id
        scene = Level1(preview_progress)
        scene.cutscene.active = False
        scene.bottom_hud.started_at -= 300
        scene.player.rect.bottom = scene.floor.top
        scene.draw(surface)
        pygame.image.save(surface, output / f"player_{character_id}_review.png")
    _render_animation_reviews(output)
    pygame.quit()


def _render_animation_reviews(output):
    states = (
        "idle",
        "walk",
        "carry_idle",
        "carry_walk",
        "carry_jump",
        "carry_fall",
        "carry_land",
        "celebrate",
        "special_cross",
        "special_tap",
        "special_adjust",
    )
    font = get_font(15, "ui", bold=True)
    for character_id in ("player_default", "luiza", "andrew_lessa"):
        animation = AnimationPlayer((81, 110), character_id)
        review = pygame.Surface((900, len(states) * 130))
        review.fill((10, 21, 31))
        for row, state in enumerate(states):
            y = row * 130
            review.blit(font.render(state.upper(), True, (255, 220, 90)), (12, y + 10))
            pygame.draw.line(review, (80, 105, 118), (105, y + 118), (890, y + 118), 1)
            for index, frame in enumerate(animation.frames[state]["right"]):
                center_x = 150 + index * 115
                review.blit(frame, frame.get_rect(midbottom=(center_x, y + 118)))
        pygame.image.save(review, output / f"animations_{character_id}_review.png")


if __name__ == "__main__":
    main()
