from pathlib import Path
import random

import pygame

from missao_estoque.settings import NPC_ACTION_MAX_TIME_MS, NPC_ACTION_MIN_TIME_MS, NPC_FRAME_TIME_MS

from missao_estoque.settings import NPC_SCALE, NPC_SPRITE_HEIGHT, NPC_SPRITE_WIDTH, SHOW_ANIMATION_DEBUG


class NPC:
    """Funcionario decorativo com animacao e temporizador proprios."""

    MAX_ELAPSED_MS = 50
    _debug_font = None

    FRAME_REGIONS = {
        # Regioes do novo sprite sheet (1536 x 1024). Os personagens ficam
        # na metade esquerda; objetos decorativos, na direita, não são usados.
        "checker": [(10, 0, 105, 205), (120, 0, 215, 205), (230, 0, 325, 205), (345, 0, 440, 205), (460, 0, 555, 205)],
        "organizer": [(10, 205, 100, 440), (120, 205, 210, 440), (235, 205, 330, 440), (350, 205, 450, 440), (480, 205, 575, 440)],
        "resting": [(10, 440, 105, 700), (120, 440, 215, 700), (230, 440, 325, 700), (345, 440, 440, 700), (460, 440, 555, 700)],
    }
    STATES = {
        "checker": {"idle": [0], "checking": [1, 2], "writing": [2, 3], "looking": [3, 4]},
        "organizer": {"idle": [0], "carrying_box": [1, 2], "placing": [2, 3], "adjusting": [3, 4]},
        "resting": {"idle": [0], "cross_arms": [1], "drinking": [2], "looking_around": [1, 2, 3]},
    }
    # Os NPCs atuais são decorativos e não possuem deslocamento físico. Por
    # isso, a animacao de carregar caminhando não pode ser escolhida sozinha.
    # Ela fica reservada para um futuro ciclo com movimento real.
    IDLE_ACTIONS = {
        "checker": ("checking", "writing", "looking"),
        "organizer": ("placing", "adjusting"),
        "resting": ("cross_arms", "drinking", "looking_around"),
    }
    _sheet = None
    _frames = {}
    _feet_offsets = {}
    ACTION_DURATIONS = {"checker": (4_000, 6_000), "organizer": (4_500, 7_000), "resting": (6_000, 9_000)}

    def __init__(self, x, floor_top, npc_type, action_interval=(4_000, 7_000), layer=0, calm=False):
        self.npc_type = npc_type
        self.layer = layer
        self.rect = pygame.Rect(x, floor_top - NPC_SPRITE_HEIGHT, NPC_SPRITE_WIDTH, NPC_SPRITE_HEIGHT)
        self.frames = self._load_frames(npc_type)
        self.feet_offsets = self._feet_offsets[npc_type]
        self.calm = calm
        calm_actions = {
            "checker": ("checking", "writing", "looking"),
            "organizer": ("adjusting",),
            "resting": ("cross_arms", "looking_around"),
        }
        self.idle_actions = calm_actions[npc_type] if calm else self.IDLE_ACTIONS[npc_type]
        self.state = "idle"
        self.frame_index = 0
        self.last_frame_at = pygame.time.get_ticks()
        self.animation_elapsed_ms = 0.0
        self.actual_dx = 0.0
        self.next_action_at = self.last_frame_at + random.randint(*action_interval)
        self.action_ends_at = None
        self.action_interval = action_interval
        self.last_action = None

    @classmethod
    def _load_frames(cls, npc_type):
        if npc_type in cls._frames:
            return cls._frames[npc_type]
        if cls._sheet is None:
            path = Path(__file__).resolve().parents[1] / "missao_estoque" / "assets" / "npcs" / "npc_sheet_transparent.png"
            cls._sheet = pygame.image.load(str(path)).convert_alpha()

        frames, feet_offsets = [], []
        for left, top, right, bottom in cls.FRAME_REGIONS[npc_type]:
            frame = cls._sheet.subsurface(pygame.Rect(left, top, right - left, bottom - top)).copy()
            # mantém o alpha original. Não usamos colorkey: o uniforme possui
            # partes escuras que seriam removidas por uma limpeza por cor.
            canvas = pygame.Surface((130, 260), pygame.SRCALPHA)
            canvas.blit(frame, frame.get_rect(midbottom=(65, 260)))
            target_size = (
                round(NPC_SPRITE_WIDTH * NPC_SCALE),
                round(NPC_SPRITE_HEIGHT * NPC_SCALE),
            )
            scaled = pygame.transform.scale(canvas, target_size)
            bounds = scaled.get_bounding_rect()
            frames.append(scaled)
            feet_offsets.append(max(0, scaled.get_height() - bounds.bottom))
        cls._frames[npc_type] = frames
        cls._feet_offsets[npc_type] = feet_offsets
        return frames

    def update(self, dt_seconds=None):
        now = pygame.time.get_ticks()
        if self.state == "idle" and now >= self.next_action_at:
            choices = [action for action in self.idle_actions if action != self.last_action]
            self.state = random.choice(choices or self.idle_actions)
            self.last_action = self.state
            self.frame_index = 0
            minimum, maximum = (2_500, 4_500) if self.calm else self.ACTION_DURATIONS.get(self.npc_type, (NPC_ACTION_MIN_TIME_MS, NPC_ACTION_MAX_TIME_MS))
            self.action_ends_at = now + random.randint(minimum, maximum)
        elif self.state != "idle" and now >= self.action_ends_at:
            self.state = "idle"
            self.frame_index = 0
            self.next_action_at = now + random.randint(*self.action_interval)

        if dt_seconds is None:
            elapsed_ms = min(max(0, now - self.last_frame_at), self.MAX_ELAPSED_MS)
        else:
            elapsed_ms = min(max(0.0, dt_seconds * 1000.0), self.MAX_ELAPSED_MS)
        self.last_frame_at = now
        self.animation_elapsed_ms += elapsed_ms
        while self.animation_elapsed_ms >= NPC_FRAME_TIME_MS:
            self.animation_elapsed_ms -= NPC_FRAME_TIME_MS
            state_frames = self.STATES[self.npc_type][self.state]
            self.frame_index = (self.frame_index + 1) % len(state_frames)

    def draw(self, surface, camera):
        indices = self.STATES[self.npc_type][self.state]
        frame_index = indices[self.frame_index]
        frame = self.frames[frame_index]
        draw_rect = camera.apply_rect(self.rect)
        feet_y = draw_rect.bottom + self.feet_offsets[frame_index]
        surface.blit(frame, frame.get_rect(midbottom=(draw_rect.centerx, feet_y)))
        if SHOW_ANIMATION_DEBUG:
            if NPC._debug_font is None:
                NPC._debug_font = pygame.font.Font(None, 14)
            remaining = max(0, (self.action_ends_at or self.next_action_at) - pygame.time.get_ticks())
            text = f"NPC {self.state} dx:{self.actual_dx:.1f} t:{remaining / 1000:.1f}"
            label = NPC._debug_font.render(text, True, (245, 245, 245), (8, 18, 27))
            surface.blit(label, label.get_rect(midbottom=(draw_rect.centerx, draw_rect.top - 3)))


class NarrativeCharacter(NPC):
    """Personagem recorrente: entidade visual própria, sem colisão de gameplay."""

    def __init__(self, x, floor_top, character_key, npc_type="checker", action_interval=(6_000, 9_000), calm=False):
        super().__init__(x, floor_top, npc_type, action_interval, calm=calm)
        self.character_key = character_key
