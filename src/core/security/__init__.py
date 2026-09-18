"""
src/core/security — Subpaquete modularizado para operaciones criptográficas y seguridad.
"""

from core.security.app_key import AppKeyManager
from core.security.kdf import (
    ITERATIONS, KEY_LEN,
    derive_key, derive_key_v3, derive_key_legacy
)
from core.security.crypto import (
    MAGIC_V2, MAGIC_V3, TOTP_SECRET_SLOT,
    is_v2_format, is_v3_format,
    encrypt_data, encrypt_data_v3, decrypt_data
)
from core.security.packager import (
    package_project, unpackage_project,
    migrate_v1_to_v2, migrate_v2_to_v3
)


class SecurityManager:
    """Fachada unificada para la capa de seguridad y cifrado de Aura Writer."""
    ITERATIONS = ITERATIONS
    KEY_LEN = KEY_LEN

    _MAGIC_V2 = MAGIC_V2
    _MAGIC_V3 = MAGIC_V3
    _TOTP_SECRET_SLOT = TOTP_SECRET_SLOT

    # App Key
    generate_random_key_hex = staticmethod(AppKeyManager.generate_random_key_hex)
    get_app_key = classmethod(lambda cls: AppKeyManager.get_app_key())
    get_app_key_hex = classmethod(lambda cls: AppKeyManager.get_app_key_hex())
    set_app_key_hex = classmethod(lambda cls, hex_key: AppKeyManager.set_app_key_hex(hex_key))

    # KDF
    derive_key = staticmethod(derive_key)
    derive_key_v3 = staticmethod(derive_key_v3)
    derive_key_legacy = staticmethod(derive_key_legacy)

    # Primitivas
    encrypt_data = staticmethod(encrypt_data)
    encrypt_data_v3 = staticmethod(encrypt_data_v3)
    decrypt_data = staticmethod(decrypt_data)
    is_v2_format = staticmethod(is_v2_format)
    is_v3_format = staticmethod(is_v3_format)

    # Empaquetado y migraciones
    package_project = staticmethod(package_project)
    unpackage_project = staticmethod(unpackage_project)
    migrate_v1_to_v2 = staticmethod(migrate_v1_to_v2)
    migrate_v2_to_v3 = staticmethod(migrate_v2_to_v3)


__all__ = [
    "SecurityManager",
    "AppKeyManager",
    "derive_key",
    "derive_key_v3",
    "derive_key_legacy",
    "encrypt_data",
    "encrypt_data_v3",
    "decrypt_data",
    "package_project",
    "unpackage_project",
    "migrate_v1_to_v2",
    "migrate_v2_to_v3",
    "is_v2_format",
    "is_v3_format",
]
