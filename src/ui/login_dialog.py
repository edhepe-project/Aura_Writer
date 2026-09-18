# Shim de retrocompatibilidad
# Re-exporta LoginDialog desde el subpaquete ui.login.
# No eliminar: otros modulos pueden importar desde ui.login_dialog directamente.
from ui.login import LoginDialog  # noqa: F401

__all__ = ["LoginDialog"]
