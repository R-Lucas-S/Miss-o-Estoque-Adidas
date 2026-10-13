import random

import pygame

from missao_estoque.settings import GRAVITY, MAX_FALL_SPEED, PLAYER_HEIGHT, PLAYER_JUMP_FORCE, PLAYER_SPEED, PLAYER_SPRITE_HEIGHT, PLAYER_SPRITE_WIDTH, PLAYER_START_X, PLAYER_START_Y, PLAYER_WIDTH, SHOW_ANIMATION_DEBUG
from data.playable_characters import character_definition
from systems.animation import AnimationPlayer
from systems.audio_manager import get_audio_manager
from systems import frame_time


class Player:
    """Personagem com hitbox fixa e animacoes reais do sprite sheet."""

    MOVEMENT_EPSILON = 0.1
    FOOTSTEP_COOLDOWN_MS = 120
    WALK_CYCLE_DISTANCE = 140
    CARRY_CYCLE_DISTANCE = 150
    animation_debug = SHOW_ANIMATION_DEBUG
    animation_slow = False
    _debug_font = None

    STATE_ANIMATIONS = {"idle": "idle", "walk": "walk", "run": "run", "jump": "jump", "fall": "fall", "land": "land", "carry_idle": "carry_idle", "carry_walk": "carry_walk", "carry_jump": "carry_jump", "carry_fall": "carry_fall", "carry_land": "carry_land"}

    def __init__(self, character_id="player_default"):
        self.rect = pygame.Rect(PLAYER_START_X, PLAYER_START_Y, PLAYER_WIDTH, PLAYER_HEIGHT)
        self._position = pygame.Vector2(self.rect.topleft)
        self._last_rect_position = self.rect.topleft
        self.dt_seconds = 1 / 60
        self.velocity_y = 0.0
        self.on_ground = False
        self.was_on_ground = False
        self.move_direction = 0
        self.is_moving = False
        self.actual_delta_x = 0.0
        self.facing_direction = "right"
        self.state = "idle"
        self.idle_started_at = pygame.time.get_ticks()
        self.next_special_at = self.idle_started_at + random.randint(5_000, 12_000)
        self.special_name = None
        self.last_special_name = None
        self.special_started_at = None
        self.character_id = character_id
        self.character_data = character_definition(character_id)
        self.carry_offsets = self.character_data.get("carry_offsets", {})
        self.carrying = False
        self.animation = AnimationPlayer((PLAYER_SPRITE_WIDTH, PLAYER_SPRITE_HEIGHT), character_id)
        self.audio = get_audio_manager()
        self.last_footstep_at = -self.FOOTSTEP_COOLDOWN_MS

    def handle_input(self, keys):
        move_left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        move_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        self.move_direction = int(move_right) - int(move_left)
        if self.move_direction:
            self.facing_direction = "right" if self.move_direction > 0 else "left"
        if keys[pygame.K_SPACE] and self.on_ground:
            self.velocity_y = PLAYER_JUMP_FORCE
            self.on_ground = False

    @property
    def position(self):
        return self._position.copy()

    @property
    def hitbox(self):
        return self.rect

    @property
    def feet_position(self):
        return self.rect.midbottom

    def update(self, floor, world_width, solid_rects=(), carrying=False, dt_seconds=None):
        self.dt_seconds = max(0.0, min(frame_time.seconds if dt_seconds is None else dt_seconds, .05))
        step = self.dt_seconds * 60
        if self.rect.topleft != self._last_rect_position:
            self._position.update(self.rect.topleft)
        self.carrying = carrying
        self.was_on_ground = self.on_ground
        previous_x = self._position.x
        speed_x = self.move_direction * PLAYER_SPEED * step
        self._position.x += speed_x
        self.rect.x = round(self._position.x)
        proposed_x = self.rect.x
        self.rect.left = max(self.rect.left, 0)
        self.rect.right = min(self.rect.right, world_width)
        for solid in solid_rects:
            if self.rect.colliderect(solid):
                if speed_x > 0:
                    self.rect.right = solid.left
                elif speed_x < 0:
                    self.rect.left = solid.right
        if self.rect.x != proposed_x:
            self._position.x = self.rect.x
        self.actual_delta_x = self._position.x - previous_x
        self.is_moving = abs(self.actual_delta_x) > self.MOVEMENT_EPSILON

        self.velocity_y = min(self.velocity_y + GRAVITY * step, MAX_FALL_SPEED)
        self._position.y += self.velocity_y * step
        self.rect.y = round(self._position.y)
        self.on_ground = False
        if self.rect.right > floor.left and self.rect.left < floor.right and self.rect.bottom >= floor.top and self.rect.top < floor.bottom and self.velocity_y >= 0:
            self.rect.bottom = floor.top
            self.velocity_y = 0
            self.on_ground = True
        for solid in solid_rects:
            if self.rect.colliderect(solid) or (self.velocity_y >= 0 and self.rect.bottom == solid.top and self.rect.right > solid.left and self.rect.left < solid.right):
                if self.velocity_y >= 0:
                    self.rect.bottom = solid.top
                    self.velocity_y = 0
                    self.on_ground = True
                else:
                    self.rect.top = solid.bottom
                    self.velocity_y = 0
        if self.velocity_y == 0:
            self._position.y = self.rect.y
        self._last_rect_position = self.rect.topleft
        self._update_state(carrying)
        self.animation.update(
            .25 if self.animation_slow else 1.0, self.dt_seconds,
            distance=self.actual_delta_x,
            cycle_distance=self.CARRY_CYCLE_DISTANCE if carrying else self.WALK_CYCLE_DISTANCE,
        )
        self._play_animation_audio()

    def _animation_speed_multiplier(self):
        """Casa o ciclo visual à distância real para impedir pés deslizando."""
        if not self.is_moving:
            return .8
        frames = len(self.animation.frames[self.animation.name]["right"])
        base_duration = self.animation.DURATIONS.get(self.animation.name, 120) * frames
        pixels_per_second = abs(self.actual_delta_x) / max(self.dt_seconds, 1e-8)
        target_distance = self.CARRY_CYCLE_DISTANCE if self.state == "carry_walk" else self.WALK_CYCLE_DISTANCE
        desired_duration = target_distance / max(1, pixels_per_second) * 1000
        return base_duration / desired_duration

    def _play_animation_audio(self):
        if not self.on_ground or not self.is_moving or self.state not in ("walk", "carry_walk"):
            self.animation.consume_events()
            return
        now = pygame.time.get_ticks()
        for event in self.animation.consume_events():
            if event == "footstep" and now - self.last_footstep_at >= self.FOOTSTEP_COOLDOWN_MS:
                self.audio.play_sound("footstep", category="player", volume=0.32)
                self.last_footstep_at = now
                break

    def _set_state(self, new_state):
        if new_state == self.state:
            return
        self.state = new_state
        if new_state == "idle_special":
            self.special_started_at = pygame.time.get_ticks()
        elif self.special_started_at is not None:
            self.special_started_at = None
        name = self.special_name if new_state == "idle_special" else self.STATE_ANIMATIONS[new_state]
        self.animation.set(name)
        if new_state not in ("idle", "idle_special"):
            self.next_special_at = pygame.time.get_ticks() + random.randint(5_000, 12_000)

    def _update_state(self, carrying):
        now = pygame.time.get_ticks()
        if not self.on_ground:
            if carrying:
                self._set_state("carry_jump" if self.velocity_y < 0 else "carry_fall")
            else:
                self._set_state("jump" if self.velocity_y < 0 else "fall")
            self.idle_started_at = now
            return
        if not self.was_on_ground:
            self._set_state("carry_land" if carrying else "land")
            self.idle_started_at = now
            return
        if self.state in ("land", "carry_land") and not self.animation.finished:
            return
        if carrying:
            self._set_state("carry_walk" if self.is_moving else "carry_idle")
            self.idle_started_at = now
            return
        if self.is_moving:
            self._set_state("walk")
            self.idle_started_at = now
            return
        if self.state == "idle_special":
            if self.move_direction:
                self._set_state("idle")
                self.idle_started_at = now
                return
            if not self.animation.finished:
                return
            self._set_state("idle")
            self.idle_started_at = now
            self.next_special_at = now + random.randint(5_000, 12_000)
            return
        if now >= self.next_special_at:
            choices = [name for name in ("special_cross", "special_tap", "special_adjust") if name != self.last_special_name]
            self.special_name = random.choice(choices or ("special_cross", "special_tap", "special_adjust"))
            self.last_special_name = self.special_name
            self._set_state("idle_special")
            return
        self._set_state("idle")

    def carry_anchor(self):
        if self.state in self.animation.carry_anchors:
            offsets = self.animation.carry_anchors[self.state]
        else:
            offsets = self.carry_offsets.get(self.state) or self.carry_offsets.get("carry_idle", ((18, -10),))
        offset_x, offset_y = offsets[self.animation.frame_index % len(offsets)]
        if self.facing_direction == "left":
            offset_x = -offset_x
        return self.rect.centerx + offset_x, self.rect.bottom + offset_y

    def draw(self, surface, camera):
        frame = self.animation.image(self.facing_direction)
        draw_rect = camera.apply_rect(self.rect)
        surface.blit(frame, frame.get_rect(midbottom=(draw_rect.centerx, draw_rect.bottom)))
        if self.animation_debug:
            self._draw_animation_debug(surface, camera, draw_rect)

    def _draw_animation_debug(self, surface, camera, draw_rect):
        if Player._debug_font is None:
            Player._debug_font = pygame.font.Font(None, 15)
        feet = (draw_rect.centerx, draw_rect.bottom)
        hand_world = self.carry_anchor()
        hand = (round(camera.apply_x(hand_world[0])), round(hand_world[1]))
        pygame.draw.circle(surface, (60, 255, 120), feet, 3)
        pygame.draw.circle(surface, (255, 90, 190), hand, 3)
        lines = (
            f"Character: {self.character_data['name']}  State: {self.state.upper()}",
            f"Frame: {self.animation.frame_index + 1}/{len(self.animation.frames[self.animation.name]['right'])}  Anchor: MIDBOTTOM",
            f"Animation FPS: {self.animation_fps():.1f}  Game FPS: {frame_time.game_fps:.1f}",
            f"Speed: {abs(self.actual_delta_x) / max(self.dt_seconds, 1e-8):.1f} px/s  Direction: {self.facing_direction.upper()}",
            f"F8 debug | F9 slow: {'25%' if self.animation_slow else '100%'}",
        )
        y = draw_rect.top - len(lines) * 15 - 4
        for line in lines:
            label = Player._debug_font.render(line, True, (245, 245, 245), (8, 18, 27))
            surface.blit(label, (draw_rect.centerx - label.get_width() // 2, y))
            y += 15

    def animation_fps(self):
        rate = 1000 / self.animation.DURATIONS.get(self.animation.name, 120)
        if self.state in ('walk', 'carry_walk'):
            distance = self.CARRY_CYCLE_DISTANCE if self.carrying else self.WALK_CYCLE_DISTANCE
            rate = abs(self.actual_delta_x) / max(self.dt_seconds, 1e-8) / distance * len(self.animation.frames[self.animation.name]['right'])
        return rate * (.25 if self.animation_slow else 1)
