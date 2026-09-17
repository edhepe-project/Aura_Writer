"""
tree_view.py — Componente de Árbol Jerárquico de Personajes y Relaciones con Búsqueda Rápida.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QMenu, QLineEdit, QMessageBox, QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPoint
from PyQt6.QtGui import QFont, QColor
import qtawesome as qta

from core.models import Character, CharacterRelation
from core.theme_manager import ThemeManager
from ui.character_edit_dialog import CharacterEditDialog
from ui.relation_dialog import RelationDialog


class CharacterTreeView(QWidget):
    """Árbol interactivo de personajes clasificados por rol y agrupados por relaciones."""

    character_added = pyqtSignal(object)     # Character
    character_deleted = pyqtSignal(str)        # char_id
    character_selected = pyqtSignal(str)       # char_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._characters: list[Character] = []
        self._relations: list[CharacterRelation] = []
        self._obras: list = []
        self._current_char: Character | None = None
        self._loading = False

        self._build_ui()

    def _build_ui(self):
        tl = QVBoxLayout(self)
        tl.setContentsMargins(8, 8, 8, 4)
        tl.setSpacing(4)

        tree_header = QHBoxLayout()
        tree_lbl = QLabel("Árbol de personajes")
        tree_header.addWidget(tree_lbl)
        tree_header.addStretch()

        # Botones colapsar / expandir árbol
        self._btn_collapse = self._icon_btn("fa5s.minus", "#aeaeb2", "Colapsar todo")
        self._btn_collapse.clicked.connect(self._on_collapse_all)
        self._btn_expand = self._icon_btn("fa5s.plus", "#aeaeb2", "Expandir todo")
        self._btn_expand.clicked.connect(self._on_expand_all)
        tree_header.addWidget(self._btn_collapse)
        tree_header.addWidget(self._btn_expand)

        # Separador visual entre grupos de botones
        sep_lbl = QLabel("│")
        tree_header.addWidget(sep_lbl)

        self._btn_add_char = self._icon_btn("fa5s.user-plus", "#30d158", "Nuevo personaje")
        self._btn_add_char.clicked.connect(self._on_add_character)
        self._btn_edit_char = self._icon_btn("fa5s.pen", "#5e5ce6", "Editar personaje")
        self._btn_edit_char.clicked.connect(self._on_edit_character)
        self._btn_del_char = self._icon_btn("fa5s.user-minus", "#ff453a", "Eliminar personaje")
        self._btn_del_char.clicked.connect(self._on_del_character)
        tree_header.addWidget(self._btn_add_char)
        tree_header.addWidget(self._btn_edit_char)
        tree_header.addWidget(self._btn_del_char)
        tl.addLayout(tree_header)

        # Barra de búsqueda rápida
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("🔍 Buscar personaje...")
        self._search_input.setClearButtonEnabled(True)
        self._update_search_style(ThemeManager.is_dark())
        self._search_input.textChanged.connect(self._on_search_text_changed)
        tl.addWidget(self._search_input)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setAnimated(True)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._on_tree_context_menu)
        self._tree.currentItemChanged.connect(self._on_tree_selection)
        self._tree.itemDoubleClicked.connect(self._on_tree_double_click)
        tl.addWidget(self._tree)

    def _icon_btn(self, icon_name: str, color: str, tooltip: str) -> QPushButton:
        btn = QPushButton()
        try:
            btn.setIcon(qta.icon(icon_name, color=color))
        except Exception:
            btn.setText(tooltip[0])
        btn.setToolTip(tooltip)
        btn.setFixedSize(QSize(28, 28))
        return btn

    def _update_search_style(self, is_dark: bool = True):
        bg = "#2c2c2e" if is_dark else "#faf7f3"
        fg = "#f2f2f7" if is_dark else "#1a1a2e"
        border = "#3a3a3c" if is_dark else "#c4bfb8"
        focus_border = "#30d158" if is_dark else "#16a34a"
        if hasattr(self, "_search_input"):
            self._search_input.setStyleSheet(f"""
                QLineEdit {{
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 11px;
                    background-color: {bg};
                    color: {fg};
                    border: 1px solid {border};
                }}
                QLineEdit:focus {{
                    border: 1px solid {focus_border};
                }}
            """)

    def set_data(self, characters: list[Character], relations: list[CharacterRelation], obras: list):
        self._loading = True
        self._characters = list(characters)
        self._relations = list(relations)
        self._obras = list(obras)
        prev_id = self._current_char.id if self._current_char else None
        self.rebuild_tree()
        if prev_id:
            self.select_by_char_id(prev_id)
        self._loading = False

    def rebuild_tree(self):
        self._tree.blockSignals(True)
        self._tree.clear()
        char_map = {c.id: c for c in self._characters}
        is_dark = ThemeManager.is_dark()

        # Pre-indexar relaciones O(R)
        rels_by_char: dict[str, list[tuple[str, CharacterRelation, bool]]] = {}
        for rel in self._relations:
            rels_by_char.setdefault(rel.char_id_a, []).append((rel.char_id_b, rel, True))
            rels_by_char.setdefault(rel.char_id_b, []).append((rel.char_id_a, rel, False))

        _ROLE_ORDER = {"Protagonista": 0, "Antagonista": 1, "Secundario": 2, "Misterioso": 3, "Otro": 4}
        sorted_characters = sorted(
            self._characters,
            key=lambda c: (_ROLE_ORDER.get(c.role, 5), (c.name or "").lower())
        )

        for char in sorted_characters:
            root_item = QTreeWidgetItem()
            root_item.setText(0, f"  {char.name}")
            root_item.setData(0, Qt.ItemDataRole.UserRole, char.id)
            root_item.setData(0, Qt.ItemDataRole.UserRole + 1, "character")

            if is_dark:
                role_color = {
                    "Protagonista": "#ffd60a", "Antagonista": "#ff453a",
                    "Misterioso":   "#bf5af2", "Secundario": "#f2f2f7",
                    "Otro":         "#8e8e93"
                }.get(char.role, "#f2f2f7")
                sub_role_color = "#636366"
                rel_detail_color = "#8e8e93"
            else:
                role_color = {
                    "Protagonista": "#b45309", "Antagonista": "#dc2626",
                    "Misterioso":   "#7c3aed", "Secundario": "#1f2937",
                    "Otro":         "#6b7280"
                }.get(char.role, "#1f2937")
                sub_role_color = "#78716c"
                rel_detail_color = "#57534e"

            root_item.setForeground(0, QColor(role_color))
            fnt = QFont()
            fnt.setBold(True)
            fnt.setPointSize(11)
            root_item.setFont(0, fnt)

            role_item = QTreeWidgetItem(root_item)
            role_item.setText(0, f"      {char.role}")
            role_item.setForeground(0, QColor(sub_role_color))
            role_item.setFlags(role_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            role_fnt = QFont()
            role_fnt.setPointSize(9)
            role_fnt.setItalic(True)
            role_item.setFont(0, role_fnt)

            grouped_rels: dict[str, tuple[str, str, list[tuple[Character, CharacterRelation]]]] = {}

            for other_id, rel, is_source in rels_by_char.get(char.id, []):
                rtype = rel.relation_type
                if is_source:
                    if rtype == "descendiente":
                        g_key, g_lbl, g_col = "es_descendiente", "Es descendiente de:", "#2ecc71"
                    elif rtype == "mentor":
                        g_key, g_lbl, g_col = "es_mentor", "Es mentor de:", "#3498db"
                    elif rtype == "pareja":
                        g_key, g_lbl, g_col = "pareja", "Pareja de:", "#e84393"
                    elif rtype == "familiar":
                        g_key, g_lbl, g_col = "familiar", "Familiar de:", "#27ae60"
                    elif rtype == "rival":
                        g_key, g_lbl, g_col = "rival", "Rival de:", "#e67e22"
                    elif rtype == "amigo":
                        g_key, g_lbl, g_col = "amigo", "Amigo de:", "#9b59b6"
                    else:
                        g_key, g_lbl, g_col = "otro", "Vínculo con:", "#95a5a6"
                else:
                    if rtype == "descendiente":
                        g_key, g_lbl, g_col = "es_antepasado", "Es progenitor / antepasado de:", "#27ae60"
                    elif rtype == "mentor":
                        g_key, g_lbl, g_col = "es_aprendiz", "Es aprendiz de:", "#2980b9"
                    elif rtype == "pareja":
                        g_key, g_lbl, g_col = "pareja", "Pareja de:", "#e84393"
                    elif rtype == "familiar":
                        g_key, g_lbl, g_col = "familiar", "Familiar de:", "#27ae60"
                    elif rtype == "rival":
                        g_key, g_lbl, g_col = "rival", "Rival de:", "#e67e22"
                    elif rtype == "amigo":
                        g_key, g_lbl, g_col = "amigo", "Amigo de:", "#9b59b6"
                    else:
                        g_key, g_lbl, g_col = "otro", "Vínculo con:", "#95a5a6"

                if other_id and other_id in char_map:
                    if g_key not in grouped_rels:
                        grouped_rels[g_key] = (g_lbl, g_col, [])
                    grouped_rels[g_key][2].append((char_map[other_id], rel))

            for g_key, (g_lbl, g_col, rel_items) in grouped_rels.items():
                group_item = QTreeWidgetItem(root_item)
                group_item.setText(0, f"  {g_lbl}")
                group_item.setForeground(0, QColor(g_col))
                group_item.setFlags(group_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                fnt2 = QFont()
                fnt2.setPointSize(9)
                group_item.setFont(0, fnt2)

                for other, rel in rel_items:
                    rel_item = QTreeWidgetItem(group_item)
                    label = f"    {other.name}"
                    if rel.label:
                        label += f"  ·  {rel.label}"
                    rel_item.setText(0, label)
                    rel_item.setData(0, Qt.ItemDataRole.UserRole, other.id)
                    rel_item.setData(0, Qt.ItemDataRole.UserRole + 1, "character")
                    rel_item.setData(0, Qt.ItemDataRole.UserRole + 2, rel.id)
                    rel_item.setForeground(0, QColor(rel_detail_color))

            self._tree.addTopLevelItem(root_item)

        if len(self._characters) < 25:
            self._tree.expandAll()
        self._tree.blockSignals(False)

        if hasattr(self, "_search_input") and self._search_input.text().strip():
            self._on_search_text_changed(self._search_input.text())

    def _on_search_text_changed(self, text: str):
        query = text.strip().lower()
        for i in range(self._tree.topLevelItemCount()):
            item = self._tree.topLevelItem(i)
            if not query:
                item.setHidden(False)
            else:
                name_text = item.text(0).strip().lower()
                matches = query in name_text
                item.setHidden(not matches)
                if matches and len(query) >= 2:
                    item.setExpanded(True)

    def select_by_char_id(self, char_id: str):
        for i in range(self._tree.topLevelItemCount()):
            item = self._tree.topLevelItem(i)
            if item.data(0, Qt.ItemDataRole.UserRole) == char_id:
                self._tree.setCurrentItem(item)
                return

    def _on_collapse_all(self):
        self._tree.collapseAll()

    def _on_expand_all(self):
        self._tree.expandAll()

    def _on_tree_selection(self, current: QTreeWidgetItem | None, _prev):
        if self._loading or not current:
            return
        item_type = current.data(0, Qt.ItemDataRole.UserRole + 1)
        char_id = current.data(0, Qt.ItemDataRole.UserRole)
        if item_type == "character" and char_id:
            char = next((c for c in self._characters if c.id == char_id), None)
            if char:
                self._current_char = char
                self.character_selected.emit(char_id)

    def _on_tree_double_click(self, item: QTreeWidgetItem, _col: int):
        item_type = item.data(0, Qt.ItemDataRole.UserRole + 1)
        if item_type == "character":
            self._on_edit_character()

    def _on_tree_context_menu(self, pos: QPoint):
        item = self._tree.itemAt(pos)
        if not item:
            return
        char_id = item.data(0, Qt.ItemDataRole.UserRole)
        char = next((c for c in self._characters if c.id == char_id), None)
        if not char:
            return
        self._current_char = char

        menu = QMenu(self)
        a_edit = menu.addAction("✏️  Editar Ficha Completa")
        a_rel = menu.addAction("🔗  Gestionar Relaciones...")
        menu.addSeparator()
        a_alias = menu.addAction("🏷️  Editar Alias de Detección...")
        menu.addSeparator()
        a_del = menu.addAction("🗑️  Eliminar Personaje")

        action = menu.exec(self._tree.viewport().mapToGlobal(pos))
        if action == a_edit:
            self._on_edit_character()
        elif action == a_rel:
            self._on_manage_relations(char)
        elif action == a_alias:
            self._on_edit_aliases(char)
        elif action == a_del:
            self._on_del_character()

    def _on_add_character(self):
        dlg = CharacterEditDialog(
            character=None, obras=self._obras,
            characters=self._characters, relations=self._relations, parent=self
        )
        if dlg.exec():
            char = dlg.get_character()
            self._characters.append(char)
            self._relations = dlg.get_all_relations()
            self._current_char = char
            self.character_added.emit(char)
            self.rebuild_tree()
            self.select_by_char_id(char.id)

    def _on_edit_character(self):
        if not self._current_char:
            QMessageBox.information(self, "Info", "Selecciona un personaje primero.")
            return

        dlg = CharacterEditDialog(
            character=self._current_char, obras=self._obras,
            characters=self._characters, relations=self._relations, parent=self
        )
        if dlg.exec():
            self._relations = dlg.get_all_relations()
            self.character_added.emit(self._current_char)
            self.rebuild_tree()
            self.select_by_char_id(self._current_char.id)

    def _on_del_character(self):
        if not self._current_char:
            return
        reply = QMessageBox.question(
            self, "Eliminar Personaje",
            f"¿Eliminar a '{self._current_char.name}' del universo?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            char_id = self._current_char.id
            self._characters = [c for c in self._characters if c.id != char_id]
            self._relations = [r for r in self._relations
                               if r.char_id_a != char_id and r.char_id_b != char_id]
            self._current_char = None
            self.character_deleted.emit(char_id)
            self.rebuild_tree()

    def _on_manage_relations(self, char: Character):
        dlg = RelationDialog(
            characters=self._characters,
            current_char_id=char.id,
            obras=self._obras,
            parent=self
        )
        if dlg.exec():
            data = dlg.get_data()
            if not data.get("target_id"):
                return
            new_rel = CharacterRelation(
                char_id_a=data["char_id_a"],
                char_id_b=data["char_id_b"],
                relation_type=data["relation_type"],
                label=data["label"],
                intensity=data["intensity"],
                obra_id=data["obra_id"],
            )
            self._relations.append(new_rel)
            self.character_added.emit(char)
            self.rebuild_tree()
            self.select_by_char_id(char.id)

    def _on_edit_aliases(self, char: Character):
        current_str = ", ".join(char.aliases)
        text, ok = QInputDialog.getText(
            self, f"Alias — {char.name}",
            "Nombres alternativos separados por coma:\n(ej: El Caballero Oscuro, Bruce, Bruno)",
            QLineEdit.EchoMode.Normal, current_str
        )
        if ok:
            aliases = [a.strip() for a in text.split(",") if a.strip()]
            char.aliases = aliases
            self.character_added.emit(char)
