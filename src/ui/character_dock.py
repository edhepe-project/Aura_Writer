"""
character_dock.py — Módulo retrocompatible que re-exporta CharacterDock
desde el paquete modular `src.ui.character_dock`.
"""
from ui.character_dock.dock import CharacterDock
from ui.character_dock.tree_view import CharacterTreeView
from ui.character_dock.context_panel import CharacterContextPanel

__all__ = ["CharacterDock", "CharacterTreeView", "CharacterContextPanel"]
