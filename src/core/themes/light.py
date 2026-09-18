"""
light.py — Hoja de estilo Qt para el tema Claro (papel / diario literario).
"""

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
