"""
ConfigManager — Administrador centralizado y multiplataforma de configuración y preferencias.
Soporta:
  1. Modo Portátil: si existe 'aura_prefs.json' o 'aura_portable.marker' en la raíz.
  2. Modo Estándar del Sistema Operativo:
     - Windows: %APPDATA%/AuraWriter/aura_prefs.json
     - Linux/macOS: ~/.config/aura_writer/aura_prefs.json
"""

import os
import json
import sys
import logging

log = logging.getLogger(__name__)


class ConfigManager:
    _cached_prefs: dict | None = None

    @classmethod
    def get_prefs_path(cls) -> str:
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        local_prefs = os.path.join(root_dir, "aura_prefs.json")
        portable_marker = os.path.join(root_dir, "aura_portable.marker")

        # Si existe marcador portable o ya existe archivo local, priorizar modo portátil
        if os.path.exists(portable_marker) or os.path.exists(local_prefs):
            return local_prefs

        # Ubicación estándar según sistema operativo
        if sys.platform == "win32":
            appdata = os.environ.get("APPDATA")
            if appdata:
                config_dir = os.path.join(appdata, "AuraWriter")
            else:
                config_dir = os.path.expanduser("~/.aurawriter")
        else:
            xdg_config = os.environ.get("XDG_CONFIG_HOME")
            if xdg_config:
                config_dir = os.path.join(xdg_config, "aura_writer")
            else:
                config_dir = os.path.expanduser("~/.config/aura_writer")

        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "aura_prefs.json")

    @classmethod
    def load_prefs(cls) -> dict:
        prefs_path = cls.get_prefs_path()
        if os.path.exists(prefs_path):
            try:
                with open(prefs_path, "r", encoding="utf-8") as f:
                    cls._cached_prefs = json.load(f)
                    return cls._cached_prefs
            except Exception as e:
                log.warning("No se pudo leer el archivo de preferencias: %s", e)
        cls._cached_prefs = {}
        return cls._cached_prefs

    @classmethod
    def get(cls, key: str, default=None):
        if cls._cached_prefs is None:
            cls.load_prefs()
        return cls._cached_prefs.get(key, default)

    @classmethod
    def set(cls, key: str, value) -> bool:
        if cls._cached_prefs is None:
            cls.load_prefs()
        cls._cached_prefs[key] = value
        prefs_path = cls.get_prefs_path()
        try:
            os.makedirs(os.path.dirname(os.path.abspath(prefs_path)), exist_ok=True)
            with open(prefs_path, "w", encoding="utf-8") as f:
                json.dump(cls._cached_prefs, f, indent=2)
            return True
        except Exception as e:
            log.error("Error al guardar preferencia %s: %s", key, e)
            return False
