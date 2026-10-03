"""
ThemeManager — Gestor de temas visuales de Aura Writer.

Arquitectura de tokens:
  - Cada tema define ÚNICAMENTE una paleta de colores (diccionario).
  - El stylesheet se genera automáticamente desde base.py interpolando esa paleta.
  - Para añadir un tema nuevo: crear un archivo en core/themes/ con una paleta
    que tenga todos los tokens, luego registrarlo en THEMES aquí abajo.
  - NINGÚN color está hardcodeado fuera de los archivos de paleta.
"""

from __future__ import annotations
import os

from PyQt6.QtCore import QObject, pyqtSignal


# ── Señales ────────────────────────────────────────────────────────────────────

class ThemeSignalEmitter(QObject):
    theme_changed = pyqtSignal(str)

_theme_signals = ThemeSignalEmitter()


# ── IDs de temas ───────────────────────────────────────────────────────────────

DARK  = "dark"
LIGHT = "light"
SEPIA = "sepia"


# ── Registro de temas ──────────────────────────────────────────────────────────
# Para añadir un tema: importa su paleta y agrégala aquí.
# El resto del código se adapta automáticamente.

def _load_themes() -> dict:
    """Importa las paletas de todos los temas registrados."""
    from core.themes.dark  import DARK_PALETTE,  DARK_STYLESHEET
    from core.themes.light import LIGHT_PALETTE, LIGHT_STYLESHEET
    from core.themes.sepia import SEPIA_PALETTE, SEPIA_STYLESHEET

    # Asegura que cada tema contenga al menos todos los tokens de DARK_PALETTE
    full_dark = dict(DARK_PALETTE)
    full_light = {**DARK_PALETTE, **LIGHT_PALETTE}
    full_sepia = {**DARK_PALETTE, **SEPIA_PALETTE}

    return {
        DARK:  {"palette": full_dark,  "stylesheet": DARK_STYLESHEET},
        LIGHT: {"palette": full_light, "stylesheet": LIGHT_STYLESHEET},
        SEPIA: {"palette": full_sepia, "stylesheet": SEPIA_STYLESHEET},
    }


# ── ThemeManager ───────────────────────────────────────────────────────────────

class ThemeManager:
    """Controlador central de temas visuales y paletas de la aplicación."""

    _current: str = DARK
    signals = _theme_signals

    # Orden de alternancia con el botón de toggle
    TOGGLE_ORDER = [DARK, LIGHT, SEPIA]

    # Cache para no recargar imports en cada acceso
    _themes: dict | None = None

    # ── acceso interno ────────────────────────────────────────────────────────

    @classmethod
    def _get_themes(cls) -> dict:
        if cls._themes is None:
            cls._themes = _load_themes()
        return cls._themes

    @classmethod
    def _theme_data(cls, theme: str | None = None) -> dict:
        theme = theme or cls._current
        return cls._get_themes().get(theme, cls._get_themes()[DARK])

    # ── API pública ───────────────────────────────────────────────────────────

    @classmethod
    def load(cls) -> str:
        """Lee el tema guardado. Retorna 'dark' si no existe preferencia."""
        try:
            from core.config_manager import ConfigManager
            theme = ConfigManager.get("theme", DARK)
            if theme in cls._get_themes():
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
        themes = cls._get_themes()
        if theme not in themes:
            theme = DARK
        cls._current = theme

        palette_data = cls._theme_data(theme)["palette"]

        # Sincronizar QPalette del sistema con el tema activo
        try:
            from PyQt6.QtGui import QPalette, QColor
            qp = QPalette()
            qp.setColor(QPalette.ColorRole.Window,          QColor(palette_data["bg_app"]))
            qp.setColor(QPalette.ColorRole.WindowText,      QColor(palette_data["fg_primary"]))
            qp.setColor(QPalette.ColorRole.Base,            QColor(palette_data["bg_surface"]))
            qp.setColor(QPalette.ColorRole.AlternateBase,   QColor(palette_data["bg_hover"]))
            qp.setColor(QPalette.ColorRole.ToolTipBase,     QColor(palette_data["bg_overlay"]))
            qp.setColor(QPalette.ColorRole.ToolTipText,     QColor(palette_data["fg_primary"]))
            qp.setColor(QPalette.ColorRole.Text,            QColor(palette_data["fg_primary"]))
            qp.setColor(QPalette.ColorRole.Button,          QColor(palette_data["bg_button"]))
            qp.setColor(QPalette.ColorRole.ButtonText,      QColor(palette_data["fg_primary"]))
            qp.setColor(QPalette.ColorRole.BrightText,      QColor("#ffffff"))
            qp.setColor(QPalette.ColorRole.Highlight,       QColor(palette_data["accent"]))
            qp.setColor(QPalette.ColorRole.HighlightedText, QColor(palette_data["fg_selected"]))
            app.setPalette(qp)
        except Exception:
            pass

        app.setStyleSheet(cls._theme_data(theme)["stylesheet"])
        cls.save(theme)
        cls.signals.theme_changed.emit(theme)

    @classmethod
    def toggle(cls, app) -> str:
        """Alterna cíclicamente entre los temas en TOGGLE_ORDER."""
        order = cls.TOGGLE_ORDER
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

    # ── Acceso a colores de la paleta ─────────────────────────────────────────

    @classmethod
    def palette(cls) -> dict:
        """
        Retorna la paleta completa del tema activo.

        Uso en Python:
            colors = ThemeManager.palette()
            my_widget.setStyleSheet(f"background: {colors['bg_surface']};")
        """
        return cls._theme_data()["palette"]

    @classmethod
    def color(cls, token: str, fallback: str = "#ff00ff") -> str:
        """
        Retorna el color de un token semántico del tema activo.

        Args:
            token:    Nombre del token (ej. 'bg_surface', 'fg_primary', 'accent').
            fallback: Color de emergencia si el token no existe (magenta = error visible).

        Ejemplo:
            accent = ThemeManager.color("accent")
            border = ThemeManager.color("border_default")
        """
        return cls._theme_data()["palette"].get(token, fallback)

    # ── Compatibilidad hacia atrás (deprecado) ────────────────────────────────

    @classmethod
    def theme_colors(cls) -> dict:
        """
        [DEPRECADO] Usar ThemeManager.palette() en su lugar.
        Retorna un subconjunto de tokens con los nombres del API anterior.
        Se mantiene para no romper código existente.
        """
        p = cls.palette()
        return {
            "bg_main":   p["bg_app"],
            "bg_card":   p["bg_surface"],
            "bg_input":  p["bg_input"],
            "fg_text":   p["fg_primary"],
            "sub_text":  p["fg_secondary"],
            "subtext":   p["fg_muted"],
            "border":    p["border_default"],
            "accent":    p["accent"],
            "hover":     p["bg_hover"],
            "green":     p.get("green",  "#30d158"),
            "blue":      p.get("blue",   "#0a84ff"),
            "red":       p.get("red",    "#ff453a"),
            "purple":    p.get("purple", "#bf5af2"),
            "amber":     p["accent"],
        }

    @classmethod
    def get_color(cls, dark: str, light: str, sepia: str = None) -> str:
        """
        [DEPRECADO] Usar ThemeManager.color(token) en su lugar.
        Retorna uno de los tres colores según el tema activo.
        """
        cur = cls._current
        if cur == SEPIA:
            return sepia if sepia is not None else dark
        elif cur == LIGHT:
            return light
        return dark
