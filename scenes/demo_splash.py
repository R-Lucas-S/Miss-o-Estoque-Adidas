import pygame

from missao_estoque.settings import SCREEN_HEIGHT, SCREEN_WIDTH
from systems.ui_theme import get_font


class DemoSplash:
    """Aviso curto exibido somente na primeira abertura da demo."""

    def __init__(self, progress):
        self.progress = progress
        self.title_font = get_font(54, "display")
        self.heading_font = get_font(31, "ui", bold=True)
        self.body_font = get_font(25, "body")

    def enter(self):
        pass

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
            self.progress.data["demo_welcome_seen"] = True
            self.progress._save()
            return "menu"
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.progress.data["demo_welcome_seen"] = True
            self.progress._save()
            return "menu"

    def update(self, keys):
        pass

    def draw(self, surface):
        surface.fill((7, 17, 27))
        panel = pygame.Rect(180, 120, 920, 480)
        pygame.draw.rect(surface, (12, 29, 43), panel, border_radius=10)
        pygame.draw.rect(surface, (255, 193, 64), panel, 3, border_radius=10)
        texts = (
            (self.title_font, "MISSÃO: ESTOQUE PERFEITO", (255, 255, 255), 205),
            (self.heading_font, "DEMO / PLAYTEST", (255, 193, 64), 290),
            (self.body_font, "Esta é uma versão de teste do projeto.", (220, 229, 235), 365),
            (self.body_font, "Seu feedback ajuda a melhorar o jogo.", (220, 229, 235), 405),
            (self.heading_font, "[ENTER] CONTINUAR", (76, 214, 139), 520),
        )
        for font, value, color, y in texts:
            label = font.render(value, True, color)
            surface.blit(label, label.get_rect(center=(SCREEN_WIDTH // 2, y)))
