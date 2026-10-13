import pygame

from systems.ui_theme import get_font

from missao_estoque.settings import SCREEN_HEIGHT, SCREEN_WIDTH
from systems.ui_icons import draw_star
from data.narrative import CHARACTERS
from systems.dialogue_system import DialogueSystem
from systems.text_layout import wrap_text


class Results:
    """Tela de resultado da tentativa, alimentada pelo Progress.pending_result."""

    NAMES = {1: "RECEBIMENTO", 2: "ORGANIZAÇÃO", 3: "CONFERÊNCIA", 4: "SEPARAÇÃO", 5: "REPOSIÇÃO"}

    def __init__(self, progress):
        self.progress = progress
        self.title_font = get_font(42, "display")
        self.font = get_font(23, "ui", bold=True)
        self.small_font = get_font(18, "body")
        self.result = None
        self.selected = 0
        self.buttons = []

    def enter(self):
        self.result = self.progress.take_pending_result()
        self.selected = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            for index, rect in enumerate(self.buttons):
                if rect.collidepoint(event.pos):
                    self.selected = index
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for index, rect in enumerate(self.buttons):
                if rect.collidepoint(event.pos):
                    self.selected = index
                    return self._activate()
        if event.type != pygame.KEYDOWN:
            return None
        if event.key in (pygame.K_LEFT, pygame.K_a):
            self.selected = (self.selected - 1) % len(self.buttons)
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self.selected = (self.selected + 1) % len(self.buttons)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            return self._activate()
        elif event.key == pygame.K_ESCAPE:
            return "mission_map"
        return None

    def _activate(self):
        level = self.result["level"]
        if self.selected == 0:
            return "level%d" % level
        if self.selected == 1:
            return "mission_map"
        return "level%d" % (level + 1) if level < 5 else "mission_map"

    def update(self, keys):
        return None

    def draw(self, surface):
        surface.fill((8, 17, 28))
        defaults = {"level": 1, "stars": 0, "score": 0, "accuracy": 0, "errors": 0, "max_combo": 0, "quiz_correct": 0, "quiz_total": 0, "objectives_completed": 0, "elapsed_seconds": 0, "new_record": False}
        result = {**defaults, **(self.result or {})}
        panel = pygame.Rect(260, 70, 760, 570)
        pygame.draw.rect(surface, (17, 31, 47), panel, border_radius=9)
        pygame.draw.rect(surface, (240, 190, 58), panel, 3, border_radius=9)
        title = self.title_font.render("MISSÃO CONCLUÍDA!", True, (255, 220, 90))
        name = self.font.render(self.NAMES[result["level"]], True, (230, 239, 244))
        surface.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 125)))
        surface.blit(name, name.get_rect(center=(SCREEN_WIDTH // 2, 165)))
        for index in range(3):
            draw_star(surface, (SCREEN_WIDTH // 2 - 48 + index * 48, 220), 20, index < result["stars"])
        elapsed = result["elapsed_seconds"]
        objective_name = "Divergências" if result["level"] == 3 else ("Itens validados" if result["level"] == 5 else "Caixas corretas")
        metrics = ("Pontuação: %d" % result["score"], "Precisão: %d%%" % result["accuracy"], "Erros: %d" % result["errors"], "Combo máximo: x%d" % result["max_combo"], "%s: %d" % (objective_name, result["objectives_completed"]), "Quiz: %d/%d" % (result["quiz_correct"], result["quiz_total"]), "Tempo: %02d:%02d" % (elapsed // 60, elapsed % 60))
        for index, text in enumerate(metrics):
            label = self.font.render(text, True, (235, 240, 242))
            x = 360 if index % 2 == 0 else 665
            y = 270 + (index // 2) * 40
            surface.blit(label, (x, y))
        if result["level"] == 3:
            false_checks = self.small_font.render("Falsos erros: %d" % result.get("false_checks", 0), True, (220, 225, 230))
            surface.blit(false_checks, false_checks.get_rect(center=(SCREEN_WIDTH // 2, 425)))
        if result["level"] == 4:
            scanner = self.small_font.render("Scanner: %d usos | Pedido: %s" % (result.get("scanner_uses", 0), result.get("order_id", "-")), True, (220, 225, 230))
            surface.blit(scanner, scanner.get_rect(center=(SCREEN_WIDTH // 2, 425)))
        if result["level"] == 5:
            replenishment = self.small_font.render("Lista: %s | Scanner: %d | Ajustes: %d" % (result.get("order_id", "-"), result.get("scanner_uses", 0), result.get("divergences_found", 0)), True, (220, 225, 230))
            surface.blit(replenishment, replenishment.get_rect(center=(SCREEN_WIDTH // 2, 425)))
        if result["new_record"]:
            record = self.font.render("NOVO RECORDE!", True, (80, 230, 145))
            surface.blit(record, record.get_rect(center=(SCREEN_WIDTH // 2, 452)))
        speaker = {1: "marcelli", 2: "jessica", 3: "larissa", 4: "rafael", 5: "rafael"}[result["level"]]
        profile = CHARACTERS[speaker]
        if result["level"] == 5:
            feedback = "Boa. Estoque e salão juntos ganham tempo." if result["stars"] == 3 else ("Bom trabalho. O salão já está sendo abastecido." if result["stars"] >= 2 else "Reposição concluída. Na próxima, revise as prioridades.")
        else:
            feedback = "Excelente execução. Você manteve o estoque em ordem." if result["stars"] == 3 else ("Missão concluída. Continue atento aos detalhes." if result["stars"] >= 2 else "Missão concluída. Na próxima, revise cada etapa com calma.")
        story_panel = pygame.Rect(300, 470, 680, 54)
        pygame.draw.rect(surface, (12, 25, 37), story_panel, border_radius=5)
        pygame.draw.rect(surface, profile["color"], story_panel, 1, border_radius=5)
        portrait = DialogueSystem._portrait(speaker)
        surface.blit(portrait, portrait.get_rect(midbottom=(story_panel.x + 38, story_panel.bottom + 14)))
        story = "%s: %s" % (profile["name"], feedback)
        for index, line in enumerate(wrap_text(story, self.small_font, story_panel.width - 92, max_lines=2)):
            narrator = self.small_font.render(line, True, (235, 241, 244))
            surface.blit(narrator, (story_panel.x + 76, story_panel.y + 8 + index * 19))
        labels = ("REPETIR", "MAPA", "PRÓXIMA" if result["level"] < 5 else "MAPA")
        self.buttons = []
        for index, label_text in enumerate(labels):
            rect = pygame.Rect(330 + index * 210, 535, 185, 52)
            self.buttons.append(rect)
            active = index == self.selected
            pygame.draw.rect(surface, (51, 141, 83) if active else (34, 57, 77), rect, border_radius=5)
            pygame.draw.rect(surface, (255, 220, 90), rect, 2, border_radius=5)
            label = self.small_font.render(label_text, True, (255, 255, 255))
            surface.blit(label, label.get_rect(center=rect.center))
