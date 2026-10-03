"""
presence_grid/place_picker.py - Popup selector de lugar para la Cuadricula de Presencias.

Contiene _PlacePickerDialog: dialogo con header de color, lista buscable de lugares
y pastillas de estado (Presente / En transito / Salida) para asignacion rapida.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QListWidget, QListWidgetItem, QWidget, QLineEdit,
)
from PyQt6.QtCore import Qt

from core.theme_manager import ThemeManager


# Opciones de estado disponibles para la presencia de un personaje
_STATUS_PILL_DEFS_DARK  = [
    ("present",  "Presente",    "#30d158"),
    ("transit",  "En transito", "#0a84ff"),
    ("departed", "Salida",      "#ff453a"),
]
_STATUS_PILL_DEFS_LIGHT = [
    ("present",  "Presente",    "#1a7a38"),
    ("transit",  "En transito", "#1a56b0"),
    ("departed", "Salida",      "#c41e0e"),
]


class _PlacePickerDialog(QDialog):
    """
    Popup que aparece al hacer clic en una celda de la cuadricula.
    Permite seleccionar el lugar donde aparece el personaje en ese capitulo
    y el tipo de presencia mediante pastillas clickeables.

    Atributos publicos tras exec():
      selected_place_id : str | None  -- ID del lugar seleccionado
      selected_type     : str         -- 'present' | 'transit' | 'departed'
      cleared           : bool        -- True si el usuario pulso "Limpiar"
    """

class _PlacePickerDialog(QDialog):
    """
    Popup que aparece al hacer clic en una celda de la cuadrícula.
    Permite seleccionar el lugar donde aparece el personaje en ese capítulo
    y el tipo de presencia mediante pastillas clickeables.
    """

    def __init__(
        self,
        char_name: str,
        cap_title: str,
        places: list,
        current_place_id: str | None,
        current_type: str | None,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Asignar ubicación de personaje")
        self.setFixedSize(390, 480)
        self.selected_place_id = current_place_id or None
        self.selected_type     = current_type or "present"
        self.cleared           = False
        
        tc = ThemeManager.theme_colors()
        self._tc = tc
        bg   = tc["bg_main"]
        fg   = tc["fg_text"]
        card = tc["bg_card"]
        bord = tc["border"]
        sub  = tc["subtext"]
        accent = tc["accent"]
        input_bg = tc["bg_input"]

        self.setStyleSheet(f"""
            QDialog {{ background: {bg}; }}
            QLabel {{ color: {fg}; }}
            QListWidget {{
                background: {input_bg}; border: 1px solid {bord};
                border-radius: 8px; color: {fg}; font-size: 12px; outline: none;
            }}
            QListWidget::item {{ padding: 9px 12px; border-bottom: 1px solid {bord}; }}
            QListWidget::item:selected {{ background: {accent}; color: #ffffff; border-radius: 4px; font-weight: bold; }}
            QListWidget::item:hover {{ background: {tc['hover']}; }}
            QLineEdit {{
                background: {input_bg}; border: 1px solid {bord};
                border-radius: 8px; color: {fg}; padding: 6px 12px; font-size: 12px;
            }}
            QLineEdit:focus {{ border-color: {accent}; }}
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # -- Header Elegante --------------------------------------------------
        hdr = QFrame()
        hdr.setFixedHeight(72)
        hdr.setStyleSheet(f"background: {card}; border-bottom: 1px solid {bord};")
        hdr_lay = QVBoxLayout(hdr)
        hdr_lay.setContentsMargins(20, 12, 20, 12)
        hdr_lay.setSpacing(3)

        name_lbl = QLabel(char_name)
        name_lbl.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {accent}; background: transparent;")
        hdr_lay.addWidget(name_lbl)

        cap_lbl = QLabel(f"Capítulo: {cap_title}")
        cap_lbl.setStyleSheet(f"font-size: 11px; color: {sub}; background: transparent; font-weight: 500;")
        cap_lbl.setWordWrap(True)
        hdr_lay.addWidget(cap_lbl)

        lay.addWidget(hdr)

        # -- Cuerpo -----------------------------------------------------------
        body = QWidget()
        body.setStyleSheet(f"background: {bg};")
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(18, 16, 18, 16)
        body_lay.setSpacing(12)

        # Buscador
        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍 Buscar lugar del universo...")
        self._search.setFixedHeight(36)
        self._search.textChanged.connect(self._filter_places)
        body_lay.addWidget(self._search)

        # Lista de lugares
        self._list = QListWidget()
        self._all_places = places
        self._populate_list(places, current_place_id)
        body_lay.addWidget(self._list, stretch=1)

        # -- Pastillas de estado ----------------------------------------------
        state_lbl = QLabel("TIPO DE PRESENCIA:")
        state_lbl.setStyleSheet(f"font-size: 10px; color: {sub}; font-weight: bold; letter-spacing: 0.8px;")
        body_lay.addWidget(state_lbl)

        pills_row = QHBoxLayout()
        pills_row.setSpacing(8)
        self._pill_btns: dict = {}

        pill_defs = [
            ("present",  "Presente",    tc["green"]),
            ("transit",  "En tránsito", tc["blue"]),
            ("departed", "Salida",      tc["red"]),
        ]

        for key, label, color in pill_defs:
            btn = QPushButton(label)
            btn.setFixedHeight(32)
            btn.setCheckable(True)
            btn.setProperty("pill_key", key)
            btn.setProperty("pill_color", color)
            btn.setChecked(key == self.selected_type)
            btn.clicked.connect(lambda _checked, k=key: self._on_pill_clicked(k))
            self._pill_btns[key] = btn
            pills_row.addWidget(btn)
        self._apply_pill_styles()
        body_lay.addLayout(pills_row)

        # -- Botones de acción ------------------------------------------------
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        btn_clear = QPushButton("Limpiar")
        btn_clear.setFixedHeight(36)
        btn_clear.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {bord};
                border-radius: 6px;
                color: {sub};
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                border-color: {tc['red']};
                color: {tc['red']};
                background: rgba(239, 68, 68, 0.08);
            }}
        """)
        btn_clear.clicked.connect(self._on_clear)
        btn_row.addWidget(btn_clear)

        btn_ok = QPushButton("Guardar Ubicación")
        btn_ok.setFixedHeight(36)
        btn_ok.setDefault(True)
        btn_ok.setStyleSheet(f"""
            QPushButton {{
                background: {accent};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """)
        btn_ok.clicked.connect(self._on_accept)
        btn_row.addWidget(btn_ok)
        body_lay.addLayout(btn_row)

        lay.addWidget(body, stretch=1)


    # -- Metodos internos -----------------------------------------------------

    def _on_pill_clicked(self, key: str) -> None:
        self.selected_type = key
        for k, btn in self._pill_btns.items():
            btn.setChecked(k == key)
        self._apply_pill_styles()

    def _apply_pill_styles(self) -> None:
        for btn in self._pill_btns.values():
            color = btn.property("pill_color")
            if btn.isChecked():
                btn.setStyleSheet(
                    f"QPushButton {{ background: {color}; color: #ffffff; border: 2px solid {color}; "
                    f"border-radius: 8px; font-weight: bold; font-size: 11px; }}"
                    f"QPushButton:hover {{ background: {color}cc; }}"
                )
            else:
                btn.setStyleSheet(
                    f"QPushButton {{ background: transparent; color: {color}; border: 1.5px solid {color}66; "
                    f"border-radius: 8px; font-size: 11px; }}"
                    f"QPushButton:hover {{ background: {color}18; border-color: {color}; }}"
                )

    def _populate_list(self, places: list, selected_id: str | None) -> None:
        self._list.clear()
        for p in places:
            item = QListWidgetItem(f"  {p.name}")
            item.setData(Qt.ItemDataRole.UserRole, p.id)
            self._list.addItem(item)
            if p.id == selected_id:
                self._list.setCurrentItem(item)

    def _filter_places(self, query: str) -> None:
        q = query.strip().lower()
        filtered = [p for p in self._all_places if q in p.name.lower()] if q else self._all_places
        self._populate_list(filtered, self.selected_place_id or "")

    def _on_accept(self) -> None:
        item = self._list.currentItem()
        if item:
            self.selected_place_id = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    def _on_clear(self) -> None:
        self.cleared = True
        self.accept()
