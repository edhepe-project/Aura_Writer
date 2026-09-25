"""
vocabulary_dialog.py — Gestor de Vocabulario y Conlang del Universo.
Responsabilidad única: Permitir al autor registrar palabras inventadas (conlang),
términos mágicos, verbos de desplazamiento o aliases con sus categorías gramaticales.
"""
from __future__ import annotations
from typing import Optional, List

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QLineEdit, QComboBox,
    QHeaderView, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
import qtawesome as qta

from core.models import CustomVocabularyEntry, UniverseMetadata
from core.theme_manager import ThemeManager


class VocabularyDialog(QDialog):
    """
    Diálogo para administrar el glosario de Conlang y verbos personalizados del proyecto.
    """

    def __init__(self, project_manager, parent=None):
        super().__init__(parent)
        self.pm = project_manager
        self.setWindowTitle("Vocabulario & Conlang del Universo")
        self.resize(720, 520)
        self.setMinimumSize(580, 400)
        self._setup_ui()
        ThemeManager.signals.theme_changed.connect(self._setup_ui)
        self._load_data()

    def _setup_ui(self):
        tc = ThemeManager.theme_colors()
        bg_main = tc["bg_main"]
        border_col = tc["border"]
        fg_col = tc["fg_text"]
        input_bg = tc["bg_input"]
        hover_col = tc["hover"]
        header_bg = tc["bg_card"]
        btn_bg = tc["bg_input"]
        accent = tc["accent"]

        self.setStyleSheet(f"""
            QDialog {{ background-color: {bg_main}; }}
            QLabel {{ color: {fg_col}; }}
            QLineEdit, QComboBox {{
                background-color: {input_bg};
                color: {fg_col};
                border: 1px solid {border_col};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
            }}
            QTableWidget {{
                background-color: {input_bg};
                color: {fg_col};
                border: 1px solid {border_col};
                border-radius: 6px;
                gridline-color: {border_col};
            }}
            QHeaderView::section {{
                background-color: {header_bg};
                color: {fg_col};
                padding: 6px;
                border: none;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton {{
                background-color: {btn_bg};
                color: {fg_col};
                border: 1px solid {border_col};
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {hover_col};
                border-color: {accent};
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        # Encabezado
        title = QLabel("Glosario de Términos, Verbos y Conlang")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(13)
        title.setFont(title_font)
        root.addWidget(title)

        desc = QLabel(
            "Registra las palabras de tu idioma inventado o términos especiales. "
            "El motor NLP las utilizará para detectar la presencia y movimiento de personajes con máxima precisión."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #8e8e93; font-size: 11px;")
        root.addWidget(desc)

        # Formulario rápido para añadir
        add_frame = QFrame()
        add_layout = QHBoxLayout(add_frame)
        add_layout.setContentsMargins(0, 0, 0, 0)
        add_layout.setSpacing(8)

        self.word_input = QLineEdit()
        self.word_input.setPlaceholderText("Palabra o verbo (ej. vel'thar, ael)")
        add_layout.addWidget(self.word_input, stretch=2)

        self.type_combo = QComboBox()
        self.type_combo.addItem("Verbo de Llegada / Presencia", "verb_arrive")
        self.type_combo.addItem("Verbo de Tránsito / Movimiento", "verb_transit")
        self.type_combo.addItem("Verbo de Salida / Partida", "verb_depart")
        self.type_combo.addItem("Sustantivo / Nombre de Lugar", "place_noun")
        self.type_combo.addItem("Término Mágico / Objeto", "lore_term")
        add_layout.addWidget(self.type_combo, stretch=2)

        self.meaning_input = QLineEdit()
        self.meaning_input.setPlaceholderText("Significado / Notas (opcional)")
        add_layout.addWidget(self.meaning_input, stretch=3)

        btn_add = QPushButton("＋ Agregar")
        btn_add.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {accent};
                border: 1px solid {accent};
            }}
            QPushButton:hover {{
                background-color: {hover_col};
            }}
        """)
        btn_add.clicked.connect(self._on_add_entry)
        add_layout.addWidget(btn_add)
        root.addWidget(add_frame)

        # Tabla de términos
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Término", "Categoría / Rol", "Significado / Notas", "Acciones"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 70)
        self.table.verticalHeader().setVisible(False)
        root.addWidget(self.table, stretch=1)

        # Footer
        footer = QHBoxLayout()
        footer.addStretch()
        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.accept)
        footer.addWidget(btn_close)
        root.addLayout(footer)

    def _load_data(self):
        if not self.pm or not self.pm.metadata:
            return

        vocab: List[CustomVocabularyEntry] = getattr(self.pm.metadata, "custom_vocabulary", [])
        self.table.setRowCount(0)

        for row, entry in enumerate(vocab):
            self.table.insertRow(row)

            # Término
            item_word = QTableWidgetItem(entry.word)
            item_word.setFont(QFont("Inter", 10, QFont.Weight.Bold))
            self.table.setItem(row, 0, item_word)

            # Tipo
            type_label = {
                "verb_arrive": "Verbo Llegada",
                "verb_transit": "Verbo Tránsito",
                "verb_depart": "Verbo Salida",
                "place_noun": "Sustantivo Lugar",
                "lore_term": "Término Lore"
            }.get(entry.entry_type, entry.entry_type)
            item_type = QTableWidgetItem(type_label)
            self.table.setItem(row, 1, item_type)

            # Significado
            item_meaning = QTableWidgetItem(entry.meaning or "")
            self.table.setItem(row, 2, item_meaning)

            # Botón Eliminar
            btn_del = QPushButton()
            btn_del.setIcon(qta.icon('ph.trash-bold', color="#ff453a"))
            btn_del.setFixedSize(30, 24)
            btn_del.setToolTip("Eliminar término")
            btn_del.setStyleSheet("border: none; background: transparent;")
            btn_del.clicked.connect(lambda _, w=entry.word: self._on_delete_entry(w))
            self.table.setCellWidget(row, 3, btn_del)

    def _on_add_entry(self):
        word = self.word_input.text().strip()
        if not word:
            return

        entry_type = self.type_combo.currentData()
        meaning = self.meaning_input.text().strip()

        if not self.pm or not self.pm.metadata:
            return

        vocab = getattr(self.pm.metadata, "custom_vocabulary", [])
        # Evitar duplicados
        if any(e.word.lower() == word.lower() for e in vocab):
            QMessageBox.warning(self, "Término Duplicado", f"El término '{word}' ya existe en el vocabulario.")
            return

        new_entry = CustomVocabularyEntry(word=word, entry_type=entry_type, meaning=meaning)
        vocab.append(new_entry)
        self.pm.metadata.custom_vocabulary = vocab

        self.word_input.clear()
        self.meaning_input.clear()
        self._load_data()

    def _on_delete_entry(self, word: str):
        if not self.pm or not self.pm.metadata:
            return

        vocab = getattr(self.pm.metadata, "custom_vocabulary", [])
        self.pm.metadata.custom_vocabulary = [e for e in vocab if e.word != word]
        self._load_data()
