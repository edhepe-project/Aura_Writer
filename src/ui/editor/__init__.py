"""
Paquete modular del editor principal de Aura Writer.
"""
from .editor_view import AuraEditor
from .context_menu import EditorContextMenu

__all__ = ["AuraEditor", "EditorContextMenu"]
