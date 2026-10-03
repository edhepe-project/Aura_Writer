"""
Tests unitarios para ThemeManager.
Valida la paleta de colores, el toggle de temas y que los stylesheets no estén vacíos.
"""
import pytest
from core.theme_manager import ThemeManager, DARK, LIGHT, SEPIA, NORDIC, DRACULA, FOREST

ALL_THEMES = [DARK, LIGHT, SEPIA, NORDIC, DRACULA, FOREST]
DARK_THEMES = [DARK, NORDIC, DRACULA, FOREST]
LIGHT_THEMES = [LIGHT, SEPIA]


def setup_function():
    """Resetear al tema oscuro antes de cada test para aislamiento."""
    ThemeManager._current = DARK


def test_default_theme_is_dark():
    assert ThemeManager.current() == DARK
    assert ThemeManager.is_dark() is True


def test_stylesheets_are_not_empty():
    """Todos los temas deben tener un stylesheet con contenido CSS real."""
    themes = ThemeManager._get_themes()
    for name in ALL_THEMES:
        ss = themes[name]["stylesheet"]
        assert isinstance(ss, str) and len(ss) > 100, \
            f"Stylesheet '{name}' está vacío o demasiado corto"


def test_stylesheets_contain_basic_css_selectors():
    """Cada stylesheet debe contener CSS válido con selectores Qt."""
    themes = ThemeManager._get_themes()
    for name, data in themes.items():
        ss = data["stylesheet"]
        assert "QWidget" in ss or "QMainWindow" in ss or "background" in ss, \
            f"Stylesheet '{name}' parece no contener CSS válido"


def test_is_dark_returns_true_for_all_dark_themes():
    """Dark, Nordic, Drácula y Forest deben ser considerados oscuros."""
    for theme in DARK_THEMES:
        ThemeManager._current = theme
        assert ThemeManager.is_dark() is True, \
            f"is_dark() debería ser True para '{theme}'"


def test_is_dark_returns_false_for_light_themes():
    """Light y Sepia no deben ser considerados oscuros."""
    for theme in LIGHT_THEMES:
        ThemeManager._current = theme
        assert ThemeManager.is_dark() is False, \
            f"is_dark() debería ser False para '{theme}'"


def test_current_returns_active_theme():
    ThemeManager._current = LIGHT
    assert ThemeManager.current() == LIGHT

    ThemeManager._current = DARK
    assert ThemeManager.current() == DARK


def test_toggle_switches_theme(qtbot):
    """El toggle debe recorrer todos los temas en TOGGLE_ORDER correctamente."""
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()

    ThemeManager._current = DARK
    result = ThemeManager.toggle(app)
    assert result == FOREST
    assert ThemeManager.current() == FOREST

    result = ThemeManager.toggle(app)
    assert result == DRACULA
    assert ThemeManager.current() == DRACULA

    result = ThemeManager.toggle(app)
    assert result == LIGHT
    assert ThemeManager.current() == LIGHT

    result = ThemeManager.toggle(app)
    assert result == SEPIA
    assert ThemeManager.current() == SEPIA

    result = ThemeManager.toggle(app)
    assert result == NORDIC
    assert ThemeManager.current() == NORDIC

    result = ThemeManager.toggle(app)
    assert result == DARK
    assert ThemeManager.current() == DARK


def test_toggle_is_cyclic(qtbot):
    """El toggle debe ser cíclico: N toggles = regresa al inicio."""
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    order = ThemeManager.TOGGLE_ORDER
    ThemeManager._current = DARK
    for _ in order:
        ThemeManager.toggle(app)
    assert ThemeManager.current() == DARK


def test_apply_invalid_theme_falls_back_to_dark(qtbot):
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()

    ThemeManager.apply(app, "nonexistent_theme")
    assert ThemeManager.current() == DARK


def test_apply_light_theme(qtbot):
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()

    ThemeManager.apply(app, LIGHT)
    assert ThemeManager.current() == LIGHT
    assert ThemeManager.is_dark() is False


def test_apply_dark_theme(qtbot):
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()

    ThemeManager._current = LIGHT
    ThemeManager.apply(app, DARK)
    assert ThemeManager.current() == DARK
    assert ThemeManager.is_dark() is True


def test_apply_dracula_theme(qtbot):
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()

    ThemeManager.apply(app, DRACULA)
    assert ThemeManager.current() == DRACULA
    assert ThemeManager.is_dark() is True


def test_apply_forest_theme(qtbot):
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()

    ThemeManager.apply(app, FOREST)
    assert ThemeManager.current() == FOREST
    assert ThemeManager.is_dark() is True


def test_all_stylesheets_are_unique():
    """Los 6 temas deben tener hojas de estilo distintas entre sí."""
    themes = ThemeManager._get_themes()
    stylesheets = [themes[t]["stylesheet"] for t in ALL_THEMES]
    assert len(set(stylesheets)) == len(ALL_THEMES), \
        "Dos o más temas comparten el mismo stylesheet exacto"


def test_all_palettes_have_required_tokens():
    """Todos los temas deben tener al menos los tokens base de DARK."""
    from core.themes.dark import DARK_PALETTE
    required = set(DARK_PALETTE.keys())
    themes = ThemeManager._get_themes()
    for name in ALL_THEMES:
        palette = themes[name]["palette"]
        missing = required - set(palette.keys())
        assert not missing, \
            f"Tema '{name}' le faltan tokens: {missing}"


def test_color_helper_returns_string():
    """ThemeManager.color() debe retornar un string hex para tokens conocidos."""
    for theme in ALL_THEMES:
        ThemeManager._current = theme
        val = ThemeManager.color("bg_app")
        assert isinstance(val, str) and val.startswith("#"), \
            f"color('bg_app') en tema '{theme}' no retornó hex: {val!r}"
