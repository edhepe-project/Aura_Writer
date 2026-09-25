"""
ThemeManager — Gestor de temas visuales de Aura Writer.
Proporciona los temas Oscuro (Dark) y Claro (Light) como hojas de estilo Qt,
y persiste la preferencia del usuario en un archivo de configuración local.
"""

from __future__ import annotations
import os

from core.themes.dark import DARK_STYLESHEET
from core.themes.light import LIGHT_STYLESHEET
from core.themes.sepia import SEPIA_STYLESHEET

from PyQt6.QtCore import QObject, pyqtSignal

class ThemeSignalEmitter(QObject):
    theme_changed = pyqtSignal(str)

_theme_signals = ThemeSignalEmitter()

_PREFS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "..", "aura_prefs.json")

DARK = "dark"
LIGHT = "light"
SEPIA = "sepia"


class ThemeManager:
    """Controlador central de temas visuales y paletas de la aplicación."""
    _current: str = DARK
    signals = _theme_signals

    STYLESHEETS = {
        DARK:  DARK_STYLESHEET,
        LIGHT: LIGHT_STYLESHEET,
        SEPIA: SEPIA_STYLESHEET,
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
                palette.setColor(QPalette.ColorRole.Window, QColor("#faf8f5"))
                palette.setColor(QPalette.ColorRole.WindowText, QColor("#1f2937"))
                palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
                palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#f3f0ea"))
                palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#ffffff"))
                palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#1f2937"))
                palette.setColor(QPalette.ColorRole.Text, QColor("#1f2937"))
                palette.setColor(QPalette.ColorRole.Button, QColor("#f3f0ea"))
                palette.setColor(QPalette.ColorRole.ButtonText, QColor("#1f2937"))
                palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
                palette.setColor(QPalette.ColorRole.Highlight, QColor("#d97706"))
                palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
            elif theme == SEPIA:
                palette.setColor(QPalette.ColorRole.Window, QColor("#f4ecd8"))
                palette.setColor(QPalette.ColorRole.WindowText, QColor("#2d241e"))
                palette.setColor(QPalette.ColorRole.Base, QColor("#fcf8ee"))
                palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#ebdcb9"))
                palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#fcf8ee"))
                palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#2d241e"))
                palette.setColor(QPalette.ColorRole.Text, QColor("#2d241e"))
                palette.setColor(QPalette.ColorRole.Button, QColor("#ebdcb9"))
                palette.setColor(QPalette.ColorRole.ButtonText, QColor("#2d241e"))
                palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
                palette.setColor(QPalette.ColorRole.Highlight, QColor("#b45309"))
                palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
            else:
                palette.setColor(QPalette.ColorRole.Window, QColor("#121214"))
                palette.setColor(QPalette.ColorRole.WindowText, QColor("#f2f2f7"))
                palette.setColor(QPalette.ColorRole.Base, QColor("#1c1c1e"))
                palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#2c2c2e"))
                palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#1c1c1e"))
                palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#f2f2f7"))
                palette.setColor(QPalette.ColorRole.Text, QColor("#f2f2f7"))
                palette.setColor(QPalette.ColorRole.Button, QColor("#1c1c1e"))
                palette.setColor(QPalette.ColorRole.ButtonText, QColor("#f2f2f7"))
                palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
                palette.setColor(QPalette.ColorRole.Highlight, QColor("#ffd60a"))
                palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#000000"))
            app.setPalette(palette)
        except Exception:
            pass

        app.setStyleSheet(cls.STYLESHEETS[theme])
        cls.save(theme)
        cls.signals.theme_changed.emit(theme)

    @classmethod
    def toggle(cls, app) -> str:
        """Alterna cíclicamente entre todos los temas disponibles (oscuro, claro, sepia)."""
        order = [DARK, LIGHT, SEPIA]
        idx = order.index(cls._current) if cls._current in order else 0
        next_theme = order[(idx + 1) % len(order)]
        cls.apply(app, next_theme)
        return next_theme

    @classmethod
    def current(cls) -> str:
        return cls._current

    @classmethod
    def is_dark(cls) -> bool:
        return cls._current == DARK

    @classmethod
    def is_sepia(cls) -> bool:
        return cls._current == SEPIA

    @classmethod
    def get_color(cls, dark: str, light: str, sepia: str = None) -> str:
        """Retorna un color adaptado según el tema activo (dark, light, sepia)."""
        cur = cls._current
        if cur == SEPIA:
            return sepia if sepia is not None else "#fcf8ee"
        elif cur == LIGHT:
            return light
        return dark

    @classmethod
    def theme_colors(cls) -> dict[str, str]:
        """Retorna un diccionario con los colores fundamentales del tema activo."""
        cur = cls._current
        if cur == SEPIA:
            return {
                "bg_main": "#f4ecd8",
                "bg_card": "#fcf8ee",
                "bg_input": "#fcf8ee",
                "fg_text": "#2d241e",
                "sub_text": "#5c4d41",
                "border": "#cbb894",
                "accent": "#b45309",
                "hover": "#ebdcb9",
            }
        elif cur == LIGHT:
            return {
                "bg_main": "#faf8f5",
                "bg_card": "#ffffff",
                "bg_input": "#ffffff",
                "fg_text": "#1f2937",
                "sub_text": "#6b7280",
                "border": "#e5e7eb",
                "accent": "#d97706",
                "hover": "#f3f0ea",
            }
        else:
            return {
                "bg_main": "#121214",
                "bg_card": "#1c1c1e",
                "bg_input": "#2c2c2e",
                "fg_text": "#f2f2f7",
                "sub_text": "#8e8e93",
                "border": "#3a3a3c",
                "accent": "#ffd60a",
                "hover": "#2c2c2e",
            }
