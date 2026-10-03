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
    Diálogo independiente — Cuadrícula de Presencias con columna congelada.
    Filas = personajes (por rol), Columnas = capítulos (cronológico).
    La columna de personajes y el header de capítulos permanecen fijos al hacer scroll.
    """

    def __init__(self, project_manager, parent=None):
        super().__init__(parent)
        self._pm = project_manager
        self.setWindowTitle("Cuadrícula de Presencias del Universo")
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinMaxButtonsHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        screen = QApplication.primaryScreen().availableGeometry()
        w = min(1400, int(screen.width()  * 0.90))
        h = min(860,  int(screen.height() * 0.88))
        self.resize(w, h)

        self._apply_theme()
        ThemeManager.signals.theme_changed.connect(self._apply_theme)

    def _apply_theme(self) -> None:
        tc = ThemeManager.theme_colors()
        bg_main = tc["bg_main"]
        self.setStyleSheet(f"""
            QDialog {{ background-color: {bg_main}; }}
            QLabel {{ border: none !important; background: transparent; outline: none !important; }}
        """)
        self._setup_ui(tc)
        if hasattr(self, "_grid_widget"):
            self._grid_widget.build()

    def _setup_ui(self, tc: dict = None) -> None:
        if tc is None:
            tc = ThemeManager.theme_colors()
        
        bg_card = tc["bg_card"]
        border_col = tc["border"]
        fg_col = tc["fg_text"]
        sub_col = tc["subtext"]
        accent = tc["accent"]
        bg_main = tc["bg_main"]
        hover_col = tc["hover"]

        # Limpiar layout previo si existe
        if self.layout():
            QWidget().setLayout(self.layout())

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # -- Toolbar Superior Elegante ----------------------------------------
        tb = QFrame()
        tb.setFixedHeight(56)
        tb.setStyleSheet(f"QFrame {{ background: {bg_card}; border-bottom: 1px solid {border_col}; }}")
        tbl = QHBoxLayout(tb)
        tbl.setContentsMargins(20, 0, 20, 0)
        tbl.setSpacing(14)

        tl = QLabel("Cuadrícula de Presencias")
        tl.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {accent}; letter-spacing: 0.3px;")
        tbl.addWidget(tl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"color: {border_col}; margin: 12px 0;")
        tbl.addWidget(sep)

        sl = QLabel("Filas = Personajes  •  Columnas = Capítulos")
        sl.setStyleSheet(f"font-size: 12px; color: {sub_col}; font-weight: 500;")
        tbl.addWidget(sl)
        tbl.addStretch()

        # Pastillas de Leyenda Homogéneas
        pills = [
            ("Presente", tc["green"], "rgba(34, 197, 94, 0.12)"),
            ("En tránsito", tc["blue"], "rgba(59, 130, 246, 0.12)"),
            ("Salida", tc["red"], "rgba(239, 68, 68, 0.12)"),
            ("Mención", tc["purple"], "rgba(168, 85, 247, 0.12)"),
        ]

        for lbl, color, bg_pill in pills:
            pill = QLabel(f"  {lbl}")
            pill.setStyleSheet(
                f"font-size: 11px; color: {color}; font-weight: 600; "
                f"border: 1px solid {color}55; border-radius: 12px; padding: 4px 12px; background: {bg_pill};"
            )
            tbl.addWidget(pill)

        root.addWidget(tb)

        # -- Cuadrícula Principal ---------------------------------------------
        self._grid_widget = _PresenceGridWidget(self._pm)
        root.addWidget(self._grid_widget, stretch=1)

        # -- Barra Inferior ---------------------------------------------------
        bot = QFrame()
        bot.setFixedHeight(48)
        bot.setStyleSheet(f"QFrame {{ background: {bg_card}; border-top: 1px solid {border_col}; }}")
        bl = QHBoxLayout(bot)
        bl.setContentsMargins(20, 0, 20, 0)
        bl.setSpacing(12)

        hl = QLabel("💡 Clic en celda para asignar ubicación   |   Clic derecho para limpiar")
        hl.setStyleSheet(f"font-size: 11px; color: {sub_col}; font-weight: 500;")
        bl.addWidget(hl)
        bl.addStretch()

        cb = QPushButton("Cerrar")
        cb.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cb.setFixedHeight(32)
        cb.setStyleSheet(f"""
            QPushButton {{
                background-color: {tc['bg_input']};
                border: 1px solid {border_col};
                border-radius: 6px;
                color: {fg_col};
                font-weight: 600;
                font-size: 12px;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background-color: {hover_col};
                border-color: {accent};
            }}
        """)
        cb.clicked.connect(self.accept)
        bl.addWidget(cb)
        root.addWidget(bot)

