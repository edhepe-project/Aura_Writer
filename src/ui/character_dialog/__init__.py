"""
src/ui/character_dialog — Subpaquete modularizado para diálogos y pestañas de edición de personajes.
"""

from ui.character_dialog.tab_profile import CharacterProfileTab
from ui.character_dialog.tab_relations import CharacterRelationsTab
from ui.character_dialog.dialog import CharacterEditDialog

__all__ = [
    "CharacterProfileTab",
    "CharacterRelationsTab",
    "CharacterEditDialog",
]
