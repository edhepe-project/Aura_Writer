"""
app_key.py — Gestión y persistencia de la Llave Maestra de Aplicación.
"""

import logging
from Crypto.Random import get_random_bytes

log = logging.getLogger(__name__)


class AppKeyManager:
    """Manejo centralizado de la Llave Maestra (App Key) de 256 bits."""
    _cached_app_key: bytes | None = None

    @staticmethod
    def generate_random_key_hex() -> str:
        """Genera una llave aleatoria criptográficamente segura de 256 bits (64 hex)."""
        return get_random_bytes(32).hex()

    @classmethod
    def get_app_key(cls) -> bytes:
        """
        Obtiene la llave maestra activa.
        Si es una instalación nueva sin llave configurada, genera automáticamente
        una llave única de 256 bits y la guarda en las preferencias locales.
        """
        if cls._cached_app_key is not None:
            return cls._cached_app_key

        from core.config_manager import ConfigManager
        try:
            custom_key = ConfigManager.get("app_key")
            if custom_key and isinstance(custom_key, str) and len(custom_key.strip()) == 64:
                cls._cached_app_key = bytes.fromhex(custom_key.strip())
                return cls._cached_app_key
        except Exception as e:
            log.warning("No se pudo leer app_key de preferencias: %s", e)

        new_key_hex = cls.generate_random_key_hex()
        cls.set_app_key_hex(new_key_hex)
        log.info("Llave maestra única generada y guardada para esta instalación.")
        return cls._cached_app_key

    @classmethod
    def get_app_key_hex(cls) -> str:
        """Retorna la llave activa como string hexadecimal de 64 caracteres."""
        return cls.get_app_key().hex()

    @classmethod
    def set_app_key_hex(cls, hex_key: str) -> bool:
        """
        Guarda una nueva llave maestra en las preferencias locales.
        Valida que sea una cadena hexadecimal de 64 caracteres (256 bits).
        """
        clean_key = hex_key.strip().lower()
        if len(clean_key) != 64:
            raise ValueError("La llave maestra debe tener exactamente 64 caracteres hexadecimales (256 bits).")

        try:
            key_bytes = bytes.fromhex(clean_key)
        except ValueError as e:
            raise ValueError("La llave contiene caracteres no hexadecimales válidos.") from e

        cls._cached_app_key = key_bytes

        from core.config_manager import ConfigManager
        success = ConfigManager.set("app_key", clean_key)
        if success:
            log.info("Nueva llave maestra de aplicación guardada correctamente.")
            return True
        else:
            log.error("Error al guardar la llave maestra en preferencias.")
            return False
