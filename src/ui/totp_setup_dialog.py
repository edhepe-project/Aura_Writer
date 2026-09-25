"""
Aura Writer — Diálogo de Configuración 2FA

Permite al usuario activar/desactivar la autenticación
de doble factor mostrando un código QR escaneble.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QMessageBox, QTextEdit)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import qtawesome as qta

from core.totp_manager import TOTPManager
from core.theme_manager import ThemeManager


class TOTPSetupDialog(QDialog):
    """Diálogo para activar 2FA escaneando un código QR."""

    def __init__(self, universe_title: str = "Escritor", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurar Autenticación 2FA")
        self.setFixedSize(480, 620)
        self.universe_title = universe_title

        self.secret = TOTPManager.generate_secret()
        self.recovery_codes = TOTPManager.generate_recovery_codes(8)
        self.confirmed = False

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # ── Encabezado ──────────────────────────────────────────
        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        try:
            icon_lbl.setPixmap(qta.icon("fa5s.shield-alt", color="#30d158").pixmap(48, 48))
        except Exception:
            pass
        layout.addWidget(icon_lbl)

        title = QLabel("<b style='font-size:16px;'>Activar Autenticación 2FA</b>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        instructions = QLabel(
            "Escanea este código QR con tu app de autenticación<br>"
            "(Google Authenticator, Authy, Microsoft Authenticator)."
        )
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #8e8e93; font-size: 12px;")
        layout.addWidget(instructions)

        # ── Código QR ───────────────────────────────────────────
        qr_bytes = TOTPManager.generate_qr_image(self.secret, self.universe_title)
        qr_pixmap = QPixmap()
        qr_pixmap.loadFromData(qr_bytes)
        qr_label = QLabel()
        qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qr_label.setPixmap(qr_pixmap.scaled(
            220, 220,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))
        qr_label.setStyleSheet(
            "background: white; padding: 12px; border-radius: 12px;"
        )
        layout.addWidget(qr_label)

        # ── Secreto manual ──────────────────────────────────────
        is_dark = ThemeManager.is_dark()
        code_bg = "rgba(255, 255, 255, 0.08)" if is_dark else "rgba(0, 0, 0, 0.04)"
        code_border = "#3a3a3c" if is_dark else "#d1d5db"
        txt_col = "#f2f2f7" if is_dark else "#1f2937"
        sub_col = "#8e8e93" if is_dark else "#6b7280"

        secret_lbl = QLabel(
            f"<span style='color: {sub_col}; font-weight: 500;'>Clave manual:</span> "
            f"<code style='background: {code_bg}; border: 1px solid {code_border}; border-radius: 4px; padding: 3px 8px; font-size: 13px; font-family: Monospace, Courier New; color: {txt_col}; font-weight: bold;'>{self.secret}</code>"
        )
        secret_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        secret_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        secret_lbl.setStyleSheet("font-size: 12px; margin: 4px 0;")
        layout.addWidget(secret_lbl)

        # ── Verificación ────────────────────────────────────────
        verify_lbl = QLabel("Ingresa el código de tu app para confirmar:")
        verify_lbl.setStyleSheet("font-size: 12px; margin-top: 8px;")
        layout.addWidget(verify_lbl)

        code_row = QHBoxLayout()
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("000 000")
        self.code_input.setMaxLength(7)
        self.code_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.code_input.setStyleSheet(
            "font-size: 22px; font-family: 'Consolas', 'Courier New', monospace; "
            "letter-spacing: 6px; padding: 8px; text-align: center;"
        )
        self.code_input.returnPressed.connect(self._verify_and_accept)
        code_row.addWidget(self.code_input)
        layout.addLayout(code_row)

        # ── Botones ─────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)

        self.btn_confirm = QPushButton("Confirmar y Activar")
        self.btn_confirm.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_confirm.setIcon(qta.icon("fa5s.check-circle", color="#ffffff"))
        self.btn_confirm.setStyleSheet(
            "background-color: #30d158; color: white; font-weight: bold; "
            "padding: 10px; font-size: 13px; border-radius: 6px;"
        )
        self.btn_confirm.clicked.connect(self._verify_and_accept)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(self.btn_confirm)
        layout.addLayout(btn_row)

    def _verify_and_accept(self):
        code = self.code_input.text().strip().replace(" ", "")
        if TOTPManager.verify_code(self.secret, code):
            self.confirmed = True
            # Mostrar códigos de recuperación
            self._show_recovery_codes()
        else:
            QMessageBox.warning(
                self, "Código Incorrecto",
                "El código no es válido. Verifica que escaneaste el QR\n"
                "correctamente y que la hora de tu dispositivo es correcta."
            )
            self.code_input.clear()
            self.code_input.setFocus()

    def _show_recovery_codes(self):
        """Muestra los códigos de recuperación ANTES de cerrar."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Códigos de Recuperación")
        dlg.setFixedSize(400, 420)
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(20, 20, 20, 20)

        warn = QLabel(
            "<b style='color:#ff9f0a;'>⚠️ GUARDA ESTOS CÓDIGOS EN UN LUGAR SEGURO</b><br><br>"
            "Si pierdes acceso a tu app de autenticación,<br>"
            "estos códigos son tu <b>única</b> forma de recuperar el acceso.<br>"
            "Cada código funciona <b>una sola vez</b>."
        )
        warn.setWordWrap(True)
        warn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(warn)

        codes_text = QTextEdit()
        codes_text.setReadOnly(True)
        codes_text.setStyleSheet(
            "font-family: 'Consolas', 'Courier New', monospace; "
            "font-size: 16px; padding: 12px; background: #2c2c2e; "
            "color: #30d158; border-radius: 8px; line-height: 1.8;"
        )
        codes_formatted = "\n".join(
            f"  {i+1}.  {code}" for i, code in enumerate(self.recovery_codes)
        )
        codes_text.setPlainText(codes_formatted)
        layout.addWidget(codes_text)

        note = QLabel("<small>Estos códigos no se mostrarán de nuevo.</small>")
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        note.setStyleSheet("color: #636366;")
        layout.addWidget(note)

        btn_ok = QPushButton("✅ Los he guardado, continuar")
        btn_ok.setStyleSheet(
            "background-color: #30d158; color: white; font-weight: bold; "
            "padding: 10px; font-size: 13px;"
        )
        btn_ok.clicked.connect(dlg.accept)
        layout.addWidget(btn_ok)

        dlg.exec()
        self.accept()

    def get_result(self) -> dict:
        """Retorna el resultado de la configuración."""
        if self.confirmed:
            return {
                "secret": self.secret,
                "recovery_codes": self.recovery_codes,
                "enabled": True,
            }
        return {"enabled": False}
