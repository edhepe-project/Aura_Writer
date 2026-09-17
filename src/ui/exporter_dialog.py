from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                             QLineEdit, QPushButton, QComboBox, QFileDialog,
                             QFormLayout, QCheckBox)
from core.models import UniverseMetadata


class ExporterDialog(QDialog):
    def __init__(self, metadata: UniverseMetadata, suggested_title: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Exportar Obra - Aura Writer")
        self.setFixedWidth(480)
        self.meta = metadata
        self.suggested_title = suggested_title
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # Tipo de exportación
        self.export_type = QComboBox()
        self.export_type.addItems(["Borrador (DOCX)", "PDF Publicable (A5)", "E-Book (EPUB)"])
        self.export_type.currentIndexChanged.connect(self._on_format_changed)
        form.addRow("Formato:", self.export_type)

        # Metadatos
        self.title_input = QLineEdit(self.suggested_title or self.meta.title)
        form.addRow("Título:", self.title_input)

        self.author_input = QLineEdit(self.meta.author)
        form.addRow("Autor:", self.author_input)

        self.lang_input = QLineEdit("es")
        form.addRow("Idioma (ISO):", self.lang_input)

        layout.addLayout(form)

        # Opciones adicionales
        self.chk_author_notes = QCheckBox("Incluir notas de autor en la exportación")
        self.chk_author_notes.setChecked(False)
        self.chk_author_notes.setStyleSheet("margin-top: 8px; font-size: 12px;")
        layout.addWidget(self.chk_author_notes)

        # Ruta de salida
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.btn_path = QPushButton("Seleccionar…")
        self.btn_path.clicked.connect(self.select_path)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.btn_path)
        form.addRow("Guardar en:", path_layout)

        # Botones
        btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_export = QPushButton("Generar Archivo")
        btn_export.setStyleSheet(
            "background-color: #27ae60; color: white; font-weight: bold; padding: 8px 18px; border-radius: 6px;"
        )
        btn_export.clicked.connect(self.accept)

        btns.addStretch()
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_export)
        layout.addLayout(btns)

    def _on_format_changed(self, index: int):
        """Actualiza automáticamente la extensión del archivo si ya se había ingresado una ruta."""
        current_path = self.path_input.text().strip()
        if not current_path:
            return
        ext_map = {0: ".docx", 1: ".pdf", 2: ".epub"}
        new_ext = ext_map.get(index, ".docx")
        import os
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

    def get_config(self) -> dict:
        return {
            "type": self.export_type.currentIndex(),
            "title": self.title_input.text(),
            "author": self.author_input.text(),
            "language": self.lang_input.text(),
            "output_path": self.path_input.text(),
            "include_author_notes": self.chk_author_notes.isChecked(),
        }
