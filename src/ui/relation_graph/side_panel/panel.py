"""
panel.py — NexusSidePanel (Contenedor principal y controlador del panel lateral de grafos).
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFrame, QLabel, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal

from core.models import Character, CharacterRelation
from core.theme_manager import ThemeManager
from ui.relation_graph.models import CharacterMetrics
from ui.relation_graph.side_panel.cards import _PanelHeader, _RelationCard
from ui.relation_graph.side_panel.views import build_compact_view, build_full_sheet_view


class NexusSidePanel(QFrame):
    """Panel lateral interactivo del grafo de relaciones con modos compacto y ficha completa."""
    jump_to = pyqtSignal(str)
    jump_to_character_requested = pyqtSignal(str)
    open_sheet_requested = pyqtSignal(str)
    add_relation_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mode = "compact"  # "compact" (320px) o "full" (460px)
        self.setFixedWidth(320)
        self.setObjectName("NexusSidePanel")

        is_dark = ThemeManager.is_dark()
        bg_panel = "#1c1c1e" if is_dark else "#f5f0ea"
        b_border = "#3a3a3c" if is_dark else "#d4cfc8"
        self.setStyleSheet(f"""
            QFrame#NexusSidePanel {{
                background: {bg_panel};
                border-left: 1px solid {b_border};
            }}
        """)

        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(0, 0, 0, 0)
        self._outer.setSpacing(0)

        self._header = _PanelHeader()
        self._header.edit_requested.connect(self._on_edit_clicked)
        self._header.close_full_requested.connect(self._on_close_full)
        self._outer.addWidget(self._header)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 6px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {'rgba(255,255,255,0.2)' if is_dark else 'rgba(0,0,0,0.15)'};
                min-height: 20px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {'rgba(255,255,255,0.35)' if is_dark else 'rgba(0,0,0,0.3)'};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        self._outer.addWidget(self._scroll, 1)

        self._char_map: dict[str, Character] = {}
        self._metrics_map: dict[str, CharacterMetrics] = {}
        self._current_char: Optional[Character] = None
        self._current_relations: list[CharacterRelation] = []

        self.clear()

    def set_metrics_map(self, m_map: dict[str, CharacterMetrics]):
        self._metrics_map = m_map

    def display_character(self, char_data, relations: list, all_characters: list, metrics: CharacterMetrics):
        if isinstance(char_data, dict):
            char = Character(**{k: v for k, v in char_data.items() if k in Character.__annotations__})
        else:
            char = char_data

        char_map = {}
        for c in all_characters:
            if isinstance(c, dict):
                obj = Character(**{k: v for k, v in c.items() if k in Character.__annotations__})
                char_map[obj.id] = obj
            else:
                char_map[c.id] = c

        rel_objs = []
        for r in relations:
            if isinstance(r, dict):
                robj = CharacterRelation(
                    id=r.get("id", ""),
                    char_id_a=r.get("source", ""),
                    char_id_b=r.get("target", ""),
                    label=r.get("label", ""),
                    relation_type=r.get("relation_type", "otro"),
                    intensity=int(r.get("intensity", 3))
                )
                rel_objs.append(robj)
            else:
                rel_objs.append(r)

        self._metrics_map[str(char.id)] = metrics
        self._current_char = char
        self._current_relations = rel_objs
        self._char_map = char_map
        self.show_character(char, rel_objs, char_map)

    def display_empty(self):
        self.clear()

    def _on_edit_clicked(self):
        if self._current_char:
            self.open_sheet_requested.emit(self._current_char.id)

    def _on_close_full(self):
        self._mode = "compact"
        self.setFixedWidth(320)
        if self._current_char:
            self.show_character(self._current_char, self._current_relations, self._char_map)

    def _on_open_full_sheet(self):
        self._mode = "full"
        self.setFixedWidth(460)
        if self._current_char:
            self.show_character(self._current_char, self._current_relations, self._char_map)

    def show_character(self, char: Character, relations: list[CharacterRelation],
                        char_map: dict[str, Character]):
        self._current_char = char
        self._current_relations = relations
        self._char_map = char_map

        m = self._metrics_map.get(char.id)
        is_full = (self._mode == "full")
        self._header.set_character(char, m, is_full=is_full)

        my_rels = [
            r for r in relations
            if r.char_id_a == char.id or r.char_id_b == char.id
        ]

        if not is_full:
            new_body = build_compact_view(
                char, my_rels, char_map,
                on_open_full_sheet=self._on_open_full_sheet,
                on_jump_to=self._on_jump_to
            )
        else:
            new_body = build_full_sheet_view(
                char, my_rels, char_map,
                on_jump_to=self._on_jump_to
            )

        # Reemplazo atómico seguro del widget en QScrollArea
        old_body = self._scroll.takeWidget()
        if old_body:
            old_body.setParent(None)
            old_body.deleteLater()
        self._scroll.setWidget(new_body)

    def _on_jump_to(self, oid: str):
        self.jump_to.emit(oid)
        self.jump_to_character_requested.emit(oid)

    def clear(self):
        self._current_char = None
        self._current_relations.clear()
        self._mode = "compact"
        self.setFixedWidth(320)
        self._header.clear()

        is_dark = ThemeManager.is_dark()
        fg_ph = "#636366" if is_dark else "#a8a29e"

        empty_body = QWidget()
        empty_body.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(empty_body)
        layout.setContentsMargins(14, 20, 14, 20)

        ph = QLabel("← Selecciona un\npersonaje para ver\nsus relaciones")
        ph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ph.setStyleSheet(
            f"color: {fg_ph}; font-size:11px; "
            f"background:transparent; padding:40px 0;"
        )
        layout.addWidget(ph)
        layout.addStretch()

        old_body = self._scroll.takeWidget()
        if old_body:
            old_body.setParent(None)
            old_body.deleteLater()
        self._scroll.setWidget(empty_body)

    def update_theme(self, is_dark: bool):
        bg_panel = "#1c1c1e" if is_dark else "#f5f0ea"
        b_border = "#3a3a3c" if is_dark else "#d4cfc8"
        tip_bg   = "#2c2c2e" if is_dark else "#faf7f3"
        tip_fg   = "#f2f2f7" if is_dark else "#1a1a2e"
        tip_b    = "#3a3a3c" if is_dark else "#c4bfb8"

        self.setStyleSheet(f"""
            QToolTip {{
                background-color: {tip_bg};
                color: {tip_fg};
                border: 1px solid {tip_b};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }}
            QFrame#NexusSidePanel {{
                background: {bg_panel};
                border-left: 1px solid {b_border};
            }}
        """)
        self._header.update_theme(is_dark)
        if self._current_char:
            self.show_character(self._current_char, self._current_relations, self._char_map)
        else:
            self.clear()
