"""
dialog.py — Diálogo completo de creación y edición de personajes en Aura Writer.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QMessageBox
)

from core.models import Character, CharacterRelation
from core.theme_manager import ThemeManager
from ui.genealogy.widget import GenealogyWidget
from ui.character_dialog.tab_profile import CharacterProfileTab
from ui.character_dialog.tab_relations import CharacterRelationsTab


class CharacterEditDialog(QDialog):
    """
    Ventana emergente completa para crear o editar un personaje.
    Contiene tres pestañas:
      - Perfil: nombre, rol, aliases, descripción, esencia y notas
      - Relaciones: lista de relaciones con acciones para añadir/editar/eliminar
      - Genealogía: mapa conceptual radial centrado en este personaje
    """

    def __init__(self, character: Character | None = None,
                 obras: list = None,
                 characters: list[Character] = None,
                 relations: list[CharacterRelation] = None,
                 parent=None):
        super().__init__(parent)
        self._is_new = character is None
        self._char = character or Character()
        self._obras = obras or []
        self._characters = list(characters or [])
        self._all_relations = list(relations or [])
        self._relations = [r for r in self._all_relations
                           if r.char_id_a == self._char.id
                           or r.char_id_b == self._char.id]

        self.setWindowTitle("Nuevo Personaje" if self._is_new else f"Editar — {self._char.name}")
        self.setMinimumSize(680, 620)
        self.resize(760, 800)

        self._build_ui()
        if not self._is_new:
            self._load_from_character()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 16)
        root.setSpacing(14)

        # Header
        is_dark = ThemeManager.is_dark()
        header_color = "#f2f2f7" if is_dark else "#1a1a2e"
        header_lbl = QLabel("👤  FICHA DE PERSONAJE")
        header_lbl.setStyleSheet(
            f"font-size: 13px; font-weight: 800; color: {header_color}; "
            f"letter-spacing: 0.8px; padding: 2px 0; background: transparent;"
        )
        root.addWidget(header_lbl)

        # Tabs
        self._tabs = QTabWidget()
        root.addWidget(self._tabs, 1)

        # Tab 1: Perfil
        self._profile_tab = CharacterProfileTab(self._char, self._characters, parent=self)
        self._tabs.addTab(self._profile_tab, "📋 Perfil")

        # Tab 2: Relaciones
        self._relations_tab = CharacterRelationsTab(
            self._char,
            self._characters,
            self._relations,
            self._all_relations,
            obras=self._obras,
            on_relations_changed=self._on_relations_changed,
            parent=self
        )
        self._tabs.addTab(self._relations_tab, "🔗 Relaciones")

        # Tab 3: Genealogía / Mapa conceptual
        if not self._is_new:
            self._genealogy_widget = GenealogyWidget(
                self._char, self._characters, self._all_relations, parent=self
            )
            self._tabs.addTab(self._genealogy_widget, "Genealogía")

        # Botones
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        self._btn_save = QPushButton("💾  Guardar" if not self._is_new else "✅  Crear Personaje")
        self._btn_save.clicked.connect(self._on_save)
        btn_row.addWidget(self._btn_save)

        root.addLayout(btn_row)

    def _on_relations_changed(self):
        if hasattr(self, '_genealogy_widget'):
            self._genealogy_widget.set_data(self._char, self._characters, self._all_relations)

    def _load_from_character(self):
        self._profile_tab.load_from_character(self._char)

    def _on_save(self):
        name = self._profile_tab.get_name()
        if not name:
            QMessageBox.warning(self, "Campo requerido", "El nombre del personaje es obligatorio.")
            self._profile_tab.focus_name_input()
            return

        self._profile_tab.save_to_character(self._char)
        self.accept()

    def get_character(self) -> Character:
        return self._char

    def get_relations(self) -> list[CharacterRelation]:
        return self._all_relations

    def get_all_relations(self) -> list[CharacterRelation]:
        return self._all_relations
