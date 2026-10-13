from pathlib import Path

import pygame

from systems.ui_theme import get_font

from entities.box import Box
from entities.camera import Camera
from entities.npc import NarrativeCharacter
from entities.player import Player
from entities.shelf import Shelf
from entities.storage import Storage
from missao_estoque.settings import CAMERA_SMOOTHING, FLOOR_HEIGHT, SCREEN_HEIGHT, SCREEN_WIDTH
from scenes.quiz import Quiz
from systems.dialogue_system import DialogueSystem
from systems.cutscene_system import CutsceneSystem
from systems.industrial_floor import IndustrialFloor
from systems.background import load_world_background
from systems.bottom_hud import BottomHUD
from systems.text_layout import wrap_text
from systems.scoring import Scoring


class Tutorial:
    """Treinamento jogável: cada estado avança por uma ação real do jogador."""

    INTRO = "intro"
    MOVE = "move"
    JUMP = "jump"
    APPROACH_BOX = "approach_box"
    INSPECT = "inspect"
    PICKUP = "pickup"
    FIND_SHELF = "find_shelf"
    QUIZ = "quiz"
    FINAL = "final"
    COMPLETE = "complete"

    WORLD_WIDTH = 1800

    def __init__(self, progress):
        self.progress = progress
        self.font = get_font(21, "ui", bold=True)
        self.small_font = get_font(17, "body")
        self.title_font = get_font(34, "display")
        self.dialogue = DialogueSystem()
        self.cutscene = CutsceneSystem()
        self.quiz = Quiz("tutorial", question_count=1, completion_scene=None)
        self.floor = pygame.Rect(0, SCREEN_HEIGHT - FLOOR_HEIGHT, self.WORLD_WIDTH, FLOOR_HEIGHT)
        self.floor_visual = IndustrialFloor(self.floor, seed=17)
        path = Path(__file__).resolve().parents[1] / "missao_estoque" / "assets" / "environment" / "walls" / "level1_store_human_scale_v5.png"
        self.background = load_world_background(path, self.WORLD_WIDTH, SCREEN_HEIGHT, source_ground_y=570)
        self.bottom_hud = BottomHUD()
        self.reset()

    def reset(self):
        self.player = Player(getattr(self.progress, "selected_character", "player_default"))
        self.player.rect.x = 125
        self.player.rect.bottom = self.floor.top
        self.camera = Camera(self.WORLD_WIDTH, SCREEN_WIDTH, CAMERA_SMOOTHING)
        self.instructor = NarrativeCharacter(285, self.floor.top, "marcelli", "organizer")
        self.shelves = [Shelf(830, self.floor.top)]
        self.storages = [
            Storage(1170, self.floor.top, "TÊNIS", (70, 170, 255), "tennis"),
            Storage(1460, self.floor.top, "ROUPAS", (110, 205, 130), "clothing"),
        ]
        self.training_box = Box(650, self.floor.top, "tennis")
        self.final_box = None
        self.boxes = [self.training_box]
        self.carried_box = None
        self.scoring = Scoring()
        self.state = self.MOVE
        self.after_dialogue = None
        self.message = "Vamos começar! Use A e D para se movimentar."
        self.feedback = ""
        self.feedback_until = 0
        self.move_origin_x = self.player.rect.x
        self.jump_started = False
        self.hint_started_at = None
        self.final_mistakes = 0
        self.skip_confirmation = False
        self.fade_started_at = None
        self.quiz.reset()
        self.cutscene.start("prologue")

    def enter(self):
        self.reset()

    def handle_event(self, event):
        if self.cutscene.active:
            self.cutscene.handle_event(event)
            return None
        if event.type != pygame.KEYDOWN:
            return None
        if self.state == self.QUIZ:
            result = self.quiz.handle_event(event)
            if result == "quiz_complete":
                self._start_final_challenge()
            return result if result in ("menu", "quit") else None
        if self.skip_confirmation:
            if event.key in (pygame.K_y, pygame.K_RETURN):
                self.progress.complete_tutorial()
                return "mission_map"
            if event.key in (pygame.K_n, pygame.K_ESCAPE, pygame.K_p):
                self.skip_confirmation = False
            return None
        if event.key == pygame.K_ESCAPE:
            return "menu"
        if event.key == pygame.K_p and self.state != self.COMPLETE:
            self.skip_confirmation = True
            return None
        if self.dialogue.active:
            if event.key in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE) and self.dialogue.advance():
                self._finish_dialogue()
            return None
        if event.key == pygame.K_e:
            self.interact()
        if self.state == self.COMPLETE and event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
            self.fade_started_at = pygame.time.get_ticks()
        return None

    def interact(self):
        if self.state == self.INTRO and self._near_instructor():
            self._start_dialogue(("Bem-vindo ao estoque!", "Antes da sua primeira missão, vou mostrar como tudo funciona.", "Vamos começar pelo básico."), self._begin_move)
            return
        if self.carried_box:
            for storage in self.storages:
                if not storage.accepts(self.player.rect):
                    continue
                if storage.accepts_box(self.carried_box):
                    self.scoring.correct_delivery(self.carried_box)
                    storage.store(self.carried_box)
                    delivered = self.carried_box
                    self.carried_box = None
                    if delivered is self.training_box:
                        self._show_feedback("OK - ORGANIZAÇÃO CORRETA")
                        self._start_dialogue(("Perfeito! Você conferiu a caixa e encontrou o local correto.", "Boa! Agora quero ver se você entendeu."), self._begin_quiz)
                    else:
                        self._complete_training()
                    return
                self._handle_wrong_storage()
                return
            self.message = "Aproxime-se de uma prateleira e pressione E para armazenar."
            return
        target = self._near_box()
        if target and self.state in (self.PICKUP, self.FINAL):
            target.set_status(Box.CARRIED)
            self.carried_box = target
            if self.state == self.PICKUP:
                self.state = self.FIND_SHELF
                self.hint_started_at = pygame.time.get_ticks()
                self.message = "Leve a caixa para a prateleira TÊNIS."
                self._show_feedback("OK - CAIXA COLETADA")
                self._start_dialogue(("Essa caixa é de TÊNIS.", "Procure a prateleira correspondente."), None)
            else:
                self.message = "Organize a caixa corretamente."
            return
        if self.state == self.INSPECT and self.training_box.is_near(self.player.rect):
            self.state = self.PICKUP
            self.message = "Pressione [E] para pegar a caixa."

    def update(self, keys):
        self.instructor.update()
        if self.dialogue.active:
            self.dialogue.update()
        if self.fade_started_at is not None:
            if pygame.time.get_ticks() - self.fade_started_at >= 450:
                return "mission_map"
            return None
        if self.state == self.QUIZ:
            return
        if self.cutscene.active:
            self.player.move_direction = 0
            self.player.update(self.floor, self.WORLD_WIDTH, (), self.carried_box is not None)
            self.cutscene.update(self.camera)
        elif not self.dialogue.active and not self.skip_confirmation and self.state != self.COMPLETE:
            self.player.handle_input(keys)
            solid_boxes = [box.rect for box in self.boxes if not box.carried and not box.stored]
            self.player.update(self.floor, self.WORLD_WIDTH, solid_boxes, self.carried_box is not None)
            self._check_progress()
        else:
            self.player.move_direction = 0
            self.player.update(self.floor, self.WORLD_WIDTH, (), self.carried_box is not None)
        if self.carried_box:
            self.carried_box.follow_player(self.player)
        if not self.cutscene.active:
            self.camera.update(self.player.rect)
        return None

    def _check_progress(self):
        if self.state == self.MOVE:
            if self.move_origin_x is not None and abs(self.player.rect.x - self.move_origin_x) >= 70:
                self._show_feedback("BOA! VOCÊ JÁ SABE SE MOVIMENTAR.")
                self.state = self.JUMP
                self.message = "Agora pule usando ESPAÇO."
        elif self.state == self.JUMP:
            if not self.player.on_ground:
                self.jump_started = True
            if self.jump_started and self.player.on_ground and self.player.was_on_ground is False:
                self._show_feedback("BOA! PULO CONCLUÍDO.")
                self.state = self.APPROACH_BOX
                self.message = "Agora aproxime-se da caixa de treinamento."
        elif self.state == self.APPROACH_BOX and self.training_box.is_near(self.player.rect):
            self.state = self.INSPECT
            self._start_dialogue(("Antes de guardar qualquer produto, confira a identificação.", "Observe principalmente a categoria da caixa."), self._enable_pickup)
        elif self.state == self.FIND_SHELF:
            elapsed = pygame.time.get_ticks() - self.hint_started_at
            if elapsed > 16_000:
                self.message = "Dica: a seta aponta para a placa TÊNIS."
            elif elapsed > 8_000:
                self.message = "Dica: procure a placa TÊNIS nas prateleiras."
        elif self.state == self.FINAL and self.final_mistakes >= 2:
            self.message = "Dica: confira a categoria da etiqueta antes de escolher a seção."

    def _begin_move(self):
        self.state = self.MOVE
        self.move_origin_x = self.player.rect.x
        self.message = "Movimente-se para a direita. [A/D] ou setas"

    def _enable_pickup(self):
        self.state = self.PICKUP
        self.message = "Pressione [E] para pegar a caixa."

    def _begin_quiz(self):
        self.state = self.QUIZ
        self.quiz.enter()

    def _start_final_challenge(self):
        self.final_box = Box(930, self.floor.top, "clothing")
        self.boxes.append(self.final_box)
        self.state = self.FINAL
        self.message = "TREINAMENTO FINAL: organize a caixa corretamente."
        self._start_dialogue(("Agora é com você.", "Organize esta próxima caixa sem minha ajuda."), None)

    def _complete_training(self):
        self.progress.complete_tutorial()
        self.state = self.COMPLETE
        self.message = "TREINAMENTO CONCLUÍDO"
        self._start_dialogue(("Mandou bem!", "Agora você está pronto para sua primeira missão."), None)

    def _handle_wrong_storage(self):
        if self.state == self.FINAL:
            self.final_mistakes += 1
        self.message = "Essa não é a seção correta. Confira novamente a categoria da caixa."
        self._show_feedback("SEM PROBLEMA — TENTE NOVAMENTE")

    def _start_dialogue(self, lines, after):
        self.after_dialogue = after
        self.dialogue.start("CONFERENTE", lines)

    def _finish_dialogue(self):
        after = self.after_dialogue
        self.after_dialogue = None
        if after:
            after()

    def _near_instructor(self):
        return self.instructor.rect.colliderect(self.player.rect.inflate(70, 30))

    def _near_box(self):
        return next((box for box in self.boxes if not box.stored and box.is_near(self.player.rect)), None)

    def _show_feedback(self, text):
        self.feedback = text
        self.feedback_until = pygame.time.get_ticks() + 1_800

    def draw(self, surface):
        if self.state == self.QUIZ:
            self.quiz.draw(surface)
            return
        surface.blit(self.background, (self.camera.apply_x(0), 0))
        self.floor_visual.draw(surface, self.camera)
        self._draw_shadows(surface)
        for shelf in self.shelves:
            shelf.draw(surface, self.camera)
        for storage in self.storages:
            highlight = self.carried_box is not None and storage.accepts(self.player.rect)
            storage.draw(surface, self.camera, highlight)
        for box in self.boxes:
            if box is not self.carried_box:
                active = box is self.training_box and self.state in (self.APPROACH_BOX, self.INSPECT, self.PICKUP)
                box.draw(surface, self.camera, active)
        self.instructor.draw(surface, self.camera)
        self._draw_instructor_indicator(surface)
        self.player.draw(surface, self.camera)
        self._draw_objective_marker(surface)
        # A animacao CARRY já possui a caixa entre as maos do personagem.
        if not self.cutscene.active:
            self._draw_hud(surface)
            self._draw_box_panel(surface)
        self._draw_bottom_hud(surface)
        if self.dialogue.active:
            self.dialogue.draw(surface)
        self.cutscene.draw(surface)
        if self.skip_confirmation:
            self._draw_skip_confirmation(surface)
        if self.state == self.COMPLETE and not self.dialogue.active:
            self._draw_completion(surface)
        if self.fade_started_at is not None:
            alpha = min(255, round((pygame.time.get_ticks() - self.fade_started_at) / 450 * 255))
            fade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            fade.fill((0, 0, 0))
            fade.set_alpha(alpha)
            surface.blit(fade, (0, 0))

    def _draw_shadows(self, surface):
        for item in (self.instructor, self.player, *self.shelves, *self.storages):
            self.floor_visual.draw_contact_shadow(surface, self.camera, item.rect.centerx, item.rect.width * .8)
        for box in self.boxes:
            if not box.carried and not box.stored:
                self.floor_visual.draw_contact_shadow(surface, self.camera, box.rect.centerx, box.rect.width * .8)

    def _draw_instructor_indicator(self, surface):
        if self.state != self.INTRO:
            return
        rect = self.camera.apply_rect(self.instructor.rect)
        mark = self.title_font.render("!", True, (255, 220, 90))
        surface.blit(mark, mark.get_rect(center=(rect.centerx, rect.top - 20)))
        if self._near_instructor():
            label = self.font.render("[E] CONVERSAR", True, (255, 238, 170))
            surface.blit(label, label.get_rect(center=(rect.centerx, rect.top - 44)))

    def _draw_hud(self, surface):
        steps = {self.INTRO: "1/8", self.MOVE: "1/8", self.JUMP: "2/8", self.APPROACH_BOX: "3/8", self.INSPECT: "4/8", self.PICKUP: "5/8", self.FIND_SHELF: "6/8", self.FINAL: "8/8", self.COMPLETE: "8/8"}
        panel_width = 520
        line_height = self.font.get_linesize() + 2
        message_lines = wrap_text(self.message, self.font, panel_width - 32, max_lines=2)
        panel_height = 78 + max(0, len(message_lines) - 1) * line_height
        panel = pygame.Rect(22, 20, panel_width, panel_height)
        pygame.draw.rect(surface, (13, 23, 32, 225), panel, border_radius=6)
        pygame.draw.rect(surface, (235, 188, 58), panel, 2, border_radius=6)
        title = self.small_font.render("TUTORIAL " + steps.get(self.state, "7/8"), True, (255, 220, 110))
        surface.blit(title, (38, 31))
        message_top = 58
        for index, line in enumerate(message_lines):
            message = self.font.render(line, True, (244, 246, 247))
            surface.blit(message, (38, message_top + index * line_height))
        controls = pygame.Rect(panel.x, panel.bottom + 7, 310, 30)
        pygame.draw.rect(surface, (13, 23, 32, 205), controls, border_radius=4)
        pygame.draw.rect(surface, (74, 101, 118), controls, 1, border_radius=4)
        skip = self.small_font.render("[P] Pular treinamento    [ESC] Menu", True, (210, 220, 226))
        surface.blit(skip, skip.get_rect(center=controls.center))
        if pygame.time.get_ticks() < self.feedback_until:
            feedback = self.font.render(self.feedback, True, (80, 230, 145))
            surface.blit(feedback, feedback.get_rect(center=(SCREEN_WIDTH // 2, panel.bottom + 24)))

    def _draw_bottom_hud(self, surface):
        steps = {
            self.INTRO: 1, self.MOVE: 1, self.JUMP: 2, self.APPROACH_BOX: 3,
            self.INSPECT: 4, self.PICKUP: 5, self.FIND_SHELF: 6,
            self.QUIZ: 7, self.FINAL: 8, self.COMPLETE: 8,
        }
        current = steps.get(self.state, 1)
        self.bottom_hud.draw(
            surface,
            "TUTORIAL  -  TREINAMENTO",
            ("PROGRESSO", f"{current} / 8", (80, 210, 140), current / 8),
            (
                {"key": "step", "label": "ETAPA", "value": current, "display": str(current), "color": (255, 220, 90)},
                {"key": "score", "label": "PONTOS", "value": self.scoring.score, "display": str(self.scoring.score), "color": (80, 210, 140)},
            ),
            self.feedback if pygame.time.get_ticks() < self.feedback_until else "",
        )

    def _draw_box_panel(self, surface):
        nearby = self._near_box()
        if nearby is None or self.carried_box:
            return
        if self.state not in (self.INSPECT, self.PICKUP, self.FINAL):
            return
        panel = pygame.Rect(30, 385, 325, 130)
        pygame.draw.rect(surface, (20, 26, 33), panel, border_radius=6)
        pygame.draw.rect(surface, (240, 220, 130), panel, 3 if self.state == self.INSPECT else 2, border_radius=6)
        lines = ("CAIXA DE " + nearby.product["name"], "Referência: " + nearby.product["reference"], "Tamanho: " + nearby.product["size"], "[E] PEGAR")
        for index, line in enumerate(lines):
            label = self.font.render(line, True, (255, 220, 110) if index == 3 else (245, 245, 245))
            surface.blit(label, (50, panel.y + 12 + index * 28))

    def _draw_objective_marker(self, surface):
        if self.state not in (self.APPROACH_BOX, self.INSPECT, self.PICKUP, self.FIND_SHELF):
            return
        target_x = self.training_box.rect.centerx if self.state != self.FIND_SHELF else self.storages[0].rect.centerx
        screen_x = self.camera.apply_x(target_x)
        pulse = 4 + round((pygame.time.get_ticks() % 700) / 700 * 5)
        if screen_x < 25 or screen_x > SCREEN_WIDTH - 25:
            direction = 1 if screen_x > SCREEN_WIDTH // 2 else -1
            x = SCREEN_WIDTH - 34 if direction > 0 else 34
            points = ((x + direction * 12, 250), (x - direction * 8, 240), (x - direction * 8, 260))
            pygame.draw.polygon(surface, (255, 220, 90), points)
            label = self.small_font.render("OBJETIVO", True, (255, 220, 90))
            surface.blit(label, label.get_rect(center=(x, 225)))
            return
        pygame.draw.circle(surface, (255, 220, 90), (round(screen_x), self.floor.top - 8), 18 + pulse, 2)

    def _draw_skip_confirmation(self, surface):
        panel = pygame.Rect(SCREEN_WIDTH // 2 - 230, SCREEN_HEIGHT // 2 - 74, 460, 148)
        pygame.draw.rect(surface, (15, 23, 32), panel, border_radius=8)
        pygame.draw.rect(surface, (239, 190, 58), panel, 2, border_radius=8)
        question = self.font.render("Pular o treinamento?", True, (255, 255, 255))
        options = self.small_font.render("[ENTER/Y] SIM       [ESC/N] NÃO", True, (255, 220, 110))
        surface.blit(question, question.get_rect(center=(SCREEN_WIDTH // 2, panel.y + 55)))
        surface.blit(options, options.get_rect(center=(SCREEN_WIDTH // 2, panel.y + 98)))

    def _draw_completion(self, surface):
        panel = pygame.Rect(SCREEN_WIDTH // 2 - 280, 170, 560, 255)
        pygame.draw.rect(surface, (12, 22, 31, 240), panel, border_radius=8)
        pygame.draw.rect(surface, (80, 230, 145), panel, 2, border_radius=8)
        title = self.title_font.render("TREINAMENTO CONCLUÍDO", True, (80, 230, 145))
        surface.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 215)))
        for index, text in enumerate(("OK - Movimentação", "OK - Interação", "OK - Identificação", "OK - Organização", "OK - Conhecimento básico")):
            label = self.font.render(text, True, (242, 245, 246))
            surface.blit(label, (SCREEN_WIDTH // 2 - 150, 250 + index * 27))
        action = self.small_font.render("MISSÃO 1 LIBERADA — pressione ENTER", True, (255, 220, 110))
        surface.blit(action, action.get_rect(center=(SCREEN_WIDTH // 2, 395)))
