import os
import sys
import logging
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QFileDialog, QStackedWidget,
                             QWidget, QFormLayout, QMessageBox, QCheckBox)
from PyQt6.QtCore import Qt
import qtawesome as qta

log = logging.getLogger(__name__)


class LoginDialog(QDialog):
    """
    Diálogo de inicio de Aura Writer.
    Permite abrir un proyecto existente (.aura) o crear uno nuevo.
    Soporta autenticación 2FA (TOTP) para proyectos protegidos.
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

        # ── Encabezado ──────────────────────────────────────────────
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

        btn_updates = QPushButton("🔄 Actualizaciones")
        btn_updates.setToolTip("Comprobar si existe una versión más reciente de Aura Writer")
        btn_updates.setStyleSheet("padding: 4px 8px; font-size: 11px;")
        btn_updates.clicked.connect(self._check_updates)
        header.addWidget(btn_updates)

        btn_app_key = QPushButton("🔑 Llave...")
        btn_app_key.setToolTip("Consultar o configurar la Llave Maestra de Aplicación (para nuevo equipo)")
        btn_app_key.setStyleSheet("padding: 4px 8px; font-size: 11px;")
        btn_app_key.clicked.connect(self._open_app_key_dialog)
        header.addWidget(btn_app_key)

        root.addLayout(header)

        # ── Selector de modo ─────────────────────────────────────────
        mode_layout = QHBoxLayout()
        self.btn_mode_open = QPushButton("Abrir Proyecto")
        self.btn_mode_new  = QPushButton("Nuevo Proyecto")
        for btn in (self.btn_mode_open, self.btn_mode_new):
            btn.setCheckable(True)
            btn.setStyleSheet("padding: 6px 14px;")
            mode_layout.addWidget(btn)
        self.btn_mode_open.setChecked(True)
        root.addLayout(mode_layout)

        # ── Páginas apiladas: Abrir / Nuevo ──────────────────────────
        self.stack = QStackedWidget()
        root.addWidget(self.stack)

        self.stack.addWidget(self._make_open_page())   # index 0
        self.stack.addWidget(self._make_new_page())    # index 1

        # ── Botón principal ──────────────────────────────────────────
        self.btn_action = QPushButton("Desbloquear")
        self.btn_action.setEnabled(False)
        self.btn_action.setStyleSheet(
            "background-color: #d4a017; color: white; font-weight: bold; padding: 10px; font-size: 13px;"
        )
        self.btn_action.clicked.connect(self.accept)
        self.btn_action.setDefault(True)
        root.addWidget(self.btn_action)

        # ── Conexiones de modo ───────────────────────────────────────
        self.btn_mode_open.clicked.connect(lambda: self._switch_mode(self.MODE_OPEN))
        self.btn_mode_new.clicked.connect(lambda:  self._switch_mode(self.MODE_NEW))

    def _make_open_page(self) -> QWidget:
        page   = QWidget()
        layout = QFormLayout(page)

        self.btn_select_file = QPushButton("Seleccionar archivo .aura...")
        self.btn_select_file.clicked.connect(self._select_file)
        layout.addRow("Proyecto:", self.btn_select_file)

        self.open_pass_input = QLineEdit()
        self.open_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.open_pass_input.setPlaceholderText("Contraseña maestra")
        self.open_pass_input.textChanged.connect(self._validate)
        layout.addRow("Contraseña:", self.open_pass_input)
        self.open_pass_input.returnPressed.connect(self._on_return_pressed)

        # ── Campo TOTP (visible cuando se detecta 2FA) ──────────────
        self.open_totp_input = QLineEdit()
        self.open_totp_input.setPlaceholderText("Código de 6 dígitos (o código de recuperación)")
        self.open_totp_input.setMaxLength(10)
        self.open_totp_input.setStyleSheet(
            "font-family: 'Consolas', 'Courier New', monospace; "
            "font-size: 14px; letter-spacing: 3px;"
        )
        self.open_totp_input.textChanged.connect(self._validate)
        self.open_totp_input.returnPressed.connect(self._on_return_pressed)
        self.open_totp_label = QLabel("Código 2FA:")
        self.open_totp_label.setStyleSheet("color: #30d158; font-weight: bold;")
        layout.addRow(self.open_totp_label, self.open_totp_input)

        # Nota informativa
        self.totp_note = QLabel(
            "<small style='color:#8e8e93;'>🔐 Este proyecto tiene 2FA activado. "
            "Ingresa el código de tu app de autenticación.</small>"
        )
        self.totp_note.setWordWrap(True)
        layout.addRow("", self.totp_note)

        # Inicialmente oculto (se muestra post-descifrado si hay 2FA)
        self.open_totp_label.setVisible(False)
        self.open_totp_input.setVisible(False)
        self.totp_note.setVisible(False)

        return page

    def _make_new_page(self) -> QWidget:
        page   = QWidget()
        layout = QFormLayout(page)

        self.new_title_input  = QLineEdit()
        self.new_title_input.setPlaceholderText("Mi Gran Novela")
        layout.addRow("Título:", self.new_title_input)

        self.new_author_input = QLineEdit()
        self.new_author_input.setPlaceholderText("Tu nombre")
        layout.addRow("Autor:", self.new_author_input)

        self.new_pass_input   = QLineEdit()
        self.new_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_pass_input.setPlaceholderText("Contraseña maestra (mín. 8 caracteres)")
        layout.addRow("Contraseña:", self.new_pass_input)

        self.new_pass2_input  = QLineEdit()
        self.new_pass2_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_pass2_input.setPlaceholderText("Repite la contraseña")
        layout.addRow("Confirmar:", self.new_pass2_input)

        # ── Etiqueta de advertencia en rojo para contraseñas no coincidentes ──
        # Se mantiene visible con altura fija para evitar saltos o recortes en los inputs
        self.pass_mismatch_label = QLabel("")
        self.pass_mismatch_label.setFixedHeight(18)
        self.pass_mismatch_label.setStyleSheet("color: #ff453a; font-size: 11px; font-weight: bold;")
        layout.addRow("", self.pass_mismatch_label)

        # ── Checkbox 2FA ─────────────────────────────────────────────
        self.chk_2fa = QCheckBox("🔐 Activar autenticación 2FA (TOTP)")
        self.chk_2fa.setStyleSheet("color: #30d158;")
        self.chk_2fa.setToolTip(
            "Protege tu proyecto con un segundo factor de autenticación.\n"
            "Necesitarás una app como Google Authenticator o Authy."
        )
        layout.addRow("", self.chk_2fa)

        for w in (self.new_title_input, self.new_author_input, self.new_pass_input, self.new_pass2_input):
            w.returnPressed.connect(self._on_return_pressed)

        for w in (self.new_title_input, self.new_author_input,
                  self.new_pass_input, self.new_pass2_input):
            w.textChanged.connect(self._validate)

        return page

    # ------------------------------------------------------------------
    # 2FA: mostrar/ocultar campo TOTP
    # ------------------------------------------------------------------

    def show_totp_field(self):
        """Muestra el campo TOTP en la página de apertura."""
        self.open_totp_label.setVisible(True)
        self.open_totp_input.setVisible(True)
        self.totp_note.setVisible(True)
        self.open_totp_input.setFocus()
        # Ajustar tamaño del diálogo
        self.setFixedSize(440, 380)

    # ------------------------------------------------------------------
    # Lógica de interacción
    # ------------------------------------------------------------------

    def _switch_mode(self, mode: str):
        self.mode = mode
        self.btn_mode_open.setChecked(mode == self.MODE_OPEN)
        self.btn_mode_new.setChecked(mode  == self.MODE_NEW)
        self.stack.setCurrentIndex(0 if mode == self.MODE_OPEN else 1)
        self.btn_action.setText("Desbloquear" if mode == self.MODE_OPEN else "Crear Proyecto")
        self._validate()

    def _select_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir Proyecto Aura", "", "Aura Files (*.aura)"
        )
        if path:
            self.project_path = path
            self.btn_select_file.setText(os.path.basename(path))
            self._validate()

    def _validate(self):
        """Habilita el botón de acción solo cuando todos los campos requeridos están completos."""
        if self.mode == self.MODE_OPEN:
            ok = bool(self.project_path) and bool(self.open_pass_input.text())
            # Si el campo TOTP es visible, requiere al menos algo
            if ok and self.open_totp_input.isVisible():
                totp_text = self.open_totp_input.text().strip()
                ok = len(totp_text) >= 6
        else:
            p1 = self.new_pass_input.text()
            p2 = self.new_pass2_input.text()

            # Feedback visual de contraseña (mantiene espacio reservado)
            if p1 and len(p1) < 8:
                self.pass_mismatch_label.setText("La contrasena debe tener al menos 8 caracteres.")
                self.new_pass2_input.setStyleSheet("")
            elif p2 and p1 != p2:
                self.pass_mismatch_label.setText("Las contrasenas no coinciden.")
                self.new_pass2_input.setStyleSheet("border: 1px solid #ff453a;")
            else:
                self.pass_mismatch_label.setText("")
                self.new_pass2_input.setStyleSheet("")

            ok = (
                bool(self.new_title_input.text().strip())
                and bool(self.new_author_input.text().strip())
                and len(p1) >= 8
                and p1 == p2
            )
        self.btn_action.setEnabled(ok)

    def _on_return_pressed(self):
        """Si el formulario es válido, acepta el diálogo al presionar Enter."""
        self._validate()
        if self.btn_action.isEnabled():
            self.accept()

    def accept(self):
        """Valida y acepta el diálogo. Para nuevo proyecto pide la ruta de guardado."""
        if self.mode == self.MODE_NEW:
            # Seleccionar dónde guardar el nuevo proyecto
            path, _ = QFileDialog.getSaveFileName(
                self, "Guardar nuevo proyecto", 
                f"{self.new_title_input.text().replace(' ', '_')}.aura",
                "Aura Files (*.aura)"
            )
            if not path:
                return  # El usuario canceló
            if not path.endswith(".aura"):
                path += ".aura"
            self.project_path = path
            self.password     = self.new_pass_input.text()
            self.enable_2fa   = self.chk_2fa.isChecked()
        else:
            self.password  = self.open_pass_input.text()
            self.totp_code = self.open_totp_input.text().strip() if self.open_totp_input.isVisible() else None

        super().accept()

    # ------------------------------------------------------------------
    # Accesores públicos
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
        """Retorna el código TOTP ingresado (si aplica)."""
        return self.totp_code

    def _open_app_key_dialog(self):
        """Abre el diálogo de gestión de Llave Maestra de Aplicación."""
        from ui.app_key_dialog import AppKeyDialog
        dlg = AppKeyDialog(self)
        dlg.exec()

    def _check_updates(self):
        """Comprueba actualizaciones directamente desde la pantalla de bienvenida."""
        from core.updater import UpdateCheckWorker
        from ui.update_dialog import UpdateDialog

        worker = UpdateCheckWorker(self)

        def _on_finish(has_update: bool, release_info: dict, err: str):
            if has_update:
                dlg = UpdateDialog(release_info, self)
                dlg.exec()
            elif err:
                QMessageBox.warning(
                    self, "Buscar Actualizaciones",
                    f"No se pudo comprobar si hay actualizaciones:\n{err}"
                )
            else:
                from version import __version__
                QMessageBox.information(
                    self, "Buscar Actualizaciones",
                    f"¡Estás al día!\nAura Writer v{__version__} es la versión más reciente."
                )

        worker.check_finished.connect(_on_finish)
        worker.start()
