from __future__ import annotations

from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QWidget, QFrame,
)
import qtawesome as qta


class LockDialog(QDialog):
    """
    Pantalla de bloqueo de sesión de Aura Writer.
    Diseño premium tipo 'lock screen' – tamaño generoso y estilo oscuro.
    Soporta contraseña maestra + código TOTP / código de recuperación.
    """

    def __init__(
        self,
        correct_password: str,
        totp_enabled: bool = False,
        totp_secret: str = "",
        recovery_codes: "list | None" = None,
        parent=None,
    ):
        super().__init__(parent)
        self.correct_password = correct_password
        self.totp_enabled = totp_enabled
        self.totp_secret = totp_secret
        self.recovery_codes = recovery_codes or []

        self.setWindowTitle("Sesión Bloqueada — Aura Writer")
        # Sin botón de cerrar para forzar desbloqueo
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
        )
        self.setMinimumSize(500, 380 if totp_enabled else 320)
        self.resize(500, 400 if totp_enabled else 340)

        self._build_ui()
        self._apply_style()

    # ── Construcción de la UI ─────────────────────────────────────────────────
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Panel superior con icono y título ─────────────────────────────
        top = QWidget()
        top.setObjectName("ld_top")
        top_l = QVBoxLayout(top)
        top_l.setContentsMargins(48, 40, 48, 28)
        top_l.setSpacing(10)
        top_l.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setPixmap(
            qta.icon("fa5s.lock", color="#ffd60a").pixmap(QSize(36, 36))
        )
        top_l.addWidget(icon_lbl)

        title = QLabel("Sesión bloqueada")
        title.setObjectName("ld_title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_l.addWidget(title)

        subtitle = QLabel("Ingresa tu contraseña maestra para continuar.")
        subtitle.setObjectName("ld_subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_l.addWidget(subtitle)

        root.addWidget(top)

        # ── Separador ─────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("ld_sep")
        root.addWidget(sep)

        # ── Panel de formulario ───────────────────────────────────────────
        form = QWidget()
        form.setObjectName("ld_form")
        form_l = QVBoxLayout(form)
        form_l.setContentsMargins(40, 28, 40, 32)
        form_l.setSpacing(14)

        # Label contraseña
        pass_label = QLabel("Contraseña maestra")
        pass_label.setObjectName("ld_field_label")
        form_l.addWidget(pass_label)

        # Campo contraseña
        self.pass_input = QLineEdit()
        self.pass_input.setObjectName("ld_input")
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setPlaceholderText("••••••••••••")
        self.pass_input.setMinimumHeight(44)
        form_l.addWidget(self.pass_input)

        # ── Campo TOTP (solo si 2FA activo) ───────────────────────────────
        if self.totp_enabled:
            totp_label = QLabel("Código de autenticación (2FA)")
            totp_label.setObjectName("ld_field_label")
            form_l.addWidget(totp_label)

            self.totp_input = QLineEdit()
            self.totp_input.setObjectName("ld_input_mono")
            self.totp_input.setPlaceholderText("000 000")
            self.totp_input.setMaxLength(10)
            self.totp_input.setMinimumHeight(44)
            self.totp_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.totp_input.returnPressed.connect(self.check_unlock)
            form_l.addWidget(self.totp_input)

            totp_note = QLabel("🔐  Usa tu app de autenticación o un código de recuperación.")
            totp_note.setObjectName("ld_note")
            totp_note.setWordWrap(True)
            form_l.addWidget(totp_note)

        self.pass_input.returnPressed.connect(
            lambda: self.totp_input.setFocus() if self.totp_enabled else self.check_unlock()
        )

        form_l.addSpacing(4)

        # ── Mensaje de error (encima del botón para que no se corte) ─────────
        self._err_label = QLabel()
        self._err_label.setObjectName("ld_error")
        self._err_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._err_label.setWordWrap(True)
        self._err_label.setMinimumHeight(36)   # reserva espacio aunque esté oculto
        self._err_label.setText(" ")           # placeholder invisible para fijar altura
        form_l.addWidget(self._err_label)

        # ── Botón desbloquear ─────────────────────────────────────────────────
        btn = QPushButton("  Desbloquear")
        btn.setObjectName("ld_btn")
        btn.setMinimumHeight(46)
        btn.setIcon(qta.icon("fa5s.unlock-alt", color="#1c1c1e"))
        btn.setIconSize(QSize(18, 18))
        btn.clicked.connect(self.check_unlock)
        form_l.addWidget(btn)

        root.addWidget(form)

    # ── Lógica de desbloqueo ──────────────────────────────────────────────────
    def check_unlock(self) -> None:
        self._clear_error()

        if self.pass_input.text() != self.correct_password:
            self._show_error("Contraseña incorrecta. Inténtalo de nuevo.")
            self.pass_input.clear()
            self.pass_input.setFocus()
            return

        if self.totp_enabled:
            code = self.totp_input.text().strip().replace(" ", "")
            if not code:
                self._show_error("Ingresa el código de tu app de autenticación.")
                self.totp_input.setFocus()
                return

            from core.totp_manager import TOTPManager

            if TOTPManager.verify_code(self.totp_secret, code):
                self.accept()
                return

            success, remaining = TOTPManager.verify_recovery_code(code, self.recovery_codes)
            if success:
                self.recovery_codes = remaining
                QMessageBox.information(
                    self,
                    "Código de recuperación",
                    f"Código de recuperación usado.\nQuedan {len(remaining)} códigos.",
                )
                self.accept()
                return

            self._show_error("Código 2FA incorrecto.")
            self.totp_input.clear()
            self.totp_input.setFocus()
            return

        self.accept()

    def _show_error(self, msg: str) -> None:
        self._err_label.setText(f"⚠  {msg}")
        self._err_label.setProperty("active", True)
        self._err_label.style().unpolish(self._err_label)
        self._err_label.style().polish(self._err_label)
        # Limpiar el error después de 4 s
        QTimer.singleShot(4000, self._clear_error)

    def _clear_error(self) -> None:
        self._err_label.setText(" ")
        self._err_label.setProperty("active", False)
        self._err_label.style().unpolish(self._err_label)
        self._err_label.style().polish(self._err_label)

    def reject(self) -> None:
        # Impedir cierre con ESC — el usuario debe desbloquear
        pass

    # ── Estilos ────────────────────────────────────────────────────────────────
    def _apply_style(self) -> None:
        self.setStyleSheet("""
            QDialog {
                background: #1c1c1e;
            }

            /* ── Panel superior ── */
            #ld_top {
                background: #2c2c2e;
            }
            #ld_title {
                font-size: 20px;
                font-weight: 700;
                color: #f2f2f7;
                font-family: 'Segoe UI', sans-serif;
            }
            #ld_subtitle {
                font-size: 13px;
                color: #8e8e93;
                font-family: 'Segoe UI', sans-serif;
            }

            /* ── Separador ── */
            #ld_sep {
                background: #3a3a3c;
                min-height: 1px;
                max-height: 1px;
                border: none;
            }

            /* ── Formulario ── */
            #ld_form {
                background: #1c1c1e;
            }
            #ld_field_label {
                font-size: 11px;
                font-weight: 600;
                color: #636366;
                letter-spacing: 0.06em;
                font-family: 'Segoe UI', sans-serif;
            }

            /* Inputs */
            #ld_input, #ld_input_mono {
                background: #2c2c2e;
                border: 1.5px solid #3a3a3c;
                border-radius: 10px;
                color: #f2f2f7;
                font-size: 15px;
                padding: 0 14px;
                font-family: 'Segoe UI', sans-serif;
            }
            #ld_input:focus, #ld_input_mono:focus {
                border-color: #ffd60a;
                background: #3a3a3c;
            }
            #ld_input_mono {
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 18px;
                letter-spacing: 6px;
            }
            QLineEdit::placeholder {
                color: #636366;
            }

            /* Nota 2FA */
            #ld_note {
                font-size: 11px;
                color: #30d158;
                font-family: 'Segoe UI', sans-serif;
            }

            /* Botón */
            #ld_btn {
                background: #ffd60a;
                color: #1c1c1e;
                border: none;
                border-radius: 12px;
                font-size: 15px;
                font-weight: 700;
                font-family: 'Segoe UI', sans-serif;
            }
            #ld_btn:hover   { background: #ffe84d; }
            #ld_btn:pressed { background: #c9a800; }

            /* Error — base siempre transparente */
            #ld_error {
                font-size: 12px;
                color: transparent;
                font-family: 'Segoe UI', sans-serif;
                padding: 6px 12px;
                background: transparent;
                border-radius: 8px;
            }
            /* Error activo — muestra el texto y el fondo */
            #ld_error[active="true"] {
                color: #ff453a;
                background: rgba(255, 69, 58, 0.12);
            }
        """)
