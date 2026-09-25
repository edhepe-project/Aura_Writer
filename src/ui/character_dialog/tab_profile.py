"""
tab_profile.py — Pestaña de perfil para CharacterEditDialog (Identidad, Biografía, 7 Esencias, Atributos Dinámicos, Notas).
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QLineEdit, QComboBox, QFrame, QScrollArea,
    QCompleter
)
from PyQt6.QtCore import Qt, QStringListModel

from core.models import Character
from core.theme_manager import ThemeManager


class CharacterProfileTab(QWidget):
    """Pestaña de edición de perfil, datos biográficos, 7 campos esenciales y atributos personalizados."""

    def __init__(self, character: Character, characters: list[Character], parent=None):
        super().__init__(parent)
        self._char = character
        self._characters = characters
        self._attr_rows: list[tuple[QWidget, QLineEdit, QLineEdit]] = []
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        container = QWidget()
        container.setObjectName("profileContainer")
        container.setStyleSheet("QWidget#profileContainer { background: transparent; }")
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
        layout.addWidget(self._section_header("Esencia del Personaje"))

        layout.addWidget(self._section_label("Deseo motivador — su propósito vital"))
        self._edit_driving_desire = QTextEdit()
        self._edit_driving_desire.setPlaceholderText(
            "¿Qué quiere más que nada en la vida? Define su arco narrativo.\n"
            "Ej: busca redención, libertad, reconocimiento, conocimiento prohibido…"
        )
        self._edit_driving_desire.setMinimumHeight(60)
        self._edit_driving_desire.setMaximumHeight(120)
        layout.addWidget(self._edit_driving_desire)

        layout.addWidget(self._section_label("Miedo más profundo — su límite emocional"))
        self._edit_deepest_fear = QTextEdit()
        self._edit_deepest_fear.setPlaceholderText(
            "Lo que evita o teme convertirse; da vulnerabilidad y conflicto.\n"
            "Ej: teme perder control, ser olvidado, volverse igual que su enemigo…"
        )
        self._edit_deepest_fear.setMinimumHeight(60)
        self._edit_deepest_fear.setMaximumHeight(120)
        layout.addWidget(self._edit_deepest_fear)

        layout.addWidget(self._section_label("Valores y creencias — su brújula ética"))
        self._edit_core_values = QTextEdit()
        self._edit_core_values.setPlaceholderText(
            "Su visión del mundo y cómo juzga el bien y el mal.\n"
            "Ej: «La verdad siempre libera» · «La tradición debe prevalecer»…"
        )
        self._edit_core_values.setMinimumHeight(60)
        self._edit_core_values.setMaximumHeight(120)
        layout.addWidget(self._edit_core_values)

        layout.addWidget(self._section_label("Arco de transformación — inicio → medio → final"))
        self._edit_transformation_arc = QTextEdit()
        self._edit_transformation_arc.setPlaceholderText(
            "Su evolución emocional o espiritual dentro de la historia.\n"
            "Si este arco es sólido, el personaje se siente vivo ante el lector."
        )
        self._edit_transformation_arc.setMinimumHeight(60)
        self._edit_transformation_arc.setMaximumHeight(140)
        layout.addWidget(self._edit_transformation_arc)

        layout.addWidget(self._section_label("Tono o voz distintiva — cómo se expresa"))
        self._edit_distinctive_voice = QTextEdit()
        self._edit_distinctive_voice.setPlaceholderText(
            "Forma de hablar, ritmo, actitud ante otros — espejo de su identidad.\n"
            "Ej: calma solemne, sarcasmo constante, lenguaje ritualizado…"
        )
        self._edit_distinctive_voice.setMinimumHeight(60)
        self._edit_distinctive_voice.setMaximumHeight(120)
        layout.addWidget(self._edit_distinctive_voice)

        layout.addWidget(self._section_label("Símbolo o metáfora que representa"))
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
        layout.addWidget(self._section_header("Atributos Personalizados"))

        # Contenedor dinámico de filas
        self._attr_container = QWidget()
        self._attr_container.setStyleSheet("background: transparent;")
        self._attr_layout = QVBoxLayout(self._attr_container)
        self._attr_layout.setContentsMargins(0, 4, 0, 4)
        self._attr_layout.setSpacing(8)
        layout.addWidget(self._attr_container)

        self._lbl_empty_attrs = QLabel("Sin atributos adicionales. Haz clic en el botón inferior para añadir uno.")
        is_dark = ThemeManager.is_dark()
        empty_col = "#8e8e93" if is_dark else "#78716c"
        self._lbl_empty_attrs.setStyleSheet(
            f"color: {empty_col}; font-size: 11px; padding: 4px 2px; background: transparent;"
        )
        self._attr_layout.addWidget(self._lbl_empty_attrs)

        attr_btn_layout = QHBoxLayout()
        btn_add_attr = QPushButton("Añadir Atributo")
        btn_add_attr.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add_attr.clicked.connect(lambda: self.add_custom_attr())

        attr_btn_layout.addWidget(btn_add_attr)
        attr_btn_layout.addStretch()
        layout.addLayout(attr_btn_layout)

        layout.addWidget(self._separator())

        # SECCIÓN: NOTAS DEL AUTOR
        layout.addWidget(self._section_header("Notas privadas del autor"))
        self._edit_notes = QTextEdit()
        self._edit_notes.setPlaceholderText("Notas del autor (no se exportan)…")
        self._edit_notes.setMinimumHeight(70)
        self._edit_notes.setMaximumHeight(140)
        layout.addWidget(self._edit_notes)

        layout.addStretch()
        scroll.setWidget(container)
        root.addWidget(scroll)

    # ------------------------------------------------------------------
    # Autocompletado de atributos
    # ------------------------------------------------------------------

    def _get_known_attribute_keys(self) -> list[str]:
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
    # Gestión de filas dinámicas
    # ------------------------------------------------------------------

    def add_custom_attr(self, key: str = "", val: str = ""):
        if not isinstance(key, str):
            key = ""
        if not isinstance(val, str):
            val = ""

        self._lbl_empty_attrs.hide()

        row_widget = QWidget()
        row_widget.setStyleSheet("background: transparent;")
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)

        # Campo Clave (Atributo)
        key_edit = QLineEdit(key)
        key_edit.setPlaceholderText("Atributo (ej. Raza, Facción, Rango…)")
        known_keys = self._get_known_attribute_keys()

        key_model = QStringListModel(known_keys, key_edit)
        key_completer = QCompleter(key_model, key_edit)
        key_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        key_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        key_edit.setCompleter(key_completer)

        # Separador visual
        is_dark = ThemeManager.is_dark()
        arrow_col = "#636366" if is_dark else "#a8a29e"
        sep_lbl = QLabel(":")
        sep_lbl.setStyleSheet(f"color: {arrow_col}; font-weight: bold; font-size: 14px; background: transparent;")

        # Campo Valor
        val_edit = QLineEdit(val)
        val_edit.setPlaceholderText("Valor (ej. Elfo, Capitán, Fuego…)")

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

        # Botón de eliminar directo en la fila
        btn_del = QPushButton("✕")
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.setToolTip("Eliminar este atributo")
        btn_del.setFixedSize(28, 28)
        del_bg = "rgba(255, 69, 58, 0.12)" if is_dark else "rgba(220, 38, 38, 0.1)"
        del_hover = "rgba(255, 69, 58, 0.3)" if is_dark else "rgba(220, 38, 38, 0.25)"
        del_color = "#ff453a" if is_dark else "#dc2626"
        btn_del.setStyleSheet(f"""
            QPushButton {{
                background-color: {del_bg};
                color: {del_color};
                border: 1px solid transparent;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                padding: 0;
            }}
            QPushButton:hover {{
                background-color: {del_hover};
                border: 1px solid {del_color};
            }}
        """)

        def _remove_this_row():
            if (row_widget, key_edit, val_edit) in self._attr_rows:
                self._attr_rows.remove((row_widget, key_edit, val_edit))
            row_widget.deleteLater()
            if not self._attr_rows:
                self._lbl_empty_attrs.show()

        btn_del.clicked.connect(_remove_this_row)

        row_layout.addWidget(key_edit, 2)
        row_layout.addWidget(sep_lbl)
        row_layout.addWidget(val_edit, 3)
        row_layout.addWidget(btn_del)

        self._attr_rows.append((row_widget, key_edit, val_edit))
        self._attr_layout.addWidget(row_widget)

    # ------------------------------------------------------------------
    # Carga y Guardado
    # ------------------------------------------------------------------

    def load_from_character(self, char: Character):
        self._char = char
        self._edit_name.setText(char.name)
        idx = self._combo_role.findText(char.role)
        self._combo_role.setCurrentIndex(max(0, idx))
        self._edit_aliases.setText(", ".join(char.aliases))

        # Datos biográficos
        self._edit_description.setPlainText(char.description)
        self._edit_age.setText(char.age)
        self._edit_birth_date.setText(char.birth_date)
        self._edit_birthplace.setText(char.birthplace)

        # 7 campos esenciales
        self._edit_driving_desire.setPlainText(char.driving_desire)
        self._edit_deepest_fear.setPlainText(char.deepest_fear)
        self._edit_core_values.setPlainText(char.core_values)
        self._edit_transformation_arc.setPlainText(char.transformation_arc)
        self._edit_distinctive_voice.setPlainText(char.distinctive_voice)
        self._edit_symbol_metaphor.setPlainText(char.symbol_metaphor)

        # Cargar atributos personalizados
        for row_w, _, _ in list(self._attr_rows):
            row_w.deleteLater()
        self._attr_rows.clear()
        self._lbl_empty_attrs.show()

        for k, v in char.custom_attributes.items():
            self.add_custom_attr(k, v)

        # Notas
        self._edit_notes.setPlainText(char.notes)

    def save_to_character(self, char: Character):
        raw_aliases = self._edit_aliases.text()
        char.name = self._edit_name.text().strip()
        char.role = self._combo_role.currentText()
        char.aliases = [a.strip() for a in raw_aliases.split(",") if a.strip()]
        char.description = self._edit_description.toPlainText()
        char.notes = self._edit_notes.toPlainText()
        char.age = self._edit_age.text().strip()
        char.birth_date = self._edit_birth_date.text().strip()
        char.birthplace = self._edit_birthplace.text().strip()
        char.driving_desire = self._edit_driving_desire.toPlainText()
        char.deepest_fear = self._edit_deepest_fear.toPlainText()
        char.core_values = self._edit_core_values.toPlainText()
        char.transformation_arc = self._edit_transformation_arc.toPlainText()
        char.distinctive_voice = self._edit_distinctive_voice.toPlainText()
        char.symbol_metaphor = self._edit_symbol_metaphor.toPlainText()

        custom_attrs = {}
        for _, key_edit, val_edit in self._attr_rows:
            k = key_edit.text().strip()
            v = val_edit.text().strip()
            if k:
                custom_attrs[k] = v
        char.custom_attributes = custom_attrs

    def get_name(self) -> str:
        return self._edit_name.text().strip()

    def focus_name_input(self):
        self._edit_name.setFocus()

    # ------------------------------------------------------------------
    # UI Helpers
    # ------------------------------------------------------------------

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

    @staticmethod
    def _section_header(text: str) -> QLabel:
        is_dark = ThemeManager.is_dark()
        color = "#f2f2f7" if is_dark else "#1a1a2e"
        bg_bar = "rgba(255, 255, 255, 0.04)" if is_dark else "rgba(0, 0, 0, 0.04)"
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {color}; font-size: 13px; font-weight: 800; "
            f"background: {bg_bar}; border-left: 3px solid #5e5ce6; "
            f"padding: 6px 10px; border-radius: 4px; margin-top: 6px;"
        )
        return lbl

    @staticmethod
    def _separator() -> QFrame:
        is_dark = ThemeManager.is_dark()
        sep_color = "#3a3a3c" if is_dark else "#d4cfc8"
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background: {sep_color}; height: 1px; border: none; margin: 8px 0;")
        return sep
