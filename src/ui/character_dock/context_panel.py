"""
context_panel.py — Panel de Información Contextual Dinámica (Apariciones en Capítulos, Obras y Universo).
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from core.models import Character
from core.theme_manager import ThemeManager


class CharacterContextPanel(QWidget):
    """Panel inferior dinámico que muestra apariciones de personajes o listas según la selección."""

    chapter_requested = pyqtSignal(str)       # chapter_id
    character_requested = pyqtSignal(str)     # char_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_context_type: str | None = None
        self._last_context_args: tuple | None = None
        self._build_ui()

    def _build_ui(self):
        al = QVBoxLayout(self)
        al.setContentsMargins(8, 6, 8, 6)
        al.setSpacing(4)

        self._context_label = QLabel("INFORMACIÓN CONTEXTUAL")
        al.addWidget(self._context_label)

        self._context_sublabel = QLabel("")
        self._context_sublabel.setWordWrap(True)
        self._context_sublabel.hide()
        al.addWidget(self._context_sublabel)

        self._list_appear = QListWidget()
        self._list_appear.itemDoubleClicked.connect(self._on_appearance_clicked)
        al.addWidget(self._list_appear)

    def clear(self):
        self._list_appear.clear()
        self._context_sublabel.hide()

    def update_appearances(self, current_char: Character | None, chapters_data: list[tuple]):
        self._last_context_type = "appearances"
        self._last_context_args = (current_char, chapters_data)
        self._list_appear.clear()
        if not current_char:
            return
        self._context_label.setText(f"APARICIONES DE {current_char.name.upper()}")
        self._context_sublabel.setText(
            f"👤 {current_char.name} aparece en {len(chapters_data)} capítulo(s)"
        )
        self._context_sublabel.show()
        for cap, obra_title, libro_title in chapters_data:
            item = QListWidgetItem(f"📖 {cap.title}  ·  {obra_title} › {libro_title}")
            item.setData(Qt.ItemDataRole.UserRole, cap.id)
            item.setData(Qt.ItemDataRole.UserRole + 1, "chapter")
            self._list_appear.addItem(item)

    def update_context_for_chapter(self, chapter_title: str,
                                   characters_in_chapter: list[Character],
                                   obra_title: str, libro_title: str):
        self._last_context_type = "chapter"
        self._last_context_args = (chapter_title, characters_in_chapter, obra_title, libro_title)
        self._list_appear.clear()
        self._context_label.setText("PERSONAJES EN CAPÍTULO")
        self._context_sublabel.setText(
            f"📖 {chapter_title}  ·  {obra_title} › {libro_title}\n"
            f"{len(characters_in_chapter)} personaje(s) detectado(s)"
        )
        self._context_sublabel.show()
        if not characters_in_chapter:
            item = QListWidgetItem("  (ningún personaje detectado)")
            is_dark = ThemeManager.is_dark()
            item.setForeground(QColor("#8e8e93" if is_dark else "#6b7280"))
            self._list_appear.addItem(item)
            return
        self._populate_character_list_items(characters_in_chapter)

    def update_context_for_obra(self, obra_title: str,
                                characters_in_obra: list[Character],
                                chapter_count: int):
        self._last_context_type = "obra"
        self._last_context_args = (obra_title, characters_in_obra, chapter_count)
        self._list_appear.clear()
        self._context_label.setText("PERSONAJES EN OBRA")
        self._context_sublabel.setText(
            f"📖 {obra_title}\n"
            f"{len(characters_in_obra)} personaje(s) · {chapter_count} capítulo(s)"
        )
        self._context_sublabel.show()
        if not characters_in_obra:
            item = QListWidgetItem("  (ningún personaje detectado)")
            is_dark = ThemeManager.is_dark()
            item.setForeground(QColor("#8e8e93" if is_dark else "#6b7280"))
            self._list_appear.addItem(item)
            return
        self._populate_character_list_items(characters_in_obra)

    def update_context_for_libro(self, libro_title: str, obra_title: str,
                                 characters_in_libro: list[Character],
                                 chapter_count: int):
        self._last_context_type = "libro"
        self._last_context_args = (libro_title, obra_title, characters_in_libro, chapter_count)
        self._list_appear.clear()
        self._context_label.setText("PERSONAJES EN LIBRO")
        self._context_sublabel.setText(
            f"📘 {libro_title}  ·  {obra_title}\n"
            f"{len(characters_in_libro)} personaje(s) · {chapter_count} capítulo(s)"
        )
        self._context_sublabel.show()
        if not characters_in_libro:
            item = QListWidgetItem("  (ningún personaje detectado)")
            is_dark = ThemeManager.is_dark()
            item.setForeground(QColor("#8e8e93" if is_dark else "#6b7280"))
            self._list_appear.addItem(item)
            return
        self._populate_character_list_items(characters_in_libro)

    def update_context_for_universe(self, title: str,
                                    all_characters: list[Character],
                                    total_chapters: int, total_obras: int):
        self._last_context_type = "universe"
        self._last_context_args = (title, all_characters, total_chapters, total_obras)
        self._list_appear.clear()
        self._context_label.setText("RESUMEN DEL UNIVERSO")
        self._context_sublabel.setText(
            f"{title}\n"
            f"{len(all_characters)} personaje(s) · {total_obras} obra(s) · {total_chapters} capítulo(s)"
        )
        self._context_sublabel.show()
        self._populate_character_list_items(all_characters)

    def _populate_character_list_items(self, char_list: list[Character]):
        is_dark = ThemeManager.is_dark()
        role_icons = {
            "Protagonista": "★", "Antagonista": "▲",
            "Secundario": "●", "Misterioso": "◆", "Otro": "○"
        }
        if is_dark:
            role_colors = {
                "Protagonista": "#ffd60a", "Antagonista": "#ff453a",
                "Misterioso":   "#bf5af2", "Secundario":   "#f2f2f7",
                "Otro":         "#aeaeb2"
            }
        else:
            role_colors = {
                "Protagonista": "#b45309", "Antagonista": "#dc2626",
                "Misterioso":   "#7c3aed", "Secundario":   "#111827",
                "Otro":         "#4b5563"
            }
        default_color = "#f2f2f7" if is_dark else "#111827"

        for char in char_list:
            icon = role_icons.get(char.role, "○")
            item = QListWidgetItem(f"{icon} {char.name}  ·  {char.role}")
            item.setData(Qt.ItemDataRole.UserRole, char.id)
            item.setData(Qt.ItemDataRole.UserRole + 1, "character")
            item.setForeground(QColor(role_colors.get(char.role, default_color)))
            self._list_appear.addItem(item)

    def _on_appearance_clicked(self, item: QListWidgetItem):
        item_id = item.data(Qt.ItemDataRole.UserRole)
        item_type = item.data(Qt.ItemDataRole.UserRole + 1)
        if not item_id:
            return
        if item_type == "chapter":
            self.chapter_requested.emit(item_id)
        elif item_type == "character":
            self.character_requested.emit(item_id)

    def update_theme(self):
        if self._last_context_type == "appearances" and self._last_context_args:
            self.update_appearances(*self._last_context_args)
        elif self._last_context_type == "chapter" and self._last_context_args:
            self.update_context_for_chapter(*self._last_context_args)
        elif self._last_context_type == "obra" and self._last_context_args:
            self.update_context_for_obra(*self._last_context_args)
        elif self._last_context_type == "libro" and self._last_context_args:
            self.update_context_for_libro(*self._last_context_args)
        elif self._last_context_type == "universe" and self._last_context_args:
            self.update_context_for_universe(*self._last_context_args)
