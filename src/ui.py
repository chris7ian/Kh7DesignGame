from __future__ import annotations

from typing import Optional, Tuple

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


class FontManager:
    def __init__(self) -> None:
        self.font_cache: dict[int, pygame.font.Font] = {}
        pygame.font.init()

    def get(self, size: int) -> pygame.font.Font:
        if size not in self.font_cache:
            path = settings.FONTS_PATH / settings.DEFAULT_FONT
            if path.exists():
                font = pygame.font.Font(path.as_posix(), size)
            else:
                font = pygame.font.SysFont("Consolas", size, bold=True)
            self.font_cache[size] = font
        return self.font_cache[size]


class HUD:
    def __init__(self, font_manager: FontManager) -> None:
        self.font_manager = font_manager

    def draw_text(
        self,
        surface: pygame.Surface,
        text: str,
        pos: Tuple[int, int],
        size: int = 24,
        center: bool = False,
        color: Tuple[int, int, int] = settings.COLOR_TEXT,
        shadow: bool = True,
    ) -> None:
        font = self.font_manager.get(size)
        render = font.render(text, True, color)
        rect = render.get_rect()
        if center:
            rect.center = pos
        else:
            rect.topleft = pos
        if shadow:
            shadow_render = font.render(text, True, settings.COLOR_TEXT_SHADOW)
            shadow_rect = shadow_render.get_rect(center=rect.center)
            shadow_rect.topleft = (rect.x + 3, rect.y + 3)
            surface.blit(shadow_render, shadow_rect)
        surface.blit(render, rect)

    def draw_hud(self, surface: pygame.Surface, score: int, lives: int, level: int = 1, *, footer: bool = False) -> None:
        if footer:
            base_y = settings.HEIGHT + settings.FOOTER_HEIGHT // 2
            offset = 28
            self.draw_text(surface, f"Puntuación: {score}", (40, base_y - offset), size=22)
            self.draw_text(surface, f"Vidas: {lives}", (40, base_y + offset), size=22)
            self.draw_text(surface, f"Nivel: {level}", (40, base_y + offset * 2), size=22, color=(150, 200, 255))
        else:
            self.draw_text(surface, f"Puntuación: {score}", (20, 20))
            self.draw_text(surface, f"Vidas: {lives}", (20, 60))
            self.draw_text(surface, f"Nivel: {level}", (20, 100), color=(150, 200, 255))
    
    def draw_objectives(self, surface: pygame.Surface, meteors_destroyed: int, required_meteors: int, 
                       aliens_alive: int, total_aliens: int, current_wave: int, total_waves: int) -> None:
        """Muestra el progreso de los objetivos del nivel"""
        base_y = settings.HEIGHT + settings.FOOTER_HEIGHT // 2
        offset = 28
        
        # Calcular ancho del minimapa para evitar superposición
        minimap_width = int(settings.WIDTH * settings.MINIMAP_SCALE)
        minimap_left = (settings.WIDTH - minimap_width) // 2
        minimap_right = minimap_left + minimap_width
        
        # Objetivos en el lado derecho del footer, asegurándose de estar fuera del minimapa
        x_pos = max(settings.WIDTH - 320, minimap_right + 20)
        
        # Progreso de meteoritos (más arriba para evitar superposición con otros textos)
        meteors_color = (100, 255, 100) if meteors_destroyed >= required_meteors else (255, 255, 255)
        meteors_text = f"Meteoritos: {meteors_destroyed}/{required_meteors}"
        if total_waves > 1:
            meteors_text += f" (Oleada {current_wave + 1}/{total_waves})"
        self.draw_text(surface, meteors_text, (x_pos, base_y - offset * 1.5), size=18, center=False, color=meteors_color)
        
        # Progreso de aliens (en la misma línea que Vidas para alineación)
        aliens_killed = total_aliens - aliens_alive
        aliens_color = (100, 255, 100) if aliens_alive == 0 else (255, 255, 255)
        self.draw_text(surface, f"Aliens: {aliens_killed}/{total_aliens}", (x_pos, base_y + offset * 0.5), size=18, center=False, color=aliens_color)

    def draw_center_message(self, surface: pygame.Surface, title: str, company: Optional[str] = None,subtitle: Optional[str] = None) -> None:
        if company:
            self.draw_text(surface, company, (settings.WIDTH // 2, settings.HEIGHT // 2 - 80), size=20, center=True)
        self.draw_text(surface, title, (settings.WIDTH // 2, settings.HEIGHT // 2 - 40), size=36, center=True)
        if subtitle:
            self.draw_text(surface, subtitle, (settings.WIDTH // 2, settings.HEIGHT // 2 + 20), size=20, center=True)

