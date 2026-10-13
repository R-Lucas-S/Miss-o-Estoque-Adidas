import os
import ast
import re
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from systems.text_layout import wrap_text
from systems.ui_theme import get_font


class TextLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))
        cls.font = pygame.font.Font(None, 24)

    def test_every_wrapped_line_respects_available_width(self):
        lines = wrap_text(
            "Boa leitura da etiqueta. Continue nesse ritmo.",
            self.font,
            190,
        )
        self.assertGreater(len(lines), 1)
        self.assertTrue(all(self.font.size(line)[0] <= 190 for line in lines))

    def test_long_unbroken_token_is_not_split_mid_word(self):
        lines = wrap_text("ACESSORIOSMUITOGRANDE", self.font, 80)
        self.assertEqual(lines, ["ACESSORIOSMUITOGRANDE"])

    def test_ui_fonts_support_brazilian_portuguese_glyphs(self):
        characters = "áàâãéêíóôõúçÁÃÇÊÓ"
        for role in ("body", "ui", "display"):
            font = get_font(22, role)
            self.assertTrue(all(font.metrics(character)[0] is not None for character in characters), role)

    def test_visible_strings_do_not_restore_common_unaccented_terms(self):
        forbidden = re.compile(
            r"\b(missao|missoes|selecao|conferencia|organizacao|reposicao|"
            r"precisao|pontuacao|opcoes|creditos|acessorios|tenis|"
            r"divergencias|referencia|referencias|secao|interacao)\b",
            re.IGNORECASE,
        )
        root = Path(__file__).resolve().parents[1]
        for folder in ("scenes", "systems", "data", "entities"):
            for path in (root / folder).glob("*.py"):
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Constant) and isinstance(node.value, str):
                        # Identificadores internos, tags e segmentos de caminho
                        # não são texto visível ao jogador.
                        if node.value.islower() and " " not in node.value:
                            continue
                        self.assertIsNone(forbidden.search(node.value), (path.name, node.lineno, node.value))


if __name__ == "__main__":
    unittest.main()
