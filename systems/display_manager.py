"""Apresenta o canvas 1280x720 em janela ou tela cheia sem deformar."""

import pygame

from missao_estoque.settings import SCREEN_HEIGHT, SCREEN_WIDTH, WINDOW_TITLE


class DisplayManager:
    LOGICAL_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)

    def __init__(self, progress):
        self.progress = progress
        self.fullscreen = bool(progress.fullscreen_enabled)
        self.canvas = pygame.Surface(self.LOGICAL_SIZE)
        self.window = None
        self.viewport = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        self._apply_mode()
        pygame.display.set_caption(WINDOW_TITLE)

    def _apply_mode(self):
        if self.fullscreen:
            self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.DOUBLEBUF)
        else:
            self.window = pygame.display.set_mode(self.LOGICAL_SIZE, pygame.DOUBLEBUF)
        self._update_viewport()

    def _update_viewport(self):
        width, height = self.window.get_size()
        scale = min(width / SCREEN_WIDTH, height / SCREEN_HEIGHT)
        view_width = max(1, round(SCREEN_WIDTH * scale))
        view_height = max(1, round(SCREEN_HEIGHT * scale))
        self.viewport = pygame.Rect(
            (width - view_width) // 2,
            (height - view_height) // 2,
            view_width,
            view_height,
        )

    def set_fullscreen(self, enabled, persist=True):
        enabled = bool(enabled)
        if enabled != self.fullscreen:
            self.fullscreen = enabled
            self._apply_mode()
        if persist:
            self.progress.set_fullscreen_enabled(enabled)

    def toggle_fullscreen(self):
        self.set_fullscreen(not self.fullscreen)

    def present(self):
        self.window.fill((0, 0, 0))
        if self.viewport.size == self.LOGICAL_SIZE:
            frame = self.canvas
        else:
            frame = pygame.transform.scale(self.canvas, self.viewport.size)
        self.window.blit(frame, self.viewport)
        pygame.display.flip()

    def logical_position(self, position):
        x, y = position
        x = (x - self.viewport.x) * SCREEN_WIDTH / self.viewport.width
        y = (y - self.viewport.y) * SCREEN_HEIGHT / self.viewport.height
        return round(x), round(y)

    def translate_event(self, event):
        if event.type not in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            return event
        attributes = dict(event.dict)
        if "pos" in attributes:
            attributes["pos"] = self.logical_position(attributes["pos"])
        if event.type == pygame.MOUSEMOTION and "rel" in attributes:
            attributes["rel"] = (
                round(attributes["rel"][0] * SCREEN_WIDTH / self.viewport.width),
                round(attributes["rel"][1] * SCREEN_HEIGHT / self.viewport.height),
            )
        return pygame.event.Event(event.type, attributes)
