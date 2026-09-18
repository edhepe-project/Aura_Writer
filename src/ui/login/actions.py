"""
login/actions.py
----------------
Acciones externas disparadas desde LoginDialog:
  - check_updates       : comprueba actualizaciones en GitHub
  - open_app_key_dialog : abre el dialogo de Llave Maestra
"""

from PyQt6.QtWidgets import QMessageBox


def check_updates(dialog) -> None:
    """Comprueba actualizaciones directamente desde la pantalla de bienvenida."""
    from core.updater import UpdateCheckWorker
    from ui.update_dialog import UpdateDialog

    worker = UpdateCheckWorker(dialog)

    def _on_finish(has_update: bool, release_info: dict, err: str):
        if has_update:
            dlg = UpdateDialog(release_info, dialog)
            dlg.exec()
        elif err:
            QMessageBox.warning(
                dialog, "Buscar Actualizaciones",
                f"No se pudo comprobar si hay actualizaciones:\n{err}"
            )
        else:
            from version import __version__
            QMessageBox.information(
                dialog, "Buscar Actualizaciones",
                f"Estas al dia!\nAura Writer v{__version__} es la version mas reciente."
            )

    worker.check_finished.connect(_on_finish)
    worker.start()


def open_app_key_dialog(dialog) -> None:
    """Abre el dialogo de gestion de Llave Maestra de Aplicacion."""
    from ui.app_key_dialog import AppKeyDialog
    dlg = AppKeyDialog(dialog)
    dlg.exec()
