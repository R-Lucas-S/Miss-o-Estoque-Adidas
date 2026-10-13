import random
from pathlib import Path

import pygame

from entities.box import Box
from entities.camera import Camera
from entities.npc import NPC, NarrativeCharacter
from entities.player import Player
from entities.separation_cart import SeparationCart
from missao_estoque.settings import CAMERA_SMOOTHING, FLOOR_HEIGHT, MAP_WIDTH, SCREEN_HEIGHT, SCREEN_WIDTH
from scenes.quiz import Quiz
from systems.background import load_world_background
from systems.bottom_hud import BottomHUD
from systems.cutscene_system import CutsceneSystem
from systems.dialogue_system import CommsSystem
from systems.mission_guidance import draw_mission_guidance
from systems.industrial_floor import IndustrialFloor
from systems.results import build_result
from systems.scoring import Scoring
from systems.ui_icons import draw_check
from systems.ui_theme import get_font


class Level5:
    """Reposição: priorizar produtos e abastecer a área de vendas."""

    ORDER_ITEMS = (
        {"category": "tennis", "name": "TÊNIS", "reference": "TN-014", "size": "40", "priority": "ALTA"},
        {"category": "clothing", "name": "ROUPAS", "reference": "RP-022", "size": "M", "priority": "MEDIA"},
        {"category": "accessories", "name": "ACESSÓRIOS", "reference": "AC-018", "size": "-", "priority": "NORMAL"},
    )
    CHECKLIST = (
        ("quantity", "Quantidade correta"),
        ("references", "Referências corretas"),
        ("sizes", "Tamanhos corretos"),
        ("scanner", "Lista escaneada"),
        ("label", "Lista confirmada"),
        ("released", "Reposição concluída"),
    )

    def __init__(self, progress):
        self.progress = progress
        self.floor = pygame.Rect(0, SCREEN_HEIGHT - FLOOR_HEIGHT, MAP_WIDTH, FLOOR_HEIGHT)
        self.floor_visual = IndustrialFloor(self.floor, seed=5)
        self.font = get_font(21, "ui", bold=True)
        self.small_font = get_font(17, "body")
        self.tiny_font = get_font(15, "body")
        self.title_font = get_font(33, "display")
        path = Path(__file__).resolve().parents[1] / "missao_estoque" / "assets" / "environment" / "walls" / "level5_store_human_scale_v6.png"
        self.background = load_world_background(path, MAP_WIDTH, SCREEN_HEIGHT, source_ground_y=570)
        self.cutscene = CutsceneSystem()
        self.quiz = Quiz("level5", question_count=5, completion_scene=None)
        self.reset()

    def reset(self, divergence_index="random"):
        self.player = Player(getattr(self.progress, "selected_character", "player_default"))
        self.player.rect.x = 250
        self.camera = Camera(MAP_WIDTH, SCREEN_WIDTH, CAMERA_SMOOTHING)
        self.scoring = Scoring()
        self.bottom_hud = BottomHUD()
        self.cart = SeparationCart(850, self.floor.top)
        self.cart_boxes = []
        if divergence_index == "random":
            divergence_index = random.choice((None, 0, 1, 2))
        self.divergence_index = divergence_index
        for index, item in enumerate(self.ORDER_ITEMS):
            data = dict(item)
            if index == divergence_index:
                data["size"] = "42" if item["category"] == "tennis" else ("G" if item["category"] == "clothing" else "X")
            box = Box(0, self.floor.top, item["category"], product_data={"reference": data["reference"], "size": data["size"]})
            box.set_status(Box.DELIVERED)
            box.rect.midbottom = self.cart.slot_position(index)
            self.cart_boxes.append(box)
        self.correction_box = None
        if divergence_index is not None:
            item = self.ORDER_ITEMS[divergence_index]
            self.correction_box = Box(1260, self.floor.top, item["category"], product_data={"reference": item["reference"], "size": item["size"]})
        self.carried_box = None
        self.scanned = set()
        self.divergence_detected = False
        self.divergences_found = 0
        self.checks = {key: False for key, _ in self.CHECKLIST}
        self.prepared = False
        self.loading_started = 0
        self.loaded = False
        self.quiz_active = False
        self.show_checklist = False
        self.scanner_box = None
        self.scanner_good = False
        self.scanner_until = 0
        self.scan_line_until = 0
        self.scanner_uses = 0
        self.message = "O salão precisa de reposição. Comece pela prioridade ALTA."
        self.feedback = ""
        self.feedback_color = (255, 255, 255)
        self.feedback_until = 0
        self.started_at = pygame.time.get_ticks()
        self.props = []
        self.npcs = [NarrativeCharacter(410, self.floor.top, "jessica", "checker"), NarrativeCharacter(1050, self.floor.top, "larissa", "organizer")]
        self.cutscene.start("level5_intro")
        self.comms = CommsSystem(5_000)

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
            self.show_checklist = not self.show_checklist
        elif event.key == pygame.K_q:
            self._scan_cart_item()
        elif event.key == pygame.K_e:
            self._interact()
        return None

    def _near(self, x, radius=145):
        return abs(self.player.rect.centerx - x) <= radius

    def _scan_cart_item(self):
        if not self._near(self.cart.rect.centerx, 190):
            self.message = "Aproxime-se do carrinho para usar o scanner."
            return
        candidates = [i for i in range(len(self.cart_boxes)) if i not in self.scanned]
        if not candidates:
            self.message = "Todos os itens do carrinho já foram escaneados."
            return
        index = candidates[0]
        box = self.cart_boxes[index]
        expected = self.ORDER_ITEMS[index]
        good = box.product["reference"] == expected["reference"] and box.product["size"] == expected["size"]
        self.scanner_box, self.scanner_good = box, good
        now = pygame.time.get_ticks()
        self.scanner_until, self.scan_line_until = now + 3_000, now + 280
        self.scanner_uses += 1
        if good:
            self.scanned.add(index)
            points = self.scoring.correct_delivery(box)
            self._feedback("ITEM VALIDADO  +%d" % points, (80, 230, 145))
            self.message = "Item %d/%d validado." % (len(self.scanned), len(self.cart_boxes))
        else:
            self.divergence_detected = True
            self.divergences_found = 1
            self.scoring.add_points(75)
            self._feedback("divergência ENCONTRADA  +75", (255, 193, 64))
            self.message = "Reposição pausada. Busque o item correto na área de apoio."
            self.comms.show("larissa", "Boa. Era isso que precisavamos identificar.", force=True)
        self._refresh_validation()

    def _refresh_validation(self):
        all_scanned = len(self.scanned) == len(self.cart_boxes)
        all_correct = all(
            box.product["reference"] == expected["reference"] and box.product["size"] == expected["size"]
            for box, expected in zip(self.cart_boxes, self.ORDER_ITEMS)
        )
        self.checks["scanner"] = all_scanned
        self.checks["references"] = all_scanned and all_correct
        self.checks["sizes"] = all_scanned and all_correct

    def _interact(self):
        if self.carried_box:
            if not self._near(self.cart.rect.centerx, 190) or self.divergence_index is None:
                self.message = "Leve o item correto até o carrinho."
                return
            old = self.cart_boxes[self.divergence_index]
            old.set_status(Box.DELIVERED)
            self.carried_box.set_status(Box.DELIVERED)
            self.carried_box.rect.midbottom = self.cart.slot_position(self.divergence_index)
            self.cart_boxes[self.divergence_index] = self.carried_box
            self.carried_box = None
            self.scanned.discard(self.divergence_index)
            self.scoring.add_points(100)
            self._feedback("ITEM SUBSTITUIDO  +100", (80, 230, 145))
            self.message = "Item corrigido. Escaneie novamente para validar."
            self.comms.show("larissa", "Correcao feita. Confirme novamente no scanner.", force=True)
            self._refresh_validation()
            return
        if self.correction_box and not self.correction_box.stored and self.correction_box.is_near(self.player.rect):
            if not self.divergence_detected:
                self.message = "Confira primeiro os itens que estão no carrinho."
                return
            self.correction_box.set_status(Box.CARRIED)
            self.carried_box = self.correction_box
            self.message = "Item correto em maos. Leve-o ao carrinho."
            return
        if self._near(self.cart.rect.centerx, 190):
            self.checks["quantity"] = True
            self.scoring.add_points(50)
            if self.checks["scanner"] and self.checks["references"] and self.checks["sizes"]:
                self.message = "Produtos conferidos. Confirme a lista na estacao."
                self.comms.show("jessica", "Boa. Agora confirma a lista de reposição.", force=True)
            else:
                self.message = "Quantidade correta. Agora escaneie todos os itens com Q."
            return
        if self._near(310, 150):
            if not all(self.checks[key] for key in ("quantity", "references", "sizes", "scanner")):
                self._blocked("Confira os produtos antes de confirmar a lista.")
                return
            if not self.checks["label"]:
                self.checks["label"] = True
                self.scoring.add_points(75)
                self._feedback("LISTA CONFIRMADA  +75", (80, 230, 145))
                self.message = "Priorize e organize o carrinho para o salão."
            return
        if self._near(1580, 165):
            if not self.checks["label"]:
                self._blocked("Confirme a lista antes de organizar o carrinho.")
                return
            if not self.prepared:
                self.prepared = True
                self.cart.rect.x = 1470
                for index, box in enumerate(self.cart_boxes):
                    box.rect.midbottom = self.cart.slot_position(index)
                self.scoring.add_points(100)
                self._feedback("CARRINHO ORGANIZADO  +100", (80, 230, 145))
                self.message = "Carrinho pronto. Leve a reposição para a área de vendas."
                self.comms.show("larissa", "O salão está logo ali. Pode levar o carrinho.", force=True)
            return
        if self._near(2200, 180):
            if not self.prepared:
                self._blocked("Organize o carrinho antes de seguir para o salão.")
                return
            if not self.checks["released"]:
                self.checks["released"] = True
                self.scoring.add_points(150)
                self.loading_started = pygame.time.get_ticks()
                self._feedback("REPOSIÇÃO CONCLUÍDA  +150", (80, 230, 145))
                self.message = "Levando os produtos para a área de vendas."
                self.comms.show("rafael", "Boa. Estoque e salão trabalhando juntos ganham tempo.", force=True)
            return
        self.message = "Aproxime-se do carrinho, estacao ou acesso ao salão."

    def _blocked(self, message):
        self.scoring.wrong_delivery()
        self._feedback("REPOSIÇÃO PAUSADA", (244, 67, 54))
        self.message = message
        self.comms.show("larissa", "Confere as referências antes de levar para o salão.")

    def _feedback(self, text, color):
        self.feedback, self.feedback_color = text, color
        self.feedback_until = pygame.time.get_ticks() + 1_700

    def update(self, keys):
        if self.quiz_active:
            return None
        if self.cutscene.active or self.loading_started:
            self.player.move_direction = 0
        else:
            self.player.handle_input(keys)
        solids = [] if self.correction_box is None or self.correction_box.stored or self.correction_box.carried else [self.correction_box.rect]
        self.player.update(self.floor, MAP_WIDTH, solids, self.carried_box is not None)
        if self.carried_box:
            self.carried_box.follow_player(self.player)
        for npc in self.npcs:
            npc.update()
        if self.cutscene.active:
            self.cutscene.update(self.camera)
        elif self.loading_started:
            self.camera.focus_world_x(2140)
            if pygame.time.get_ticks() - self.loading_started >= 1_800:
                self.loaded = True
                self.loading_started = 0
                self.quiz_active = True
                self.quiz.enter()
        else:
            self.camera.update(self.player.rect, self.player.move_direction)
        return None

    def draw(self, surface):
        if self.quiz_active:
            self.quiz.draw(surface)
            return
        surface.blit(self.background, (self.camera.apply_x(0), 0))
        self.floor_visual.draw(surface, self.camera)
        cart_offset = self._cart_loading_offset()
        if not self.loaded:
            self.cart.draw(surface, self.camera, len(self.cart_boxes), self._near(self.cart.rect.centerx), self.checks["scanner"], cart_offset)
            self._draw_cart_boxes(surface, cart_offset)
        if self.correction_box and not self.correction_box.stored and self.correction_box is not self.carried_box:
            self.floor_visual.draw_contact_shadow(surface, self.camera, self.correction_box.rect.centerx, self.correction_box.rect.width * .8)
            self.correction_box.draw(surface, self.camera, self.correction_box.is_near(self.player.rect))
        for npc in self.npcs:
            npc.draw(surface, self.camera)
        self.floor_visual.draw_contact_shadow(surface, self.camera, self.player.rect.centerx, self.player.rect.width)
        self.player.draw(surface, self.camera)
        self._draw_world_prompt(surface)
        self._draw_hud(surface)
        if self.scanner_box and pygame.time.get_ticks() < self.scanner_until:
            self._draw_scanner(surface)
        draw_mission_guidance(surface, self)
        self.cutscene.draw(surface)
        self.comms.draw(surface)

    def _cart_loading_offset(self):
        if self.loaded:
            return 0
        if not self.loading_started:
            return 0
        progress = min(1, (pygame.time.get_ticks() - self.loading_started) / 1_500)
        return round((2130 - self.cart.rect.centerx) * progress)

    def _draw_cart_boxes(self, surface, offset_x=0):
        for box in self.cart_boxes:
            original_x = box.rect.x
            box.rect.x += offset_x
            box.draw(surface, self.camera)
            box.rect.x = original_x

    def _draw_world_prompt(self, surface):
        text, world_x = None, 0
        if self.carried_box and self._near(self.cart.rect.centerx, 190):
            text, world_x = "[E] SUBSTITUIR", self.cart.rect.centerx
        elif self._near(self.cart.rect.centerx, 190):
            text, world_x = "[E] CONFERIR   [Q] SCANEAR", self.cart.rect.centerx
        elif self._near(310, 150):
            text, world_x = "[E] CONFIRMAR LISTA", 310
        elif self._near(1580, 165):
            text, world_x = "[E] ORGANIZAR CARRINHO", 1580
        elif self._near(2200, 180):
            text, world_x = "[E] LEVAR PARA O SALÃO", 2200
        elif self.correction_box and not self.correction_box.stored and self.correction_box.is_near(self.player.rect):
            text, world_x = "[E] PEGAR ITEM CORRETO", self.correction_box.rect.centerx
        if text:
            label = self.small_font.render(text, True, (255, 220, 90))
            surface.blit(label, label.get_rect(midbottom=(self.camera.apply_x(world_x), self.floor.top - 118)))

    def _draw_hud_legacy(self, surface):
        panel = pygame.Rect(20, 18, 365, 72)
        pygame.draw.rect(surface, (8, 18, 28), panel, border_radius=6)
        pygame.draw.rect(surface, (33, 150, 243), panel, 2, border_radius=6)
        title = self.font.render("REPOSIÇÃO  •  LISTA A-104", True, (255, 220, 90))
        done = sum(self.checks.values())
        detail = self.small_font.render("Checklist %d/6   TAB: abrir   Pontos %d" % (done, self.scoring.score), True, (230, 237, 240))
        surface.blit(title, (35, 26))
        surface.blit(detail, (35, 58))
        if pygame.time.get_ticks() < self.feedback_until:
            label = self.font.render(self.feedback, True, self.feedback_color)
            surface.blit(label, label.get_rect(center=(SCREEN_WIDTH // 2, 112)))
        if self.show_checklist:
            self._draw_checklist(surface)

    def _draw_hud(self, surface):
        done = sum(self.checks.values())
        if not self.cutscene.active:
            pending_index = min(len(self.scanned), len(self.ORDER_ITEMS) - 1)
            priority = "CONCLUÍDA" if all(self.checks.values()) else self.ORDER_ITEMS[pending_index]["priority"]
            priority_color = (244, 90, 54) if priority == "ALTA" else (255, 193, 64)
            feedback = (self.feedback, self.feedback_color) if pygame.time.get_ticks() < self.feedback_until else None
            self.bottom_hud.draw(surface, "MISSÃO 5  -  REPOSIÇÃO", ("CHECKLIST", "%d / %d" % (done, len(self.CHECKLIST)), (80, 210, 140), done / len(self.CHECKLIST)), (
                {"key": "score", "label": "PONTOS", "value": self.scoring.score, "display": str(self.scoring.score), "color": (255, 220, 90)},
                {"key": "priority", "label": "PRIORIDADE", "value": priority, "display": "!  " + priority, "color": priority_color},
            ), feedback)
        if self.show_checklist:
            self._draw_checklist(surface)

    def _draw_checklist(self, surface):
        panel = pygame.Rect(28, 105, 340, 300)
        pygame.draw.rect(surface, (12, 25, 37), panel, border_radius=7)
        pygame.draw.rect(surface, (33, 150, 243), panel, 2, border_radius=7)
        title = self.font.render("REPOSIÇÃO A-104", True, (255, 220, 90))
        surface.blit(title, (48, 122))
        for index, (key, text) in enumerate(self.CHECKLIST):
            y = 168 + index * 35
            if self.checks[key]:
                draw_check(surface, (59, y + 8), 8)
            else:
                pygame.draw.rect(surface, (155, 177, 190), (51, y, 17, 17), 2, border_radius=3)
            label = self.small_font.render(text, True, (240, 244, 246))
            surface.blit(label, (80, y - 2))
        status = "REPOSIÇÃO CONCLUÍDA" if all(self.checks.values()) else "EM PREPARAÇÃO"
        color = (80, 230, 145) if all(self.checks.values()) else (255, 193, 64)
        label = self.font.render(status, True, color)
        surface.blit(label, label.get_rect(center=(panel.centerx, panel.bottom - 23)))

    def _draw_scanner(self, surface):
        box = self.scanner_box
        panel = pygame.Rect(SCREEN_WIDTH - 315, 110, 285, 205)
        color = (80, 230, 145) if self.scanner_good else (244, 67, 54)
        pygame.draw.rect(surface, (11, 26, 38), panel, border_radius=7)
        pygame.draw.rect(surface, color, panel, 2, border_radius=7)
        priority = self.ORDER_ITEMS[self.cart_boxes.index(box)]["priority"] if box in self.cart_boxes else "ALTA"
        lines = ("REPOSIÇÃO • " + priority, box.product["name"], "REF " + box.product["reference"], "TAM " + box.product["size"], "LISTA A-104", "CONFIRMADO" if self.scanner_good else "DIVERGÊNCIA")
        for index, text in enumerate(lines):
            font = self.font if index in (0, 5) else self.small_font
            label = font.render(text, True, color if index in (0, 5) else (240, 244, 246))
            surface.blit(label, (panel.x + 18, panel.y + 15 + index * 30))

    def _finish_attempt(self):
        attempts = self.scoring.correct_deliveries + self.scoring.errors
        accuracy = round(self.scoring.correct_deliveries / max(1, attempts) * 100)
        result = build_result(5, self.scoring, self.quiz, self.started_at, pygame.time.get_ticks(), accuracy=accuracy, objectives_completed=len(self.cart_boxes), scanner_uses=self.scanner_uses, order_id="A-104", divergences_found=self.divergences_found, checklist_completed=sum(self.checks.values()))
        self.progress.record_result(5, result)
