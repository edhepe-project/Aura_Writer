"""
login/widgets.py
----------------
Constructores de paginas UI para LoginDialog.
"""

from PyQt6.QtWidgets import (
    QWidget, QFormLayout, QLineEdit, QLabel, QPushButton
)
import qtawesome as qta


def add_password_toggle(dialog, line_edit: QLineEdit) -> None:
    """Agrega un icono de ojo interactivo dentro del campo de contrasena."""
    try:
        show_icon = qta.icon("fa5s.eye", color="#8e8e93")
        hide_icon = qta.icon("fa5s.eye-slash", color="#d4a017")
        action = line_edit.addAction(show_icon, QLineEdit.ActionPosition.TrailingPosition)
        action.setToolTip("Mostrar / Ocultar contrasena")

        def _toggle():
            if line_edit.echoMode() == QLineEdit.EchoMode.Password:
                line_edit.setEchoMode(QLineEdit.EchoMode.Normal)
                action.setIcon(hide_icon)
            else:
                line_edit.setEchoMode(QLineEdit.EchoMode.Password)
                action.setIcon(show_icon)

        action.triggered.connect(_toggle)
    except Exception:
        pass


def build_open_page(dialog) -> QWidget:
    """
    Construye la pagina "Abrir Proyecto" y adjunta los widgets
    como atributos del dialogo padre.
    """
    page = QWidget()
    layout = QFormLayout(page)

    dialog.btn_select_file = QPushButton("Seleccionar archivo .aura...")
    dialog.btn_select_file.clicked.connect(dialog._select_file)
    layout.addRow("Proyecto:", dialog.btn_select_file)

    dialog.open_pass_input = QLineEdit()
    dialog.open_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
    dialog.open_pass_input.setPlaceholderText("Contrasena maestra")
    add_password_toggle(dialog, dialog.open_pass_input)
    dialog.open_pass_input.textChanged.connect(dialog._validate)
    layout.addRow("Contrasena:", dialog.open_pass_input)
    dialog.open_pass_input.returnPressed.connect(dialog._on_return_pressed)

    dialog.open_totp_input = QLineEdit()
    dialog.open_totp_input.setPlaceholderText("Codigo de 6 digitos (o codigo de recuperacion)")
    dialog.open_totp_input.setMaxLength(10)
    dialog.open_totp_input.setStyleSheet(
        "font-family: 'Consolas', 'Courier New', monospace; "
        "font-size: 14px; letter-spacing: 3px;"
    )
    dialog.open_totp_input.textChanged.connect(dialog._validate)
    dialog.open_totp_input.returnPressed.connect(dialog._on_return_pressed)
    dialog.open_totp_label = QLabel("Codigo 2FA:")
    dialog.open_totp_label.setStyleSheet("color: #30d158; font-weight: bold;")
    layout.addRow(dialog.open_totp_label, dialog.open_totp_input)

    dialog.totp_note = QLabel(
        "<small style='color:#8e8e93;'>Este proyecto tiene 2FA activado. "
        "Ingresa el codigo de tu app de autenticacion.</small>"
    )
    dialog.totp_note.setWordWrap(True)
    layout.addRow("", dialog.totp_note)

    dialog.open_totp_label.setVisible(False)
    dialog.open_totp_input.setVisible(False)
    dialog.totp_note.setVisible(False)

    return page


def build_new_page(dialog) -> QWidget:
    """
    Construye la pagina "Nuevo Proyecto" y adjunta los widgets
    como atributos del dialogo padre.
    """
    from PyQt6.QtWidgets import QCheckBox

    page = QWidget()
    layout = QFormLayout(page)

    dialog.new_title_input = QLineEdit()
    dialog.new_title_input.setPlaceholderText("Mi Novela")
    layout.addRow("Titulo:", dialog.new_title_input)

    dialog.new_author_input = QLineEdit()
    dialog.new_author_input.setPlaceholderText("Tu nombre")
    layout.addRow("Autor:", dialog.new_author_input)

    dialog.new_pass_input = QLineEdit()
    dialog.new_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
    dialog.new_pass_input.setPlaceholderText("Contrasena maestra (min. 8 caracteres)")
    add_password_toggle(dialog, dialog.new_pass_input)
    layout.addRow("Contrasena:", dialog.new_pass_input)

    dialog.new_pass2_input = QLineEdit()
    dialog.new_pass2_input.setEchoMode(QLineEdit.EchoMode.Password)
    dialog.new_pass2_input.setPlaceholderText("Repite la contrasena")
    add_password_toggle(dialog, dialog.new_pass2_input)
    layout.addRow("Confirmar:", dialog.new_pass2_input)

    dialog.pass_mismatch_label = QLabel("")
    dialog.pass_mismatch_label.setFixedHeight(18)
    dialog.pass_mismatch_label.setStyleSheet("color: #ff453a; font-size: 11px; font-weight: bold;")
    layout.addRow("", dialog.pass_mismatch_label)

    dialog.chk_2fa = QCheckBox("Activar autenticacion 2FA (TOTP)")
    dialog.chk_2fa.setStyleSheet("color: #30d158;")
    dialog.chk_2fa.setToolTip(
        "Protege tu proyecto con un segundo factor de autenticacion.\n"
        "Necesitaras una app como Google Authenticator o Authy."
    )
    layout.addRow("", dialog.chk_2fa)

    for w in (dialog.new_title_input, dialog.new_author_input,
              dialog.new_pass_input, dialog.new_pass2_input):
        w.returnPressed.connect(dialog._on_return_pressed)

    for w in (dialog.new_title_input, dialog.new_author_input,
              dialog.new_pass_input, dialog.new_pass2_input):
        w.textChanged.connect(dialog._validate)

    return page
