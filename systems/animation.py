import json
import pygame

from missao_estoque.settings import PLAYER_CARRY_IDLE_FRAME_TIME, PLAYER_CARRY_WALK_FRAME_TIME, PLAYER_IDLE_FRAME_TIME, PLAYER_WALK_FRAME_TIME
from data.playable_characters import character_definition


class AnimationPlayer:
    """Prepara os frames uma vez e controla sua troca por tempo."""

    MAX_ELAPSED_MS = 50

    FRAME_BOUNDS = {
        "idle": [(23, 58, 118, 248), (147, 58, 239, 248), (266, 58, 354, 248), (383, 58, 471, 248), (495, 58, 580, 248), (607, 58, 694, 248)],
        "walk": [(729, 61, 834, 251), (855, 61, 965, 248), (994, 61, 1102, 251), (1112, 61, 1234, 251), (1263, 58, 1374, 251), (1398, 59, 1506, 251)],
        "run": [(22, 321, 156, 499), (160, 318, 285, 500), (268, 320, 409, 500), (400, 320, 528, 501), (513, 321, 661, 501), (665, 313, 803, 503)],
        "jump": [(851, 380, 969, 505), (984, 315, 1094, 491), (1122, 294, 1233, 454), (1266, 311, 1358, 484), (1383, 377, 1499, 505)],
        "fall": [(20, 566, 135, 723), (151, 576, 259, 723), (250, 629, 367, 754)],
        "land": [(384, 636, 504, 754), (502, 622, 620, 755), (633, 577, 736, 754)],
        "carry": [(800, 570, 907, 759), (916, 570, 1028, 758), (1041, 570, 1149, 758), (1165, 567, 1266, 755), (1274, 565, 1387, 756), (1394, 571, 1501, 758)],
        "special_cross": [(9, 836, 82, 998), (94, 837, 171, 998), (171, 837, 245, 998), (254, 839, 324, 998), (331, 837, 403, 998)],
        "special_tap": [(416, 835, 487, 998), (501, 833, 580, 998), (599, 832, 675, 998), (692, 835, 769, 999)],
        "special_adjust": [(788, 836, 864, 999), (873, 836, 951, 999), (954, 837, 1030, 999), (1037, 857, 1114, 999), (1115, 836, 1189, 999)],
    }
    DURATIONS = {
        "idle": PLAYER_IDLE_FRAME_TIME,
        "walk": PLAYER_WALK_FRAME_TIME,
        "run": 83,
        "jump": 75,
        "fall": 110,
        "land": 75,
        "carry_idle": PLAYER_CARRY_IDLE_FRAME_TIME,
        "carry_walk": PLAYER_CARRY_WALK_FRAME_TIME,
        "carry_jump": 85,
        "carry_fall": 120,
        "carry_land": 85,
        "pick_up": 110,
        "put_down": 110,
        "scan": 220,
        "interact": 240,
        "celebrate": 75,
        "clap": 320,
        "thinking": 420,
        "push_cart": 110,
        "special_cross": 170,
        "special_tap": 220,
        "special_adjust": 200,
    }
    NON_LOOPING = {
        "jump", "fall", "land", "carry_jump", "carry_fall", "carry_land",
        "pick_up", "put_down", "interact", "celebrate",
        "special_cross", "special_tap", "special_adjust",
    }

    def __init__(self, target_size, character_id="player_default"):
        definition = character_definition(character_id)
        self.character_id = character_id
        self.footstep_frames = dict(definition.get("footstep_frames", {}))
        sheet = pygame.image.load(str(definition["sheet"])).convert_alpha()
        visual_scale = definition.get("visual_scale", 1.0)
        self.frames = self._prepare_grid_frames(sheet, target_size, visual_scale) if definition["layout"] == "grid_6x4" else self._prepare_frames(sheet, target_size)
        if definition.get("motion_sheet"):
            motion_sheet = pygame.image.load(str(definition["motion_sheet"])).convert_alpha()
            self.frames.update(self._prepare_motion_frames(
                motion_sheet,
                target_size,
                visual_scale,
                definition.get("motion_columns", 6),
                definition.get("motion_frame_limit"),
                definition.get("motion_right_margin", 8),
                definition.get("motion_centers"),
                definition.get("motion_crop_width", 190),
            ))
        if definition["layout"] == "legacy":
            aliases = {
                "interact": "special_adjust", "scan": "special_tap", "celebrate": "special_cross",
                "clap": "special_tap", "thinking": "special_adjust", "push_cart": "walk",
                "pick_up": "carry_idle", "put_down": "carry_idle",
            }
            for alias, source in aliases.items():
                self.frames[alias] = self.frames[source]
        self.gait_names = ()
        self.carry_anchors = {}
        if definition.get("gait_manifest"):
            self._load_gait(definition["gait_manifest"], target_size)
        if definition.get("rest_manifest"):
            self._load_gait(definition["rest_manifest"], target_size)
            # A mesma caixa e mãos acompanham todo o arco físico do salto.
            for name, source, index in (("carry_jump", "carry_walk", 1), ("carry_fall", "carry_walk", 3), ("carry_land", "carry_idle", 0)):
                self.frames[name] = {"right": [self.frames[source]["right"][index]], "left": []}
                self.carry_anchors[name] = (self.carry_anchors[source][index],)
        self.frames["idle"]["right"] = self.frames["idle"]["right"][:4]
        self._normalize_canvases(target_size[1])
        self.name = "idle"
        self.frame_index = 0
        self.last_frame_at = pygame.time.get_ticks()
        self.animation_elapsed_ms = 0.0
        self.finished = False
        self.events = []

    def _load_gait(self, manifest_path, target_size):
        """Atlas revisado: uma escala e pivôs autorados, sem fit por pose."""
        metadata = json.loads(manifest_path.read_text(encoding="utf-8"))
        sheet = pygame.image.load(str(manifest_path.parent / metadata["image"])).convert_alpha()
        # Descarta só resíduos de transparência fora da silhueta da arte.
        mask = pygame.mask.from_surface(sheet, 127).to_surface(
            setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
        sheet.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        scale = metadata["height_at_110"] / metadata["source_height"] * target_size[1] / 110
        canvas_size = (target_size[1], target_size[1])
        self.gait_names = tuple(metadata.get("phases", self.gait_names))
        for name in ("walk", "carry_walk", "idle", "carry_idle"):
            if name not in metadata:
                continue
            frames = []
            anchors = []
            for entry in metadata[name]:
                region = pygame.Rect(entry["rect"])
                raw = sheet.subsurface(region)
                scaled = pygame.transform.scale(raw, (round(region.w * scale), round(region.h * scale)))
                px, py = entry["pivot"]
                origin = (canvas_size[0] // 2 - round((px - region.x) * scale), canvas_size[1] - round((py - region.y) * scale))
                canvas = pygame.Surface(canvas_size, pygame.SRCALPHA)
                canvas.blit(scaled, origin)
                frames.append(canvas)
                if "hand" in entry:
                    hx, hy = entry["hand"]
                    anchors.append((round((hx - px) * scale), round((hy - py) * scale)))
            self.frames[name] = {"right": frames, "left": []}
            if name in ("walk", "carry_walk"):
                self.footstep_frames[name] = tuple(metadata["contacts"])
            if anchors:
                self.carry_anchors[name] = tuple(anchors)

    def _normalize_canvases(self, canvas_height):
        """Mantém um canvas único sem redimensionar ou recentralizar o conteúdo."""
        content_width = max(frame.get_width() for animation in self.frames.values() for frames in animation.values() for frame in frames)
        width = max(canvas_height, content_width)
        for animation in self.frames.values():
            for direction, frames in (("right", animation["right"]),):
                normalized = []
                for frame in frames:
                    canvas = pygame.Surface((width, canvas_height), pygame.SRCALPHA)
                    canvas.blit(frame, frame.get_rect(midbottom=(width // 2, canvas_height)))
                    normalized.append(canvas)
                animation[direction] = normalized
            # Espelhar DEPOIS do padding evita deslocamento de 1px em
            # larguras ímpares. O pivot é sempre o centro do mesmo canvas.
            animation["left"] = [pygame.transform.flip(frame, True, False) for frame in animation["right"]]

    @staticmethod
    def _scaled_frame(raw, target_size, visual_scale):
        # O fundo removido pelo gerador ainda contem um halo de alpha baixo.
        # Medir a pose pelos pixels realmente visiveis mantém a escala corporal
        # constante entre idle, caminhada e transporte da caixa.
        bounds = raw.get_bounding_rect(min_alpha=160)
        cropped = raw.subsurface(bounds) if bounds.width and bounds.height else raw
        content_height = max(1, round(target_size[1] * visual_scale))
        scale = content_height / cropped.get_height()
        scaled_size = (max(1, round(cropped.get_width() * scale)), content_height)
        scaled = pygame.transform.scale(cropped, scaled_size)
        canvas_width = max(target_size[0], scaled.get_width())
        canvas = pygame.Surface((canvas_width, target_size[1]), pygame.SRCALPHA)
        canvas.blit(scaled, scaled.get_rect(midbottom=(canvas_width // 2, target_size[1])))
        return canvas

    def _prepare_grid_frames(self, sheet, target_size, visual_scale=1.0):
        cell_w, cell_h = sheet.get_width() // 6, sheet.get_height() // 4
        grid = []
        for row in range(4):
            frames = []
            for column in range(6):
                raw = sheet.subsurface((column * cell_w, row * cell_h, cell_w, cell_h))
                # O atlas gerado possui alguns pixels de poses vizinhas junto
                # as bordas das celulas. Mantemos uma área segura nas poses de
                # corpo e liberamos mais largura apenas para props reais.
                if row == 0:
                    margin = 32
                elif row == 1:
                    margin = 20
                elif row == 2:
                    margin = 10
                elif column == 5:  # carrinho ocupa legitimamente toda a celula
                    margin = 0
                else:
                    margin = 35 if column == 4 else 20
                if margin:
                    raw = raw.subsurface((margin, 0, cell_w - margin * 2, cell_h))
                frames.append(self._scaled_frame(raw, target_size, visual_scale))
            grid.append(frames)
        named = {
            "idle": grid[0][0:2], "walk": grid[0][2:6], "run": grid[1][0:2],
            "jump": [grid[1][2]], "fall": [grid[1][3]], "land": [grid[1][4]],
            "interact": [grid[1][5]], "carry_idle": [grid[2][0]],
            "carry_walk": grid[2][1:4], "pick_up": [grid[2][4]], "put_down": [grid[2][5]],
            "scan": grid[3][0:2], "celebrate": [grid[3][2]], "clap": [grid[3][3]],
            "thinking": [grid[3][4]], "push_cart": [grid[3][5]],
        }
        named["carry_jump"] = [grid[2][1]]
        named["carry_fall"] = [grid[2][2]]
        named["carry_land"] = [grid[2][0]]
        named["special_cross"] = named["thinking"]
        named["special_tap"] = named["clap"]
        named["special_adjust"] = named["interact"]
        return {name: {"right": frames, "left": [pygame.transform.flip(frame, True, False) for frame in frames]} for name, frames in named.items()}

    def _prepare_motion_frames(
        self, sheet, target_size, visual_scale, columns=6, frame_limit=None,
        right_margin=8, centers=None, crop_width=190,
    ):
        cell_w, cell_h = sheet.get_width() // columns, sheet.get_height() // 4
        rows = []
        for row in range(4):
            frames = []
            frame_regions = []
            if centers:
                for center_x in centers[row]:
                    left = max(0, round(center_x - crop_width / 2))
                    width = min(crop_width, sheet.get_width() - left)
                    frame_regions.append((left, row * cell_h, width, cell_h))
            else:
                for column in range(columns):
                    frame_regions.append((column * cell_w, row * cell_h, cell_w, cell_h))
            for region in frame_regions:
                raw = sheet.subsurface(region)
                # A geracao v2 respeita margem interna; um corte pequeno remove
                # residuos junto as divisorias. A margem inferior e importante:
                # alguns pixels da linha seguinte faziam o corpo parecer menor
                # nas poses com caixa, embora o bounding box continuasse alto.
                if not centers:
                    raw = raw.subsurface((8, 0, cell_w - 8 - right_margin, cell_h))
                if row == 2:
                    raw = raw.subsurface((0, 0, raw.get_width(), raw.get_height() - 56))
                if raw.get_bounding_rect(min_alpha=8).width:
                    frames.append(self._scaled_frame(raw, target_size, visual_scale))
            if frame_limit:
                frames = frames[:frame_limit]
            rows.append(frames)
        named = {
            "idle": rows[0],
            "walk": rows[1],
            "carry_idle": [rows[2][0]],
            "carry_walk": rows[2],
            # Mantemos o mesmo conjunto e a mesma densidade visual durante
            # todo o arco do salto. Antes estes estados vinham do atlas v1 e
            # Andrew encolhia assim que os pes deixavam o chao.
            "carry_jump": rows[2][2:4],
            "carry_fall": rows[2][3:5],
            "carry_land": [rows[2][1], rows[2][0]],
            "celebrate": rows[3],
            "special_cross": rows[0],
            "special_tap": rows[3][4:6] + rows[3][4:5],
            "special_adjust": list(reversed(rows[0])),
        }
        return {
            name: {"right": frames, "left": [pygame.transform.flip(frame, True, False) for frame in frames]}
            for name, frames in named.items()
        }

    def _prepare_frames(self, sheet, target_size):
        animations = {}
        canvas_size = (160, 215)
        for name, bounds_list in self.FRAME_BOUNDS.items():
            right_frames = []
            for left, top, right, bottom in bounds_list:
                raw_frame = sheet.subsurface(pygame.Rect(left, top, right - left, bottom - top))
                canvas = pygame.Surface(canvas_size, pygame.SRCALPHA)
                canvas.blit(raw_frame, raw_frame.get_rect(midbottom=(canvas_size[0] // 2, canvas_size[1])))
                right_frames.append(pygame.transform.scale(canvas, target_size))
            animations[name] = {"right": right_frames, "left": [pygame.transform.flip(frame, True, False) for frame in right_frames]}
        # A sequencia CARRY já traz a caixa posicionada entre os antebracos e
        # as maos. Ela e a camada visual autoritativa enquanto o Player leva
        # uma caixa; portanto não desenhamos uma segunda caixa sobre o sprite.
        carry_right = animations["carry"]["right"]
        carry_left = animations["carry"]["left"]
        animations["carry_idle"] = {"right": [carry_right[0]], "left": [carry_left[0]]}
        animations["carry_walk"] = {"right": carry_right, "left": carry_left}
        # O sheet não possui poses aereas exclusivas com carga. Reutilizamos
        # poses CARRY contiguas: a fisica faz o arco do salto, enquanto bracos,
        # maos e caixa continuam juntos na arte (sem caixa sobreposta).
        animations["carry_jump"] = {"right": carry_right[1:4], "left": carry_left[1:4]}
        animations["carry_fall"] = {"right": carry_right[3:6], "left": carry_left[3:6]}
        animations["carry_land"] = {"right": [carry_right[0], carry_right[1], carry_right[0]], "left": [carry_left[0], carry_left[1], carry_left[0]]}
        return animations

    def set(self, name):
        if name != self.name:
            self.name = name
            self.frame_index = 0
            self.finished = False
            self.last_frame_at = pygame.time.get_ticks()
            self.animation_elapsed_ms = 0.0
            self.events.clear()

    def update(self, speed_multiplier=1.0, dt_seconds=None, *, distance=None, cycle_distance=None):
        self.events.clear()
        now = pygame.time.get_ticks()
        if dt_seconds is None:
            elapsed_ms = min(max(0, now - self.last_frame_at), self.MAX_ELAPSED_MS)
        else:
            elapsed_ms = min(max(0.0, dt_seconds * 1000.0), self.MAX_ELAPSED_MS)
        self.last_frame_at = now
        # A caminhada consome deslocamento APÓS colisões. O tempo continua
        # disponível para previews e para estados sem locomoção.
        if distance is not None and self.name in ("walk", "carry_walk"):
            if cycle_distance is None or cycle_distance <= 0:
                raise ValueError("cycle_distance must be positive")
            duration = self.DURATIONS[self.name]
            count = len(self.frames[self.name]["right"])
            self.animation_elapsed_ms += abs(distance) / cycle_distance * count * duration * speed_multiplier
            speed_multiplier = 1.0
        else:
            self.animation_elapsed_ms += elapsed_ms * speed_multiplier
        interval = self.DURATIONS.get(self.name, 120)
        last_index = len(self.frames[self.name]["right"]) - 1
        while self.animation_elapsed_ms + 1e-8 >= interval and not self.finished:
            self.animation_elapsed_ms -= interval
            if self.frame_index < last_index:
                self.frame_index += 1
            elif self.name in self.NON_LOOPING:
                self.finished = True
                self.animation_elapsed_ms = 0.0
            else:
                self.frame_index = 0
            contacts = self.footstep_frames.get(self.name, self._foot_contact_frames(last_index + 1))
            if self.name in ("walk", "carry_walk") and self.frame_index in contacts:
                self.events.append("footstep")

    def step_frame(self, delta=1):
        """Controle explícito para inspetores/debug; não é usado no gameplay."""
        count = len(self.frames[self.name]["right"])
        self.frame_index = (self.frame_index + delta) % count
        self.animation_elapsed_ms = 0.0
        self.finished = False

    @staticmethod
    def _foot_contact_frames(frame_count):
        if frame_count >= 6:
            return (1, 4)
        if frame_count >= 4:
            return (1, 3)
        return (1,) if frame_count > 1 else ()

    def consume_events(self):
        events = tuple(self.events)
        self.events.clear()
        return events

    def image(self, direction):
        return self.frames[self.name][direction][self.frame_index]
