"""
config.py — Manejo de configuración persistente para la sincronización USB.
"""

import os
import json
import logging

log = logging.getLogger(__name__)

CONFIG_FILENAME = ".aura_usb_config.json"


class USBSyncConfig:
    """Gestiona la lectura y escritura del archivo de configuración USB junto al proyecto."""

    @staticmethod
    def config_path(project_dir: str) -> str:
        return os.path.join(os.path.dirname(project_dir), CONFIG_FILENAME)

    @staticmethod
    def load(project_path: str) -> dict:
        cfg_path = USBSyncConfig.config_path(project_path)
        if not os.path.exists(cfg_path):
            return {}
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log.warning("No se pudo cargar configuración USB: %s", e)
            return {}

    @staticmethod
    def save(project_path: str, data: dict):
        cfg_path = USBSyncConfig.config_path(project_path)
        try:
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log.warning("No se pudo guardar configuración USB: %s", e)
