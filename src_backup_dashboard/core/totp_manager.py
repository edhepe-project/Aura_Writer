"""
Aura Writer — TOTP Manager (2FA Offline)

Maneja la generación, almacenamiento y verificación de códigos TOTP
para autenticación de doble factor compatible con Google Authenticator,
Authy, Microsoft Authenticator, etc.
"""

import io
import pyotp
import qrcode
from qrcode.image.pil import PilImage


class TOTPManager:
    """Gestión completa de TOTP offline para Aura Writer."""

    ISSUER = "Aura Writer"

    @staticmethod
    def generate_secret() -> str:
        """Genera un secreto TOTP base32 aleatorio de 32 caracteres."""
        return pyotp.random_base32(length=32)

    @staticmethod
    def generate_recovery_codes(count: int = 8) -> list[str]:
        """
        Genera códigos de recuperación de un solo uso.
        Formato: XXXX-XXXX (8 dígitos agrupados).
        """
        import secrets
        codes = []
        for _ in range(count):
            num = secrets.randbelow(10**8)
            code = f"{num:08d}"
            codes.append(f"{code[:4]}-{code[4:]}")
        return codes

    @staticmethod
    def get_totp(secret: str) -> pyotp.TOTP:
        """Retorna un objeto TOTP configurado."""
        return pyotp.TOTP(secret, interval=30, digits=6)

    @staticmethod
    def get_provisioning_uri(secret: str, username: str = "Escritor") -> str:
        """
        Genera la URI otpauth:// que codifica el QR.
        Compatible con Google Authenticator, Authy, etc.
        """
        totp = TOTPManager.get_totp(secret)
        return totp.provisioning_uri(
            name=username,
            issuer_name=TOTPManager.ISSUER
        )

    @staticmethod
    def generate_qr_image(secret: str, username: str = "Escritor") -> bytes:
        """
        Genera una imagen PNG del código QR para escanear.
        Retorna los bytes de la imagen.
        """
        uri = TOTPManager.get_provisioning_uri(secret, username)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)
        img: PilImage = qr.make_image(fill_color="black", back_color="white")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    @staticmethod
    def verify_code(secret: str, code: str) -> bool:
        """
        Verifica un código TOTP con ventana de ±1 periodo (±30s).
        Esto permite relojes ligeramente desincronizados.
        """
        if not secret or not code:
            return False
        code = code.strip().replace(" ", "").replace("-", "")
        if len(code) != 6 or not code.isdigit():
            return False
        totp = TOTPManager.get_totp(secret)
        return totp.verify(code, valid_window=1)

    @staticmethod
    def verify_recovery_code(code: str, stored_codes: list[str]) -> tuple[bool, list[str]]:
        """
        Verifica un código de recuperación. Si es válido, lo elimina
        de la lista (un solo uso).
        Retorna (éxito, lista_actualizada).
        """
        code_clean = code.strip().upper()
        if code_clean in stored_codes:
            remaining = [c for c in stored_codes if c != code_clean]
            return True, remaining
        return False, stored_codes

    @staticmethod
    def get_current_code(secret: str) -> str:
        """Retorna el código TOTP actual (para testing/debug)."""
        totp = TOTPManager.get_totp(secret)
        return totp.now()
