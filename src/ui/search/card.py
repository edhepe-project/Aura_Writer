"""
card.py — Tarjeta interactiva y visual para elementos del resultado de búsqueda.
"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal

from core.theme_manager import ThemeManager
from ui.search.engine import escape_html, highlight_text


class SearchResultCard(QFrame):
    """Fila de resultado interactiva con fondo alternado y efectos de hover."""
    activated = pyqtSignal(str, str)   # (item_id, item_type)

    _count = 0   # contador de instancias para alternar colores

    def __init__(self, icon: str, title: str, location: str, snippet: str,
                 query: str, item_id: str, item_type: str, is_regex: bool = False, parent=None):
        super().__init__(parent)
        SearchResultCard._count += 1
        self._item_id = item_id
        self._item_type = item_type
        self._is_regex = is_regex

        is_dark = ThemeManager.is_dark()

        if is_dark:
            self._even_bg = "#1c1c1e"
            self._odd_bg = "#242426"
            self._hover_bg = "#2c2c2e"
            self._border_col = "#2c2c2e"
            self._hover_border = "#3a3a3c"
            self._hover_bar = "#636366"
            text_col = "#f2f2f7"
            sub_col = "#8e8e93"
            loc_col = "#636366"
        else:
            self._even_bg = "#f5f0ea"
            self._odd_bg = "#ede8e1"
            self._hover_bg = "#dedad2"
            self._border_col = "#d4cfc8"
            self._hover_border = "#c4bfb8"
            self._hover_bar = "#9a9490"
            text_col = "#1a1a2e"
            sub_col = "#7a7a8a"
            loc_col = "#7a7a8a"

        self._bg = self._even_bg if SearchResultCard._count % 2 == 0 else self._odd_bg

        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame {{
                background: {self._bg};
                border: none;
                border-bottom: 1px solid {self._border_col};
            }}
        """)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(3)

        # Título
        t = QLabel(f"<b>{escape_html(icon)} {escape_html(title)}</b>")
        t.setTextFormat(Qt.TextFormat.RichText)
        t.setStyleSheet(f"color:{text_col}; font-size:13px; background:transparent;")
        layout.addWidget(t)

        # Ubicación
        loc = QLabel(f"{'  '}{escape_html(location)}")
        loc.setStyleSheet(f"color:{loc_col}; font-size:11px; background:transparent;")
        layout.addWidget(loc)

        # Snippet
        if snippet:
            hl = highlight_text(snippet, query, is_dark=is_dark, is_regex=self._is_regex)
            snip = QLabel(hl)
            snip.setTextFormat(Qt.TextFormat.RichText)
            snip.setWordWrap(True)
            snip.setStyleSheet(f"color:{sub_col}; font-size:11px; background:transparent;")
            layout.addWidget(snip)

    def enterEvent(self, event):
        self.setStyleSheet(f"""
            QFrame {{
                background: {self._hover_bg};
                border: none;
                border-bottom: 1px solid {self._hover_border};
                border-left: 3px solid {self._hover_bar};
            }}
        """)
        super().enterEvent(event)

    def leaveEvent(self, a0):
        event = a0
        self.setStyleSheet(f"""
            QFrame {{
                background: {self._bg};
                border: none;
                border-bottom: 1px solid {self._border_col};
            }}
        """)
        super().leaveEvent(event)

    def mousePressEvent(self, a0):
        event = a0
        if event.button() == Qt.MouseButton.LeftButton:
            self.activated.emit(self._item_id, self._item_type)
        super().mousePressEvent(event)
