"""
syncer.py — Motor central de sincronización bidireccional y verificación SHA-256 para USB.
"""

import os
import shutil
import hashlib
import logging
from datetime import datetime

from core.usb.detector import USBDrive, USBDetector
from core.usb.config import USBSyncConfig

log = logging.getLogger(__name__)


class USBNotFoundError(Exception):
    """La USB configurada no está conectada."""
    pass


class USBSyncError(Exception):
    """Error durante la sincronización con la USB."""
    pass


class USBSync:
    """Gestiona la sincronización del archivo .aura entre disco local y USB."""
    CONFIG_FILENAME = USBSyncConfig.config_path

    # Constantes para el resultado de compare_versions
    SYNC_IN_SYNC = "in_sync"          # Hashes iguales
    SYNC_USB_NEWER = "usb_newer"      # USB tiene mtime más reciente (trabajo en otro equipo)
    SYNC_LOCAL_NEWER = "local_newer"  # Local más reciente (se puede sincronizar)
    SYNC_CONFLICT = "both_changed"    # Hashes distintos, ninguno es claramente más nuevo
    SYNC_USB_MISSING = "usb_missing"  # USB conectada pero sin archivo (primera vez)
    SYNC_DISCONNECTED = "disconnected"  # USB no conectada

    def __init__(self, project_dir: str | None = None):
        self._volume_label: str = ""
        self._usb_filename: str = ""
        self._enabled: bool = False
        self._last_sync_hash: str = ""
        self._last_sync_time: str = ""
        self._project_dir = project_dir

        if project_dir:
            self._load_config(project_dir)

    def _load_config(self, project_path: str):
        data = USBSyncConfig.load(project_path)
        self._volume_label = data.get("volume_label", "")
        self._usb_filename = data.get("usb_filename", "")
        self._enabled = data.get("enabled", False)
        self._last_sync_hash = data.get("last_sync_hash", "")
        self._last_sync_time = data.get("last_sync_time", "")
        if self._volume_label:
            log.info("Configuración USB cargada: volumen='%s', archivo='%s', enabled=%s",
                     self._volume_label, self._usb_filename, self._enabled)

    def save_config(self, project_path: str):
        data = {
            "volume_label": self._volume_label,
            "usb_filename": self._usb_filename,
            "enabled": self._enabled,
            "last_sync_hash": self._last_sync_hash,
            "last_sync_time": self._last_sync_time,
        }
        USBSyncConfig.save(project_path, data)

    @property
    def volume_label(self) -> str:
        return self._volume_label

    @property
    def usb_filename(self) -> str:
        return self._usb_filename

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def last_sync_hash(self) -> str:
        return self._last_sync_hash

    @property
    def last_sync_time(self) -> str:
        return self._last_sync_time

    def is_configured(self) -> bool:
        return bool(self._enabled and self._volume_label and self._usb_filename)

    def configure(self, volume_label: str, usb_filename: str, enabled: bool = True):
        self._volume_label = volume_label
        self._usb_filename = usb_filename
        self._enabled = enabled
        log.info("USB configurada: volumen='%s', archivo='%s'", volume_label, usb_filename)

    def set_enabled(self, enabled: bool):
        self._enabled = enabled

    @staticmethod
    def detect_removable_drives() -> list[USBDrive]:
        return USBDetector.detect_removable_drives()

    def find_configured_drive(self) -> USBDrive | None:
        if not self._volume_label:
            return None
        for drive in self.detect_removable_drives():
            if drive.label.upper() == self._volume_label.upper():
                return drive
        return None

    @staticmethod
    def compute_file_hash(filepath: str) -> str:
        sha = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha.update(chunk)
        return sha.hexdigest()

    def sync_to_usb(self, source_path: str) -> str:
        """Copia el archivo .aura al USB configurado de forma atómica y verifica SHA-256."""
        if not self.is_configured():
            raise USBSyncError("Sincronización USB no configurada.")

        drive = self.find_configured_drive()
        if not drive:
            raise USBNotFoundError(f"USB '{self._volume_label}' no está conectada.")

        file_size = os.path.getsize(source_path)
        if drive.free_bytes < file_size * 2:
            raise USBSyncError(
                f"Espacio insuficiente en USB. Necesario: {file_size / 1024 / 1024:.1f} MB, Disponible: {drive.free_mb:.1f} MB"
            )

        dest_path = os.path.join(drive.path, self._usb_filename)
        temp_path = dest_path + ".tmp"

        try:
            shutil.copy2(source_path, temp_path)

            source_hash = self.compute_file_hash(source_path)
            temp_hash = self.compute_file_hash(temp_path)

            if source_hash != temp_hash:
                os.remove(temp_path)
                raise USBSyncError("Verificación de integridad fallida. Los hashes no coinciden.")

            if os.path.exists(dest_path):
                os.replace(temp_path, dest_path)
            else:
                os.rename(temp_path, dest_path)

            self._last_sync_hash = source_hash
            self._last_sync_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            log.info("Sincronización USB exitosa: %s → %s (hash: %s...)",
                     source_path, dest_path, source_hash[:12])
            return dest_path

        except (USBSyncError, USBNotFoundError):
            raise
        except Exception as e:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
            raise USBSyncError(f"Error durante sincronización USB: {e}") from e

    def get_usb_file_info(self) -> dict | None:
        drive = self.find_configured_drive()
        if not drive:
            return None

        dest_path = os.path.join(drive.path, self._usb_filename)
        if not os.path.exists(dest_path):
            return None

        return {
            "path": dest_path,
            "size_bytes": os.path.getsize(dest_path),
            "hash": self.compute_file_hash(dest_path),
            "drive_label": drive.label,
            "drive_path": drive.path,
            "drive_free_mb": drive.free_mb,
        }

    def is_usb_in_sync(self, local_path: str) -> bool:
        usb_info = self.get_usb_file_info()
        if not usb_info:
            return False
        local_hash = self.compute_file_hash(local_path)
        return local_hash == usb_info["hash"]

    def get_usb_file_mtime(self) -> float | None:
        drive = self.find_configured_drive()
        if not drive:
            return None
        dest_path = os.path.join(drive.path, self._usb_filename)
        if not os.path.exists(dest_path):
            return None
        return os.path.getmtime(dest_path)

    def compare_versions(self, local_path: str) -> dict:
        """Compara la versión local con la de la USB."""
        drive = self.find_configured_drive()
        if not drive:
            return {"status": self.SYNC_DISCONNECTED,
                    "local_mtime": None, "usb_mtime": None, "usb_path": None}

        dest_path = os.path.join(drive.path, self._usb_filename)
        if not os.path.exists(dest_path):
            return {"status": self.SYNC_USB_MISSING,
                    "local_mtime": None, "usb_mtime": None, "usb_path": dest_path}

        try:
            local_hash = self.compute_file_hash(local_path)
            usb_hash = self.compute_file_hash(dest_path)
        except OSError as e:
            log.warning("compare_versions: no se pudo calcular hash: %s", e)
            return {"status": self.SYNC_DISCONNECTED,
                    "local_mtime": None, "usb_mtime": None, "usb_path": None}

        local_mtime = os.path.getmtime(local_path)
        usb_mtime = os.path.getmtime(dest_path)

        if local_hash == usb_hash:
            status = self.SYNC_IN_SYNC
        else:
            delta = usb_mtime - local_mtime
            if delta > 5:
                status = self.SYNC_USB_NEWER
            elif delta < -5:
                status = self.SYNC_LOCAL_NEWER
            else:
                status = self.SYNC_CONFLICT

        return {
            "status": status,
            "local_mtime": local_mtime,
            "usb_mtime": usb_mtime,
            "usb_path": dest_path,
        }
