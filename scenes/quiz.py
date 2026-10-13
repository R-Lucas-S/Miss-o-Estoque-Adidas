import random

import pygame

from data.questions import QUESTIONS_BY_LEVEL
from missao_estoque.settings import BACKGROUND_COLOR, SCREEN_HEIGHT, SCREEN_WIDTH
from systems.text_layout import wrap_text
from systems.ui_theme import get_font


class Quiz:
    """Quiz contextual com perguntas e alternativas embaralhadas."""

    recent_ids = []

    def __init__(self, quiz_level="level1", question_count=3, completion_scene="level2"):
        self.title_font = get_font(40, "display")
        self.question_font = get_font(25, "ui", bold=True)
        self.option_font = get_font(20, "body")
        self.quiz_level = quiz_level
        self.question_count = question_count
        self.completion_scene = completion_scene
        self.option_rects = []
        self.reset()

    def reset(self):
        available = list(QUESTIONS_BY_LEVEL.get(self.quiz_level, ()))
        fresh = [question for question in available if question["id"] not in self.recent_ids]
        pool = fresh if len(fresh) >= min(self.question_count, len(available)) else available
        selected = random.sample(pool, min(self.question_count, len(pool)))
        self.questions = [self._shuffle_question(question) for question in selected]
        self.recent_ids.extend(question["id"] for question in selected)
        self.recent_ids[:] = self.recent_ids[-12:]
        self.current_index = 0
        self.score = 0
        self.checked = False
        self.correct = False
        self.selected = 0

    @staticmethod
    def _shuffle_question(question):
        result = dict(question)
        options = list(question["options"])
        random.shuffle(options)
        result["options"] = tuple(options)
        result["answer"] = options.index(question["correct"])
        return result

    def enter(self):
        self.reset()

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION and not self.checked:
            for index, rect in enumerate(self.option_rects):
                if rect.collidepoint(event.pos):
                    self.selected = index
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.checked:
                return self._advance()
            for index, rect in enumerate(self.option_rects):
                if rect.collidepoint(event.pos):
                    self.selected = index
                    self._check_answer(index)
                    return None
        if event.type != pygame.KEYDOWN:
            return None
        if event.key == pygame.K_ESCAPE:
            return "menu"
        if self.current_index == len(self.questions):
            return self._advance() if event.key in (pygame.K_RETURN, pygame.K_SPACE) else None
        if self.checked:
            return self._advance() if event.key in (pygame.K_RETURN, pygame.K_SPACE) else None
        if event.key in (pygame.K_UP, pygame.K_w):
            self.selected = (self.selected - 1) % len(self.questions[self.current_index]["options"])
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.selected = (self.selected + 1) % len(self.questions[self.current_index]["options"])
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self._check_answer(self.selected)
        else:
            choices = (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_a, pygame.K_b, pygame.K_c, pygame.K_d)
            if event.key in choices:
                self.selected = choices.index(event.key) % 4
                self._check_answer(self.selected)
        return None

    def _check_answer(self, selected):
        question = self.questions[self.current_index]
        if selected >= len(question["options"]):
            return
        self.correct = selected == question["answer"]
        self.score += int(self.correct)
        self.checked = True

    def _advance(self):
        if self.current_index == len(self.questions):
            return self.completion_scene or "quiz_complete"
        self.current_index += 1
        self.checked = False
        self.selected = 0
        return None

    def update(self, keys):
        return None

    def draw(self, surface):
        surface.fill(BACKGROUND_COLOR)
        title = self.title_font.render("QUIZ DO ESTOQUE", True, (255, 220, 90))
        surface.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 65)))
        if self.current_index == len(self.questions):
            self.draw_result(surface)
            return
        question = self.questions[self.current_index]
        progress = self.option_font.render("PERGUNTA %d / %d" % (self.current_index + 1, len(self.questions)), True, (166, 190, 203))
        surface.blit(progress, progress.get_rect(center=(SCREEN_WIDTH // 2, 116)))
        question_lines = wrap_text(question["question"], self.question_font, SCREEN_WIDTH - 190, max_lines=3)
        for line_index, line in enumerate(question_lines):
            prompt = self.question_font.render(line, True, (245, 247, 248))
            surface.blit(prompt, prompt.get_rect(center=(SCREEN_WIDTH // 2, 158 + line_index * 31)))
        option_y = 250
        self.option_rects = []
        letters = "ABCD"
        for index, option in enumerate(question["options"]):
            lines = wrap_text("[%s] %s" % (letters[index], option), self.option_font, 850, max_lines=2)
            card = pygame.Rect(165, option_y, 950, max(52, 16 + len(lines) * 25))
            self.option_rects.append(card)
            active = index == self.selected
            border = (255, 193, 64) if active else (73, 99, 116)
            if self.checked and index == question["answer"]:
                border = (80, 230, 145)
            elif self.checked and active and not self.correct:
                border = (235, 105, 95)
            pygame.draw.rect(surface, (28, 39, 50), card, border_radius=5)
            pygame.draw.rect(surface, border, card, 3 if active or self.checked else 1, border_radius=5)
            for line_index, line in enumerate(lines):
                text = self.option_font.render(line, True, (235, 239, 242))
                surface.blit(text, (card.x + 22, card.y + 10 + line_index * 25))
            option_y = card.bottom + 8
        if self.checked:
            message = "RESPOSTA CORRETA!" if self.correct else "A RESPOSTA CORRETA ESTÁ DESTACADA."
            color = (80, 230, 145) if self.correct else (235, 105, 95)
            feedback = self.question_font.render(message, True, color)
            surface.blit(feedback, feedback.get_rect(center=(SCREEN_WIDTH // 2, 542)))
            for line_index, line in enumerate(wrap_text(question["explanation"], self.option_font, SCREEN_WIDTH - 220, max_lines=2)):
                explanation = self.option_font.render(line, True, (220, 226, 230))
                surface.blit(explanation, explanation.get_rect(center=(SCREEN_WIDTH // 2, 578 + line_index * 25)))
            instruction = "ENTER ou clique para continuar"
        else:
            instruction = "A-D / 1-4 para responder | setas para selecionar"
        label = self.option_font.render(instruction, True, (255, 218, 110))
        surface.blit(label, label.get_rect(center=(SCREEN_WIDTH // 2, 662)))

    def draw_result(self, surface):
        finish = self.title_font.render("QUIZ CONCLUÍDO!", True, (80, 230, 145))
        message = self.question_font.render("Você acertou %d de %d perguntas." % (self.score, len(self.questions)), True, (255, 255, 255))
        back = self.option_font.render("Pressione ENTER para continuar", True, (255, 218, 110))
        surface.blit(finish, finish.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60)))
        surface.blit(message, message.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 5)))
        surface.blit(back, back.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70)))
