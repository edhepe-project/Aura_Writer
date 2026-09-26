"""
login/logic.py
--------------
Logica de interaccion de LoginDialog:
  - _switch_mode   : alterna entre Abrir / Nuevo
  - _select_file   : selector de archivo .aura
  - _validate      : habilita/deshabilita boton de accion
  - _on_return     : acepta dialogo con Enter
  - do_accept      : logica de accept() (guardado de ruta/pass)
"""

import os
import re
from PyQt6.QtWidgets import QFileDialog

# ── Validacion centralizada de contrasena ────────────────────────────────────
MIN_PASSWORD_LEN = 8
_SPECIAL_CHARS = r"""!@#$%^&*()-_=+[]{}|;:',.<>?/~`\\"""


def password_error(password: str) -> str:
    """
    Valida la contrasena y devuelve un mensaje de error si no cumple los requisitos,
    o una cadena vacia si es valida.
    Requisitos actuales:
      - Al menos 8 caracteres
      - Al menos 1 letra mayuscula
      - Al menos 1 caracter especial
    """
    if len(password) < MIN_PASSWORD_LEN:
        return f"La contraseña debe tener al menos {MIN_PASSWORD_LEN} caracteres."
    if not re.search(r"[A-Z]", password):
        return "La contraseña debe incluir al menos una letra mayúscula (A-Z)."
    if not re.search(r"[" + re.escape(_SPECIAL_CHARS) + r"]", password):
        return "La contraseña debe incluir al menos un carácter especial (!@#$%^&*...)"
    return ""


def switch_mode(dialog, mode: str) -> None:
    """Alterna entre modo Abrir y Nuevo Proyecto."""
    dialog.mode = mode
    dialog.btn_mode_open.setChecked(mode == dialog.MODE_OPEN)
    dialog.btn_mode_new.setChecked(mode == dialog.MODE_NEW)
    dialog.stack.setCurrentIndex(0 if mode == dialog.MODE_OPEN else 1)
    dialog.btn_action.setText("Desbloquear" if mode == dialog.MODE_OPEN else "Crear Proyecto")
    dialog._validate()


def select_file(dialog) -> None:
    """Abre el selector de archivos .aura."""
    path, _ = QFileDialog.getOpenFileName(
        dialog, "Abrir Proyecto Aura", "", "Aura Files (*.aura)"
    )
    if path:
        dialog.project_path = path
        dialog.btn_select_file.setText(os.path.basename(path))
        dialog._validate()


def validate(dialog) -> None:
    """Habilita el boton de accion solo cuando todos los campos requeridos estan completos."""
    if dialog.mode == dialog.MODE_OPEN:
        ok = bool(dialog.project_path) and bool(dialog.open_pass_input.text())
        if ok and dialog.open_totp_input.isVisible():
            ok = len(dialog.open_totp_input.text().strip()) >= 6
    else:
        p1 = dialog.new_pass_input.text()
        p2 = dialog.new_pass2_input.text()

        err = password_error(p1) if p1 else ""
        if err:
            dialog.pass_mismatch_label.setText(err)
            dialog.new_pass2_input.setStyleSheet("")
        elif p2 and p1 != p2:
            dialog.pass_mismatch_label.setText("Las contraseñas no coinciden.")
            dialog.new_pass2_input.setStyleSheet("border: 1px solid #ff453a;")
        else:
            dialog.pass_mismatch_label.setText("")
            dialog.new_pass2_input.setStyleSheet("")

        ok = (
            bool(dialog.new_title_input.text().strip())
            and bool(dialog.new_author_input.text().strip())
            and not password_error(p1)
            and p1 == p2
        )

    dialog.btn_action.setEnabled(ok)


def on_return_pressed(dialog) -> None:
    """Si el formulario es valido, acepta el dialogo al presionar Enter."""
    dialog._validate()
    if dialog.btn_action.isEnabled():
        dialog.accept()


def do_accept(dialog) -> bool:
    """
    Ejecuta la logica de aceptacion del dialogo.
    Retorna True si se debe llamar a super().accept(), False si el usuario cancelo.
    """
    if dialog.mode == dialog.MODE_NEW:
        path, _ = QFileDialog.getSaveFileName(
            dialog,
            "Guardar nuevo proyecto",
            f"{dialog.new_title_input.text().replace(' ', '_')}.aura",
            "Aura Files (*.aura)",
        )
        if not path:
            return False
        if not path.endswith(".aura"):
            path += ".aura"
        dialog.project_path = path
        dialog.password = dialog.new_pass_input.text()
        dialog.enable_2fa = dialog.chk_2fa.isChecked()
    else:
        dialog.password = dialog.open_pass_input.text()
        dialog.totp_code = (
            dialog.open_totp_input.text().strip()
            if dialog.open_totp_input.isVisible()
            else None
        )
    return True
