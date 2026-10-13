"""Painel inferior compartilhado pelas fases de gameplay."""

import math

import pygame

from missao_estoque.settings import (
    BOTTOM_HUD_HEIGHT,
    GAME_VIEW_HEIGHT,
    SCREEN_WIDTH,
    UI_ACCENT,
    UI_GAP,
    UI_PADDING,
    UI_PANEL_BG,
    UI_TEXT_PRIMARY,
    UI_TEXT_SECONDARY,
)
from systems.ui_theme import get_font
from systems.text_layout import wrap_text


class BottomHUD:
    """HUD adaptativo, barato e independente das regras das fases."""

    ENTER_MS = 240
    PULSE_MS = 320

    def __init__(self):
        self.started_at = pygame.time.get_ticks()
        self.label_font = get_font(14, "ui", bold=True)
        self.value_font = get_font(25, "ui", bold=True)
        self.detail_font = get_font(16, "body")
        self.feedback_font = get_font(20, "ui", bold=True)
        self.previous = {}
        self.pulses = {}
        self.point_delta = 0
        self.point_delta_at = 0

    def draw(self, surface, mission, objective, metrics, feedback=None):
        now = pygame.time.get_ticks()
        self._observe(metrics, now)
        progress = min(1.0, max(0.0, (now - self.started_at) / self.ENTER_MS))
        eased = 1 - (1 - progress) ** 3
        top = round(GAME_VIEW_HEIGHT + (1 - eased) * 18)
        alpha = round(255 * eased)
        layer = pygame.Surface((SCREEN_WIDTH, BOTTOM_HUD_HEIGHT + 18), pygame.SRCALPHA)
        self._draw_panel(layer, mission, objective, metrics, feedback, now, alpha)
        surface.blit(layer, (0, top))

    def _observe(self, metrics, now):
        for item in metrics:
            key, value = item["key"], item["value"]
            old = self.previous.get(key)
            if old is not None and old != value:
                self.pulses[key] = now
                if key == "score" and isinstance(old, int) and isinstance(value, int) and value > old:
                    self.point_delta = value - old
                    self.point_delta_at = now
            self.previous[key] = value

    def _draw_panel(self, layer, mission, objective, metrics, feedback, now, alpha):
        h = BOTTOM_HUD_HEIGHT
        bg = (*UI_PANEL_BG, min(alpha, 248))
        points = ((0, 8), (8, 0), (SCREEN_WIDTH - 8, 0), (SCREEN_WIDTH, 8), (SCREEN_WIDTH, h), (0, h))
        pygame.draw.polygon(layer, bg, points)
        pygame.draw.line(layer, (*UI_ACCENT, alpha), (0, 1), (SCREEN_WIDTH, 1), 2)
        pygame.draw.line(layer, (38, 72, 94, alpha), (0, 7), (SCREEN_WIDTH, 7), 1)

        left = UI_PADDING
        mission_width = 245
        objective_width = 285
        mission_label, mission_value = self._mission_parts(mission)
        self._block(layer, left, mission_label, mission_value, mission_width, UI_ACCENT, alpha)
        left += mission_width + UI_GAP
        self._divider(layer, left - UI_GAP // 2, alpha)
        self._block(layer, left, objective[0], objective[1], objective_width, objective[2], alpha, objective[3] if len(objective) > 3 else None)
        left += objective_width + UI_GAP
        self._divider(layer, left - UI_GAP // 2, alpha)

        metric_width = max(112, (SCREEN_WIDTH - left - UI_PADDING - UI_GAP * max(0, len(metrics) - 1)) // max(1, len(metrics)))
        for index, item in enumerate(metrics):
            self._metric(layer, left, metric_width, item, now, alpha)
            left += metric_width + UI_GAP
            if index < len(metrics) - 1:
                self._divider(layer, left - UI_GAP // 2, alpha)

        if isinstance(feedback, str):
            active_feedback = (feedback, UI_TEXT_PRIMARY) if feedback else None
        else:
            active_feedback = feedback if feedback and feedback[0] else None
        if active_feedback:
            text, color = active_feedback
            line = wrap_text(text, self.feedback_font, SCREEN_WIDTH - 80, max_lines=1)[0]
            label = self.feedback_font.render(line, True, color)
            plate = label.get_rect(center=(SCREEN_WIDTH // 2, 16))
            shade = pygame.Surface(plate.inflate(28, 10).size, pygame.SRCALPHA)
            shade.fill((UI_PANEL_BG[0], UI_PANEL_BG[1], UI_PANEL_BG[2], 235))
            layer.blit(shade, shade.get_rect(center=plate.center))
            layer.blit(label, plate)

    def _block(self, layer, x, label, value, width, color, alpha, progress=None):
        layer.blit(self.label_font.render(label, True, UI_TEXT_SECONDARY), (x, 27))
        rendered = self.value_font.render(str(value), True, color)
        layer.blit(rendered, (x, 51))
        if progress is not None:
            bar = pygame.Rect(x, 91, width - 25, 9)
            pygame.draw.rect(layer, (26, 47, 61, alpha), bar)
            fill = bar.copy()
            fill.width = round(bar.width * max(0.0, min(1.0, progress)))
            pygame.draw.rect(layer, (*color, alpha), fill)
            pygame.draw.rect(layer, (74, 111, 130, alpha), bar, 1)

    def _metric(self, layer, x, width, item, now, alpha):
        key = item["key"]
        color = item.get("color", UI_TEXT_PRIMARY)
        value = item["display"]
        pulse_age = now - self.pulses.get(key, -10_000)
        pulse = 1.0
        if 0 <= pulse_age < self.PULSE_MS:
            pulse += math.sin(pulse_age / self.PULSE_MS * math.pi) * 0.13
        layer.blit(self.label_font.render(item["label"], True, UI_TEXT_SECONDARY), (x, 27))
        base = self.value_font.render(str(value), True, color)
        if pulse != 1:
            base = pygame.transform.scale(base, (round(base.get_width() * pulse), round(base.get_height() * pulse)))
        layer.blit(base, base.get_rect(midleft=(x, 69)))
        if key == "score" and self.point_delta and now - self.point_delta_at < 1_200:
            age = now - self.point_delta_at
            delta = self.detail_font.render("+%d" % self.point_delta, True, (80, 230, 145))
            delta.set_alpha(max(0, 255 - round(age / 1_200 * 255)))
            layer.blit(delta, (x + width - delta.get_width() - 8, 49 - round(age / 60)))

    @staticmethod
    def _divider(layer, x, alpha):
        pygame.draw.line(layer, (52, 83, 101, min(alpha, 180)), (x, 25), (x, 112), 1)

    @staticmethod
    def _mission_parts(mission):
        parts = str(mission).split("  -  ", 1)
        return (parts[0], parts[1]) if len(parts) == 2 else ("MISSÃO", parts[0])


def combo_color(combo):
    if combo >= 4:
        return 244, 90, 54
    if combo == 3:
        return 255, 142, 42
    if combo == 2:
        return 255, 210, 70
    return UI_TEXT_PRIMARY
