class Camera:
    """Camera horizontal suave, limitada ao tamanho do mapa."""

    def __init__(self, world_width, viewport_width, smoothing, deadzone=110, look_ahead=48):
        self.world_width = world_width
        self.viewport_width = viewport_width
        self.smoothing = smoothing
        self.deadzone = deadzone
        self.look_ahead = look_ahead
        self.x = 0.0

    def update(self, target_rect, direction=0):
        max_x = max(0, self.world_width - self.viewport_width)
        center = self.x + self.viewport_width / 2
        target_x = self.x
        if target_rect.centerx < center - self.deadzone:
            target_x = target_rect.centerx - (self.viewport_width / 2 - self.deadzone)
        elif target_rect.centerx > center + self.deadzone:
            target_x = target_rect.centerx - (self.viewport_width / 2 + self.deadzone)
        if direction:
            target_x += direction * self.look_ahead
        target_x = max(0, min(target_x, max_x))
        self.x += (target_x - self.x) * self.smoothing

    def focus_world_x(self, world_x, smoothing=None):
        """Pan cinematografico suave, limitado ao mapa e sem alterar a fisica."""
        max_x = max(0, self.world_width - self.viewport_width)
        target_x = max(0, min(world_x - self.viewport_width / 2, max_x))
        self.x += (target_x - self.x) * (self.smoothing if smoothing is None else smoothing)

    def apply_rect(self, rect):
        return rect.move(-round(self.x), 0)

    def apply_x(self, x):
        return x - round(self.x)
