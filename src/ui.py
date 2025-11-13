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

    def draw_hud(self, surface: pygame.Surface, score: int, lives: int, *, footer: bool = False) -> None:
        if footer:
            base_y = settings.HEIGHT + settings.FOOTER_HEIGHT // 2
            offset = 28
            self.draw_text(surface, f"Puntuación: {score}", (40, base_y - offset), size=22)
            self.draw_text(surface, f"Vidas: {lives}", (40, base_y + offset), size=22)
        else:
            self.draw_text(surface, f"Puntuación: {score}", (20, 20))
            self.draw_text(surface, f"Vidas: {lives}", (20, 60))

    def draw_center_message(self, surface: pygame.Surface, title: str, company: Optional[str] = None,subtitle: Optional[str] = None) -> None:
        if company:
            self.draw_text(surface, company, (settings.WIDTH // 2, settings.HEIGHT // 2 - 80), size=20, center=True)
        self.draw_text(surface, title, (settings.WIDTH // 2, settings.HEIGHT // 2 - 40), size=36, center=True)
        if subtitle:
            self.draw_text(surface, subtitle, (settings.WIDTH // 2, settings.HEIGHT // 2 + 20), size=20, center=True)

