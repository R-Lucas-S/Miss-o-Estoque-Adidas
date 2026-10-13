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


class Level1:
    """Primeira fase jogável, com movimento e pulo."""

    def __init__(self, progress):
        self.progress = progress
        self.floor = pygame.Rect(0, SCREEN_HEIGHT - FLOOR_HEIGHT, MAP_WIDTH, FLOOR_HEIGHT)
        self.floor_visual = IndustrialFloor(self.floor, seed=1)
        self.font = get_font(21, "ui", bold=True)
        self.title_font = get_font(33, "display")
        image_path = Path(__file__).resolve().parents[1] / "missao_estoque" / "assets" / "environment" / "walls" / "level1_store_human_scale_v5.png"
        self.background = load_world_background(image_path, MAP_WIDTH, SCREEN_HEIGHT, source_ground_y=570)
        self.cutscene = CutsceneSystem()
        self.reset()

    def reset(self):
        self.player = Player(getattr(self.progress, "selected_character", "player_default"))
        self.camera = Camera(MAP_WIDTH, SCREEN_WIDTH, CAMERA_SMOOTHING)
        self.storages = [
            Storage(1640, self.floor.top, "TÊNIS", (70, 170, 255), "tennis"),
            Storage(1880, self.floor.top, "ROUPAS", (110, 205, 130), "clothing"),
            Storage(2120, self.floor.top, "ACESSÓRIOS", (255, 175, 60), "accessories"),
        ]
        self.shelves = []
        self.props = []
        self.npcs = [
            NarrativeCharacter(270, self.floor.top, "marcelli", "organizer"),
            NPC(1370, self.floor.top, "organizer", (5_500, 8_000)),
            NPC(960, self.floor.top, "resting", (7_000, 10_000)),
        ]
        self.boxes = [
            Box(620, self.floor.top, "clothing", product_data={"reference": "RP-022", "size": "G"}),
            Box(1080, self.floor.top, "accessories", product_data={"reference": "AC-018"}),
            Box(1570, self.floor.top, "tennis", product_data={"reference": "TN-015", "size": "42"}),
        ]
        self.carried_box = None
        self.scoring = Scoring()
        self.bottom_hud = BottomHUD()
        self.feedback = ""
        self.feedback_color = (255, 255, 255)
        self.feedback_until = 0
        self.initial_message = "Observe a etiqueta e leve cada caixa para a prateleira correta."
        self.message = self.initial_message
        self.completed = False
        self.quiz_active = False
        self.quiz = Quiz("level1", question_count=3, completion_scene=None)
        self.started_at = pygame.time.get_ticks()
        self.cutscene.start("level1_intro")
        self.comms = CommsSystem()

    def enter(self):
        """Reinicia o jogador ao iniciar a fase."""
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
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "menu"

        if self.completed and event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.quiz_active = True
            self.quiz.enter()
            return None

        if event.type == pygame.KEYDOWN and event.key == pygame.K_e and not self.completed:
            self.interact()
        return None

    def interact(self):
        """Pega uma caixa próxima ou a guarda na estante."""
        if self.carried_box:
            for storage in self.storages:
                if storage.accepts(self.player.rect):
                    if storage.accepts_box(self.carried_box):
                        points = self.scoring.correct_delivery(self.carried_box)
                        storage.store(self.carried_box)
                        self.message = "Organização correta! +%d | Combo x%d" % (points, self.scoring.combo)
                        self.feedback, self.feedback_color = "CAIXA ARMAZENADA", (80, 230, 145)
                        self.feedback_until = pygame.time.get_ticks() + 1_700
                        self.comms.show("marcelli", "Boa leitura da etiqueta. Continue nesse ritmo.")
                        self.carried_box = None
                        self.completed = all(box.stored for box in self.boxes)
                    else:
                        self.carried_box.mistakes += 1
                        self.scoring.wrong_delivery()
                        hint = "Confira a etiqueta da caixa." if self.carried_box.mistakes == 1 else "Dica: procure a seção da categoria do produto."
                        self.message = "Ops! %s" % hint
                        self.feedback, self.feedback_color = "X  SEÇÃO INCORRETA", (235, 105, 95)
                        self.feedback_until = pygame.time.get_ticks() + 1_700
                        self.comms.show("marcelli", "Confira a etiqueta novamente antes de armazenar.")
                    return
            self.message = "Aproxime-se de uma prateleira e pressione E para armazenar."
            return

        for box in self.boxes:
            if not box.stored and box.is_near(self.player.rect):
                box.set_status(box.CARRIED)
                self.carried_box = box
                self.message = "Caixa de %s em maos. Procure a prateleira correspondente." % box.product["name"]
                return

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
            highlight = self.carried_box is not None and storage.accepts(self.player.rect)
            storage.draw(surface, self.camera, highlight)
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
            feedback = (self.feedback, self.feedback_color) if pygame.time.get_ticks() < self.feedback_until else None
            self.bottom_hud.draw(surface, "MISSÃO 1  -  RECEBIMENTO", ("CAIXAS", "%d / %d" % (done, len(self.boxes)), (255, 193, 64), done / len(self.boxes)), (
                {"key": "score", "label": "PONTOS", "value": self.scoring.score, "display": str(self.scoring.score), "color": (255, 220, 90)},
                {"key": "combo", "label": "COMBO", "value": self.scoring.combo, "display": "x%d" % self.scoring.combo, "color": combo_color(self.scoring.combo)},
            ), feedback)
        self._draw_nearby_box_info(surface)
        if SHOW_DEBUG:
            state = self.font.render("Estado: %s" % self.player.state.upper(), True, (230, 230, 230))
            surface.blit(state, (30, 124))

        if self.completed:
            complete = self.title_font.render("ESTOQUE ORGANIZADO!", True, (0, 220, 130))
            next_step = self.font.render("Pressione ENTER para iniciar o quiz", True, (255, 218, 110))
            surface.blit(complete, complete.get_rect(center=(SCREEN_WIDTH // 2, 170)))
            surface.blit(next_step, next_step.get_rect(center=(SCREEN_WIDTH // 2, 210)))
        draw_mission_guidance(surface, self)
        self.cutscene.draw(surface)
        self.comms.draw(surface)

    def _finish_attempt(self):
        result = build_result(1, self.scoring, self.quiz, self.started_at, pygame.time.get_ticks())
        self.progress.record_result(1, result)

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

    def _draw_nearby_box_info(self, surface):
        if self.carried_box:
            return
        nearby = next((box for box in self.boxes if not box.stored and box.is_near(self.player.rect)), None)
        if nearby is None:
            return
        panel = pygame.Rect(30, 354, 310, 135)
        pygame.draw.rect(surface, (20, 26, 33), panel, border_radius=6)
        pygame.draw.rect(surface, (240, 220, 130), panel, 2, border_radius=6)
        lines = (
            "CAIXA DE %s" % nearby.product["name"],
            "Referência: %s" % nearby.product["reference"],
            "Tamanho: %s" % nearby.product["size"],
            "[E] PEGAR",
        )
        for index, text in enumerate(lines):
            color = (255, 220, 110) if index == 3 else (245, 245, 245)
            label = self.font.render(text, True, color)
            surface.blit(label, (50, panel.y + 14 + index * 30))
        prompt = self.font.render("[E] PEGAR", True, (255, 225, 130))
        box_rect = self.camera.apply_rect(nearby.rect)
        surface.blit(prompt, prompt.get_rect(midbottom=(box_rect.centerx, box_rect.top - 8)))
