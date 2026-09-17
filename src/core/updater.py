# ─────────────────────────────────────────────────────────────────────────────
# Aura Writer — Actualizador Automático (Core)
# Consulta la API de GitHub Releases para detectar nuevas versiones.
# ─────────────────────────────────────────────────────────────────────────────
import os
import re
import json
import logging
import tempfile
import urllib.request
import urllib.error
from typing import Tuple
from PyQt6.QtCore import pyqtSignal, QThread

from version import __version__, APP_URL

log = logging.getLogger(__name__)

# URL de la API de GitHub para la última versión
GITHUB_REPO_API = "https://api.github.com/repos/edhepe-project/Aura_Writer/releases/latest"


def parse_version(ver_str: str) -> Tuple[int, ...]:
    """Convierte una cadena de versión '1.0.0' o 'v1.2.3' en una tupla de enteros (1, 2, 3)."""
    clean = re.sub(r"^[^\d]*", "", ver_str.strip())
    # Extraer los números
    parts = []
    for chunk in clean.split("."):
        m = re.match(r"^(\d+)", chunk)
        if m:
            parts.append(int(m.group(1)))
        else:
            break
    return tuple(parts) if parts else (0,)


def is_newer_version(latest_version: str, current_version: str = __version__) -> bool:
    """Retorna True si latest_version es estrictamente más reciente que current_version."""
    v_latest = parse_version(latest_version)
    v_current = parse_version(current_version)
    # Rellenar con ceros si tienen longitudes distintas
    max_len = max(len(v_latest), len(v_current))
    v_latest = v_latest + (0,) * (max_len - len(v_latest))
    v_current = v_current + (0,) * (max_len - len(v_current))
    return v_latest > v_current


class UpdateCheckWorker(QThread):
    """Hilo para consultar la API de GitHub sin congelar la interfaz gráfica."""
    check_finished = pyqtSignal(bool, dict, str)  # (has_update, release_info, error_msg)

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        req = urllib.request.Request(
            GITHUB_REPO_API,
            headers={
                "User-Agent": f"AuraWriter/{__version__}",
                "Accept": "application/vnd.github.v3+json"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    tag_name = data.get("tag_name", "")
                    body = data.get("body", "")
                    html_url = data.get("html_url", APP_URL)
                    assets = data.get("assets", [])

                    # Buscar instalador exe en los assets
                    installer_url = None
                    installer_name = None
                    installer_size = 0
                    for asset in assets:
                        name = asset.get("name", "")
                        if name.lower().endswith(".exe"):
                            installer_url = asset.get("browser_download_url")
                            installer_name = name
                            installer_size = asset.get("size", 0)
                            break

                    has_update = is_newer_version(tag_name, __version__)
                    release_info = {
                        "tag_name": tag_name,
                        "version": tag_name.lstrip("vV"),
                        "notes": body,
                        "url": html_url,
                        "installer_url": installer_url,
                        "installer_name": installer_name,
                        "installer_size": installer_size,
                        "published_at": data.get("published_at", "")
                    }
                    self.check_finished.emit(has_update, release_info, "")
                    return
                else:
                    self.check_finished.emit(False, {}, f"HTTP {response.status}")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # Si no hay releases creadas en GitHub, significa que la versión instalada es la actual
                self.check_finished.emit(False, {}, "")
            else:
                self.check_finished.emit(False, {}, f"Error del servidor ({e.code}): {e.reason}")
        except urllib.error.URLError as e:
            self.check_finished.emit(False, {}, f"No se pudo conectar a Internet:\n{e.reason}")
        except Exception as e:
            log.exception("Error checking updates")
            self.check_finished.emit(False, {}, str(e))


class DownloadWorker(QThread):
    """Hilo para descargar el instalador con notificación de progreso."""
    progress = pyqtSignal(int, int)  # (bytes_descargados, total_bytes)
    finished = pyqtSignal(bool, str)  # (success, file_path_o_error)

    def __init__(self, download_url: str, file_name: str, parent=None):
        super().__init__(parent)
        self.download_url = download_url
        self.file_name = file_name
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            dest_dir = tempfile.gettempdir()
            dest_path = os.path.join(dest_dir, self.file_name)

            req = urllib.request.Request(
                self.download_url,
                headers={"User-Agent": f"AuraWriter/{__version__}"}
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                total_size = int(response.headers.get("content-length", 0))
                downloaded = 0
                block_size = 64 * 1024  # 64 KB

                with open(dest_path, "wb") as f:
                    while True:
                        if self._is_cancelled:
                            self.finished.emit(False, "Descarga cancelada por el usuario.")
                            return
                        buffer = response.read(block_size)
                        if not buffer:
                            break
                        downloaded += len(buffer)
                        f.write(buffer)
                        self.progress.emit(downloaded, total_size)

            self.finished.emit(True, dest_path)

        except Exception as e:
            log.exception("Error downloading update")
            self.finished.emit(False, f"Error al descargar: {str(e)}")
