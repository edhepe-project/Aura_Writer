import sys
import os
import logging
import ctypes
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon

# ── Logging Seguro (Guarda en APPDATA para nunca fallar por permisos) ──
def _setup_logging():
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        log_dir = os.path.join(appdata, "AuraWriter") if appdata else os.path.expanduser("~/.aurawriter")
    else:
        log_dir = os.path.expanduser("~/.config/aura_writer")
    
    try:
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "aura_error.log")
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        )
    except Exception:
        logging.basicConfig(level=logging.INFO)

_setup_logging()
log = logging.getLogger(__name__)

# ── Path de importaciones ──────────────────────────────────────────────
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from ui.main_window import AuraMainWindow
from ui.login_dialog import LoginDialog
from core.theme_manager import ThemeManager


def main():
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        bundle_dir = getattr(sys, "_MEIPASS")
    else:
        bundle_dir = os.path.dirname(current_dir)

    if sys.platform == "win32":
        try:
            myappid = "aura.writer.app.1.0"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception as e:
            log.warning("Could not set AppUserModelID: %s", e)

    app = QApplication(sys.argv)
    
    icon_path = os.path.join(bundle_dir, "aura_writer.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    app.setStyle("Fusion")

    # ── Tema global (lee preferencia guardada) ──────────────────────────
    ThemeManager.apply(app, ThemeManager.load())

    # ── Motor de sonido (inicializar con QApplication activo) ──────────
    try:
        from core.sound_manager import AuraSoundEngine
        AuraSoundEngine.instance()  # crea el singleton mientras el event loop existe
    except Exception as e:
        log.warning("Sound engine init failed: %s", e)

    # Detectar si se pasó un archivo .aura como argumento (Doble clic en Windows)
    initial_file = None
    if len(sys.argv) > 1 and sys.argv[1].lower().endswith(".aura") and os.path.exists(sys.argv[1]):
        initial_file = os.path.abspath(sys.argv[1])

    attempts = 0
    max_attempts = 3
    last_project_path = initial_file

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
                    # Obtener el código TOTP que el usuario pudo haber ingresado
                    totp_code = login.get_totp_code() or ""

                    # Detectar ANTES de abrir si el archivo requiere TOTP (formato V3).
                    # Esto evita el falso positivo donde cualquier error de apertura
                    # disparaba el diálogo de TOTP por coincidir palabras en el mensaje.
                    from core.security import SecurityManager as _SM
                    try:
                        with open(project_path, 'rb') as _f:
                            _hdr_pre = _f.read(6)
                        _is_v3_file = _SM.is_v3_format(_hdr_pre)
                    except OSError:
                        _is_v3_file = False

                    # Si es V3 y no se proporcionó código, pedirlo antes de intentar abrir
                    if _is_v3_file and not totp_code:
                        login2 = LoginDialog()
                        login2.project_path = project_path
                        login2.open_pass_input.setText(password)
                        login2.btn_select_file.setText(os.path.basename(project_path))
                        login2.show_totp_field()
                        login2._validate()
                        if not login2.exec():
                            sys.exit(0)
                        totp_code = login2.get_totp_code() or ""

                    try:
                        main_win.project_manager.open_project(project_path, password,
                                                              totp_code=totp_code)
                    except ValueError as ve:
                        err_lower = str(ve).lower()
                        # Solo reintentar con TOTP si el archivo es realmente V3
                        if _is_v3_file and ("totp" in err_lower or "autenticación" in err_lower):
                            login2 = LoginDialog()
                            login2.project_path = project_path
                            login2.open_pass_input.setText(password)
                            login2.btn_select_file.setText(os.path.basename(project_path))
                            login2.show_totp_field()
                            login2._validate()
                            if not login2.exec():
                                sys.exit(0)
                            totp_code = login2.get_totp_code() or ""
                            # Segundo intento con código TOTP correcto
                            main_win.project_manager.open_project(project_path, password,
                                                                   totp_code=totp_code)
                        else:
                            raise  # contraseña incorrecta, llave maestra distinta, etc.

                    # ── Post-apertura: manejar 2FA según versión del formato ──────
                    if main_win.project_manager.is_2fa_enabled():
                        # Leer el header del archivo recién abierto para saber la versión
                        with open(project_path, 'rb') as _f:
                            _hdr = _f.read(6)
                        from core.security import SecurityManager as _SM

                        if _SM.is_v2_format(_hdr):
                            # Archivo V2: TOTP solo en UI, verificar ahora
                            if not totp_code:
                                login2 = LoginDialog()
                                login2.project_path = project_path
                                login2.open_pass_input.setText(password)
                                login2.btn_select_file.setText(os.path.basename(project_path))
                                login2.show_totp_field()
                                login2._validate()
                                if not login2.exec():
                                    sys.exit(0)
                                totp_code = login2.get_totp_code() or ""

                            if totp_code:
                                if not main_win.project_manager.verify_totp(totp_code):
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
                                QMessageBox.critical(None, "2FA",
                                                     "Se requiere un código de autenticación.")
                                main_win.project_manager.close_project()
                                sys.exit(0)

                        else:
                            # Archivo V3: TOTP ya validado criptográficamente en open_project.
                            # Si fue código de recuperación (XXXX-XXXX), consumirlo ahora.
                            is_recovery = (
                                len(totp_code.replace("-", "").replace(" ", "")) == 8
                                and "-" in totp_code
                            )
                            if is_recovery:
                                if not main_win.project_manager.use_recovery_code(totp_code):
                                    QMessageBox.critical(
                                        None, "Código de recuperación",
                                        "El código de recuperación no es válido o ya fue usado.\n"
                                        "Verifica tus códigos de respaldo."
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

