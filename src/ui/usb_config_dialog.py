"""
Aura Writer — USB Configuration Dialog
Diálogo premium para configurar la sincronización con memoria USB.
"""

import os
import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QCheckBox, QLineEdit,
    QMessageBox, QGroupBox, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from core.usb import USBSync, USBDrive

log = logging.getLogger(__name__)


class USBConfigDialog(QDialog):
    """Diálogo para configurar la sincronización USB."""

    def __init__(self, project_manager, parent=None):
        super().__init__(parent)
        self.project_manager = project_manager
        self.usb_sync = project_manager.usb_sync
        self._selected_drive: USBDrive | None = None

        self.setWindowTitle("⚙️ Configuración USB — Aura Writer")
        self.setFixedSize(520, 580)
        self._build_ui()
        self._refresh_drives()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # ── Título ──────────────────────────────────────────────────
        title = QLabel("🔌 Sincronización con Memoria USB")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        subtitle = QLabel(
            "Configura una USB dedicada para mantener una copia cifrada "
            "de tu novela sincronizada automáticamente."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size: 12px; margin-bottom: 8px;")
        layout.addWidget(subtitle)

        # ── Separador ───────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        # ── USBs detectadas ─────────────────────────────────────────
        drives_group = QGroupBox("Unidades USB detectadas")
        drives_layout = QVBoxLayout(drives_group)

        self.drives_list = QListWidget()
        self.drives_list.setMinimumHeight(120)
        self.drives_list.setMaximumHeight(180)
        self.drives_list.currentItemChanged.connect(self._on_drive_selected)
        drives_layout.addWidget(self.drives_list)

        btn_refresh = QPushButton("🔄 Buscar USBs")
        btn_refresh.setFixedWidth(140)
        btn_refresh.clicked.connect(self._refresh_drives)
        drives_layout.addWidget(btn_refresh, alignment=Qt.AlignmentFlag.AlignRight)

        layout.addWidget(drives_group)

        # ── Configuración ───────────────────────────────────────────
        config_group = QGroupBox("Configuración")
        config_layout = QVBoxLayout(config_group)

        # Nombre del archivo en la USB
        fname_layout = QHBoxLayout()
        fname_label = QLabel("Nombre del archivo en USB:")
        self.fname_input = QLineEdit()
        self.fname_input.setPlaceholderText("mi_novela.aura")

        # Pre-rellenar con el nombre actual
        if self.usb_sync.usb_filename:
            self.fname_input.setText(self.usb_sync.usb_filename)
        elif self.project_manager.current_project_path:
            default_name = os.path.basename(self.project_manager.current_project_path)
            self.fname_input.setText(default_name)

        fname_layout.addWidget(fname_label)
        fname_layout.addWidget(self.fname_input)
        config_layout.addLayout(fname_layout)

        # Checkbox auto-sync
        self.chk_enabled = QCheckBox("Sincronizar automáticamente al guardar")
        self.chk_enabled.setChecked(self.usb_sync.enabled)
        config_layout.addWidget(self.chk_enabled)

        layout.addWidget(config_group)

        # ── Estado actual ───────────────────────────────────────────
        status_group = QGroupBox("Estado actual")
        status_layout = QVBoxLayout(status_group)

        self.status_label = QLabel("Sin configuración USB")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("font-size: 12px;")
        status_layout.addWidget(self.status_label)

        self._update_status_label()
        layout.addWidget(status_group)

        # ── Botones ─────────────────────────────────────────────────
        btn_layout = QHBoxLayout()

        self.btn_import = QPushButton("📥 Importar desde USB")
        self.btn_import.setToolTip(
            "Reemplaza el archivo local con la versión de la USB.\n"
            "Se creará un backup del archivo local (.aura.bak) antes de importar."
        )
        self.btn_import.clicked.connect(self._on_import_from_usb)
        btn_layout.addWidget(self.btn_import)

        btn_layout.addStretch()

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        self.btn_save = QPushButton("✅ Guardar Configuración")
        self.btn_save.clicked.connect(self._on_save)
        self.btn_save.setStyleSheet("background-color: #30d158; color: white; font-weight: bold;")
        btn_layout.addWidget(self.btn_save)

        layout.addLayout(btn_layout)

        # Actualizar estado del botón de importación
        self._refresh_import_button()


    # ------------------------------------------------------------------
    # Lógica
    # ------------------------------------------------------------------

    def _refresh_drives(self):
        """Escanea y lista las unidades USB conectadas."""
        self.drives_list.clear()
        self._selected_drive = None
        drives = USBSync.detect_removable_drives()

        if not drives:
            item = QListWidgetItem("  ❌  No se detectaron unidades USB")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setForeground(Qt.GlobalColor.gray)
            self.drives_list.addItem(item)
            return

        for drive in drives:
            label = drive.label or "(Sin nombre)"
            text = f"  💾  {label}  —  {drive.path}  ({drive.free_gb:.1f} GB libre)"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, drive)
            self.drives_list.addItem(item)

            # Pre-seleccionar si coincide con la configuración actual
            if (self.usb_sync.volume_label and
                    drive.label.upper() == self.usb_sync.volume_label.upper()):
                self.drives_list.setCurrentItem(item)

    def _on_drive_selected(self, current, previous):
        """Cuando el usuario selecciona una unidad."""
        if current:
            self._selected_drive = current.data(Qt.ItemDataRole.UserRole)
        else:
            self._selected_drive = None

    def _update_status_label(self):
        """Actualiza la etiqueta de estado con la configuración actual."""
        if not self.usb_sync.is_configured():
            self.status_label.setText(
                "📌 No hay USB configurada.\n"
                "Selecciona una unidad arriba y guarda la configuración."
            )
            self.status_label.setStyleSheet("color: #8e8e93; font-size: 12px;")
            return

        drive = self.usb_sync.find_configured_drive()
        if drive:
            sync_time = self.usb_sync.last_sync_time or "Nunca"
            self.status_label.setText(
                f"🟢 USB conectada: {drive.label} ({drive.path})\n"
                f"Archivo: {self.usb_sync.usb_filename}\n"
                f"Última sincronización: {sync_time}"
            )
            self.status_label.setStyleSheet("color: #30d158; font-size: 12px;")
        else:
            self.status_label.setText(
                f"🔴 USB '{self.usb_sync.volume_label}' no está conectada.\n"
                f"Archivo configurado: {self.usb_sync.usb_filename}\n"
                f"Conecta la USB para sincronizar."
            )
            self.status_label.setStyleSheet("color: #ff453a; font-size: 12px;")

    def _refresh_import_button(self):
        """Habilita el botón de importación solo si la USB está conectada y tiene el archivo."""
        can_import = False
        if self.usb_sync.is_configured() and self.project_manager.current_project_path:
            drive = self.usb_sync.find_configured_drive()
            if drive:
                import os as _os
                usb_file = _os.path.join(drive.path, self.usb_sync.usb_filename)
                can_import = _os.path.exists(usb_file)
        self.btn_import.setEnabled(can_import)
        if not can_import:
            self.btn_import.setStyleSheet("color: #636366;")
        else:
            self.btn_import.setStyleSheet(
                "background-color: #0a84ff; color: white; font-weight: bold;"
            )

    def _on_import_from_usb(self):
        """Importa el archivo .aura desde la USB al disco local."""
        reply = QMessageBox.question(
            self, "Importar desde USB",
            f"¿Reemplazar el archivo local con la versión de la USB?\n\n"
            f"Se creará un backup del archivo local como:\n"
            f"{self.project_manager.current_project_path}.bak\n\n"
            f"Esta acción recargará el proyecto.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            backup_path = self.project_manager.import_from_usb()

            # Reabrir el proyecto con la contraseña actual
            password = self.project_manager.password
            project_path = self.project_manager.current_project_path
            self.project_manager.close_project()
            self.project_manager.open_project(project_path, password)

            self._update_status_label()
            self._refresh_import_button()

            QMessageBox.information(
                self, "✅ Importación exitosa",
                f"El proyecto fue actualizado desde la USB.\n\n"
                f"Backup del archivo anterior:\n{backup_path}"
            )
            self.accept()

        except Exception as e:
            log.exception("Error al importar desde USB en diálogo de configuración")
            QMessageBox.critical(
                self, "Error al importar",
                f"No se pudo importar el archivo desde la USB:\n\n{e}"
            )



    def _on_save(self):
        """Guarda la configuración USB."""
        if not self._selected_drive:
            QMessageBox.warning(
                self, "USB",
                "Selecciona una unidad USB de la lista."
            )
            return

        filename = self.fname_input.text().strip()
        if not filename:
            QMessageBox.warning(
                self, "USB",
                "Ingresa un nombre para el archivo en la USB."
            )
            return

        # Asegurar extensión .aura
        if not filename.lower().endswith(".aura"):
            filename += ".aura"

        label = self._selected_drive.label
        if not label:
            QMessageBox.warning(
                self, "USB",
                "La USB seleccionada no tiene nombre de volumen.\n\n"
                "Por favor, asígnale un nombre en Windows (clic derecho → Propiedades)\n"
                "para que Aura Writer pueda identificarla automáticamente."
            )
            return

        # Configurar
        enabled = self.chk_enabled.isChecked()
        self.usb_sync.configure(label, filename, enabled)

        # Persistir configuración
        if self.project_manager.current_project_path:
            self.usb_sync.save_config(self.project_manager.current_project_path)

        log.info("USB configurada: volumen='%s', archivo='%s', enabled=%s",
                 label, filename, enabled)

        # Confirmar con sync inicial si la USB está lista
        if enabled:
            reply = QMessageBox.question(
                self, "Sincronizar ahora",
                f"¿Sincronizar el proyecto con '{label}' ahora?\n\n"
                f"Se copiará '{filename}' a la USB.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    self.project_manager.save_project()
                    QMessageBox.information(
                        self, "USB",
                        f"✅ Proyecto sincronizado con '{label}' exitosamente."
                    )
                except Exception as e:
                    QMessageBox.warning(
                        self, "USB",
                        f"Error al sincronizar: {e}"
                    )

        self.accept()
