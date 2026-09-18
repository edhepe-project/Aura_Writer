"""
login/dialog.py
---------------
LoginDialog: dialogo de inicio de Aura Writer.
Ensambla widgets (widgets.py), logica (logic.py) y acciones (actions.py)
en un QDialog limpio y cohesivo.
"""

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget
)
import qtawesome as qta

from .widgets import build_open_page, build_new_page
from . import logic, actions

log = logging.getLogger(__name__)


class LoginDialog(QDialog):
    """
    Dialogo de inicio de Aura Writer.
    Permite abrir un proyecto existente (.aura) o crear uno nuevo.
    Soporta autenticacion 2FA (TOTP) para proyectos protegidos.
    """
    MODE_OPEN = "open"
    MODE_NEW  = "new"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aura Writer")
        self.setFixedSize(460, 370)
        self.project_path = None
        self.password = None
        self.mode = self.MODE_OPEN
        self.totp_code = None
        self.enable_2fa = False
        self.setup_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def setup_ui(self):
        root = QVBoxLayout(self)

        # Encabezado
        header = QHBoxLayout()
        icon_lbl = QLabel()
        try:
            icon_lbl.setPixmap(qta.icon("fa5s.feather-alt", color="#d4a017").pixmap(48, 48))
        except Exception:
            pass
        title_lbl = QLabel("<b>Aura Writer</b><br><small>Tu obra. Tu privacidad.</small>")
        title_lbl.setStyleSheet("font-size: 14px;")
        header.addWidget(icon_lbl)
        header.addWidget(title_lbl)
        header.addStretch()

        btn_updates = QPushButton("Actualizaciones")
        btn_updates.setToolTip("Comprobar si existe una version mas reciente de Aura Writer")
        btn_updates.setStyleSheet("padding: 4px 8px; font-size: 11px;")
        btn_updates.clicked.connect(self._check_updates)
        header.addWidget(btn_updates)

        btn_app_key = QPushButton("Llave...")
        btn_app_key.setToolTip("Consultar o configurar la Llave Maestra de Aplicacion")
        btn_app_key.setStyleSheet("padding: 4px 8px; font-size: 11px;")
        btn_app_key.clicked.connect(self._open_app_key_dialog)
        header.addWidget(btn_app_key)

        root.addLayout(header)

        # Selector de modo
        mode_layout = QHBoxLayout()
        self.btn_mode_open = QPushButton("Abrir Proyecto")
        self.btn_mode_new  = QPushButton("Nuevo Proyecto")
        for btn in (self.btn_mode_open, self.btn_mode_new):
            btn.setCheckable(True)
            btn.setStyleSheet("padding: 6px 14px;")
            mode_layout.addWidget(btn)
        self.btn_mode_open.setChecked(True)
        root.addLayout(mode_layout)

        # Paginas apiladas
        self.stack = QStackedWidget()
        root.addWidget(self.stack)
        self.stack.addWidget(build_open_page(self))   # index 0
        self.stack.addWidget(build_new_page(self))    # index 1

        # Boton principal
        self.btn_action = QPushButton("Desbloquear")
        self.btn_action.setEnabled(False)
        self.btn_action.setStyleSheet(
            "background-color: #d4a017; color: white; font-weight: bold; "
            "padding: 10px; font-size: 13px;"
        )
        self.btn_action.clicked.connect(self.accept)
        self.btn_action.setDefault(True)
        root.addWidget(self.btn_action)

        # Conexiones de modo
        self.btn_mode_open.clicked.connect(lambda: self._switch_mode(self.MODE_OPEN))
        self.btn_mode_new.clicked.connect(lambda:  self._switch_mode(self.MODE_NEW))

    # ------------------------------------------------------------------
    # 2FA: mostrar/ocultar campo TOTP
    # ------------------------------------------------------------------

    def show_totp_field(self):
        """Muestra el campo TOTP en la pagina de apertura."""
        self.open_totp_label.setVisible(True)
        self.open_totp_input.setVisible(True)
        self.totp_note.setVisible(True)
        self.open_totp_input.setFocus()
        self.setFixedSize(440, 380)

    # ------------------------------------------------------------------
    # Delegacion a modulos especializados
    # ------------------------------------------------------------------

    def _switch_mode(self, mode: str):
        logic.switch_mode(self, mode)

    def _select_file(self):
        logic.select_file(self)

    def _validate(self):
        logic.validate(self)

    def _on_return_pressed(self):
        logic.on_return_pressed(self)

    def accept(self):
        """Valida y acepta el dialogo."""
        if logic.do_accept(self):
            super().accept()

    def _check_updates(self):
        actions.check_updates(self)

    def _open_app_key_dialog(self):
        actions.open_app_key_dialog(self)

    # ------------------------------------------------------------------
    # Accesores publicos
    # ------------------------------------------------------------------

    def get_credentials(self):
        """Retorna (project_path, password, mode, extra_meta)."""
        extra = {}
        if self.mode == self.MODE_NEW:
            extra["title"]  = self.new_title_input.text()
            extra["author"] = self.new_author_input.text()
            extra["enable_2fa"] = self.enable_2fa
        return self.project_path, self.password, self.mode, extra

    def get_totp_code(self) -> str | None:
        """Retorna el codigo TOTP ingresado (si aplica)."""
        return self.totp_code

    def showEvent(self, a0):
        event = a0
        super().showEvent(event)
        if self.mode == self.MODE_OPEN and self.project_path:
            self.open_pass_input.setFocus()
