"""
Aura Writer — USB Controller Mixin
Indicador de estado USB, configuracion, sincronizacion y reporte.
"""
import os
import logging
from datetime import datetime
from PyQt6.QtWidgets import QMessageBox

log = logging.getLogger(__name__)


class UsbControllerMixin:
    """Mixin para AuraMainWindow: gestion de sincronizacion USB."""

    def _update_usb_indicator(self):
        """Actualiza el indicador visual de estado USB en la barra de estado."""
        usb = self.project_manager.usb_sync
        if not usb.is_configured():
            self._usb_indicator.setText("USB: No configurada")
            self._usb_indicator.setStyleSheet("color: #636366; font-size: 11px; padding: 0 8px;")
            return
        drive = usb.find_configured_drive()
        if drive:
            self._usb_indicator.setText(f"USB: {drive.label} ({drive.path.rstrip(os.sep)})")
            self._usb_indicator.setStyleSheet("color: #30d158; font-size: 11px; padding: 0 8px;")
        else:
            self._usb_indicator.setText(f"USB: {usb.volume_label} (no conectada)")
            self._usb_indicator.setStyleSheet("color: #ff453a; font-size: 11px; padding: 0 8px;")

    def open_usb_config(self):
        """Abre el dialogo de configuracion USB."""
        if not self.project_manager.metadata:
            QMessageBox.warning(self, "USB", "Abre un proyecto primero.")
            return
        from ui.usb_config_dialog import USBConfigDialog
        dlg = USBConfigDialog(self.project_manager, self)
        if dlg.exec():
            self._update_usb_indicator()
            self.statusBar().showMessage("Configuracion USB actualizada", 3000)

    def sync_usb_now(self):
        """Fuerza sincronizacion inmediata con USB."""
        if not self.project_manager.metadata:
            QMessageBox.warning(self, "USB", "Abre un proyecto primero.")
            return
        usb = self.project_manager.usb_sync
        if not usb.is_configured():
            QMessageBox.information(
                self, "USB",
                "No hay una USB configurada.\n\nVe a USB para configurarla."
            )
            return
        self.save_project()
        self._update_usb_indicator()

    def show_usb_status(self):
        """Muestra informacion detallada del estado de sincronizacion USB."""
        usb = self.project_manager.usb_sync
        if not usb.is_configured():
            QMessageBox.information(self, "Estado USB", "No hay una USB configurada.")
            return
        drive = usb.find_configured_drive()
        if drive:
            in_sync = False
            if self.project_manager.current_project_path:
                in_sync = usb.is_usb_in_sync(self.project_manager.current_project_path)
            info = (
                f"Estado de Sincronizacion USB\n\n"
                f"Volumen: {drive.label}\nUnidad: {drive.path}\n"
                f"Espacio libre: {drive.free_gb:.2f} GB\nArchivo: {usb.usb_filename}\n\n"
                f"Sincronizado: {'Si' if in_sync else 'No'}\n"
                f"Ultimo sync: {usb.last_sync_time or 'Nunca'}"
            )
        else:
            info = (
                f"Estado USB\n\n"
                f"Volumen configurado: {usb.volume_label}\n"
                f"Estado: No conectada"
            )
        QMessageBox.information(self, "Estado USB", info)

    # ------------------------------------------------------------------
    # Detección de versión más nueva / conflicto al abrir proyecto
    # ------------------------------------------------------------------

    def _check_usb_version_on_open(self):
        """
        Compara la versión local con la de la USB justo después de abrir el proyecto.

        Comportamiento según estado:
          - usb_newer   → pregunta si importar la versión más nueva de la USB
          - both_changed → alerta de conflicto con opciones: mantener local / importar USB
          - in_sync / local_newer / disconnected / usb_missing → sin diálogo
        """
        pm = self.project_manager
        usb = pm.usb_sync

        if not usb.is_configured() or not pm.current_project_path:
            return

        try:
            result = usb.compare_versions(pm.current_project_path)
        except Exception as e:
            log.warning("_check_usb_version_on_open: error al comparar versiones: %s", e)
            return

        status = result["status"]

        if status in (usb.SYNC_IN_SYNC, usb.SYNC_LOCAL_NEWER,
                      usb.SYNC_DISCONNECTED, usb.SYNC_USB_MISSING):
            return  # Sin acción necesaria

        if status == usb.SYNC_USB_NEWER:
            self._prompt_import_newer_usb(result)
        elif status == usb.SYNC_CONFLICT:
            self._prompt_resolve_conflict(result)

    def _prompt_import_newer_usb(self, version_info: dict):
        """Diálogo cuando la USB tiene una versión más reciente que el local."""
        usb_time = datetime.fromtimestamp(version_info["usb_mtime"]).strftime("%d/%m/%Y %H:%M")
        local_time = datetime.fromtimestamp(version_info["local_mtime"]).strftime("%d/%m/%Y %H:%M")

        msg = QMessageBox(self)
        msg.setWindowTitle("USB — Versión más nueva detectada")
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setText(
            "La USB contiene una versión <b>más reciente</b> del proyecto.\n\n"
            f"Local:   {local_time}\n"
            f"USB:     {usb_time}\n\n"
            "¿Deseas importar la versión de la USB?\n"
            "<small>(El archivo local actual se guardará como copia de respaldo .bak)</small>"
        )
        btn_import = msg.addButton("Importar desde USB", QMessageBox.ButtonRole.AcceptRole)
        msg.addButton("Mantener versión local", QMessageBox.ButtonRole.RejectRole)
        msg.setDefaultButton(btn_import)
        msg.exec()

        if msg.clickedButton() == btn_import:
            self._do_import_from_usb()

    def _prompt_resolve_conflict(self, version_info: dict):
        """Diálogo de conflicto cuando ambas versiones difieren sin un orden claro."""
        usb_time = datetime.fromtimestamp(version_info["usb_mtime"]).strftime("%d/%m/%Y %H:%M")
        local_time = datetime.fromtimestamp(version_info["local_mtime"]).strftime("%d/%m/%Y %H:%M")

        msg = QMessageBox(self)
        msg.setWindowTitle("USB — Conflicto de versiones")
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText(
            "<b>¡Conflicto detectado!</b>\n\n"
            "El proyecto local y el de la USB tienen contenidos distintos "
            "con timestamps similares. Probablemente se editaron de forma independiente.\n\n"
            f"Local:   {local_time}\n"
            f"USB:     {usb_time}\n\n"
            "¿Qué versión deseas conservar?"
        )
        btn_usb   = msg.addButton("Importar desde USB (y hacer backup del local)",
                                  QMessageBox.ButtonRole.AcceptRole)
        btn_local = msg.addButton("Mantener local (y sobrescribir USB al guardar)",
                                  QMessageBox.ButtonRole.RejectRole)
        msg.setDefaultButton(btn_local)
        msg.exec()

        if msg.clickedButton() == btn_usb:
            self._do_import_from_usb()
        # Si elige local, la próxima vez que guarde la USB se actualizará automáticamente

    def _do_import_from_usb(self):
        """Ejecuta la importación desde USB, recarga el proyecto y notifica al usuario."""
        pm = self.project_manager
        try:
            backup_path = pm.import_from_usb()
            # Reabrir el proyecto con la contraseña actual (el archivo local ya fue reemplazado)
            password = pm.password
            project_path = pm.current_project_path
            pm.close_project()
            pm.open_project(project_path, password)

            # Actualizar la UI con los nuevos metadatos
            meta = pm.metadata
            self.setWindowTitle(f"Aura Writer - {meta.title}")
            self.outline_tree.populate_from_metadata(meta)
            self.char_dock.populate(meta.characters, meta.relations, meta.obras)
            if hasattr(self, "_refresh_place_dock"):
                self._refresh_place_dock()
            self._update_usb_indicator()

            QMessageBox.information(
                self,
                "✅ Importación exitosa",
                f"El proyecto fue actualizado desde la USB.\n\n"
                f"Backup del archivo anterior guardado en:\n{backup_path}"
            )
            log.info("Proyecto reimportado desde USB exitosamente.")

        except Exception as e:
            log.exception("Error al importar desde USB")
            QMessageBox.critical(
                self, "Error al importar",
                f"No se pudo importar el proyecto desde la USB:\n\n{e}"
            )

