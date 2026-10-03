"""
src/core/themes — Subpaquete de temas visuales de Aura Writer.

Arquitectura:
  base.py        — Template único de stylesheet (sin colores hardcodeados)
  dark.py        — Paleta oscura  → genera DARK_STYLESHEET
  light.py       — Paleta clara   → genera LIGHT_STYLESHEET
  sepia.py       — Paleta sepia   → genera SEPIA_STYLESHEET

Para agregar un tema nuevo:
  1. Crea un archivo ej. "oceano.py" con OCEANO_PALETTE y OCEANO_STYLESHEET.
  2. Regístralo en ThemeManager._load_themes() en core/theme_manager.py.
  ¡Eso es todo! No hay que tocar el template ni el código de la UI.
"""

from core.themes.dark   import DARK_STYLESHEET,   DARK_PALETTE
from core.themes.light  import LIGHT_STYLESHEET,  LIGHT_PALETTE
from core.themes.sepia  import SEPIA_STYLESHEET,  SEPIA_PALETTE
from core.themes.nordic import NORDIC_STYLESHEET, NORDIC_PALETTE

__all__ = [
    "DARK_STYLESHEET",   "DARK_PALETTE",
    "LIGHT_STYLESHEET",  "LIGHT_PALETTE",
    "SEPIA_STYLESHEET",  "SEPIA_PALETTE",
    "NORDIC_STYLESHEET", "NORDIC_PALETTE",
]

