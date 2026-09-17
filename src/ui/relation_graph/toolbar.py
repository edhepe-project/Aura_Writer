import os
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QToolButton, QCompleter, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QColor, QCursor, QPixmap, QPainter, QPolygonF
import qtawesome as qta


def _get_arrow_icon_path(is_dark: bool) -> str:
    color_name = "dark" if is_dark else "light"
    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    os.makedirs(assets_dir, exist_ok=True)
    icon_path = os.path.join(assets_dir, f"combo_arrow_{color_name}.png")
    
    pixmap = QPixmap(16, 16)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    arrow_color = QColor("#8e8e93" if is_dark else "#5c5c66")
    painter.setBrush(arrow_color)
    painter.setPen(Qt.PenStyle.NoPen)
    
    points = [QPointF(3.5, 6.0), QPointF(12.5, 6.0), QPointF(8.0, 11.0)]
    painter.drawPolygon(QPolygonF(points))
    painter.end()
    
    pixmap.save(icon_path, "PNG")
    return icon_path.replace("\\", "/")


class _GraphToolbar(QWidget):
    search_submitted = pyqtSignal(str)
    character_selected = pyqtSignal(str)
    filter_changed = pyqtSignal(str)
    show_all_edges_toggled = pyqtSignal(bool)
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

        # Checkbox: Mostrar todas las líneas
        self.chk_show_all = QCheckBox("Mostrar todas las líneas")
        self.chk_show_all.setChecked(False)
        self.chk_show_all.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.chk_show_all.setToolTip("Activa o desactiva la visibilidad global de las líneas de relación.")
        self.chk_show_all.setStyleSheet("""
            QCheckBox {
                color: #e5e5ea;
                font-size: 11px;
                font-weight: 600;
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1.5px solid rgba(255, 255, 255, 0.30);
                background: #2c2c2e;
            }
            QCheckBox::indicator:hover {
                border-color: #ffd60a;
                background: #3a3a3c;
            }
            QCheckBox::indicator:checked {
                background: #ffd60a;
                border-color: #ffd60a;
                /* Checkmark dibujado con border-trick: flecha diagonal */
                image: none;
            }
            QCheckBox::indicator:checked:hover {
                background: #ffe84d;
                border-color: #ffe84d;
            }
        """)
        # Usar stateChanged en lugar de toggled para mayor fiabilidad
        self.chk_show_all.stateChanged.connect(
            lambda state: self.show_all_edges_toggled.emit(state == 2)  # 2 = Qt.Checked
        )
        layout.addWidget(self.chk_show_all)

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

    def _combo_style(self, is_dark: bool = True) -> str:
        bg = "#2c2c2e" if is_dark else "#faf7f3"
        hover_bg = "#3a3a3c" if is_dark else "#ede8e1"
        fg = "#f5f5f7" if is_dark else "#1a1a2e"
        border = "#3a3a3c" if is_dark else "#c4bfb8"
        hover_border = "#ffd60a" if is_dark else "#9a5c00"
        popup_bg = "#1c1c1e" if is_dark else "#faf7f3"
        popup_border = "#3a3a3c" if is_dark else "#d4cfc8"
        sel_bg = "#ffd60a" if is_dark else "#ede8e1"
        sel_fg = "#000000" if is_dark else "#1a1a2e"
        tip_bg = "#2c2c2e" if is_dark else "#faf7f3"
        tip_fg = "#f2f2f7" if is_dark else "#1a1a2e"
        tip_border = "#3a3a3c" if is_dark else "#c4bfb8"
        arrow_icon = _get_arrow_icon_path(is_dark)

        return f"""
            QToolTip {{
                background-color: {tip_bg};
                color: {tip_fg};
                border: 1px solid {tip_border};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }}
            QComboBox {{
                background: {bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 0 24px 0 10px;
                font-size: 11px;
                font-weight: 500;
            }}
            QComboBox:hover {{
                border-color: {hover_border};
                background: {hover_bg};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 22px;
                border: none;
            }}
            QComboBox::down-arrow {{
                image: url("{arrow_icon}");
                width: 10px;
                height: 10px;
            }}
            QComboBox QAbstractItemView {{
                background: {popup_bg};
                color: {fg};
                border: 1px solid {popup_border};
                border-radius: 6px;
                selection-background-color: {sel_bg};
                selection-color: {sel_fg};
                padding: 4px;
                outline: none;
            }}
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
        idx = self.char_combo.findData(char_id)
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
        self._update_completer_style(completer)
        completer.activated.connect(self.search_submitted.emit)
        self.search_input.setCompleter(completer)

    def _update_completer_style(self, completer: QCompleter | None = None):
        if completer is None:
            completer = self.search_input.completer()
        if completer and completer.popup():
            from core.theme_manager import ThemeManager
            is_dark = ThemeManager.is_dark()
            bg = "#1c1c1e" if is_dark else "#faf7f3"
            fg = "#f5f5f7" if is_dark else "#1a1a2e"
            border = "#3a3a3c" if is_dark else "#c4bfb8"
            sel_bg = "#ffd60a" if is_dark else "#ede8e1"
            sel_fg = "#000000" if is_dark else "#1a1a2e"
            completer.popup().setStyleSheet(f"""
                QListView {{
                    background: {bg};
                    color: {fg};
                    border: 1px solid {border};
                    border-radius: 6px;
                    padding: 4px;
                    selection-background-color: {sel_bg};
                    selection-color: {sel_fg};
                    font-size: 11px;
                }}
            """)

    def _on_search_enter(self):
        text = self.search_input.text().strip()
        if text:
            self.search_submitted.emit(text)

    def _on_filter_changed(self, text: str):
        self.filter_changed.emit(text)

    def update_theme(self, is_dark: bool):
        bg = "#161618" if is_dark else "#ede8e1"
        border = "#3a3a3c" if is_dark else "#d4cfc8"
        text_color = "#f5f5f7" if is_dark else "#1a1a2e"
        inp_bg = "#2c2c2e" if is_dark else "#faf7f3"
        inp_border = "#3a3a3c" if is_dark else "#c4bfb8"
        icon_color = "#d1d1d6" if is_dark else "#4a4a5a"
        accent_focus = "#ffd60a" if is_dark else "#9a5c00"
        tip_bg = "#2c2c2e" if is_dark else "#faf7f3"
        tip_fg = "#f2f2f7" if is_dark else "#1a1a2e"
        tip_border = "#3a3a3c" if is_dark else "#c4bfb8"

        self.setStyleSheet(f"""
            QToolTip {{
                background-color: {tip_bg};
                color: {tip_fg};
                border: 1px solid {tip_border};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }}
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

        # Checkbox: Mostrar todas las líneas
        chk_color = "#e5e5ea" if is_dark else "#1a1a2e"
        chk_bg = "#2c2c2e" if is_dark else "#faf7f3"
        chk_border = "rgba(255, 255, 255, 0.30)" if is_dark else "#b4afa8"
        chk_hover_border = "#ffd60a" if is_dark else "#9a5c00"
        chk_hover_bg = "#3a3a3c" if is_dark else "#ede8e1"
        chk_checked_bg = "#ffd60a" if is_dark else "#9a5c00"

        self.chk_show_all.setStyleSheet(f"""
            QToolTip {{
                background-color: {tip_bg};
                color: {tip_fg};
                border: 1px solid {tip_border};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }}
            QCheckBox {{
                color: {chk_color};
                font-size: 11px;
                font-weight: 600;
                spacing: 6px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1.5px solid {chk_border};
                background: {chk_bg};
            }}
            QCheckBox::indicator:hover {{
                border-color: {chk_hover_border};
                background: {chk_hover_bg};
            }}
            QCheckBox::indicator:checked {{
                background: {chk_checked_bg};
                border-color: {chk_checked_bg};
                image: none;
            }}
            QCheckBox::indicator:checked:hover {{
                background: {'#ffe84d' if is_dark else '#b36e00'};
                border-color: {'#ffe84d' if is_dark else '#b36e00'};
            }}
        """)

        self.search_input.setStyleSheet(f"""
            QToolTip {{
                background-color: {tip_bg};
                color: {tip_fg};
                border: 1px solid {tip_border};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }}
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
                border: 1px solid {accent_focus};
                background: {'#3a3a3c' if is_dark else '#ffffff'};
            }}
        """)

        combo_css = self._combo_style(is_dark)
        self.char_combo.setStyleSheet(combo_css)
        self.combo.setStyleSheet(combo_css)

        btn_style = self._btn_style(is_dark)
        self.btn_out.setIcon(qta.icon("fa5s.search-minus", color=icon_color))
        self.btn_out.setStyleSheet(btn_style)
        self.btn_in.setIcon(qta.icon("fa5s.search-plus", color=icon_color))
        self.btn_in.setStyleSheet(btn_style)
        self.btn_fit.setIcon(qta.icon("fa5s.expand-arrows-alt", color=icon_color))
        self.btn_fit.setStyleSheet(btn_style)

        self._update_completer_style()

    def _btn_style(self, is_dark: bool = True) -> str:
        bg = "#2c2c2e" if is_dark else "#ede8e1"
        bg_hover = "#3a3a3c" if is_dark else "#dedad2"
        border = "#3a3a3c" if is_dark else "#c4bfb8"
        accent_hover = "#ffd60a" if is_dark else "#9a5c00"
        tip_bg = "#2c2c2e" if is_dark else "#faf7f3"
        tip_fg = "#f2f2f7" if is_dark else "#1a1a2e"
        tip_border = "#3a3a3c" if is_dark else "#c4bfb8"

        return f"""
            QToolTip {{
                background-color: {tip_bg};
                color: {tip_fg};
                border: 1px solid {tip_border};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }}
            QToolButton {{
                background: {bg};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 4px;
            }}
            QToolButton:hover {{
                background: {bg_hover};
                border-color: {accent_hover};
            }}
            QToolButton:pressed {{
                background: {accent_hover};
            }}
        """
