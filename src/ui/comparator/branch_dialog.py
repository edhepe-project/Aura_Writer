"""
branch_dialog.py — Diálogo de confirmación para bifurcar capítulos o abrir en modo solo lectura.
"""

from typing import Literal
from PyQt6.QtWidgets import (
    QDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout
)
from core.theme_manager import ThemeManager


class ChapterBranchDialog(QDialog):
    """Diálogo emergente para resolver la colisión al abrir el mismo capítulo en ambos paneles."""

    def __init__(self, chapter_title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("¿Deseas bifurcar este capítulo?")
        self.setFixedWidth(560)
        self.chosen_action: Literal["branch", "readonly", "cancel"] = "cancel"

        c = ThemeManager.palette()

        dlg_layout = QVBoxLayout(self)
        dlg_layout.setContentsMargins(20, 20, 20, 20)
        dlg_layout.setSpacing(16)

        title_msg = QLabel(f"<b>Has seleccionado «{chapter_title}» en ambos lados de la mesa de cotejo.</b>")
        title_msg.setStyleSheet(f"font-size: 13px; color: {c['fg_primary']};")
        dlg_layout.addWidget(title_msg)

        info_msg = QLabel(
            "Para proteger tu obra de sobreescrituras accidentales, puedes crear una copia "
            "alternativa para experimentar libremente o abrirlo en modo lectura:"
        )
        info_msg.setWordWrap(True)
        info_msg.setStyleSheet(f"font-size: 12px; color: {c['fg_muted']}; line-height: 1.4;")
        dlg_layout.addWidget(info_msg)

        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        btn_branch = QPushButton("🌿 Crear Borrador Alternativo")
        btn_branch.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['green']};
                color: {c['fg_selected']};
                font-weight: bold;
                padding: 8px 14px;
                border-radius: 6px;
                font-size: 12px;
            }}
            QPushButton:hover {{ background-color: {c['accent']}; }}
        """)

        btn_readonly = QPushButton("👀 Solo Lectura")
        btn_readonly.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['bg_hover']};
                color: {c['fg_primary']};
                border: 1px solid {c['border_default']};
                padding: 8px 14px;
                border-radius: 6px;
                font-size: 12px;
            }}
            QPushButton:hover {{ background-color: {c['bg_selected']}; }}
        """)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {c['fg_muted']};
                border: 1px solid {c['border_default']};
                padding: 8px 14px;
                border-radius: 6px;
                font-size: 12px;
            }}
            QPushButton:hover {{ background-color: {c['bg_hover']}; }}
        """)

        def _choose_branch():
            self.chosen_action = "branch"
            self.accept()

        def _choose_readonly():
            self.chosen_action = "readonly"
            self.accept()

        def _choose_cancel():
            self.chosen_action = "cancel"
            self.reject()

        btn_branch.clicked.connect(_choose_branch)
        btn_readonly.clicked.connect(_choose_readonly)
        btn_cancel.clicked.connect(_choose_cancel)

        btn_box.addWidget(btn_branch)
        btn_box.addWidget(btn_readonly)
        btn_box.addStretch()
        btn_box.addWidget(btn_cancel)
        dlg_layout.addLayout(btn_box)

    @classmethod
    def ask_action(cls, chapter_title: str, parent=None) -> Literal["branch", "readonly", "cancel"]:
        dlg = cls(chapter_title, parent=parent)
        if dlg.exec():
            return dlg.chosen_action
        return "cancel"
