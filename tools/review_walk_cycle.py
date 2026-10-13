"""Reproduz Player.update/draw e exporta evidências visuais sem modificar saves.

python -m tools.review_walk_cycle
Pillow é necessário apenas para os GIFs de revisão.
"""

import json
import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from PIL import Image

from data.playable_characters import CHARACTER_IDS, character_definition
from entities.camera import Camera
from entities.player import Player


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    output = Path("artifacts/walk_review")
    output.mkdir(parents=True, exist_ok=True)
    font = pygame.font.Font(None, 20)
    players = [Player(cid) for cid in CHARACTER_IDS]
    for player in players:
        player.rect.topleft = (500, 168)
        player.on_ground = True
    floor = pygame.Rect(0, 260, 3000, 100)
    frames, log = [], []
    captures = pygame.Surface((960, 8 * 300))
    captures.fill((18, 28, 39))
    for tick in range(240):
        time = tick / 30
        moving = .4 <= time < 3.2 or 4.3 <= time < 7.3
        direction = -1 if 2.4 <= time < 3.2 or 6.2 <= time < 7.3 else 1
        carry = 3.7 <= time < 7.3
        surface = pygame.Surface((960, 300))
        surface.fill((18, 28, 39))
        for col, player in enumerate(players):
            player.move_direction = direction if moving else 0
            if moving:
                player.facing_direction = "right" if direction > 0 else "left"
            if tick in (45, 156):
                player.velocity_y = -15
                player.on_ground = False
            player.update(floor, 3000, carrying=carry, dt_seconds=1 / 30)
            camera = Camera(3000, 320, 1)
            camera.x = player.rect.centerx - (col * 320 + 160)
            pygame.draw.line(surface, (70, 150, 110), (col * 320, 260), ((col + 1) * 320, 260))
            for world_x in range(0, 3000, 40):
                x = camera.apply_x(world_x)
                if col * 320 <= x < (col + 1) * 320 - 10:
                    pygame.draw.line(surface, (43, 56, 70), (x, 270), (x + 10, 270))
            player.draw(surface, camera)
            text = f"{character_definition(player.character_id)['name']} {player.state} {player.animation.frame_index + 1}"
            surface.blit(font.render(text, True, (240, 240, 240)), (col * 320 + 10, 12))
            surface.blit(font.render(f"t={time:.2f}s x={player.position.x:.1f} {player.facing_direction}", True, (190, 200, 210)), (col * 320 + 10, 280))
            log.append(dict(tick=tick, character=player.character_id, state=player.state, frame=player.animation.frame_index, x=player.position.x, bottom=player.rect.bottom, hitbox=list(player.rect.size)))
        frames.append(Image.frombytes("RGB", surface.get_size(), pygame.image.tobytes(surface, "RGB")))
        if tick in (20, 49, 80, 104, 120, 140, 165, 204):
            row = (20, 49, 80, 104, 120, 140, 165, 204).index(tick)
            captures.blit(surface, (0, row * 300))
    frames[0].save(output / "gameplay.gif", save_all=True, append_images=frames[1:], duration=33, loop=0)
    pygame.image.save(captures, output / "transitions.png")
    (output / "trace.json").write_text(json.dumps(log, indent=2), encoding="utf-8")
    # Cada quadro real, com baseline e pivot, em ambas as direções.
    for player in players:
        sheet = pygame.Surface((4 * 240, 4 * 270))
        sheet.fill((18, 28, 39))
        for row, (state, direction) in enumerate((("walk", "right"), ("walk", "left"), ("carry_walk", "right"), ("carry_walk", "left"))):
            for col, frame in enumerate(player.animation.frames[state][direction]):
                anchor = (col * 240 + 120, row * 270 + 235)
                pygame.draw.line(sheet, (70, 150, 110), (col * 240, anchor[1]), ((col + 1) * 240, anchor[1]))
                enlarged = pygame.transform.scale_by(frame, 2)
                sheet.blit(enlarged, enlarged.get_rect(midbottom=anchor))
                label = f"{state} {direction} {col + 1}"
                sheet.blit(font.render(label, True, (240, 240, 240)), (col * 240 + 8, row * 270 + 245))
        pygame.image.save(sheet, output / f"{player.character_id}_poses.png")
        # Loop isolado em 25% facilita ver a alternância sem mudar a física.
        gif = []
        for frame in player.animation.frames["walk"]["right"]:
            canvas = pygame.Surface((240, 260))
            canvas.fill((18, 28, 39))
            enlarged = pygame.transform.scale_by(frame, 2)
            canvas.blit(enlarged, enlarged.get_rect(midbottom=(120, 240)))
            gif.append(Image.frombytes("RGB", canvas.get_size(), pygame.image.tobytes(canvas, "RGB")))
        gif[0].save(output / f"{player.character_id}_slow.gif", save_all=True, append_images=gif[1:], duration=player.animation.DURATIONS['walk'] * 4, loop=0)
    pygame.quit()
    print(output.resolve())


if __name__ == "__main__":
    main()
