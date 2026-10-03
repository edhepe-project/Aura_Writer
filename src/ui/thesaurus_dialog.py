"""
thesaurus_dialog.py — Diálogo flotante de sinónimos y alternativas léxicas (Shift+F7).

Permite a los novelistas buscar sinónimos de cualquier término en español de forma 100% offline,
explorar acepciones y reemplazar directamente la palabra en el editor activo.
"""
from __future__ import annotations

from typing import Callable, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QFrame, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import qtawesome as qta

from core.theme_manager import ThemeManager
from core.thesaurus import AuraThesaurus, match_case


class ThesaurusDialog(QDialog):
    """
    Diálogo interactivo para explorar sinónimos y sustituir términos en el editor.
    """

    def __init__(
        self,
        initial_word: str = "",
        on_replace: Optional[Callable[[str], None]] = None,
        parent=None
    ):
        super().__init__(parent)
        self.setWindowTitle("Diccionario de Sinónimos — Aura Writer")
        self.resize(520, 480)
        self.setMinimumSize(420, 360)

        self._initial_word = initial_word.strip()
        self._on_replace = on_replace
        self._thesaurus = AuraThesaurus.get_instance()

        self._setup_ui()
        self._apply_theme()
        ThemeManager.signals.theme_changed.connect(self._apply_theme)

        if self._initial_word:
            self._search_input.setText(self._initial_word)
            self._do_search()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # ── Encabezado ───────────────────────────────────────────────
        header_layout = QHBoxLayout()
        self._icon_lbl = QLabel()
        header_layout.addWidget(self._icon_lbl)

        self._title_lbl = QLabel("Sinónimos y Variantes Léxicas")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(13)
        self._title_lbl.setFont(title_font)
        header_layout.addWidget(self._title_lbl)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # ── Barra de búsqueda ─────────────────────────────────────────
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Escribe una palabra en español… (ej. caminar, brillo, misterio)")
        self._search_input.returnPressed.connect(self._do_search)
        search_layout.addWidget(self._search_input, stretch=1)

        self._btn_search = QPushButton("Buscar")
        self._btn_search.clicked.connect(self._do_search)
        search_layout.addWidget(self._btn_search)

        layout.addLayout(search_layout)

        # ── Estado / Contador ─────────────────────────────────────────
        self._status_lbl = QLabel("Escribe una palabra para consultar sinónimos.")
        status_font = QFont()
        status_font.setPointSize(10)
        self._status_lbl.setFont(status_font)
        layout.addWidget(self._status_lbl)

        # ── Lista de sinónimos ────────────────────────────────────────
        self._list_widget = QListWidget()
        self._list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self._list_widget, stretch=1)

        # ── Botones de acción ─────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self._btn_copy = QPushButton("Copiar")
        self._btn_copy.setEnabled(False)
        self._btn_copy.clicked.connect(self._copy_selected)
        btn_layout.addWidget(self._btn_copy)

        btn_layout.addStretch()

        if self._on_replace:
            self._btn_replace = QPushButton("Reemplazar en Editor")
            self._btn_replace.setEnabled(False)
            self._btn_replace.clicked.connect(self._replace_selected)
            btn_layout.addWidget(self._btn_replace)

        self._btn_close = QPushButton("Cerrar")
        self._btn_close.clicked.connect(self.reject)
        btn_layout.addWidget(self._btn_close)

        layout.addLayout(btn_layout)

    def _apply_theme(self):
        tc = ThemeManager.theme_colors()
        bg_main = tc["bg_main"]
        bg_card = tc["bg_card"]
        bg_input = tc["bg_input"]
        border = tc["border"]
        fg = tc["fg_text"]
        sub_text = ThemeManager.color("fg_muted")
        accent = tc["accent"]
        hover = ThemeManager.color("bg_hover")

        # En temas claros/sepia, el texto seleccionado debe contrastar nítidamente
        if ThemeManager.is_dark():
            sel_bg = accent
            sel_fg = "#000000"
            btn_primary_fg = "#000000"
        else:
            sel_bg = accent
            sel_fg = "#ffffff"
            btn_primary_fg = "#ffffff"

        # Actualizar iconos dinámicamente con la paleta activa
        self._icon_lbl.setPixmap(qta.icon("fa5s.book-open", color=accent).pixmap(24, 24))
        self._btn_search.setIcon(qta.icon("fa5s.search", color=btn_primary_fg))
        self._btn_copy.setIcon(qta.icon("fa5s.copy", color=fg))
        if hasattr(self, "_btn_replace"):
            self._btn_replace.setIcon(qta.icon("fa5s.check", color=btn_primary_fg))

        # Re-colorear items existentes en la lista
        for i in range(self._list_widget.count()):
            item = self._list_widget.item(i)
            if item:
                # El icono cambia según si está seleccionado o no mediante stylesheet/palette
                item.setIcon(qta.icon("fa5s.angle-right", color=accent))

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_main};
                color: {fg};
            }}
            QLabel {{
                color: {fg};
            }}
            QLineEdit {{
                background-color: {bg_input};
                color: {fg};
                border: 1px solid {border};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                selection-background-color: {hover};
                selection-color: {fg};
            }}
            QLineEdit:focus {{
                border: 1.5px solid {accent};
            }}
            QListWidget {{
                background-color: {bg_card};
                color: {fg};
                border: 1px solid {border};
                border-radius: 8px;
                padding: 6px;
                font-size: 13px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 9px 14px;
                border-radius: 6px;
                margin-bottom: 3px;
                color: {fg};
            }}
            QListWidget::item:hover {{
                background-color: {hover};
            }}
            QListWidget::item:selected {{
                background-color: {sel_bg};
                color: {sel_fg};
                font-weight: bold;
            }}
            QPushButton {{
                background-color: {bg_card};
                color: {fg};
                border: 1px solid {border};
                border-radius: 8px;
                padding: 7px 18px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {hover};
                border-color: {accent};
            }}
            QPushButton:disabled {{
                color: {sub_text};
                border-color: {border};
                background-color: {bg_main};
                opacity: 0.6;
            }}
            QPushButton#primaryAction {{
                background-color: {accent};
                color: {btn_primary_fg};
                font-weight: bold;
                border: 1px solid {accent};
            }}
            QPushButton#primaryAction:hover {{
                background-color: {accent};
                opacity: 0.9;
                border-color: {accent};
            }}
        """)
        if hasattr(self, "_btn_search"):
            self._btn_search.setObjectName("primaryAction")
        if hasattr(self, "_btn_replace"):
            self._btn_replace.setObjectName("primaryAction")

    def _do_search(self):
        query = self._search_input.text().strip()
        sub_text = ThemeManager.color("fg_muted")
        accent = ThemeManager.color("accent")

        if not query:
            self._status_lbl.setText("Ingresa una palabra para buscar.")
            self._status_lbl.setStyleSheet(f"color: {sub_text}; font-size: 11px;")
            self._list_widget.clear()
            return

        clean_query = "".join(c for c in query if c.isalpha() or c in "- ")
        synonyms = self._thesaurus.get_synonyms(clean_query, max_results=30)

        self._list_widget.clear()
        if not synonyms:
            self._status_lbl.setText(f"No se encontraron sinónimos para «{clean_query}».")
            self._status_lbl.setStyleSheet(f"color: {sub_text}; font-size: 11px;")
            return

        self._status_lbl.setText(f"{len(synonyms)} alternativas encontradas para «{clean_query}»:")
        self._status_lbl.setStyleSheet(f"color: {accent}; font-weight: bold; font-size: 11px;")

        for syn in synonyms:
            item = QListWidgetItem(syn)
            item.setIcon(qta.icon("fa5s.angle-right", color=accent))
            self._list_widget.addItem(item)

        if self._list_widget.count() > 0:
            self._list_widget.setCurrentRow(0)

    def _on_selection_changed(self):
        has_sel = bool(self._list_widget.selectedItems())
        self._btn_copy.setEnabled(has_sel)
        if hasattr(self, "_btn_replace"):
            self._btn_replace.setEnabled(has_sel)

    def _on_item_double_clicked(self, item: QListWidgetItem):
        if hasattr(self, "_btn_replace") and self._btn_replace.isEnabled():
            self._replace_selected()
        else:
            self._copy_selected()

    def _copy_selected(self):
        items = self._list_widget.selectedItems()
        if items:
            QApplication.clipboard().setText(items[0].text())
            tc = ThemeManager.theme_colors()
            accent = tc["accent"]
            self._status_lbl.setText(f"¡«{items[0].text()}» copiado al portapapeles!")
            self._status_lbl.setStyleSheet(f"color: {accent}; font-weight: bold; font-size: 11px;")

    def _replace_selected(self):
        items = self._list_widget.selectedItems()
        if items and self._on_replace:
            self._on_replace(items[0].text())
            self.accept()

    def closeEvent(self, event):
        try:
            ThemeManager.signals.theme_changed.disconnect(self._apply_theme)
        except Exception:
            pass
        super().closeEvent(event)

    def reject(self):
        try:
            ThemeManager.signals.theme_changed.disconnect(self._apply_theme)
        except Exception:
            pass
        super().reject()
