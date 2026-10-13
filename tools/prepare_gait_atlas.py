"""Remove o fundo claro conectado às bordas de um atlas gerado.

Uso: python tools/prepare_gait_atlas.py origem.png destino.png
"""

from collections import deque
from pathlib import Path
import sys

from PIL import Image


def is_background(pixel):
    red, green, blue, _ = pixel
    return min(red, green, blue) >= 220 and max(red, green, blue) - min(red, green, blue) <= 24


def remove_connected_background(image):
    image = image.convert("RGBA")
    pixels = image.load()
    width, height = image.size
    queue = deque()
    seen = bytearray(width * height)

    for x in range(width):
        queue.append((x, 0))
        queue.append((x, height - 1))
    for y in range(height):
        queue.append((0, y))
        queue.append((width - 1, y))

    while queue:
        x, y = queue.popleft()
        index = y * width + x
        if seen[index] or not is_background(pixels[x, y]):
            continue
        seen[index] = 1
        red, green, blue, _ = pixels[x, y]
        pixels[x, y] = (red, green, blue, 0)
        if x:
            queue.append((x - 1, y))
        if x + 1 < width:
            queue.append((x + 1, y))
        if y:
            queue.append((x, y - 1))
        if y + 1 < height:
            queue.append((x, y + 1))
    return image


def main():
    source, destination = map(Path, sys.argv[1:3])
    destination.parent.mkdir(parents=True, exist_ok=True)
    remove_connected_background(Image.open(source)).save(destination)


if __name__ == "__main__":
    main()
