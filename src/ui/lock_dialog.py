from __future__ import annotations

from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QWidget, QFrame,
)
import qtawesome as qta
from core.theme_manager import ThemeManager


class LockDialog(QDialog):
    """
    Pantalla de bloqueo de sesión de Aura Writer.
    Diseño premium tipo 'lock screen' sincronizado con el tema activo.
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
        accent_color = ThemeManager.color("accent")
        icon_lbl.setPixmap(
            qta.icon("fa5s.lock", color=accent_color).pixmap(QSize(36, 36))
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
        btn.setIcon(qta.icon("fa5s.unlock-alt", color=ThemeManager.color("fg_selected")))
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
        c = ThemeManager.palette()
        bg_dialog = c["bg_surface"]
        bg_top = c["bg_app"]
        fg_title = c["fg_primary"]
        fg_subtitle = c["fg_muted"]
        border_sep = c["border_default"]
        
        lbl_field = c["fg_muted"]
        bg_input = c["bg_input"]
        border_input = c["border_default"]
        fg_input = c["fg_primary"]
        focus_border = c["accent"]
        focus_bg = c["bg_hover"]
        ph_color = c["fg_placeholder"]
        note_color = c["green"]
        
        btn_bg = c["accent"]
        btn_fg = c["fg_selected"]
        btn_hover = c["accent_hover"]
        btn_pressed = c["accent_hover"]
        err_color = c["red"]

        self.setStyleSheet(f"""
            QDialog {{
                background: {bg_dialog};
            }}

            /* ── Panel superior ── */
            #ld_top {{
                background: {bg_top};
            }}
            #ld_title {{
                font-size: 20px;
                font-weight: 700;
                color: {fg_title};
                font-family: 'Segoe UI', sans-serif;
            }}
            #ld_subtitle {{
                font-size: 13px;
                color: {fg_subtitle};
                font-family: 'Segoe UI', sans-serif;
            }}

            /* ── Separador ── */
            #ld_sep {{
                background: {border_sep};
                min-height: 1px;
                max-height: 1px;
                border: none;
            }}

            /* ── Formulario ── */
            #ld_form {{
                background: {bg_dialog};
            }}
            #ld_field_label {{
                font-size: 11px;
                font-weight: 600;
                color: {lbl_field};
                letter-spacing: 0.06em;
                font-family: 'Segoe UI', sans-serif;
            }}

            /* Inputs */
            #ld_input, #ld_input_mono {{
                background: {bg_input};
                border: 1.5px solid {border_input};
                border-radius: 10px;
                color: {fg_input};
                font-size: 15px;
                padding: 0 14px;
                font-family: 'Segoe UI', sans-serif;
            }}
            #ld_input:focus, #ld_input_mono:focus {{
                border-color: {focus_border};
                background: {focus_bg};
            }}
            #ld_input_mono {{
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 18px;
                letter-spacing: 6px;
            }}
            QLineEdit::placeholder {{
                color: {ph_color};
            }}

            /* Nota 2FA */
            #ld_note {{
                font-size: 11px;
                color: {note_color};
                font-family: 'Segoe UI', sans-serif;
            }}

            /* Botón */
            #ld_btn {{
                background: {btn_bg};
                color: {btn_fg};
                border: none;
                border-radius: 12px;
                font-size: 15px;
                font-weight: 700;
                font-family: 'Segoe UI', sans-serif;
            }}
            #ld_btn:hover   {{ background: {btn_hover}; }}
            #ld_btn:pressed {{ background: {btn_pressed}; }}

            /* Error — base siempre transparente */
            #ld_error {{
                font-size: 12px;
                color: transparent;
                font-family: 'Segoe UI', sans-serif;
                padding: 6px 12px;
                background: transparent;
                border-radius: 8px;
            }}
            /* Error activo — muestra el texto y el fondo */
            #ld_error[active="true"] {{
                color: {err_color};
                background: rgba(255, 69, 58, 0.12);
            }}
        """)
