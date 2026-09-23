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
        bg = "#141416" if is_dark else "#f4f6fa"
        self.setStyleSheet(f"QDialog {{ background: {bg}; }}")
        self._setup_ui(is_dark)
        self._grid_widget.build()

    def _setup_ui(self, is_dark: bool) -> None:
        fg    = "#f2f2f7" if is_dark else "#1a1d23"
        bord  = "#3a3a3c" if is_dark else "#c2cbd9"
        bg_tb = "#1c1c1e" if is_dark else "#dde3f0"
        sub   = "#636366" if is_dark else "#5a6a8a"

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # -- Toolbar ----------------------------------------------------------
        tb = QFrame()
        tb.setFixedHeight(50)
        tb.setStyleSheet(f"QFrame {{ background: {bg_tb}; border-bottom: 1px solid {bord}; }}")
        tbl = QHBoxLayout(tb)
        tbl.setContentsMargins(16, 0, 16, 0)
        tbl.setSpacing(12)

        tl = QLabel("Cuadricula de Presencias")
        tl.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {fg};")
        tbl.addWidget(tl)

        sl = QLabel("Filas = personajes  |  Columnas = capitulos")
        sl.setStyleSheet(f"font-size: 10px; color: {sub};")
        tbl.addWidget(sl)
        tbl.addStretch()

        # Pastillas de leyenda
        if is_dark:
            pills = [("Presente", "#30d158"), ("En transito", "#0a84ff"), ("Salida", "#ff453a")]
        else:
            pills = [("Presente", "#1a7a38"), ("En transito", "#1a56b0"), ("Salida", "#c41e0e")]

        for lbl, col in pills:
            pill = QLabel(f"  {lbl}")
            pill.setStyleSheet(
                f"font-size: 10px; color: {col}; font-weight: bold; "
                f"border: 1px solid {col}55; border-radius: 4px; padding: 2px 8px; background: {col}18;"
            )
            tbl.addWidget(pill)

        root.addWidget(tb)

        # -- Cuadricula -------------------------------------------------------
        self._grid_widget = _PresenceGridWidget(self._pm)
        root.addWidget(self._grid_widget, stretch=1)

        # -- Barra inferior ---------------------------------------------------
        bot = QFrame()
        bot.setFixedHeight(40)
        bot.setStyleSheet(f"QFrame {{ background: {bg_tb}; border-top: 1px solid {bord}; }}")
        bl = QHBoxLayout(bot)
        bl.setContentsMargins(16, 0, 16, 0)
        bl.setSpacing(12)

        hl = QLabel("Clic para asignar ubicacion   |   Clic derecho para limpiar")
        hl.setStyleSheet("font-size: 10px; color: #636366;")
        bl.addWidget(hl)
        bl.addStretch()

        cb = QPushButton("Cerrar")
        cb.setFixedHeight(28)
        cb.setStyleSheet(
            "QPushButton { background: transparent; border: 1px solid #636366; "
            "border-radius: 6px; color: #8e8e93; padding: 0 14px; } "
            "QPushButton:hover { border-color: #f2f2f7; color: #f2f2f7; }"
        )
        cb.clicked.connect(self.accept)
        bl.addWidget(cb)
        root.addWidget(bot)
