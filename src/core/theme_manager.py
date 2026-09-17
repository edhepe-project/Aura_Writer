"""
ThemeManager — Gestor de temas visuales de Aura Writer.
Proporciona los temas Oscuro (Dark) y Claro (Light) como hojas de estilo Qt,
y persiste la preferencia del usuario en un archivo de configuración local.
"""

from __future__ import annotations
import json
import os

# Ruta del archivo de preferencias (junto a main.py / al ejecutable)
_PREFS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "..", "aura_prefs.json")

DARK  = "dark"
LIGHT = "light"

# ======================================================================
# Paletas base
# ======================================================================

_SCROLLBARS = """
    QScrollBar:vertical {
        background: transparent; width: 7px; margin: 2px 1px;
    }
    QScrollBar::handle:vertical {
        background: {scroll_handle}; border-radius: 3px; min-height: 28px;
    }
    QScrollBar::handle:vertical:hover { background: {scroll_hover}; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }

    QScrollBar:horizontal {
        background: transparent; height: 7px; margin: 1px 2px;
    }
    QScrollBar::handle:horizontal {
        background: {scroll_handle}; border-radius: 3px; min-width: 28px;
    }
    QScrollBar::handle:horizontal:hover { background: {scroll_hover}; }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: none; }
"""

# ── Tema Oscuro (Apple dark / macOS style) ────────────────────────────
DARK_STYLESHEET = """
    * {
        font-family: "Segoe UI", system-ui, sans-serif;
        font-size: 13px;
    }
    QMainWindow, QDialog { 
        background-color: #1c1c1e; 
        color: #f2f2f7;
    }

    QMenuBar {
        background-color: #1c1c1e; color: #aeaeb2;
        border-bottom: 1px solid #3a3a3c; padding: 2px 0;
    }
    QMenuBar::item:selected { background: #2c2c2e; border-radius: 4px; }
    QMenu {
        background: #2c2c2e; color: #f2f2f7;
        border: 1px solid #3a3a3c; border-radius: 8px; padding: 4px;
    }
    QMenu::item { padding: 5px 20px; border-radius: 5px; }
    QMenu::item:selected { background: #3a3a3c; }
    QMenu::item:disabled { color: #636366; }
    QMenu::separator { height: 1px; background: #3a3a3c; margin: 3px 0; }

    QToolBar {
        background-color: #1c1c1e; border-bottom: 1px solid #3a3a3c;
        spacing: 4px; padding: 3px 6px;
    }
    QToolBar QToolButton {
        background: transparent; color: #aeaeb2;
        border: 1px solid transparent; border-radius: 6px; padding: 4px 8px;
    }
    QToolBar QToolButton:hover { background: #2c2c2e; color: #f2f2f7; }
    QToolBar QToolButton:pressed { background: #3a3a3c; }
    QToolBar QToolButton:checked { background: #3a3a3c; color: #ffd60a; border: 1px solid #ffd60a; }
    QToolBar QToolButton:checked:hover { background: #48484a; border-color: #ffe84d; }

    QStatusBar {
        background: #1c1c1e; color: #8e8e93;
        border-top: 1px solid #3a3a3c; font-size: 11px;
    }

    QPushButton {
        background: #2c2c2e; color: #f2f2f7;
        border: 1px solid #3a3a3c; border-radius: 8px;
        padding: 6px 14px; font-size: 13px;
    }
    QPushButton:hover   { background: #3a3a3c; }
    QPushButton:pressed { background: #48484a; }
    QPushButton:disabled { color: #48484a; background: #222224; }

    QLineEdit, QTextEdit, QPlainTextEdit {
        background: #2c2c2e; color: #f2f2f7;
        border: 1px solid #3a3a3c; border-radius: 8px;
        padding: 6px 10px; selection-background-color: #636366;
    }
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
        border: 1px solid #636366;
    }

    QComboBox {
        background: #2c2c2e; color: #f2f2f7;
        border: 1px solid #3a3a3c; border-radius: 8px; padding: 5px 10px;
    }
    QComboBox::drop-down { border: none; width: 20px; }
    QComboBox QAbstractItemView {
        background: #2c2c2e; color: #f2f2f7;
        border: 1px solid #3a3a3c; selection-background-color: #3a3a3c;
    }

    QSpinBox {
        background: #2c2c2e; color: #f2f2f7;
        border: 1px solid #3a3a3c; border-radius: 8px; padding: 4px 8px;
    }
    QSpinBox::up-button, QSpinBox::down-button { width: 0; }

    QSplitter::handle { background: #3a3a3c; }

    QGroupBox {
        color: #aeaeb2;
        border: 1px solid #3a3a3c;
        border-radius: 8px;
        margin-top: 10px;
        padding: 12px 10px 10px 10px;
        font-weight: bold;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
    }

    QCheckBox {
        color: #f2f2f7;
        spacing: 8px;
    }
    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        border: 2px solid #636366;
        border-radius: 4px;
        background: #2c2c2e;
    }
    QCheckBox::indicator:checked {
        background: #d4a017;
        border-color: #d4a017;
    }

    QRadioButton {
        color: #f2f2f7;
        spacing: 8px;
    }
    QRadioButton::indicator {
        width: 16px;
        height: 16px;
        border: 2px solid #636366;
        border-radius: 9px;
        background: #2c2c2e;
    }
    QRadioButton::indicator:hover {
        border-color: #d4a017;
    }
    QRadioButton::indicator:checked {
        background: #d4a017;
        border-color: #d4a017;
    }

    QTabWidget::pane {
        border: 1px solid #3a3a3c;
        background: #1c1c1e;
        border-radius: 6px;
    }
    QTabBar::tab {
        background: #2c2c2e;
        color: #8e8e93;
        border: 1px solid #3a3a3c;
        padding: 6px 14px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        margin-right: 2px;
    }
    QTabBar::tab:selected {
        background: #1c1c1e;
        color: #f2f2f7;
        border-bottom: 1px solid #1c1c1e;
    }

    QGraphicsView {
        background-color: #1c1c1e;
        border: none;
    }

    QScrollArea {
        background: transparent;
        border: none;
    }
    QScrollArea > QWidget > QWidget {
        background: transparent;
    }
    QScrollArea > .QWidget {
        background: transparent;
    }

    QTreeWidget, QTreeView {
        background: #1c1c1e; color: #f2f2f7; border: none; outline: none;
    }
    QTreeWidget::item, QTreeView::item { padding: 4px 6px; }
    QTreeWidget::item:selected, QTreeView::item:selected {
        background: #2c2c2e; color: #ffffff;
    }
    QTreeWidget::item:hover, QTreeView::item:hover { background: #2c2c2e; }
    QHeaderView::section {
        background: #2c2c2e; color: #8e8e93; border: none; padding: 5px;
    }

    QListWidget, QListView {
        background: #1c1c1e; color: #f2f2f7; border: none;
    }
    QListWidget::item, QListView::item { padding: 5px 8px; border-radius: 5px; }
    QListWidget::item:selected, QListView::item:selected { background: #2c2c2e; color: #ffffff; }
    QListWidget::item:hover, QListView::item:hover { background: #2c2c2e; }

    QTableWidget { background: #1c1c1e; color: #f2f2f7; border: none; }

    QFrame[frameShape="4"], QFrame[frameShape="5"] { color: #3a3a3c; }
    QLabel { color: #f2f2f7; background: transparent; }

    QToolTip {
        background: #2c2c2e; color: #f2f2f7;
    }
    QDialogButtonBox QPushButton { min-width: 80px; }

    QScrollBar:vertical { background: transparent; width: 7px; margin: 2px 1px; }
    QScrollBar::handle:vertical { background: #3a3a3c; border-radius: 3px; min-height: 28px; }
    QScrollBar::handle:vertical:hover { background: #636366; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
    QScrollBar:horizontal { background: transparent; height: 7px; margin: 1px 2px; }
    QScrollBar::handle:horizontal { background: #3a3a3c; border-radius: 3px; min-width: 28px; }
    QScrollBar::handle:horizontal:hover { background: #636366; }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: none; }

    QCheckBox { color: #aeaeb2; spacing: 6px; }
    QCheckBox::indicator {
        width: 15px; height: 15px;
        border: 1px solid #48484a;
        border-radius: 4px;
        background: #2c2c2e;
    }
    QCheckBox::indicator:hover { border-color: #636366; background: #3a3a3c; }
    QCheckBox::indicator:checked {
        background: #ffd60a;
        border-color: #ffd60a;
        image: none;
    }
    QCheckBox::indicator:checked:hover { background: #ffe234; border-color: #ffe234; }
"""

# ── Tema Claro (papel / diario literario) ────────────────────────────
LIGHT_STYLESHEET = """
    * {
        font-family: "Segoe UI", system-ui, sans-serif;
        font-size: 13px;
    }
    QMainWindow, QDialog { 
        background-color: #f5f0ea; 
        color: #1a1a2e;
    }

    QMenuBar {
        background-color: #ede8e1; color: #4a4a5a;
        border-bottom: 1px solid #d4cfc8; padding: 2px 0;
    }
    QMenuBar::item:selected { background: #dedad2; border-radius: 4px; }
    QMenu {
        background: #faf7f3; color: #1a1a2e;
        border: 1px solid #d4cfc8; border-radius: 8px; padding: 4px;
    }
    QMenu::item { padding: 5px 20px; border-radius: 5px; }
    QMenu::item:selected { background: #ede8e1; }
    QMenu::item:disabled { color: #a8a29e; }
    QMenu::separator { height: 1px; background: #d4cfc8; margin: 3px 0; }

    QToolBar {
        background-color: #ede8e1; border-bottom: 1px solid #d4cfc8;
        spacing: 4px; padding: 3px 6px;
    }
    QToolBar QToolButton {
        background: transparent; color: #4a4a5a;
        border: 1px solid transparent; border-radius: 6px; padding: 4px 8px;
    }
    QToolBar QToolButton:hover { background: #dedad2; color: #1a1a2e; }
    QToolBar QToolButton:pressed { background: #cfc9c0; }
    QToolBar QToolButton:checked { background: #dedad2; color: #9a5c00; border: 1px solid #b36e00; }
    QToolBar QToolButton:checked:hover { background: #cfc9c0; border-color: #804c00; }

    QStatusBar {
        background: #ede8e1; color: #7a7a8a;
        border-top: 1px solid #d4cfc8; font-size: 11px;
    }

    QPushButton {
        background: #ede8e1; color: #1a1a2e;
        border: 1px solid #c4bfb8; border-radius: 8px;
        padding: 6px 14px; font-size: 13px;
    }
    QPushButton:hover   { background: #dedad2; }
    QPushButton:pressed { background: #cfc9c0; }
    QPushButton:disabled { color: #b0aba4; background: #eae5de; }

    QLineEdit, QTextEdit, QPlainTextEdit {
        background: #faf7f3; color: #1a1a2e;
        border: 1px solid #c4bfb8; border-radius: 8px;
        padding: 6px 10px; selection-background-color: #c8c0b8;
    }
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
        border: 1px solid #9a9490;
    }

    QComboBox {
        background: #faf7f3; color: #1a1a2e;
        border: 1px solid #c4bfb8; border-radius: 8px; padding: 5px 10px;
    }
    QComboBox::drop-down { border: none; width: 20px; }
    QComboBox QAbstractItemView {
        background: #faf7f3; color: #1a1a2e;
        border: 1px solid #c4bfb8; selection-background-color: #ede8e1;
    }

    QSpinBox {
        background: #faf7f3; color: #1a1a2e;
        border: 1px solid #c4bfb8; border-radius: 8px; padding: 4px 8px;
    }
    QSpinBox::up-button, QSpinBox::down-button { width: 0; }

    QSplitter::handle { background: #d4cfc8; }

    QGroupBox {
        color: #4a4a5a;
        border: 1px solid #d4cfc8;
        border-radius: 8px;
        margin-top: 10px;
        padding: 12px 10px 10px 10px;
        font-weight: bold;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
    }

    QCheckBox, QRadioButton {
        color: #1a1a2e;
        spacing: 8px;
    }
    QCheckBox::indicator, QRadioButton::indicator {
        width: 16px;
        height: 16px;
        border: 2px solid #9a9490;
        border-radius: 4px;
        background: #faf7f3;
    }
    QCheckBox::indicator:checked, QRadioButton::indicator:checked {
        background: #d4a017;
        border-color: #d4a017;
    }

    QTabWidget::pane {
        border: 1px solid #d4cfc8;
        background: #f5f0ea;
        border-radius: 6px;
    }
    QTabBar::tab {
        background: #ede8e1;
        color: #7a7a8a;
        border: 1px solid #d4cfc8;
        padding: 6px 14px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        margin-right: 2px;
    }
    QTabBar::tab:selected {
        background: #f5f0ea;
        color: #1a1a2e;
        border-bottom: 1px solid #f5f0ea;
    }

    QGraphicsView {
        background-color: #f5f0ea;
        border: none;
    }

    QScrollArea {
        background: transparent;
        border: none;
    }
    QScrollArea > QWidget > QWidget {
        background: transparent;
    }
    QScrollArea > .QWidget {
        background: transparent;
    }

    QTreeWidget, QTreeView {
        background: #f5f0ea; color: #1a1a2e; border: none; outline: none;
    }
    QTreeWidget::item, QTreeView::item { padding: 4px 6px; }
    QTreeWidget::item:selected, QTreeView::item:selected {
        background: #dedad2; color: #1a1a2e;
    }
    QTreeWidget::item:hover, QTreeView::item:hover { background: #ede8e1; }
    QHeaderView::section {
        background: #ede8e1; color: #7a7a8a; border: none; padding: 5px;
    }

    QListWidget, QListView {
        background: #f5f0ea; color: #1a1a2e; border: none;
    }
    QListWidget::item, QListView::item { padding: 5px 8px; border-radius: 5px; }
    QListWidget::item:selected, QListView::item:selected { background: #dedad2; color: #1a1a2e; }
    QListWidget::item:hover, QListView::item:hover { background: #ede8e1; }

    QTableWidget { background: #f5f0ea; color: #1a1a2e; border: none; }

    QFrame[frameShape="4"], QFrame[frameShape="5"] { color: #d4cfc8; }
    QLabel { color: #1a1a2e; background: transparent; }

    QToolTip {
        background: #faf7f3; color: #1a1a2e;
    }
    QDialogButtonBox QPushButton { min-width: 80px; }

    QScrollBar:vertical { background: transparent; width: 7px; margin: 2px 1px; }
    QScrollBar::handle:vertical { background: #c4bfb8; border-radius: 3px; min-height: 28px; }
    QScrollBar::handle:vertical:hover { background: #9a9490; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
    QScrollBar:horizontal { background: transparent; height: 7px; margin: 1px 2px; }
    QScrollBar::handle:horizontal { background: #c4bfb8; border-radius: 3px; min-width: 28px; }
    QScrollBar::handle:horizontal:hover { background: #9a9490; }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: none; }

    QCheckBox { color: #4a4a5a; spacing: 6px; }
    QCheckBox::indicator {
        width: 15px; height: 15px;
        border: 1px solid #b4afa8;
        border-radius: 4px;
        background: #f5f0ea;
    }
    QCheckBox::indicator:hover { border-color: #8a8580; background: #ede8e1; }
    QCheckBox::indicator:checked {
        background: #9a5c00;
        border-color: #9a5c00;
        image: none;
    }
    QCheckBox::indicator:checked:hover { background: #b36e00; border-color: #b36e00; }

    QRadioButton { color: #1a1a2e; spacing: 8px; }
    QRadioButton::indicator {
        width: 16px; height: 16px;
        border: 2px solid #b4afa8;
        border-radius: 9px;
        background: #faf7f3;
    }
    QRadioButton::indicator:hover { border-color: #d4a017; }
    QRadioButton::indicator:checked {
        border: 2px solid #d4a017;
        background: #d4a017;
    }
"""


# ======================================================================
# ThemeManager
# ======================================================================

class ThemeManager:
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
