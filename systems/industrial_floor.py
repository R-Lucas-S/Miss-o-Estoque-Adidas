import random

import pygame


class IndustrialFloor:
    """Piso visual reutilizável, separado da colisão física do nível."""

    def __init__(self, floor_rect, seed=0):
        self.rect = floor_rect.copy()
        self.image = self._build_surface(seed)
        self._shadows = {}

    def _build_surface(self, seed):
        """Gera a textura uma vez, evitando trabalho extra no game loop."""
        image = pygame.Surface(self.rect.size)
        image.fill((45, 50, 56))

        # Faixa horizontal realmente caminhavel. Ela permanece visivel entre
        # os pes dos personagens e o HUD, deixando clara a profundidade do piso.
        walkable_height = min(70, self.rect.height)
        pygame.draw.rect(image, (105, 110, 112), (0, 0, self.rect.width, walkable_height))
        pygame.draw.rect(image, (93, 99, 102), (0, 24, self.rect.width, walkable_height - 24))
        pygame.draw.line(image, (178, 184, 184), (0, 1), (self.rect.width, 1), 2)
        pygame.draw.line(image, (68, 74, 78), (0, walkable_height - 2), (self.rect.width, walkable_height - 2), 2)

        # Placas vistas em perspectiva, sem formar uma parede escura vertical.
        for x in range(180, self.rect.width, 240):
            pygame.draw.line(image, (76, 82, 85), (x, 3), (x + 18, walkable_height - 3), 1)
        pygame.draw.line(image, (126, 131, 132), (0, 25), (self.rect.width, 25), 1)
        pygame.draw.line(image, (82, 88, 91), (0, 50), (self.rect.width, 50), 1)

        # Acabamento inferior, normalmente coberto pelo HUD nas fases.
        pygame.draw.line(image, (25, 29, 33), (0, self.rect.height - 3), (self.rect.width, self.rect.height - 3), 3)

        # Juntas verticais discretas entre placas de concreto.
        for x in range(180, self.rect.width, 240):
            pygame.draw.line(image, (34, 39, 44), (x, walkable_height), (x, self.rect.height - 5), 2)
            pygame.draw.line(image, (62, 68, 73), (x + 2, walkable_height), (x + 2, self.rect.height - 5), 1)

        # Marcacoes de seguranca pontuais, sem competir com os objetos.
        for start_x in range(100, self.rect.width, 720):
            for stripe_x in range(start_x, min(start_x + 150, self.rect.width), 24):
                pygame.draw.rect(image, (210, 168, 45), (stripe_x, 55, 14, 4))

        # Pequenas marcas de uso, deterministicas e pre-renderizadas.
        generator = random.Random(seed)
        for _ in range(max(8, self.rect.width // 160)):
            x = generator.randrange(0, self.rect.width)
            y = generator.randrange(8, max(9, walkable_height - 8))
            length = generator.randrange(8, 28)
            pygame.draw.line(image, (57, 62, 67), (x, y), (min(x + length, self.rect.width), y), 1)

        return image

    def draw(self, surface, camera):
        surface.blit(self.image, (camera.apply_x(self.rect.left), self.rect.top))

    def draw_contact_shadow(self, surface, camera, world_x, width=54):
        """Desenha uma sombra visual sob um objeto apoiado no piso."""
        width = max(16, int(width))
        if width not in self._shadows:
            shadow = pygame.Surface((width, 12), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (8, 11, 15, 108), shadow.get_rect())
            self._shadows[width] = shadow

        shadow = self._shadows[width]
        shadow_rect = shadow.get_rect(midbottom=(camera.apply_x(world_x), self.rect.top + 7))
        surface.blit(shadow, shadow_rect)
