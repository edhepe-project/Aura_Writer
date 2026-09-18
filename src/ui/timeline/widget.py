"""
widget.py — Lienzo interactivo horizontal de la Cronología Literaria.
Dibuja el eje de tiempo con marcadores conectores hacia las tarjetas de evento.
"""
from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QScrollArea, QFrame, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QPainter, QPen, QColor, QFont

from core.models import Chapter, Obra, UniverseMetadata
from core.theme_manager import ThemeManager
from .event_card import TimelineEventCard


class TimelineCanvas(QWidget):
    """
    Lienzo horizontal donde se dibuja el riel de tiempo y se disponen las tarjetas de evento.
    """
    chapter_selected = pyqtSignal(str)
    chapter_double_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cards: list[TimelineEventCard] = []
        self._events_data: list[tuple] = []  # [(chapter, obra_title, obra_color, char_names, place_names), ...]
        self._selected_chapter_id: str | None = None

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(40, 60, 40, 40)
        self._layout.setSpacing(32)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

    def set_data(self, events_data: list[tuple]):
        """
        events_data: lista de tuplas (chapter, obra_title, obra_color, char_names, place_names)
        ordenadas cronológicamente.
        """
        self._events_data = events_data
        self._rebuild()

    def _rebuild(self):
        # Limpiar tarjetas existentes
        for card in self._cards:
            card.deleteLater()
        self._cards.clear()

        while self._layout.count() > 0:
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._events_data:
            empty = QLabel("No hay capítulos o eventos con los filtros seleccionados.")
            empty.setStyleSheet("color: #8e8e93; font-style: italic; font-size: 13px; margin: 40px;")
            self._layout.addWidget(empty)
            self.update()
            return

        for chapter, obra_title, obra_color, chars, places in self._events_data:
            card = TimelineEventCard(
                chapter=chapter,
                obra_title=obra_title,
                obra_color=obra_color,
                characters_names=chars,
                places_names=places,
                parent=self
            )
            card.clicked.connect(self._on_card_clicked)
            card.double_clicked.connect(self._on_card_double_clicked)
            if chapter.id == self._selected_chapter_id:
                card.set_selected(True)
            self._cards.append(card)
            self._layout.addWidget(card)

        self.update()

    def _on_card_clicked(self, chapter_id: str):
        self._selected_chapter_id = chapter_id
        for card in self._cards:
            card.set_selected(card.chapter.id == chapter_id)
        self.chapter_selected.emit(chapter_id)

    def _on_card_double_clicked(self, chapter_id: str):
        self.chapter_double_clicked.emit(chapter_id)

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self._cards:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        is_dark = ThemeManager.is_dark()
        line_color = QColor("#ff9f0a" if is_dark else "#d97706")
        dot_bg = QColor("#1c1c1e" if is_dark else "#ffffff")

        # Dibujar la línea de tiempo principal arriba de las tarjetas
        rail_y = 35
        p_first = self._cards[0].pos()
        p_last = self._cards[-1].pos()
        start_x = max(20, p_first.x())
        end_x = p_last.x() + self._cards[-1].width() + 20

        pen = QPen(line_color, 3, Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        painter.drawLine(start_x, rail_y, end_x, rail_y)

        # Conectar cada tarjeta con un punto y línea vertical al riel
        for card in self._cards:
            card_top_center_x = card.x() + (card.width() // 2)
            card_top_y = card.y()

            # Línea conectora
            con_pen = QPen(QColor(card.obra_color), 1.5, Qt.PenStyle.DashLine)
            painter.setPen(con_pen)
            painter.drawLine(card_top_center_x, rail_y, card_top_center_x, card_top_y)

            # Nodo / Punto sobre el riel
            painter.setPen(QPen(QColor(card.obra_color), 2))
            painter.setBrush(dot_bg)
            painter.drawEllipse(QPoint(card_top_center_x, rail_y), 6, 6)

            # Micro punto central
            painter.setBrush(QColor(card.obra_color))
            painter.drawEllipse(QPoint(card_top_center_x, rail_y), 3, 3)

        painter.end()


class TimelineWidget(QWidget):
    """
    Contenedor con scroll horizontal suave para el lienzo de la cronología.
    """
    chapter_selected = pyqtSignal(str)
    chapter_double_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._canvas = TimelineCanvas()
        self._canvas.chapter_selected.connect(self.chapter_selected)
        self._canvas.chapter_double_clicked.connect(self.chapter_double_clicked)
        self._scroll.setWidget(self._canvas)

        layout.addWidget(self._scroll)

    def set_data(self, events_data: list[tuple]):
        self._canvas.set_data(events_data)

    def get_canvas(self) -> TimelineCanvas:
        return self._canvas
