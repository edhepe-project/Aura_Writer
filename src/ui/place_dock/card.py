"""
card.py — Tarjeta individual interactiva para representar un Lugar en el PlaceDock.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QEvent
from PyQt6.QtGui import QColor, QFont
import qtawesome as qta

from core.models import Place, PLACE_ICONS
from core.theme_manager import ThemeManager


class PlaceCard(QFrame):
    """Tarjeta individual que muestra un lugar con su categoría, nombre y acciones rápidas."""
    clicked = pyqtSignal(str)       # place_id
    edit_requested = pyqtSignal(str) # place_id
    delete_requested = pyqtSignal(str) # place_id

    def __init__(self, place: Place, parent_name: str = "", parent=None):
        super().__init__(parent)
        self.place = place
        self.parent_name = parent_name
        self._is_selected = False
        self._build_ui()
        self._apply_style()

    def _build_ui(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        # Icono de categoría
        icon_val = PLACE_ICONS.get(self.place.category, "📍")
        self._icon_lbl = QLabel()
        if "." in icon_val:
            icon_color = "#ffd60a" if ThemeManager.is_dark() else "#d97706"
            self._icon_lbl.setPixmap(qta.icon(icon_val, color=icon_color).pixmap(20, 20))
        else:
            self._icon_lbl.setText(icon_val)
            self._icon_lbl.setStyleSheet("font-size: 16px; background: transparent;")
        self._icon_lbl.setFixedWidth(24)
        self._icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._icon_lbl)

        # Información textual (Nombre y Jerarquía/Atmósfera)
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setContentsMargins(0, 0, 0, 0)

        self._name_lbl = QLabel(self.place.name or "Sin nombre")
        name_font = QFont()
        name_font.setBold(True)
        name_font.setPointSize(10)
        self._name_lbl.setFont(name_font)
        text_layout.addWidget(self._name_lbl)

        sub_parts = []
        if self.place.category:
            sub_parts.append(self.place.category)
        if self.parent_name:
            sub_parts.append(f"en {self.parent_name}")
        elif self.place.climate_atmosphere:
            sub_parts.append(self.place.climate_atmosphere[:35] + ("..." if len(self.place.climate_atmosphere) > 35 else ""))

        sub_text = " • ".join(sub_parts) if sub_parts else "Escenario general"
        self._sub_lbl = QLabel(sub_text)
        sub_font = QFont()
        sub_font.setPointSize(8)
        self._sub_lbl.setFont(sub_font)
        text_layout.addWidget(self._sub_lbl)

        layout.addLayout(text_layout, 1)

        # Botones de acción rápida
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(2)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        self._btn_edit = QPushButton()
        self._btn_edit.setIcon(qta.icon("fa5s.edit", color="#0a84ff" if ThemeManager.is_dark() else "#007aff"))
        self._btn_edit.setFixedSize(24, 24)
        self._btn_edit.setToolTip("Editar escenario")
        self._btn_edit.clicked.connect(lambda: self.edit_requested.emit(self.place.id))
        btn_layout.addWidget(self._btn_edit)

        self._btn_del = QPushButton()
        self._btn_del.setIcon(qta.icon("fa5s.trash-alt", color="#ff453a" if ThemeManager.is_dark() else "#ff3b30"))
        self._btn_del.setFixedSize(24, 24)
        self._btn_del.setToolTip("Eliminar escenario")
        self._btn_del.clicked.connect(lambda: self.delete_requested.emit(self.place.id))
        btn_layout.addWidget(self._btn_del)

        layout.addLayout(btn_layout)

    def set_selected(self, selected: bool):
        self._is_selected = selected
        self._apply_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.place.id)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.edit_requested.emit(self.place.id)
        super().mouseDoubleClickEvent(event)

    def _apply_style(self):
        is_dark = ThemeManager.is_dark()
        if self._is_selected:
            bg = "#3a3a3c" if is_dark else "#e5e0d8"
            border = "#ffd60a" if is_dark else "#d97706"
        else:
            bg = "#252528" if is_dark else "#fdfcf9"
            border = "#3a3a3c" if is_dark else "#e0dbd3"

        fg_name = "#f2f2f7" if is_dark else "#1c1c1e"
        fg_sub = "#8e8e93" if is_dark else "#6e6e73"

        self.setStyleSheet(f"""
            PlaceCard {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 8px;
            }}
            PlaceCard:hover {{
                border: 1px solid {'#ffd60a' if is_dark else '#d97706'};
                background-color: {'#2c2c2e' if is_dark else '#f5f0ea'};
            }}
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 4px;
                padding: 2px;
            }}
            QPushButton:hover {{
                background: {'rgba(255,255,255,0.1)' if is_dark else 'rgba(0,0,0,0.06)'};
            }}
        """)
        self._name_lbl.setStyleSheet(f"color: {fg_name};")
        self._sub_lbl.setStyleSheet(f"color: {fg_sub};")
