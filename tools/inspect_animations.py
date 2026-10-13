"""Inspetor manual: câmera lenta, avanço quadro a quadro e onion skin."""

import pygame

from data.playable_characters import CHARACTER_IDS, character_definition
from systems.animation import AnimationPlayer


ANIMATIONS = ("idle", "walk", "run", "jump", "fall", "land", "carry_idle", "carry_walk", "special_cross", "special_tap", "special_adjust")


def main():
    pygame.init()
    screen = pygame.display.set_mode((900, 520))
    pygame.display.set_caption("Inspetor de animações")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 28)
    character_index = animation_index = 0
    player = AnimationPlayer((162, 220), CHARACTER_IDS[character_index])
    paused = True
    onion_skin = True
    previous = None
    direction = "right"
    slow = True
    running = True
    while running:
        dt = clock.tick(60) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key in (pygame.K_RIGHT, pygame.K_PERIOD):
                    previous = player.image(direction).copy()
                    player.step_frame(1)
                elif event.key in (pygame.K_LEFT, pygame.K_COMMA):
                    previous = player.image(direction).copy()
                    player.step_frame(-1)
                elif event.key == pygame.K_UP:
                    animation_index = (animation_index - 1) % len(ANIMATIONS)
                    player.set(ANIMATIONS[animation_index])
                elif event.key == pygame.K_DOWN:
                    animation_index = (animation_index + 1) % len(ANIMATIONS)
                    player.set(ANIMATIONS[animation_index])
                elif event.key == pygame.K_TAB:
                    character_index = (character_index + 1) % len(CHARACTER_IDS)
                    player = AnimationPlayer((162, 220), CHARACTER_IDS[character_index])
                    player.set(ANIMATIONS[animation_index])
                    previous = None
                elif event.key == pygame.K_o:
                    onion_skin = not onion_skin
                elif event.key == pygame.K_f:
                    direction = "left" if direction == "right" else "right"
                    previous = None
                elif event.key == pygame.K_s:
                    slow = not slow
        if not paused:
            previous = player.image(direction).copy()
            player.update(.25 if slow else 1.0, dt)
        screen.fill((7, 18, 28))
        ground_y = 390
        pygame.draw.line(screen, (70, 112, 132), (80, ground_y), (820, ground_y), 2)
        if onion_skin and previous:
            ghost = previous.copy()
            ghost.set_alpha(55)
            screen.blit(ghost, ghost.get_rect(midbottom=(450, ground_y)))
        frame = player.image(direction)
        screen.blit(frame, frame.get_rect(midbottom=(450, ground_y)))
        definition = character_definition(CHARACTER_IDS[character_index])
        info = "%s | %s | frame %d/%d" % (
            definition["name"], player.name.upper(), player.frame_index + 1,
            len(player.frames[player.name]["right"]),
        )
        screen.blit(font.render(info, True, definition["accent"]), (25, 22))
        controls = "TAB personagem | cima/baixo estado | espaço play | setas frame | O onion | F flip | S 25% | ESC"
        screen.blit(font.render(controls, True, (220, 229, 234)), (25, 480))
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
