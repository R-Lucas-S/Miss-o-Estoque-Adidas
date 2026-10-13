import pygame

from systems.ui_theme import get_font

from data.narrative import CUTSCENES
from systems.dialogue_system import DialogueSystem


class CutsceneSystem:
    """Cutscene curta: foco de camera, dialogo, titulo e retorno de controle."""

    def __init__(self):
        self.dialogue = DialogueSystem()
        self.active = False
        self.focus_x = 0
        self.title = ""
        self.subtitle = ""
        self.title_until = 0
        self.started_at = 0
        self.title_font = get_font(37, "display")
        self.subtitle_font = get_font(21, "body")

    def start(self, key):
        data = CUTSCENES[key]
        self.focus_x = data["focus_x"]
        self.title = data["title"]
        self.subtitle = data["subtitle"]
        self.title_until = 0
        self.started_at = pygame.time.get_ticks()
        self.active = True
        self.dialogue.start(data["lines"])

    def handle_event(self, event):
        if not self.active or event.type != pygame.KEYDOWN:
            return False
        if event.key == pygame.K_ESCAPE:
            self.finish()
            return True
        if event.key in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE):
            self.dialogue.advance()
            return True
        return True

    def update(self, camera):
        if not self.active:
            return
        camera.focus_world_x(self.focus_x)
        self.dialogue.update()
        if not self.dialogue.active and not self.title_until:
            self.title_until = pygame.time.get_ticks() + 1_300
        if self.title_until and pygame.time.get_ticks() >= self.title_until:
            self.finish()

    def finish(self):
        self.dialogue.active = False
        self.active = False
        self.title_until = 0

    def draw(self, surface):
        if not self.active:
            return
        # Letterbox discreto comunica a cena sem ocultar o ambiente.
        pygame.draw.rect(surface, (4, 8, 13), (0, 0, surface.get_width(), 34))
        pygame.draw.rect(surface, (4, 8, 13), (0, surface.get_height() - 34, surface.get_width(), 34))
        if self.dialogue.active:
            self.dialogue.draw(surface)
        else:
            title = self.title_font.render(self.title, True, (255, 220, 90))
            subtitle = self.subtitle_font.render(self.subtitle, True, (235, 241, 245))
            center_x = surface.get_width() // 2
            surface.blit(title, title.get_rect(center=(center_x, 118)))
            surface.blit(subtitle, subtitle.get_rect(center=(center_x, 155)))
        # Fade-in curto: apenas estabelece a transicao, sem alongar a cena.
        elapsed = pygame.time.get_ticks() - self.started_at
        if elapsed < 220:
            fade = pygame.Surface(surface.get_size())
            fade.fill((0, 0, 0))
            fade.set_alpha(round(180 * (1 - elapsed / 220)))
            surface.blit(fade, (0, 0))
