"""
Aura Writer — Exporter Dialog
Diálogo de configuración para exportación de obras.

MEJORA-2: Incluye selector de alcance explícito (Todo / Obra / Libro / Capítulo actual)
           en lugar de depender del nodo seleccionado en el árbol.
"""

import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                             QLineEdit, QPushButton, QComboBox, QFileDialog,
                             QFormLayout, QCheckBox, QLabel)
from PyQt6.QtCore import Qt
from core.models import UniverseMetadata


class ExporterDialog(QDialog):
    def __init__(self, metadata: UniverseMetadata, current_chapter=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Exportar Obra — Aura Writer")
        self.setFixedWidth(520)
        self.meta = metadata
        self.current_chapter = current_chapter  # Chapter | None
        self._scope_data = []   # lista de (label, type, id) para el combobox
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Alcance de exportación (MEJORA-2) --------------------------------
        self.scope_combo = QComboBox()
        self._populate_scope()
        form.addRow("Exportar:", self.scope_combo)

        # Formato -----------------------------------------------------------
        self.export_type = QComboBox()
        self.export_type.addItems(["Borrador (DOCX)", "PDF Publicable (A5 / 6x9)", "E-Book (EPUB)"])
        self.export_type.currentIndexChanged.connect(self._on_format_changed)
        form.addRow("Formato:", self.export_type)

        # Tamaño de Edición / Trim Size -------------------------------------
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItem("A5 (148 x 210 mm) — Estándar (Novelas cortas y medianas)", "a5")
        self.page_size_combo.addItem('6" x 9" (152 x 229 mm) — Gran Formato / Saga (Novelas extensas)', "6x9")
        form.addRow("Edición / Tamaño:", self.page_size_combo)

        # Metadatos ---------------------------------------------------------
        suggested_title = self.meta.title or "Mi Obra"
        self.title_input = QLineEdit(suggested_title)
        form.addRow("Título:", self.title_input)

        self.author_input = QLineEdit(self.meta.author or "")
        form.addRow("Autor:", self.author_input)

        self.lang_input = QLineEdit("es")
        form.addRow("Idioma (ISO):", self.lang_input)

        layout.addLayout(form)

        # Opciones adicionales ----------------------------------------------
        self.chk_author_notes = QCheckBox("Incluir notas de autor en la exportación")
        self.chk_author_notes.setChecked(False)
        self.chk_author_notes.setStyleSheet("margin-top: 4px; font-size: 12px;")
        layout.addWidget(self.chk_author_notes)

        self.chk_aura_protect = QCheckBox("🛡️ Activar protección forense 'Aura Protect' (Huella invisible y metadatos SHA-256)")
        self.chk_aura_protect.setChecked(True)
        self.chk_aura_protect.setStyleSheet("margin-top: 2px; font-size: 12px; font-weight: bold; color: #27ae60;")
        layout.addWidget(self.chk_aura_protect)

        # Ruta de salida ----------------------------------------------------
        path_form = QFormLayout()
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Selecciona dónde guardar el archivo…")
        self.btn_path = QPushButton("Seleccionar…")
        self.btn_path.clicked.connect(self.select_path)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.btn_path)
        path_form.addRow("Guardar en:", path_layout)
        layout.addLayout(path_form)

        # Botones -----------------------------------------------------------
        btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        self.btn_export = QPushButton("Generar Archivo")
        self.btn_export.setStyleSheet(
            "background-color: #27ae60; color: white; font-weight: bold;"
            " padding: 8px 18px; border-radius: 6px;"
        )
        self.btn_export.clicked.connect(self.accept)

        btns.addStretch()
        btns.addWidget(btn_cancel)
        btns.addWidget(self.btn_export)
        layout.addLayout(btns)

    # -----------------------------------------------------------------------
    # Scope population
    # -----------------------------------------------------------------------

    def _populate_scope(self):
        """Rellena el combobox de alcance con las obras y libros del proyecto."""
        self._scope_data = []
        self.scope_combo.clear()

        # Opción por defecto: todo el universo
        self._scope_data.append(("all", None))
        self.scope_combo.addItem("Todo el universo")

        for obra in self.meta.obras:
            label_obra = f"Obra: {obra.title}"
            self._scope_data.append(("obra", obra.id))
            self.scope_combo.addItem(label_obra)
            for libro in obra.libros:
                label_libro = f"    Libro: {libro.title}"
                self._scope_data.append(("libro", libro.id))
                self.scope_combo.addItem(label_libro)

        # Solo capítulo actual si hay uno abierto
        if self.current_chapter:
            label_cap = f"Solo: {self.current_chapter.title}"
            self._scope_data.append(("chapter", self.current_chapter.id))
            self.scope_combo.addItem(label_cap)
            # Preseleccionar el capítulo actual
            self.scope_combo.setCurrentIndex(len(self._scope_data) - 1)

    # -----------------------------------------------------------------------
    # Format / path helpers
    # -----------------------------------------------------------------------

    def _on_format_changed(self, index: int):
        """Actualiza automáticamente la extensión del archivo si ya hay ruta."""
        current_path = self.path_input.text().strip()
        if not current_path:
            return
        ext_map = {0: ".docx", 1: ".pdf", 2: ".epub"}
        new_ext = ext_map.get(index, ".docx")
        base, _ = os.path.splitext(current_path)
        self.path_input.setText(base + new_ext)

    def select_path(self):
        ext_map = {0: "DOCX (*.docx)", 1: "PDF (*.pdf)", 2: "EPUB (*.epub)"}
        selected_filter = ext_map.get(self.export_type.currentIndex(), "DOCX (*.docx)")
        default_filename = self.title_input.text().strip().replace(" ", "_")
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar exportación", default_filename, selected_filter
        )
        if path:
            self.path_input.setText(path)

    # -----------------------------------------------------------------------
    # Config output
    # -----------------------------------------------------------------------

    def get_config(self) -> dict:
        scope_idx = self.scope_combo.currentIndex()
        scope_type, scope_id = self._scope_data[scope_idx] if scope_idx < len(self._scope_data) else ("all", None)
        return {
            "type": self.export_type.currentIndex(),
            "title": self.title_input.text().strip(),
            "author": self.author_input.text().strip(),
            "language": self.lang_input.text().strip(),
            "output_path": self.path_input.text().strip(),
            "include_author_notes": self.chk_author_notes.isChecked(),
            "aura_protect": self.chk_aura_protect.isChecked(),
            "page_size": self.page_size_combo.currentData() or "a5",
            "scope_type": scope_type,
            "scope_id": scope_id,
        }
