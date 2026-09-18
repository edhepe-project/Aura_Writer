"""
packager.py — Empaquetado y desempaquetado de proyectos .aura (ZIP cifrado atómico).
"""

import os
import io
import zipfile
import logging
from core.security.crypto import (
    encrypt_data, encrypt_data_v3, decrypt_data,
    is_v2_format, is_v3_format, _decrypt_v1
)

log = logging.getLogger(__name__)


def package_project(password: str, source_dir: str, output_file: str, totp_secret: str = ""):
    """Comprime un directorio y lo guarda cifrado atómicamente."""
    memory_zip = io.BytesIO()
    with zipfile.ZipFile(memory_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(source_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, source_dir)
                zf.write(full_path, rel_path)

    zip_data = memory_zip.getvalue()
    if totp_secret:
        encrypted_blob = encrypt_data_v3(password, totp_secret, zip_data)
        log.debug("Proyecto empaquetado en formato V3 (3FA).")
    else:
        encrypted_blob = encrypt_data(password, zip_data)
        log.debug("Proyecto empaquetado en formato V2.")

    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    temp_output = output_file + ".tmp"
    with open(temp_output, 'wb') as f:
        f.write(encrypted_blob)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp_output, output_file)


def unpackage_project(password: str, encrypted_file: str, target_dir: str, totp_code: str = ""):
    """Descifra un archivo .aura y lo extrae en el directorio destino."""
    with open(encrypted_file, 'rb') as f:
        encrypted_blob = f.read()

    decrypted_zip_data = decrypt_data(password, encrypted_blob, totp_code=totp_code)
    memory_zip = io.BytesIO(decrypted_zip_data)

    with zipfile.ZipFile(memory_zip, 'r') as zf:
        zf.extractall(target_dir)


def migrate_v1_to_v2(password: str, file_path: str) -> bool:
    """Migra un archivo .aura de V1 (sin llave) a V2 (con llave maestra)."""
    with open(file_path, 'rb') as f:
        blob = f.read()

    if is_v2_format(blob) or is_v3_format(blob):
        log.info("El archivo ya está en formato V2 o V3. No se requiere migración V1→V2.")
        return False

    try:
        plaintext = _decrypt_v1(password, blob)
    except ValueError as e:
        raise ValueError(f"No se pudo migrar V1→V2: {e}") from e

    new_blob = encrypt_data(password, plaintext)
    with open(file_path, 'wb') as f:
        f.write(new_blob)

    log.info("Archivo migrado exitosamente a formato V2: %s", file_path)
    return True


def migrate_v2_to_v3(password: str, totp_secret: str, file_path: str) -> bool:
    """Migra un archivo .aura de V2 a V3 (3FA — TOTP integrado en KDF)."""
    with open(file_path, 'rb') as f:
        blob = f.read()

    if is_v3_format(blob):
        log.info("El archivo ya está en formato V3. No se requiere migración.")
        return False

    try:
        plaintext = decrypt_data(password, blob)
    except ValueError as e:
        raise ValueError(f"No se pudo migrar V2→V3: {e}") from e

    new_blob = encrypt_data_v3(password, totp_secret, plaintext)

    temp_path = file_path + ".tmp"
    with open(temp_path, 'wb') as f:
        f.write(new_blob)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp_path, file_path)

    log.info("Archivo migrado exitosamente a formato V3 (3FA): %s", file_path)
    return True
