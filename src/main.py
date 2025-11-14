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


class GameMode(Enum):
    SHIP = auto()
    PLATFORMER = auto()


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

        self.game_mode = GameMode.SHIP
        self.player = entities.Player((int(settings.WIDTH * 0.15), settings.HEIGHT // 2))
        self.astronaut = entities.Astronaut((settings.WIDTH // 2, 100))
        self.meteor_spawner = entities.MeteorSpawner()
        self.platforms = self._create_platforms()
        self.aliens: list[entities.Alien] = []
        self.score = 0
        self.lives = 3
        self.time_accumulator = 0.0
        self._reset_starfield()
        self._create_aliens()

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

    def _create_platforms(self) -> list[entities.Platform]:
        """Crea las plataformas del nivel"""
        platforms = []
        
        # Suelo base
        ground = entities.Platform(
            pygame.Rect(0, settings.HEIGHT - settings.GROUND_HEIGHT, settings.WIDTH, settings.GROUND_HEIGHT),
            settings.PLATFORM_COLOR
        )
        platforms.append(ground)
        
        # Plataformas adicionales
        platform_data = [
            (100, 450, 200, 20),
            (350, 380, 150, 20),
            (550, 300, 180, 20),
            (200, 250, 120, 20),
            (450, 180, 200, 20),
        ]
        
        for x, y, w, h in platform_data:
            platform = entities.Platform(
                pygame.Rect(x, y, w, h),
                settings.PLATFORM_COLOR
            )
            platforms.append(platform)
        
        return platforms

    def _create_aliens(self) -> None:
        """Crea aliens en algunas plataformas"""
        self.aliens.clear()
        # Añadir aliens a algunas plataformas (excluyendo el suelo base)
        platform_data = [
            (100, 450, 200, 20),
            (350, 380, 150, 20),
            (550, 300, 180, 20),
            (200, 250, 120, 20),
            (450, 180, 200, 20),
        ]
        
        # Añadir aliens a algunas plataformas específicas
        alien_platform_indices = [1, 2, 4]  # Índices de plataformas que tendrán aliens
        
        for idx in alien_platform_indices:
            if idx < len(platform_data):
                x, y, w, h = platform_data[idx]
                # Encontrar la plataforma correspondiente
                for platform in self.platforms:
                    if platform.rect.x == x and platform.rect.y == y:
                        # Crear alien en el centro de la plataforma
                        alien = entities.Alien((x + w // 2, y), platform)
                        self.aliens.append(alien)
                        break

    def reset(self) -> None:
        self.game_mode = GameMode.SHIP
        self.player = entities.Player((int(settings.WIDTH * 0.15), settings.HEIGHT // 2))
        self.astronaut = entities.Astronaut((settings.WIDTH // 2, 100))
        self.meteor_spawner = entities.MeteorSpawner()
        self.platforms = self._create_platforms()
        self._create_aliens()
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

    def handle_gameplay_events(self) -> None:
        """Maneja eventos comunes para ambos modos"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = GameState.PAUSED
                # Cambiar entre nave y astronauta con la tecla E
                if event.key == pygame.K_e:
                    if self.game_mode == GameMode.SHIP:
                        # Solo permitir bajar si la nave está cerca del suelo
                        ground_level = settings.HEIGHT - settings.GROUND_HEIGHT
                        # Verificar si la nave está cerca del suelo
                        # La nave puede estar hasta LANDING_DISTANCE píxeles arriba del suelo
                        # o en el límite inferior de la pantalla (tocando el suelo visualmente)
                        player_bottom = self.player.rect.bottom
                        is_near_ground = (ground_level - settings.LANDING_DISTANCE <= player_bottom <= settings.HEIGHT)
                        
                        if is_near_ground:
                            # Cambiar a modo plataformas - posicionar astronauta cerca de la nave
                            self.astronaut.rect.x = self.player.rect.centerx
                            self.astronaut.rect.y = ground_level - self.astronaut.rect.height
                            self.astronaut.velocity = pygame.math.Vector2(0, 0)
                            # Limpiar meteoritos y láseres al cambiar a modo plataformas (están en el espacio)
                            self.meteor_spawner.meteors.clear()
                            self.player.lasers.clear()
                            self.game_mode = GameMode.PLATFORMER
                    else:
                        # Cambiar a modo nave - solo si el astronauta está cerca de la nave
                        # Calcular distancia entre el astronauta y la nave
                        astronaut_center = pygame.math.Vector2(self.astronaut.rect.centerx, self.astronaut.rect.centery)
                        ship_center = pygame.math.Vector2(self.player.rect.centerx, self.player.rect.centery)
                        distance = (astronaut_center - ship_center).length()
                        
                        if distance <= settings.BOARDING_DISTANCE:
                            # Cambiar a modo nave
                            self.game_mode = GameMode.SHIP

    def handle_ship_input(self) -> pygame.math.Vector2:
        """Maneja input para modo nave"""
        directions = pygame.math.Vector2(0, 0)
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
    
    def handle_platformer_input(self) -> Tuple[bool, bool, bool, bool]:
        """Retorna (move_left, move_right, jump, shoot)"""
        keys = pygame.key.get_pressed()
        move_left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        move_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        jump = keys[pygame.K_w] or keys[pygame.K_UP]
        shoot = keys[pygame.K_SPACE]  # Espacio para disparar en modo plataformas
        return move_left, move_right, jump, shoot

    def update_gameplay(self, dt: float) -> None:
        # Manejar eventos comunes primero
        self.handle_gameplay_events()
        
        if self.game_mode == GameMode.SHIP:
            directions = self.handle_ship_input()
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
        
        elif self.game_mode == GameMode.PLATFORMER:
            move_left, move_right, jump, shoot = self.handle_platformer_input()
            self.astronaut.update(dt, self.platforms, move_left, move_right, jump)
            
            # Manejar disparo del astronauta
            if shoot:
                fired = self.astronaut.try_shoot()
                if fired and self.shoot_sound:
                    self.shoot_sound.play()
            
            # Actualizar aliens
            for alien in self.aliens:
                if alien.alive:
                    alien.update(dt)
            
            # Colisiones láser del astronauta - alien
            for laser in list(self.astronaut.lasers):
                for alien in list(self.aliens):
                    if alien.alive and laser.rect.colliderect(alien.rect):
                        self.astronaut.lasers.remove(laser)
                        alien.alive = False
                        self.score += 20
                        if self.explosion_sound:
                            self.explosion_sound.play()
                        break
            
            # Colisiones alien - astronauta
            for alien in list(self.aliens):
                if alien.alive and alien.rect.colliderect(self.astronaut.rect):
                    if not self.astronaut.is_invulnerable():
                        self.lives -= 1
                        self.astronaut.set_invulnerable()
                        if self.lives <= 0:
                            self.state = GameState.GAME_OVER
                    break
            
            # No actualizar ni generar meteoritos en modo plataformas (están en el espacio)

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
        if self.game_mode == GameMode.SHIP:
            self.play_surface.fill(settings.COLOR_BG)
            for x, y, speed in self.stars:
                size = 3 if speed > 110 else 2
                if y < settings.HEIGHT:
                    self.play_surface.fill((255, 255, 255), (int(x), int(y), size, size))
        else:
            # Fondo para modo plataformas (cielo espacial más oscuro)
            self.play_surface.fill((10, 10, 25))
            # Estrellas más tenues
            for x, y, speed in self.stars:
                size = 2 if speed > 110 else 1
                if y < settings.HEIGHT - settings.GROUND_HEIGHT:
                    self.play_surface.fill((150, 150, 150), (int(x), int(y), size, size))

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

        # Player (nave o astronauta según el modo)
        if self.game_mode == GameMode.SHIP:
            px, py = world_to_minimap(self.player.rect.centerx, self.player.rect.centery)
            pygame.draw.circle(minimap_surface, settings.COLOR_PLAYER, (px, py), 6)
            
            # Lasers
            for laser in self.player.lasers:
                lx1, ly1 = world_to_minimap(laser.rect.left, laser.rect.centery)
                lx2, ly2 = world_to_minimap(laser.rect.right, laser.rect.centery)
                pygame.draw.line(minimap_surface, settings.COLOR_LASER, (lx1, ly1), (lx2, ly2), 2)
        else:
            # Astronauta en modo plataformas
            ax, ay = world_to_minimap(self.astronaut.rect.centerx, self.astronaut.rect.centery)
            pygame.draw.circle(minimap_surface, settings.COLOR_ASTRONAUT_SUIT, (ax, ay), 5)
            
            # También mostrar la nave en el fondo
            px, py = world_to_minimap(self.player.rect.centerx, self.player.rect.centery)
            pygame.draw.circle(minimap_surface, settings.COLOR_PLAYER, (px, py), 4)

        # Meteors (solo en modo nave, no en modo plataformas)
        if self.game_mode == GameMode.SHIP:
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
            if self.game_mode == GameMode.SHIP:
                self.player.draw(target_surface)
                self.meteor_spawner.draw(target_surface)
            else:
                # Modo plataformas
                for platform in self.platforms:
                    platform.draw(target_surface)
                # Dibujar aliens
                for alien in self.aliens:
                    if alien.alive:
                        alien.draw(target_surface)
                self.astronaut.draw(target_surface)
                # Dibujar láseres del astronauta
                self.astronaut.draw_lasers(target_surface)
                # No dibujar meteoritos ni láseres en modo plataformas (están en el espacio)
                # Mostrar nave en el fondo sin láseres
                # Dibujar solo la nave sin láseres creando una copia temporal
                original_lasers = self.player.lasers
                self.player.lasers = []
                self.player.draw(target_surface)
                self.player.lasers = original_lasers
        elif self.state == GameState.PAUSED:
            if self.game_mode == GameMode.SHIP:
                self.player.draw(target_surface)
                self.meteor_spawner.draw(target_surface)
            else:
                for platform in self.platforms:
                    platform.draw(target_surface)
                # Dibujar aliens
                for alien in self.aliens:
                    if alien.alive:
                        alien.draw(target_surface)
                self.astronaut.draw(target_surface)
                self.astronaut.draw_lasers(target_surface)
                # No dibujar meteoritos ni láseres en modo plataformas (están en el espacio)
                # Dibujar nave sin láseres
                original_lasers = self.player.lasers
                self.player.lasers = []
                self.player.draw(target_surface)
                self.player.lasers = original_lasers
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
            mode_text = "Modo: Nave" if self.game_mode == GameMode.SHIP else "Modo: Plataformas"
            self.hud.draw_hud(self.screen, self.score, self.lives, footer=True)
            self.hud.draw_text(self.screen, mode_text, (settings.WIDTH - 200, settings.HEIGHT + 10), size=18, center=False)
            
            if self.game_mode == GameMode.SHIP:
                # Mostrar si se puede bajar o no
                ground_level = settings.HEIGHT - settings.GROUND_HEIGHT
                player_bottom = self.player.rect.bottom
                is_near_ground = (ground_level - settings.LANDING_DISTANCE <= player_bottom <= settings.HEIGHT)
                
                if is_near_ground:
                    self.hud.draw_text(self.screen, "Presiona E para bajar", (settings.WIDTH - 200, settings.HEIGHT + 35), size=14, center=False, color=(100, 255, 100))
                else:
                    self.hud.draw_text(self.screen, "Acércate al suelo para bajar", (settings.WIDTH - 250, settings.HEIGHT + 35), size=12, center=False, color=(255, 150, 150))
            else:
                # Verificar si el astronauta está cerca de la nave
                astronaut_center = pygame.math.Vector2(self.astronaut.rect.centerx, self.astronaut.rect.centery)
                ship_center = pygame.math.Vector2(self.player.rect.centerx, self.player.rect.centery)
                distance = (astronaut_center - ship_center).length()
                
                if distance <= settings.BOARDING_DISTANCE:
                    self.hud.draw_text(self.screen, "Presiona E para volver a la nave", (settings.WIDTH - 280, settings.HEIGHT + 35), size=12, center=False, color=(100, 255, 100))
                else:
                    self.hud.draw_text(self.screen, "Acércate a la nave para abordar", (settings.WIDTH - 280, settings.HEIGHT + 35), size=12, center=False, color=(255, 150, 150))
            
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

