"""
detector.py — Detección nativa de unidades removibles USB en Windows y Linux.
"""

import os
import platform
import logging

log = logging.getLogger(__name__)


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


class USBDetector:
    """Detección multiplataforma optimizada de unidades USB."""

    @staticmethod
    def detect_removable_drives() -> list[USBDrive]:
        """Detecta todas las unidades removibles conectadas."""
        system = platform.system()
        if system == "Windows":
            return USBDetector._detect_windows()
        elif system == "Linux":
            return USBDetector._detect_linux()
        else:
            log.warning("Sistema operativo no soportado para detección USB: %s", system)
            return []

    @staticmethod
    def _detect_windows() -> list[USBDrive]:
        """Detecta unidades removibles en Windows usando la API nativa Win32 (sub-milisegundo)."""
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
