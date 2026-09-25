"""
tab_relations.py — Pestaña de relaciones para CharacterEditDialog.
"""

from __future__ import annotations
from typing import Callable

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QColor

from core.models import Character, CharacterRelation, RELATION_COLORS
from core.theme_manager import ThemeManager
from ui.relation_dialog import RelationDialog


class CharacterRelationsTab(QWidget):
    """Pestaña de gestión y listado de relaciones de un personaje."""

    def __init__(self,
                 character: Character,
                 characters: list[Character],
                 relations: list[CharacterRelation],
                 all_relations: list[CharacterRelation],
                 obras: list = None,
                 on_relations_changed: Callable[[], None] | None = None,
                 parent=None):
        super().__init__(parent)
        self._char = character
        self._characters = characters
        self._relations = relations
        self._all_relations = all_relations
        self._obras = obras or []
        self._on_relations_changed = on_relations_changed
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        container = QWidget()
        container.setObjectName("relationsContainer")
        container.setStyleSheet("QWidget#relationsContainer { background: transparent; }")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.addWidget(self._section_label("Relaciones de este personaje"))
        header.addStretch()
        btn_add_rel = QPushButton("+ Añadir relación")
        btn_add_rel.clicked.connect(self._on_add_relation)
        header.addWidget(btn_add_rel)
        layout.addLayout(header)

        self._rel_list = QListWidget()
        self._rel_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._rel_list.customContextMenuRequested.connect(self._on_rel_context_menu)
        layout.addWidget(self._rel_list, 1)

        is_dark = ThemeManager.is_dark()
        info_col = "#8e8e93" if is_dark else "#78716c"
        info = QLabel("ℹ️  Clic derecho en una relación para editar o eliminar")
        info.setStyleSheet(f"color: {info_col}; font-size: 11px; padding: 2px 4px; background: transparent;")
        layout.addWidget(info)

        root.addWidget(container)
        self.refresh_rel_list()

    def refresh_rel_list(self):
        self._rel_list.clear()
        char_map = {c.id: c for c in self._characters}
        for rel in self._relations:
            other_id = None
            if rel.char_id_a == self._char.id:
                other_id = rel.char_id_b
            elif rel.char_id_b == self._char.id:
                other_id = rel.char_id_a
            if not other_id or other_id not in char_map:
                continue

            other = char_map[other_id]
            rtype = rel.relation_type

            if rtype == "descendiente":
                if rel.char_id_a == self._char.id:
                    text = f"Descendiente (hijo/a) de → {other.name}"
                else:
                    text = f"Progenitor / Antepasado de → {other.name}"
            elif rtype == "mentor":
                if rel.char_id_a == self._char.id:
                    text = f"Mentor de → {other.name}"
                else:
                    text = f"Aprendiz de → {other.name}"
            elif rtype == "pareja":
                text = f"Pareja de → {other.name}"
            elif rtype == "familiar":
                text = f"Familiar de → {other.name}"
            elif rtype == "rival":
                text = f"Rival de → {other.name}"
            elif rtype == "amigo":
                text = f"Amigo de → {other.name}"
            else:
                text = f"Vínculo con → {other.name}"

            if rel.label:
                text += f"  ·  {rel.label}"

            color = RELATION_COLORS.get(rtype, "#636366")
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, rel.id)
            item.setData(Qt.ItemDataRole.UserRole + 1, other_id)
            item.setForeground(QColor(color))
            self._rel_list.addItem(item)

        if self._on_relations_changed:
            self._on_relations_changed()

    def _on_rel_context_menu(self, pos: QPoint):
        item = self._rel_list.itemAt(pos)
        if not item:
            return
        rel_id = item.data(Qt.ItemDataRole.UserRole)
        other_id = item.data(Qt.ItemDataRole.UserRole + 1)

        menu = QMenu(self)
        act_edit = menu.addAction("Editar relación")
        act_delete = menu.addAction("Eliminar relación")
        chosen = menu.exec(self._rel_list.viewport().mapToGlobal(pos))

        if chosen == act_edit:
            rel = next((r for r in self._relations if r.id == rel_id), None)
            if rel:
                dlg = RelationDialog(
                    self._characters, self._char.id, self._obras,
                    relation=rel, fixed_target_id=other_id, parent=self
                )
                if dlg.exec():
                    data = dlg.get_data()
                    rel.char_id_a = data.get("char_id_a", self._char.id)
                    rel.char_id_b = data.get("char_id_b", data["target_id"])
                    rel.relation_type = data["relation_type"]
                    rel.label = data["label"]
                    rel.intensity = data["intensity"]
                    rel.obra_id = data["obra_id"]
                    self.refresh_rel_list()
        elif chosen == act_delete:
            reply = QMessageBox.question(
                self, "Eliminar Relación", "¿Eliminar esta relación?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._relations[:] = [r for r in self._relations if r.id != rel_id]
                self._all_relations[:] = [r for r in self._all_relations if r.id != rel_id]
                self.refresh_rel_list()

    def _on_add_relation(self):
        if len(self._characters) < 2:
            QMessageBox.information(
                self, "Info",
                "Necesitas al menos 2 personajes para crear una relación."
            )
            return
        dlg = RelationDialog(
            self._characters, self._char.id, self._obras, parent=self
        )
        if dlg.exec():
            data = dlg.get_data()
            if not data["target_id"]:
                return
            rel = CharacterRelation(
                char_id_a=data.get("char_id_a", self._char.id),
                char_id_b=data.get("char_id_b", data["target_id"]),
                relation_type=data["relation_type"],
                label=data["label"],
                intensity=data["intensity"],
                obra_id=data["obra_id"],
            )
            self._relations.append(rel)
            self._all_relations.append(rel)
            self.refresh_rel_list()

    @staticmethod
    def _section_label(text: str) -> QLabel:
        is_dark = ThemeManager.is_dark()
        color = "#8e8e93" if is_dark else "#5a554e"
        lbl = QLabel(text.upper())
        lbl.setStyleSheet(
            f"color: {color}; font-size: 11px; font-weight: 700; "
            f"letter-spacing: 0.5px; background: transparent; margin-top: 4px;"
        )
        return lbl
