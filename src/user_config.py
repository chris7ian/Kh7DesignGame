"""User-editable options persisted to a config file."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

try:
    from . import settings
except ImportError:
    import settings  # type: ignore

CONFIG_FILENAME = "config.json"
CONFIG_APP_NAME = "Interste11ar"
CONFIG_MIN = {
    "music_volume": 0.0,
    "background_opacity": 50,
    "fps_limit": 30,
}
CONFIG_MAX = {
    "music_volume": 1.0,
    "background_opacity": 255,
    "fps_limit": 120,
}
FPS_CHOICES = (30, 60, 120)
# Widescreen-first resolution presets (16:9 or common laptop)
RESOLUTION_CHOICES = [
    (1280, 720),   # 720p
    (1920, 1080),  # 1080p
    (2560, 1440),  # 1440p
    (1366, 768),   # common laptop
    (3840, 2160),  # 4K
    (800, 600),    # legacy 4:3
]


def _config_path() -> Path:
    """Config file path. When frozen (e.g. .app), use Application Support so it's writable."""
    if getattr(sys, "frozen", False):
        if sys.platform == "darwin":
            base = Path(os.environ.get("HOME", "")) / "Library" / "Application Support" / CONFIG_APP_NAME
        else:
            base = Path(__file__).resolve().parent.parent
        base.mkdir(parents=True, exist_ok=True)
        return base / CONFIG_FILENAME
    return Path(__file__).resolve().parent.parent / CONFIG_FILENAME


def load() -> dict:
    """Load user config from file. Returns dict with music_volume, background_opacity, fps_limit."""
    path = _config_path()
    if not path.exists():
        return _defaults()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return _defaults()
    return _validate(data)


def _defaults() -> dict:
    w = getattr(settings, "WIDTH", 800)
    h = getattr(settings, "HEIGHT", 600)
    return {
        "music_volume": 0.4,
        "background_opacity": getattr(settings, "BACKGROUND_OPACITY", 90),
        "fps_limit": getattr(settings, "FPS", 60),
        "width": w,
        "height": h,
    }


def _validate(data: dict) -> dict:
    out = _defaults()
    if isinstance(data.get("music_volume"), (int, float)):
        v = float(data["music_volume"])
        out["music_volume"] = max(0.0, min(1.0, v))
    if isinstance(data.get("background_opacity"), (int, float)):
        v = int(data["background_opacity"])
        out["background_opacity"] = max(50, min(255, v))
    if isinstance(data.get("fps_limit"), (int, float)):
        v = int(data["fps_limit"])
        if v in FPS_CHOICES:
            out["fps_limit"] = v
        else:
            out["fps_limit"] = min(FPS_CHOICES, key=lambda x: abs(x - v))
    if isinstance(data.get("width"), (int, float)) and isinstance(data.get("height"), (int, float)):
        w, h = int(data["width"]), int(data["height"])
        if (w, h) in RESOLUTION_CHOICES:
            out["width"], out["height"] = w, h
        else:
            out["width"] = max(640, min(3840, w))
            out["height"] = max(480, min(2160, h))
    return out


def save(config: dict) -> None:
    """Save config to file."""
    path = _config_path()
    data = _validate(config)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass
