"""
Tests unitarios para ThemeManager.
Valida la paleta de colores, el toggle de temas y que los stylesheets no estén vacíos.
"""
import pytest
from core.theme_manager import ThemeManager, DARK, LIGHT, SEPIA, NORDIC


def setup_function():
    """Resetear al tema oscuro antes de cada test para aislamiento."""
    ThemeManager._current = DARK


def test_default_theme_is_dark():
    assert ThemeManager.current() == DARK
    assert ThemeManager.is_dark() is True


def test_stylesheets_are_not_empty():
    themes = ThemeManager._get_themes()
    dark_ss = themes[DARK]["stylesheet"]
    light_ss = themes[LIGHT]["stylesheet"]
    sepia_ss = themes[SEPIA]["stylesheet"]
    nordic_ss = themes[NORDIC]["stylesheet"]
    assert isinstance(dark_ss, str) and len(dark_ss) > 100
    assert isinstance(light_ss, str) and len(light_ss) > 100
    assert isinstance(sepia_ss, str) and len(sepia_ss) > 100
    assert isinstance(nordic_ss, str) and len(nordic_ss) > 100


def test_stylesheets_contain_basic_css_selectors():
    themes = ThemeManager._get_themes()
    for name, data in themes.items():
        ss = data["stylesheet"]
        assert "QWidget" in ss or "QMainWindow" in ss or "background" in ss, \
            f"Stylesheet '{name}' parece no contener CSS válido"


def test_is_dark_returns_correct_value():
    ThemeManager._current = DARK
    assert ThemeManager.is_dark() is True

    ThemeManager._current = NORDIC
    assert ThemeManager.is_dark() is True

    ThemeManager._current = LIGHT
    assert ThemeManager.is_dark() is False


def test_current_returns_active_theme():
    ThemeManager._current = LIGHT
    assert ThemeManager.current() == LIGHT

    ThemeManager._current = DARK
    assert ThemeManager.current() == DARK


def test_toggle_switches_theme(qtbot):
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()

    ThemeManager._current = DARK
    result = ThemeManager.toggle(app)
    assert result == "forest"
    assert ThemeManager.current() == "forest"

    result = ThemeManager.toggle(app)
    assert result == "dracula"
    assert ThemeManager.current() == "dracula"

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


def test_all_stylesheets_are_different():
    """Dark, Light, Sepia y Nordic deben ser hojas de estilo distintas."""
    themes = ThemeManager._get_themes()
    stylesheets = [themes[t]["stylesheet"] for t in [DARK, LIGHT, SEPIA, NORDIC]]
    assert len(set(stylesheets)) == 4
