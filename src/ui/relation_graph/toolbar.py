"""
_GraphToolbar: Top toolbar for RelationGraphWidget.
Houses title, character search completer, relation filter combo, and zoom controls.
"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QToolButton, QCompleter, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QCursor
import qtawesome as qta


class _GraphToolbar(QWidget):
    search_submitted = pyqtSignal(str)
    character_selected = pyqtSignal(str)
    filter_changed = pyqtSignal(str)
    zoom_in_requested = pyqtSignal()
    zoom_out_requested = pyqtSignal()
    zoom_fit_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(46)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("GraphToolbar")
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(10)

        # Title / Label
        self.title_label = QLabel("Red de Relaciones")
        self.title_label.setStyleSheet("""
            font-size: 13px;
            font-weight: 700;
            color: #f5f5f7;
            letter-spacing: 0.3px;
        """)
        layout.addWidget(self.title_label)

        layout.addStretch()

        # Search Bar with Completer
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar personaje...")
        self.search_input.setFixedWidth(160)
        self.search_input.setFixedHeight(28)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: #2c2c2e;
                color: #f5f5f7;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 6px;
                padding: 0 10px;
                font-size: 11px;
                font-weight: 500;
            }
            QLineEdit:focus {
                border: 1px solid #ffd60a;
                background: #3a3a3c;
            }
        """)
        self.search_input.returnPressed.connect(self._on_search_enter)
        layout.addWidget(self.search_input)

        # Character Selector ComboBox
        self.char_combo = QComboBox()
        self.char_combo.setFixedHeight(28)
        self.char_combo.setMinimumWidth(160)
        self.char_combo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.char_combo.setStyleSheet(self._combo_style())
        self.char_combo.currentIndexChanged.connect(self._on_char_combo_changed)
        layout.addWidget(self.char_combo)

        # Relation Type Filter ComboBox
        self.combo = QComboBox()
        self.combo.setFixedHeight(28)
        self.combo.setMinimumWidth(140)
        self.combo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.combo.setStyleSheet(self._combo_style())
        self.combo.currentTextChanged.connect(self._on_filter_changed)
        layout.addWidget(self.combo)

        # Separator
        sep = QLabel("|")
        sep.setStyleSheet("color: rgba(255, 255, 255, 0.15); font-size: 12px; margin: 0 2px;")
        layout.addWidget(sep)

        # Zoom Out Button
        self.btn_out = QToolButton()
        self.btn_out.setIcon(qta.icon("fa5s.search-minus", color="#d1d1d6"))
        self.btn_out.setToolTip("Alejar (Ctrl + Rueda)")
        self.btn_out.setFixedSize(28, 28)
        self.btn_out.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_out.setStyleSheet(self._btn_style())
        self.btn_out.clicked.connect(self.zoom_out_requested.emit)
        layout.addWidget(self.btn_out)

        # Zoom In Button
        self.btn_in = QToolButton()
        self.btn_in.setIcon(qta.icon("fa5s.search-plus", color="#d1d1d6"))
        self.btn_in.setToolTip("Acercar (Ctrl + Rueda)")
        self.btn_in.setFixedSize(28, 28)
        self.btn_in.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_in.setStyleSheet(self._btn_style())
        self.btn_in.clicked.connect(self.zoom_in_requested.emit)
        layout.addWidget(self.btn_in)

        # Zoom Fit / Reset Button
        self.btn_fit = QToolButton()
        self.btn_fit.setIcon(qta.icon("fa5s.expand-arrows-alt", color="#d1d1d6"))
        self.btn_fit.setToolTip("Restaurar vista (Doble clic en el fondo)")
        self.btn_fit.setFixedSize(28, 28)
        self.btn_fit.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_fit.setStyleSheet(self._btn_style())
        self.btn_fit.clicked.connect(self.zoom_fit_requested.emit)
        layout.addWidget(self.btn_fit)

    def _combo_style(self) -> str:
        return """
            QComboBox {
                background: #2c2c2e;
                color: #f5f5f7;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 6px;
                padding: 0 12px 0 10px;
                font-size: 11px;
                font-weight: 500;
            }
            QComboBox:hover {
                border-color: rgba(255, 255, 255, 0.25);
                background: #3a3a3c;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #8e8e93;
                margin-right: 6px;
            }
            QComboBox QAbstractItemView {
                background: #1c1c1e;
                color: #f5f5f7;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 6px;
                selection-background-color: #ffd60a;
                selection-color: #000000;
                padding: 4px;
                outline: none;
            }
        """

    def set_characters_list(self, characters: list):
        """Puebla el ComboBox con todos los personajes disponibles."""
        self.char_combo.blockSignals(True)
        self.char_combo.clear()
        self.char_combo.addItem("👤 Seleccionar personaje...", "")
        for ch in characters:
            cid = str(ch.get("id") if isinstance(ch, dict) else getattr(ch, "id", ""))
            name = str(ch.get("name") if isinstance(ch, dict) else getattr(ch, "name", ""))
            if name:
                self.char_combo.addItem(f"👤 {name}", cid)
        self.char_combo.blockSignals(False)

    def select_character_id(self, char_id: str):
        self.char_combo.blockSignals(True)
        idx = self.char_combo.findData(str(char_id))
        if idx >= 0:
            self.char_combo.setCurrentIndex(idx)
        else:
            self.char_combo.setCurrentIndex(0)
        self.char_combo.blockSignals(False)

    def _on_char_combo_changed(self, index: int):
        cid = self.char_combo.currentData()
        if cid:
            self.character_selected.emit(str(cid))
        elif index == 0:
            self.character_selected.emit("")

    def set_completer_model(self, names: list):
        completer = QCompleter(names, self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        if completer.popup():
            completer.popup().setStyleSheet("""
                QListView {
                    background: #1c1c1e;
                    color: #f5f5f7;
                    border: 1px solid rgba(255, 255, 255, 0.15);
                    border-radius: 6px;
                    padding: 4px;
                    selection-background-color: #ffd60a;
                    selection-color: #000000;
                    font-size: 11px;
                }
            """)
        completer.activated.connect(self.search_submitted.emit)
        self.search_input.setCompleter(completer)

    def _on_search_enter(self):
        text = self.search_input.text().strip()
        if text:
            self.search_submitted.emit(text)

    def _on_filter_changed(self, text: str):
        self.filter_changed.emit(text)

    def update_theme(self, is_dark: bool):
        bg = "#161618" if is_dark else "#f2f2f7"
        border = "rgba(255, 255, 255, 0.08)" if is_dark else "rgba(0, 0, 0, 0.08)"
        text_color = "#f5f5f7" if is_dark else "#1c1c1e"
        inp_bg = "#2c2c2e" if is_dark else "#ffffff"
        inp_border = "rgba(255, 255, 255, 0.12)" if is_dark else "rgba(0, 0, 0, 0.12)"
        icon_color = "#d1d1d6" if is_dark else "#3a3a3c"

        self.setStyleSheet(f"""
            #GraphToolbar {{
                background: {bg};
                border-bottom: 1px solid {border};
            }}
        """)
        self.title_label.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 700;
            color: {text_color};
            letter-spacing: 0.3px;
        """)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background: {inp_bg};
                color: {text_color};
                border: 1px solid {inp_border};
                border-radius: 6px;
                padding: 0 10px;
                font-size: 11px;
                font-weight: 500;
            }}
            QLineEdit:focus {{
                border: 1px solid #ffd60a;
                background: {'#3a3a3c' if is_dark else '#ffffff'};
            }}
        """)
        self.combo.setStyleSheet(f"""
            QComboBox {{
                background: {inp_bg};
                color: {text_color};
                border: 1px solid {inp_border};
                border-radius: 6px;
                padding: 0 12px 0 10px;
                font-size: 11px;
                font-weight: 500;
            }}
            QComboBox:hover {{
                border-color: {'rgba(255, 255, 255, 0.25)' if is_dark else 'rgba(0, 0, 0, 0.25)'};
                background: {'#3a3a3c' if is_dark else '#f5f5f7'};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #8e8e93;
                margin-right: 6px;
            }}
            QComboBox QAbstractItemView {{
                background: {bg};
                color: {text_color};
                border: 1px solid {inp_border};
                border-radius: 6px;
                selection-background-color: #ffd60a;
                selection-color: #000000;
                padding: 4px;
                outline: none;
            }}
        """)
        btn_style = self._btn_style(is_dark)
        self.btn_out.setIcon(qta.icon("fa5s.search-minus", color=icon_color))
        self.btn_out.setStyleSheet(btn_style)
        self.btn_in.setIcon(qta.icon("fa5s.search-plus", color=icon_color))
        self.btn_in.setStyleSheet(btn_style)
        self.btn_fit.setIcon(qta.icon("fa5s.expand-arrows-alt", color=icon_color))
        self.btn_fit.setStyleSheet(btn_style)

    def _btn_style(self, is_dark: bool = True) -> str:
        bg = "#2c2c2e" if is_dark else "#e5e5ea"
        bg_hover = "#3a3a3c" if is_dark else "#d1d1d6"
        border = "rgba(255, 255, 255, 0.12)" if is_dark else "rgba(0, 0, 0, 0.12)"
        return f"""
            QToolButton {{
                background: {bg};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 4px;
            }}
            QToolButton:hover {{
                background: {bg_hover};
                border-color: #ffd60a;
            }}
            QToolButton:pressed {{
                background: #ffd60a;
            }}
        """
