"""
ThemeManager — Gestor de temas visuales de Aura Writer.
Proporciona los temas Oscuro (Dark) y Claro (Light) como hojas de estilo Qt,
y persiste la preferencia del usuario en un archivo de configuración local.
"""

from __future__ import annotations
import os

from core.themes.dark import DARK_STYLESHEET
from core.themes.light import LIGHT_STYLESHEET

_PREFS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "..", "aura_prefs.json")

DARK = "dark"
LIGHT = "light"


class ThemeManager:
    """Controlador central de temas visuales y paletas de la aplicación."""
    _current: str = DARK

    STYLESHEETS = {
        DARK:  DARK_STYLESHEET,
        LIGHT: LIGHT_STYLESHEET,
    }

    @classmethod
    def load(cls) -> str:
        """Lee el tema guardado. Retorna 'dark' si no existe preferencia."""
        try:
            from core.config_manager import ConfigManager
            theme = ConfigManager.get("theme", DARK)
            if theme in cls.STYLESHEETS:
                cls._current = theme
        except Exception:
            pass
        return cls._current

    @classmethod
    def save(cls, theme: str):
        """Persiste la preferencia del tema en disco."""
        try:
            from core.config_manager import ConfigManager
            ConfigManager.set("theme", theme)
        except Exception:
            pass

    @classmethod
    def apply(cls, app, theme: str):
        """Aplica un tema a la QApplication y lo guarda."""
        if theme not in cls.STYLESHEETS:
            theme = DARK
        cls._current = theme

        # Sincronizar QPalette del sistema con el tema para evitar fondos oscuros residuales
        try:
            from PyQt6.QtGui import QPalette, QColor
            palette = QPalette()
            if theme == LIGHT:
                palette.setColor(QPalette.ColorRole.Window, QColor("#f5f0ea"))
                palette.setColor(QPalette.ColorRole.WindowText, QColor("#1a1a2e"))
                palette.setColor(QPalette.ColorRole.Base, QColor("#faf7f3"))
                palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#ede8e1"))
                palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#faf7f3"))
                palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#1a1a2e"))
                palette.setColor(QPalette.ColorRole.Text, QColor("#1a1a2e"))
                palette.setColor(QPalette.ColorRole.Button, QColor("#ede8e1"))
                palette.setColor(QPalette.ColorRole.ButtonText, QColor("#1a1a2e"))
                palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
                palette.setColor(QPalette.ColorRole.Highlight, QColor("#9a5c00"))
                palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
            else:
                palette.setColor(QPalette.ColorRole.Window, QColor("#1c1c1e"))
                palette.setColor(QPalette.ColorRole.WindowText, QColor("#f2f2f7"))
                palette.setColor(QPalette.ColorRole.Base, QColor("#2c2c2e"))
                palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#3a3a3c"))
                palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#2c2c2e"))
                palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#f2f2f7"))
                palette.setColor(QPalette.ColorRole.Text, QColor("#f2f2f7"))
                palette.setColor(QPalette.ColorRole.Button, QColor("#2c2c2e"))
                palette.setColor(QPalette.ColorRole.ButtonText, QColor("#f2f2f7"))
                palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
                palette.setColor(QPalette.ColorRole.Highlight, QColor("#d4a017"))
                palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#000000"))
            app.setPalette(palette)
        except Exception:
            pass

        app.setStyleSheet(cls.STYLESHEETS[theme])
        cls.save(theme)

    @classmethod
    def toggle(cls, app) -> str:
        """Alterna entre dark y light. Retorna el nuevo tema activo."""
        next_theme = LIGHT if cls._current == DARK else DARK
        cls.apply(app, next_theme)
        return next_theme

    @classmethod
    def current(cls) -> str:
        return cls._current

    @classmethod
    def is_dark(cls) -> bool:
        return cls._current == DARK
