from pathlib import Path
import math

import pygame

from systems.ui_theme import get_font

from missao_estoque.settings import GAME_VERSION, SCREEN_HEIGHT, SCREEN_WIDTH
from systems.audio_manager import get_audio_manager


class Menu:
    """Menu tematico, navegavel por teclado ou mouse."""

    OPTIONS = ("JOGAR", "COMO JOGAR", "OPÇÕES", "FEEDBACK", "CRÉDITOS", "SAIR")
    AUDIO_ROWS = ("master", "music", "sfx", "music_toggle", "sfx_toggle", "hints_toggle", "fullscreen_toggle", "mute")

    def __init__(self, progress, audio=None, display=None):
        self.progress = progress
        self.audio = audio or get_audio_manager()
        self.display = display
        self.title_font = get_font(58, "display")
        self.subtitle_font = get_font(28, "body")
        self.button_font = get_font(28, "ui", bold=True)
        self.small_font = get_font(19, "body")
        path = Path(__file__).resolve().parents[1] / "missao_estoque" / "assets" / "environment" / "walls" / "level1_background.png"
        background = pygame.image.load(str(path)).convert()
        self.background = pygame.transform.scale(background, (SCREEN_WIDTH + 80, SCREEN_HEIGHT))
        self.dim_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.dim_overlay.fill((4, 10, 18, 142))
        self.light_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for x in (260, 640, 1020):
            pygame.draw.polygon(self.light_overlay, (255, 230, 145, 255), ((x - 120, 112), (x + 120, 112), (x + 260, 560), (x - 260, 560)))
        self.selected = 0
        self.page = "main"
        self.button_rects = []
        self.reset_confirmation = False
        self.audio_selected = 0
        self.audio_control_rects = []

    def enter(self):
        self.page = "main"
        self.reset_confirmation = False
        self.audio_selected = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            rects = self.button_rects if self.page == "main" else self.audio_control_rects
            for index, rect in enumerate(rects):
                if rect.collidepoint(event.pos):
                    if self.page == "main":
                        self.selected = index
                    elif self.page == "options":
                        self.audio_selected = index
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.page == "main":
                for index, rect in enumerate(self.button_rects):
                    if rect.collidepoint(event.pos):
                        return self._activate(index)
            elif self.page == "options":
                for index, rect in enumerate(self.audio_control_rects):
                    if rect.collidepoint(event.pos):
                        self.audio_selected = index
                        direction = 0 if index >= 3 else (1 if event.pos[0] >= rect.centerx else -1)
                        self._adjust_audio(direction)
                        return None
            else:
                self.page = "main"
        if event.type != pygame.KEYDOWN:
            return None
        if self.page != "main":
            if self.reset_confirmation:
                if event.key in (pygame.K_y, pygame.K_RETURN):
                    self.progress.reset()
                    self.reset_confirmation = False
                    self.page = "main"
                elif event.key in (pygame.K_n, pygame.K_ESCAPE):
                    self.reset_confirmation = False
                return None
            if self.page == "how_to_play" and event.key == pygame.K_t:
                return "tutorial"
            if self.page == "options" and event.key == pygame.K_r:
                self.reset_confirmation = True
                return None
            if self.page == "options":
                if event.key in (pygame.K_UP, pygame.K_w):
                    self.audio_selected = (self.audio_selected - 1) % len(self.AUDIO_ROWS)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.audio_selected = (self.audio_selected + 1) % len(self.AUDIO_ROWS)
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    self._adjust_audio(-1)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self._adjust_audio(1)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._adjust_audio(0)
                elif event.key == pygame.K_m:
                    self.audio.toggle_muted()
                elif event.key == pygame.K_ESCAPE:
                    self.page = "main"
                return None
            if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                self.page = "main"
            return None
        if event.key in (pygame.K_UP, pygame.K_w):
            self.selected = (self.selected - 1) % len(self.OPTIONS)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.selected = (self.selected + 1) % len(self.OPTIONS)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            return self._activate(self.selected)
        elif event.key == pygame.K_ESCAPE:
            return "quit"
        return None

    def _adjust_audio(self, direction):
        row = self.AUDIO_ROWS[self.audio_selected]
        if row in ("master", "music", "sfx"):
            current = getattr(self.audio, f"{row}_volume")
            self.audio.set_volume(row, round(current + direction * 0.05, 2))
        elif row == "music_toggle":
            self.audio.set_enabled("music", not self.audio.music_enabled)
        elif row == "sfx_toggle":
            self.audio.set_enabled("sfx", not self.audio.sfx_enabled)
        elif row == "hints_toggle":
            self.progress.set_hints_enabled(not self.progress.hints_enabled)
        elif row == "fullscreen_toggle":
            if self.display is not None:
                self.display.toggle_fullscreen()
            else:
                self.progress.set_fullscreen_enabled(not self.progress.fullscreen_enabled)
        else:
            self.audio.toggle_muted()

    def _activate(self, index):
        option = self.OPTIONS[index]
        if option == "JOGAR":
            return "character_select"
        if option == "SAIR":
            return "quit"
        self.page = {
            "COMO JOGAR": "how_to_play",
            "OPÇÕES": "options",
            "FEEDBACK": "feedback",
            "CRÉDITOS": "credits",
        }[option]
        return None

    def update(self, keys):
        pass

    def draw(self, surface):
        shift = round(math.sin(pygame.time.get_ticks() / 6000) * 24)
        surface.blit(self.background, (shift - 40, 0))
        surface.blit(self.dim_overlay, (0, 0))
        self._draw_lights(surface)
        if self.page == "main":
            self._draw_main(surface)
        else:
            self._draw_page(surface)
        version = self.small_font.render(GAME_VERSION, True, (165, 175, 184))
        surface.blit(version, (20, SCREEN_HEIGHT - 32))

    def _draw_lights(self, surface):
        pulse = 25 + round((math.sin(pygame.time.get_ticks() / 900) + 1) * 8)
        self.light_overlay.set_alpha(pulse)
        surface.blit(self.light_overlay, (0, 0))

    def _draw_main(self, surface):
        title_y = 80 + round(math.sin(pygame.time.get_ticks() / 800) * 3)
        title = self.title_font.render("MISSÃO:", True, (255, 255, 255))
        name = self.title_font.render("ESTOQUE PERFEITO", True, (255, 219, 92))
        subtitle = self.subtitle_font.render("Treinamento de organização em estoque", True, (210, 218, 224))
        surface.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, title_y)))
        surface.blit(name, name.get_rect(center=(SCREEN_WIDTH // 2, title_y + 62)))
        surface.blit(subtitle, subtitle.get_rect(center=(SCREEN_WIDTH // 2, title_y + 108)))

        self.button_rects = []
        for index, option in enumerate(self.OPTIONS):
            rect = pygame.Rect(SCREEN_WIDTH // 2 - 170, 225 + index * 55, 340, 44)
            self.button_rects.append(rect)
            active = index == self.selected
            fill = (33, 43, 54, 235) if not active else (224, 174, 42, 245)
            border = (135, 151, 163) if not active else (255, 241, 174)
            pygame.draw.rect(surface, fill, rect, border_radius=4)
            pygame.draw.rect(surface, border, rect, 2, border_radius=4)
            label_color = (235, 240, 242) if not active else (20, 25, 30)
            label = self.button_font.render(option, True, label_color)
            surface.blit(label, label.get_rect(center=rect.center))
        tip = self.small_font.render("Setas/WASD + ENTER ou mouse", True, (200, 207, 211))
        surface.blit(tip, tip.get_rect(center=(SCREEN_WIDTH // 2, 580)))

    def _draw_page(self, surface):
        panel = pygame.Rect(190, 115, 900, 500)
        pygame.draw.rect(surface, (15, 23, 32, 238), panel, border_radius=7)
        pygame.draw.rect(surface, (224, 174, 42), panel, 2, border_radius=7)
        headings = {"how_to_play": "COMO JOGAR", "options": "OPÇÕES", "feedback": "FEEDBACK DO PLAYTEST", "credits": "CRÉDITOS"}
        heading = self.title_font.render(headings[self.page], True, (255, 219, 92))
        surface.blit(heading, heading.get_rect(center=(SCREEN_WIDTH // 2, 170)))
        if self.page == "how_to_play":
            lines = ("A / SETA ESQUERDA  - mover para a esquerda", "D / SETA DIREITA   - mover para a direita", "espaço             - pular", "E                  - pegar ou armazenar caixas", "", "Leia a etiqueta. Encontre a prateleira. Organize corretamente.", "", "[T] REPETIR TUTORIAL")
        elif self.page == "options":
            self._draw_audio_options(surface)
            lines = ()
        elif self.page == "feedback":
            lines = (
                "Os controles e objetivos ficaram claros?",
                "Qual fase foi mais divertida ou confusa?",
                "Você encontrou algum bug? O que estava fazendo?",
                "Como estavam animações e áudio?",
                "De 0 a 10, quanto gostou do jogo?",
                "Envie também um print e a versão exibida no menu.",
            )
        else:
            lines = (
                "MISSÃO: ESTOQUE PERFEITO",
                "Ideia original: projeto criado em parceria com Nathan.",
                "Desenvolvimento e design: em produção.",
                "Arte e tecnologia: assets do projeto.",
            )
        for index, text in enumerate(lines):
            label = self.subtitle_font.render(text, True, (230, 234, 236))
            surface.blit(label, (245, 225 + index * 40))
        back = self.small_font.render("ENTER, ESC ou clique para voltar", True, (255, 219, 92))
        surface.blit(back, back.get_rect(center=(SCREEN_WIDTH // 2, 570)))
        if self.reset_confirmation:
            confirm = pygame.Rect(365, 420, 550, 115)
            pygame.draw.rect(surface, (12, 20, 29), confirm, border_radius=6)
            pygame.draw.rect(surface, (235, 105, 95), confirm, 2, border_radius=6)
            question = self.subtitle_font.render("Apagar o progresso desta demonstração?", True, (255, 255, 255))
            options = self.small_font.render("[ENTER/Y] SIM     [ESC/N] NÃO", True, (255, 220, 90))
            surface.blit(question, question.get_rect(center=(SCREEN_WIDTH // 2, 455)))
            surface.blit(options, options.get_rect(center=(SCREEN_WIDTH // 2, 495)))

    def _draw_audio_options(self, surface):
        labels = ("VOLUME GERAL", "MÚSICA", "EFEITOS", "MÚSICA ATIVA", "EFEITOS ATIVOS", "DICAS", "TELA CHEIA", "SILENCIAR TUDO")
        values = (
            self.audio.master_volume, self.audio.music_volume, self.audio.sfx_volume,
            self.audio.music_enabled, self.audio.sfx_enabled, self.progress.hints_enabled,
            self.display.fullscreen if self.display is not None else self.progress.fullscreen_enabled,
            self.audio.muted,
        )
        self.audio_control_rects = []
        for index, (label_text, value) in enumerate(zip(labels, values)):
            row = pygame.Rect(310, 205 + index * 43, 660, 35)
            self.audio_control_rects.append(row)
            active = index == self.audio_selected
            pygame.draw.rect(surface, (29, 42, 54) if active else (18, 29, 40), row, border_radius=4)
            pygame.draw.rect(surface, (255, 193, 64) if active else (67, 92, 109), row, 2, border_radius=4)
            label = self.small_font.render(label_text, True, (236, 241, 244))
            surface.blit(label, (row.x + 14, row.centery - label.get_height() // 2))
            if index < 3:
                bar = pygame.Rect(row.x + 330, row.y + 10, 230, 18)
                pygame.draw.rect(surface, (8, 17, 25), bar)
                fill = bar.copy()
                fill.width = round(bar.width * value)
                pygame.draw.rect(surface, (255, 193, 64), fill)
                value_label = f"{round(value * 100):d}%"
                value_color = (245, 247, 248)
            else:
                enabled = (not value) if self.AUDIO_ROWS[index] == "mute" else value
                value_label = "SIM" if enabled else "NÃO"
                value_color = (67, 207, 126) if enabled else (235, 105, 95)
            text = self.small_font.render(value_label, True, value_color)
            surface.blit(text, text.get_rect(midright=(row.right - 14, row.centery)))
        help_text = self.small_font.render("Setas/WASD: ajustar   ENTER: alternar   M: silenciar   R: resetar", True, (190, 204, 213))
        surface.blit(help_text, help_text.get_rect(center=(SCREEN_WIDTH // 2, 558)))
