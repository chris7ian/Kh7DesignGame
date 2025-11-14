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


class LevelConfig:
    """Configuración de un nivel"""
    def __init__(
        self,
        level: int,
        alien_count: int,
        alien_speed: float,
        meteor_spawn_interval: float,
        meteor_min_speed: float,
        meteor_max_speed: float,
        required_meteors: int = 0,
        meteor_waves: int = 1,
    ):
        self.level = level
        self.alien_count = alien_count
        self.alien_speed = alien_speed
        self.meteor_spawn_interval = meteor_spawn_interval
        self.meteor_min_speed = meteor_min_speed
        self.meteor_max_speed = meteor_max_speed
        self.required_meteors = required_meteors  # Meteoritos que deben destruirse
        self.meteor_waves = meteor_waves  # Número de oleadas de meteoritos
        self.meteors_destroyed = 0  # Contador de meteoritos destruidos
    
    @staticmethod
    def get_level_config(level: int) -> "LevelConfig":
        """Obtiene la configuración para un nivel específico"""
        # Dificultad progresiva para meteoritos
        base_interval = settings.METEOR_SPAWN_INTERVAL
        interval_reduction = min(0.3, level * 0.05)  # Reducir intervalo hasta un mínimo
        spawn_interval = max(0.3, base_interval - interval_reduction)
        
        # Velocidad de meteoritos aumenta con el nivel
        base_min_speed = settings.METEOR_MIN_SPEED
        base_max_speed = settings.METEOR_MAX_SPEED
        meteor_speed_increase = level * 20  # Aumentar velocidad con el nivel (más agresivo)
        min_speed = base_min_speed + meteor_speed_increase
        max_speed = base_max_speed + meteor_speed_increase
        
        # Más aliens en niveles superiores
        alien_count = min(8, 3 + level)  # Empezar con 3, máximo 8
        
        # Velocidad de aliens aumenta con el nivel
        base_alien_speed = settings.ALIEN_SPEED
        alien_speed_increase = level * 10  # Aumentar velocidad con el nivel
        alien_speed = base_alien_speed + alien_speed_increase
        
        # Meteoritos requeridos según el nivel (objetivo del nivel)
        # Niveles iniciales: menos meteoritos, niveles avanzados: más
        required_meteors = max(5, 5 + level * 2)  # Mínimo 5, aumenta con el nivel
        
        # Número de oleadas de meteoritos
        meteor_waves = 1 + (level - 1) // 3  # Más oleadas en niveles superiores
        
        return LevelConfig(
            level=level,
            alien_count=alien_count,
            alien_speed=alien_speed,
            meteor_spawn_interval=spawn_interval,
            meteor_min_speed=min_speed,
            meteor_max_speed=max_speed,
            required_meteors=required_meteors,
            meteor_waves=meteor_waves,
        )


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
        self.level = 1
        self.level_config = LevelConfig.get_level_config(1)
        self.level_complete_timer = 0.0
        self.level_complete_message_duration = 3.0
        self.current_wave = 0
        self.meteors_in_wave = 0
        self.wave_complete = False
        self._reset_starfield()
        self._setup_level()

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

    def _can_reach(self, from_rect: pygame.Rect, to_rect: pygame.Rect, max_jump_height: float, max_jump_distance: float) -> bool:
        """Verifica si se puede alcanzar una plataforma desde otra"""
        # Calcular distancia horizontal y vertical
        dx = abs((to_rect.centerx - from_rect.centerx))
        dy = from_rect.top - to_rect.top  # Positivo si to_rect está arriba
        
        # Verificar si está dentro del alcance del salto
        return dx <= max_jump_distance and dy >= 0 and dy <= max_jump_height
    
    def _create_platforms(self, level: int = 1) -> list[entities.Platform]:
        """Genera plataformas de forma procedural asegurando rutas alcanzables"""
        platforms = []
        
        # Suelo base (siempre igual)
        ground = entities.Platform(
            pygame.Rect(0, settings.HEIGHT - settings.GROUND_HEIGHT, settings.WIDTH, settings.GROUND_HEIGHT),
            settings.PLATFORM_COLOR
        )
        platforms.append(ground)
        
        # Usar el nivel como semilla para consistencia
        random.seed(level * 42)
        
        # Parámetros del salto del astronauta (basados en física del juego)
        # Altura máxima de salto aproximada: v²/(2*g) donde v=600, g=800
        max_jump_height = (settings.ASTRONAUT_JUMP_STRENGTH ** 2) / (2 * settings.ASTRONAUT_GRAVITY)
        # Distancia horizontal máxima aproximada (considerando tiempo de vuelo)
        max_jump_distance = max_jump_height * 1.5  # Factor de seguridad
        
        # Número de plataformas según el nivel
        num_platforms = 5 + min(4, level // 2)
        
        ground_level = settings.HEIGHT - settings.GROUND_HEIGHT
        min_y = 120
        max_y = ground_level - 60
        
        # Generar plataformas en capas verticales
        platform_rects = []
        
        # Capa 1: Plataformas cerca del suelo (accesibles desde el suelo)
        layer1_count = max(2, num_platforms // 3)
        for i in range(layer1_count):
            y = ground_level - random.randint(80, 140)
            x = random.randint(40, settings.WIDTH - 180)
            w = random.randint(120, 200)
            if x + w > settings.WIDTH - 20:
                w = settings.WIDTH - x - 20
            platform_rects.append(pygame.Rect(x, y, w, 20))
        
        # Capas superiores: generar proceduralmente asegurando conectividad
        remaining_platforms = num_platforms - layer1_count
        layers = []
        
        # Dividir el espacio vertical en capas
        num_layers = min(4, max(2, remaining_platforms // 2))
        layer_height = (max_y - min_y) / num_layers
        
        for layer_idx in range(num_layers):
            layer_y_base = min_y + layer_height * layer_idx
            layer_y_range = layer_height * 0.6  # Variación dentro de la capa
            layers.append((layer_y_base, layer_y_range))
        
        # Generar plataformas en cada capa asegurando conectividad
        for layer_idx, (layer_y_base, layer_y_range) in enumerate(layers):
            platforms_in_layer = remaining_platforms // num_layers
            if layer_idx == num_layers - 1:
                platforms_in_layer += remaining_platforms % num_layers
            
            for _ in range(platforms_in_layer):
                attempts = 0
                max_attempts = 50
                valid_platform = False
                
                while not valid_platform and attempts < max_attempts:
                    attempts += 1
                    
                    # Generar posición y tamaño
                    y = int(layer_y_base + random.uniform(-layer_y_range/2, layer_y_range/2))
                    y = max(min_y, min(max_y, y))
                    
                    x = random.randint(30, settings.WIDTH - 150)
                    w = random.randint(100, 220)
                    if x + w > settings.WIDTH - 20:
                        w = settings.WIDTH - x - 20
                    
                    new_rect = pygame.Rect(x, y, w, 20)
                    
                    # Verificar que no se solape con plataformas existentes
                    overlaps = False
                    for existing in platform_rects:
                        if new_rect.colliderect(existing):
                            overlaps = True
                            break
                    
                    if overlaps:
                        continue
                    
                    # Verificar conectividad: debe ser alcanzable desde al menos una plataforma existente
                    # o desde el suelo si es la primera capa
                    reachable = False
                    
                    if layer_idx == 0:
                        # Primera capa: debe ser alcanzable desde el suelo
                        ground_rect = pygame.Rect(0, ground_level, settings.WIDTH, 1)
                        reachable = self._can_reach(ground_rect, new_rect, max_jump_height, max_jump_distance)
                    else:
                        # Capas superiores: debe ser alcanzable desde al menos una plataforma anterior
                        for existing in platform_rects:
                            if self._can_reach(existing, new_rect, max_jump_height, max_jump_distance):
                                reachable = True
                                break
                    
                    if reachable:
                        platform_rects.append(new_rect)
                        valid_platform = True
                
                # Si no se encontró una plataforma válida después de muchos intentos,
                # crear una garantizada conectada a la última plataforma
                if not valid_platform and platform_rects:
                    last_platform = platform_rects[-1]
                    y = int(layer_y_base)
                    # Posicionar cerca de la última plataforma pero alcanzable
                    x_offset = random.randint(-int(max_jump_distance * 0.7), int(max_jump_distance * 0.7))
                    x = max(30, min(settings.WIDTH - 150, last_platform.centerx + x_offset))
                    w = random.randint(100, 180)
                    if x + w > settings.WIDTH - 20:
                        w = settings.WIDTH - x - 20
                    
                    new_rect = pygame.Rect(x, y, w, 20)
                    # Verificar solapamiento
                    overlaps = any(new_rect.colliderect(p) for p in platform_rects)
                    if not overlaps:
                        platform_rects.append(new_rect)
        
        # Crear las plataformas
        for rect in platform_rects:
            platform = entities.Platform(rect, settings.PLATFORM_COLOR)
            platforms.append(platform)
        
        return platforms

    def _create_aliens(self, level_config: LevelConfig) -> None:
        """Crea aliens en algunas plataformas según la configuración del nivel"""
        self.aliens.clear()
        # Obtener todas las plataformas excepto el suelo base
        available_platforms = [p for p in self.platforms if p.rect.y < settings.HEIGHT - settings.GROUND_HEIGHT]
        
        if not available_platforms:
            return
        
        # Seleccionar plataformas aleatorias para aliens
        num_aliens = min(level_config.alien_count, len(available_platforms))
        selected_platforms = random.sample(available_platforms, num_aliens)
        
        for platform in selected_platforms:
            # Crear alien en el centro de la plataforma con velocidad del nivel
            alien = entities.Alien((platform.rect.centerx, platform.rect.y), platform, level_config.alien_speed)
            self.aliens.append(alien)
    
    def _setup_level(self) -> None:
        """Configura el nivel actual"""
        self.level_config = LevelConfig.get_level_config(self.level)
        self.platforms = self._create_platforms(self.level)
        self._create_aliens(self.level_config)
        
        # Configurar spawner de meteoritos según el nivel
        self.meteor_spawner.spawn_interval = self.level_config.meteor_spawn_interval
        self.meteor_spawner.level_config = self.level_config
        
        # Resetear variables de oleadas y objetivos
        self.level_config.meteors_destroyed = 0
        self.current_wave = 0
        self.meteors_in_wave = 0
        self.wave_complete = False
        self.meteor_spawner.meteors.clear()  # Limpiar meteoritos anteriores
        
        # Resetear posición del jugador
        if self.game_mode == GameMode.SHIP:
            self.player.rect.center = (int(settings.WIDTH * 0.15), settings.HEIGHT // 2)
        else:
            ground_level = settings.HEIGHT - settings.GROUND_HEIGHT
            self.astronaut.rect.x = settings.WIDTH // 2
            self.astronaut.rect.y = ground_level - self.astronaut.rect.height
            self.astronaut.velocity = pygame.math.Vector2(0, 0)
        
        self.level_complete_timer = 0.0

    def reset(self) -> None:
        self.game_mode = GameMode.SHIP
        self.player = entities.Player((int(settings.WIDTH * 0.15), settings.HEIGHT // 2))
        self.astronaut = entities.Astronaut((settings.WIDTH // 2, 100))
        self.meteor_spawner = entities.MeteorSpawner()
        self.score = 0
        self.lives = 3
        self.time_accumulator = 0.0
        self.level = 1
        self.level_complete_timer = 0.0
        self._reset_starfield()
        self._setup_level()

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
            
            # Generar meteoritos hasta alcanzar el objetivo requerido
            # Las oleadas son solo organizativas, no bloquean el progreso
            meteors_destroyed = self.level_config.meteors_destroyed
            required_meteors = self.level_config.required_meteors
            
            # Solo generar meteoritos si aún no se ha alcanzado el objetivo
            if meteors_destroyed < required_meteors:
                # Si la oleada actual está completa y no hay meteoritos, avanzar a la siguiente oleada
                if self.wave_complete and len(self.meteor_spawner.meteors) == 0:
                    if self.current_wave < self.level_config.meteor_waves - 1:
                        # Avanzar a la siguiente oleada
                        self.current_wave += 1
                        self.meteors_in_wave = 0
                        self.wave_complete = False
                        self.meteor_spawner.timer = 0.0
                    else:
                        # Todas las oleadas completadas, pero aún faltan meteoritos
                        # Resetear para continuar generando
                        self.meteors_in_wave = 0
                        self.wave_complete = False
                
                # Siempre generar meteoritos si aún faltan por destruir
                # (sin importar el estado de las oleadas)
                self.meteor_spawner.update(dt)
                
                # Actualizar contador de meteoritos generados en la oleada actual (solo para display)
                if self.current_wave < self.level_config.meteor_waves:
                    meteors_per_wave = self.level_config.required_meteors // self.level_config.meteor_waves
                    if self.current_wave == self.level_config.meteor_waves - 1:
                        meteors_per_wave += self.level_config.required_meteors % self.level_config.meteor_waves
                    
                    # Contar meteoritos generados en esta oleada (solo para referencia)
                    if not self.wave_complete:
                        current_meteors = len(self.meteor_spawner.meteors)
                        if current_meteors > self.meteors_in_wave:
                            self.meteors_in_wave = current_meteors
                        
                        # Marcar oleada como completa cuando se hayan generado suficientes
                        # (pero esto no bloquea la generación si aún faltan meteoritos por destruir)
                        if self.meteors_in_wave >= meteors_per_wave:
                            self.wave_complete = True
            else:
                # Objetivo alcanzado, solo actualizar meteoritos existentes
                for meteor in self.meteor_spawner.meteors:
                    meteor.update(dt)
                self.meteor_spawner.meteors = [m for m in self.meteor_spawner.meteors if not m.is_offscreen()]

            # Colisiones láser - meteorito
            for laser in list(self.player.lasers):
                for meteor in list(self.meteor_spawner.meteors):
                    if laser.rect.colliderect(meteor.rect):
                        self.player.lasers.remove(laser)
                        self.meteor_spawner.meteors.remove(meteor)
                        self.score += 10
                        # Contar meteorito destruido
                        self.level_config.meteors_destroyed += 1
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
        
        # Verificar si el nivel está completo (objetivos combinados)
        if self.level_complete_timer == 0.0:
            alive_aliens = sum(1 for alien in self.aliens if alien.alive)
            meteors_destroyed = self.level_config.meteors_destroyed
            
            # El nivel se completa cuando:
            # 1. Todos los aliens están muertos (modo plataformas)
            # 2. Se han destruido todos los meteoritos requeridos (modo nave)
            aliens_complete = alive_aliens == 0
            meteors_complete = meteors_destroyed >= self.level_config.required_meteors
            
            if aliens_complete and meteors_complete:
                # Nivel completado
                self.level_complete_timer = self.level_complete_message_duration
        
        # Manejar transición de nivel
        if self.level_complete_timer > 0.0:
            self.level_complete_timer -= dt
            if self.level_complete_timer <= 0.0:
                # Avanzar al siguiente nivel
                self.level += 1
                self._setup_level()
                # Bonus por completar nivel
                self.score += 50 * self.level

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
            
            # Mostrar mensaje de nivel completado
            if self.level_complete_timer > 0.0:
                self.hud.draw_center_message(
                    target_surface,
                    f"¡Nivel {self.level} Completado!",
                    f"Avanzando al Nivel {self.level + 1}...",
                    None,
                )
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
            # Dibujar minimapa primero para que los textos queden encima
            self.draw_minimap()
            
            mode_text = "Modo: Nave" if self.game_mode == GameMode.SHIP else "Modo: Plataformas"
            self.hud.draw_hud(self.screen, self.score, self.lives, self.level, footer=True)
            
            # Mostrar objetivos del nivel
            alive_aliens = sum(1 for alien in self.aliens if alien.alive)
            total_aliens = len(self.aliens)
            self.hud.draw_objectives(
                self.screen,
                self.level_config.meteors_destroyed,
                self.level_config.required_meteors,
                alive_aliens,
                total_aliens,
                self.current_wave,
                self.level_config.meteor_waves
            )
            
            # Modo y mensajes de acción en el lado izquierdo del footer para evitar superposición con minimapa
            footer_center_y = settings.HEIGHT + settings.FOOTER_HEIGHT // 2
            # Calcular posición izquierda del minimapa para evitar superposición
            minimap_width = int(settings.WIDTH * settings.MINIMAP_SCALE)
            minimap_left = (settings.WIDTH - minimap_width) // 2
            # Colocar textos a la izquierda del minimapa, pero no más a la izquierda que el borde de la pantalla
            left_text_x = max(40, minimap_left - 200)
            
            self.hud.draw_text(self.screen, mode_text, (left_text_x, footer_center_y - 40), size=18, center=False)
            
            if self.game_mode == GameMode.SHIP:
                # Mostrar si se puede bajar o no
                ground_level = settings.HEIGHT - settings.GROUND_HEIGHT
                player_bottom = self.player.rect.bottom
                is_near_ground = (ground_level - settings.LANDING_DISTANCE <= player_bottom <= settings.HEIGHT)
                
                if is_near_ground:
                    self.hud.draw_text(self.screen, "Presiona E para bajar", (left_text_x, footer_center_y + 10), size=14, center=False, color=(100, 255, 100))
                else:
                    self.hud.draw_text(self.screen, "Acércate al suelo para bajar", (left_text_x, footer_center_y + 10), size=12, center=False, color=(255, 150, 150))
            else:
                # Verificar si el astronauta está cerca de la nave
                astronaut_center = pygame.math.Vector2(self.astronaut.rect.centerx, self.astronaut.rect.centery)
                ship_center = pygame.math.Vector2(self.player.rect.centerx, self.player.rect.centery)
                distance = (astronaut_center - ship_center).length()
                
                if distance <= settings.BOARDING_DISTANCE:
                    self.hud.draw_text(self.screen, "Presiona E para volver a la nave", (left_text_x, footer_center_y + 10), size=12, center=False, color=(100, 255, 100))
                else:
                    self.hud.draw_text(self.screen, "Acércate a la nave para abordar", (left_text_x, footer_center_y + 10), size=12, center=False, color=(255, 150, 150))
        elif self.state == GameState.PAUSED:
            self.hud.draw_hud(self.screen, self.score, self.lives, self.level, footer=True)
            self.draw_minimap()
        elif self.state == GameState.GAME_OVER:
            self.hud.draw_hud(self.screen, self.score, self.lives, self.level, footer=True)
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

