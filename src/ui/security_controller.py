"""
Aura Writer — Security Controller Mixin
Bloqueo rapido, configuracion 2FA, cambio de contrasena, papelera y busqueda.
"""
import sys
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QTextEdit, QPushButton, QLineEdit, QMessageBox)
from PyQt6.QtCore import Qt
from ui.lock_dialog import LockDialog
from ui.search import SearchDialog


class SecurityControllerMixin:
    """Mixin para AuraMainWindow: seguridad, busqueda y papelera."""

    def quick_lock(self):
        """Guarda y bloquea la interfaz de forma segura."""
        if not self.project_manager.metadata:
            return
        # FIX BUG-12: si el guardado falla, no dejar la ventana oculta
        try:
            self.save_project()
        except Exception:
            return  # error ya reportado por save_project(); abortar bloqueo
        self.statusBar().showMessage("Proyecto guardado. Privatizando sesion...", 2000)
        self.hide()
        meta = self.project_manager.metadata
        dialog = LockDialog(
            correct_password=self.project_manager.password,
            totp_enabled=meta.totp_enabled,
            totp_secret=meta.totp_secret,
            recovery_codes=list(meta.totp_recovery_codes),
        )
        if dialog.exec():
            if dialog.recovery_codes != meta.totp_recovery_codes:
                meta.totp_recovery_codes = dialog.recovery_codes
                self.save_project()
            self.show()
            self.statusBar().showMessage("Sesion restaurada", 3000)
        else:
            sys.exit(0)

    def configure_totp(self):
        """Permite activar o desactivar 2FA en el proyecto."""
        if not self.project_manager.metadata:
            QMessageBox.warning(self, "2FA", "Abre un proyecto primero.")
            return
        meta = self.project_manager.metadata
        from ui.totp_setup_dialog import TOTPSetupDialog
        if not meta.totp_enabled:
            dlg = TOTPSetupDialog(universe_title=meta.title or "Escritor", parent=self)
            if dlg.exec() and dlg.confirmed:
                # FIX BUG-10: usar el metodo centralizado del project_manager
                self.project_manager.enable_2fa(dlg.secret, list(dlg.recovery_codes))
                QMessageBox.information(self, "2FA Activado",
                                        "Autenticacion de doble factor activada y guardada.")
        else:
            self._show_totp_admin_dialog(meta)

    def _show_totp_admin_dialog(self, meta):
        """Dialogo de administracion cuando 2FA ya esta activado."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Administrar Autenticacion 2FA")
        dlg.setFixedSize(450, 380)
        l = QVBoxLayout(dlg)
        l.setContentsMargins(20, 20, 20, 20)
        l.setSpacing(12)

        title_lbl = QLabel("2FA esta ACTIVADO")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(title_lbl)

        desc = QLabel("Tu proyecto requiere un codigo de 6 digitos al abrirse.")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(desc)

        l.addWidget(QLabel("Codigos de recuperacion restantes:"))
        codes_text = QTextEdit()
        codes_text.setReadOnly(True)
        codes_text.setPlainText(
            "\n".join(meta.totp_recovery_codes) if meta.totp_recovery_codes else "No quedan codigos."
        )
        codes_text.setFixedHeight(90)
        l.addWidget(codes_text)

        btn_box = QHBoxLayout()
        btn_disable = QPushButton("Desactivar 2FA")
        btn_disable.setStyleSheet(
            "background-color: #ff453a; color: white; font-weight: bold; padding: 6px 14px;"
        )
        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(dlg.accept)
        btn_box.addWidget(btn_disable)
        btn_box.addStretch()
        btn_box.addWidget(btn_close)
        l.addLayout(btn_box)

        def _disable_2fa():
            reply = QMessageBox.question(
                dlg, "Desactivar 2FA", "Desactivar la autenticacion 2FA?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                # FIX BUG-09: usar el metodo centralizado del project_manager
                self.project_manager.disable_2fa()
                dlg.accept()
                QMessageBox.information(self, "2FA Desactivado",
                                        "La autenticacion 2FA ha sido desactivada.")

        btn_disable.clicked.connect(_disable_2fa)
        dlg.exec()

    def change_password_dialog(self):
        """Dialogo para cambiar la contrasena del proyecto."""
        if not self.project_manager.metadata:
            QMessageBox.warning(self, "Seguridad", "Abre un proyecto primero.")
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("Cambiar Contrasena del Proyecto")
        dlg.setFixedSize(400, 260)
        l = QVBoxLayout(dlg)
        l.setContentsMargins(20, 20, 20, 20)
        l.setSpacing(10)
        l.addWidget(QLabel("Introduce la nueva contrasena:"))

        curr_input = QLineEdit()
        curr_input.setEchoMode(QLineEdit.EchoMode.Password)
        curr_input.setPlaceholderText("Contrasena actual")
        l.addWidget(curr_input)

        new_input = QLineEdit()
        new_input.setEchoMode(QLineEdit.EchoMode.Password)
        new_input.setPlaceholderText("Nueva contrasena (minimo 4 caracteres)")
        l.addWidget(new_input)

        confirm_input = QLineEdit()
        confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        confirm_input.setPlaceholderText("Confirmar nueva contrasena")
        l.addWidget(confirm_input)

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(dlg.reject)
        btn_save = QPushButton("Guardar Contrasena")
        btn_save.setStyleSheet("background-color: #30d158; color: white; font-weight: bold;")
        btn_box.addStretch()
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        l.addLayout(btn_box)

        def _do_change():
            curr = curr_input.text()
            new_p = new_input.text()
            conf = confirm_input.text()
            if curr != self.project_manager.password:
                QMessageBox.critical(dlg, "Error", "La contrasena actual es incorrecta.")
                curr_input.clear()
                curr_input.setFocus()
                return
            if len(new_p) < 4:
                QMessageBox.warning(dlg, "Error", "La contrasena debe tener al menos 4 caracteres.")
                return
            if new_p != conf:
                QMessageBox.warning(dlg, "Error", "Las nuevas contrasenas no coinciden.")
                return
            try:
                self.project_manager.change_password(new_p)
                dlg.accept()
                QMessageBox.information(self, "Contrasena Actualizada",
                                        "Contrasena cambiada con exito.")
            except Exception as e:
                QMessageBox.critical(dlg, "Error", f"No se pudo cambiar la contrasena: {e}")

        btn_save.clicked.connect(_do_change)
        dlg.exec()

    def open_trash_dialog(self):
        """Abre el dialogo de la papelera de reciclaje."""
        if not self.project_manager.metadata:
            QMessageBox.warning(self, "Papelera", "Abre un proyecto primero.")
            return
        # FIX BUG-01: vaciar el editor antes de que TrashDialog llame a pm.save_project()
        self._flush_content_to_metadata()
        from ui.trash_dialog import TrashDialog
        dlg = TrashDialog(self.project_manager, self)
        dlg.item_restored.connect(self._on_item_restored_from_trash)
        dlg.exec()

    def _on_item_restored_from_trash(self, item_id: str, item_type: str):
        """Actualiza la interfaz cuando se restaura un elemento de la papelera."""
        self._refresh_tree()
        self._refresh_char_dock()
        self.on_item_selected(item_id, item_type)
        self.outline_tree.select_item_by_id(item_id)

    def open_search(self):
        """Abre el Buscador Global."""
        if not self.project_manager.metadata:
            QMessageBox.warning(self, "Buscador", "No hay un proyecto abierto.")
            return
        dlg = SearchDialog(self.project_manager, self)
        dlg.result_selected.connect(self.navigate_to_item)
        dlg.exec()

    def navigate_to_item(self, item_id: str, item_type: str, query: str = "", is_regex: bool = False):
        """Salta a un elemento específico desde el buscador y resalta la coincidencia en el editor."""
        if item_type == "place":
            if hasattr(self, "_switch_inspector_tab"):
                self._switch_inspector_tab("places")
            if hasattr(self, "place_dock") and self.place_dock:
                self.place_dock.select_place_by_id(item_id)
            if hasattr(self, "open_place_edit_dialog"):
                self.open_place_edit_dialog(item_id)
            return

        self.on_item_selected(item_id, item_type)
        self.outline_tree.select_item_by_id(item_id)

        # Si el elemento seleccionado es un capítulo y hay una búsqueda activa, resaltar el texto
        if item_type == "chapter" and query and hasattr(self, "editor"):
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, lambda: self.editor.find_and_highlight(query, is_regex=is_regex))