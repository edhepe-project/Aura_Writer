"""
relation_dialog.py — Diálogo para crear o editar una relación entre dos personajes.
Extraído de character_dock.py para mantener archivos de tamaño manejable.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QComboBox,
    QLineEdit, QSpinBox, QDialogButtonBox
)
from PyQt6.QtCore import Qt

from core.models import Character, CharacterRelation
from core.theme_manager import ThemeManager


class RelationDialog(QDialog):
    """Diálogo para crear o editar una relación entre dos personajes con dirección clara."""

    RELATION_CHOICES = [
        ("👶 Es descendiente de... (hijo/a, nieto/a de)", "descendiente_de"),
        ("👴 Es progenitor / antepasado de... (padre/madre de)", "antepasado_de"),
        ("🎓 Es mentor / maestro de... (enseña a)", "mentor_de"),
        ("📚 Es aprendiz / discípulo de... (aprende de)", "aprendiz_de"),
        ("👫 Pareja / Cónyuge de...", "pareja"),
        ("👨‍👩‍👧 Familiar (hermano/a, primo/a, etc.) de...", "familiar"),
        ("⚔️ Rival / Enemigo de...", "rival"),
        ("🤝 Amigo / Aliado de...", "amigo"),
        ("👥 Otro vínculo con...", "otro"),
    ]

    def __init__(self, characters: list[Character], current_char_id: str,
                 obras: list, relation: CharacterRelation = None,
                 fixed_target_id: str = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Relación entre Personajes")
        self.setMinimumWidth(480)
        self.current_char_id = current_char_id
        curr_obj = next((c for c in characters if c.id == current_char_id), None)
        self.curr_name = curr_obj.name if curr_obj else "Personaje"

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        # ── Caja de Vista Previa en tiempo real ──
        is_dark = ThemeManager.is_dark()
        self.preview_lbl = QLabel()
        if is_dark:
            self.preview_lbl.setStyleSheet(
                "background: rgba(94, 92, 230, 0.2); border: 1px solid #5e5ce6; "
                "border-radius: 8px; padding: 10px 14px; font-size: 13px; color: #f2f2f7; font-weight: bold;"
            )
        else:
            self.preview_lbl.setStyleSheet(
                "background: #ede9fe; border: 1px solid #818cf8; "
                "border-radius: 8px; padding: 10px 14px; font-size: 13px; color: #3730a3; font-weight: bold;"
            )
        self.preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_lbl.setWordWrap(True)
        layout.addWidget(self.preview_lbl)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Personaje origen (fijo para claridad)
        self.lbl_origin = QLabel(f"<b>{self.curr_name}</b>")
        form.addRow("Personaje principal:", self.lbl_origin)

        # Personaje destino
        self.combo_target = QComboBox()
        for ch in characters:
            if ch.id != current_char_id:
                self.combo_target.addItem(ch.name, ch.id)
        if fixed_target_id:
            self.combo_target.setEnabled(False)
        form.addRow("Conectar con:", self.combo_target)

        # Tipo de relación
        self.combo_type = QComboBox()
        for label, code in self.RELATION_CHOICES:
            self.combo_type.addItem(label, code)
        form.addRow("Tipo de vínculo:", self.combo_type)

        # Label libre
        self.edit_label = QLineEdit()
        self.edit_label.setPlaceholderText("ej. 'hijo primogénito', 'maestro de esgrima'...")
        form.addRow("Detalle opcional:", self.edit_label)

        # Intensidad
        self.spin_intensity = QSpinBox()
        self.spin_intensity.setRange(1, 5)
        self.spin_intensity.setValue(2)
        form.addRow("Intensidad (1-5):", self.spin_intensity)

        # Obra (opcional)
        self.combo_obra = QComboBox()
        self.combo_obra.addItem("Universal (todas las obras)", "")
        for obra in obras:
            self.combo_obra.addItem(obra.title, obra.id)
        form.addRow("Específica de:", self.combo_obra)

        layout.addLayout(form)

        # Conectar cambios a la vista previa
        self.combo_target.currentIndexChanged.connect(self._update_preview)
        self.combo_type.currentIndexChanged.connect(self._update_preview)

        # Precargar valores si editando
        if relation:
            target_id = relation.char_id_b if relation.char_id_a == current_char_id else relation.char_id_a
            for i in range(self.combo_target.count()):
                if self.combo_target.itemData(i) == target_id:
                    self.combo_target.setCurrentIndex(i)
                    break

            rtype = relation.relation_type
            if rtype == "descendiente":
                code = "descendiente_de" if relation.char_id_a == current_char_id else "antepasado_de"
            elif rtype == "mentor":
                code = "mentor_de" if relation.char_id_a == current_char_id else "aprendiz_de"
            else:
                code = rtype

            for i in range(self.combo_type.count()):
                if self.combo_type.itemData(i) == code:
                    self.combo_type.setCurrentIndex(i)
                    break

            self.edit_label.setText(relation.label)
            self.spin_intensity.setValue(relation.intensity)
            for i in range(self.combo_obra.count()):
                if self.combo_obra.itemData(i) == relation.obra_id:
                    self.combo_obra.setCurrentIndex(i)
                    break

        # Prefill fixed target
        if fixed_target_id:
            for i in range(self.combo_target.count()):
                if self.combo_target.itemData(i) == fixed_target_id:
                    self.combo_target.setCurrentIndex(i)
                    break

        self._update_preview()

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                QDialogButtonBox.StandardButton.Cancel)
        btns.button(QDialogButtonBox.StandardButton.Ok).setText("Guardar Relación")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _update_preview(self):
        name_a = self.curr_name
        name_b = self.combo_target.currentText() or "Personaje B"
        choice = self.combo_type.currentData()

        if choice == "descendiente_de":
            sent = f"👶 <b>{name_a}</b> es descendiente (hijo/a, nieto/a) de <b>{name_b}</b>"
        elif choice == "antepasado_de":
            sent = f"👴 <b>{name_a}</b> es progenitor / antepasado de <b>{name_b}</b>"
        elif choice == "mentor_de":
            sent = f"🎓 <b>{name_a}</b> es mentor / maestro de <b>{name_b}</b>"
        elif choice == "aprendiz_de":
            sent = f"📚 <b>{name_a}</b> es aprendiz / alumno de <b>{name_b}</b>"
        elif choice == "pareja":
            sent = f"👫 <b>{name_a}</b> y <b>{name_b}</b> son pareja / cónyuges"
        elif choice == "familiar":
            sent = f"👨‍👩‍👧 <b>{name_a}</b> y <b>{name_b}</b> son familiares (hermanos, primos...)"
        elif choice == "rival":
            sent = f"⚔️ <b>{name_a}</b> es rival / enemigo de <b>{name_b}</b>"
        elif choice == "amigo":
            sent = f"🤝 <b>{name_a}</b> y <b>{name_b}</b> son amigos / aliados"
        else:
            sent = f"👥 <b>{name_a}</b> tiene un vínculo con <b>{name_b}</b>"

        self.preview_lbl.setText(f"💡 Vista previa: {sent}")

    def get_data(self) -> dict:
        target_id = self.combo_target.currentData()
        choice = self.combo_type.currentData()

        # Determinar A y B según la dirección seleccionada
        if choice == "descendiente_de":
            char_a = self.current_char_id
            char_b = target_id
            rtype = "descendiente"
        elif choice == "antepasado_de":
            char_a = target_id
            char_b = self.current_char_id
            rtype = "descendiente"
        elif choice == "mentor_de":
            char_a = self.current_char_id
            char_b = target_id
            rtype = "mentor"
        elif choice == "aprendiz_de":
            char_a = target_id
            char_b = self.current_char_id
            rtype = "mentor"
        else:
            char_a = self.current_char_id
            char_b = target_id
            rtype = choice

        return {
            "target_id":     target_id,
            "char_id_a":     char_a,
            "char_id_b":     char_b,
            "relation_type": rtype,
            "label":         self.edit_label.text().strip(),
            "intensity":     self.spin_intensity.value(),
            "obra_id":       self.combo_obra.currentData() or "",
        }
