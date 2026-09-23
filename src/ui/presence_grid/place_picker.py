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

    def __init__(
        self,
        char_name: str,
        cap_title: str,
        places: list,
        current_place_id: str | None,
        current_type: str | None,
        is_dark: bool,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Asignar ubicacion")
        self.setFixedSize(380, 460)
        self.selected_place_id = current_place_id or None
        self.selected_type     = current_type or "present"
        self.cleared           = False
        self._is_dark          = is_dark

        bg   = "#1c1c1e" if is_dark else "#f8f9fc"
        fg   = "#f2f2f7" if is_dark else "#1a1d23"
        card = "#2c2c2e" if is_dark else "#ffffff"
        bord = "#3a3a3c" if is_dark else "#c8d0dc"
        sub  = "#8e8e93" if is_dark else "#5a6a8a"

        self.setStyleSheet(f"""
            QDialog {{ background: {bg}; }}
            QLabel {{ color: {fg}; }}
            QListWidget {{
                background: {card}; border: 1px solid {bord};
                border-radius: 8px; color: {fg}; font-size: 12px; outline: none;
            }}
            QListWidget::item {{ padding: 9px 12px; border-bottom: 1px solid {bord}; }}
            QListWidget::item:selected {{ background: #0a84ff; color: #fff; border-radius: 4px; }}
            QListWidget::item:hover {{ background: {'#3a3a3c' if is_dark else '#eef1f8'}; }}
            QLineEdit {{
                background: {card}; border: 1px solid {bord};
                border-radius: 8px; color: {fg}; padding: 5px 10px; font-size: 12px;
            }}
            QLineEdit:focus {{ border-color: #0a84ff; }}
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # -- Header de color --------------------------------------------------
        hdr_bg = "#1a2a3a" if is_dark else "#3d5a8a"
        hdr = QFrame()
        hdr.setFixedHeight(72)
        hdr.setStyleSheet(f"background: {hdr_bg}; border: none;")
        hdr_lay = QVBoxLayout(hdr)
        hdr_lay.setContentsMargins(18, 12, 18, 12)
        hdr_lay.setSpacing(3)

        name_lbl = QLabel(char_name)
        name_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #ffffff; background: transparent;")
        hdr_lay.addWidget(name_lbl)

        cap_lbl = QLabel(cap_title)
        cap_lbl.setStyleSheet("font-size: 11px; color: #a8c4e0; background: transparent;")
        cap_lbl.setWordWrap(True)
        hdr_lay.addWidget(cap_lbl)

        lay.addWidget(hdr)

        # -- Cuerpo -----------------------------------------------------------
        body = QWidget()
        body.setStyleSheet(f"background: {bg};")
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(16, 14, 16, 14)
        body_lay.setSpacing(10)

        # Buscador
        self._search = QLineEdit()
        self._search.setPlaceholderText("Buscar lugar...")
        self._search.setFixedHeight(36)
        self._search.textChanged.connect(self._filter_places)
        body_lay.addWidget(self._search)

        # Lista de lugares
        self._list = QListWidget()
        self._all_places = places
        self._populate_list(places, current_place_id)
        body_lay.addWidget(self._list, stretch=1)

        # -- Pastillas de estado ----------------------------------------------
        state_lbl = QLabel("Estado de presencia:")
        state_lbl.setStyleSheet(f"font-size: 10px; color: {sub}; font-weight: bold; letter-spacing: 0.5px;")
        body_lay.addWidget(state_lbl)

        pills_row = QHBoxLayout()
        pills_row.setSpacing(8)
        self._pill_btns: dict = {}
        pill_defs = _STATUS_PILL_DEFS_DARK if is_dark else _STATUS_PILL_DEFS_LIGHT
        for key, label, color in pill_defs:
            btn = QPushButton(label)
            btn.setFixedHeight(34)
            btn.setCheckable(True)
            btn.setProperty("pill_key", key)
            btn.setProperty("pill_color", color)
            btn.setChecked(key == self.selected_type)
            btn.clicked.connect(lambda _checked, k=key: self._on_pill_clicked(k))
            self._pill_btns[key] = btn
            pills_row.addWidget(btn)
        self._apply_pill_styles()
        body_lay.addLayout(pills_row)

        # -- Botones de accion ------------------------------------------------
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        btn_clear = QPushButton("Limpiar")
        btn_clear.setFixedHeight(36)
        btn_clear.setStyleSheet(
            f"QPushButton {{ background: transparent; border: 1px solid {'#636366' if is_dark else '#c2cbd9'}; "
            f"border-radius: 8px; color: {'#8e8e93' if is_dark else '#5a6a8a'}; font-size: 12px; }}"
            f"QPushButton:hover {{ border-color: #ff453a; color: #ff453a; }}"
        )
        btn_clear.clicked.connect(self._on_clear)
        btn_row.addWidget(btn_clear)

        btn_ok = QPushButton("Guardar")
        btn_ok.setFixedHeight(36)
        btn_ok.setDefault(True)
        btn_ok.setStyleSheet(
            "QPushButton { background: #0a84ff; color: #fff; border: none; "
            "border-radius: 8px; font-weight: bold; font-size: 12px; }"
            "QPushButton:hover { background: #3399ff; }"
        )
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
