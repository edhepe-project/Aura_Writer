"""
dark.py — Hoja de estilo Qt para el tema Oscuro (Apple dark / macOS style).
"""

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
