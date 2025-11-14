from __future__ import annotations

import pathlib

# Dimensiones de la ventana
WIDTH = 800
HEIGHT = 600

# Colores
COLOR_BG = (5, 5, 20)
COLOR_PLAYER = (80, 200, 255)
COLOR_METEOR = (200, 120, 60)
COLOR_LASER = (255, 255, 120)
COLOR_TEXT = (240, 240, 240)
COLOR_TEXT_SHADOW = (20, 20, 40)

# Minimap
MINIMAP_SCALE = 0.25  # porcentaje de la pantalla principal
MINIMAP_MARGIN = 16
MINIMAP_PADDING = 8
MINIMAP_WORLD_EXTRA = 680  # espacio adicional visible hacia la derecha
COLOR_MINIMAP_BG = (12, 12, 28)
COLOR_MINIMAP_BORDER = (120, 140, 200)
COLOR_MINIMAP_VIEW = (60, 90, 160)
FOOTER_HEIGHT = 120

# Configuración del jugador
PLAYER_SPEED = 350  # px/s
PLAYER_SIZE = (60, 40)
PLAYER_COOLDOWN = 0.25  # segundos entre disparos
PLAYER_INVULNERABILITY_TIME = 2.0  # segundos después de una colisión

# Configuración de meteoritos
METEOR_MIN_SPEED = 80
METEOR_MAX_SPEED = 220
METEOR_SPAWN_INTERVAL = 0.9
METEOR_SIZE_MIN = (30, 30)
METEOR_SIZE_MAX = (100, 100)
METEOR_SIZE_RANGE = (METEOR_SIZE_MIN, METEOR_SIZE_MAX)

# Configuración de los proyectiles
LASER_SPEED = 500
LASER_SIZE = (18, 6)

# Configuración del astronauta
ASTRONAUT_SPEED = 250  # px/s
ASTRONAUT_SIZE = (30, 50)
ASTRONAUT_JUMP_STRENGTH = 600  # velocidad inicial del salto (aumentado para alcanzar plataformas)
ASTRONAUT_GRAVITY = 800  # px/s²
ASTRONAUT_COOLDOWN = 0.3  # segundos entre disparos
ASTRONAUT_LASER_SPEED = 400  # px/s
ASTRONAUT_LASER_SIZE = (12, 4)
COLOR_ASTRONAUT_HELMET = (200, 200, 200)
COLOR_ASTRONAUT_SUIT = (100, 100, 150)
COLOR_ASTRONAUT_LASER = (100, 255, 100)

# Configuración de aliens
ALIEN_SIZE = (40, 40)
ALIEN_SPEED = 50  # px/s
ALIEN_PATROL_DISTANCE = 100  # distancia que patrullan en cada dirección
COLOR_ALIEN = (200, 50, 50)

# Configuración de plataformas
PLATFORM_COLOR = (120, 100, 80)
GROUND_HEIGHT = 50  # altura del suelo base
LANDING_DISTANCE = 100  # distancia máxima desde el suelo para poder aterrizar
BOARDING_DISTANCE = 120  # distancia máxima del astronauta a la nave para poder abordar

# Dificultad
DIFFICULTY_STEP = 0.02  # reducción del intervalo de generación
DIFFICULTY_MIN_INTERVAL = 0.35

# Hud / fuentes
BASE_PATH = pathlib.Path(__file__).resolve().parent.parent
ASSETS_PATH = BASE_PATH / "assets"
FONTS_PATH = ASSETS_PATH / "fonts"
DEFAULT_FONT = "PressStart2P.ttf"  # deberá agregarse manualmente si se desea

# Varios
FPS = 60

