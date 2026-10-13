"""Catálogo data-driven dos personagens jogáveis."""

from pathlib import Path


ASSET_ROOT = Path(__file__).resolve().parents[1] / "missao_estoque" / "assets"

# Offsets relativos ao midbottom da hitbox. O eixo X e invertido ao olhar para
# a esquerda; o Y acompanha discretamente o passo sem alterar a fisica.
DEFAULT_CARRY_OFFSETS = {
    "carry_idle": ((18, -10),),
    "carry_walk": ((18, -10), (18, -9), (18, -10), (18, -11), (18, -10), (18, -9)),
    "carry_jump": ((18, -11), (18, -12)),
    "carry_fall": ((18, -12), (18, -11)),
    "carry_land": ((18, -9), (18, -10)),
}

PLAYABLE_CHARACTERS = {
    "player_default": {
        "name": "Daniel",
        "role": "Estoquista",
        "tagline": "Pronto para organizar cada missão.",
        "accent": (255, 193, 64),
        "sheet": ASSET_ROOT / "player" / "sheets" / "warehouse_worker_animations.png",
        "layout": "legacy",
        "gait_manifest": ASSET_ROOT / "characters" / "playable" / "daniel" / "gait_v4.json",
        "rest_manifest": ASSET_ROOT / "characters" / "playable" / "daniel" / "rest_v4.json",
        "visual_scale": 1.0,
        "footstep_frames": {"walk": (1, 4), "carry_walk": (1, 4)},
        "carry_offsets": DEFAULT_CARRY_OFFSETS,
    },
    "luiza": {
        "name": "Luiza",
        "gait_manifest": ASSET_ROOT / "characters" / "playable" / "luiza" / "gait_v4.json",
        "rest_manifest": ASSET_ROOT / "characters" / "playable" / "luiza" / "rest_v4.json",
        "role": "Estoquista",
        "tagline": "Organização e foco em cada detalhe!",
        "accent": (233, 30, 99),
        "sheet": ASSET_ROOT / "characters" / "playable" / "luiza" / "atlas_v1.png",
        "motion_sheet": ASSET_ROOT / "characters" / "playable" / "luiza" / "motion_atlas_v2.png",
        # O gerador preservou as poses, mas distribuiu a Luiza com espacamento
        # levemente irregular. Centros explicitos impedem cortar membros ou
        # capturar pixels da pose vizinha.
        "motion_centers": (
            (170, 385, 600, 815, 1045, 1280),
            (170, 385, 600, 815, 1045, 1280),
            (170, 385, 600, 815, 1045, 1280),
            (170, 390, 600, 815, 1015, 1210),
        ),
        "motion_crop_width": 170,
        "layout": "grid_6x4",
        "visual_scale": 0.88,
        "footstep_frames": {"walk": (1, 4), "carry_walk": (1, 4)},
        "carry_offsets": DEFAULT_CARRY_OFFSETS,
    },
    "andrew_lessa": {
        "name": "Andrew",
        "gait_manifest": ASSET_ROOT / "characters" / "playable" / "andrew_lessa" / "gait_v4.json",
        "rest_manifest": ASSET_ROOT / "characters" / "playable" / "andrew_lessa" / "rest_v4.json",
        "role": "Estoquista",
        "tagline": "Disciplina e agilidade sempre!",
        "accent": (66, 165, 245),
        "sheet": ASSET_ROOT / "characters" / "playable" / "andrew_lessa" / "atlas_v1.png",
        "motion_sheet": ASSET_ROOT / "characters" / "playable" / "andrew_lessa" / "motion_atlas_v2.png",
        "layout": "grid_6x4",
        "visual_scale": 0.88,
        "footstep_frames": {"walk": (1, 4), "carry_walk": (1, 4)},
        "carry_offsets": DEFAULT_CARRY_OFFSETS,
    },
}

CHARACTER_IDS = tuple(PLAYABLE_CHARACTERS)


def character_definition(character_id):
    return PLAYABLE_CHARACTERS.get(character_id, PLAYABLE_CHARACTERS["player_default"])
