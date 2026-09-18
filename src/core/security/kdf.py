"""
kdf.py — Funciones de derivación de claves criptográficas (PBKDF2 + HMAC).
"""

import hmac
import hashlib
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256

from core.security.app_key import AppKeyManager

ITERATIONS = 600_000
KEY_LEN = 32  # 256 bits


def derive_key(password: str, salt: bytes) -> bytes:
    """
    Deriva una clave de 256 bits combinando contraseña + llave de app (V2).
    Proceso:
      1. PBKDF2(contraseña, salt) → clave del usuario
      2. HMAC-SHA256(clave_usuario, APP_KEY) → clave final
    """
    user_key = PBKDF2(
        password, salt,
        dkLen=KEY_LEN,
        count=ITERATIONS,
        hmac_hash_module=SHA256
    )
    return hmac.new(
        user_key,
        AppKeyManager.get_app_key(),
        hashlib.sha256
    ).digest()


def derive_key_v3(password: str, totp_secret: str, salt: bytes) -> bytes:
    """
    Deriva una clave de 256 bits combinando contraseña + secreto TOTP + llave de app (V3 3FA).
    Proceso:
      1. PBKDF2(password + "\x00" + totp_secret, salt) → clave combinada
      2. HMAC-SHA256(clave_combinada, APP_KEY) → clave final
    """
    combined_password = password + "\x00" + totp_secret
    user_key = PBKDF2(
        combined_password, salt,
        dkLen=KEY_LEN,
        count=ITERATIONS,
        hmac_hash_module=SHA256
    )
    return hmac.new(
        user_key,
        AppKeyManager.get_app_key(),
        hashlib.sha256
    ).digest()


def derive_key_legacy(password: str, salt: bytes) -> bytes:
    """Derivación v1 (sin llave de app) — para compatibilidad."""
    return PBKDF2(
        password, salt,
        dkLen=KEY_LEN,
        count=ITERATIONS,
        hmac_hash_module=SHA256
    )
