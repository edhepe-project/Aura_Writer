"""
editor.py — Módulo retrocompatible que re-exporta AuraEditor
desde el paquete modular `src.ui.editor`.
"""
from ui.editor.editor_view import AuraEditor
from ui.editor.context_menu import EditorContextMenu

__all__ = ["AuraEditor", "EditorContextMenu"]
