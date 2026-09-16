"""
Aura Writer — USB Sync Module
Detecta unidades USB removibles y sincroniza el archivo .aura cifrado.

Características:
  - Detección por nombre de volumen (independiente de letra de unidad)
  - Copia atómica (escribe .tmp → renombra) para evitar corrupción
  - Verificación SHA-256 post-copia
  - Manejo silencioso cuando la USB no está conectada
"""

import os
import json
import shutil
import hashlib
import logging
import platform
import subprocess
import tempfile

log = logging.getLogger(__name__)


class USBNotFoundError(Exception):
    """La USB configurada no está conectada."""
    pass


class USBSyncError(Exception):
    """Error durante la sincronización con la USB."""
    pass


class USBDrive:
    """Representa una unidad removible detectada."""

    def __init__(self, path: str, label: str, free_bytes: int = 0):
        self.path = path          # Ej: "E:\\"
        self.label = label        # Ej: "AURA_USB"
        self.free_bytes = free_bytes

    @property
    def free_mb(self) -> float:
        return self.free_bytes / (1024 * 1024)

    @property
    def free_gb(self) -> float:
        return self.free_bytes / (1024 * 1024 * 1024)

    def __repr__(self):
        return f"USBDrive({self.path}, '{self.label}', {self.free_mb:.1f} MB libre)"


class USBSync:
    """
    Gestiona la sincronización del archivo .aura entre disco local y USB.

    Configuración persistente:
      - volume_label: nombre del volumen USB (para detectarla sin importar la letra)
      - usb_filename: nombre del archivo .aura en la USB
      - enabled: si la sincronización está activa
    """

    CONFIG_FILENAME = ".aura_usb_config.json"

    def __init__(self, project_dir: str | None = None):
        self._volume_label: str = ""
        self._usb_filename: str = ""
        self._enabled: bool = False
        self._last_sync_hash: str = ""
        self._last_sync_time: str = ""
        self._project_dir = project_dir

        # Cargar configuración si existe
        if project_dir:
            self._load_config(project_dir)

    # ------------------------------------------------------------------
    # Configuración persistente
    # ------------------------------------------------------------------

    def _config_path(self, project_dir: str) -> str:
        """Ruta del archivo de configuración USB (junto al .aura local)."""
        return os.path.join(os.path.dirname(project_dir), self.CONFIG_FILENAME)

    def _load_config(self, project_path: str):
        """Carga la configuración USB desde disco."""
        cfg_path = self._config_path(project_path)
        if not os.path.exists(cfg_path):
            return
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._volume_label = data.get("volume_label", "")
            self._usb_filename = data.get("usb_filename", "")
            self._enabled = data.get("enabled", False)
            self._last_sync_hash = data.get("last_sync_hash", "")
            self._last_sync_time = data.get("last_sync_time", "")
            log.info("Configuración USB cargada: volumen='%s', archivo='%s', enabled=%s",
                     self._volume_label, self._usb_filename, self._enabled)
        except Exception as e:
            log.warning("No se pudo cargar configuración USB: %s", e)

    def save_config(self, project_path: str):
        """Persiste la configuración USB a disco."""
        cfg_path = self._config_path(project_path)
        data = {
            "volume_label": self._volume_label,
            "usb_filename": self._usb_filename,
            "enabled": self._enabled,
            "last_sync_hash": self._last_sync_hash,
            "last_sync_time": self._last_sync_time,
        }
        try:
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log.warning("No se pudo guardar configuración USB: %s", e)

    # ------------------------------------------------------------------
    # Propiedades
    # ------------------------------------------------------------------

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
        """Retorna True si hay una USB configurada y la sincronización está activa."""
        return bool(self._enabled and self._volume_label and self._usb_filename)

    # ------------------------------------------------------------------
    # Configuración
    # ------------------------------------------------------------------

    def configure(self, volume_label: str, usb_filename: str, enabled: bool = True):
        """Configura la USB destino."""
        self._volume_label = volume_label
        self._usb_filename = usb_filename
        self._enabled = enabled
        log.info("USB configurada: volumen='%s', archivo='%s'", volume_label, usb_filename)

    def set_enabled(self, enabled: bool):
        self._enabled = enabled

    # ------------------------------------------------------------------
    # Detección de unidades removibles
    # ------------------------------------------------------------------

    @staticmethod
    def detect_removable_drives() -> list[USBDrive]:
        """Detecta todas las unidades removibles conectadas."""
        system = platform.system()
        if system == "Windows":
            return USBSync._detect_windows()
        elif system == "Linux":
            return USBSync._detect_linux()
        else:
            log.warning("Sistema operativo no soportado para detección USB: %s", system)
            return []

    @staticmethod
    def _detect_windows() -> list[USBDrive]:
        """Detecta unidades removibles en Windows usando la API nativa Win32 (sub-milisegundo, sin congelamientos)."""
        drives = []
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            bitmask = kernel32.GetLogicalDrives()
            for letter_idx in range(26):
                if bitmask & (1 << letter_idx):
                    drive_path = chr(65 + letter_idx) + ":\\"
                    # 2 = DRIVE_REMOVABLE
                    if kernel32.GetDriveTypeW(drive_path) == 2:
                        volume_name_buf = ctypes.create_unicode_buffer(261)
                        kernel32.GetVolumeInformationW(
                            drive_path, volume_name_buf, 260, None, None, None, None, 0
                        )
                        free_bytes = ctypes.c_ulonglong(0)
                        kernel32.GetDiskFreeSpaceExW(
                            drive_path, ctypes.byref(free_bytes), None, None
                        )
                        drives.append(USBDrive(
                            path=drive_path,
                            label=volume_name_buf.value or f"Unidad ({chr(65 + letter_idx)}:)",
                            free_bytes=int(free_bytes.value)
                        ))
        except Exception as e:
            log.warning("Error en detección nativa Win32 USB: %s", e)

        return drives

    @staticmethod
    def _detect_linux() -> list[USBDrive]:
        """Detecta unidades removibles en Linux desde /media o /run/media."""
        drives = []
        media_dirs = []

        # Buscar en las ubicaciones estándar de montaje
        user = os.environ.get("USER", "")
        for base in [f"/media/{user}", f"/run/media/{user}", "/media", "/mnt"]:
            if os.path.isdir(base):
                media_dirs.append(base)

        for media_base in media_dirs:
            try:
                for entry in os.listdir(media_base):
                    mount_path = os.path.join(media_base, entry)
                    if os.path.ismount(mount_path):
                        try:
                            stat = os.statvfs(mount_path)
                            free = stat.f_bavail * stat.f_bsize
                        except OSError:
                            free = 0
                        drives.append(USBDrive(
                            path=mount_path,
                            label=entry,
                            free_bytes=free
                        ))
            except PermissionError:
                continue

        return drives

    def find_configured_drive(self) -> USBDrive | None:
        """Busca la USB configurada entre las unidades conectadas."""
        if not self._volume_label:
            return None
        for drive in self.detect_removable_drives():
            if drive.label.upper() == self._volume_label.upper():
                return drive
        return None

    # ------------------------------------------------------------------
    # Sincronización
    # ------------------------------------------------------------------

    @staticmethod
    def compute_file_hash(filepath: str) -> str:
        """Calcula el SHA-256 de un archivo."""
        sha = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha.update(chunk)
        return sha.hexdigest()

    def sync_to_usb(self, source_path: str) -> str:
        """
        Copia el archivo .aura al USB configurado de forma atómica.

        Returns:
            Ruta del archivo en la USB.

        Raises:
            USBNotFoundError: USB no conectada.
            USBSyncError: Error durante la copia o verificación.
        """
        if not self.is_configured():
            raise USBSyncError("Sincronización USB no configurada.")

        drive = self.find_configured_drive()
        if not drive:
            raise USBNotFoundError(
                f"USB '{self._volume_label}' no está conectada."
            )

        # Verificar que la USB tenga espacio suficiente
        file_size = os.path.getsize(source_path)
        if drive.free_bytes < file_size * 2:  # Margen de seguridad 2x
            raise USBSyncError(
                f"Espacio insuficiente en USB. "
                f"Necesario: {file_size / 1024 / 1024:.1f} MB, "
                f"Disponible: {drive.free_mb:.1f} MB"
            )

        dest_path = os.path.join(drive.path, self._usb_filename)
        temp_path = dest_path + ".tmp"

        try:
            # 1. Copiar a archivo temporal
            shutil.copy2(source_path, temp_path)

            # 2. Verificar integridad
            source_hash = self.compute_file_hash(source_path)
            temp_hash = self.compute_file_hash(temp_path)

            if source_hash != temp_hash:
                os.remove(temp_path)
                raise USBSyncError("Verificación de integridad fallida. Los hashes no coinciden.")

            # 3. Renombrar atómicamente (reemplaza el archivo anterior)
            if os.path.exists(dest_path):
                # En Windows, os.rename no reemplaza — usar os.replace
                os.replace(temp_path, dest_path)
            else:
                os.rename(temp_path, dest_path)

            # 4. Actualizar metadata de sincronización
            from datetime import datetime
            self._last_sync_hash = source_hash
            self._last_sync_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            log.info("Sincronización USB exitosa: %s → %s (hash: %s...)",
                     source_path, dest_path, source_hash[:12])

            return dest_path

        except (USBSyncError, USBNotFoundError):
            raise
        except Exception as e:
            # Limpiar archivo temporal si quedó
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
            raise USBSyncError(f"Error durante sincronización USB: {e}") from e

    def get_usb_file_info(self) -> dict | None:
        """
        Obtiene información del archivo .aura en la USB.
        Retorna None si la USB no está conectada o el archivo no existe.
        """
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
        """Verifica si el archivo en USB está sincronizado con el local."""
        usb_info = self.get_usb_file_info()
        if not usb_info:
            return False
        local_hash = self.compute_file_hash(local_path)
        return local_hash == usb_info["hash"]

    def get_usb_file_mtime(self) -> float | None:
        """
        Retorna el mtime (timestamp Unix) del archivo .aura en la USB,
        o None si la USB no está conectada o el archivo no existe.
        """
        drive = self.find_configured_drive()
        if not drive:
            return None
        dest_path = os.path.join(drive.path, self._usb_filename)
        if not os.path.exists(dest_path):
            return None
        return os.path.getmtime(dest_path)

    # Constantes para el resultado de compare_versions
    SYNC_IN_SYNC     = "in_sync"       # Hashes iguales
    SYNC_USB_NEWER   = "usb_newer"     # USB tiene mtime más reciente (posible trabajo en otro equipo)
    SYNC_LOCAL_NEWER = "local_newer"   # Local más reciente (se puede sincronizar)
    SYNC_CONFLICT    = "both_changed"  # Hashes distintos, ninguno es claramente más nuevo
    SYNC_USB_MISSING = "usb_missing"   # USB conectada pero sin archivo (primera vez)
    SYNC_DISCONNECTED = "disconnected" # USB no conectada

    def compare_versions(self, local_path: str) -> dict:
        """
        Compara la versión local con la de la USB.

        Retorna un dict con:
            status  : una de las constantes SYNC_*
            local_mtime : float | None
            usb_mtime   : float | None
            usb_path    : str | None
        """
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
            usb_hash   = self.compute_file_hash(dest_path)
        except OSError as e:
            log.warning("compare_versions: no se pudo calcular hash: %s", e)
            return {"status": self.SYNC_DISCONNECTED,
                    "local_mtime": None, "usb_mtime": None, "usb_path": None}

        local_mtime = os.path.getmtime(local_path)
        usb_mtime   = os.path.getmtime(dest_path)

        if local_hash == usb_hash:
            status = self.SYNC_IN_SYNC
        else:
            # Tolerancia de 5 segundos para evitar falsos conflictos por timestamps del SO
            delta = usb_mtime - local_mtime
            if delta > 5:
                status = self.SYNC_USB_NEWER
            elif delta < -5:
                status = self.SYNC_LOCAL_NEWER
            else:
                # Timestamps casi iguales pero hashes distintos → conflicto real
                status = self.SYNC_CONFLICT

        return {
            "status": status,
            "local_mtime": local_mtime,
            "usb_mtime": usb_mtime,
            "usb_path": dest_path,
        }

