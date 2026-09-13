import sys
import os
import logging
import ctypes
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon

# ── Logging ────────────────────────────────────────────────────────────
logging.basicConfig(
    filename="aura_error.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
log = logging.getLogger(__name__)

# ── Path de importaciones ──────────────────────────────────────────────
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from ui.main_window import AuraMainWindow
from ui.login_dialog import LoginDialog
from core.theme_manager import ThemeManager


def main():
    if sys.platform == "win32":
        try:
            myappid = "aura.writer.app.1.0"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception as e:
            log.warning("Could not set AppUserModelID: %s", e)

    app = QApplication(sys.argv)
    
    icon_path = os.path.join(os.path.dirname(current_dir), "aura_writer.ico")
    app.setWindowIcon(QIcon(icon_path))
    
    app.setStyle("Fusion")

    # ── Tema global (lee preferencia guardada) ──────────────────────────
    ThemeManager.apply(app, ThemeManager.load())


    attempts = 0
    max_attempts = 3
    last_project_path = None

    while attempts < max_attempts:
        try:
            login = LoginDialog()
            if last_project_path:
                login.project_path = last_project_path
                login.btn_select_file.setText(os.path.basename(last_project_path))
            
            if not login.exec():
                sys.exit(0)

            project_path, password, mode, extra = login.get_credentials()
            last_project_path = project_path
            main_win = AuraMainWindow()

            try:
                if mode == LoginDialog.MODE_NEW:
                    main_win.project_manager.create_new_project(
                        name=extra.get("title", "Nuevo Universo"),
                        author=extra.get("author", ""),
                        password=password,
                        export_path=project_path,
                    )

                    # ── Configurar 2FA si el usuario lo eligió ──────────
                    if extra.get("enable_2fa"):
                        from ui.totp_setup_dialog import TOTPSetupDialog
                        totp_dlg = TOTPSetupDialog(
                            universe_title=extra.get("title", "Escritor"),
                            parent=None
                        )
                        if totp_dlg.exec():
                            result = totp_dlg.get_result()
                            if result.get("enabled"):
                                main_win.project_manager.enable_2fa(
                                    result["secret"], result["recovery_codes"]
                                )
                                QMessageBox.information(
                                    None, "2FA Activado",
                                    "La autenticación de doble factor ha sido activada.\n"
                                    "Necesitarás tu app de autenticación para abrir este proyecto."
                                )

                else:
                    main_win.project_manager.open_project(project_path, password)

                    # ── Verificar 2FA si está activo ────────────────────
                    if main_win.project_manager.is_2fa_enabled():
                        totp_code = login.get_totp_code()

                        if not totp_code:
                            # El campo TOTP no estaba visible — volver a pedir
                            login2 = LoginDialog()
                            login2.project_path = project_path
                            login2.open_pass_input.setText(password)
                            login2.btn_select_file.setText(os.path.basename(project_path))
                            login2.show_totp_field()
                            login2._validate()
                            if not login2.exec():
                                sys.exit(0)
                            totp_code = login2.get_totp_code()

                        if totp_code:
                            # Intentar código TOTP normal
                            if not main_win.project_manager.verify_totp(totp_code):
                                # Intentar como código de recuperación
                                if not main_win.project_manager.use_recovery_code(totp_code):
                                    QMessageBox.critical(
                                        None, "2FA",
                                        "Código de autenticación incorrecto.\n"
                                        "Verifica tu app de autenticación e intenta de nuevo."
                                    )
                                    main_win.project_manager.close_project()
                                    sys.exit(0)
                                else:
                                    remaining = len(main_win.project_manager.metadata.totp_recovery_codes)
                                    QMessageBox.information(
                                        None, "Código de recuperación",
                                        f"Código de recuperación usado.\n"
                                        f"Quedan {remaining} códigos de recuperación."
                                    )
                        else:
                            QMessageBox.critical(None, "2FA", "Se requiere un código de autenticación.")
                            main_win.project_manager.close_project()
                            sys.exit(0)

                meta = main_win.project_manager.metadata
                main_win.setWindowTitle(f"Aura Writer - {meta.title}")
                main_win.outline_tree.populate_from_metadata(meta)
                main_win.char_dock.populate(meta.characters, meta.relations, meta.obras)

                main_win.show()
                # Verificar versiones USB después de mostrar la ventana
                # (requiere que la UI esté visible para mostrar diálogos)
                main_win._check_usb_version_on_open()
                sys.exit(app.exec())

            except ValueError as ve:
                attempts += 1
                if attempts >= max_attempts:
                    QMessageBox.critical(None, "Bloqueado", "Demasiados intentos fallidos. Cerrando aplicación.")
                    sys.exit(1)
                else:
                    msg = (
                        f"{str(ve)}\n\n"
                        f"Intentos restantes: {max_attempts - attempts}\n\n"
                        "💡 Si estás abriendo este archivo en una computadora nueva, "
                        "asegúrate de haber configurado tu Llave Maestra usando el botón '🔑 Llave...' en la pantalla de inicio."
                    )
                    QMessageBox.warning(None, "Error de Acceso", msg)
                log.warning("Error de acceso: %s", ve)

        except Exception:
            log.exception("Error crítico durante la ejecución")
            QMessageBox.critical(
                None, "Error Inesperado",
                "Ocurrió un error inesperado.\nRevisa aura_error.log para más detalles."
            )
            sys.exit(1)


if __name__ == "__main__":
    main()

