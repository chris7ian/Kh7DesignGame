from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Tuple

import pygame

try:
    from . import settings
except ImportError:  # pragma: no cover - soporte para ejecución directa
    import sys
    from pathlib import Path

    current_dir = Path(__file__).resolve().parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    import settings  # type: ignore  # noqa: E402

Vec2 = pygame.math.Vector2
Rect = pygame.Rect


@dataclass
class Laser:
    rect: Rect
    velocity: Vec2

    def update(self, dt: float) -> None:
        self.rect.x += self.velocity.x * dt

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, settings.COLOR_LASER, self.rect)

    def is_offscreen(self) -> bool:
        return self.rect.left > settings.WIDTH


@dataclass
class Meteor:
    rect: Rect
    velocity: Vec2

    def update(self, dt: float) -> None:
        self.rect.x += self.velocity.x * dt
        self.rect.y += self.velocity.y * dt

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, settings.COLOR_METEOR, self.rect, border_radius=8)

    def is_offscreen(self) -> bool:
        return self.rect.right < 0


class Player:
    def __init__(self, position: Tuple[int, int]) -> None:
        w, h = settings.PLAYER_SIZE
        self.rect = Rect(0, 0, w, h)
        self.rect.center = position
        self.speed = settings.PLAYER_SPEED
        self.cooldown = settings.PLAYER_COOLDOWN
        self.cooldown_timer = 0.0
        self.lasers: List[Laser] = []
        self.invulnerable_timer = 0.0

    def update(self, dt: float, directions: Vec2) -> None:
        movement = directions * self.speed * dt
        max_x = max(0, int(settings.WIDTH * 0.4) - self.rect.width)
        new_x = max(0, min(max_x, self.rect.x + movement.x))
        new_y = max(0, min(settings.HEIGHT - self.rect.height, self.rect.y + movement.y))
        self.rect.x = int(new_x)
        self.rect.y = int(new_y)

        # Update lasers
        for laser in self.lasers:
            laser.update(dt)
        self.lasers = [laser for laser in self.lasers if not laser.is_offscreen()]

        # Reduce cooldown
        if self.cooldown_timer > 0:
            self.cooldown_timer -= dt

        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= dt

    def try_shoot(self) -> bool:
        if self.cooldown_timer > 0:
            return False
        lx = self.rect.right
        ly = self.rect.centery - settings.LASER_SIZE[1] // 2
        laser_rect = Rect(lx, ly, *settings.LASER_SIZE)
        velocity = Vec2(settings.LASER_SPEED, 0)
        self.lasers.append(Laser(laser_rect, velocity))
        self.cooldown_timer = self.cooldown
        return True

    def draw(self, surface: pygame.Surface) -> None:
        visible = True
        if self.invulnerable_timer > 0:
            blink_period = 0.15
            phase = int((self.invulnerable_timer / blink_period)) % 2
            visible = phase == 0

        if visible:
            nose = (self.rect.right, self.rect.centery)
            top = (self.rect.left + int(self.rect.width * 0.25), self.rect.top)
            bottom = (self.rect.left + int(self.rect.width * 0.25), self.rect.bottom)
            tail_top = (self.rect.left, self.rect.centery - int(self.rect.height * 0.25))
            tail_bottom = (self.rect.left, self.rect.centery + int(self.rect.height * 0.25))

            pygame.draw.polygon(
                surface,
                settings.COLOR_PLAYER,
                [nose, top, tail_top, tail_bottom, bottom],
            )

            flame_rect = Rect(
                self.rect.left - int(self.rect.width * 0.15),
                self.rect.centery - int(self.rect.height * 0.2),
                int(self.rect.width * 0.15),
                int(self.rect.height * 0.4),
            )
            pygame.draw.rect(surface, settings.COLOR_LASER, flame_rect)

        for laser in self.lasers:
            laser.draw(surface)

    def set_invulnerable(self) -> None:
        self.invulnerable_timer = settings.PLAYER_INVULNERABILITY_TIME

    def is_invulnerable(self) -> bool:
        return self.invulnerable_timer > 0


class MeteorSpawner:
    def __init__(self) -> None:
        self.spawn_interval = settings.METEOR_SPAWN_INTERVAL
        self.timer = 0.0
        self.meteors: List[Meteor] = []

    def update(self, dt: float) -> None:
        self.timer += dt
        if self.timer >= self.spawn_interval:
            self.timer = 0.0
            self.spawn_meteor()

        for meteor in self.meteors:
            meteor.update(dt)
        self.meteors = [meteor for meteor in self.meteors if not meteor.is_offscreen()]

    def spawn_meteor(self) -> None:
        min_w, min_h = settings.METEOR_SIZE_MIN
        max_w, max_h = settings.METEOR_SIZE_MAX
        w = random.randint(min_w, max_w)
        h = random.randint(min_h, max_h)
        x = settings.WIDTH + settings.MINIMAP_WORLD_EXTRA
        buffer = max(60, int(settings.MINIMAP_WORLD_EXTRA * 0.4))
        x += random.randint(-buffer, buffer)
        y = random.randint(0, settings.HEIGHT - h)
        vx = -random.uniform(settings.METEOR_MIN_SPEED, settings.METEOR_MAX_SPEED)
        vy = random.uniform(-60, 60)
        rect = Rect(x, y, w, h)
        velocity = Vec2(vx, vy)
        self.meteors.append(Meteor(rect, velocity))

    def draw(self, surface: pygame.Surface) -> None:
        for meteor in self.meteors:
            meteor.draw(surface)

    def increase_difficulty(self) -> None:
        self.spawn_interval = max(settings.DIFFICULTY_MIN_INTERVAL, self.spawn_interval - settings.DIFFICULTY_STEP)

