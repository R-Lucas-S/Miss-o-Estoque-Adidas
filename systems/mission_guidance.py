"""Orientação visual consistente sem conhecer ou alterar regras de gameplay."""

import weakref

import pygame

from missao_estoque.settings import SCREEN_WIDTH
from systems.text_layout import wrap_text
from systems.ui_theme import get_font


_state = weakref.WeakKeyDictionary()
_title_font = None
_text_font = None
_small_font = None


MISSION_COPY = {
    "Level1": ("RECEBA E ORGANIZE AS CAIXAS", "Observe a etiqueta e use a prateleira da categoria."),
    "Level2": ("CONFIRA ANTES DE ARMAZENAR", "Categoria, referência e tamanho devem corresponder."),
    "Level3": ("ENCONTRE 3 DIVERGÊNCIAS", "Compare lista e produto; depois corrija a localização."),
    "Level4": ("SEPARE O PEDIDO ATUAL", "Confira referência e tamanho e leve ao carrinho."),
    "Level5": ("COMPLETE A REPOSIÇÃO", "Siga a lista por prioridade até a área de vendas."),
}


def _fonts():
    global _title_font, _text_font, _small_font
    if _title_font is None:
        _title_font = get_font(15, "ui", bold=True)
        _text_font = get_font(18, "body")
        _small_font = get_font(14, "body")
    return _title_font, _text_font, _small_font


def _progress(scene):
    name = type(scene).__name__
    if name in ("Level1", "Level2"):
        done = sum(box.stored for box in scene.boxes)
        return done, len(scene.boxes)
    if name == "Level3":
        return scene.corrected_divergences, scene.total_divergences
    if name == "Level4":
        return scene.order.separated_count, scene.order.total_count
    if name == "Level5":
        return sum(scene.checks.values()), len(scene.checks)
    return 0, 1


def _current_step(scene):
    carried = getattr(scene, "carried_box", None)
    if getattr(scene, "completed", False):
        return "Missão concluída. Pressione ENTER para o quiz."
    if carried:
        product = carried.product
        details = "%s | %s" % (product["reference"], product["name"])
        if product.get("size") not in (None, "-"):
            details += " | TAM. %s" % product["size"]
        if type(scene).__name__ == "Level4":
            return "CARREGANDO %s — leve ao carrinho." % details
        return "CARREGANDO %s — leve até %s." % (details, product["name"])
    if type(scene).__name__ == "Level3":
        return "Aproxime-se de uma caixa e pressione E para conferir."
    if type(scene).__name__ == "Level5":
        return getattr(scene, "message", "Consulte a lista e siga o próximo passo.")
    if type(scene).__name__ == "Level4":
        return "Consulte o pedido [TAB], aproxime-se e use [Q] para escanear."
    return "Aproxime-se de uma caixa e pressione E para pegar."


def _hint(scene, elapsed):
    carried = getattr(scene, "carried_box", None)
    if elapsed >= 20_000:
        if carried:
            return "DICA: a categoria da etiqueta indica o destino."
        return "DICA: procure o brilho nas caixas e aproxime-se."
    if elapsed >= 12_000:
        return "DICA: consulte o PASSO ATUAL acima."
    return ""


def draw_mission_guidance(surface, scene):
    if getattr(scene, "cutscene", None) and scene.cutscene.active:
        return
    name = type(scene).__name__
    if name not in MISSION_COPY:
        return
    now = pygame.time.get_ticks()
    done, total = _progress(scene)
    signature = (done, bool(getattr(scene, "carried_box", None)), getattr(scene, "message", ""))
    record = _state.setdefault(scene, {"signature": signature, "changed": now})
    if record["signature"] != signature:
        record.update(signature=signature, changed=now)
    title_font, text_font, small_font = _fonts()
    panel = pygame.Rect(SCREEN_WIDTH // 2 - 315, 16, 630, 91)
    layer = pygame.Surface(panel.size, pygame.SRCALPHA)
    pygame.draw.rect(layer, (8, 20, 30, 224), layer.get_rect(), border_radius=6)
    pygame.draw.rect(layer, (33, 150, 243, 230), layer.get_rect(), 2, border_radius=6)
    title, description = MISSION_COPY[name]
    layer.blit(title_font.render("OBJETIVO  %d / %d  |  %s" % (done, total, title), True, (255, 220, 90)), (16, 10))
    step = _current_step(scene)
    for index, line in enumerate(wrap_text("PASSO ATUAL: " + step, text_font, panel.width - 32, max_lines=2)):
        layer.blit(text_font.render(line, True, (244, 247, 248)), (16, 35 + index * 22))
    surface.blit(layer, panel)
    hints_enabled = getattr(getattr(scene, "progress", None), "hints_enabled", True)
    hint = _hint(scene, now - record["changed"]) if hints_enabled else ""
    if hint:
        label = small_font.render(hint, True, (255, 220, 90))
        plate = label.get_rect(midtop=(panel.centerx, panel.bottom + 6)).inflate(20, 8)
        pygame.draw.rect(surface, (10, 23, 34), plate, border_radius=4)
        pygame.draw.rect(surface, (255, 193, 64), plate, 1, border_radius=4)
        surface.blit(label, label.get_rect(center=plate.center))
