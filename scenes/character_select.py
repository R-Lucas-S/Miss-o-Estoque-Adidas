from pathlib import Path
import math

import pygame

from data.playable_characters import CHARACTER_IDS, PLAYABLE_CHARACTERS
from missao_estoque.settings import SCREEN_HEIGHT, SCREEN_WIDTH
from systems.animation import AnimationPlayer
from systems.text_layout import wrap_text
from systems.ui_theme import get_font


class CharacterSelect:
    """Seleção visual da equipe, sem alterar capacidades de gameplay."""

    CONFIRM_MS = 650
    TRANSITION_MS = 220

    def __init__(self, progress):
        self.progress = progress
        self.title_font = get_font(43, "display")
        self.name_font = get_font(29, "ui", bold=True)
        self.body_font = get_font(21, "body")
        self.small_font = get_font(16, "body", bold=True)
        path = Path(__file__).resolve().parents[1] / "missao_estoque" / "assets" / "environment" / "walls" / "level1_store_human_scale_v5.png"
        image = pygame.image.load(str(path)).convert()
        self.background = pygame.transform.scale(image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.previews = {key: AnimationPlayer((155, 215), key) for key in CHARACTER_IDS}
        self.cards = []
        self.confirm_rect = pygame.Rect(SCREEN_WIDTH // 2 - 140, 620, 280, 52)
        self.selected = 0
        self.changed_at = 0
        self.confirmed_at = None

    def enter(self):
        current = self.progress.selected_character
        self.selected = CHARACTER_IDS.index(current) if current in CHARACTER_IDS else 0
        self.changed_at = pygame.time.get_ticks()
        self.confirmed_at = None
        self.first_time = not self.progress.data.get("has_selected_character", False)

    def handle_event(self, event):
        if self.confirmed_at is not None:
            return None
        if event.type == pygame.MOUSEMOTION:
            for index, rect in enumerate(self.cards):
                if rect.collidepoint(event.pos):
                    self._select(index)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.confirm_rect.collidepoint(event.pos):
                self._confirm()
            else:
                for index, rect in enumerate(self.cards):
                    if rect.collidepoint(event.pos):
                        if index == self.selected:
                            self._confirm()
                        else:
                            self._select(index)
                        break
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self._select((self.selected - 1) % len(CHARACTER_IDS))
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self._select((self.selected + 1) % len(CHARACTER_IDS))
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._confirm()
            elif event.key == pygame.K_ESCAPE:
                return "menu"
        return None

    def _select(self, index):
        if index != self.selected:
            self.selected = index
            self.changed_at = pygame.time.get_ticks()

    def _confirm(self):
        self.progress.select_character(CHARACTER_IDS[self.selected])
        self.confirmed_at = pygame.time.get_ticks()
        self.previews[CHARACTER_IDS[self.selected]].set("celebrate")

    def update(self, keys):
        preview = self.previews[CHARACTER_IDS[self.selected]]
        preview.update(.65)
        if self.confirmed_at is not None and pygame.time.get_ticks() - self.confirmed_at >= self.CONFIRM_MS:
            return "mission_map"
        return None

    def draw(self, surface):
        surface.blit(self.background, (0, 0))
        dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((4, 12, 21, 205))
        surface.blit(dim, (0, 0))
        title = "ESCOLHA SEU PERSONAGEM" if self.first_time else "EQUIPE DO ESTOQUE"
        surface.blit(self.title_font.render(title, True, (255, 220, 90)), self.title_font.render(title, True, (255, 220, 90)).get_rect(center=(SCREEN_WIDTH // 2, 46)))
        subtitle = self.body_font.render("Escolha quem vai encarar as missões de hoje.", True, (220, 230, 235))
        surface.blit(subtitle, subtitle.get_rect(center=(SCREEN_WIDTH // 2, 83)))

        self.cards = []
        now = pygame.time.get_ticks()
        transition = min(1, (now - self.changed_at) / self.TRANSITION_MS)
        for index, character_id in enumerate(CHARACTER_IDS):
            definition = PLAYABLE_CHARACTERS[character_id]
            rect = pygame.Rect(70 + index * 395, 120, 350, 455)
            self.cards.append(rect)
            active = index == self.selected
            lift = -5 if active else 0
            card = rect.move(0, lift)
            fill = (11, 25, 37, 244) if active else (17, 28, 38, 225)
            pygame.draw.rect(surface, fill, card, border_radius=9)
            accent = definition["accent"]
            pulse = 1 + round((math.sin(now / 220) + 1) * .5) if active else 1
            pygame.draw.rect(surface, accent if active else (91, 112, 126), card, 2 + pulse if active else 1, border_radius=9)
            if active:
                glow = pygame.Surface((230, 230), pygame.SRCALPHA)
                pygame.draw.circle(glow, (*accent, 34), (115, 115), 105)
                surface.blit(glow, (card.centerx - 115, card.y + 15))
            animation = self.previews[character_id]
            if not active:
                animation.set("idle")
            frame = animation.image("right")
            slide = round((1 - transition) * (18 if index >= self.selected else -18)) if active else 0
            surface.blit(frame, frame.get_rect(midbottom=(card.centerx + slide, card.y + 250)))
            name = self.name_font.render(definition["name"].upper(), True, accent if active else (235, 240, 242))
            surface.blit(name, name.get_rect(center=(card.centerx, card.y + 292)))
            role = self.body_font.render(definition["role"], True, (190, 207, 216))
            surface.blit(role, role.get_rect(center=(card.centerx, card.y + 326)))
            for line_index, line in enumerate(wrap_text(definition["tagline"], self.body_font, card.width - 50, 3)):
                label = self.body_font.render(line, True, (238, 241, 243))
                surface.blit(label, label.get_rect(center=(card.centerx, card.y + 365 + line_index * 25)))
            state = "EM DESTAQUE" if active else "ESCOLHER"
            badge = self.small_font.render(state, True, accent if active else (145, 160, 170))
            surface.blit(badge, badge.get_rect(center=(card.centerx, card.bottom - 25)))

        chosen = PLAYABLE_CHARACTERS[CHARACTER_IDS[self.selected]]
        active_confirm = self.confirmed_at is not None
        color = (80, 230, 145) if active_confirm else chosen["accent"]
        pygame.draw.rect(surface, color, self.confirm_rect, border_radius=6)
        pygame.draw.rect(surface, (255, 246, 190), self.confirm_rect, 2, border_radius=6)
        text = "PERSONAGEM SELECIONADO!" if active_confirm else "SELECIONAR"
        label = self.name_font.render(text, True, (10, 20, 28))
        surface.blit(label, label.get_rect(center=self.confirm_rect.center))
        controls = self.small_font.render("A/D ou SETAS: escolher   ENTER: selecionar   ESC: voltar   mouse", True, (184, 201, 211))
        surface.blit(controls, controls.get_rect(center=(SCREEN_WIDTH // 2, 698)))
