from pathlib import Path

import pygame

from systems.ui_theme import get_font
from systems.text_layout import wrap_text

from data.narrative import CHARACTERS
from missao_estoque.settings import GAME_VIEW_HEIGHT, SCREEN_HEIGHT, SCREEN_WIDTH


class DialogueSystem:
    """diálogos curtos com retrato cacheado, quebra de linha e digitacao rapida."""

    CHARACTERS_PER_SECOND = 42
    _portraits = {}

    def __init__(self):
        self.name_font = get_font(21, "ui", bold=True)
        self.text_font = get_font(22, "body")
        self.hint_font = get_font(17, "body", bold=True)
        self.active = False
        self.lines = ()
        self.index = 0
        self.visible_characters = 0
        self.last_update_at = pygame.time.get_ticks()

    def start(self, speaker_or_lines, lines=None):
        """Aceita a API antiga ``start(nome, falas)`` e linhas data-driven."""
        if lines is None:
            self.lines = tuple(speaker_or_lines)
        else:
            key = str(speaker_or_lines).lower()
            self.lines = tuple({"speaker": key, "expression": "normal", "text": text} for text in lines)
        self.index = 0
        self.visible_characters = 0
        self.last_update_at = pygame.time.get_ticks()
        self.active = bool(self.lines)

    @property
    def current(self):
        return self.lines[self.index] if self.active else None

    def update(self):
        if not self.active:
            return
        now = pygame.time.get_ticks()
        elapsed = now - self.last_update_at
        if elapsed > 0:
            self.visible_characters = min(len(self.current["text"]), self.visible_characters + elapsed * self.CHARACTERS_PER_SECOND / 1000)
            self.last_update_at = now

    def advance(self):
        """avança uma fala e devolve True quando o dialogo termina."""
        if not self.active:
            return False
        if self.visible_characters < len(self.current["text"]):
            self.visible_characters = len(self.current["text"])
            return False
        self.index += 1
        if self.index >= len(self.lines):
            self.active = False
            return True
        self.visible_characters = 0
        self.last_update_at = pygame.time.get_ticks()
        return False

    @classmethod
    def _portrait(cls, speaker, expression="normal", target_size=(82, 96)):
        speaker_key = speaker.lower()
        key = (speaker_key, expression.lower(), target_size)
        if key in cls._portraits:
            return cls._portraits[key]
        profile = CHARACTERS.get(speaker_key, CHARACTERS["conferente"])
        # Portraits já são bustos individuais com alpha/padding; não há crop de
        # corpo inteiro durante o draw. Expressao ausente usa NORMAL com seguranca.
        root = Path(__file__).resolve().parents[1] / "missao_estoque" / "assets" / "characters" / "portraits" / profile["portrait_dir"]
        path = root / (expression.lower() + ".png")
        if not path.exists():
            path = root / "normal.png"
        sprite = pygame.image.load(str(path)).convert_alpha()
        scale = min(target_size[0] / sprite.get_width(), target_size[1] / sprite.get_height())
        size = (max(1, round(sprite.get_width() * scale)), max(1, round(sprite.get_height() * scale)))
        canvas = pygame.Surface(target_size, pygame.SRCALPHA)
        scaled = pygame.transform.scale(sprite, size)
        canvas.blit(scaled, scaled.get_rect(center=canvas.get_rect().center))
        cls._portraits[key] = canvas
        return cls._portraits[key]

    def _wrapped_lines(self, text, max_width):
        return wrap_text(text, self.text_font, max_width, max_lines=3)

    def draw(self, surface):
        if not self.active:
            return
        entry = self.current
        profile = CHARACTERS.get(entry["speaker"].lower(), CHARACTERS["conferente"])
        dim = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 42))
        surface.blit(dim, (0, 0))
        panel = pygame.Rect(82, SCREEN_HEIGHT - 178, SCREEN_WIDTH - 164, 132)
        shade = pygame.Surface(panel.size, pygame.SRCALPHA)
        shade.fill((12, 21, 31, 240))
        surface.blit(shade, panel)
        pygame.draw.rect(surface, profile["color"], panel, 2, border_radius=8)
        portrait_box = pygame.Rect(panel.x + 12, panel.y + 17, 88, 98)
        pygame.draw.rect(surface, (21, 36, 49), portrait_box, border_radius=5)
        surface.blit(self._portrait(entry["speaker"], entry.get("expression", "normal")), (portrait_box.x + 3, portrait_box.y + 1))
        name = self.name_font.render(profile["name"].upper(), True, profile["color"])
        role = self.hint_font.render(profile["role"], True, (181, 201, 211))
        surface.blit(name, (panel.x + 118, panel.y + 15))
        surface.blit(role, (panel.x + 118, panel.y + 42))
        visible = entry["text"][:round(self.visible_characters)]
        for index, line in enumerate(self._wrapped_lines(visible, panel.width - 156)):
            text = self.text_font.render(line, True, (245, 247, 248))
            surface.blit(text, (panel.x + 118, panel.y + 65 + index * 25))
        hint = self.hint_font.render("[E] continuar" if self.visible_characters >= len(entry["text"]) else "[E] completar", True, (190, 205, 213))
        surface.blit(hint, hint.get_rect(bottomright=(panel.right - 20, panel.bottom - 13)))


class CommsSystem:
    """Mensagem contextual não bloqueante, com cooldown para evitar spam."""

    def __init__(self, cooldown_ms=8_000):
        self.cooldown_ms = cooldown_ms
        self.text = ""
        self.speaker = ""
        self.until = 0
        self.last_shown_at = -cooldown_ms
        self.font = get_font(17, "body")
        self.name_font = get_font(15, "ui", bold=True)

    def show(self, speaker, text, duration_ms=3_000, force=False):
        now = pygame.time.get_ticks()
        if not force and now - self.last_shown_at < self.cooldown_ms:
            return False
        self.speaker, self.text = speaker.lower(), text
        self.until = now + duration_ms
        self.last_shown_at = now
        return True

    def draw(self, surface):
        if pygame.time.get_ticks() >= self.until:
            return
        profile = CHARACTERS.get(self.speaker, CHARACTERS["conferente"])
        panel = pygame.Rect(SCREEN_WIDTH - 330, GAME_VIEW_HEIGHT - 94, 300, 78)
        pygame.draw.rect(surface, (11, 25, 37), panel, border_radius=6)
        pygame.draw.rect(surface, profile["color"], panel, 2, border_radius=6)
        portrait = DialogueSystem._portrait(self.speaker, "normal", (42, 50))
        surface.blit(portrait, (panel.x + 10, panel.y + 20))
        name = self.name_font.render(profile["name"].upper(), True, profile["color"])
        surface.blit(name, (panel.x + 62, panel.y + 10))
        text_x = panel.x + 62
        text_right = panel.right - 12
        lines = wrap_text(self.text, self.font, text_right - text_x, max_lines=2)
        for index, line in enumerate(lines[:2]):
            label = self.font.render(line, True, (235, 241, 244))
            surface.blit(label, (text_x, panel.y + 33 + index * 20))
