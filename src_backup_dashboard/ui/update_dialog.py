# ─────────────────────────────────────────────────────────────────────────────
# Aura Writer — Diálogo de Actualizaciones
# Muestra información de nuevas versiones y gestiona la descarga.
# ─────────────────────────────────────────────────────────────────────────────
import os
import sys
import subprocess
import webbrowser
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextBrowser, QProgressBar, QMessageBox, QWidget
)
from PyQt6.QtCore import Qt
import qtawesome as qta

from version import __version__, APP_NAME, APP_URL
from core.updater import UpdateCheckWorker, DownloadWorker


class UpdateDialog(QDialog):
    """Diálogo para notificar sobre nuevas versiones y permitir la descarga."""

    def __init__(self, release_info: dict, parent=None):
        super().__init__(parent)
        self.release_info = release_info
        self._download_worker = None
        self.setWindowTitle(f"Actualización disponible — {APP_NAME}")
        self.setFixedSize(520, 420)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(18, 18, 18, 18)

        # ── Encabezado ──────────────────────────────────────────────
        header = QHBoxLayout()
        icon_lbl = QLabel()
        try:
            icon_lbl.setPixmap(qta.icon("fa5s.arrow-alt-circle-up", color="#30d158").pixmap(44, 44))
        except Exception:
            pass
        header.addWidget(icon_lbl)

        new_ver = self.release_info.get("version", "Nueva")
        title_text = f"<b>¡Nueva versión disponible: v{new_ver}!</b><br>" \
                     f"<span style='color:#8e8e93;'>Versión actual instalada: v{__version__}</span>"
        lbl_title = QLabel(title_text)
        lbl_title.setStyleSheet("font-size: 13px;")
        header.addWidget(lbl_title)
        header.addStretch()
        layout.addLayout(header)

        # ── Notas de la versión (Changelog) ─────────────────────────
        lbl_notes = QLabel("Novedades y cambios:")
        lbl_notes.setStyleSheet("font-weight: bold; font-size: 11px;")
        layout.addWidget(lbl_notes)

        self.notes_browser = QTextBrowser()
        self.notes_browser.setOpenExternalLinks(True)
        raw_notes = self.release_info.get("notes", "").strip()
        if not raw_notes:
            raw_notes = "Mejoras de rendimiento y corrección de errores."
        
        # Renderizar markdown básico
        self.notes_browser.setMarkdown(raw_notes)
        layout.addWidget(self.notes_browser)

        # ── Barra de Progreso (Oculta al inicio) ─────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("")
        self.lbl_status.setVisible(False)
        self.lbl_status.setStyleSheet("font-size: 11px; color: #8e8e93;")
        layout.addWidget(self.lbl_status)

        # ── Botones de acción ────────────────────────────────────────
        btn_layout = QHBoxLayout()

        self.btn_web = QPushButton("Ver en GitHub")
        self.btn_web.setStyleSheet("padding: 6px 12px; font-size: 11px;")
        self.btn_web.clicked.connect(self._open_web)
        btn_layout.addWidget(self.btn_web)

        btn_layout.addStretch()

        self.btn_later = QPushButton("Más tarde")
        self.btn_later.setStyleSheet("padding: 6px 14px; font-size: 11px;")
        self.btn_later.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_later)

        installer_url = self.release_info.get("installer_url")
        if installer_url:
            self.btn_download = QPushButton("Descargar e Instalar")
            self.btn_download.setStyleSheet(
                "background-color: #30d158; color: white; font-weight: bold; padding: 6px 16px; font-size: 12px;"
            )
            self.btn_download.clicked.connect(self._start_download)
            btn_layout.addWidget(self.btn_download)
        else:
            self.btn_download = QPushButton("Ir a la descarga")
            self.btn_download.setStyleSheet(
                "background-color: #0a84ff; color: white; font-weight: bold; padding: 6px 16px; font-size: 12px;"
            )
            self.btn_download.clicked.connect(self._open_web)
            btn_layout.addWidget(self.btn_download)

        layout.addLayout(btn_layout)

    def _open_web(self):
        url = self.release_info.get("url", APP_URL)
        webbrowser.open(url)

    def _start_download(self):
        installer_url = self.release_info.get("installer_url")
        installer_name = self.release_info.get("installer_name", "AuraWriter_Update.exe")
        if not installer_url:
            self._open_web()
            return

        self.btn_download.setEnabled(False)
        self.btn_later.setText("Cancelar")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.lbl_status.setVisible(True)
        self.lbl_status.setText("Descargando actualización...")

        self._download_worker = DownloadWorker(installer_url, installer_name, self)
        self._download_worker.progress.connect(self._on_download_progress)
        self._download_worker.finished.connect(self._on_download_finished)
        self._download_worker.start()

    def _on_download_progress(self, downloaded: int, total: int):
        if total > 0:
            pct = int((downloaded / total) * 100)
            self.progress_bar.setValue(pct)
            mb_down = downloaded / (1024 * 1024)
            mb_tot = total / (1024 * 1024)
            self.lbl_status.setText(f"Descargando: {mb_down:.1f} MB de {mb_tot:.1f} MB ({pct}%)")
        else:
            self.progress_bar.setRange(0, 0) # Indeterminado

    def _on_download_finished(self, success: bool, path_or_error: str):
        if success:
            self.lbl_status.setText("Descarga completada. Ejecutando instalador...")
            reply = QMessageBox.information(
                self,
                "Actualización Lista",
                "El instalador se ha descargado correctamente.\n\n"
                "Aura Writer se cerrará para completar la actualización.\n"
                "¿Deseas ejecutar el instalador ahora?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    # Ejecutar instalador de forma independiente
                    subprocess.Popen([path_or_error], shell=True)
                    # Cerrar la aplicación actual
                    sys.exit(0)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"No se pudo iniciar el instalador:\n{e}")
                    self.btn_download.setEnabled(True)
        else:
            self.progress_bar.setVisible(False)
            self.lbl_status.setText(f"Error: {path_or_error}")
            QMessageBox.warning(self, "Error en la descarga", path_or_error)
            self.btn_download.setEnabled(True)
            self.btn_later.setText("Cerrar")

    def reject(self):
        if self._download_worker and self._download_worker.isRunning():
            self._download_worker.cancel()
            self._download_worker.wait()
        super().reject()
