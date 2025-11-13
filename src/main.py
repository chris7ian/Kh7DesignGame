from __future__ import annotations

import random
from enum import Enum, auto
from pathlib import Path
from typing import Tuple

import pygame

try:
    from . import entities, settings, ui
except ImportError:  # pragma: no cover - fallback for direct execution
    import sys

    current_dir = Path(__file__).resolve().parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    import entities  # type: ignore  # noqa: E402
    import settings  # type: ignore  # noqa: E402
    import ui  # type: ignore  # noqa: E402


class GameState(Enum):
    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()


class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Interste11ar")
        self.screen = pygame.display.set_mode((settings.WIDTH, settings.HEIGHT + settings.FOOTER_HEIGHT))
        self.play_surface = pygame.Surface((settings.WIDTH, settings.HEIGHT))
        self.clock = pygame.time.Clock()
        self.state = GameState.MENU
        self.stars = [
            [
                random.uniform(0, settings.WIDTH),
                random.uniform(0, settings.HEIGHT),
                random.uniform(40, 140),
            ]
            for _ in range(70)
        ]

        icon_path = Path(__file__).resolve().parent / "icon.png"
        if icon_path.exists():
            try:
                icon_surface = pygame.image.load(icon_path.as_posix())
                pygame.display.set_icon(icon_surface)
            except pygame.error:
                pass

        self.font_manager = ui.FontManager()
        self.hud = ui.HUD(self.font_manager)

        self.player = entities.Player((int(settings.WIDTH * 0.15), settings.HEIGHT // 2))
        self.meteor_spawner = entities.MeteorSpawner()
        self.score = 0
        self.lives = 3
        self.time_accumulator = 0.0
        self._reset_starfield()

        self.shoot_sound = self._load_sound("laser.wav")
        self.explosion_sound = self._load_sound("explosion.wav")
        self.music_loaded = self._load_music("space_theme.ogg")
        if self.music_loaded:
            pygame.mixer.music.play(-1)

    def _load_sound(self, filename: str):
        path = settings.ASSETS_PATH / "sounds" / filename
        if not path.exists():
            return None
        try:
            return pygame.mixer.Sound(path.as_posix())
        except pygame.error:
            return None

    def _load_music(self, filename: str) -> bool:
        path = settings.ASSETS_PATH / "sounds" / filename
        if not path.exists():
            return False
        try:
            pygame.mixer.music.load(path.as_posix())
            pygame.mixer.music.set_volume(0.4)
            return True
        except pygame.error:
            return False

    def reset(self) -> None:
        self.player = entities.Player((int(settings.WIDTH * 0.15), settings.HEIGHT // 2))
        self.meteor_spawner = entities.MeteorSpawner()
        self.score = 0
        self.lives = 3
        self.time_accumulator = 0.0
        self._reset_starfield()

    def handle_menu_input(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.quit()
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.reset()
                    self.state = GameState.PLAYING

    def handle_paused_input(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = GameState.MENU
                if event.key == pygame.K_SPACE:
                    self.state = GameState.PLAYING

    def handle_game_over_input(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = GameState.MENU
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.reset()
                    self.state = GameState.PLAYING

    def handle_gameplay_input(self) -> Tuple[int, int]:
        directions = pygame.math.Vector2(0, 0)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = GameState.PAUSED
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            directions.x -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            directions.x += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            directions.y -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            directions.y += 1
        if keys[pygame.K_SPACE]:
            fired = self.player.try_shoot()
            if fired and self.shoot_sound:
                self.shoot_sound.play()
        return directions.normalize() if directions.length_squared() > 0 else directions

    def update_gameplay(self, dt: float) -> None:
        directions = self.handle_gameplay_input()
        self.player.update(dt, directions)
        self.meteor_spawner.update(dt)

        # Colisiones láser - meteorito
        for laser in list(self.player.lasers):
            for meteor in list(self.meteor_spawner.meteors):
                if laser.rect.colliderect(meteor.rect):
                    self.player.lasers.remove(laser)
                    self.meteor_spawner.meteors.remove(meteor)
                    self.score += 10
                    if self.explosion_sound:
                        self.explosion_sound.play()
                    break

        # Colisiones meteorito - jugador
        for meteor in list(self.meteor_spawner.meteors):
            if meteor.rect.colliderect(self.player.rect):
                self.meteor_spawner.meteors.remove(meteor)
                if not self.player.is_invulnerable():
                    self.lives -= 1
                    self.player.set_invulnerable()
                    if self.lives <= 0:
                        self.state = GameState.GAME_OVER
                break

        # Incrementar dificultad
        self.time_accumulator += dt
        if self.time_accumulator >= 10:
            self.time_accumulator = 0.0
            self.meteor_spawner.increase_difficulty()

    def _reset_starfield(self) -> None:
        for star in self.stars:
            star[0] = random.uniform(0, settings.WIDTH)
            star[1] = random.uniform(0, settings.HEIGHT)
            star[2] = random.uniform(40, 140)

    def update_starfield(self, dt: float) -> None:
        for star in self.stars:
            star[0] -= star[2] * dt * 0.6
            if star[0] < -5:
                star[0] = settings.WIDTH + random.uniform(5, 60)
                star[1] = random.uniform(0, settings.HEIGHT)
                star[2] = random.uniform(40, 140)

    def draw_background(self) -> None:
        self.play_surface.fill(settings.COLOR_BG)
        for x, y, speed in self.stars:
            size = 3 if speed > 110 else 2
            if y < settings.HEIGHT:
                self.play_surface.fill((255, 255, 255), (int(x), int(y), size, size))

    def draw_footer(self) -> None:
        footer_rect = pygame.Rect(0, settings.HEIGHT, settings.WIDTH, settings.FOOTER_HEIGHT)
        pygame.draw.rect(self.screen, (15, 20, 45), footer_rect)
        pygame.draw.line(self.screen, settings.COLOR_MINIMAP_BORDER, (0, settings.HEIGHT), (settings.WIDTH, settings.HEIGHT), width=2)

    def draw_minimap(self) -> None:
        scale = settings.MINIMAP_SCALE
        minimap_width = max(1, int(settings.WIDTH * scale))
        minimap_height = max(1, int(settings.HEIGHT * scale))

        minimap_surface = pygame.Surface((minimap_width, minimap_height))
        minimap_surface.fill(settings.COLOR_MINIMAP_BG)

        world_width = settings.WIDTH + settings.MINIMAP_WORLD_EXTRA
        world_height = settings.HEIGHT
        scale_x = minimap_width / world_width
        scale_y = minimap_height / world_height

        # Área visible actual
        main_width = settings.WIDTH * scale_x
        pygame.draw.rect(
            minimap_surface,
            settings.COLOR_MINIMAP_VIEW,
            pygame.Rect(0, 0, int(main_width), minimap_height),
            width=2,
            border_radius=6,
        )

        def world_to_minimap(x: float, y: float) -> tuple[int, int]:
            clamped_x = max(0.0, min(world_width, x))
            clamped_y = max(0.0, min(world_height, y))
            return int(clamped_x * scale_x), int(clamped_y * scale_y)

        # Player
        px, py = world_to_minimap(self.player.rect.centerx, self.player.rect.centery)
        pygame.draw.circle(minimap_surface, settings.COLOR_PLAYER, (px, py), 6)

        # Lasers
        for laser in self.player.lasers:
            lx1, ly1 = world_to_minimap(laser.rect.left, laser.rect.centery)
            lx2, ly2 = world_to_minimap(laser.rect.right, laser.rect.centery)
            pygame.draw.line(minimap_surface, settings.COLOR_LASER, (lx1, ly1), (lx2, ly2), 2)

        # Meteors
        for meteor in self.meteor_spawner.meteors:
            mx, my = world_to_minimap(meteor.rect.centerx, meteor.rect.centery)
            radius = max(2, int(max(meteor.rect.width * scale_x, meteor.rect.height * scale_y) / 2))
            pygame.draw.circle(minimap_surface, settings.COLOR_METEOR, (mx, my), radius)

        margin = settings.MINIMAP_MARGIN
        padding = settings.MINIMAP_PADDING
        x = int((settings.WIDTH - minimap_width) / 2)
        y = settings.HEIGHT + (settings.FOOTER_HEIGHT - minimap_height) // 2

        frame_rect = pygame.Rect(x - padding, y - padding, minimap_width + padding * 2, minimap_height + padding * 2)
        backdrop = pygame.Surface((frame_rect.width, frame_rect.height), pygame.SRCALPHA)
        backdrop.fill((*settings.COLOR_BG, 210))
        self.screen.blit(backdrop, (frame_rect.x, frame_rect.y))
        self.screen.blit(minimap_surface, (x, y))
        pygame.draw.rect(self.screen, settings.COLOR_MINIMAP_BORDER, frame_rect, width=2, border_radius=10)

    def render(self) -> None:
        self.draw_background()
        target_surface = self.play_surface
        if self.state == GameState.MENU:
            self.hud.draw_center_message(
                target_surface,
                "Interste11ar",
                "Kh7 Designs presents",
                "Presiona Enter o Espacio para comenzar",
            )
        elif self.state == GameState.PLAYING:
            self.player.draw(target_surface)
            self.meteor_spawner.draw(target_surface)
        elif self.state == GameState.PAUSED:
            self.player.draw(target_surface)
            self.meteor_spawner.draw(target_surface)
            self.hud.draw_center_message(target_surface, "Pausa", "Espacio = continuar | Esc = menú")
        elif self.state == GameState.GAME_OVER:
            self.hud.draw_center_message(
                target_surface,
                "Game Over",
                f"Puntuación final: {self.score} | Enter/Espacio = Reiniciar",
            )

        self.screen.blit(self.play_surface, (0, 0))
        self.draw_footer()

        if self.state == GameState.PLAYING:
            self.hud.draw_hud(self.screen, self.score, self.lives, footer=True)
            self.draw_minimap()
        elif self.state == GameState.PAUSED:
            self.hud.draw_hud(self.screen, self.score, self.lives, footer=True)
            self.draw_minimap()
        elif self.state == GameState.GAME_OVER:
            self.hud.draw_hud(self.screen, self.score, self.lives, footer=True)
            self.draw_minimap()

        pygame.display.flip()

    def run(self) -> None:
        while True:
            dt_ms = self.clock.tick(settings.FPS)
            dt = dt_ms / 1000.0

            if self.state == GameState.MENU:
                self.handle_menu_input()
            elif self.state == GameState.PLAYING:
                self.update_gameplay(dt)
            elif self.state == GameState.PAUSED:
                self.handle_paused_input()
            elif self.state == GameState.GAME_OVER:
                self.handle_game_over_input()

            self.update_starfield(dt)
            self.render()

    @staticmethod
    def quit() -> None:
        pygame.quit()
        raise SystemExit()


def main() -> None:
    game = Game()
    game.run()


if __name__ == "__main__":
    main()

