#!/usr/bin/env python3
"""
Launcher for Interste11ar. Use this as the entry point for PyInstaller
so that the game runs both as a package (python -m src.main) and from
the built .app bundle.
"""
from __future__ import annotations

from src.main import main

if __name__ == "__main__":
    main()
