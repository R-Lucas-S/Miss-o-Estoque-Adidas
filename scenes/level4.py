from pathlib import Path

import pygame

from systems.ui_theme import get_font

from entities.box import Box
from entities.camera import Camera
from entities.decorative_prop import DecorativeProp
from entities.npc import NPC, NarrativeCharacter
from entities.player import Player
from entities.separation_cart import SeparationCart
from entities.storage import Storage
from missao_estoque.settings import CAMERA_SMOOTHING, FLOOR_HEIGHT, MAP_WIDTH, SCREEN_HEIGHT, SCREEN_WIDTH
from scenes.quiz import Quiz
from systems.background import load_world_background
from systems.bottom_hud import BottomHUD, combo_color
from systems.cutscene_system import CutsceneSystem
from systems.dialogue_system import CommsSystem
from systems.mission_guidance import draw_mission_guidance
from systems.industrial_floor import IndustrialFloor
from systems.order_system import Order
from systems.results import build_result
from systems.scoring import Scoring
from systems.ui_icons import draw_check


class Level4:
    """separação de pedidos: localizar, escanear e levar itens ao carrinho."""

    ORDER_ITEMS = (
        {"category": "tennis", "label": "TÊNIS", "reference": "TN-014", "size": "40", "quantity": 1},
        {"category": "clothing", "label": "ROUPAS", "reference": "RP-022", "size": "M", "quantity": 1},
        {"category": "accessories", "label": "ACESSÓRIOS", "reference": "AC-018", "size": "-", "quantity": 1},
    )

    def __init__(self, progress):
        self.progress = progress
        self.floor = pygame.Rect(0, SCREEN_HEIGHT - FLOOR_HEIGHT, MAP_WIDTH, FLOOR_HEIGHT)
        self.floor_visual = IndustrialFloor(self.floor, seed=4)
        self.font = get_font(21, "ui", bold=True)
        self.small_font = get_font(17, "body")
        self.title_font = get_font(33, "display")
        path = Path(__file__).resolve().parents[1] / "missao_estoque" / "assets" / "environment" / "walls" / "level4_store_human_scale_v5.png"
        self.background = load_world_background(path, MAP_WIDTH, SCREEN_HEIGHT, source_ground_y=570)
        self.cutscene = CutsceneSystem()
        self.quiz = Quiz("level4", question_count=4, completion_scene=None)
        self.reset()

    def reset(self):
        self.player = Player(getattr(self.progress, "selected_character", "player_default"))
        self.camera = Camera(MAP_WIDTH, SCREEN_WIDTH, CAMERA_SMOOTHING)
        self.order = Order("A-104", self.ORDER_ITEMS)
        self.scoring = Scoring()
        self.bottom_hud = BottomHUD()
        self.storages = [
            Storage(660, self.floor.top, "TÊNIS", (70, 170, 255), "tennis"),
            Storage(1210, self.floor.top, "ROUPAS", (110, 205, 130), "clothing"),
            Storage(1760, self.floor.top, "ACESSÓRIOS", (174, 118, 225), "accessories"),
        ]
        self.cart = SeparationCart(2180, self.floor.top)
        self.props = []
        self.npcs = [
            NarrativeCharacter(310, self.floor.top, "rafael", "checker"),
            NPC(1510, self.floor.top, "organizer", (6_000, 9_000)),
        ]
        self.boxes = []
        self._add_box(730, "tennis", "TN-014", "42")
        self._add_box(815, "tennis", "TN-014", "40")
        self._add_box(900, "tennis", "TN-021", "40")
        self._add_box(1280, "clothing", "RP-022", "G")
        self._add_box(1365, "clothing", "RP-022", "M")
        self._add_box(1450, "clothing", "RP-030", "M")
        self._add_box(1830, "accessories", "AC-020", "-")
        self._add_box(1915, "accessories", "AC-018", "-")
        self.carried_box = None
        self.scanner_box = None
        self.scanner_until = 0
        self.scanner_uses = 0
        self.scan_line_until = 0
        self.cart_motion = None
        self.show_order = False
        self.message = "Leia o pedido e encontre os produtos corretos."
        self.feedback = ""
        self.feedback_color = (255, 255, 255)
        self.feedback_until = 0
        self.completed = False
        self.quiz_active = False
        self.started_at = pygame.time.get_ticks()
        self.cutscene.start("level4_intro")
        self.comms = CommsSystem()

    def _add_box(self, x, box_type, reference, size):
        box = Box(x, self.floor.top, box_type, product_data={"reference": reference, "size": size})
        box.home_midbottom = box.rect.midbottom
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
        if event.key == pygame.K_TAB:
            self.show_order = not self.show_order
        elif event.key == pygame.K_q:
            self._scan_nearby()
        elif event.key == pygame.K_e:
            self._interact()
        return None

    def _near_box(self):
        boxes = [box for box in self.boxes if not box.stored and box.is_near(self.player.rect)]
        return min(boxes, key=lambda box: abs(box.rect.centerx - self.player.rect.centerx), default=None)

    def _at_separation(self):
        return self.cart.accepts(self.player.rect)

    def _scan_nearby(self):
        box = self._near_box()
        if box is None:
            self.message = "Aproxime-se de uma caixa para escanear."
            return
        self.scanner_box = box
        self.scanner_until = pygame.time.get_ticks() + 3_000
        self.scan_line_until = pygame.time.get_ticks() + 260
        self.scanner_uses += 1
        self.message = "Produto solicitado." if self.order.can_separate(box) else "Produto não pertence ao pedido."
        self.comms.show("rafael", "Item confirmado pelo scanner." if self.order.can_separate(box) else "Esse item não pertence ao pedido.")

    def _interact(self):
        if self.carried_box:
            if not self._at_separation():
                self.message = "Leve o item para a área de separação."
                return
            accepted, text = self.order.separate(self.carried_box)
            if accepted:
                points = self.scoring.correct_delivery(self.carried_box)
                source_position = self.carried_box.rect.midbottom
                target_position = self.cart.slot_position(self.order.separated_count - 1)
                self.carried_box.set_status(Box.DELIVERED)
                self.carried_box.rect.midbottom = target_position
                self.cart_motion = (self.carried_box, source_position, target_position, pygame.time.get_ticks())
                self.carried_box = None
                self._feedback("%s  +%d" % (text, points), (80, 230, 145))
                self.comms.show("rafael", "Item separado. O pedido está avançando.")
                self.message = "Pedido: %d/%d itens separados." % (self.order.separated_count, self.order.total_count)
                self.completed = self.order.completed
            else:
                self.scoring.wrong_delivery()
                self.carried_box.set_status(Box.GROUND)
                self.carried_box.rect.midbottom = self.carried_box.home_midbottom
                self.carried_box = None
                self._feedback("PRODUTO INCORRETO", (235, 105, 95))
                self.comms.show("rafael", "Revise o pedido antes de colocar o item no carrinho.")
                self.message = text
            return
        if self.completed and self._at_separation():
            self.quiz_active = True
            self.quiz.enter()
            return
        box = self._near_box()
        if box:
            box.set_status(Box.CARRIED)
            self.carried_box = box
            self.message = "%s %s TAM %s em maos." % (box.product["name"], box.product["reference"], box.product["size"])
        else:
            self.message = "Aproxime-se de uma caixa ou da área de separação."

    def _feedback(self, text, color):
        self.feedback, self.feedback_color = text, color
        self.feedback_until = pygame.time.get_ticks() + 1_700

    def update(self, keys):
        if self.quiz_active:
            return None
        if self.cutscene.active:
            self.player.move_direction = 0
        else:
            self.player.handle_input(keys)
        solids = [box.rect for box in self.boxes if not box.carried and not box.stored]
        self.player.update(self.floor, MAP_WIDTH, solids, self.carried_box is not None)
        if self.carried_box:
            self.carried_box.follow_player(self.player)
        for npc in self.npcs:
            npc.update()
        if self.cart_motion and pygame.time.get_ticks() - self.cart_motion[3] >= 320:
            self.cart_motion = None
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
        self._draw_shadows(surface)
        for prop in self.props:
            if prop.layer == "back":
                prop.draw(surface, self.camera)
        for storage in self.storages:
            storage.draw(surface, self.camera)
        for prop in self.props:
            if prop.layer == "world":
                prop.draw(surface, self.camera)
        self._draw_separation(surface)
        for npc in self.npcs:
            npc.draw(surface, self.camera)
        for box in self.boxes:
            if box is not self.carried_box and (not self.cart_motion or box is not self.cart_motion[0]):
                box.draw(surface, self.camera, box.is_near(self.player.rect))
        self._draw_cart_motion(surface)
        self.player.draw(surface, self.camera)
        # A animacao CARRY já possui a caixa entre as maos do personagem.
        self._draw_hud(surface)
        if self.scanner_box and pygame.time.get_ticks() < self.scanner_until:
            self._draw_scanner(surface)
        if self.scanner_box and pygame.time.get_ticks() < self.scan_line_until:
            self._draw_scan_line(surface)
        draw_mission_guidance(surface, self)
        self.cutscene.draw(surface)
        self.comms.draw(surface)

    def _draw_shadows(self, surface):
        for storage in self.storages:
            self.floor_visual.draw_contact_shadow(surface, self.camera, storage.rect.centerx, storage.rect.width * .7)
        for prop in self.props:
            self.floor_visual.draw_contact_shadow(surface, self.camera, prop.x + prop.image.get_width() // 2, prop.image.get_width() * .65)
        for box in self.boxes:
            if not box.carried and not box.stored:
                self.floor_visual.draw_contact_shadow(surface, self.camera, box.rect.centerx, box.rect.width * .8)
        self.floor_visual.draw_contact_shadow(surface, self.camera, self.player.rect.centerx, self.player.rect.width)

    def _draw_separation(self, surface):
        active = self.carried_box is not None and self._at_separation()
        self.cart.draw(surface, self.camera, self.order.separated_count, active, self.completed)
        rect = self.camera.apply_rect(self.cart.rect)
        text = "[E] CONFERIR PEDIDO" if self.completed else "[E] SEPARAR"
        if self._at_separation() and (self.carried_box is not None or self.completed):
            prompt = self.small_font.render(text, True, (255, 220, 90))
            surface.blit(prompt, prompt.get_rect(midbottom=(rect.centerx, rect.y - 8)))

    def _draw_hud(self, surface):
        if not self.cutscene.active:
            feedback = (self.feedback, self.feedback_color) if pygame.time.get_ticks() < self.feedback_until else None
            self.bottom_hud.draw(surface, "MISSÃO 4  -  SEPARAÇÃO", ("PEDIDO " + self.order.order_id, "%d / %d" % (self.order.separated_count, self.order.total_count), (33, 150, 243), self.order.separated_count / self.order.total_count), (
                {"key": "score", "label": "PONTOS", "value": self.scoring.score, "display": str(self.scoring.score), "color": (255, 220, 90)},
                {"key": "combo", "label": "COMBO", "value": self.scoring.combo, "display": "x%d" % self.scoring.combo, "color": combo_color(self.scoring.combo)},
                {"key": "scanner", "label": "SCANNER", "value": self.scanner_uses, "display": "%d USOS" % self.scanner_uses, "color": (90, 190, 245)},
            ), feedback)
        if self.show_order:
            self._draw_order_panel(surface)

    def _draw_order_panel(self, surface):
        panel = pygame.Rect(28, 105, 315, 245)
        pygame.draw.rect(surface, (12, 25, 37), panel, border_radius=7)
        pygame.draw.rect(surface, (85, 162, 191), panel, 2, border_radius=7)
        title = self.font.render("PEDIDO %s" % self.order.order_id, True, (255, 220, 90))
        surface.blit(title, (48, 122))
        for index, item in enumerate(self.order.items):
            y = 160 + index * 58
            if item["separated"]:
                draw_check(surface, (58, y + 10), 8)
            else:
                pygame.draw.rect(surface, (165, 179, 188), (50, y + 2, 17, 17), 2, border_radius=3)
            line = self.small_font.render("%s  %s" % (item["label"], item["reference"]), True, (242, 245, 246))
            detail = self.small_font.render("TAM %s" % item["size"], True, (184, 203, 213))
            surface.blit(line, (80, y))
            surface.blit(detail, (80, y + 23))

    def _draw_scanner(self, surface):
        box = self.scanner_box
        panel = pygame.Rect(SCREEN_WIDTH - 290, 110, 260, 190)
        pygame.draw.rect(surface, (11, 26, 38), panel, border_radius=7)
        good = self.order.can_separate(box)
        color = (80, 230, 145) if good else (235, 145, 100)
        pygame.draw.rect(surface, color, panel, 2, border_radius=7)
        lines = ("SCANNER", box.product["name"], "REF " + box.product["reference"], "TAM " + box.product["size"], "SOLICITADO" if good else "NÃO PERTENCE AO PEDIDO")
        for index, text in enumerate(lines):
            label = self.font.render(text, True, color if index in (0, 4) else (240, 244, 246))
            surface.blit(label, (panel.x + 20, panel.y + 18 + index * 31))

    def _draw_scan_line(self, surface):
        rect = self.camera.apply_rect(self.scanner_box.rect)
        progress = 1 - (self.scan_line_until - pygame.time.get_ticks()) / 260
        y = rect.top + round(rect.height * progress)
        pygame.draw.line(surface, (125, 210, 190), (rect.left - 3, y), (rect.right + 3, y), 2)

    def _draw_cart_motion(self, surface):
        if not self.cart_motion:
            return
        box, start, target, started = self.cart_motion
        progress = min(1.0, (pygame.time.get_ticks() - started) / 320)
        progress = progress * progress * (3 - 2 * progress)
        x = start[0] + (target[0] - start[0]) * progress
        y = start[1] + (target[1] - start[1]) * progress - round(8 * (1 - progress))
        draw_rect = box.image.get_rect(midbottom=(self.camera.apply_x(round(x)), round(y)))
        surface.blit(box.image, draw_rect)

    def _finish_attempt(self):
        result = build_result(4, self.scoring, self.quiz, self.started_at, pygame.time.get_ticks(), accuracy=round(self.order.separated_count / max(1, self.order.separated_count + self.scoring.errors) * 100), objectives_completed=self.order.separated_count, scanner_uses=self.scanner_uses, order_id=self.order.order_id)
        self.progress.record_result(4, result)
