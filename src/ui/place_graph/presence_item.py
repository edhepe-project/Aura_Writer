"""
place_graph/presence_item.py - Widgets de card de personaje para el panel de presencias.

Contiene:
  _MoveCharacterDialog -- Popup para elegir destino al mover un personaje
  PresenceItemWidget   -- Card horizontal de personaje en el lugar activo
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QFrame, QHBoxLayout, QVBoxLayout, QLabel,
    QComboBox, QPushButton, QDialog, QListWidget, QListWidgetItem,
    QDialogButtonBox,
)
from PyQt6.QtCore import Qt, pyqtSignal

from core.models import CharacterPresence, Place
from core.theme_manager import ThemeManager

# Paleta de colores por tipo de presencia (compartida con presence_panel.py)
_TYPE_INFO: dict[str, tuple[str, str, str]] = {
    "present":    ("Presente",    "#30d158", "bullet_green"),
    "transit":    ("En transito", "#0a84ff", "bullet_blue"),
    "departed":   ("Salida",      "#ff453a", "bullet_red"),
    "referenced": ("Mencion",     "#8e8e93", "bullet_gray"),
}

_STATUS_OPTIONS = [
    ("Presente",    "present"),
    ("En transito", "transit"),
    ("Salida",      "departed"),
]


# ---------------------------------------------------------------------------
#  Dialogo modal para elegir destino al mover un personaje
# ---------------------------------------------------------------------------
class _MoveCharacterDialog(QDialog):
    """Popup para elegir el escenario destino al mover un personaje."""

    def __init__(
        self,
        char_name: str,
        places: list[Place],
        current_place_id: str,
        is_dark: bool,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Mover personaje")
        self.setFixedSize(340, 260)
        self.selected_place_id: str | None = None

        bg   = "#1c1c1e" if is_dark else "#f5f0ea"
        fg   = "#f2f2f7" if is_dark else "#1c1c1e"
        card = "#2c2c2e" if is_dark else "#ffffff"
        bord = "#3a3a3c" if is_dark else "#d4cfc8"

        self.setStyleSheet(f"""
            QDialog  {{ background: {bg}; }}
            QLabel   {{ color: {fg}; font-size: 12px; }}
            QListWidget {{
                background: {card}; border: 1px solid {bord};
                border-radius: 6px; color: {fg}; font-size: 11px; outline: none;
            }}
            QListWidget::item {{ padding: 6px 10px; border-bottom: 1px solid {bord}; }}
            QListWidget::item:selected {{ background: #0a84ff; color: #fff; border-radius: 4px; }}
            QPushButton {{
                background: #0a84ff; color: #fff; border: none;
                border-radius: 6px; padding: 6px 14px; font-weight: bold;
            }}
            QPushButton:hover {{ background: #3399ff; }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel(f"A donde se mueve <b>{char_name}</b>?")
        title.setWordWrap(True)
        layout.addWidget(title)

        hint = QLabel("Selecciona el nuevo escenario y presiona Mover.")
        hint.setStyleSheet("font-size: 10px; color: #8e8e93;")
        layout.addWidget(hint)

        self._list = QListWidget()
        for p in places:
            if p.id != current_place_id:
                item = QListWidgetItem(f"  {p.name}")
                item.setData(Qt.ItemDataRole.UserRole, p.id)
                self._list.addItem(item)
        self._list.itemDoubleClicked.connect(self._accept_selection)
        layout.addWidget(self._list, stretch=1)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.button(QDialogButtonBox.StandardButton.Ok).setText("Mover aqui")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        btns.accepted.connect(self._accept_selection)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _accept_selection(self) -> None:
        item = self._list.currentItem()
        if item:
            self.selected_place_id = item.data(Qt.ItemDataRole.UserRole)
            self.accept()
        else:
            self.reject()


# ---------------------------------------------------------------------------
#  Card de personaje presente (fila horizontal compacta)
# ---------------------------------------------------------------------------
class PresenceItemWidget(QFrame):
    """
    Card horizontal que representa a un personaje ubicado en el lugar activo.

    Senales:
      presence_updated(char_id, new_type) -- el autor cambio el tipo de presencia
      presence_removed(char_id)           -- el autor quito al personaje del lugar
      presence_moved(char_id, place_id)   -- el autor movio al personaje a otro escenario
    """

    presence_updated = pyqtSignal(str, str)   # char_id, new_type
    presence_removed = pyqtSignal(str)         # char_id
    presence_moved   = pyqtSignal(str, str)    # char_id, new_place_id

    def __init__(
        self,
        presence: CharacterPresence,
        char_name: str,
        places: list[Place] | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.presence  = presence
        self.char_name = char_name
        self.places    = places or []
        self._setup_ui()

    def _setup_ui(self) -> None:
        is_dark = ThemeManager.is_dark()
        bg   = "#2c2c2e" if is_dark else "#ffffff"
        bord = "#3a3a3c" if is_dark else "#e0dbd3"
        fg   = "#f2f2f7" if is_dark else "#1c1c1e"

        p_type = self.presence.presence_type
        info   = _TYPE_INFO.get(p_type, ("?", "#8e8e93", "?"))
        color  = info[1]

        self.setStyleSheet(f"""
            PresenceItemWidget {{
                background: {bg};
                border: 1px solid {bord};
                border-left: 3px solid {color};
                border-radius: 8px;
            }}
        """)
        self.setFixedHeight(48)

        row = QHBoxLayout(self)
        row.setContentsMargins(10, 0, 8, 0)
        row.setSpacing(8)

        # Avatar circular con inicial del nombre
        av = QLabel(self.char_name[:1].upper() if self.char_name else "?")
        av.setFixedSize(30, 30)
        av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        av.setStyleSheet(f"""
            background: {color}22;
            color: {color};
            border: 1px solid {color}66;
            border-radius: 15px;
            font-weight: bold;
            font-size: 12px;
        """)
        row.addWidget(av)

        # Nombre del personaje
        name_lbl = QLabel(self.char_name)
        name_lbl.setStyleSheet(f"font-weight: 600; font-size: 12px; color: {fg};")
        row.addWidget(name_lbl, stretch=1)

        # Combo de estado (compacto, coloreado)
        self.type_combo = QComboBox()
        self.type_combo.setFixedWidth(115)
        self.type_combo.setFixedHeight(26)
        for label, data in _STATUS_OPTIONS:
            self.type_combo.addItem(label, data)
        idx = self.type_combo.findData(p_type)
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)
        self.type_combo.setStyleSheet(f"""
            QComboBox {{
                background: {color}18;
                color: {color};
                border: 1px solid {color}55;
                border-radius: 5px;
                padding: 2px 6px;
                font-size: 10px;
                font-weight: bold;
            }}
            QComboBox::drop-down {{ border: none; width: 14px; }}
        """)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        row.addWidget(self.type_combo)

        # Boton Mover -> destino
        if self.places:
            btn_move = QPushButton("->")
            btn_move.setFixedSize(28, 28)
            btn_move.setToolTip("Mover este personaje a otro escenario")
            btn_move.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_move.setStyleSheet("""
                QPushButton {
                    background: #0a84ff22;
                    color: #0a84ff;
                    border: 1px solid #0a84ff55;
                    border-radius: 5px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover { background: #0a84ff44; border-color: #0a84ff; }
            """)
            btn_move.clicked.connect(self._on_move_clicked)
            row.addWidget(btn_move)

        # Boton Eliminar (x)
        btn_del = QPushButton("x")
        btn_del.setFixedSize(24, 24)
        btn_del.setToolTip("Quitar personaje de este lugar")
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #636366;
                border: none;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover { color: #ff453a; }
        """)
        btn_del.clicked.connect(
            lambda: self.presence_removed.emit(self.presence.character_id)
        )
        row.addWidget(btn_del)

    def _on_type_changed(self) -> None:
        new_type = self.type_combo.currentData()
        info  = _TYPE_INFO.get(new_type, ("?", "#8e8e93", "?"))
        color = info[1]
        is_dark = ThemeManager.is_dark()
        bg   = "#2c2c2e" if is_dark else "#ffffff"
        bord = "#3a3a3c" if is_dark else "#e0dbd3"
        self.setStyleSheet(f"""
            PresenceItemWidget {{
                background: {bg};
                border: 1px solid {bord};
                border-left: 3px solid {color};
                border-radius: 8px;
            }}
        """)
        self.presence_updated.emit(self.presence.character_id, new_type)

    def _on_move_clicked(self) -> None:
        is_dark = ThemeManager.is_dark()
        dlg = _MoveCharacterDialog(
            char_name=self.char_name,
            places=self.places,
            current_place_id=self.presence.place_id,
            is_dark=is_dark,
            parent=self,
        )
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.selected_place_id:
            self.presence_moved.emit(self.presence.character_id, dlg.selected_place_id)
