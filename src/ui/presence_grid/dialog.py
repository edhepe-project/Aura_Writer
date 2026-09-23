"""
presence_grid/dialog.py - Cuadricula de Presencias (tipo spreadsheet).

Vista principal para gestionar manualmente donde esta cada personaje
en cada capitulo. Filas = personajes (por rol), Columnas = capitulos
(orden cronologico). Clic en celda -> popup para asignar lugar y estado.
"""
from __future__ import annotations
import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea, QWidget, QGridLayout,
    QSizePolicy, QListWidget, QListWidgetItem, QComboBox,
    QDialogButtonBox, QApplication, QLineEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor

from core.models import Character, CharacterPresence, Place
from core.theme_manager import ThemeManager

log = logging.getLogger(__name__)

_ROLE_ORDER = ["Protagonista", "Antagonista", "Secundario", "Misterioso", "Otro"]

_TYPE_INFO = {
    "present":    ("Presente",    "#30d158"),
    "transit":    ("En transito", "#0a84ff"),
    "departed":   ("Salida",      "#ff453a"),
    "referenced": ("Mencion",     "#8e8e93"),
}

_STATUS_OPTIONS = [
    ("Presente",    "present"),
    ("En transito", "transit"),
    ("Salida",      "departed"),
]

_COL_CHAR_WIDTH  = 170
_COL_CHAPTER_W   = 130
_ROW_HEADER_H    = 64
_ROW_CELL_H      = 52


class _PlacePickerDialog(QDialog):
    def __init__(self, char_name, cap_title, places, current_place_id, current_type, is_dark, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{char_name}")
        self.setFixedSize(360, 420)
        self.selected_place_id = current_place_id or None
        self.selected_type = current_type or "present"
        self.cleared = False

        bg   = "#1c1c1e" if is_dark else "#f5f0ea"
        fg   = "#f2f2f7" if is_dark else "#1c1c1e"
        card = "#2c2c2e" if is_dark else "#ffffff"
        bord = "#3a3a3c" if is_dark else "#d4cfc8"

        self.setStyleSheet(f"""
            QDialog {{ background: {bg}; }}
            QLabel {{ color: {fg}; font-size: 11px; }}
            QListWidget {{
                background: {card}; border: 1px solid {bord};
                border-radius: 6px; color: {fg}; font-size: 11px; outline: none;
            }}
            QListWidget::item {{ padding: 7px 10px; border-bottom: 1px solid {bord}; }}
            QListWidget::item:selected {{ background: #0a84ff; color: #fff; border-radius: 4px; }}
            QComboBox {{ background: {card}; border: 1px solid {bord}; border-radius: 6px; color: {fg}; padding: 4px 8px; font-size: 11px; }}
            QComboBox::drop-down {{ border: none; width: 16px; }}
            QLineEdit {{ background: {card}; border: 1px solid {bord}; border-radius: 6px; color: {fg}; padding: 3px 8px; font-size: 11px; }}
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)

        title = QLabel(f"Ubicar a <b>{char_name}</b><br><small>en {cap_title}</small>")
        title.setWordWrap(True)
        title.setStyleSheet(f"font-size: 12px; color: {fg};")
        lay.addWidget(title)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Buscar lugar...")
        self._search.setFixedHeight(30)
        self._search.textChanged.connect(self._filter_places)
        lay.addWidget(self._search)

        self._list = QListWidget()
        self._all_places = places
        self._populate_list(places, current_place_id)
        lay.addWidget(self._list, stretch=1)

        state_row = QHBoxLayout()
        state_row.addWidget(QLabel("Estado:"))
        self._combo = QComboBox()
        self._combo.setFixedHeight(28)
        for label, data in _STATUS_OPTIONS:
            self._combo.addItem(label, data)
        idx = self._combo.findData(current_type)
        if idx >= 0:
            self._combo.setCurrentIndex(idx)
        self._combo.currentIndexChanged.connect(lambda: setattr(self, "selected_type", self._combo.currentData()))
        state_row.addWidget(self._combo, stretch=1)
        lay.addLayout(state_row)

        btn_row = QHBoxLayout()
        btn_clear = QPushButton("Limpiar")
        btn_clear.setFixedHeight(30)
        btn_clear.setStyleSheet("QPushButton { background: transparent; border: 1px solid #636366; border-radius: 6px; color: #636366; } QPushButton:hover { border-color: #ff453a; color: #ff453a; }")
        btn_clear.clicked.connect(self._on_clear)
        btn_row.addWidget(btn_clear)

        btn_ok = QPushButton("Guardar")
        btn_ok.setFixedHeight(30)
        btn_ok.setDefault(True)
        btn_ok.setStyleSheet("QPushButton { background: #0a84ff; color: #fff; border: none; border-radius: 6px; font-weight: bold; } QPushButton:hover { background: #3399ff; }")
        btn_ok.clicked.connect(self._on_accept)
        btn_row.addWidget(btn_ok)
        lay.addLayout(btn_row)

    def _populate_list(self, places, selected_id):
        self._list.clear()
        for p in places:
            item = QListWidgetItem(f"  {p.name}")
            item.setData(Qt.ItemDataRole.UserRole, p.id)
            self._list.addItem(item)
            if p.id == selected_id:
                self._list.setCurrentItem(item)

    def _filter_places(self, query):
        q = query.strip().lower()
        filtered = [p for p in self._all_places if q in p.name.lower()] if q else self._all_places
        self._populate_list(filtered, self.selected_place_id or "")

    def _on_accept(self):
        item = self._list.currentItem()
        if item:
            self.selected_place_id = item.data(Qt.ItemDataRole.UserRole)
            self.selected_type = self._combo.currentData()
        self.accept()

    def _on_clear(self):
        self.cleared = True
        self.accept()


class _PresenceCell(QFrame):
    def __init__(self, char_id, chapter_id, is_dark, parent=None):
        super().__init__(parent)
        self.char_id    = char_id
        self.chapter_id = chapter_id
        self._is_dark   = is_dark
        self._place_id  = ""
        self._place_name= ""
        self._pres_type = ""

        self.setFixedSize(_COL_CHAPTER_W - 2, _ROW_CELL_H - 2)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setToolTip("Clic para asignar  |  Clic derecho para limpiar")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 4, 6, 4)
        lay.setSpacing(1)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._pill = QLabel("--")
        self._pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pill.setWordWrap(False)
        lay.addWidget(self._pill)

        self._type_lbl = QLabel("")
        self._type_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._type_lbl)

        self._refresh_style()

    def set_presence(self, place_name, place_id, pres_type):
        self._place_name = place_name
        self._place_id   = place_id
        self._pres_type  = pres_type
        short = place_name[:13] + "..." if len(place_name) > 13 else place_name
        self._pill.setText(short)
        info = _TYPE_INFO.get(pres_type, ("", "#8e8e93"))
        self._type_lbl.setText(info[0])
        self._refresh_style()

    def clear_presence(self):
        self._place_id = self._place_name = self._pres_type = ""
        self._pill.setText("--")
        self._type_lbl.setText("")
        self._refresh_style()

    def get_place_id(self): return self._place_id
    def get_pres_type(self): return self._pres_type

    def _refresh_style(self):
        is_dark = self._is_dark
        if self._place_id:
            color = _TYPE_INFO.get(self._pres_type, ("", "#8e8e93"))[1]
            bg, bord, text_c = f"{color}18", f"{color}55", color
        else:
            bg    = "#2a2a2c" if is_dark else "#f2ede4"
            bord  = "#3a3a3c" if is_dark else "#ddd8cf"
            text_c = "#48484a" if is_dark else "#c7c3bc"
            color  = "transparent"

        self.setStyleSheet(f"""
            background: {bg}; border: 1px solid {bord}; border-radius: 6px;
        """)
        weight = "bold" if self._place_id else "normal"
        self._pill.setStyleSheet(f"font-size: 11px; font-weight: {weight}; color: {text_c}; background: transparent;")
        self._type_lbl.setStyleSheet(f"font-size: 8px; color: {color}; background: transparent;")

    def mousePressEvent(self, event):
        grid_w = self._find_grid_widget()
        if grid_w:
            if event.button() == Qt.MouseButton.LeftButton:
                grid_w._on_cell_clicked(self)
            elif event.button() == Qt.MouseButton.RightButton:
                grid_w._on_cell_right_clicked(self)
        super().mousePressEvent(event)

    def _find_grid_widget(self):
        w = self.parent()
        while w:
            if isinstance(w, _PresenceGridWidget):
                return w
            w = w.parent() if hasattr(w, "parent") else None
        return None


class _PresenceGridWidget(QWidget):
    def __init__(self, project_manager, parent=None):
        super().__init__(parent)
        self._pm         = project_manager
        self._cells: dict = {}
        self._places     = []
        self._characters = []
        self._chapters   = []
        self._is_dark    = ThemeManager.is_dark()

    def build(self):
        # Limpiar layout previo
        if self.layout():
            while self.layout().count():
                item = self.layout().takeAt(0)
                w = item.widget()
                if w: w.deleteLater()
            QWidget().setLayout(self.layout())

        meta = self._pm.metadata
        if not meta: return

        self._places      = list(getattr(meta, "places", []))
        self._characters  = self._sorted_characters(getattr(meta, "characters", []))
        self._chapters    = self._sorted_chapters(meta)
        place_map         = {p.id: p.name for p in self._places}

        pres_map: dict = {}
        for p in getattr(meta, "presences", []):
            key = (p.character_id, p.chapter_id)
            if key not in pres_map or p.is_manual:
                pres_map[key] = p

        is_dark = self._is_dark
        fg      = "#f2f2f7" if is_dark else "#1c1c1e"
        bg_hdr  = "#1c1c1e" if is_dark else "#e8e4dc"
        bord    = "#3a3a3c" if is_dark else "#d4cfc8"

        grid = QGridLayout(self)
        grid.setSpacing(2)
        grid.setContentsMargins(4, 4, 4, 4)

        # Corner
        corner = QFrame()
        corner.setFixedSize(_COL_CHAR_WIDTH, _ROW_HEADER_H)
        corner.setStyleSheet(f"background: {bg_hdr}; border-right: 1px solid {bord}; border-bottom: 1px solid {bord};")
        cl = QHBoxLayout(corner)
        cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lc = QLabel("PERSONAJE")
        lc.setStyleSheet("font-size: 9px; font-weight: bold; color: #636366; letter-spacing: 0.8px;")
        cl.addWidget(lc)
        grid.addWidget(corner, 0, 0)

        # Headers capitulos
        for ci, chapter in enumerate(self._chapters):
            hdr = QFrame()
            hdr.setFixedSize(_COL_CHAPTER_W, _ROW_HEADER_H)
            hdr.setStyleSheet(f"background: {bg_hdr}; border-left: 1px solid {bord}; border-bottom: 2px solid {bord};")
            hl = QVBoxLayout(hdr)
            hl.setContentsMargins(4, 6, 4, 4)
            hl.setSpacing(2)
            hl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            n = QLabel(f"#{chapter.in_world_order}" if chapter.in_world_order > 0 else "")
            n.setStyleSheet("font-size: 9px; color: #8e8e93; font-weight: bold;")
            n.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hl.addWidget(n)
            raw = (chapter.title or "").strip()
            t = QLabel((raw[:15] + "...") if len(raw) > 15 else raw or "Sin titulo")
            t.setStyleSheet(f"font-size: 10px; font-weight: bold; color: {fg};")
            t.setAlignment(Qt.AlignmentFlag.AlignCenter)
            t.setToolTip(raw)
            hl.addWidget(t)
            grid.addWidget(hdr, 0, ci + 1)

        role_colors = {
            "Protagonista": "#ffd60a", "Antagonista": "#ff453a",
            "Secundario": "#30d158",   "Misterioso": "#bf5af2", "Otro": "#636366",
        }

        for ri, char in enumerate(self._characters):
            # Header personaje
            ch = QFrame()
            ch.setFixedSize(_COL_CHAR_WIDTH, _ROW_CELL_H)
            rc = role_colors.get(char.role, "#636366")
            ch.setStyleSheet(f"background: {bg_hdr}; border-right: 1px solid {bord}; border-top: 1px solid {bord}; border-left: 3px solid {rc};")
            chl = QHBoxLayout(ch)
            chl.setContentsMargins(10, 0, 8, 0)
            chl.setSpacing(7)
            av = QLabel(char.name[:1].upper() if char.name else "?")
            av.setFixedSize(28, 28)
            av.setAlignment(Qt.AlignmentFlag.AlignCenter)
            av.setStyleSheet(f"background: {rc}22; color: {rc}; border: 1px solid {rc}66; border-radius: 14px; font-weight: bold; font-size: 11px;")
            chl.addWidget(av)
            nc = QVBoxLayout()
            nc.setSpacing(1)
            nl = QLabel(char.name[:17] if len(char.name) > 17 else char.name)
            nl.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {fg};")
            nl.setToolTip(char.name)
            nc.addWidget(nl)
            rl = QLabel(char.role)
            rl.setStyleSheet(f"font-size: 8px; color: {rc};")
            nc.addWidget(rl)
            chl.addLayout(nc, stretch=1)
            grid.addWidget(ch, ri + 1, 0)

            # Celdas
            for ci, chapter in enumerate(self._chapters):
                cell = _PresenceCell(char.id, chapter.id, is_dark, parent=self)
                key  = (char.id, chapter.id)
                pres = pres_map.get(key)
                if pres and pres.place_id:
                    cell.set_presence(place_map.get(pres.place_id, "?"), pres.place_id, pres.presence_type)
                self._cells[key] = cell

                wrapper = QWidget()
                wrapper.setFixedSize(_COL_CHAPTER_W, _ROW_CELL_H)
                wl = QVBoxLayout(wrapper)
                wl.setContentsMargins(1, 1, 1, 1)
                wl.addWidget(cell)
                grid.addWidget(wrapper, ri + 1, ci + 1)

    def _on_cell_clicked(self, cell):
        meta = self._pm.metadata
        if not meta: return

        cap_title = "este capitulo"
        for c in self._chapters:
            if c.id == cell.chapter_id:
                cap_title = (c.title or "").strip() or f"Cap. {c.in_world_order}"
                break

        char_name = next((c.name for c in self._characters if c.id == cell.char_id), "Personaje")

        dlg = _PlacePickerDialog(
            char_name=char_name, cap_title=cap_title, places=self._places,
            current_place_id=cell.get_place_id(), current_type=cell.get_pres_type() or "present",
            is_dark=self._is_dark, parent=self,
        )
        if dlg.exec() != QDialog.DialogCode.Accepted: return

        if dlg.cleared:
            self._remove_presence(cell)
        elif dlg.selected_place_id:
            self._set_presence(cell, dlg.selected_place_id, dlg.selected_type)

    def _on_cell_right_clicked(self, cell):
        if cell.get_place_id():
            self._remove_presence(cell)

    def _set_presence(self, cell, place_id, pres_type):
        meta = self._pm.metadata
        if not meta: return
        place_map = {p.id: p.name for p in self._places}
        meta.presences = [
            p for p in getattr(meta, "presences", [])
            if not (p.character_id == cell.char_id and p.chapter_id == cell.chapter_id)
        ]
        new_p = CharacterPresence(
            character_id=cell.char_id, place_id=place_id, chapter_id=cell.chapter_id,
            presence_type=pres_type, confidence=1.0, is_manual=True,
            matched_text="Cuadricula de Presencias",
        )
        meta.presences.append(new_p)
        cell.set_presence(place_map.get(place_id, "?"), place_id, pres_type)
        try:
            self._pm.save_project()
        except Exception as e:
            log.warning("Error guardando presencia: %s", e)

    def _remove_presence(self, cell):
        meta = self._pm.metadata
        if not meta: return
        meta.presences = [
            p for p in getattr(meta, "presences", [])
            if not (p.character_id == cell.char_id and p.chapter_id == cell.chapter_id)
        ]
        cell.clear_presence()
        try:
            self._pm.save_project()
        except Exception as e:
            log.warning("Error guardando: %s", e)

    @staticmethod
    def _sorted_characters(chars):
        def _key(c):
            try: ri = _ROLE_ORDER.index(c.role)
            except ValueError: ri = len(_ROLE_ORDER)
            return (ri, c.name.lower())
        return sorted(chars, key=_key)

    @staticmethod
    def _sorted_chapters(meta):
        """
        Retorna capitulos en el orden correcto para la cuadricula:
          1. Orden primario: in_world_order (si > 0) — orden cronologico del mundo.
          2. Orden fallback: indice de insercion en el esquema (obra -> libro -> capitulo).
             Esto preserva el orden narrativo que el autor definio en el panel de estructura,
             incluso cuando no ha asignado un in_world_order explicito.
        Si mezcla de capitulos con y sin in_world_order, los que tienen van primero
        por numero, el resto sigue el orden del esquema al final.
        """
        caps_with_idx = []
        struct_idx = 0
        for obra in getattr(meta, "obras", []):
            for libro in getattr(obra, "libros", []):
                for cap in getattr(libro, "capitulos", []):
                    caps_with_idx.append((cap, struct_idx))
                    struct_idx += 1

        def _sort_key(item):
            cap, idx = item
            order = cap.in_world_order or 0
            if order > 0:
                # Tiene orden explicito: va primero, ordenado por ese numero
                return (0, order, idx)
            else:
                # Sin orden explicito: preservar orden del esquema
                return (1, idx, 0)

        caps_with_idx.sort(key=_sort_key)
        return [cap for cap, _ in caps_with_idx]



class PresenceGridDialog(QDialog):
    """
    Dialogo independiente - Cuadricula de Presencias.
    Filas = personajes (por rol), Columnas = capitulos (cronologico).
    Clic en celda -> elegir lugar y estado. Clic derecho -> limpiar.
    """

    def __init__(self, project_manager, parent=None):
        super().__init__(parent)
        self._pm = project_manager
        self.setWindowTitle("Cuadricula de Presencias")
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinMaxButtonsHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        screen = QApplication.primaryScreen().availableGeometry()
        w = min(1400, int(screen.width() * 0.90))
        h = min(860,  int(screen.height() * 0.88))
        self.resize(w, h)

        is_dark = ThemeManager.is_dark()
        bg = "#141416" if is_dark else "#f0ece3"
        self.setStyleSheet(f"QDialog {{ background: {bg}; }}")
        self._setup_ui(is_dark)
        self._grid_widget.build()

    def _setup_ui(self, is_dark):
        fg   = "#f2f2f7" if is_dark else "#1c1c1e"
        bord = "#3a3a3c" if is_dark else "#d4cfc8"
        bg_tb = "#1c1c1e" if is_dark else "#e8e4dc"

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Toolbar
        tb = QFrame()
        tb.setFixedHeight(50)
        tb.setStyleSheet(f"QFrame {{ background: {bg_tb}; border-bottom: 1px solid {bord}; }}")
        tbl = QHBoxLayout(tb)
        tbl.setContentsMargins(16, 0, 16, 0)
        tbl.setSpacing(12)

        tl = QLabel("Cuadricula de Presencias")
        tl.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {fg};")
        tbl.addWidget(tl)

        sl = QLabel("Filas = personajes   |   Columnas = capitulos (orden cronologico)")
        sl.setStyleSheet("font-size: 10px; color: #636366;")
        tbl.addWidget(sl)
        tbl.addStretch()

        for lbl, col in [("Presente", "#30d158"), ("En transito", "#0a84ff"), ("Salida", "#ff453a")]:
            pill = QLabel(f"  {lbl}")
            pill.setStyleSheet(f"font-size: 10px; color: {col}; font-weight: bold; border: 1px solid {col}44; border-radius: 4px; padding: 2px 8px; background: {col}18;")
            tbl.addWidget(pill)

        root.addWidget(tb)

        # Scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._grid_widget = _PresenceGridWidget(self._pm, parent=scroll)
        scroll.setWidget(self._grid_widget)
        root.addWidget(scroll, stretch=1)

        # Barra inferior
        bot = QFrame()
        bot.setFixedHeight(40)
        bot.setStyleSheet(f"QFrame {{ background: {bg_tb}; border-top: 1px solid {bord}; }}")
        bl = QHBoxLayout(bot)
        bl.setContentsMargins(16, 0, 16, 0)
        bl.setSpacing(12)
        hl = QLabel("Clic en celda para asignar ubicacion   |   Clic derecho para limpiar")
        hl.setStyleSheet("font-size: 10px; color: #636366;")
        bl.addWidget(hl)
        bl.addStretch()
        cb = QPushButton("Cerrar")
        cb.setFixedHeight(28)
        cb.setStyleSheet("QPushButton { background: transparent; border: 1px solid #636366; border-radius: 6px; color: #8e8e93; padding: 0 14px; } QPushButton:hover { border-color: #f2f2f7; color: #f2f2f7; }")
        cb.clicked.connect(self.accept)
        bl.addWidget(cb)
        root.addWidget(bot)
