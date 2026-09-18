"""
event_card.py — Tarjeta interactiva de evento/capítulo en la línea temporal.
"""
from __future__ import annotations
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor

from core.models import Chapter
from core.theme_manager import ThemeManager


class TimelineEventCard(QFrame):
    """
    Tarjeta visual que representa un hito o capítulo en el timeline cronológico.
    """
    clicked = pyqtSignal(str)          # chapter_id
    double_clicked = pyqtSignal(str)   # chapter_id

    def __init__(self, chapter: Chapter, obra_title: str, obra_color: str,
                 characters_names: list[str], places_names: list[str], parent=None):
        super().__init__(parent)
        self.chapter = chapter
        self.obra_title = obra_title
        self.obra_color = obra_color or "#0a84ff"
        self.characters_names = characters_names
        self.places_names = places_names
        self._selected = False

        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedWidth(240)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Header con Pill de Obra y Orden / Fecha
        top_row = QHBoxLayout()
        top_row.setSpacing(6)

        self._obra_pill = QLabel(self.obra_title.upper())
        self._obra_pill.setStyleSheet(f"""
            QLabel {{
                background-color: {self.obra_color}22;
                color: {self.obra_color};
                border: 1px solid {self.obra_color}55;
                border-radius: 4px;
                padding: 2px 6px;
                font-size: 9px;
                font-weight: bold;
            }}
        """)
        top_row.addWidget(self._obra_pill)
        top_row.addStretch()

        order_text = f"#{self.chapter.in_world_order}" if self.chapter.in_world_order else ""
        self._order_label = QLabel(order_text)
        self._order_label.setStyleSheet("font-size: 10px; color: #8e8e93; font-weight: bold;")
        top_row.addWidget(self._order_label)
        layout.addLayout(top_row)

        # Título del capítulo
        self._title_label = QLabel(self.chapter.title)
        self._title_label.setWordWrap(True)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(11)
        self._title_label.setFont(title_font)
        layout.addWidget(self._title_label)

        # Fecha en el mundo (diegética)
        date_text = self.chapter.in_world_date.strip() or "Fecha sin definir"
        self._date_label = QLabel(f"⏳ {date_text}")
        self._date_label.setStyleSheet("font-size: 11px; color: #e67e22; font-style: italic;")
        self._date_label.setWordWrap(True)
        layout.addWidget(self._date_label)

        # Tags de Lugares presentes
        if self.places_names:
            places_txt = " • ".join(self.places_names[:3])
            if len(self.places_names) > 3:
                places_txt += f" (+{len(self.places_names)-3})"
            self._places_label = QLabel(f"🏰 {places_txt}")
            self._places_label.setStyleSheet("font-size: 10px; color: #30d158;")
            self._places_label.setWordWrap(True)
            layout.addWidget(self._places_label)

        # Tags de Personajes presentes
        if self.characters_names:
            chars_txt = ", ".join(self.characters_names[:3])
            if len(self.characters_names) > 3:
                chars_txt += f" (+{len(self.characters_names)-3})"
            self._chars_label = QLabel(f"👤 {chars_txt}")
            self._chars_label.setStyleSheet("font-size: 10px; color: #8e8e93;")
            self._chars_label.setWordWrap(True)
            layout.addWidget(self._chars_label)

        self._apply_theme()

    def set_selected(self, selected: bool):
        self._selected = selected
        self._apply_theme()

    def _apply_theme(self):
        is_dark = ThemeManager.is_dark()
        bg = "#2c2c2e" if is_dark else "#ffffff"
        fg = "#f2f2f7" if is_dark else "#1c1c1e"
        border_color = self.obra_color if self._selected else ("#3a3a3c" if is_dark else "#d1d1d6")
        border_width = "2px" if self._selected else "1px"

        self.setStyleSheet(f"""
            TimelineEventCard {{
                background-color: {bg};
                color: {fg};
                border: {border_width} solid {border_color};
                border-top: 4px solid {self.obra_color};
                border-radius: 8px;
            }}
            TimelineEventCard:hover {{
                border-color: {self.obra_color};
            }}
        """)
        self._title_label.setStyleSheet(f"color: {fg}; font-weight: bold;")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.chapter.id)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.chapter.id)
        super().mouseDoubleClickEvent(event)
