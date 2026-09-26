"""
Aura Writer — Protection Verifier Dialog
Diálogo de verificación de autoría en metadatos de archivos (Aura Protect).
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QGroupBox, QFileDialog
)
from PyQt6.QtCore import Qt
from tools.protection.aura_protect import extract_watermark_from_file


class ProtectionVerifierDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🛡️ Verificador de Autoría — Aura Protect")
        self.resize(520, 320)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        info_lbl = QLabel(
            "<b>🛡️ Verificación de Autoría por Metadatos</b><br>"
            "Carga un archivo exportado (PDF, DOCX o EPUB) para verificar su firma de autoría criptográfica inalterable."
        )
        info_lbl.setWordWrap(True)
        info_lbl.setStyleSheet("font-size: 13px; color: #d0d0d0; line-height: 1.4;")
        layout.addWidget(info_lbl)

        # Botón de cargar archivo
        btn_file = QPushButton("📁 Cargar y Analizar Archivo (PDF / DOCX / EPUB)…")
        btn_file.setStyleSheet(
            "background-color: #8e44ad; color: white; font-weight: bold; padding: 10px 18px; border-radius: 5px; font-size: 14px;"
        )
        btn_file.clicked.connect(self.verify_file)
        layout.addWidget(btn_file)

        # Resultado
        self.res_box = QGroupBox("Resultado del Análisis de Autoría")
        res_layout = QVBoxLayout(self.res_box)
        self.lbl_status = QLabel("Selecciona un archivo para verificar...")
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setStyleSheet("font-size: 13px; font-weight: bold; color: #7f8c8d;")
        res_layout.addWidget(self.lbl_status)
        layout.addWidget(self.res_box)

        # Botón cerrar
        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.accept)
        btns = QHBoxLayout()
        btns.addStretch()
        btns.addWidget(btn_close)
        layout.addLayout(btns)

    def _show_result(self, payload: str | None, file_name: str):
        if payload:
            parts = payload.split("|")
            if len(parts) >= 4 and parts[0] == "AURA-PROTECT":
                author = parts[1]
                title = parts[2]
                short_hash = parts[3]
                date = parts[4] if len(parts) > 4 else "N/A"
                self.lbl_status.setText(
                    f"✅ **¡FIRMA DE AUTORÍA CONFIRMADA!**\n\n"
                    f"• **Archivo:** {file_name}\n"
                    f"• **Autor Registrado:** {author}\n"
                    f"• **Título de la Obra:** {title}\n"
                    f"• **Hash SHA-256:** {short_hash}\n"
                    f"• **Fecha de Generación:** {date}\n\n"
                    f"*Este archivo fue generado oficialmente por Aura Writer con protección inalterable.*"
                )
                self.lbl_status.setStyleSheet("font-size: 13px; color: #27ae60; font-weight: bold;")
            else:
                self.lbl_status.setText(f"✅ **Firma Detectada:**\n{payload}")
                self.lbl_status.setStyleSheet("font-size: 13px; color: #2980b9; font-weight: bold;")
        else:
            self.lbl_status.setText(
                f"❌ **No se encontró firma de autoría en el archivo.**\n"
                "El documento no posee metadatos de Aura Protect o fue exportado sin la opción activa."
            )
            self.lbl_status.setStyleSheet("font-size: 13px; color: #c0392b;")

    def verify_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo a verificar", "", "Documentos (*.pdf *.docx *.epub);;Todos los archivos (*.*)"
        )
        if not path:
            return

        payload = extract_watermark_from_file(path)
        import os
        self._show_result(payload, file_name=os.path.basename(path))
