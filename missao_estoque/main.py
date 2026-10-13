import ctypes
import logging
import os
import traceback

import pygame

from missao_estoque.settings import (
    FPS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WINDOW_TITLE,
)
from scenes.level1 import Level1
from scenes.level2 import Level2
from scenes.level3 import Level3
from scenes.level4 import Level4
from scenes.level5 import Level5
from scenes.menu import Menu
from scenes.mission_map import MissionMap
from scenes.quiz import Quiz
from scenes.results import Results
from systems.audio_manager import AudioManager
from systems.progress import Progress
from scenes.tutorial import Tutorial
from scenes.character_select import CharacterSelect
from scenes.demo_splash import DemoSplash
from systems.runtime import IS_FROZEN, configure_logging, write_crash_log
from systems.display_manager import DisplayManager
from systems import frame_time
from entities.player import Player


def main():
    """Inicia e executa o loop principal do jogo."""
    configure_logging()
    if hasattr(ctypes, "windll"):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    progress = Progress()
    display = DisplayManager(progress)
    audio = AudioManager(progress)
    audio.play_music("pixel_adventures")

    screen = display.canvas
    clock = pygame.time.Clock()

    scenes = {
        "demo_splash": DemoSplash(progress),
        "menu": Menu(progress, audio, display),
        "character_select": CharacterSelect(progress),
        "tutorial": Tutorial(progress),
        "mission_map": MissionMap(progress),
        "results": Results(progress),
        "level1": Level1(progress),
        "level2": Level2(progress),
        "level3": Level3(progress),
        "level4": Level4(progress),
        "level5": Level5(progress),
        "quiz": Quiz(),
    }
    current_scene = "demo_splash" if IS_FROZEN and not progress.data.get("demo_welcome_seen", False) else "menu"
    running = True
    smoke_test = os.environ.get("MISSAO_DEMO_SMOKE_TEST") == "1"
    rendered_frames = 0

    while running:
        elapsed = clock.tick(FPS) / 1000.0
        frame_time.seconds = min(elapsed, .05)
        frame_time.game_fps = clock.get_fps()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F8:
                Player.animation_debug = not Player.animation_debug
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F9:
                Player.animation_slow = not Player.animation_slow
                continue
            if event.type == pygame.KEYDOWN and (
                event.key == pygame.K_F11
                or (event.key == pygame.K_RETURN and event.mod & pygame.KMOD_ALT)
            ):
                display.toggle_fullscreen()
                continue

            event = display.translate_event(event)
            next_scene = scenes[current_scene].handle_event(event)
            if next_scene == "quit":
                running = False
            elif next_scene in scenes:
                current_scene = next_scene
                scenes[current_scene].enter()

        next_scene = scenes[current_scene].update(pygame.key.get_pressed())
        if next_scene in scenes:
            current_scene = next_scene
            scenes[current_scene].enter()
        scenes[current_scene].draw(screen)
        display.present()
        rendered_frames += 1
        if smoke_test and rendered_frames >= 3:
            running = False


    audio.fadeout_music(300)
    pygame.quit()


def run_safely():
    try:
        main()
    except Exception:
        details = traceback.format_exc()
        try:
            crash_path = write_crash_log(details)
            logging.critical("Falha fatal\n%s", details)
            message = "O jogo encontrou um erro inesperado.\n\nUm arquivo de diagnóstico foi salvo em:\n" + str(crash_path)
        except Exception:
            message = "O jogo encontrou um erro inesperado e precisa ser fechado."
        if hasattr(ctypes, "windll"):
            ctypes.windll.user32.MessageBoxW(None, message, "Missão: Estoque Perfeito — DEMO", 0x10)
        else:
            print(message)
        raise


if __name__ == "__main__":
    run_safely()
