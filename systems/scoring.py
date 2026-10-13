from missao_estoque.settings import CORRECT_DELIVERY_SCORE, MAX_COMBO, WRONG_DELIVERY_PENALTY


class Scoring:
    """Pontuação e combo reutilizáveis para as fases de estoque."""

    def __init__(self):
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.errors = 0
        self.correct_deliveries = 0

    def correct_delivery(self, box):
        self.combo = min(self.combo + 1, MAX_COMBO)
        self.max_combo = max(self.max_combo, self.combo)
        self.correct_deliveries += 1
        points = box.score_value if box.mistakes == 0 else max(0, box.score_value - WRONG_DELIVERY_PENALTY)
        self.score += points
        return points

    def wrong_delivery(self):
        self.errors += 1
        self.combo = 0
        self.score = max(0, self.score - WRONG_DELIVERY_PENALTY)

    def add_points(self, points):
        """crédito pontual para objetivos que não são uma entrega de caixa."""
        self.score += max(0, points)
