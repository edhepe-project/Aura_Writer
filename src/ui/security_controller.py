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

        # ── Auto-guardado de emergencia mientras la sesion esta bloqueada ──
        # Si el equipo se apaga estando bloqueado, este timer garantiza que
        # el ultimo estado escrito al disco sea reciente (max 60 s de perdida).
        from PyQt6.QtCore import QTimer
        _autosave_timer = QTimer(self)
        _autosave_timer.setInterval(60_000)  # cada 60 segundos
        _autosave_timer.timeout.connect(self._autosave_while_locked)
        _autosave_timer.start()

        meta = self.project_manager.metadata
        dialog = LockDialog(
            correct_password=self.project_manager.password,
            totp_enabled=meta.totp_enabled,
            totp_secret=meta.totp_secret,
            recovery_codes=list(meta.totp_recovery_codes),
        )
        if dialog.exec():
            _autosave_timer.stop()
            if dialog.recovery_codes != meta.totp_recovery_codes:
                meta.totp_recovery_codes = dialog.recovery_codes
                self.save_project()
            self.show()
            self.statusBar().showMessage("Sesion restaurada", 3000)
        else:
            _autosave_timer.stop()
            sys.exit(0)

    def _autosave_while_locked(self):
        """Guardado silencioso que se ejecuta periodicamente mientras la sesion esta bloqueada."""
        try:
            self.project_manager.save_project()
        except Exception:
            pass  # silencioso — no molestar al usuario con errores en pantalla de bloqueo


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

        from core.theme_manager import ThemeManager
        c = ThemeManager.palette()
        btn_box = QHBoxLayout()
        btn_disable = QPushButton("Desactivar 2FA")
        btn_disable.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_disable.setStyleSheet(f"""
            QPushButton {{
                background-color: {c["red"]};
                color: #ffffff;
                font-weight: bold;
                padding: 6px 14px;
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {c["red"]};
            }}
        """)
        btn_close = QPushButton("Cerrar")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: {c["bg_button"]};
                color: {c["fg_primary"]};
                border: 1px solid {c["border_default"]};
                border-radius: 6px;
                padding: 6px 14px;
            }}
            QPushButton:hover {{
                background-color: {c["bg_hover"]};
            }}
        """)
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

        MIN_LEN = 8  # igual que en el dialogo de creacion de proyecto

        from ui.login.logic import password_error
        from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                                      QLabel, QLineEdit, QPushButton, QFrame)
        from PyQt6.QtCore import Qt
        from core.theme_manager import ThemeManager

        bg_dialog = ThemeManager.color("bg_surface")
        bg_header = ThemeManager.color("bg_app")
        fg_title = ThemeManager.color("fg_primary")
        fg_desc = ThemeManager.color("fg_muted")
        border_subtle = ThemeManager.color("border_default")
        
        bg_field = ThemeManager.color("bg_input")
        border_field = ThemeManager.color("border_default")
        fg_field = ThemeManager.color("fg_primary")
        lbl_field_fg = ThemeManager.color("fg_muted")
        
        btn_cancel_bg = ThemeManager.color("bg_button")
        btn_cancel_fg = ThemeManager.color("fg_primary")
        btn_cancel_border = ThemeManager.color("border_default")
        btn_cancel_hover = ThemeManager.color("bg_hover")
        
        btn_save_bg = ThemeManager.color("accent")
        btn_save_fg = ThemeManager.color("fg_selected")
        btn_save_hover = ThemeManager.color("accent_hover")
        
        err_red = ThemeManager.color("red")

        dlg = QDialog(self)
        dlg.setWindowTitle("Cambiar Contraseña del Proyecto")
        dlg.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        dlg.setMinimumWidth(440)
        dlg.setModal(True)
        dlg.setStyleSheet(f"QDialog {{ background: {bg_dialog}; }}")

        root = QVBoxLayout(dlg)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Encabezado ────────────────────────────────────────────────────
        header = QLabel()
        header.setTextFormat(Qt.TextFormat.RichText)
        header.setText(
            f"<b style='font-size:15px;color:{fg_title};'>Cambiar contraseña</b><br>"
            f"<span style='font-size:11px;color:{fg_desc};'>"
            f"La nueva contraseña debe tener al menos {MIN_LEN} caracteres.</span>"
        )
        header.setContentsMargins(24, 20, 24, 16)
        header.setStyleSheet(f"background:{bg_header};")
        header.setWordWrap(True)
        root.addWidget(header)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background:{border_subtle}; max-height:1px; border:none;")
        root.addWidget(sep)

        # ── Formulario ────────────────────────────────────────────────────
        form_w = QLabel(); form_w.setStyleSheet(f"background:{bg_dialog};")
        form = QVBoxLayout()
        form.setContentsMargins(24, 20, 24, 24)
        form.setSpacing(12)

        field_style = (
            f"background:{bg_field}; border:1.5px solid {border_field}; border-radius:9px;"
            f"color:{fg_field}; font-size:13px; padding:0 12px; font-family:'Segoe UI',sans-serif;"
        )
        label_style = (
            f"font-size:11px;font-weight:700;color:{lbl_field_fg};"
            f"letter-spacing:0.05em;font-family:'Segoe UI',sans-serif;"
        )

        def make_field(placeholder):
            f = QLineEdit()
            f.setEchoMode(QLineEdit.EchoMode.Password)
            f.setPlaceholderText(placeholder)
            f.setMinimumHeight(42)
            f.setStyleSheet(field_style)
            return f

        def make_field_with_eye(placeholder):
            """Campo de contraseña con botón ojo para mostrar/ocultar."""
            from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
            import qtawesome as qta

            wrapper = QWidget()
            wrapper.setMinimumHeight(42)
            wrapper.setStyleSheet(
                f"background:{bg_field}; border:1.5px solid {border_field}; border-radius:9px;"
            )
            hl = QHBoxLayout(wrapper)
            hl.setContentsMargins(0, 0, 4, 0)
            hl.setSpacing(0)

            field = QLineEdit()
            field.setEchoMode(QLineEdit.EchoMode.Password)
            field.setPlaceholderText(placeholder)
            field.setStyleSheet(
                f"background:transparent; border:none; border-radius:9px;"
                f"color:{fg_field}; font-size:13px; padding:0 10px;"
                f"font-family:'Segoe UI',sans-serif;"
            )
            hl.addWidget(field)

            eye_btn = QPushButton()
            eye_btn.setFixedSize(32, 32)
            eye_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            eye_btn.setCheckable(True)
            eye_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Tab no aterriza aquí
            eye_btn.setIcon(qta.icon("fa5s.eye", color=lbl_field_fg))
            eye_btn.setStyleSheet(f"""
                QPushButton {{ background:transparent; border:none; border-radius:6px; outline:none; }}
                QPushButton:hover {{ background:{btn_cancel_hover}; }}
            """)

            def _toggle(checked, f=field, b=eye_btn):
                if checked:
                    f.setEchoMode(QLineEdit.EchoMode.Normal)
                    b.setIcon(qta.icon("fa5s.eye-slash", color=btn_save_bg))
                else:
                    f.setEchoMode(QLineEdit.EchoMode.Password)
                    b.setIcon(qta.icon("fa5s.eye", color=lbl_field_fg))

            eye_btn.toggled.connect(_toggle)
            hl.addWidget(eye_btn)

            # Exponer el QLineEdit como atributo del wrapper para acceso externo
            wrapper._field = field
            return wrapper, field

        # Contraseña actual (sin ojo — no es necesario verla)
        lbl_curr = QLabel("CONTRASEÑA ACTUAL"); lbl_curr.setStyleSheet(label_style)
        curr_input = make_field("••••••••")
        form.addWidget(lbl_curr); form.addWidget(curr_input)

        # Nueva contraseña (con ojo)
        lbl_new = QLabel("NUEVA CONTRASEÑA"); lbl_new.setStyleSheet(label_style)
        new_wrapper, new_input = make_field_with_eye(f"Mínimo {MIN_LEN} caracteres")
        form.addWidget(lbl_new); form.addWidget(new_wrapper)

        # Confirmar nueva contraseña (con ojo)
        lbl_conf = QLabel("CONFIRMAR NUEVA CONTRASEÑA"); lbl_conf.setStyleSheet(label_style)
        conf_wrapper, conf_input = make_field_with_eye("Repite la nueva contraseña")
        form.addWidget(lbl_conf); form.addWidget(conf_wrapper)

        # Feedback inline
        feedback = QLabel(" ")
        feedback.setStyleSheet(
            f"font-size:12px;color:{err_red};font-family:'Segoe UI',sans-serif;"
            f"padding:6px 10px;background:transparent;border-radius:7px;"
        )
        feedback.setWordWrap(True)
        feedback.setMinimumHeight(32)
        form.addWidget(feedback)

        # Botones
        btn_row = QHBoxLayout(); btn_row.setSpacing(10)
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setMinimumHeight(40)
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background:{btn_cancel_bg};
                color:{btn_cancel_fg};
                border:1px solid {btn_cancel_border};
                border-radius:9px;
                font-size:13px;
                padding:0 18px;
                font-family:'Segoe UI',sans-serif;
            }}
            QPushButton:hover {{
                background:{btn_cancel_hover};
            }}
        """)
        btn_cancel.clicked.connect(dlg.reject)

        btn_save = QPushButton("Guardar contraseña")
        btn_save.setMinimumHeight(40)
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setStyleSheet(f"""
            QPushButton {{
                background:{btn_save_bg};
                color:{btn_save_fg};
                border:none;
                border-radius:9px;
                font-size:13px;
                font-weight:700;
                padding:0 18px;
                font-family:'Segoe UI',sans-serif;
            }}
            QPushButton:hover {{
                background:{btn_save_hover};
            }}
        """)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        form.addLayout(btn_row)

        # Montar formulario en widget de fondo
        body = QFrame()
        body.setStyleSheet(f"background:{bg_dialog};")
        body.setLayout(form)
        root.addWidget(body)

        # ── Validación ────────────────────────────────────────────────────
        def _show_err(msg):
            feedback.setText(f"⚠  {msg}")
            feedback.setStyleSheet(
                f"font-size:12px;color:{err_red};font-family:'Segoe UI',sans-serif;"
                f"padding:6px 10px;background:rgba(255,69,58,0.12);border-radius:7px;"
            )

        def _clear_err():
            feedback.setText(" ")
            feedback.setStyleSheet(
                "font-size:12px;color:transparent;font-family:'Segoe UI',sans-serif;"
                "padding:6px 10px;background:transparent;border-radius:7px;"
            )

        def _do_change():
            curr = curr_input.text()
            new_p = new_input.text()
            conf = conf_input.text()

            if curr != self.project_manager.password:
                _show_err("La contraseña actual es incorrecta.")
                curr_input.clear(); curr_input.setFocus()
                return
            pwd_err = password_error(new_p)
            if pwd_err:
                _show_err(pwd_err)
                new_input.setFocus()
                return
            if new_p != conf:
                _show_err("Las contraseñas nuevas no coinciden.")
                conf_input.setFocus()
                return
            _clear_err()
            try:
                self.project_manager.change_password(new_p)
                dlg.accept()
                QMessageBox.information(
                    self, "Contraseña actualizada",
                    "Tu contraseña fue cambiada con éxito y el proyecto fue guardado."
                )
            except Exception as e:
                _show_err(f"No se pudo cambiar la contraseña: {e}")

        btn_save.clicked.connect(_do_change)
        new_input.returnPressed.connect(lambda: conf_input.setFocus())
        conf_input.returnPressed.connect(_do_change)
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