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
        # Verificar si está fuera de la pantalla en cualquier dirección
        return self.rect.left > settings.WIDTH or self.rect.right < 0


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


@dataclass
class Platform:
    rect: Rect
    color: Tuple[int, int, int] = (100, 100, 100)

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, self.color, self.rect, border_radius=4)
        # Sombra sutil
        shadow_rect = Rect(self.rect.x + 2, self.rect.y + 2, self.rect.width, self.rect.height)
        pygame.draw.rect(surface, (50, 50, 50), shadow_rect, border_radius=4)


class Astronaut:
    def __init__(self, position: Tuple[int, int]) -> None:
        w, h = settings.ASTRONAUT_SIZE
        self.rect = Rect(0, 0, w, h)
        self.rect.center = position
        self.velocity = Vec2(0, 0)
        self.speed = settings.ASTRONAUT_SPEED
        self.jump_strength = settings.ASTRONAUT_JUMP_STRENGTH
        self.gravity = settings.ASTRONAUT_GRAVITY
        self.on_ground = False
        self.facing_right = True
        self.invulnerable_timer = 0.0
        self.cooldown = settings.ASTRONAUT_COOLDOWN
        self.cooldown_timer = 0.0
        self.lasers: List[Laser] = []

    def update(self, dt: float, platforms: List[Platform], move_left: bool, move_right: bool, jump: bool) -> None:
        # Aplicar gravedad
        self.velocity.y += self.gravity * dt
        
        # Movimiento horizontal
        if move_left:
            self.velocity.x = -self.speed
            self.facing_right = False
        elif move_right:
            self.velocity.x = self.speed
            self.facing_right = True
        else:
            # Fricción
            self.velocity.x *= 0.8
            if abs(self.velocity.x) < 10:
                self.velocity.x = 0

        # Salto
        if jump and self.on_ground:
            self.velocity.y = -self.jump_strength
            self.on_ground = False

        # Actualizar posición horizontal
        self.rect.x += int(self.velocity.x * dt)
        
        # Colisiones horizontales con plataformas
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.velocity.x > 0:  # Moviéndose a la derecha
                    self.rect.right = platform.rect.left
                elif self.velocity.x < 0:  # Moviéndose a la izquierda
                    self.rect.left = platform.rect.right
                self.velocity.x = 0
                break

        # Actualizar posición vertical
        self.rect.y += int(self.velocity.y * dt)
        self.on_ground = False

        # Colisiones verticales con plataformas
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.velocity.y > 0:  # Cayendo
                    self.rect.bottom = platform.rect.top
                    self.velocity.y = 0
                    self.on_ground = True
                elif self.velocity.y < 0:  # Saltando hacia arriba
                    self.rect.top = platform.rect.bottom
                    self.velocity.y = 0
                break

        # Límites de pantalla horizontal
        self.rect.x = max(0, min(settings.WIDTH - self.rect.width, self.rect.x))
        
        # Si cae fuera de la pantalla, resetear posición
        if self.rect.top > settings.HEIGHT:
            self.rect.x = settings.WIDTH // 2
            self.rect.y = 100
            self.velocity = Vec2(0, 0)

        # Reducir timer de invulnerabilidad
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= dt
        
        # Actualizar láseres
        for laser in self.lasers:
            laser.update(dt)
        self.lasers = [laser for laser in self.lasers if not laser.is_offscreen()]
        
        # Reducir cooldown
        if self.cooldown_timer > 0:
            self.cooldown_timer -= dt

    def draw(self, surface: pygame.Surface) -> None:
        visible = True
        if self.invulnerable_timer > 0:
            blink_period = 0.15
            phase = int((self.invulnerable_timer / blink_period)) % 2
            visible = phase == 0

        if visible:
            # Cuerpo del astronauta (casco)
            helmet_center = (self.rect.centerx, self.rect.top + int(self.rect.height * 0.3))
            helmet_radius = int(min(self.rect.width, self.rect.height) * 0.3)
            pygame.draw.circle(surface, settings.COLOR_ASTRONAUT_HELMET, helmet_center, helmet_radius)
            
            # Visor del casco
            visor_rect = Rect(
                helmet_center[0] - helmet_radius // 2,
                helmet_center[1] - helmet_radius // 3,
                helmet_radius,
                helmet_radius // 2
            )
            pygame.draw.ellipse(surface, (100, 150, 255), visor_rect)
            
            # Cuerpo (torso)
            torso_rect = Rect(
                self.rect.left + int(self.rect.width * 0.2),
                self.rect.top + int(self.rect.height * 0.4),
                int(self.rect.width * 0.6),
                int(self.rect.height * 0.4)
            )
            pygame.draw.rect(surface, settings.COLOR_ASTRONAUT_SUIT, torso_rect, border_radius=4)
            
            # Piernas
            leg_width = int(self.rect.width * 0.15)
            leg_height = int(self.rect.height * 0.3)
            left_leg = Rect(
                self.rect.left + int(self.rect.width * 0.3),
                self.rect.bottom - leg_height,
                leg_width,
                leg_height
            )
            right_leg = Rect(
                self.rect.right - int(self.rect.width * 0.3) - leg_width,
                self.rect.bottom - leg_height,
                leg_width,
                leg_height
            )
            pygame.draw.rect(surface, settings.COLOR_ASTRONAUT_SUIT, left_leg, border_radius=2)
            pygame.draw.rect(surface, settings.COLOR_ASTRONAUT_SUIT, right_leg, border_radius=2)
            
            # Brazos (opcional, solo si hay espacio)
            if self.rect.width > 20:
                arm_width = int(self.rect.width * 0.12)
                arm_height = int(self.rect.height * 0.25)
                left_arm = Rect(
                    self.rect.left,
                    self.rect.top + int(self.rect.height * 0.45),
                    arm_width,
                    arm_height
                )
                right_arm = Rect(
                    self.rect.right - arm_width,
                    self.rect.top + int(self.rect.height * 0.45),
                    arm_width,
                    arm_height
                )
                pygame.draw.rect(surface, settings.COLOR_ASTRONAUT_SUIT, left_arm, border_radius=2)
                pygame.draw.rect(surface, settings.COLOR_ASTRONAUT_SUIT, right_arm, border_radius=2)

    def set_invulnerable(self) -> None:
        self.invulnerable_timer = settings.PLAYER_INVULNERABILITY_TIME

    def is_invulnerable(self) -> bool:
        return self.invulnerable_timer > 0
    
    def try_shoot(self) -> bool:
        if self.cooldown_timer > 0:
            return False
        # Disparar en la dirección que mira el astronauta
        if self.facing_right:
            lx = self.rect.right
            ly = self.rect.centery - settings.ASTRONAUT_LASER_SIZE[1] // 2
            laser_rect = Rect(lx, ly, *settings.ASTRONAUT_LASER_SIZE)
            velocity = Vec2(settings.ASTRONAUT_LASER_SPEED, 0)
        else:
            lx = self.rect.left - settings.ASTRONAUT_LASER_SIZE[0]
            ly = self.rect.centery - settings.ASTRONAUT_LASER_SIZE[1] // 2
            laser_rect = Rect(lx, ly, *settings.ASTRONAUT_LASER_SIZE)
            velocity = Vec2(-settings.ASTRONAUT_LASER_SPEED, 0)
        self.lasers.append(Laser(laser_rect, velocity))
        self.cooldown_timer = self.cooldown
        return True
    
    def draw_lasers(self, surface: pygame.Surface) -> None:
        for laser in self.lasers:
            # Dibujar láser del astronauta con color diferente
            pygame.draw.rect(surface, settings.COLOR_ASTRONAUT_LASER, laser.rect)


class Alien:
    def __init__(self, position: Tuple[int, int], platform: Platform) -> None:
        w, h = settings.ALIEN_SIZE
        self.rect = Rect(0, 0, w, h)
        self.rect.centerx = position[0]
        self.rect.bottom = platform.rect.top
        self.platform = platform
        self.speed = settings.ALIEN_SPEED
        self.direction = 1  # 1 = derecha, -1 = izquierda
        self.start_x = self.rect.centerx
        self.patrol_distance = settings.ALIEN_PATROL_DISTANCE
        self.alive = True

    def update(self, dt: float) -> None:
        if not self.alive:
            return
        
        # Movimiento de patrulla
        self.rect.x += self.direction * self.speed * dt
        
        # Cambiar dirección si alcanza el límite de patrulla
        distance_traveled = abs(self.rect.centerx - self.start_x)
        if distance_traveled >= self.patrol_distance:
            self.direction *= -1
            # Asegurar que no se salga de la plataforma
            if self.rect.left < self.platform.rect.left:
                self.rect.left = self.platform.rect.left
                self.direction = 1
            elif self.rect.right > self.platform.rect.right:
                self.rect.right = self.platform.rect.right
                self.direction = -1

    def draw(self, surface: pygame.Surface) -> None:
        if not self.alive:
            return
        
        # Cuerpo del alien (círculo)
        pygame.draw.circle(surface, settings.COLOR_ALIEN, self.rect.center, int(self.rect.width * 0.4))
        
        # Ojos
        eye_size = 6
        left_eye = (self.rect.centerx - 8, self.rect.centery - 5)
        right_eye = (self.rect.centerx + 8, self.rect.centery - 5)
        pygame.draw.circle(surface, (255, 255, 255), left_eye, eye_size)
        pygame.draw.circle(surface, (255, 255, 255), right_eye, eye_size)
        pygame.draw.circle(surface, (0, 0, 0), left_eye, eye_size // 2)
        pygame.draw.circle(surface, (0, 0, 0), right_eye, eye_size // 2)
        
        # Tentáculos o patas
        tentacle_y = self.rect.bottom - 5
        for i in range(3):
            x_offset = (i - 1) * 12
            pygame.draw.line(surface, settings.COLOR_ALIEN, 
                           (self.rect.centerx + x_offset, self.rect.bottom),
                           (self.rect.centerx + x_offset, tentacle_y), 3)

