"""
place_graph/history_panel.py - Panel de historial de visitas al lugar seleccionado.

Contiene:
  PlaceHistoryPanel    -- Scroll con presencias agrupadas por capitulo
  _ChapterGroupHeader  -- Header colapsable de cada grupo de capitulo
"""
from __future__ import annotations
from typing import Optional, List, Dict

from PyQt6.QtWidgets import (
    QWidget, QFrame, QHBoxLayout, QVBoxLayout, QLabel, QScrollArea,
)
from PyQt6.QtCore import Qt, pyqtSignal

from core.models import CharacterPresence, Place
from core.theme_manager import ThemeManager

# Paleta de colores por tipo de presencia
_TYPE_INFO: dict[str, tuple[str, str, str]] = {
    "present":    ("Presente",    "#30d158", "bullet_green"),
    "transit":    ("En transito", "#0a84ff", "bullet_blue"),
    "departed":   ("Salida",      "#ff453a", "bullet_red"),
    "referenced": ("Mencion",     "#8e8e93", "bullet_gray"),
}


# ---------------------------------------------------------------------------
#  Header colapsable de capitulo
# ---------------------------------------------------------------------------
class _ChapterGroupHeader(QFrame):
    """Header clickeable que colapsa/expande el grupo de presencias de un capitulo."""

    toggled = pyqtSignal(bool)

    def __init__(
        self,
        cap_title: str,
        obra_title: str,
        order: int,
        count: int,
        expanded: bool,
        is_latest: bool,
        is_dark: bool,
        parent=None,
    ):
        super().__init__(parent)
        self._expanded = expanded
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        accent = "#ffd60a" if is_latest else ("#5e5ce6" if is_dark else "#4f46e5")
        bg     = "#1e1e20" if is_dark else "#ede9e0"
        fg     = "#f2f2f7" if is_dark else "#1c1c1e"
        sub_fg = "#8e8e93" if is_dark else "#6e6e73"

        self.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: 1px solid {accent}44;
                border-radius: 6px;
            }}
            QFrame:hover {{ border-color: {accent}88; }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 7, 10, 7)
        layout.setSpacing(6)

        self._arrow = QLabel("v" if expanded else ">")
        self._arrow.setStyleSheet(
            f"color: {accent}; font-size: 12px; font-weight: bold;"
        )
        self._arrow.setFixedWidth(14)
        layout.addWidget(self._arrow)

        order_str = f"#{order}  " if order > 0 else ""
        title_lbl = QLabel(f"{order_str}{cap_title}")
        title_lbl.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {fg};")
        layout.addWidget(title_lbl, stretch=1)

        if obra_title:
            obra_lbl = QLabel(obra_title)
            obra_lbl.setStyleSheet(f"font-size: 9px; color: {sub_fg};")
            layout.addWidget(obra_lbl)

        n = count
        badge = QLabel(f"{n} {'personaje' if n == 1 else 'personajes'}")
        badge.setStyleSheet(f"""
            background: {accent}22; color: {accent};
            border: 1px solid {accent}55; border-radius: 3px;
            font-size: 9px; font-weight: bold; padding: 1px 5px;
        """)
        layout.addWidget(badge)

    def mousePressEvent(self, event) -> None:
        self._expanded = not self._expanded
        self._arrow.setText("v" if self._expanded else ">")
        self.toggled.emit(self._expanded)
        super().mousePressEvent(event)


# ---------------------------------------------------------------------------
#  Panel de Historial de visitas
# ---------------------------------------------------------------------------
class PlaceHistoryPanel(QWidget):
    """
    Historial cronologico de visitas al lugar seleccionado.
    Muestra presencias agrupadas por capitulo con headers colapsables.
    Los ultimos 3 capitulos se expanden automaticamente.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_place: Optional[Place] = None
        self._project_manager = None
        self._setup_ui()

    def set_project_manager(self, pm) -> None:
        self._project_manager = pm

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 6, 0, 4)
        root.setSpacing(4)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_content = QWidget()
        self.items_layout   = QVBoxLayout(self.scroll_content)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(4)
        self.items_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.scroll_content)
        root.addWidget(self.scroll, stretch=1)

    def _clear_layout(self) -> None:
        while self.items_layout.count() > 0:
            item = self.items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def load_place(self, place: Optional[Place]) -> None:
        """Carga el historial completo agrupado por capitulo."""
        self._current_place = place
        self._clear_layout()

        if not place:
            lbl = QLabel("Selecciona un lugar en el mapa.")
            lbl.setStyleSheet("color: #8e8e93; font-style: italic; font-size: 11px;")
            self.items_layout.addWidget(lbl)
            return

        if not self._project_manager or not self._project_manager.metadata:
            return

        meta     = self._project_manager.metadata
        char_map: Dict[str, str] = {
            c.id: c.name for c in getattr(meta, "characters", [])
        }

        # Mapa capitulo_id -> (titulo, obra, orden_cronologico)
        cap_map: Dict[str, tuple] = {}
        for obra in meta.obras:
            for libro in obra.libros:
                for cap in libro.capitulos:
                    cap_map[cap.id] = (cap.title, obra.title, cap.in_world_order)

        all_pres: List[CharacterPresence] = getattr(meta, "presences", [])
        place_events = [p for p in all_pres if p.place_id == place.id]

        if not place_events:
            lbl = QLabel(
                "Ningun personaje tiene registro de haber visitado este lugar aun."
            )
            lbl.setStyleSheet(
                "color: #8e8e93; font-style: italic; font-size: 11px; margin-top: 6px;"
            )
            lbl.setWordWrap(True)
            self.items_layout.addWidget(lbl)
            return

        # Ordenar y agrupar por capitulo
        def _sort_key(p: CharacterPresence):
            info = cap_map.get(p.chapter_id, ("", "", 0))
            return (info[2] or p.in_world_order, p.created_at)

        sorted_events = sorted(place_events, key=_sort_key)
        groups: Dict[str, List[CharacterPresence]] = {}
        group_order: List[str] = []
        for p in sorted_events:
            if p.chapter_id not in groups:
                groups[p.chapter_id] = []
                group_order.append(p.chapter_id)
            groups[p.chapter_id].append(p)

        is_dark          = ThemeManager.is_dark()
        AUTO_EXPAND_LAST = 3
        expanded_ids     = set(group_order[-AUTO_EXPAND_LAST:])

        for cap_id in group_order:
            presences_in_cap = groups[cap_id]
            cap_title, obra_title, order = cap_map.get(
                cap_id, ("Capitulo desconocido", "", 0)
            )
            is_expanded = cap_id in expanded_ids
            is_latest   = cap_id == group_order[-1]

            header = _ChapterGroupHeader(
                cap_title=cap_title,
                obra_title=obra_title,
                order=order,
                count=len(presences_in_cap),
                expanded=is_expanded,
                is_latest=is_latest,
                is_dark=is_dark,
            )
            self.items_layout.addWidget(header)

            # Filas compactas bajo el header
            rows_widget = QWidget()
            rows_lay    = QVBoxLayout(rows_widget)
            rows_lay.setContentsMargins(12, 2, 4, 4)
            rows_lay.setSpacing(3)

            for p in presences_in_cap:
                c_name = char_map.get(p.character_id, "Personaje desconocido")
                info   = _TYPE_INFO.get(p.presence_type, (p.presence_type, "#8e8e93", "?"))
                type_label, type_color = info[0], info[1]

                row = QFrame()
                row_bg = "#242426" if is_dark else "#f5f2ec"
                row.setStyleSheet(f"""
                    QFrame {{
                        background: {row_bg};
                        border: none;
                        border-left: 2px solid {type_color}66;
                        border-radius: 3px;
                    }}
                """)
                row_l = QHBoxLayout(row)
                row_l.setContentsMargins(8, 4, 8, 4)
                row_l.setSpacing(6)

                av = QLabel(c_name[:1].upper())
                av.setFixedSize(20, 20)
                av.setAlignment(Qt.AlignmentFlag.AlignCenter)
                av.setStyleSheet(f"""
                    background: {type_color}22;
                    color: {type_color};
                    border: 1px solid {type_color}66;
                    border-radius: 10px;
                    font-weight: bold;
                    font-size: 9px;
                """)
                row_l.addWidget(av)

                fg_text = "#f2f2f7" if is_dark else "#1c1c1e"
                name_lbl = QLabel(c_name)
                name_lbl.setStyleSheet(
                    f"font-size: 11px; font-weight: 600; color: {fg_text};"
                )
                row_l.addWidget(name_lbl, stretch=1)

                pill = QLabel(type_label)
                pill.setStyleSheet(f"""
                    background: {type_color}22;
                    color: {type_color};
                    border: 1px solid {type_color}55;
                    border-radius: 3px;
                    font-size: 9px;
                    font-weight: bold;
                    padding: 1px 5px;
                """)
                row_l.addWidget(pill)

                if p.verb_matched:
                    verb_lbl = QLabel(f'"{p.verb_matched}"')
                    verb_lbl.setStyleSheet(
                        "font-size: 9px; color: #636366; font-style: italic;"
                    )
                    row_l.addWidget(verb_lbl)

                rows_lay.addWidget(row)

            rows_widget.setVisible(is_expanded)
            header.toggled.connect(rows_widget.setVisible)
            self.items_layout.addWidget(rows_widget)
