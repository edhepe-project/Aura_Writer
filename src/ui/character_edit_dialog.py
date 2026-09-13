"""
character_edit_dialog.py — Diálogo de creación / edición completa de personaje en Aura Writer.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QLineEdit, QComboBox, QFrame, QMessageBox,
    QDialog, QScrollArea, QMenu, QTabWidget,
    QTableWidget, QHeaderView, QCompleter,
    QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QPoint, QStringListModel
from PyQt6.QtGui import QColor

from core.models import Character, CharacterRelation, RELATION_COLORS
from ui.relation_dialog import RelationDialog
from ui.genealogy_widget import GenealogyWidget


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
        self._characters = characters or []
        self._relations = list(relations or [])

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
        header_lbl = QLabel("👤  FICHA DE PERSONAJE")
        root.addWidget(header_lbl)

        # Tabs
        self._tabs = QTabWidget()
        root.addWidget(self._tabs, 1)

        # Tab 1: Perfil
        self._tabs.addTab(self._build_profile_tab(), "📋 Perfil")

        # Tab 2: Relaciones
        self._tabs.addTab(self._build_relations_tab(), "🔗 Relaciones")

        # Tab 3: Genealogía / Mapa conceptual
        if not self._is_new:
            self._genealogy_widget = GenealogyWidget(
                self._char, self._characters, self._relations, parent=self
            )
            self._tabs.addTab(self._genealogy_widget, "🗺️ Genealogía")

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

    # ------------------------------------------------------------------
    # Tab: Perfil
    # ------------------------------------------------------------------

    def _build_profile_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(10)

        # SECCIÓN: IDENTIDAD
        layout.addWidget(self._section_header("🪪  Identidad"))

        layout.addWidget(self._section_label("Nombre"))
        self._edit_name = QLineEdit()
        self._edit_name.setPlaceholderText("Nombre del personaje")
        layout.addWidget(self._edit_name)

        layout.addWidget(self._section_label("Rol"))
        self._combo_role = QComboBox()
        self._combo_role.addItems(["Protagonista", "Secundario", "Antagonista", "Misterioso", "Otro"])
        layout.addWidget(self._combo_role)

        layout.addWidget(self._section_label("Aliases / nombres alternativos"))
        self._edit_aliases = QLineEdit()
        self._edit_aliases.setPlaceholderText("Separados por coma: El Viejo, Don Quijote…")
        layout.addWidget(self._edit_aliases)

        layout.addWidget(self._separator())

        # SECCIÓN: DATOS BIOGRÁFICOS
        layout.addWidget(self._section_header("📖  Datos Biográficos"))

        layout.addWidget(self._section_label("Descripción"))
        self._edit_description = QTextEdit()
        self._edit_description.setPlaceholderText("Descripción física, personalidad, rasgos distintivos…")
        self._edit_description.setMinimumHeight(80)
        self._edit_description.setMaximumHeight(160)
        layout.addWidget(self._edit_description)

        bio_row1 = QHBoxLayout()
        bio_row1.setSpacing(10)

        col_age = QVBoxLayout()
        col_age.setSpacing(2)
        col_age.addWidget(self._section_label("Edad"))
        self._edit_age = QLineEdit()
        self._edit_age.setPlaceholderText("ej. 32 años, Inmortal…")
        col_age.addWidget(self._edit_age)
        bio_row1.addLayout(col_age, 1)

        col_bdate = QVBoxLayout()
        col_bdate.setSpacing(2)
        col_bdate.addWidget(self._section_label("Fecha de nacimiento"))
        self._edit_birth_date = QLineEdit()
        self._edit_birth_date.setPlaceholderText("ej. 15 de marzo, Era del Fuego…")
        col_bdate.addWidget(self._edit_birth_date)
        bio_row1.addLayout(col_bdate, 1)

        layout.addLayout(bio_row1)

        layout.addWidget(self._section_label("Lugar de nacimiento"))
        self._edit_birthplace = QLineEdit()
        self._edit_birthplace.setPlaceholderText("ej. Aldea de Vientofrío, Reino del Norte…")
        layout.addWidget(self._edit_birthplace)

        layout.addWidget(self._separator())

        # SECCIÓN: 7 CAMPOS ESENCIALES
        layout.addWidget(self._section_header("✨  Esencia del Personaje"))

        layout.addWidget(self._section_label("🔥 Deseo motivador — su propósito vital"))
        self._edit_driving_desire = QTextEdit()
        self._edit_driving_desire.setPlaceholderText(
            "¿Qué quiere más que nada en la vida? Define su arco narrativo.\n"
            "Ej: busca redención, libertad, reconocimiento, conocimiento prohibido…"
        )
        self._edit_driving_desire.setMinimumHeight(60)
        self._edit_driving_desire.setMaximumHeight(120)
        layout.addWidget(self._edit_driving_desire)

        layout.addWidget(self._section_label("😨 Miedo más profundo — su límite emocional"))
        self._edit_deepest_fear = QTextEdit()
        self._edit_deepest_fear.setPlaceholderText(
            "Lo que evita o teme convertirse; da vulnerabilidad y conflicto.\n"
            "Ej: teme perder control, ser olvidado, volverse igual que su enemigo…"
        )
        self._edit_deepest_fear.setMinimumHeight(60)
        self._edit_deepest_fear.setMaximumHeight(120)
        layout.addWidget(self._edit_deepest_fear)

        layout.addWidget(self._section_label("⚖️ Valores y creencias — su brújula ética"))
        self._edit_core_values = QTextEdit()
        self._edit_core_values.setPlaceholderText(
            "Su visión del mundo y cómo juzga el bien y el mal.\n"
            "Ej: «La verdad siempre libera» · «La tradición debe prevalecer»…"
        )
        self._edit_core_values.setMinimumHeight(60)
        self._edit_core_values.setMaximumHeight(120)
        layout.addWidget(self._edit_core_values)

        layout.addWidget(self._section_label("🔄 Arco de transformación — inicio → medio → final"))
        self._edit_transformation_arc = QTextEdit()
        self._edit_transformation_arc.setPlaceholderText(
            "Su evolución emocional o espiritual dentro de la historia.\n"
            "Si este arco es sólido, el personaje se siente vivo ante el lector."
        )
        self._edit_transformation_arc.setMinimumHeight(60)
        self._edit_transformation_arc.setMaximumHeight(140)
        layout.addWidget(self._edit_transformation_arc)

        layout.addWidget(self._section_label("🗣️ Tono o voz distintiva — cómo se expresa"))
        self._edit_distinctive_voice = QTextEdit()
        self._edit_distinctive_voice.setPlaceholderText(
            "Forma de hablar, ritmo, actitud ante otros — espejo de su identidad.\n"
            "Ej: calma solemne, sarcasmo constante, lenguaje ritualizado…"
        )
        self._edit_distinctive_voice.setMinimumHeight(60)
        self._edit_distinctive_voice.setMaximumHeight(120)
        layout.addWidget(self._edit_distinctive_voice)

        layout.addWidget(self._section_label("🜁 Símbolo o metáfora que representa"))
        self._edit_symbol_metaphor = QTextEdit()
        self._edit_symbol_metaphor.setPlaceholderText(
            "Su función temática: ¿encarna el sacrificio, el caos, la esperanza?\n"
            "Lo conecta con el mensaje mayor de tu universo."
        )
        self._edit_symbol_metaphor.setMinimumHeight(60)
        self._edit_symbol_metaphor.setMaximumHeight(120)
        layout.addWidget(self._edit_symbol_metaphor)

        layout.addWidget(self._separator())

        # SECCIÓN: ATRIBUTOS PERSONALIZADOS
        layout.addWidget(self._section_header("🏷️  Atributos Personalizados"))

        self._table_custom_attr = QTableWidget(0, 2)
        self._table_custom_attr.setHorizontalHeaderLabels(["Atributo (Ej. Raza)", "Valor (Ej. Elfo)"])
        self._table_custom_attr.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._table_custom_attr.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table_custom_attr.setMinimumHeight(120)
        self._table_custom_attr.setMaximumHeight(200)
        layout.addWidget(self._table_custom_attr)

        attr_btn_layout = QHBoxLayout()
        btn_add_attr = QPushButton("+ Añadir Atributo")
        btn_add_attr.clicked.connect(lambda: self._add_custom_attr())

        btn_del_attr = QPushButton("- Eliminar")
        btn_del_attr.clicked.connect(self._remove_custom_attr)

        attr_btn_layout.addWidget(btn_add_attr)
        attr_btn_layout.addWidget(btn_del_attr)
        attr_btn_layout.addStretch()
        layout.addLayout(attr_btn_layout)

        layout.addWidget(self._separator())

        # SECCIÓN: NOTAS DEL AUTOR
        layout.addWidget(self._section_header("📝  Notas privadas del autor"))
        self._edit_notes = QTextEdit()
        self._edit_notes.setPlaceholderText("Notas del autor (no se exportan)…")
        self._edit_notes.setMinimumHeight(70)
        self._edit_notes.setMaximumHeight(140)
        layout.addWidget(self._edit_notes)

        layout.addStretch()
        scroll.setWidget(container)
        return scroll

    # ------------------------------------------------------------------
    # Tab: Relaciones
    # ------------------------------------------------------------------

    def _build_relations_tab(self) -> QWidget:
        container = QWidget()
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

        info = QLabel("Clic derecho en una relación para editar o eliminar")
        layout.addWidget(info)

        self._refresh_rel_list()
        return container

    def _refresh_rel_list(self):
        if not hasattr(self, '_rel_list'):
            return
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
                    text = f"👶 Descendiente (hijo/a) de → {other.name}"
                else:
                    text = f"👴 Progenitor / Antepasado de → {other.name}"
            elif rtype == "mentor":
                if rel.char_id_a == self._char.id:
                    text = f"🎓 Mentor de → {other.name}"
                else:
                    text = f"📚 Aprendiz de → {other.name}"
            elif rtype == "pareja":
                text = f"👫 Pareja de → {other.name}"
            elif rtype == "familiar":
                text = f"👨‍👩‍👧 Familiar de → {other.name}"
            elif rtype == "rival":
                text = f"⚔️ Rival de → {other.name}"
            elif rtype == "amigo":
                text = f"🤝 Amigo de → {other.name}"
            else:
                text = f"👥 Vínculo con → {other.name}"

            if rel.label:
                text += f"  ·  {rel.label}"

            color = RELATION_COLORS.get(rtype, "#636366")
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, rel.id)
            item.setData(Qt.ItemDataRole.UserRole + 1, other_id)
            item.setForeground(QColor(color))
            self._rel_list.addItem(item)

        if hasattr(self, '_genealogy_widget'):
            self._genealogy_widget.set_data(self._char, self._characters, self._relations)

    def _on_rel_context_menu(self, pos: QPoint):
        item = self._rel_list.itemAt(pos)
        if not item:
            return
        rel_id = item.data(Qt.ItemDataRole.UserRole)
        other_id = item.data(Qt.ItemDataRole.UserRole + 1)

        menu = QMenu(self)
        act_edit = menu.addAction("✏️  Editar relación")
        act_delete = menu.addAction("🗑️  Eliminar relación")
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
                    self._refresh_rel_list()
        elif chosen == act_delete:
            reply = QMessageBox.question(
                self, "Eliminar Relación", "¿Eliminar esta relación?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._relations = [r for r in self._relations if r.id != rel_id]
                self._refresh_rel_list()

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
            self._refresh_rel_list()

    # ------------------------------------------------------------------
    # Autocompletado de atributos
    # ------------------------------------------------------------------

    def _get_known_attribute_keys(self) -> list[str]:
        """Obtiene todos los nombres de atributos existentes en los personajes del universo."""
        keys = set()
        for ch in self._characters:
            if ch.custom_attributes:
                keys.update(ch.custom_attributes.keys())
        default_keys = [
            "Raza / Especie", "Facción / Gremio", "Rango / Título",
            "Nacionalidad", "Ocupación / Clase", "Afinidad Mágica / Elemento",
            "Arma Principal", "Estado Vital", "Nivel de Poder", "Linaje / Clan"
        ]
        return sorted(list(keys)) + [k for k in default_keys if k not in keys]

    def _get_known_values_for_key(self, key_name: str) -> list[str]:
        """Obtiene todos los valores previamente utilizados para un atributo específico."""
        if not key_name:
            return []
        vals = set()
        k_lower = key_name.strip().lower()
        for ch in self._characters:
            if ch.custom_attributes:
                for k, v in ch.custom_attributes.items():
                    if k.strip().lower() == k_lower and v.strip():
                        vals.add(v.strip())
        return sorted(list(vals))

    # ------------------------------------------------------------------
    # Atributos personalizados
    # ------------------------------------------------------------------

    def _add_custom_attr(self, key: str = "", val: str = ""):
        """Añade una fila de atributo con autocompletado dinámico y seguro."""
        if not isinstance(key, str):
            key = ""
        if not isinstance(val, str):
            val = ""

        row = self._table_custom_attr.rowCount()
        self._table_custom_attr.insertRow(row)

        key_edit = QLineEdit(key)
        key_edit.setPlaceholderText("ej. Raza, Facción, Rango…")
        known_keys = self._get_known_attribute_keys()
        
        key_model = QStringListModel(known_keys, key_edit)
        key_completer = QCompleter(key_model, key_edit)
        key_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        key_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        key_edit.setCompleter(key_completer)

        val_edit = QLineEdit(val)
        val_edit.setPlaceholderText("ej. Elfo, Capitán, Fuego…")

        val_model = QStringListModel([], val_edit)
        val_completer = QCompleter(val_model, val_edit)
        val_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        val_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        val_edit.setCompleter(val_completer)

        def _update_val_suggestions():
            current_k = key_edit.text().strip()
            known_vals = self._get_known_values_for_key(current_k)
            val_model.setStringList(known_vals)

        key_edit.textChanged.connect(lambda _: _update_val_suggestions())
        _update_val_suggestions()

        self._table_custom_attr.setCellWidget(row, 0, key_edit)
        self._table_custom_attr.setCellWidget(row, 1, val_edit)

    def _remove_custom_attr(self):
        row = self._table_custom_attr.currentRow()
        if row >= 0:
            self._table_custom_attr.removeRow(row)

    def _save_all_fields(self):
        """Persiste todos los campos del perfil en el objeto Character."""
        self._char.description = self._edit_description.toPlainText()
        self._char.notes = self._edit_notes.toPlainText()
        self._char.age = self._edit_age.text().strip()
        self._char.birth_date = self._edit_birth_date.text().strip()
        self._char.birthplace = self._edit_birthplace.text().strip()
        self._char.driving_desire = self._edit_driving_desire.toPlainText()
        self._char.deepest_fear = self._edit_deepest_fear.toPlainText()
        self._char.core_values = self._edit_core_values.toPlainText()
        self._char.transformation_arc = self._edit_transformation_arc.toPlainText()
        self._char.distinctive_voice = self._edit_distinctive_voice.toPlainText()
        self._char.symbol_metaphor = self._edit_symbol_metaphor.toPlainText()

        custom_attrs = {}
        for row in range(self._table_custom_attr.rowCount()):
            key_w = self._table_custom_attr.cellWidget(row, 0)
            val_w = self._table_custom_attr.cellWidget(row, 1)
            if key_w and val_w and isinstance(key_w, QLineEdit) and isinstance(val_w, QLineEdit):
                k = key_w.text().strip()
                v = val_w.text().strip()
            else:
                k_item = self._table_custom_attr.item(row, 0)
                v_item = self._table_custom_attr.item(row, 1)
                k = k_item.text().strip() if k_item else ""
                v = v_item.text().strip() if v_item else ""
            if k:
                custom_attrs[k] = v
        self._char.custom_attributes = custom_attrs

    # ------------------------------------------------------------------
    # Cargar datos desde un Character existente
    # ------------------------------------------------------------------

    def _load_from_character(self):
        self._edit_name.setText(self._char.name)
        idx = self._combo_role.findText(self._char.role)
        self._combo_role.setCurrentIndex(max(0, idx))
        self._edit_aliases.setText(", ".join(self._char.aliases))

        # Datos biográficos
        self._edit_description.setPlainText(self._char.description)
        self._edit_age.setText(self._char.age)
        self._edit_birth_date.setText(self._char.birth_date)
        self._edit_birthplace.setText(self._char.birthplace)

        # 7 campos esenciales
        self._edit_driving_desire.setPlainText(self._char.driving_desire)
        self._edit_deepest_fear.setPlainText(self._char.deepest_fear)
        self._edit_core_values.setPlainText(self._char.core_values)
        self._edit_transformation_arc.setPlainText(self._char.transformation_arc)
        self._edit_distinctive_voice.setPlainText(self._char.distinctive_voice)
        self._edit_symbol_metaphor.setPlainText(self._char.symbol_metaphor)

        self._table_custom_attr.setRowCount(0)
        for k, v in self._char.custom_attributes.items():
            self._add_custom_attr(k, v)

        # Notas
        self._edit_notes.setPlainText(self._char.notes)

    # ------------------------------------------------------------------
    # Guardar
    # ------------------------------------------------------------------

    def _on_save(self):
        name = self._edit_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Campo requerido", "El nombre del personaje es obligatorio.")
            self._edit_name.setFocus()
            return

        self._char.name = name
        self._char.role = self._combo_role.currentText()
        raw_aliases = self._edit_aliases.text()
        self._char.aliases = [a.strip() for a in raw_aliases.split(",") if a.strip()]
        self._save_all_fields()

        self.accept()

    # ------------------------------------------------------------------
    # Resultados
    # ------------------------------------------------------------------

    def get_character(self) -> Character:
        return self._char

    def get_relations(self) -> list[CharacterRelation]:
        return self._relations

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _section_label(text: str) -> QLabel:
        lbl = QLabel(text.upper())
        return lbl

    @staticmethod
    def _section_header(text: str) -> QLabel:
        lbl = QLabel(text)
        return lbl

    @staticmethod
    def _separator() -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        return sep
