"""
crypto.py — Primitivas de cifrado y descifrado AES-256-GCM para V1, V2 y V3.
"""

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

from core.security.kdf import derive_key, derive_key_v3, derive_key_legacy

MAGIC_V2 = b"AURA\x00\x02"  # 6 bytes: "AURA" + versión 2
MAGIC_V3 = b"AURA\x00\x03"  # 6 bytes: "AURA" + versión 3 (3FA - TOTP en KDF)
TOTP_SECRET_SLOT = 64


def is_v2_format(encrypted_blob: bytes) -> bool:
    return encrypted_blob[:6] == MAGIC_V2


def is_v3_format(encrypted_blob: bytes) -> bool:
    return encrypted_blob[:6] == MAGIC_V3


def encrypt_data(password: str, data: bytes) -> bytes:
    """Cifra datos usando AES-256-GCM con llave maestra (formato V2)."""
    salt = get_random_bytes(16)
    key = derive_key(password, salt)

    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(data)
    return MAGIC_V2 + salt + cipher.nonce + tag + ciphertext


def encrypt_data_v3(password: str, totp_secret: str, data: bytes) -> bytes:
    """Cifra datos con 3FA en dos capas AES-256-GCM (formato V3)."""
    if not totp_secret:
        raise ValueError("Se requiere un secreto TOTP para cifrar en formato V3.")

    # Capa interior
    inner_salt = get_random_bytes(16)
    inner_key = derive_key_v3(password, totp_secret, inner_salt)
    inner_cipher = AES.new(inner_key, AES.MODE_GCM)
    inner_ct, inner_tag = inner_cipher.encrypt_and_digest(data)
    inner_blob = inner_salt + inner_cipher.nonce + inner_tag + inner_ct

    # Capa exterior
    secret_bytes = totp_secret.encode("utf-8")
    if len(secret_bytes) > TOTP_SECRET_SLOT:
        raise ValueError(f"El secreto TOTP es demasiado largo ({len(secret_bytes)} bytes). Máximo: {TOTP_SECRET_SLOT} bytes.")

    padded_secret = secret_bytes.ljust(TOTP_SECRET_SLOT, b"\x00")
    outer_plaintext = padded_secret + inner_blob

    outer_salt = get_random_bytes(16)
    outer_key = derive_key(password, outer_salt)
    outer_cipher = AES.new(outer_key, AES.MODE_GCM)
    outer_ct, outer_tag = outer_cipher.encrypt_and_digest(outer_plaintext)

    return MAGIC_V3 + outer_salt + outer_cipher.nonce + outer_tag + outer_ct


def decrypt_data(password: str, encrypted_blob: bytes, totp_code: str = "") -> bytes:
    """Descifra un bloque binario detectando automáticamente V1, V2 o V3."""
    if encrypted_blob[:6] == MAGIC_V3:
        return _decrypt_v3(password, totp_code, encrypted_blob)
    elif encrypted_blob[:6] == MAGIC_V2:
        return _decrypt_v2(password, encrypted_blob)
    else:
        return _decrypt_v1(password, encrypted_blob)


def _decrypt_v2(password: str, encrypted_blob: bytes) -> bytes:
    if len(encrypted_blob) < 54:
        raise ValueError("Datos cifrados v2 inválidos o corruptos.")

    offset = 6
    salt = encrypted_blob[offset:offset + 16]
    nonce = encrypted_blob[offset + 16:offset + 32]
    tag = encrypted_blob[offset + 32:offset + 48]
    ciphertext = encrypted_blob[offset + 48:]

    key = derive_key(password, salt)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)

    try:
        return cipher.decrypt_and_verify(ciphertext, tag)
    except ValueError:
        raise ValueError("Contraseña incorrecta o archivo corrupto. Asegúrate de usar la llave maestra correcta.")


def _decrypt_v1(password: str, encrypted_blob: bytes) -> bytes:
    if len(encrypted_blob) < 48:
        raise ValueError("Datos cifrados inválidos o corruptos.")

    salt = encrypted_blob[:16]
    nonce = encrypted_blob[16:32]
    tag = encrypted_blob[32:48]
    ciphertext = encrypted_blob[48:]

    key = derive_key_legacy(password, salt)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag)


def _decrypt_v3(password: str, totp_code: str, encrypted_blob: bytes) -> bytes:
    if len(encrypted_blob) < 54:
        raise ValueError("Datos V3 inválidos o corruptos.")

    offset = 6
    outer_salt = encrypted_blob[offset:offset + 16]
    outer_nonce = encrypted_blob[offset + 16:offset + 32]
    outer_tag = encrypted_blob[offset + 32:offset + 48]
    outer_ct = encrypted_blob[offset + 48:]

    outer_key = derive_key(password, outer_salt)
    outer_cipher = AES.new(outer_key, AES.MODE_GCM, nonce=outer_nonce)
    try:
        outer_plaintext = outer_cipher.decrypt_and_verify(outer_ct, outer_tag)
    except ValueError:
        raise ValueError("Contraseña incorrecta o archivo V3 corrupto. Asegúrate de usar la llave maestra correcta.")

    secret_bytes = outer_plaintext[:TOTP_SECRET_SLOT].rstrip(b"\x00")
    totp_secret = secret_bytes.decode("utf-8")
    inner_blob = outer_plaintext[TOTP_SECRET_SLOT:]

    if not totp_secret:
        raise ValueError("El archivo V3 no contiene un secreto TOTP válido.")

    is_recovery_code = (
        len(totp_code.replace("-", "").replace(" ", "")) == 8
        and "-" in totp_code
    )

    if not is_recovery_code:
        from core.totp_manager import TOTPManager
        if not TOTPManager.verify_code(totp_secret, totp_code):
            raise ValueError("Código TOTP incorrecto. Verifica tu app de autenticación o usa un código de recuperación.")

    if len(inner_blob) < 48:
        raise ValueError("Blob interior V3 inválido o corrupto.")

    inner_salt = inner_blob[:16]
    inner_nonce = inner_blob[16:32]
    inner_tag = inner_blob[32:48]
    inner_ct = inner_blob[48:]

    inner_key = derive_key_v3(password, totp_secret, inner_salt)
    inner_cipher = AES.new(inner_key, AES.MODE_GCM, nonce=inner_nonce)
    try:
        return inner_cipher.decrypt_and_verify(inner_ct, inner_tag)
    except ValueError:
        raise ValueError("Error al descifrar la capa interior V3. El archivo puede estar corrupto o los factores de cifrado no coinciden.")
