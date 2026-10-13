from pathlib import Path

import pygame

from systems.ui_theme import get_font

from entities.box import Box
from entities.camera import Camera
from entities.decorative_prop import DecorativeProp
from entities.npc import NPC, NarrativeCharacter
from entities.player import Player
from entities.shelf import Shelf
from entities.storage import Storage
from scenes.quiz import Quiz
from systems.industrial_floor import IndustrialFloor
from systems.background import load_world_background
from systems.bottom_hud import BottomHUD, combo_color
from systems.results import build_result
from systems.scoring import Scoring
from systems.cutscene_system import CutsceneSystem
from systems.dialogue_system import CommsSystem
from systems.mission_guidance import draw_mission_guidance
from missao_estoque.settings import (
    CAMERA_SMOOTHING,
    FLOOR_HEIGHT,
    MAP_WIDTH,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SHOW_DEBUG,
)


class Level2:
    """Desafio de separar caixas nas estantes corretas."""

    def __init__(self, progress):
        self.progress = progress
        self.floor = pygame.Rect(0, SCREEN_HEIGHT - FLOOR_HEIGHT, MAP_WIDTH, FLOOR_HEIGHT)
        self.floor_visual = IndustrialFloor(self.floor, seed=2)
        self.font = get_font(21, "ui", bold=True)
        self.title_font = get_font(33, "display")
        image_path = Path(__file__).resolve().parents[1] / "missao_estoque" / "assets" / "environment" / "walls" / "level2_store_human_scale_v5.png"
        self.background = load_world_background(image_path, MAP_WIDTH, SCREEN_HEIGHT, source_ground_y=570)
        self.cutscene = CutsceneSystem()
        self.reset()

    def reset(self):
        self.player = Player(getattr(self.progress, "selected_character", "player_default"))
        self.camera = Camera(MAP_WIDTH, SCREEN_WIDTH, CAMERA_SMOOTHING)
        self.storages = [
            Storage(1540, self.floor.top, "TÊNIS", (70, 170, 255), "tennis", "TN-001", "40"),
            Storage(1800, self.floor.top, "ROUPAS", (110, 205, 130), "clothing", "RP-014", "M"),
            Storage(2060, self.floor.top, "ACESSÓRIOS", (255, 175, 60), "accessories", "AC-008"),
        ]
        self.shelves = []
        self.props = []
        self.npcs = [
            NarrativeCharacter(510, self.floor.top, "jessica", "organizer"),
            NPC(750, self.floor.top, "organizer", (5_500, 8_000)),
            NPC(2280, self.floor.top, "resting", (7_000, 10_000)),
        ]
        self.boxes = [
            Box(560, self.floor.top, "clothing"),
            Box(970, self.floor.top, "tennis"),
            Box(1300, self.floor.top, "accessories"),
        ]
        self.carried_box = None
        self.scoring = Scoring()
        self.bottom_hud = BottomHUD()
        self.feedback = ""
        self.feedback_color = (255, 255, 255)
        self.feedback_until = 0
        self.initial_message = "Confira categoria, referência e tamanho antes de armazenar."
        self.message = self.initial_message
        self.completed = False
        self.quiz_active = False
        self.quiz = Quiz("level1", question_count=3, completion_scene=None)
        self.started_at = pygame.time.get_ticks()
        self.cutscene.start("level2_intro")
        self.comms = CommsSystem()

    def enter(self):
        self.reset()

    def handle_event(self, event):
        if self.cutscene.active:
            self.cutscene.handle_event(event)
            return None
        if self.quiz_active:
            outcome = self.quiz.handle_event(event)
            if outcome == "quiz_complete":
                self._finish_attempt()
                return "results"
            return outcome
        if event.type != pygame.KEYDOWN:
            return None
        if event.key == pygame.K_ESCAPE:
            return "menu"
        if self.completed and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.quiz_active = True
            self.quiz.enter()
            return None
        if event.key == pygame.K_e and not self.completed:
            self.interact()
        return None

    def interact(self):
        if self.carried_box:
            for storage in self.storages:
                if storage.accepts(self.player.rect):
                    if storage.accepts_box(self.carried_box):
                        points = self.scoring.correct_delivery(self.carried_box)
                        storage.store(self.carried_box)
                        self.carried_box = None
                        self.message = "Conferência correta! +%d | Combo x%d" % (points, self.scoring.combo)
                        self.feedback, self.feedback_color = "ITEM CORRETO", (80, 230, 145)
                        self.feedback_until = pygame.time.get_ticks() + 1_700
                        self.comms.show("jessica", "Certo. Referência e tamanho conferem.")
                        self.completed = all(box.stored for box in self.boxes)
                    else:
                        self.carried_box.mistakes += 1
                        self.scoring.wrong_delivery()
                        self.message = "Confira categoria, referência e tamanho da etiqueta."
                        self.feedback, self.feedback_color = "X  ETIQUETA INCORRETA", (235, 105, 95)
                        self.feedback_until = pygame.time.get_ticks() + 1_700
                        self.comms.show("jessica", "Observe referência e tamanho antes de continuar.")
                    return
            self.message = "Aproxime-se de uma estante para guardar a caixa."
            return

        for box in self.boxes:
            if not box.stored and box.is_near(self.player.rect):
                box.set_status(box.CARRIED)
                self.carried_box = box
                self.message = "%s %s TAM %s em maos." % (box.product["name"], box.product["reference"], box.product["size"])
                return
        self.message = "Nenhuma caixa próxima para pegar."

    def update(self, keys):
        if self.quiz_active:
            return None
        if self.cutscene.active:
            self.player.move_direction = 0
        else:
            self.player.handle_input(keys)
        solid_boxes = [box.rect for box in self.boxes if not box.carried and not box.stored]
        self.player.update(self.floor, MAP_WIDTH, solid_boxes, self.carried_box is not None)
        if self.carried_box:
            self.carried_box.follow_player(self.player)
        for npc in self.npcs:
            npc.update()
        if self.cutscene.active:
            self.cutscene.update(self.camera)
        else:
            self.camera.update(self.player.rect, self.player.move_direction)
        return None

    def draw(self, surface):
        if self.quiz_active:
            self.quiz.draw(surface)
            return
        surface.blit(self.background, (self.camera.apply_x(0), 0))
        self.floor_visual.draw(surface, self.camera)
        self._draw_ground_shadows(surface)
        for prop in self.props:
            if prop.layer == "back":
                prop.draw(surface, self.camera)
        for shelf in self.shelves:
            shelf.draw(surface, self.camera)
        for storage in self.storages:
            storage.draw(surface, self.camera, self.carried_box is not None and storage.accepts(self.player.rect))
        for prop in self.props:
            if prop.layer == "world":
                prop.draw(surface, self.camera)
        for npc in self.npcs:
            npc.draw(surface, self.camera)
        for box in self.boxes:
            if box is not self.carried_box:
                box.draw(surface, self.camera, box.is_near(self.player.rect))
        self.player.draw(surface, self.camera)
        # A animacao CARRY já possui a caixa entre as maos do personagem.

        remaining = sum(not box.stored for box in self.boxes)
        if not self.cutscene.active:
            done = len(self.boxes) - remaining
            attempts = self.scoring.correct_deliveries + self.scoring.errors
            accuracy = 100 if attempts == 0 else round(self.scoring.correct_deliveries / attempts * 100)
            feedback = (self.feedback, self.feedback_color) if pygame.time.get_ticks() < self.feedback_until else None
            self.bottom_hud.draw(surface, "MISSÃO 2  -  ORGANIZAÇÃO", ("CAIXAS", "%d / %d" % (done, len(self.boxes)), (80, 210, 140), done / len(self.boxes)), (
                {"key": "score", "label": "PONTOS", "value": self.scoring.score, "display": str(self.scoring.score), "color": (255, 220, 90)},
                {"key": "combo", "label": "COMBO", "value": self.scoring.combo, "display": "x%d" % self.scoring.combo, "color": combo_color(self.scoring.combo)},
                {"key": "accuracy", "label": "PRECISÃO", "value": accuracy, "display": "%d%%" % accuracy},
            ), feedback)
        self._draw_nearby_box_info(surface)
        if SHOW_DEBUG:
            state = self.font.render("Estado: %s" % self.player.state.upper(), True, (230, 230, 230))
            surface.blit(state, (30, 124))

        if self.completed:
            complete = self.title_font.render("CATEGORIAS ORGANIZADAS!", True, (0, 220, 130))
            next_step = self.font.render("Pressione ENTER para iniciar o Nível 3", True, (255, 218, 110))
            surface.blit(complete, complete.get_rect(center=(SCREEN_WIDTH // 2, 170)))
            surface.blit(next_step, next_step.get_rect(center=(SCREEN_WIDTH // 2, 210)))
        draw_mission_guidance(surface, self)
        self.cutscene.draw(surface)
        self.comms.draw(surface)

    def _finish_attempt(self):
        result = build_result(2, self.scoring, self.quiz, self.started_at, pygame.time.get_ticks())
        self.progress.record_result(2, result)

    def _draw_nearby_box_info(self, surface):
        if self.carried_box:
            return
        nearby = next((box for box in self.boxes if not box.stored and box.is_near(self.player.rect)), None)
        if nearby is None:
            return
        panel = pygame.Rect(30, 359, 310, 130)
        pygame.draw.rect(surface, (20, 26, 33), panel, border_radius=6)
        pygame.draw.rect(surface, (240, 220, 130), panel, 2, border_radius=6)
        lines = ("CAIXA DE %s" % nearby.product["name"], "Referência: %s" % nearby.product["reference"], "Tamanho: %s" % nearby.product["size"], "[E] PEGAR")
        for index, text in enumerate(lines):
            label = self.font.render(text, True, (255, 220, 110) if index == 3 else (245, 245, 245))
            surface.blit(label, (50, panel.y + 12 + index * 28))
        prompt = self.font.render("[E] PEGAR", True, (255, 225, 130))
        box_rect = self.camera.apply_rect(nearby.rect)
        surface.blit(prompt, prompt.get_rect(midbottom=(box_rect.centerx, box_rect.top - 8)))

    def _draw_ground_shadows(self, surface):
        for shelf in self.shelves:
            self.floor_visual.draw_contact_shadow(surface, self.camera, shelf.rect.centerx, shelf.rect.width * 0.7)
        for storage in self.storages:
            self.floor_visual.draw_contact_shadow(surface, self.camera, storage.rect.centerx, storage.rect.width * 0.7)
        for prop in self.props:
            self.floor_visual.draw_contact_shadow(surface, self.camera, prop.x + prop.image.get_width() // 2, prop.image.get_width() * .65)
        for box in self.boxes:
            if not box.carried and not box.stored:
                self.floor_visual.draw_contact_shadow(surface, self.camera, box.rect.centerx, box.rect.width * 0.8)
        for npc in self.npcs:
            self.floor_visual.draw_contact_shadow(surface, self.camera, npc.rect.centerx, npc.rect.width * 0.9)
        self.floor_visual.draw_contact_shadow(surface, self.camera, self.player.rect.centerx, self.player.rect.width * 1.1)
