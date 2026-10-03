"""
panel.py — Panel individual de edición de capítulo para ChapterComparatorDialog.
"""

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTextEdit
)
from PyQt6.QtGui import QFont
from core.theme_manager import ThemeManager


class ChapterEditorPanel(QFrame):
    """Panel individual para un capítulo (selector, contador y editor editable)."""

    def __init__(self, title_prefix: str, parent=None):
        super().__init__(parent)
        self.title_prefix = title_prefix
        self.chapter_id = None
        self.content_file = None
        self._dirty = False

        c = ThemeManager.palette()

        panel_bg = c["bg_surface"]
        panel_border = c["border_subtle"]
        combo_bg = c["bg_input"]
        combo_fg = c["fg_primary"]
        combo_border = c["border_default"]
        editor_bg = c["bg_app"]
        editor_fg = c["fg_primary"]
        editor_border = c["border_default"]
        subtext_color = c["fg_muted"]

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"""
            ChapterEditorPanel {{
                background-color: {panel_bg};
                border: 1px solid {panel_border};
                border-radius: 8px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Header: Título + Combo de selección
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        lbl = QLabel(f"<b>{title_prefix}:</b>")
        lbl.setStyleSheet(f"color: {c['accent']}; font-size: 13px;")
        header_layout.addWidget(lbl)

        self.combo = QComboBox()
        self.combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {combo_bg};
                color: {combo_fg};
                border: 1px solid {combo_border};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {combo_bg};
                color: {combo_fg};
                selection-background-color: {c['bg_selected']};
                selection-color: {c['fg_selected']};
            }}
        """)
        header_layout.addWidget(self.combo, 1)
        layout.addLayout(header_layout)

        # Editor de texto enriquecido con estilo adaptativo
        self.editor = QTextEdit()
        font = QFont("Georgia", 13)
        font.setStyleHint(QFont.StyleHint.Serif)
        self.editor.setFont(font)
        # Aplicar la fuente al documento base para que todos los bloques la hereden,
        # incluyendo los que vienen del HTML con estilos embebidos.
        self.editor.document().setDefaultFont(font)
        self.editor.setStyleSheet(f"""
            QTextEdit {{
                background-color: {editor_bg};
                color: {editor_fg};
                border: 1px solid {editor_border};
                border-radius: 6px;
                padding: 12px;
                line-height: 1.6;
                selection-background-color: {c['selection_bg']};
            }}
        """)
        self.editor.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.editor, 1)

        # Footer: Contador de palabras
        self.stats_lbl = QLabel("Palabras: 0  |  Caracteres: 0")
        self.stats_lbl.setStyleSheet(f"color: {subtext_color}; font-size: 11px;")
        layout.addWidget(self.stats_lbl)

    def _on_text_changed(self):
        self._dirty = True
        text = self.editor.toPlainText()
        words = len(text.split())
        chars = len(text)
        self.stats_lbl.setText(f"Palabras: {words:,}  |  Caracteres: {chars:,}")
