"""
ui.login
--------
Subpaquete de autenticacion y creacion de proyectos de Aura Writer.

Modulos:
  dialog.py  - LoginDialog (clase principal, ensamblado)
  widgets.py - Constructores de paginas UI (open, new, password toggle)
  logic.py   - Logica de interaccion (validacion, selector de archivo, accept)
  actions.py - Acciones externas (actualizaciones, llave maestra)

API publica:
  from ui.login import LoginDialog
"""

from .dialog import LoginDialog

__all__ = ["LoginDialog"]
