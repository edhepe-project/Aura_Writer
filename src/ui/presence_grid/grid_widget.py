"""
presence_grid/grid_widget.py - Cuadricula de 4 cuadrantes con columna y header congelados.

Contiene:
  _PresenceCell       -- Celda individual clickeable (lugar + tipo de presencia)
  _PresenceGridWidget -- Widget maestro con scroll sincronizado entre los 4 cuadrantes
"""
from __future__ import annotations
import logging

from PyQt6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QGridLayout, QSizePolicy, QDialog,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor

from core.models import CharacterPresence
from core.theme_manager import ThemeManager
from .place_picker import _PlacePickerDialog

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
#  Constantes de layout compartidas con el resto del paquete
# ---------------------------------------------------------------------------
_ROLE_ORDER = ["Protagonista", "Antagonista", "Secundario", "Misterioso", "Otro"]

_TYPE_INFO = {
    "present":    ("Presente",    "#30d158"),
    "transit":    ("En transito", "#0a84ff"),
    "departed":   ("Salida",      "#ff453a"),
    "referenced": ("Mencion",     "#8e8e93"),
}

_COL_CHAR_WIDTH = 210   # ancho fijo de la columna de personajes (Q1 y Q3)
_COL_CHAPTER_W  = 130   # ancho de cada columna de capitulo
_ROW_HEADER_H   = 72    # alto del header de capitulos (Q1 y Q2)
_ROW_CELL_H     = 54    # alto de cada fila de personaje


# ---------------------------------------------------------------------------
#  Celda individual de presencia
# ---------------------------------------------------------------------------
class _PresenceCell(QFrame):
    """
    Celda clickeable de la cuadricula que representa la presencia de un personaje
    en un capitulo especifico. Muestra el lugar asignado y el tipo de presencia.

    Clic izquierdo → abre _PlacePickerDialog para asignar/cambiar.
    Clic derecho   → limpia la presencia directamente.
    """

    def __init__(self, char_id: str, chapter_id: str, is_dark: bool, grid_widget_ref, parent=None):
        super().__init__(parent)
        self.char_id     = char_id
        self.chapter_id  = chapter_id
        self._is_dark    = is_dark
        self._grid_ref   = grid_widget_ref  # referencia directa al _PresenceGridWidget
        self._place_id   = ""
        self._place_name = ""
        self._pres_type  = ""

        self.setFixedSize(_COL_CHAPTER_W - 2, _ROW_CELL_H - 2)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setToolTip("Clic para asignar  |  Clic derecho para limpiar")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(5, 3, 5, 3)
        lay.setSpacing(1)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._pill = QLabel("--")
        self._pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._pill)

        self._type_lbl = QLabel("")
        self._type_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._type_lbl)

        self._refresh_style()

    # -- API publica ----------------------------------------------------------

    def set_presence(self, place_name: str, place_id: str, pres_type: str) -> None:
        self._place_name = place_name
        self._place_id   = place_id
        self._pres_type  = pres_type
        short = (place_name[:12] + "...") if len(place_name) > 12 else place_name
        self._pill.setText(short)
        self._type_lbl.setText(_TYPE_INFO.get(pres_type, ("", "#8e8e93"))[0])
        self._refresh_style()

    def clear_presence(self) -> None:
        self._place_id = self._place_name = self._pres_type = ""
        self._pill.setText("--")
        self._type_lbl.setText("")
        self._refresh_style()

    def get_place_id(self) -> str:  return self._place_id
    def get_pres_type(self) -> str: return self._pres_type

    # -- Estilo ---------------------------------------------------------------

    def _refresh_style(self) -> None:
        is_dark = self._is_dark
        if self._place_id:
            color = _TYPE_INFO.get(self._pres_type, ("", "#8e8e93"))[1]
            if is_dark:
                bg, bord, text_c = f"{color}22", f"{color}66", color
            else:
                bg, bord, text_c = f"{color}28", f"{color}99", color
        else:
            bg     = "#2a2a2c" if is_dark else "#ffffff"
            bord   = "#3a3a3c" if is_dark else "#c8d0dc"
            text_c = "#48484a" if is_dark else "#9ba8b8"
            color  = "transparent"

        self.setStyleSheet(f"background: {bg}; border: 1px solid {bord}; border-radius: 6px;")
        self._pill.setStyleSheet(
            f"font-size: 12px; font-weight: {'bold' if self._place_id else 'normal'}; "
            f"color: {text_c}; background: transparent;"
        )
        self._type_lbl.setStyleSheet(f"font-size: 9px; color: {color}; background: transparent;")

    # -- Eventos de raton -----------------------------------------------------

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._grid_ref._on_cell_clicked(self)
        elif event.button() == Qt.MouseButton.RightButton:
            self._grid_ref._on_cell_right_clicked(self)
        super().mousePressEvent(event)


# ---------------------------------------------------------------------------
#  Widget principal de la cuadricula con 4 cuadrantes + scroll sincronizado
# ---------------------------------------------------------------------------
class _PresenceGridWidget(QWidget):
    """
    Layout de 4 cuadrantes para simular columnas y headers congelados:

      [Q1: Esquina]  |  [Q2: Headers capitulos (H-scroll sincronizado)]
      ---------------+--------------------------------------------------
      [Q3: Nombres   |  [Q4: Celdas de presencia (SCROLL MAESTRO)]
           (V-scroll  |
           sincronizado)]

    El Q4 es el scroll maestro. Su scrollbar horizontal se conecta al de Q2,
    y su scrollbar vertical se conecta al de Q3. Resultado: la columna de
    personajes y el header de capitulos permanecen fijos al hacer scroll.
    """

    def __init__(self, project_manager, parent=None):
        super().__init__(parent)
        self._pm         = project_manager
        self._cells: dict = {}
        self._places      = []
        self._characters  = []
        self._chapters    = []
        self._is_dark     = ThemeManager.is_dark()
        self._build_layout()

    # -- Construccion del layout de 4 cuadrantes ------------------------------

    def _build_layout(self) -> None:
        """Construye la estructura de 4 cuadrantes con scrollbars sincronizados."""
        is_dark = self._is_dark
        bg_hdr  = "#1c1c1e" if is_dark else "#e8e4dc"
        bord    = "#3a3a3c" if is_dark else "#d4cfc8"

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # -- Fila superior: Q1 (esquina) + Q2 (headers capitulos) -------------
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(0)

        # Q1: Esquina estatica
        self._q1_corner = QFrame()
        self._q1_corner.setFixedSize(_COL_CHAR_WIDTH, _ROW_HEADER_H)
        self._q1_corner.setStyleSheet(
            f"background: {bg_hdr}; border-right: 2px solid {bord}; border-bottom: 2px solid {bord};"
        )
        q1_lay = QHBoxLayout(self._q1_corner)
        q1_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        q1_lbl = QLabel("PERSONAJE")
        q1_lbl.setStyleSheet("font-size: 9px; font-weight: bold; color: #636366; letter-spacing: 0.8px;")
        q1_lay.addWidget(q1_lbl)
        top_row.addWidget(self._q1_corner)

        # Q2: Headers de capitulos (scroll horizontal, sin barra visible)
        self._q2_scroll = QScrollArea()
        self._q2_scroll.setFixedHeight(_ROW_HEADER_H)
        self._q2_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._q2_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._q2_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._q2_content = QWidget()
        self._q2_lay = QHBoxLayout(self._q2_content)
        self._q2_lay.setContentsMargins(0, 0, 0, 0)
        self._q2_lay.setSpacing(2)
        self._q2_lay.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self._q2_scroll.setWidget(self._q2_content)
        top_row.addWidget(self._q2_scroll, stretch=1)
        outer.addLayout(top_row)

        # -- Fila inferior: Q3 (nombres) + Q4 (celdas - scroll maestro) -------
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.setSpacing(0)

        # Q3: Nombres de personajes (scroll vertical, sin barra visible)
        self._q3_scroll = QScrollArea()
        self._q3_scroll.setFixedWidth(_COL_CHAR_WIDTH)
        self._q3_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._q3_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._q3_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._q3_content = QWidget()
        self._q3_lay = QVBoxLayout(self._q3_content)
        self._q3_lay.setContentsMargins(0, 0, 0, 0)
        self._q3_lay.setSpacing(2)
        self._q3_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._q3_scroll.setWidget(self._q3_content)
        bottom_row.addWidget(self._q3_scroll)

        # Q4: Celdas de presencia (SCROLL MAESTRO - ambas direcciones)
        self._q4_scroll = QScrollArea()
        self._q4_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._q4_scroll.setWidgetResizable(False)
        self._q4_content = QWidget()
        self._q4_lay = QGridLayout(self._q4_content)
        self._q4_lay.setContentsMargins(0, 0, 0, 0)
        self._q4_lay.setSpacing(2)
        self._q4_scroll.setWidget(self._q4_content)
        bottom_row.addWidget(self._q4_scroll, stretch=1)
        outer.addLayout(bottom_row, stretch=1)

        # -- Sincronizacion de scrollbars -------------------------------------
        # Q4 horizontal → Q2 horizontal (headers de capitulos)
        self._q4_scroll.horizontalScrollBar().valueChanged.connect(
            self._q2_scroll.horizontalScrollBar().setValue
        )
        # Q4 vertical → Q3 vertical (nombres de personajes)
        self._q4_scroll.verticalScrollBar().valueChanged.connect(
            self._q3_scroll.verticalScrollBar().setValue
        )

    # -- Poblado de datos -----------------------------------------------------

    def build(self) -> None:
        """Carga los datos del proyecto y puebla los 4 cuadrantes."""
        meta = self._pm.metadata
        if not meta:
            return

        self._places     = list(getattr(meta, "places", []))
        self._characters = self._sorted_characters(getattr(meta, "characters", []))
        self._chapters   = self._sorted_chapters(meta)
        self._cells      = {}
        place_map        = {p.id: p.name for p in self._places}

        pres_map: dict = {}
        for p in getattr(meta, "presences", []):
            key = (p.character_id, p.chapter_id)
            if key not in pres_map or p.is_manual:
                pres_map[key] = p

        is_dark = self._is_dark
        fg      = "#f2f2f7" if is_dark else "#1a1d23"
        bg_hdr  = "#1c1c1e" if is_dark else "#edf0f7"
        bord    = "#3a3a3c" if is_dark else "#c2cbd9"

        if is_dark:
            role_colors = {
                "Protagonista": "#ffd60a", "Antagonista": "#ff453a",
                "Secundario":   "#30d158", "Misterioso":  "#bf5af2", "Otro": "#636366",
            }
        else:
            role_colors = {
                "Protagonista": "#c07800", "Antagonista": "#c41e0e",
                "Secundario":   "#1a7a38", "Misterioso":  "#7a1fa8", "Otro": "#4a5568",
            }

        # Limpiar contenidos anteriores
        self._clear_layout(self._q2_lay)
        self._clear_layout(self._q3_lay)
        self._clear_grid(self._q4_lay)

        # -- Q2: Headers de capitulos -----------------------------------------
        accent_hdr = "#2c2c3a" if is_dark else "#3d5a8a"
        total_w = 0
        for chapter in self._chapters:
            hdr = QFrame()
            hdr.setFixedSize(_COL_CHAPTER_W, _ROW_HEADER_H)
            hdr.setStyleSheet(
                f"background: {bg_hdr}; border-right: 1px solid {bord}; "
                f"border-bottom: 2px solid {accent_hdr};"
            )
            hl = QVBoxLayout(hdr)
            hl.setContentsMargins(4, 6, 4, 4)
            hl.setSpacing(2)
            hl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            num_color = "#8e8e93" if is_dark else "#6b7fa8"
            n = QLabel(f"#{chapter.in_world_order}" if chapter.in_world_order > 0 else "")
            n.setStyleSheet(f"font-size: 10px; color: {num_color}; font-weight: bold;")
            n.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hl.addWidget(n)

            raw = (chapter.title or "").strip()
            t = QLabel((raw[:14] + "...") if len(raw) > 14 else raw or "Sin titulo")
            t.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {fg};")
            t.setAlignment(Qt.AlignmentFlag.AlignCenter)
            t.setToolTip(raw)
            hl.addWidget(t)

            self._q2_lay.addWidget(hdr)
            total_w += _COL_CHAPTER_W + 2

        self._q2_content.setFixedSize(total_w, _ROW_HEADER_H)

        # -- Q3: Nombres de personajes + Q4: Celdas ---------------------------
        total_h = 0
        for ri, char in enumerate(self._characters):
            rc = role_colors.get(char.role, "#636366")

            # Fila de personaje: [barra de color 4px] [nombre + rol]
            ch = QFrame()
            ch.setFixedSize(_COL_CHAR_WIDTH, _ROW_CELL_H)
            ch.setStyleSheet(
                f"QFrame {{ background: {bg_hdr}; "
                f"border-right: 1px solid {bord}; "
                f"border-bottom: 1px solid {bord}; }}"
            )
            ch_row = QHBoxLayout(ch)
            ch_row.setContentsMargins(0, 0, 0, 0)
            ch_row.setSpacing(0)

            color_bar = QFrame()
            color_bar.setFixedWidth(4)
            color_bar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
            color_bar.setStyleSheet(f"background: {rc}; border: none;")
            ch_row.addWidget(color_bar)

            text_area = QWidget()
            text_area.setStyleSheet("background: transparent; border: none;")
            txt_lay = QVBoxLayout(text_area)
            txt_lay.setContentsMargins(10, 6, 8, 6)
            txt_lay.setSpacing(2)
            txt_lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)

            nl = QLabel((char.name[:22] + "...") if len(char.name) > 22 else char.name)
            nl.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {fg}; background: transparent;")
            nl.setToolTip(char.name)
            txt_lay.addWidget(nl)

            rl = QLabel(char.role)
            rl.setStyleSheet(f"font-size: 10px; color: {rc}; background: transparent; font-weight: 500;")
            txt_lay.addWidget(rl)

            ch_row.addWidget(text_area, stretch=1)
            self._q3_lay.addWidget(ch)
            total_h += _ROW_CELL_H + 2

            # Celdas Q4 para este personaje
            for ci, chapter in enumerate(self._chapters):
                cell = _PresenceCell(
                    char.id, chapter.id, is_dark,
                    grid_widget_ref=self,
                    parent=self._q4_content,
                )
                key  = (char.id, chapter.id)
                pres = pres_map.get(key)
                if pres and pres.place_id:
                    cell.set_presence(place_map.get(pres.place_id, "?"), pres.place_id, pres.presence_type)
                self._cells[key] = cell

                wrapper = QWidget(self._q4_content)
                wrapper.setFixedSize(_COL_CHAPTER_W, _ROW_CELL_H)
                wl = QVBoxLayout(wrapper)
                wl.setContentsMargins(1, 1, 1, 1)
                wl.addWidget(cell)
                self._q4_lay.addWidget(wrapper, ri, ci)

        self._q3_content.setFixedSize(_COL_CHAR_WIDTH, total_h)
        self._q4_content.setFixedSize(total_w, total_h)

    # -- Limpieza de layouts --------------------------------------------------

    @staticmethod
    def _clear_layout(lay) -> None:
        while lay.count():
            item = lay.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    @staticmethod
    def _clear_grid(lay) -> None:
        while lay.count():
            item = lay.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    # -- Interaccion usuario --------------------------------------------------

    def _on_cell_clicked(self, cell: _PresenceCell) -> None:
        meta = self._pm.metadata
        if not meta:
            return

        cap_title = next(
            ((c.title or "").strip() or f"Cap. {c.in_world_order}"
             for c in self._chapters if c.id == cell.chapter_id),
            "este capitulo",
        )
        char_name = next(
            (c.name for c in self._characters if c.id == cell.char_id),
            "Personaje",
        )

        dlg = _PlacePickerDialog(
            char_name=char_name, cap_title=cap_title, places=self._places,
            current_place_id=cell.get_place_id(), current_type=cell.get_pres_type() or "present",
            is_dark=self._is_dark, parent=self,
        )
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        if dlg.cleared:
            self._remove_presence(cell)
        elif dlg.selected_place_id:
            self._set_presence(cell, dlg.selected_place_id, dlg.selected_type)

    def _on_cell_right_clicked(self, cell: _PresenceCell) -> None:
        if cell.get_place_id():
            self._remove_presence(cell)

    def _set_presence(self, cell: _PresenceCell, place_id: str, pres_type: str) -> None:
        meta = self._pm.metadata
        if not meta:
            return
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

    def _remove_presence(self, cell: _PresenceCell) -> None:
        meta = self._pm.metadata
        if not meta:
            return
        meta.presences = [
            p for p in getattr(meta, "presences", [])
            if not (p.character_id == cell.char_id and p.chapter_id == cell.chapter_id)
        ]
        cell.clear_presence()
        try:
            self._pm.save_project()
        except Exception as e:
            log.warning("Error guardando: %s", e)

    # -- Ordenamiento ---------------------------------------------------------

    @staticmethod
    def _sorted_characters(chars: list) -> list:
        def _key(c):
            try:
                ri = _ROLE_ORDER.index(c.role)
            except ValueError:
                ri = len(_ROLE_ORDER)
            return (ri, c.name.lower())
        return sorted(chars, key=_key)

    @staticmethod
    def _sorted_chapters(meta) -> list:
        """Orden: in_world_order > 0 primero (por numero), luego por indice estructural."""
        caps_with_idx = []
        idx = 0
        for obra in getattr(meta, "obras", []):
            for libro in getattr(obra, "libros", []):
                for cap in getattr(libro, "capitulos", []):
                    caps_with_idx.append((cap, idx))
                    idx += 1

        def _key(item):
            cap, i = item
            order = cap.in_world_order or 0
            return (0, order, i) if order > 0 else (1, i, 0)

        caps_with_idx.sort(key=_key)
        return [cap for cap, _ in caps_with_idx]
