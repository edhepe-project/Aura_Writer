"""
dock.py — Componente contenedor CharacterDock.
Ensambla el CharacterTreeView y CharacterContextPanel con divisor vertical.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSplitter, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal

from core.models import Character, CharacterRelation
from core.theme_manager import ThemeManager
from .tree_view import CharacterTreeView
from .context_panel import CharacterContextPanel


class CharacterDock(QWidget):
    """
    Panel de personajes:
      - Arriba: Árbol relacional con acciones CRUD
      - Abajo: Panel de contexto dinámico (apariciones por capítulo/obra/universo)
    """
    character_added = pyqtSignal(object)   # Character
    character_deleted = pyqtSignal(str)      # char_id
    character_selected = pyqtSignal(str)      # char_id
    chapter_requested = pyqtSignal(str)      # chapter_id → navegar

    def __init__(self, parent=None):
        super().__init__(parent)
        self._characters: list[Character] = []
        self._relations: list[CharacterRelation] = []
        self._obras: list = []

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QFrame()
        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 0, 0, 0)
        title_lbl = QLabel("PERSONAJES")
        hl.addWidget(title_lbl)
        hl.addStretch()
        root.addWidget(header)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setHandleWidth(1)

        # Árbol superior
        self._tree_view = CharacterTreeView(self)
        self._tree_view.character_added.connect(self.character_added)
        self._tree_view.character_deleted.connect(self._on_tree_char_deleted)
        self._tree_view.character_selected.connect(self.character_selected)
        splitter.addWidget(self._tree_view)

        # Panel inferior de contexto
        self._context_panel = CharacterContextPanel(self)
        self._context_panel.chapter_requested.connect(self.chapter_requested)
        self._context_panel.character_requested.connect(self.select_character_by_id)
        splitter.addWidget(self._context_panel)

        splitter.setSizes([420, 230])
        root.addWidget(splitter)

    def populate(self, characters: list[Character], relations: list[CharacterRelation], obras: list):
        self._characters = list(characters)
        self._relations = list(relations)
        self._obras = list(obras)
        self._tree_view.set_data(self._characters, self._relations, self._obras)

    def get_relations(self) -> list[CharacterRelation]:
        return self._tree_view._relations

    def update_appearances(self, chapters_data: list[tuple]):
        self._context_panel.update_appearances(self._tree_view._current_char, chapters_data)

    def update_context_for_chapter(self, chapter_title: str,
                                   characters_in_chapter: list[Character],
                                   obra_title: str, libro_title: str):
        self._context_panel.update_context_for_chapter(chapter_title, characters_in_chapter, obra_title, libro_title)

    def update_context_for_obra(self, obra_title: str,
                                characters_in_obra: list[Character],
                                chapter_count: int):
        self._context_panel.update_context_for_obra(obra_title, characters_in_obra, chapter_count)

    def update_context_for_libro(self, libro_title: str, obra_title: str,
                                 characters_in_libro: list[Character],
                                 chapter_count: int):
        self._context_panel.update_context_for_libro(libro_title, obra_title, characters_in_libro, chapter_count)

    def update_context_for_universe(self, title: str,
                                    all_characters: list[Character],
                                    total_chapters: int, total_obras: int):
        self._context_panel.update_context_for_universe(title, all_characters, total_chapters, total_obras)

    def get_current_char_id(self) -> str | None:
        return self._tree_view._current_char.id if self._tree_view._current_char else None

    def select_character_by_id(self, char_id: str):
        char = next((c for c in self._characters if c.id == char_id), None)
        if char:
            self._tree_view._current_char = char
            self._tree_view.select_by_char_id(char_id)
            self.character_selected.emit(char_id)

    def _on_tree_char_deleted(self, char_id: str):
        self._context_panel.clear()
        self.character_deleted.emit(char_id)

    def update_theme(self):
        self._tree_view._update_search_style(ThemeManager.is_dark())
        self._tree_view.rebuild_tree()
        self._context_panel.update_theme()

    def _save_current_card(self):
        """No-op: los datos se guardan directamente al aceptar el diálogo."""
        pass
