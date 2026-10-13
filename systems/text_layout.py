"""Utilitarios de texto para manter rotulos dentro dos paineis da UI."""


def wrap_text(text, font, max_width, max_lines=None):
    """Quebra por palavras usando a largura real, sem partir termos ao meio."""
    if max_width <= 0:
        return []
    lines = []
    for paragraph in str(text).splitlines() or [""]:
        current = ""
        for word in paragraph.split():
            candidate = word if not current else current + " " + word
            if font.size(candidate)[0] <= max_width:
                current = candidate
                continue
            if current:
                lines.append(current)
                current = ""
            current = word
        if current or not paragraph:
            lines.append(current)
    if max_lines is not None:
        return lines[:max_lines]
    return lines
