from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QHBoxLayout, QMessageBox)
from PyQt6.QtCore import Qt
import qtawesome as qta

class LockDialog(QDialog):
    """
    Diálogo de bloqueo para proteger la privacidad del escritor.
    Se activa con el botón de bloqueo rápido.
    Soporta desbloqueo con contraseña + código TOTP si 2FA está activo.
    """
    def __init__(self, correct_password: str, totp_enabled: bool = False, 
                 totp_secret: str = "", recovery_codes: list = None, parent=None):
        super().__init__(parent)
        self.correct_password = correct_password
        self.totp_enabled = totp_enabled
        self.totp_secret = totp_secret
        self.recovery_codes = recovery_codes or []
        self.setWindowTitle("Sesión Bloqueada")
        self.setFixedSize(300, 260 if totp_enabled else 180)
        # Quitar botones de cerrar ventana para forzar el desbloqueo
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setPixmap(qta.icon("fa5s.lock-open", color="#e67e22").pixmap(48, 48))
        layout.addWidget(icon_lbl)

        msg = QLabel("<b>Privacidad activada</b><br>Ingresa tu contraseña para continuar.")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(msg)

        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setPlaceholderText("Tu contraseña maestra...")
        layout.addWidget(self.pass_input)

        # ── Campo TOTP (solo si 2FA activo) ──────────────────────────
        if self.totp_enabled:
            self.totp_input = QLineEdit()
            self.totp_input.setPlaceholderText("Código 2FA (6 dígitos)")
            self.totp_input.setMaxLength(10)
            self.totp_input.setStyleSheet(
                "font-family: 'Consolas', 'Courier New', monospace; "
                "font-size: 14px; letter-spacing: 3px;"
            )
            self.totp_input.returnPressed.connect(self.check_unlock)
            layout.addWidget(self.totp_input)

            totp_note = QLabel("<small style='color:#30d158;'>🔐 Código de tu app de autenticación</small>")
            totp_note.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(totp_note)

        self.pass_input.returnPressed.connect(
            lambda: self.totp_input.setFocus() if self.totp_enabled else self.check_unlock()
        )

        btn_unlock = QPushButton("Desbloquear")
        btn_unlock.setStyleSheet("background-color: #2c3e50; color: white; font-weight: bold; padding: 6px;")
        btn_unlock.clicked.connect(self.check_unlock)
        layout.addWidget(btn_unlock)

    def check_unlock(self):
        if self.pass_input.text() != self.correct_password:
            QMessageBox.warning(self, "Bloqueo", "Contraseña incorrecta.")
            self.pass_input.clear()
            self.pass_input.setFocus()
            return

        if self.totp_enabled:
            code = self.totp_input.text().strip()
            if not code:
                QMessageBox.warning(self, "2FA", "Ingresa el código de tu app de autenticación.")
                self.totp_input.setFocus()
                return

            from core.totp_manager import TOTPManager

            # Intentar como código TOTP normal
            if TOTPManager.verify_code(self.totp_secret, code):
                self.accept()
                return

            # Intentar como código de recuperación
            success, remaining = TOTPManager.verify_recovery_code(code, self.recovery_codes)
            if success:
                self.recovery_codes = remaining
                QMessageBox.information(
                    self, "Código de recuperación",
                    f"Código de recuperación usado. Quedan {len(remaining)} códigos."
                )
                self.accept()
                return

            QMessageBox.warning(self, "2FA", "Código 2FA incorrecto.")
            self.totp_input.clear()
            self.totp_input.setFocus()
            return

        self.accept()

    def reject(self):
        # Impedir el cierre con ESC
        pass
