"""
sepia.py — Hoja de estilo Qt para el tema Sepia / Pergamino Vintage.
Diseñado para una experiencia de lectura y redacción descansada con tono papel cálido.
"""

SEPIA_STYLESHEET = """
    * {
        font-family: "Segoe UI", system-ui, sans-serif;
        font-size: 13px;
    }
    QMainWindow, QDialog, QDockWidget {
        background-color: #f4ecd8;
        color: #2d241e;
    }
    QWidget {
        color: #2d241e;
    }
    QDockWidget::title {
        background-color: #ebdcb9;
        color: #2d241e;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
    }

    QMenuBar {
        background-color: #f4ecd8; color: #5c4d41;
        border-bottom: 1px solid #d8c8a8; padding: 2px 0;
    }
    QMenuBar::item:selected { background: #e8dbb8; border-radius: 4px; }
    QMenu {
        background: #fcf8ee; color: #2d241e;
        border: 1px solid #d8c8a8; border-radius: 8px; padding: 4px;
    }
    QMenu::item { padding: 6px 20px; border-radius: 5px; }
    QMenu::item:selected { background: #ebdcb9; }
    QMenu::item:disabled { color: #a39585; }
    QMenu::separator { height: 1px; background: #d8c8a8; margin: 3px 0; }

    QToolBar {
        background-color: #f4ecd8; border-bottom: 1px solid #d8c8a8;
        spacing: 4px; padding: 4px 8px;
    }
    QToolBar QToolButton {
        background: transparent; color: #5c4d41;
        border: 1px solid transparent; border-radius: 6px; padding: 5px 9px;
    }
    QToolBar QToolButton:hover { background: #ebdcb9; color: #2d241e; }
    QToolBar QToolButton:pressed { background: #d8c8a8; }
    QToolBar QToolButton:checked { background: #ebdcb9; color: #b45309; border: 1px solid #b45309; }
    QToolBar QToolButton:checked:hover { background: #d8c8a8; border-color: #92400e; }

    QStatusBar {
        background: #f4ecd8; color: #6b5b4e;
        border-top: 1px solid #d8c8a8; font-size: 11px;
    }

    QPushButton {
        background: #fcf8ee; color: #2d241e;
        border: 1px solid #cbb894; border-radius: 8px;
        padding: 6px 16px; font-size: 13px; font-weight: 500;
    }
    QPushButton:hover   { background: #ebdcb9; border-color: #b45309; }
    QPushButton:pressed { background: #d8c8a8; }
    QPushButton:disabled { color: #a39585; background: #ebdcb9; border-color: transparent; }

    QLineEdit, QTextEdit, QPlainTextEdit, QTextBrowser {
        background-color: #fcf8ee; color: #2d241e;
        border: 1px solid #cbb894; border-radius: 8px;
        padding: 6px 10px; selection-background-color: #ebdcb9;
        selection-color: #2d241e;
    }
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QTextBrowser:focus {
        border: 1px solid #b45309;
    }

    QComboBox {
        background: #fcf8ee; color: #2d241e;
        border: 1px solid #cbb894; border-radius: 8px; padding: 5px 10px;
    }
    QComboBox::drop-down { border: none; width: 20px; }
    QComboBox QAbstractItemView {
        background: #fcf8ee; color: #2d241e;
        border: 1px solid #cbb894; selection-background-color: #ebdcb9;
        selection-color: #2d241e;
    }

    QSpinBox {
        background: #fcf8ee; color: #2d241e;
        border: 1px solid #cbb894; border-radius: 8px; padding: 4px 8px;
    }
    QSpinBox::up-button, QSpinBox::down-button { width: 0; }

    QTreeWidget, QListView, QTableWidget, QListWidget {
        background-color: #fcf8ee; color: #2d241e;
        border: 1px solid #cbb894; border-radius: 8px; outline: none;
    }
    QTreeWidget::item:hover, QListView::item:hover, QListWidget::item:hover {
        background-color: #ebdcb9; border-radius: 6px;
    }
    QTreeWidget::item:selected, QListView::item:selected, QListWidget::item:selected {
        background-color: #d8c8a8; color: #2d241e; border-radius: 6px;
    }

    QHeaderView::section {
        background-color: #ebdcb9; color: #2d241e;
        font-weight: 600; font-size: 11px;
        border: none; border-bottom: 1px solid #cbb894; padding: 4px 8px;
    }

    QTabWidget::pane {
        border: 1px solid #cbb894; border-radius: 8px;
        background-color: #fcf8ee;
    }
    QTabBar::tab {
        background: #f4ecd8; color: #5c4d41;
        border: 1px solid #d8c8a8; border-bottom: none;
        border-top-left-radius: 6px; border-top-right-radius: 6px;
        padding: 6px 14px; margin-right: 2px; font-weight: 500;
    }
    QTabBar::tab:selected {
        background: #fcf8ee; color: #b45309; font-weight: 600;
        border-color: #cbb894;
    }
    QTabBar::tab:hover:!selected { background: #ebdcb9; }

    QScrollArea, QStackedWidget {
        background-color: #f4ecd8;
        border: none;
    }

    QScrollBar:vertical {
        background: transparent; width: 6px; margin: 0;
    }
    QScrollBar::handle:vertical {
        background: #cbb894; border-radius: 3px; min-height: 20px;
    }
    QScrollBar::handle:vertical:hover { background: #b45309; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        height: 0; background: transparent;
    }

    QScrollBar:horizontal {
        background: transparent; height: 6px; margin: 0;
    }
    QScrollBar::handle:horizontal {
        background: #cbb894; border-radius: 3px; min-width: 20px;
    }
    QScrollBar::handle:horizontal:hover { background: #b45309; }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
        width: 0; background: transparent;
    }

    QSplitter::handle { background-color: #d8c8a8; }

    QGroupBox {
        font-weight: 600; font-size: 11px; color: #5c4d41;
        border: 1px solid #d8c8a8; border-radius: 8px;
        margin-top: 10px; padding-top: 10px;
    }
    QGroupBox::title {
        subcontrol-origin: margin; subcontrol-position: top left;
        left: 10px; padding: 0 4px; background-color: #f4ecd8;
    }

    QToolTip {
        background-color: #fcf8ee; color: #2d241e;
        border: 1px solid #cbb894; border-radius: 6px; padding: 4px 8px;
    }

    QCheckBox, QRadioButton {
        color: #2d241e; spacing: 6px;
    }
    QCheckBox::indicator, QRadioButton::indicator {
        width: 14px; height: 14px; border: 1px solid #cbb894;
        background: #fcf8ee; border-radius: 3px;
    }
    QCheckBox::indicator:checked, QRadioButton::indicator:checked {
        background: #b45309; border-color: #b45309;
    }
"""
