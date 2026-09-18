"""
security.py — Re-exportación para retrocompatibilidad hacia src/core/security.
"""

from core.security import (
    SecurityManager,
    AppKeyManager,
    derive_key,
    derive_key_v3,
    derive_key_legacy,
    encrypt_data,
    encrypt_data_v3,
    decrypt_data,
    package_project,
    unpackage_project,
    migrate_v1_to_v2,
    migrate_v2_to_v3,
    is_v2_format,
    is_v3_format,
)

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
