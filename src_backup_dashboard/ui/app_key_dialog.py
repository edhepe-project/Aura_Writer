"""
AppKeyDialog — Diálogo para consultar, generar o configurar la Llave Maestra de Aplicación.
Permite portar la seguridad de Aura Writer a equipos nuevos fácilmente.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame, QApplication
)
from PyQt6.QtCore import Qt
from core.security import SecurityManager


class AppKeyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔑 Llave Maestra de Aplicación")
        self.setFixedSize(540, 390)
        self.setup_ui()

    def setup_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(20, 20, 20, 20)

        # ── Encabezado informativo ──────────────────────────────────
        title = QLabel("<b>Configuración de Llave Maestra</b>")
        title.setStyleSheet("font-size: 15px; color: #f2f2f7;")
        root.addWidget(title)

        desc = QLabel(
            "Esta llave es la segunda capa de cifrado de tus proyectos. "
            "Cada usuario tiene una llave única generada automáticamente. "
            "Si trasladas tus archivos <code>.aura</code> a una computadora nueva, "
            "ingresa aquí la misma llave para poder abrirlos con tu contraseña."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #8e8e93; font-size: 12px;")
        root.addWidget(desc)

        # ── Separador ───────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #3a3a3c;")
        root.addWidget(sep)

        # ── Llave actual (con botón copiar) ─────────────────────────
        lbl_current = QLabel("<b>Llave activa en este equipo:</b>")
        root.addWidget(lbl_current)

        row_current = QHBoxLayout()
        self.txt_current = QLineEdit()
        self.txt_current.setReadOnly(True)
        self.txt_current.setText(SecurityManager.get_app_key_hex())
        self.txt_current.setStyleSheet(
            "font-family: 'Consolas', 'Courier New', monospace; font-size: 11px; padding: 6px;"
        )
        row_current.addWidget(self.txt_current)

        btn_copy = QPushButton("📋 Copiar")
        btn_copy.setStyleSheet("padding: 6px 12px;")
        btn_copy.clicked.connect(self._copy_current)
        row_current.addWidget(btn_copy)
        root.addLayout(row_current)

        # ── Ingresar o generar nueva llave ──────────────────────────
        row_new_label = QHBoxLayout()
        lbl_new = QLabel("<b>Ingresar o generar nueva llave:</b>")
        row_new_label.addWidget(lbl_new)
        row_new_label.addStretch()

        btn_generate = QPushButton("🎲 Generar Aleatoria")
        btn_generate.setStyleSheet("padding: 4px 10px; font-size: 11px;")
        btn_generate.clicked.connect(self._generate_random_key)
        row_new_label.addWidget(btn_generate)
        root.addLayout(row_new_label)

        self.txt_new = QLineEdit()
        self.txt_new.setPlaceholderText("Pega aquí una llave de 64 caracteres o presiona Generar...")
        self.txt_new.setStyleSheet(
            "font-family: 'Consolas', 'Courier New', monospace; font-size: 11px; padding: 6px;"
        )
        self.txt_new.textChanged.connect(self._on_text_changed)
        root.addWidget(self.txt_new)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("font-size: 11px;")
        root.addWidget(self.lbl_status)

        root.addStretch()

        # ── Botones de acción ───────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("Cerrar")
        btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton("💾 Guardar Llave")
        self.btn_save.setEnabled(False)
        self.btn_save.setStyleSheet(
            "background-color: #30d158; color: white; font-weight: bold; padding: 8px 16px;"
        )
        self.btn_save.clicked.connect(self._save_key)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(self.btn_save)
        root.addLayout(btn_layout)

    def _copy_current(self):
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(self.txt_current.text())
            QMessageBox.information(
                self, "Copiado",
                "Llave maestra copiada al portapapeles.\n"
                "Guárdala en tu gestor de contraseñas de forma segura."
            )

    def _generate_random_key(self):
        new_key = SecurityManager.generate_random_key_hex()
        self.txt_new.setText(new_key)

    def _on_text_changed(self, text: str):
        clean = text.strip()
        if not clean:
            self.lbl_status.setText("")
            self.btn_save.setEnabled(False)
            return

        length = len(clean)
        is_hex = all(c in "0123456789abcdefABCDEF" for c in clean)

        if length == 64 and is_hex:
            self.lbl_status.setText("✓ Llave válida de 256 bits (64 caracteres hex)")
            self.lbl_status.setStyleSheet("color: #30d158; font-size: 11px;")
            self.btn_save.setEnabled(True)
        else:
            self.lbl_status.setText(f"Caracteres: {length}/64 {'(contiene caracteres no válidos)' if not is_hex else ''}")
            self.lbl_status.setStyleSheet("color: #ff9f0a; font-size: 11px;")
            self.btn_save.setEnabled(False)

    def _save_key(self):
        key = self.txt_new.text().strip()
        try:
            SecurityManager.set_app_key_hex(key)
            self.txt_current.setText(SecurityManager.get_app_key_hex())
            self.txt_new.clear()
            QMessageBox.information(
                self, "Llave Actualizada",
                "La Llave Maestra se ha guardado correctamente en este equipo.\n"
                "Ya puedes abrir tus proyectos creados con esta llave."
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar la llave: {e}")
