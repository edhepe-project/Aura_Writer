"""
Aura Writer — Security Module
Cifrado AES-256-GCM con llave maestra embebida.

Versión 2 del formato .aura:
  - Header mágico: AURA\x00\x02 (6 bytes)
  - La clave se deriva combinando la contraseña del usuario + llave de aplicación
  - Sin la llave de aplicación (embebida en este código), el archivo es inútil
  - Compatible hacia atrás con archivos v1 (sin header)

IMPORTANTE: Guarda copias de este programa (con esta llave) en discos seguros.
Si pierdes el programa Y el código fuente, no podrás recuperar tus archivos.
"""

import os
import io
import json
import hmac
import hashlib
import zipfile
import logging
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes

log = logging.getLogger(__name__)

# Ruta del archivo de preferencias
_PREFS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "..", "aura_prefs.json")


class SecurityManager:
    ITERATIONS = 600000
    KEY_LEN = 32  # 256 bits

    _cached_app_key: bytes | None = None

    # ── Header mágico para identificar versión del formato ──────────
    _MAGIC_V2 = b"AURA\x00\x02"  # 6 bytes: "AURA" + versión 2

    # ------------------------------------------------------------------
    # Gestión de Llave Maestra (Generación Automática / Portable)
    # ------------------------------------------------------------------

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

        try:
            prefs_path = os.path.normpath(_PREFS_FILE)
            if os.path.exists(prefs_path):
                with open(prefs_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                custom_key = data.get("app_key")
                if custom_key and isinstance(custom_key, str) and len(custom_key.strip()) == 64:
                    cls._cached_app_key = bytes.fromhex(custom_key.strip())
                    return cls._cached_app_key
        except Exception as e:
            log.warning("No se pudo leer app_key de preferencias: %s", e)

        # ── Generar automáticamente para esta nueva instalación ────────
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

        # Persistir en aura_prefs.json
        try:
            prefs_path = os.path.normpath(_PREFS_FILE)
            data = {}
            if os.path.exists(prefs_path):
                with open(prefs_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            data["app_key"] = clean_key
            with open(prefs_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            log.info("Nueva llave maestra de aplicación guardada correctamente.")
            return True
        except Exception as e:
            log.error("Error al guardar la llave maestra en preferencias: %s", e)
            return False

    # ------------------------------------------------------------------
    # Derivación de clave
    # ------------------------------------------------------------------

    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        """
        Deriva una clave de 256 bits combinando contraseña + llave de app.
        
        Proceso:
          1. PBKDF2(contraseña, salt) → clave del usuario
          2. HMAC-SHA256(clave_usuario, APP_KEY) → clave final
        
        Sin la APP_KEY, la clave final es imposible de computar.
        """
        user_key = PBKDF2(
            password, salt,
            dkLen=SecurityManager.KEY_LEN,
            count=SecurityManager.ITERATIONS,
            hmac_hash_module=SHA256
        )
        # Combinar con la llave de aplicación activa
        combined = hmac.new(
            user_key,
            SecurityManager.get_app_key(),
            hashlib.sha256
        ).digest()
        return combined

    @staticmethod
    def derive_key_legacy(password: str, salt: bytes) -> bytes:
        """Derivación v1 (sin llave de app) — para compatibilidad."""
        return PBKDF2(
            password, salt,
            dkLen=SecurityManager.KEY_LEN,
            count=SecurityManager.ITERATIONS,
            hmac_hash_module=SHA256
        )

    # ------------------------------------------------------------------
    # Cifrado / Descifrado (V2 con llave maestra)
    # ------------------------------------------------------------------

    @staticmethod
    def encrypt_data(password: str, data: bytes) -> bytes:
        """
        Cifra datos usando AES-256-GCM con llave maestra (formato v2).
        
        Formato del blob:
          MAGIC_V2 (6) + salt (16) + nonce (16) + tag (16) + ciphertext
        """
        salt = get_random_bytes(16)
        key = SecurityManager.derive_key(password, salt)

        cipher = AES.new(key, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(data)

        # Header mágico v2 + datos cifrados
        return SecurityManager._MAGIC_V2 + salt + cipher.nonce + tag + ciphertext

    @staticmethod
    def decrypt_data(password: str, encrypted_blob: bytes) -> bytes:
        """
        Descifra un bloque binario. Detecta automáticamente v1 o v2.
        
        Raises:
            ValueError: Contraseña incorrecta, archivo corrupto, o falta la llave.
        """
        # ── Detectar versión del formato ──
        if encrypted_blob[:6] == SecurityManager._MAGIC_V2:
            return SecurityManager._decrypt_v2(password, encrypted_blob)
        else:
            return SecurityManager._decrypt_v1(password, encrypted_blob)

    @staticmethod
    def _decrypt_v2(password: str, encrypted_blob: bytes) -> bytes:
        """Descifra un archivo v2 (con llave maestra)."""
        # Formato: MAGIC(6) + salt(16) + nonce(16) + tag(16) + ciphertext
        if len(encrypted_blob) < 54:  # 6 + 16 + 16 + 16
            raise ValueError("Datos cifrados v2 inválidos o corruptos.")

        offset = 6  # Saltar el header mágico
        salt = encrypted_blob[offset:offset + 16]
        nonce = encrypted_blob[offset + 16:offset + 32]
        tag = encrypted_blob[offset + 32:offset + 48]
        ciphertext = encrypted_blob[offset + 48:]

        key = SecurityManager.derive_key(password, salt)
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)

        try:
            return cipher.decrypt_and_verify(ciphertext, tag)
        except ValueError:
            raise ValueError(
                "Contraseña incorrecta o archivo corrupto. "
                "Asegúrate de usar el programa Aura Writer correcto con la llave maestra."
            )

    @staticmethod
    def _decrypt_v1(password: str, encrypted_blob: bytes) -> bytes:
        """Descifra un archivo v1 (legacy, sin llave maestra)."""
        if len(encrypted_blob) < 48:
            raise ValueError("Datos cifrados inválidos o corruptos.")

        salt = encrypted_blob[:16]
        nonce = encrypted_blob[16:32]
        tag = encrypted_blob[32:48]
        ciphertext = encrypted_blob[48:]

        key = SecurityManager.derive_key_legacy(password, salt)
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)

        return cipher.decrypt_and_verify(ciphertext, tag)

    @staticmethod
    def is_v2_format(encrypted_blob: bytes) -> bool:
        """Verifica si un blob usa el formato v2 (con llave maestra)."""
        return encrypted_blob[:6] == SecurityManager._MAGIC_V2

    # ------------------------------------------------------------------
    # Empaquetado de proyecto (ZIP cifrado)
    # ------------------------------------------------------------------

    @staticmethod
    def package_project(password: str, source_dir: str, output_file: str):
        """Comprime un directorio y lo guarda cifrado en un archivo (formato v2)."""
        memory_zip = io.BytesIO()
        with zipfile.ZipFile(memory_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(source_dir):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, source_dir)
                    zf.write(full_path, rel_path)

        encrypted_blob = SecurityManager.encrypt_data(password, memory_zip.getvalue())
        # Guardado atómico para prevenir corrupción en caso de apagón/cierre forzado
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        temp_output = output_file + ".tmp"
        with open(temp_output, 'wb') as f:
            f.write(encrypted_blob)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_output, output_file)

    @staticmethod
    def unpackage_project(password: str, encrypted_file: str, target_dir: str):
        """Descifra un archivo y lo extrae en el directorio destino."""
        with open(encrypted_file, 'rb') as f:
            encrypted_blob = f.read()

        decrypted_zip_data = SecurityManager.decrypt_data(password, encrypted_blob)
        memory_zip = io.BytesIO(decrypted_zip_data)

        with zipfile.ZipFile(memory_zip, 'r') as zf:
            zf.extractall(target_dir)

    # ------------------------------------------------------------------
    # Migración v1 → v2
    # ------------------------------------------------------------------

    @staticmethod
    def migrate_v1_to_v2(password: str, file_path: str) -> bool:
        """
        Migra un archivo .aura de v1 (sin llave) a v2 (con llave maestra).
        
        Returns:
            True si la migración fue exitosa, False si ya es v2.
        """
        with open(file_path, 'rb') as f:
            blob = f.read()

        if SecurityManager.is_v2_format(blob):
            log.info("El archivo ya está en formato v2.")
            return False

        # Descifrar con v1
        try:
            plaintext = SecurityManager._decrypt_v1(password, blob)
        except ValueError as e:
            raise ValueError(f"No se pudo migrar: {e}") from e

        # Re-cifrar con v2
        new_blob = SecurityManager.encrypt_data(password, plaintext)
        with open(file_path, 'wb') as f:
            f.write(new_blob)

        log.info("Archivo migrado exitosamente a formato v2: %s", file_path)
        return True
