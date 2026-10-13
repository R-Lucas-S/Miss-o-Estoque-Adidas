from pathlib import Path
import math

import pygame

from systems.ui_theme import get_font
from systems.text_layout import wrap_text

from missao_estoque.settings import SCREEN_HEIGHT, SCREEN_WIDTH
from systems.ui_icons import draw_check, draw_lock, draw_star
from data.playable_characters import character_definition
from systems.animation import AnimationPlayer


class MissionMap:
    """Mapa de campanha com seleção de missões jogáveis e futuras bloqueadas."""

    MISSIONS = (
        ("tutorial", "TREINAMENTO", "Aprenda os fundamentos.", 0),
        ("level1", "MISSÃO 1 - RECEBIMENTO", "Organize mercadorias recém-chegadas.", 1),
        ("level2", "MISSÃO 2 - ORGANIZAÇÃO", "Confira categoria, referência e tamanho.", 2),
        ("level3", "MISSÃO 3 - CONFERÊNCIA", "Encontre e corrija divergências.", 3),
        ("level4", "MISSÃO 4 - SEPARAÇÃO", "Localize e separe os produtos solicitados.", 4),
        ("level5", "MISSÃO 5 - REPOSIÇÃO", "Priorize e abasteça a área de vendas.", 5),
        (None, "MISSÃO FINAL - HORA DO PICO", "Em breve.", 6),
    )

    def __init__(self, progress):
        self.progress = progress
        self.title_font = get_font(40, "display")
        self.name_font = get_font(21, "ui", bold=True)
        self.current_name_font = get_font(15, "ui", bold=True)
        self.text_font = get_font(17, "body")
        path = Path(__file__).resolve().parents[1] / "missao_estoque" / "assets" / "environment" / "walls" / "level2_background.png"
        image = pygame.image.load(str(path)).convert()
        self.background = pygame.transform.scale(image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.selected = 0
        self.cards = []
        self.message = "Selecione uma missão."
        self.character_previews = {key: AnimationPlayer((55, 75), key) for key in ("player_default", "luiza", "andrew_lessa")}

    def enter(self):
        self.selected = min(self.selected, len(self.MISSIONS) - 1)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            for index, rect in enumerate(self.cards):
                if rect.collidepoint(event.pos):
                    self.selected = index
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for index, rect in enumerate(self.cards):
                if rect.collidepoint(event.pos):
                    self.selected = index
                    return self._activate()
        if event.type != pygame.KEYDOWN:
            return None
        if event.key in (pygame.K_LEFT, pygame.K_UP, pygame.K_a, pygame.K_w):
            self.selected = (self.selected - 1) % len(self.MISSIONS)
        elif event.key in (pygame.K_RIGHT, pygame.K_DOWN, pygame.K_d, pygame.K_s):
            self.selected = (self.selected + 1) % len(self.MISSIONS)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            return self._activate()
        elif event.key == pygame.K_ESCAPE:
            return "menu"
        elif event.key == pygame.K_c:
            return "character_select"
        return None

    def _activate(self):
        scene, _, _, level = self.MISSIONS[self.selected]
        if scene == "tutorial":
            return scene
        if scene and self.progress.level_unlocked(level):
            return scene
        if scene is None and level == 6 and self.progress.level_unlocked(level):
            self.message = "Missão final desbloqueada. Hora do Pico chega em breve."
            return None
        self.message = "Conclua a missão anterior. As próximas estão em breve."
        return None

    def update(self, keys):
        return None

    def draw(self, surface):
        surface.blit(self.background, (0, 0))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 13, 23, 210))
        surface.blit(overlay, (0, 0))
        title = self.title_font.render("MAPA DE MISSÕES", True, (255, 220, 90))
        surface.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 52)))
        self._draw_current_character(surface)
        self.cards = []
        for index, mission in enumerate(self.MISSIONS):
            column, row = index % 4, index // 4
            rect = pygame.Rect(55 + column * 300, 115 + row * 250, 260, 205)
            self.cards.append(rect)
            scene, name, subtitle, level = mission
            future_unlocked = scene is None and level == 6 and self.progress.level_unlocked(level)
            playable = scene == "tutorial" or bool(scene and self.progress.level_unlocked(level))
            active = index == self.selected
            color = (35, 82, 120) if playable else (42, 48, 57)
            if scene == "tutorial":
                color = (48, 125, 78)
            pygame.draw.rect(surface, (*color, 242), rect, border_radius=7)
            pygame.draw.rect(surface, (255, 220, 90) if active else (132, 153, 166), rect, 3 if active else 1, border_radius=7)
            if active:
                lift = round(math.sin(pygame.time.get_ticks() / 240) * 2)
                pygame.draw.rect(surface, (255, 230, 140), rect.move(0, lift), 1, border_radius=7)
            name_lines = self._wrap(name, 22)
            for line_index, line in enumerate(name_lines):
                label = self.name_font.render(line, True, (245, 247, 248))
                surface.blit(label, label.get_rect(center=(rect.centerx, rect.y + 35 + line_index * 27)))
            if scene == "tutorial":
                status = "CONCLUÍDO" if self.progress.tutorial_completed else "DISPONÍVEL"
            elif playable:
                data = self.progress.level_data(level)
                status = None
            elif future_unlocked:
                status = "DESBLOQUEADA"
            else:
                status = "BLOQUEADA"
            if scene == "tutorial" and self.progress.tutorial_completed:
                draw_check(surface, (rect.centerx - 62, rect.y + 112), 10)
            if scene and level:
                stars = self.progress.level_data(level)["stars"]
                for star_index in range(3):
                    draw_star(surface, (rect.centerx - 34 + star_index * 34, rect.y + 112), 13, star_index < stars)
            else:
                status_y = rect.y + 112
                if not playable and not future_unlocked:
                    draw_lock(surface, pygame.Rect(rect.centerx - 18, rect.y + 91, 36, 36))
                    status_y = rect.y + 140
                status_color = (80, 230, 145) if future_unlocked else ((255, 220, 90) if playable else (185, 190, 196))
                status_label = self.name_font.render(status, True, status_color)
                surface.blit(status_label, status_label.get_rect(center=(rect.centerx + (10 if scene == "tutorial" and self.progress.tutorial_completed else 0), status_y)))
            detail = subtitle if playable or future_unlocked else "Conclua a missão anterior."
            for line_index, line in enumerate(self._wrap(detail, 29)):
                label = self.text_font.render(line, True, (220, 225, 230))
                detail_y = rect.y + (172 if not playable else 145)
                surface.blit(label, label.get_rect(center=(rect.centerx, detail_y + line_index * 20)))
            if scene and level:
                best = self.progress.level_data(level)["best_score"]
                score = self.text_font.render("Melhor: %d" % best, True, (190, 205, 215))
                surface.blit(score, score.get_rect(center=(rect.centerx, rect.bottom - 20)))
        hint = self.text_font.render(self.message + "  ENTER: jogar | ESC: menu", True, (255, 220, 90))
        surface.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, 655)))
        change = self.text_font.render("[C] TROCAR PERSONAGEM", True, (120, 195, 245))
        surface.blit(change, change.get_rect(center=(SCREEN_WIDTH // 2, 684)))

    def _draw_current_character(self, surface):
        character_id = self.progress.selected_character
        definition = character_definition(character_id)
        panel = pygame.Rect(SCREEN_WIDTH - 255, 16, 225, 72)
        pygame.draw.rect(surface, (10, 23, 34, 238), panel, border_radius=6)
        pygame.draw.rect(surface, definition["accent"], panel, 2, border_radius=6)
        preview = self.character_previews[character_id]
        preview.update(.7)
        frame = preview.image("right")
        surface.blit(frame, frame.get_rect(midbottom=(panel.x + 40, panel.bottom - 3)))
        label = self.text_font.render("JOGANDO COMO", True, (171, 191, 202))
        surface.blit(label, (panel.x + 76, panel.y + 12))
        name_lines = wrap_text(definition["name"].upper(), self.current_name_font, panel.width - 88, max_lines=2)
        for index, line in enumerate(name_lines):
            name = self.current_name_font.render(line, True, definition["accent"])
            surface.blit(name, (panel.x + 76, panel.y + 37 + index * 16))

    @staticmethod
    def _wrap(text, width):
        words, lines, current = text.split(), [], ""
        for word in words:
            candidate = (current + " " + word).strip()
            if len(candidate) > width and current:
                lines.append(current)
                current = word
            else:
                current = candidate
        return lines + ([current] if current else [])
