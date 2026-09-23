"""
Tests unitarios para ThemeManager.
Valida la paleta de colores, el toggle de temas y que los stylesheets no estén vacíos.
"""
import pytest
from core.theme_manager import ThemeManager, DARK, LIGHT


def setup_function():
    """Resetear al tema oscuro antes de cada test para aislamiento."""
    ThemeManager._current = DARK


def test_default_theme_is_dark():
    assert ThemeManager.current() == DARK
    assert ThemeManager.is_dark() is True


def test_stylesheets_are_not_empty():
    dark_ss = ThemeManager.STYLESHEETS[DARK]
    light_ss = ThemeManager.STYLESHEETS[LIGHT]
    assert isinstance(dark_ss, str) and len(dark_ss) > 100
    assert isinstance(light_ss, str) and len(light_ss) > 100


def test_stylesheets_contain_basic_css_selectors():
    for name, ss in ThemeManager.STYLESHEETS.items():
        assert "QWidget" in ss or "QMainWindow" in ss or "background" in ss, \
            f"Stylesheet '{name}' parece no contener CSS válido"


def test_is_dark_returns_correct_value():
    ThemeManager._current = DARK
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
    assert result == LIGHT
    assert ThemeManager.current() == LIGHT

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


def test_both_stylesheets_are_different():
    """Dark y Light deben ser hojas de estilo distintas."""
    assert ThemeManager.STYLESHEETS[DARK] != ThemeManager.STYLESHEETS[LIGHT]
