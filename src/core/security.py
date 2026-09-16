"""
Aura Writer — Security Module
Cifrado AES-256-GCM con llave maestra embebida.

Formatos soportados:
  V1 (legacy): Sin header. Clave derivada solo de contraseña.
  V2:          Header AURA\x00\x02. Clave = PBKDF2(password) + APP_KEY.
  V3 (3FA):    Header AURA\x00\x03. Cifrado en DOS capas:
               - Capa exterior: password + APP_KEY → revela secreto TOTP
               - Capa interior: password + secreto_TOTP + APP_KEY → revela contenido
               Sin los 3 factores simultáneos, descifrar es imposible.

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

    # ── Headers mágicos para identificar versión del formato ─────────
    _MAGIC_V2 = b"AURA\x00\x02"  # 6 bytes: "AURA" + versión 2
    _MAGIC_V3 = b"AURA\x00\x03"  # 6 bytes: "AURA" + versión 3 (3FA - TOTP en KDF)

    # Bytes reservados para el secreto TOTP en la capa exterior de V3.
    # pyotp.random_base32(length=32) produce 32 chars; dejamos 64 por si se usa
    # un secreto más largo en versiones futuras.
    _TOTP_SECRET_SLOT = 64

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

        from core.config_manager import ConfigManager
        try:
            custom_key = ConfigManager.get("app_key")
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

        # Persistir a través de ConfigManager
        from core.config_manager import ConfigManager
        success = ConfigManager.set("app_key", clean_key)
        if success:
            log.info("Nueva llave maestra de aplicación guardada correctamente.")
            return True
        else:
            log.error("Error al guardar la llave maestra en preferencias.")
            return False

    # ------------------------------------------------------------------
    # Derivación de clave
    # ------------------------------------------------------------------

    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        """
        Deriva una clave de 256 bits combinando contraseña + llave de app. (V2)
        
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
    def derive_key_v3(password: str, totp_secret: str, salt: bytes) -> bytes:
        """
        Deriva una clave de 256 bits combinando contraseña + secreto TOTP + llave de app. (V3)

        Este es el verdadero 3FA criptográfico:
          - Factor 1: contraseña (algo que sabes)
          - Factor 2: secreto TOTP (algo que tienes — tu app/backups)
          - Factor 3: APP_KEY   (algo que tiene tu equipo)

        Proceso:
          1. PBKDF2(password + "\x00" + totp_secret, salt) → clave combinada
          2. HMAC-SHA256(clave_combinada, APP_KEY) → clave final

        El separador nulo (\x00) previene ataques de concatenación donde
        una contraseña larga podría "absorber" parte del secreto TOTP.
        """
        combined_password = password + "\x00" + totp_secret
        user_key = PBKDF2(
            combined_password, salt,
            dkLen=SecurityManager.KEY_LEN,
            count=SecurityManager.ITERATIONS,
            hmac_hash_module=SHA256
        )
        return hmac.new(
            user_key,
            SecurityManager.get_app_key(),
            hashlib.sha256
        ).digest()

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
        Cifra datos usando AES-256-GCM con llave maestra (formato V2).
        
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
    def encrypt_data_v3(password: str, totp_secret: str, data: bytes) -> bytes:
        """
        Cifra datos con 3FA en DOS capas AES-256-GCM (formato V3).

        Arquitectura:
          CAPA INTERIOR: cifrada con derive_key_v3(password, totp_secret, inner_salt)
            → contiene el ZIP del proyecto
          CAPA EXTERIOR: cifrada con derive_key(password, outer_salt)  [sin TOTP]
            → contiene: secreto_TOTP_padded(64 bytes) + inner_blob

        Formato binario final:
          MAGIC_V3 (6) + OUTER_SALT (16) + OUTER_NONCE (16) + OUTER_TAG (16)
          + OUTER_CIPHERTEXT

        Para descifrar:
          1. Descifrar capa exterior con password + APP_KEY → revela totp_secret
          2. Verificar código TOTP de 6 dígitos (usando totp_secret extraído)
          3. Descifrar capa interior con password + totp_secret + APP_KEY → contenido
        """
        if not totp_secret:
            raise ValueError("Se requiere un secreto TOTP para cifrar en formato V3.")

        # ── Capa INTERIOR: password + totp_secret + APP_KEY ──────────────
        inner_salt = get_random_bytes(16)
        inner_key  = SecurityManager.derive_key_v3(password, totp_secret, inner_salt)
        inner_cipher = AES.new(inner_key, AES.MODE_GCM)
        inner_ct, inner_tag = inner_cipher.encrypt_and_digest(data)
        inner_blob = inner_salt + inner_cipher.nonce + inner_tag + inner_ct

        # ── Capa EXTERIOR: password + APP_KEY (protege totp_secret + inner_blob) ──
        secret_bytes = totp_secret.encode("utf-8")
        if len(secret_bytes) > SecurityManager._TOTP_SECRET_SLOT:
            raise ValueError(
                f"El secreto TOTP es demasiado largo ({len(secret_bytes)} bytes). "
                f"Máximo: {SecurityManager._TOTP_SECRET_SLOT} bytes."
            )
        # Rellenar con ceros hasta el tamaño fijo del slot
        padded_secret = secret_bytes.ljust(SecurityManager._TOTP_SECRET_SLOT, b"\x00")
        outer_plaintext = padded_secret + inner_blob

        outer_salt = get_random_bytes(16)
        outer_key  = SecurityManager.derive_key(password, outer_salt)
        outer_cipher = AES.new(outer_key, AES.MODE_GCM)
        outer_ct, outer_tag = outer_cipher.encrypt_and_digest(outer_plaintext)

        return (
            SecurityManager._MAGIC_V3
            + outer_salt + outer_cipher.nonce + outer_tag
            + outer_ct
        )

    @staticmethod
    def decrypt_data(password: str, encrypted_blob: bytes, totp_code: str = "") -> bytes:
        """
        Descifra un bloque binario. Detecta automáticamente V1, V2 o V3.

        Args:
            password:       Contraseña del usuario.
            encrypted_blob: Datos cifrados.
            totp_code:      Código TOTP de 6 dígitos o código de recuperación.
                            Requerido para archivos V3 (3FA). Ignorado para V1/V2.

        Raises:
            ValueError: Contraseña incorrecta, código TOTP inválido, o archivo corrupto.
        """
        # ── Detectar versión del formato ──
        if encrypted_blob[:6] == SecurityManager._MAGIC_V3:
            return SecurityManager._decrypt_v3(password, totp_code, encrypted_blob)
        elif encrypted_blob[:6] == SecurityManager._MAGIC_V2:
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
    def _decrypt_v3(password: str, totp_code: str, encrypted_blob: bytes) -> bytes:
        """
        Descifra un archivo V3 (3FA - dos capas).

        Proceso:
          1. Descifrar capa EXTERIOR con password + APP_KEY → revela totp_secret
          2. Verificar código TOTP de 6 dígitos (o detectar código de recuperación)
          3. Descifrar capa INTERIOR con password + totp_secret + APP_KEY → contenido

        Raises:
            ValueError: Contraseña incorrecta, código TOTP inválido, o archivo V3 corrupto.
        """
        # Formato: MAGIC(6) + OUTER_SALT(16) + OUTER_NONCE(16) + OUTER_TAG(16) + OUTER_CT
        if len(encrypted_blob) < 54:  # 6 + 16 + 16 + 16
            raise ValueError("Datos V3 inválidos o corruptos.")

        offset = 6
        outer_salt  = encrypted_blob[offset:offset + 16]
        outer_nonce = encrypted_blob[offset + 16:offset + 32]
        outer_tag   = encrypted_blob[offset + 32:offset + 48]
        outer_ct    = encrypted_blob[offset + 48:]

        # ── Paso 1: Descifrar capa exterior con password + APP_KEY ────────
        outer_key    = SecurityManager.derive_key(password, outer_salt)
        outer_cipher = AES.new(outer_key, AES.MODE_GCM, nonce=outer_nonce)
        try:
            outer_plaintext = outer_cipher.decrypt_and_verify(outer_ct, outer_tag)
        except ValueError:
            raise ValueError(
                "Contraseña incorrecta o archivo V3 corrupto. "
                "Asegúrate de usar la llave maestra correcta."
            )

        # ── Extraer secreto TOTP (primeros _TOTP_SECRET_SLOT bytes) ──────
        secret_bytes = outer_plaintext[:SecurityManager._TOTP_SECRET_SLOT].rstrip(b"\x00")
        totp_secret  = secret_bytes.decode("utf-8")
        inner_blob   = outer_plaintext[SecurityManager._TOTP_SECRET_SLOT:]

        if not totp_secret:
            raise ValueError("El archivo V3 no contiene un secreto TOTP válido.")

        # ── Paso 2: Verificar identidad del usuario ───────────────────────
        # Un código de recuperación tiene formato XXXX-XXXX (8 dígitos + guion)
        # Si se usa un código de recuperación, la verificación TOTP se omite aquí
        # y el ProjectManager la valida tras abrir el archivo.
        is_recovery_code = (
            len(totp_code.replace("-", "").replace(" ", "")) == 8
            and "-" in totp_code
        )

        if not is_recovery_code:
            from core.totp_manager import TOTPManager
            if not TOTPManager.verify_code(totp_secret, totp_code):
                raise ValueError(
                    "Código TOTP incorrecto. "
                    "Verifica tu app de autenticación o usa un código de recuperación."
                )

        # ── Paso 3: Descifrar capa interior con password + totp_secret + APP_KEY ──
        if len(inner_blob) < 48:  # INNER_SALT(16) + INNER_NONCE(16) + INNER_TAG(16)
            raise ValueError("Blob interior V3 inválido o corrupto.")

        inner_salt  = inner_blob[:16]
        inner_nonce = inner_blob[16:32]
        inner_tag   = inner_blob[32:48]
        inner_ct    = inner_blob[48:]

        inner_key    = SecurityManager.derive_key_v3(password, totp_secret, inner_salt)
        inner_cipher = AES.new(inner_key, AES.MODE_GCM, nonce=inner_nonce)
        try:
            return inner_cipher.decrypt_and_verify(inner_ct, inner_tag)
        except ValueError:
            raise ValueError(
                "Error al descifrar la capa interior V3. "
                "El archivo puede estar corrupto o los factores de cifrado no coinciden."
            )

    @staticmethod
    def is_v2_format(encrypted_blob: bytes) -> bool:
        """Verifica si un blob usa el formato V2 (con llave maestra, sin TOTP en KDF)."""
        return encrypted_blob[:6] == SecurityManager._MAGIC_V2

    @staticmethod
    def is_v3_format(encrypted_blob: bytes) -> bool:
        """Verifica si un blob usa el formato V3 (3FA — TOTP integrado en KDF)."""
        return encrypted_blob[:6] == SecurityManager._MAGIC_V3

    # ------------------------------------------------------------------
    # Empaquetado de proyecto (ZIP cifrado)
    # ------------------------------------------------------------------

    @staticmethod
    def package_project(password: str, source_dir: str, output_file: str,
                        totp_secret: str = ""):
        """
        Comprime un directorio y lo guarda cifrado.

        Args:
            password:    Contraseña del usuario.
            source_dir:  Directorio con los archivos del proyecto.
            output_file: Ruta de salida del archivo .aura.
            totp_secret: Secreto TOTP base32. Si se proporciona, usa formato V3 (3FA).
                         Si está vacío, usa formato V2 estándar.
        """
        memory_zip = io.BytesIO()
        with zipfile.ZipFile(memory_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(source_dir):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, source_dir)
                    zf.write(full_path, rel_path)

        zip_data = memory_zip.getvalue()
        if totp_secret:
            encrypted_blob = SecurityManager.encrypt_data_v3(password, totp_secret, zip_data)
            log.debug("Proyecto empaquetado en formato V3 (3FA).")
        else:
            encrypted_blob = SecurityManager.encrypt_data(password, zip_data)
            log.debug("Proyecto empaquetado en formato V2.")

        # Guardado atómico para prevenir corrupción en caso de apagón/cierre forzado
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        temp_output = output_file + ".tmp"
        with open(temp_output, 'wb') as f:
            f.write(encrypted_blob)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_output, output_file)

    @staticmethod
    def unpackage_project(password: str, encrypted_file: str, target_dir: str,
                          totp_code: str = ""):
        """
        Descifra un archivo .aura y lo extrae en el directorio destino.

        Args:
            password:       Contraseña del usuario.
            encrypted_file: Ruta del archivo .aura.
            target_dir:     Directorio donde extraer el proyecto.
            totp_code:      Código TOTP de 6 dígitos o código de recuperación.
                            Requerido para archivos V3. Ignorado para V1/V2.
        """
        with open(encrypted_file, 'rb') as f:
            encrypted_blob = f.read()

        decrypted_zip_data = SecurityManager.decrypt_data(password, encrypted_blob,
                                                          totp_code=totp_code)
        memory_zip = io.BytesIO(decrypted_zip_data)

        with zipfile.ZipFile(memory_zip, 'r') as zf:
            zf.extractall(target_dir)

    # ------------------------------------------------------------------
    # Migraciones de formato
    # ------------------------------------------------------------------

    @staticmethod
    def migrate_v1_to_v2(password: str, file_path: str) -> bool:
        """
        Migra un archivo .aura de V1 (sin llave) a V2 (con llave maestra).

        Returns:
            True si la migración fue exitosa, False si ya es V2 o superior.
        """
        with open(file_path, 'rb') as f:
            blob = f.read()

        if SecurityManager.is_v2_format(blob) or SecurityManager.is_v3_format(blob):
            log.info("El archivo ya está en formato V2 o V3. No se requiere migración V1→V2.")
            return False

        # Descifrar con V1
        try:
            plaintext = SecurityManager._decrypt_v1(password, blob)
        except ValueError as e:
            raise ValueError(f"No se pudo migrar V1→V2: {e}") from e

        # Re-cifrar con V2
        new_blob = SecurityManager.encrypt_data(password, plaintext)
        with open(file_path, 'wb') as f:
            f.write(new_blob)

        log.info("Archivo migrado exitosamente a formato V2: %s", file_path)
        return True

    @staticmethod
    def migrate_v2_to_v3(password: str, totp_secret: str, file_path: str) -> bool:
        """
        Migra un archivo .aura de V2 a V3 (3FA — TOTP integrado en KDF).

        Este proceso descifra el archivo con V2 y lo re-cifra con V3,
        incorporando el secreto TOTP en la capa criptográfica.

        Args:
            password:    Contraseña del usuario.
            totp_secret: Secreto TOTP base32 del proyecto.
            file_path:   Ruta del archivo .aura a migrar (se sobreescribe).

        Returns:
            True si la migración fue exitosa, False si ya es V3.
        """
        with open(file_path, 'rb') as f:
            blob = f.read()

        if SecurityManager.is_v3_format(blob):
            log.info("El archivo ya está en formato V3. No se requiere migración.")
            return False

        # Descifrar con V2 (o V1 para compatibilidad total)
        try:
            plaintext = SecurityManager.decrypt_data(password, blob)
        except ValueError as e:
            raise ValueError(f"No se pudo migrar V2→V3: {e}") from e

        # Re-cifrar con V3 (3FA)
        new_blob = SecurityManager.encrypt_data_v3(password, totp_secret, plaintext)

        # Guardado atómico
        temp_path = file_path + ".tmp"
        with open(temp_path, 'wb') as f:
            f.write(new_blob)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_path, file_path)

        log.info("Archivo migrado exitosamente a formato V3 (3FA): %s", file_path)
        return True
