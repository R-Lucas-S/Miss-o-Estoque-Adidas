from pathlib import Path
import random

import pygame

from systems.ui_theme import get_font
from systems.background import load_framed_background
from systems.bottom_hud import BottomHUD, combo_color

from entities.box import Box
from entities.camera import Camera
from entities.decorative_prop import DecorativeProp
from entities.npc import NPC, NarrativeCharacter
from entities.player import Player
from entities.storage import Storage
from missao_estoque.settings import CAMERA_SMOOTHING, LEVEL3_FLOOR_TOP, LEVEL3_MAP_WIDTH, SCREEN_HEIGHT, SCREEN_WIDTH
from scenes.quiz import Quiz
from systems.results import build_result
from systems.cutscene_system import CutsceneSystem
from systems.dialogue_system import CommsSystem
from systems.mission_guidance import draw_mission_guidance
from systems.industrial_floor import IndustrialFloor
from systems.scoring import Scoring


class Level3:
    """Fase de conferência: identificar e corrigir caixas fora da categoria."""

    STORAGE_LAYOUT = (
        (500, "TÊNIS", "A-01", (70, 170, 255), "tennis"),
        (710, "ROUPAS", "B-01", (110, 205, 130), "clothing"),
        (915, "ACESSÓRIOS", "C-01", (174, 118, 225), "accessories"),
    )
    NPC_POSITIONS = (
        (350, "larissa", "checker", (7_000, 12_000)),
        (25, None, "resting", (9_000, 14_000)),
    )

    def __init__(self, progress):
        self.progress = progress
        self.floor = pygame.Rect(0, LEVEL3_FLOOR_TOP, LEVEL3_MAP_WIDTH, SCREEN_HEIGHT - LEVEL3_FLOOR_TOP)
        self.floor_visual = IndustrialFloor(self.floor, seed=3)
        self.font = get_font(21, "ui", bold=True)
        self.small_font = get_font(17, "body")
        self.code_font = get_font(14, "mono", bold=True)
        self.title_font = get_font(33, "display")
        self.cutscene = CutsceneSystem()
        self.quiz = Quiz("level3", question_count=3, completion_scene=None)
        image_path = Path(__file__).resolve().parents[1] / "missao_estoque" / "assets" / "environment" / "walls" / "level3_store_human_scale_v5.png"
        self.background = load_framed_background(image_path, LEVEL3_MAP_WIDTH, SCREEN_HEIGHT, source_ground_y=570)
        self.reset()

    def reset(self):
        self.player = Player(getattr(self.progress, "selected_character", "player_default"))
        self.camera = Camera(LEVEL3_MAP_WIDTH, SCREEN_WIDTH, CAMERA_SMOOTHING)
        self.storages = [Storage(x, self.floor.top, label, color, category) for x, label, code, color, category in self.STORAGE_LAYOUT]
        self.npcs = []
        for x, character, npc_type, timing in self.NPC_POSITIONS:
            npc = NarrativeCharacter(x, self.floor.top, character, npc_type, timing, calm=True) if character else NPC(x, self.floor.top, npc_type, timing, calm=True)
            npc.next_action_at = pygame.time.get_ticks() + random.randint(*timing)
            self.npcs.append(npc)
        self.props = []
        self.boxes = []
        self._add_box(535, "clothing", "TÊNIS", True, "RP-203")
        self._add_box(750, "accessories", "ROUPAS", True, "AC-078")
        self._add_box(955, "tennis", "ACESSÓRIOS", True, "TN-104")
        self._add_box(610, "tennis", "TÊNIS", False, "TN-116")
        self._add_box(820, "clothing", "ROUPAS", False, "RP-218")
        self._add_box(1035, "accessories", "ACESSÓRIOS", False, "AC-091")
        self.carried_box = None
        self.scoring = Scoring()
        self.bottom_hud = BottomHUD()
        self.corrected_divergences = 0
        self.confirmed_divergences = 0
        self.false_checks = 0
        self.feedback = ""
        self.feedback_color = (255, 255, 255)
        self.feedback_until = 0
        self.message = "Confira as etiquetas e corrija as divergências."
        self.completed = False
        self.quiz_active = False
        self.started_at = pygame.time.get_ticks()
        self.cutscene.start("level3_intro")
        self.comms = CommsSystem()

    def _add_box(self, x, box_type, current_section, is_divergence, reference):
        box = Box(x, self.floor.top, box_type, product_data={"reference": reference})
        box.current_section = current_section
        box.is_divergence = is_divergence
        box.checked = False
        box.check_state = "unchecked"
        box.discovery_score_awarded = False
        box.correction_score_awarded = False
        self.boxes.append(box)

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
                if not storage.accepts(self.player.rect):
                    continue
                if self.carried_box.check_state == "checked_divergent" and storage.label == self.carried_box.current_section:
                    self._show_feedback("JÁ CONFERIDO - LEVE A SEÇÃO CORRETA", (180, 205, 215))
                    self.message = "A divergência já foi registrada. Leve a caixa para %s." % self.carried_box.product["name"]
                    return
                if storage.accepts_box(self.carried_box):
                    if self.carried_box.correction_score_awarded:
                        self._show_feedback("CONFERÊNCIA JÁ REGISTRADA", (180, 205, 215))
                        return
                    points = self.scoring.correct_delivery(self.carried_box)
                    self.carried_box.correction_score_awarded = True
                    self.carried_box.check_state = "corrected"
                    storage.store(self.carried_box)
                    self.corrected_divergences += 1
                    self._show_feedback("OK - divergência CORRIGIDA  +%d" % points, (80, 230, 145))
                    self.comms.show("larissa", "Boa conferência. Um erro foi corrigido antes de seguir.")
                    self.carried_box = None
                    self.completed = self.corrected_divergences == self.total_divergences
                    self.message = "Todas as divergências foram corrigidas." if self.completed else "Continue a conferência: ainda há caixas fora do lugar."
                else:
                    self.carried_box.mistakes += 1
                    self.scoring.wrong_delivery()
                    self._show_feedback("ERRO - CATEGORIA INCORRETA", (235, 105, 95))
                    self.comms.show("larissa", "Confirme a categoria indicada na etiqueta.")
                    self.message = "Confira a etiqueta da caixa. Ela continua em suas maos."
                return
            self.message = "Aproxime-se de uma prateleira e pressione E para armazenar."
            return

        box = self._near_box()
        if box is None:
            self.message = "Aproxime-se de uma caixa para conferir."
            return
        if box.check_state == "unchecked":
            box.checked = True
            if box.is_divergence:
                box.check_state = "checked_divergent"
                self.confirmed_divergences += 1
                if not box.discovery_score_awarded:
                    self.scoring.add_points(50)
                    box.discovery_score_awarded = True
                self._show_feedback("! divergência ENCONTRADA  +50", (255, 220, 90))
                self.message = "%s está na seção %s. Leve para %s." % (box.product["name"], box.current_section, box.product["name"])
            else:
                box.check_state = "checked_correct"
                self._show_feedback("CAIXA JÁ ESTÁ CORRETA", (180, 205, 215))
                self.message = "%s está corretamente armazenada em %s." % (box.product["name"], box.current_section)
            return
        if box.is_divergence:
            box.set_status(Box.CARRIED)
            self.carried_box = box
            self.message = "Caixa de %s em maos. Encontre a prateleira correta." % box.product["name"]
        else:
            self._show_feedback("JÁ CONFERIDO", (180, 205, 215))
            self.message = "Conferência já registrada: categoria, referência e tamanho corretos."

    @property
    def total_divergences(self):
        return sum(box.is_divergence for box in self.boxes)

    @property
    def accuracy(self):
        valid_checks = sum(box.check_state != "unchecked" for box in self.boxes)
        attempts = valid_checks + self.scoring.errors
        return 100 if attempts == 0 else round(valid_checks / attempts * 100)

    def update(self, keys):
        if self.quiz_active:
            return None
        if self.cutscene.active:
            self.player.move_direction = 0
        else:
            self.player.handle_input(keys)
        solid_boxes = [box.rect for box in self.boxes if box.is_divergence and not box.carried and not box.stored]
        self.player.update(self.floor, LEVEL3_MAP_WIDTH, solid_boxes, self.carried_box is not None)
        if self.carried_box:
            self.carried_box.follow_player(self.player)
        for npc in self.npcs:
            npc.update()
        if self.cutscene.active:
            self.cutscene.update(self.camera)
        else:
            self.camera.update(self.player.rect)
        if not self.cutscene.active and not self.completed:
            self._update_contextual_message()
        return None

    def _update_contextual_message(self):
        if self.carried_box:
            storage = next((s for s in self.storages if s.accepts(self.player.rect)), None)
            if storage:
                self.message = "[E] ARMAZENAR em %s - %s" % (storage.label, self._storage_code(storage))
            return
        box = self._near_box()
        if box:
            action = "PEGAR" if box.checked and box.is_divergence else "CONFERIR"
            self.message = "[E] %s | local atual: %s" % (action, box.current_section)

    def draw(self, surface):
        if self.quiz_active:
            self.quiz.draw(surface)
            return
        surface.blit(self.background, (self.camera.apply_x(0), 0))
        self.floor_visual.draw(surface, self.camera)
        for prop in self.props:
            prop.draw(surface, self.camera)
        self._draw_storages(surface)
        for npc in self.npcs:
            self._draw_contact_shadow(surface, npc.rect.centerx, npc.rect.width)
            npc.draw(surface, self.camera)
        for box in self.boxes:
            if box is not self.carried_box:
                if not box.stored:
                    self._draw_contact_shadow(surface, box.rect.centerx, box.rect.width * .8)
                box.draw(surface, self.camera, box.is_near(self.player.rect))
        self._draw_contact_shadow(surface, self.player.rect.centerx, self.player.rect.width)
        self.player.draw(surface, self.camera)
        # A animacao CARRY já possui a caixa entre as maos do personagem.
        self._draw_hud(surface)
        draw_mission_guidance(surface, self)
        self.cutscene.draw(surface)
        self.comms.draw(surface)
        if self.completed and not self.cutscene.active:
            complete = self.title_font.render("CONFERÊNCIA CONCLUÍDA!", True, (80, 230, 145))
            next_step = self.font.render("Pressione ENTER para iniciar o quiz de conferência", True, (255, 218, 110))
            surface.blit(complete, complete.get_rect(center=(SCREEN_WIDTH // 2, 165)))
            surface.blit(next_step, next_step.get_rect(center=(SCREEN_WIDTH // 2, 205)))

    def _draw_storages(self, surface):
        for storage in self.storages:
            active = self.carried_box is not None and storage.accepts(self.player.rect)
            storage.draw(surface, self.camera, active)
            draw_rect = self.camera.apply_rect(storage.rect)
            subdued = tuple(max(55, value // 2) for value in storage.color)
            code = self.code_font.render(self._storage_code(storage), True, subdued)
            surface.blit(code, code.get_rect(bottomright=(draw_rect.right - 8, draw_rect.top - 8)))

    def _storage_code(self, storage):
        return next(code for _, label, code, _, category in self.STORAGE_LAYOUT if category == storage.destination)

    def _draw_contact_shadow(self, surface, world_x, width):
        self.floor_visual.draw_contact_shadow(surface, self.camera, world_x, width)

    def _draw_hud(self, surface):
        if self.cutscene.active:
            return
        feedback = (self.feedback, self.feedback_color) if pygame.time.get_ticks() < self.feedback_until else None
        self.bottom_hud.draw(surface, "MISSÃO 3  -  CONFERÊNCIA", ("DIVERGÊNCIAS", "%d / %d" % (self.corrected_divergences, self.total_divergences), (80, 210, 140), self.corrected_divergences / self.total_divergences), (
            {"key": "accuracy", "label": "PRECISÃO", "value": self.accuracy, "display": "%d%%" % self.accuracy},
            {"key": "score", "label": "PONTOS", "value": self.scoring.score, "display": str(self.scoring.score), "color": (255, 220, 90)},
            {"key": "combo", "label": "COMBO", "value": self.scoring.combo, "display": "x%d" % self.scoring.combo, "color": combo_color(self.scoring.combo)},
        ), feedback)

    def _show_feedback(self, text, color):
        self.feedback = text
        self.feedback_color = color
        self.feedback_until = pygame.time.get_ticks() + 1_800

    def _near_box(self):
        candidates = [box for box in self.boxes if not box.stored and box.is_near(self.player.rect)]
        if not candidates:
            return None
        return min(candidates, key=lambda box: abs(box.rect.centerx - self.player.rect.centerx))

    def _finish_attempt(self):
        result = build_result(
            3,
            self.scoring,
            self.quiz,
            self.started_at,
            pygame.time.get_ticks(),
            accuracy=self.accuracy,
            objectives_completed=self.corrected_divergences,
            false_checks=self.false_checks,
        )
        self.progress.record_result(3, result)
