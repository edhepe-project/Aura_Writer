"""
CharacterDock — Panel de personajes para Aura Writer.

Muestra:
  - Panel superior: Árbol relacional con jerarquía de relaciones y acciones CRUD
  - Panel inferior: Panel de contexto dinámico (apariciones por capítulo, obra, libro o universo)
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QSplitter, QFrame, QInputDialog, QMessageBox,
    QListWidget, QListWidgetItem, QMenu, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPoint
from PyQt6.QtGui import QFont, QColor
import qtawesome as qta

from core.models import Character, CharacterRelation
from core.theme_manager import ThemeManager
from ui.character_edit_dialog import CharacterEditDialog
from ui.relation_dialog import RelationDialog


class CharacterDock(QWidget):
    """
    Panel de personajes:
      - Arriba: Árbol relacional con botones + / - / editar
      - Abajo: Lista de apariciones y contexto dinámico
    """
    character_added     = pyqtSignal(object)   # Character
    character_deleted   = pyqtSignal(str)      # char_id
    character_selected  = pyqtSignal(str)      # char_id
    chapter_requested   = pyqtSignal(str)      # chapter_id → navegar

    def __init__(self, parent=None):
        super().__init__(parent)
        self._characters: list[Character] = []
        self._relations: list[CharacterRelation] = []
        self._obras: list = []
        self._current_char: Character | None = None
        self._loading = False

        self._build_ui()

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QFrame()
        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 0, 0, 0)
        title_lbl = QLabel("PERSONAJES")
        hl.addWidget(title_lbl)
        hl.addStretch()
        root.addWidget(header)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setHandleWidth(1)

        # ── A) ÁRBOL DE PERSONAJES ─────────────────────────────────
        tree_frame = QFrame()
        tl = QVBoxLayout(tree_frame)
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

        # Barra de búsqueda rápida para 1000+ personajes
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("🔍 Buscar personaje...")
        self._search_input.setClearButtonEnabled(True)
        self._search_input.setStyleSheet("""
            QLineEdit {
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                background-color: rgba(255, 255, 255, 0.07);
                border: 1px solid rgba(255, 255, 255, 0.12);
            }
            QLineEdit:focus {
                border: 1px solid #30d158;
            }
        """)
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
        splitter.addWidget(tree_frame)

        # ── B) PANEL DE CONTEXTO DINÁMICO ─────────────────────────
        context_frame = QFrame()
        al = QVBoxLayout(context_frame)
        al.setContentsMargins(8, 6, 8, 6)
        al.setSpacing(4)

        self._context_label = QLabel("INFORMACIÓN CONTEXTUAL")
        al.addWidget(self._context_label)

        self._context_sublabel = QLabel("")
        self._context_sublabel.setWordWrap(True)
        self._context_sublabel.hide()
        al.addWidget(self._context_sublabel)

        self._list_appear = QListWidget()
        self._list_appear.itemDoubleClicked.connect(self._on_appearance_clicked)
        al.addWidget(self._list_appear)
        splitter.addWidget(context_frame)

        splitter.setSizes([420, 230])
        root.addWidget(splitter)

    # ------------------------------------------------------------------
    # Helpers de estilo
    # ------------------------------------------------------------------

    def _icon_btn(self, icon_name: str, color: str, tooltip: str) -> QPushButton:
        btn = QPushButton()
        try:
            btn.setIcon(qta.icon(icon_name, color=color))
        except Exception:
            btn.setText(tooltip[0])
        btn.setToolTip(tooltip)
        btn.setFixedSize(QSize(28, 28))
        return btn

    # ------------------------------------------------------------------
    # Populate
    # ------------------------------------------------------------------

    def populate(self, characters: list[Character],
                 relations: list[CharacterRelation],
                 obras: list):
        self._loading = True
        self._characters = list(characters)
        self._relations = list(relations)
        self._obras = list(obras)
        prev_id = self._current_char.id if self._current_char else None
        self._rebuild_tree()
        if prev_id:
            self._select_tree_by_char_id(prev_id)
        self._loading = False

    def get_relations(self) -> list[CharacterRelation]:
        """Devuelve la lista actual de relaciones del dock."""
        return list(self._relations)

    def _rebuild_tree(self):
        self._tree.blockSignals(True)
        self._tree.clear()
        char_map = {c.id: c for c in self._characters}
        is_dark = ThemeManager.is_dark()

        # Pre-indexar relaciones O(R) en lugar de O(N*R)
        rels_by_char: dict[str, list[tuple[str, CharacterRelation, bool]]] = {}
        for rel in self._relations:
            rels_by_char.setdefault(rel.char_id_a, []).append((rel.char_id_b, rel, True))
            rels_by_char.setdefault(rel.char_id_b, []).append((rel.char_id_a, rel, False))

        # Ordenar alfabéticamente por nombre (con prioridad por jerarquía de rol)
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

            # Rol como subtexto
            role_item = QTreeWidgetItem(root_item)
            role_item.setText(0, f"      {char.role}")
            role_item.setForeground(0, QColor(sub_role_color))
            role_item.setFlags(role_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            role_fnt = QFont()
            role_fnt.setPointSize(9)
            role_fnt.setItalic(True)
            role_item.setFont(0, role_fnt)

            # Relaciones agrupadas con claridad de dirección
            grouped_rels: dict[str, tuple[str, str, list[tuple[Character, CharacterRelation]]]] = {}

            for other_id, rel, is_source in rels_by_char.get(char.id, []):
                rtype = rel.relation_type
                if is_source:
                    if rtype == "descendiente":
                        g_key, g_lbl, g_col = "es_descendiente", "👶 Es descendiente de:", "#2ecc71"
                    elif rtype == "mentor":
                        g_key, g_lbl, g_col = "es_mentor", "🎓 Es mentor de:", "#3498db"
                    elif rtype == "pareja":
                        g_key, g_lbl, g_col = "pareja", "👫 Pareja de:", "#e84393"
                    elif rtype == "familiar":
                        g_key, g_lbl, g_col = "familiar", "👨‍👩‍👧 Familiar de:", "#27ae60"
                    elif rtype == "rival":
                        g_key, g_lbl, g_col = "rival", "⚔️ Rival de:", "#e67e22"
                    elif rtype == "amigo":
                        g_key, g_lbl, g_col = "amigo", "🤝 Amigo de:", "#9b59b6"
                    else:
                        g_key, g_lbl, g_col = "otro", "👥 Vínculo con:", "#95a5a6"
                else:
                    if rtype == "descendiente":
                        g_key, g_lbl, g_col = "es_antepasado", "👴 Es progenitor / antepasado de:", "#27ae60"
                    elif rtype == "mentor":
                        g_key, g_lbl, g_col = "es_aprendiz", "📚 Es aprendiz de:", "#2980b9"
                    elif rtype == "pareja":
                        g_key, g_lbl, g_col = "pareja", "👫 Pareja de:", "#e84393"
                    elif rtype == "familiar":
                        g_key, g_lbl, g_col = "familiar", "👨‍👩‍👧 Familiar de:", "#27ae60"
                    elif rtype == "rival":
                        g_key, g_lbl, g_col = "rival", "⚔️ Rival de:", "#e67e22"
                    elif rtype == "amigo":
                        g_key, g_lbl, g_col = "amigo", "🤝 Amigo de:", "#9b59b6"
                    else:
                        g_key, g_lbl, g_col = "otro", "👥 Vínculo con:", "#95a5a6"

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

        # Si hay texto de búsqueda, re-aplicar filtro
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

    def _select_tree_by_char_id(self, char_id: str):
        for i in range(self._tree.topLevelItemCount()):
            item = self._tree.topLevelItem(i)
            if item.data(0, Qt.ItemDataRole.UserRole) == char_id:
                self._tree.setCurrentItem(item)
                return

    # ------------------------------------------------------------------
    # Menú contextual del árbol
    # ------------------------------------------------------------------

    def _on_tree_context_menu(self, pos: QPoint):
        item = self._tree.itemAt(pos)
        if not item:
            return

        rel_id = item.data(0, Qt.ItemDataRole.UserRole + 2)
        other_id = item.data(0, Qt.ItemDataRole.UserRole)

        menu = QMenu(self)

        if rel_id:
            act_edit   = menu.addAction("✏️  Editar relación")
            act_delete = menu.addAction("🗑️  Eliminar relación")
            chosen = menu.exec(self._tree.viewport().mapToGlobal(pos))
            if chosen == act_edit:
                self._edit_relation(rel_id, other_id)
            elif chosen == act_delete:
                self._delete_relation(rel_id)
        else:
            char_id = item.data(0, Qt.ItemDataRole.UserRole)
            item_type = item.data(0, Qt.ItemDataRole.UserRole + 1)
            if item_type == "character" and char_id:
                act_edit   = menu.addAction("✏️  Editar personaje")
                act_rename = menu.addAction("✏️  Renombrar")
                act_rel    = menu.addAction("🔗  Añadir relación")
                menu.addSeparator()
                act_del_ch = menu.addAction("🗑️  Eliminar personaje")
                chosen = menu.exec(self._tree.viewport().mapToGlobal(pos))
                if chosen == act_edit:
                    self._select_tree_by_char_id(char_id)
                    self._on_edit_character()
                elif chosen == act_rename:
                    char = next((c for c in self._characters if c.id == char_id), None)
                    if char:
                        new_name, ok = QInputDialog.getText(
                            self, "Renombrar", "Nuevo nombre:", text=char.name)
                        if ok and new_name.strip():
                            char.name = new_name.strip()
                            self.character_added.emit(char)
                            self._rebuild_tree()
                elif chosen == act_rel:
                    self._select_tree_by_char_id(char_id)
                    self._on_add_relation_from_context()
                elif chosen == act_del_ch:
                    self._select_tree_by_char_id(char_id)
                    self._on_del_character()

    def _edit_relation(self, rel_id: str, other_id: str):
        if not self._current_char:
            return
        rel = next((r for r in self._relations if r.id == rel_id), None)
        if not rel:
            return
        dlg = RelationDialog(
            self._characters, self._current_char.id,
            self._obras, relation=rel,
            fixed_target_id=other_id, parent=self
        )
        if dlg.exec():
            data = dlg.get_data()
            rel.char_id_a     = data.get("char_id_a", self._current_char.id)
            rel.char_id_b     = data.get("char_id_b", data["target_id"])
            rel.relation_type = data["relation_type"]
            rel.label         = data["label"]
            rel.intensity     = data["intensity"]
            rel.obra_id       = data["obra_id"]
            self.character_added.emit(self._current_char)
            self._rebuild_tree()
            self._select_tree_by_char_id(self._current_char.id)

    def _delete_relation(self, rel_id: str):
        reply = QMessageBox.question(
            self, "Eliminar Relación",
            "¿Eliminar esta relación?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._relations = [r for r in self._relations if r.id != rel_id]
            self.character_added.emit(self._current_char)
            self._rebuild_tree()
            if self._current_char:
                self._select_tree_by_char_id(self._current_char.id)

    def _on_add_relation_from_context(self):
        if not self._current_char:
            return
        if len(self._characters) < 2:
            QMessageBox.information(self, "Info",
                                    "Necesitas al menos 2 personajes para crear una relación.")
            return
        dlg = RelationDialog(self._characters, self._current_char.id,
                             self._obras, parent=self)
        if dlg.exec():
            data = dlg.get_data()
            if not data["target_id"]:
                return
            rel = CharacterRelation(
                char_id_a=data.get("char_id_a", self._current_char.id),
                char_id_b=data.get("char_id_b", data["target_id"]),
                relation_type=data["relation_type"],
                label=data["label"],
                intensity=data["intensity"],
                obra_id=data["obra_id"],
            )
            self._relations.append(rel)
            self.character_added.emit(self._current_char)
            self._rebuild_tree()
            self._select_tree_by_char_id(self._current_char.id)

    # ------------------------------------------------------------------
    # Selección en árbol
    # ------------------------------------------------------------------

    def _on_tree_selection(self, current: QTreeWidgetItem, _prev):
        if self._loading or current is None:
            return
        char_id   = current.data(0, Qt.ItemDataRole.UserRole)
        item_type = current.data(0, Qt.ItemDataRole.UserRole + 1)
        if item_type != "character" or not char_id:
            return
        char = next((c for c in self._characters if c.id == char_id), None)
        if char:
            self._current_char = char
            self.character_selected.emit(char.id)

    def _on_tree_double_click(self, item: QTreeWidgetItem, column: int):
        """Doble clic en un personaje → abrir ficha de edición."""
        if item is None:
            return
        char_id = item.data(0, Qt.ItemDataRole.UserRole)
        item_type = item.data(0, Qt.ItemDataRole.UserRole + 1)
        if item_type == "character" and char_id:
            char = next((c for c in self._characters if c.id == char_id), None)
            if char:
                self._current_char = char
                self._on_edit_character()

    # ------------------------------------------------------------------
    # Colapsar / expandir árbol
    # ------------------------------------------------------------------

    def _on_collapse_all(self):
        """Colapsa todos los nodos del árbol de personajes."""
        self._tree.collapseAll()

    def _on_expand_all(self):
        """Expande todos los nodos del árbol de personajes."""
        self._tree.expandAll()

    # ------------------------------------------------------------------
    # Añadir / editar / eliminar personajes
    # ------------------------------------------------------------------

    def _on_add_character(self):
        """Abre la ventana emergente para crear un nuevo personaje."""
        dlg = CharacterEditDialog(
            character=None,
            obras=self._obras,
            characters=self._characters,
            relations=self._relations,
            parent=self
        )
        if dlg.exec():
            char = dlg.get_character()
            self._characters.append(char)
            self._relations = dlg.get_relations()
            self._current_char = char
            self.character_added.emit(char)
            self._rebuild_tree()
            self._select_tree_by_char_id(char.id)

    def _on_edit_character(self):
        """Abre la ventana emergente para editar el personaje seleccionado."""
        if not self._current_char:
            QMessageBox.information(self, "Info", "Selecciona un personaje primero.")
            return

        char_rels = [r for r in self._relations
                     if r.char_id_a == self._current_char.id
                     or r.char_id_b == self._current_char.id]

        dlg = CharacterEditDialog(
            character=self._current_char,
            obras=self._obras,
            characters=self._characters,
            relations=char_rels,
            parent=self
        )
        if dlg.exec():
            other_rels = [r for r in self._relations
                          if r.char_id_a != self._current_char.id
                          and r.char_id_b != self._current_char.id]
            self._relations = other_rels + dlg.get_relations()
            self.character_added.emit(self._current_char)
            self._rebuild_tree()
            self._select_tree_by_char_id(self._current_char.id)

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
            self._relations  = [r for r in self._relations
                                if r.char_id_a != char_id and r.char_id_b != char_id]
            self._current_char = None
            self._list_appear.clear()
            self.character_deleted.emit(char_id)
            self._rebuild_tree()

    # ------------------------------------------------------------------
    # Relaciones (acceso externo)
    # ------------------------------------------------------------------

    def get_relations(self) -> list[CharacterRelation]:
        return self._relations

    # ------------------------------------------------------------------
    # Panel de contexto dinámico
    # ------------------------------------------------------------------

    def update_appearances(self, chapters_data: list[tuple]):
        """Muestra las apariciones del personaje seleccionado."""
        self._list_appear.clear()
        if not self._current_char:
            return
        self._context_label.setText(f"APARICIONES DE {self._current_char.name.upper()}")
        self._context_sublabel.setText(
            f"👤 {self._current_char.name} aparece en {len(chapters_data)} capítulo(s)"
        )
        self._context_sublabel.show()
        for cap, obra_title, libro_title in chapters_data:
            item = QListWidgetItem(f"📖 {cap.title}  ·  {obra_title} › {libro_title}")
            item.setData(Qt.ItemDataRole.UserRole, cap.id)
            item.setData(Qt.ItemDataRole.UserRole + 1, "chapter")
            self._list_appear.addItem(item)

    def update_context_for_chapter(self, chapter_title: str,
                                    characters_in_chapter: list[Character],
                                    obra_title: str, libro_title: str):
        """Muestra qué personajes interactúan en el capítulo seleccionado."""
        self._list_appear.clear()
        self._context_label.setText("PERSONAJES EN CAPÍTULO")
        self._context_sublabel.setText(
            f"📖 {chapter_title}  ·  {obra_title} › {libro_title}\n"
            f"{len(characters_in_chapter)} personaje(s) detectado(s)"
        )
        self._context_sublabel.show()
        if not characters_in_chapter:
            item = QListWidgetItem("  (ningún personaje detectado)")
            item.setForeground(QColor("#636366"))
            self._list_appear.addItem(item)
            return
        self._populate_character_list_items(characters_in_chapter)

    def update_context_for_obra(self, obra_title: str,
                                 characters_in_obra: list[Character],
                                 chapter_count: int):
        """Muestra qué personajes aparecen en la obra seleccionada."""
        self._list_appear.clear()
        self._context_label.setText("PERSONAJES EN OBRA")
        self._context_sublabel.setText(
            f"📖 {obra_title}\n"
            f"{len(characters_in_obra)} personaje(s) · {chapter_count} capítulo(s)"
        )
        self._context_sublabel.show()
        if not characters_in_obra:
            item = QListWidgetItem("  (ningún personaje detectado)")
            item.setForeground(QColor("#636366"))
            self._list_appear.addItem(item)
            return
        self._populate_character_list_items(characters_in_obra)

    def update_context_for_libro(self, libro_title: str, obra_title: str,
                                  characters_in_libro: list[Character],
                                  chapter_count: int):
        """Muestra qué personajes aparecen en el libro seleccionado."""
        self._list_appear.clear()
        self._context_label.setText("PERSONAJES EN LIBRO")
        self._context_sublabel.setText(
            f"📘 {libro_title}  ·  {obra_title}\n"
            f"{len(characters_in_libro)} personaje(s) · {chapter_count} capítulo(s)"
        )
        self._context_sublabel.show()
        if not characters_in_libro:
            item = QListWidgetItem("  (ningún personaje detectado)")
            item.setForeground(QColor("#636366"))
            self._list_appear.addItem(item)
            return
        self._populate_character_list_items(characters_in_libro)

    def update_context_for_universe(self, title: str,
                                     all_characters: list[Character],
                                     total_chapters: int, total_obras: int):
        """Muestra un resumen de todos los personajes del universo."""
        self._list_appear.clear()
        self._context_label.setText("RESUMEN DEL UNIVERSO")
        self._context_sublabel.setText(
            f"🌐 {title}\n"
            f"{len(all_characters)} personaje(s) · {total_obras} obra(s) · {total_chapters} capítulo(s)"
        )
        self._context_sublabel.show()
        self._populate_character_list_items(all_characters)

    def _populate_character_list_items(self, char_list: list[Character]):
        """Helper para renderizar una lista de personajes en el panel inferior."""
        role_icons = {
            "Protagonista": "⭐", "Antagonista": "🔴",
            "Secundario": "🔵", "Misterioso": "🟣", "Otro": "⚪"
        }
        role_colors = {
            "Protagonista": "#ffd60a", "Antagonista": "#ff453a",
            "Misterioso": "#bf5af2", "Secundario": "#f2f2f7",
            "Otro": "#8e8e93"
        }
        for char in char_list:
            icon = role_icons.get(char.role, "⚪")
            item = QListWidgetItem(f"{icon} {char.name}  ·  {char.role}")
            item.setData(Qt.ItemDataRole.UserRole, char.id)
            item.setData(Qt.ItemDataRole.UserRole + 1, "character")
            item.setForeground(QColor(role_colors.get(char.role, "#f2f2f7")))
            self._list_appear.addItem(item)

    def _on_appearance_clicked(self, item: QListWidgetItem):
        """Doble clic en un item del panel de contexto."""
        item_id = item.data(Qt.ItemDataRole.UserRole)
        item_type = item.data(Qt.ItemDataRole.UserRole + 1)
        if not item_id:
            return
        if item_type == "chapter":
            self.chapter_requested.emit(item_id)
        elif item_type == "character":
            self.select_character_by_id(item_id)

    # ------------------------------------------------------------------
    # Acceso externo
    # ------------------------------------------------------------------

    def get_current_char_id(self) -> str | None:
        return self._current_char.id if self._current_char else None

    def select_character_by_id(self, char_id: str):
        char = next((c for c in self._characters if c.id == char_id), None)
        if char:
            self._current_char = char
            self._select_tree_by_char_id(char_id)

    # ------------------------------------------------------------------
    # Compatibilidad: _save_current_card (lo llama main_window)
    # ------------------------------------------------------------------

    def _save_current_card(self):
        """No-op: los datos se guardan directamente al aceptar el diálogo."""
        pass
