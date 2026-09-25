"""
presence_grid/dialog.py - Dialogo principal de la Cuadricula de Presencias.

Este modulo solo contiene PresenceGridDialog (el contenedor del dialogo).
La logica de la cuadricula esta en grid_widget.py y place_picker.py.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QApplication,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor

from core.theme_manager import ThemeManager
from .grid_widget import _PresenceGridWidget


# ---------------------------------------------------------------------------
#  Dialogo principal
# ---------------------------------------------------------------------------
class PresenceGridDialog(QDialog):
    """
    Dialogo independiente — Cuadricula de Presencias con columna congelada.
    Filas = personajes (por rol), Columnas = capitulos (cronologico).
    La columna de personajes y el header de capitulos permanecen fijos al hacer scroll.
    """

    def __init__(self, project_manager, parent=None):
        super().__init__(parent)
        self._pm = project_manager
        self.setWindowTitle("Cuadricula de Presencias")
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinMaxButtonsHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        screen = QApplication.primaryScreen().availableGeometry()
        w = min(1400, int(screen.width()  * 0.90))
        h = min(860,  int(screen.height() * 0.88))
        self.resize(w, h)

        is_dark = ThemeManager.is_dark()
        bg = "#121214" if is_dark else "#f4f6fa"
        self.setStyleSheet(f"QDialog {{ background: {bg}; }}")
        self._setup_ui(is_dark)
        self._grid_widget.build()

    def _setup_ui(self, is_dark: bool) -> None:
        fg     = "#f2f2f7" if is_dark else "#1c1e21"
        bord   = "#2c2c2e" if is_dark else "#d1d5db"
        bg_tb  = "#1a1a1c" if is_dark else "#ffffff"
        sub    = "#8e8e93" if is_dark else "#6b7280"
        atlas_col = "#ffd60a" if is_dark else "#d97706"

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # -- Toolbar ----------------------------------------------------------
        tb = QFrame()
        tb.setFixedHeight(52)
        tb.setStyleSheet(f"QFrame {{ background: {bg_tb}; border-bottom: 1px solid {bord}; }}")
        tbl = QHBoxLayout(tb)
        tbl.setContentsMargins(16, 0, 16, 0)
        tbl.setSpacing(12)

        tl = QLabel("Cuadrícula de Presencias")
        tl.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {atlas_col};")
        tbl.addWidget(tl)

        sl = QLabel("Filas = personajes  |  Columnas = capítulos")
        sl.setStyleSheet(f"font-size: 11px; color: {sub}; font-weight: 500;")
        tbl.addWidget(sl)
        tbl.addStretch()

        # Pastillas de leyenda
        if is_dark:
            pills = [("Presente", "#30d158"), ("En tránsito", "#0a84ff"), ("Salida", "#ff453a")]
        else:
            pills = [("Presente", "#16a34a"), ("En tránsito", "#2563eb"), ("Salida", "#dc2626")]

        for lbl, col in pills:
            pill = QLabel(f"  {lbl}")
            pill.setStyleSheet(
                f"font-size: 11px; color: {col}; font-weight: bold; "
                f"border: 1px solid {col}44; border-radius: 6px; padding: 3px 10px; background: {col}18;"
            )
            tbl.addWidget(pill)

        root.addWidget(tb)

        # -- Cuadricula -------------------------------------------------------
        self._grid_widget = _PresenceGridWidget(self._pm)
        root.addWidget(self._grid_widget, stretch=1)

        # -- Barra inferior ---------------------------------------------------
        bot = QFrame()
        bot.setFixedHeight(44)
        bot.setStyleSheet(f"QFrame {{ background: {bg_tb}; border-top: 1px solid {bord}; }}")
        bl = QHBoxLayout(bot)
        bl.setContentsMargins(16, 0, 16, 0)
        bl.setSpacing(12)

        hl = QLabel("Clic para asignar ubicación   |   Clic derecho para limpiar")
        hl.setStyleSheet(f"font-size: 11px; color: {sub}; font-weight: 500;")
        bl.addWidget(hl)
        bl.addStretch()

        btn_bg = "#2c2c2e" if is_dark else "#e5e7eb"
        btn_fg = "#f2f2f7" if is_dark else "#1f2937"
        btn_hover = "#3a3a3c" if is_dark else "#d1d5db"
        cb = QPushButton("Cerrar")
        cb.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cb.setFixedHeight(30)
        cb.setStyleSheet(
            f"QPushButton {{ background: {btn_bg}; border: 1px solid {bord}; "
            f"border-radius: 6px; color: {btn_fg}; font-weight: 600; padding: 0 16px; }} "
            f"QPushButton:hover {{ background: {btn_hover}; }}"
        )
        cb.clicked.connect(self.accept)
        bl.addWidget(cb)
        root.addWidget(bot)
