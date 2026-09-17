"""
Módulo de Panel Lateral: NexusSidePanel, _PanelHeader y _RelationCard.
"""

from typing import Optional, Dict, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QPushButton, QScrollArea,
)
from PyQt6.QtCore import Qt, pyqtSignal
import qtawesome as qta

from core.models import Character, CharacterRelation, RELATION_ICONS
from core.theme_manager import ThemeManager
from .models import CharacterMetrics, RELATION_STYLES, get_race


# ── Cabecera del Panel ───────────────────────────────────────────────────────

class _PanelHeader(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PanelHeaderWidget")
        self.setFixedHeight(95)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(14, 12, 14, 10)
        self._layout.setSpacing(3)

        is_dark = ThemeManager.is_dark()
        fg_main = "#f2f2f7" if is_dark else "#1a1a2e"
        fg_sub  = "rgba(212,160,23,0.95)" if is_dark else "#9a5c00"
        fg_meta = "#8e8e93" if is_dark else "#7a7a8a"
        bg_hdr  = "#242426" if is_dark else "#ede8e1"
        b_border= "#3a3a3c" if is_dark else "#d4cfc8"

        self._name_lbl = QLabel("—")
        self._name_lbl.setStyleSheet(
            f"color: {fg_main}; font-size: 15px; font-weight: 800; background:transparent;"
        )
        self._name_lbl.setWordWrap(True)
        self._layout.addWidget(self._name_lbl)

        self._sub_lbl = QLabel("")
        self._sub_lbl.setStyleSheet(
            f"color: {fg_sub}; font-size: 11px; font-weight:600; background:transparent;"
        )
        self._layout.addWidget(self._sub_lbl)

        self._metric_lbl = QLabel("")
        self._metric_lbl.setStyleSheet(
            f"color: {fg_meta}; font-size: 10px; background:transparent;"
        )
        self._layout.addWidget(self._metric_lbl)

        self.setStyleSheet(f"""
            QFrame#PanelHeaderWidget {{
                background: {bg_hdr};
                border-bottom: 1px solid {b_border};
            }}
        """)

    def set_character(self, char: Character, metrics: Optional[CharacterMetrics]):
        self._name_lbl.setText(char.name)
        parts = []
        race = get_race(char)
        if race:       parts.append(f"🧬 {race}")
        if char.role:  parts.append(f"🎭 {char.role}")
        self._sub_lbl.setText("   ·   ".join(parts))

        if metrics:
            self._metric_lbl.setText(
                f"Presencia: {metrics.chapters_count} cap.  |  Conexiones: {metrics.connections_count}"
            )
        else:
            self._metric_lbl.setText("")

    def clear(self):
        self._name_lbl.setText("—")
        self._sub_lbl.setText("")
        self._metric_lbl.setText("")


# ── Tarjeta de Relación Interactiva ──────────────────────────────────────────

class _RelationCard(QFrame):
    jump_to = pyqtSignal(str)

    def __init__(self, rel: CharacterRelation, other: Character, other_id: str, parent=None):
        super().__init__(parent)
        self.other_id = other_id
        rtype = rel.relation_type
        style = RELATION_STYLES.get(rtype, RELATION_STYLES["otro"])
        color = style["color"]
        icon  = RELATION_ICONS.get(rtype, "👥")
        is_dark = ThemeManager.is_dark()

        bg_card = "rgba(255,255,255,0.06)" if is_dark else "rgba(0,0,0,0.03)"
        bg_card_h = "rgba(255,255,255,0.12)" if is_dark else "rgba(0,0,0,0.07)"
        fg_name = "#f2f2f7" if is_dark else "#1a1a2e"
        btn_bg = "rgba(212,160,23,0.18)" if is_dark else "rgba(154,92,0,0.12)"
        btn_border = "rgba(212,160,23,0.35)" if is_dark else "rgba(154,92,0,0.30)"
        btn_fg = "#ffd60a" if is_dark else "#9a5c00"

        self.setFixedHeight(48)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(f"Ver a {other.name} en el grafo y destacar sus conexiones")
        self.setStyleSheet(f"""
            QFrame {{
                background: {bg_card};
                border-left: 4px solid {color};
                border-radius: 6px;
            }}
            QFrame:hover {{
                background: {bg_card_h};
                border-left-width: 5px;
            }}
        """)

        row = QHBoxLayout(self)
        row.setContentsMargins(10, 5, 8, 5)
        row.setSpacing(6)

        info = QVBoxLayout()
        info.setSpacing(2)
        info.setContentsMargins(0, 0, 0, 0)

        name_lbl = QLabel(other.name)
        name_lbl.setStyleSheet(
            f"color: {fg_name}; font-size: 12px; font-weight:bold; background:transparent;"
        )
        info.addWidget(name_lbl)

        label_text = rel.label if rel.label else rtype.capitalize()
        rel_lbl = QLabel(f"{icon} {label_text}")
        rel_lbl.setStyleSheet(
            f"color: {color}; font-size: 10px; font-weight:600; background:transparent;"
        )
        info.addWidget(rel_lbl)
        row.addLayout(info, 1)

        btn = QPushButton()
        btn.setIcon(qta.icon("fa5s.arrow-right", color=btn_fg))
        btn.setFixedSize(26, 26)
        btn.setToolTip(f"Ir a {other.name}")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {btn_bg};
                border: 1px solid {btn_border};
                border-radius: 5px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: rgba(212,160,23,0.45);
                border-color: #ffd60a;
            }}
        """)
        _oid = other_id
        btn.clicked.connect(lambda: self.jump_to.emit(_oid))
        row.addWidget(btn)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.jump_to.emit(self.other_id)
        super().mousePressEvent(event)


# ── Panel Lateral ────────────────────────────────────────────────────────────

class NexusSidePanel(QFrame):
    jump_to = pyqtSignal(str)
    jump_to_character_requested = pyqtSignal(str)
    open_sheet_requested = pyqtSignal(str)
    add_relation_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(240)
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
        self._outer.addWidget(self._header)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
        """)

        self._body = QWidget()
        self._body.setStyleSheet("background: transparent;")
        self._body_layout = QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(14, 12, 14, 12)
        self._body_layout.setSpacing(8)

        self._add_placeholder()

        self._scroll.setWidget(self._body)
        self._outer.addWidget(self._scroll, 1)

        self._char_map: dict[str, Character] = {}
        self._metrics_map: dict[str, CharacterMetrics] = {}

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
                char_map[str(obj.id)] = obj
            else:
                char_map[str(c.id)] = c

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
        self.show_character(char, rel_objs, char_map)

    def display_empty(self):
        self.clear()

    def show_character(self, char: Character, relations: list[CharacterRelation],
                       char_map: dict[str, Character]):
        self._char_map = char_map
        m = self._metrics_map.get(str(char.id))
        self._header.set_character(char, m)

        while self._body_layout.count():
            item = self._body_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        is_dark = ThemeManager.is_dark()
        fg_desc = "rgba(242,242,247,0.80)" if is_dark else "#4a4a5a"
        fg_title= "#aeaeb2" if is_dark else "#7a7a8a"
        b_sep   = "#3a3a3c" if is_dark else "#d4cfc8"

        # Botón Ver Ficha Completa
        btn_sheet = QPushButton("Ver Ficha Completa")
        btn_sheet.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_sheet.setIcon(qta.icon("fa5s.id-card", color="#ffd60a" if is_dark else "#9a5c00"))
        btn_sheet.setStyleSheet("""
            QPushButton {
                background: rgba(255, 214, 10, 0.12);
                color: #ffd60a;
                border: 1px solid rgba(255, 214, 10, 0.3);
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(255, 214, 10, 0.22);
                border-color: #ffd60a;
            }
        """ if is_dark else """
            QPushButton {
                background: rgba(154, 92, 0, 0.08);
                color: #9a5c00;
                border: 1px solid rgba(154, 92, 0, 0.25);
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(154, 92, 0, 0.16);
            }
        """)
        char_id_val = str(char.id)
        btn_sheet.clicked.connect(lambda: self.open_sheet_requested.emit(char_id_val))
        self._body_layout.addWidget(btn_sheet)

        # Descripción
        if char.description:
            desc = QLabel(char.description[:160] + ("…" if len(char.description) > 160 else ""))
            desc.setWordWrap(True)
            desc.setStyleSheet(
                f"color: {fg_desc}; font-size:10px; "
                f"background: transparent; line-height: 140%;"
            )
            self._body_layout.addWidget(desc)

        # Separador
        sep_row = QHBoxLayout()
        sep_lbl = QLabel("RELACIONES")
        sep_lbl.setStyleSheet(
            f"color: {fg_title}; font-size:9px; "
            f"font-weight:700; letter-spacing:1.5px; background:transparent;"
        )
        sep_row.addWidget(sep_lbl)
        sep_row.addStretch()
        self._body_layout.addLayout(sep_row)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {b_sep}; border:none;")
        self._body_layout.addWidget(sep)

        # Tarjetas de relación
        my_rels = [r for r in relations
                   if str(r.char_id_a) == str(char.id) or str(r.char_id_b) == str(char.id)]

        if not my_rels:
            empty = QLabel("Sin relaciones registradas")
            empty.setStyleSheet(
                f"color: {fg_title}; font-size:10px; "
                f"background:transparent; padding:8px 0;"
            )
            self._body_layout.addWidget(empty)
        else:
            for rel in my_rels:
                other_id = str(rel.char_id_b if str(rel.char_id_a) == str(char.id) else rel.char_id_a)
                other = char_map.get(other_id)
                if not other: continue
                card = _RelationCard(rel, other, other_id)
                card.jump_to.connect(self._on_jump_to)
                self._body_layout.addWidget(card)

        self._body_layout.addStretch()

    def _on_jump_to(self, oid: str):
        self.jump_to.emit(oid)
        self.jump_to_character_requested.emit(oid)

    def _add_placeholder(self):
        is_dark = ThemeManager.is_dark()
        fg_ph = "#636366" if is_dark else "#a8a29e"
        ph = QLabel("← Selecciona un\npersonaje para ver\nsus relaciones")
        ph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ph.setStyleSheet(
            f"color: {fg_ph}; font-size:11px; "
            f"background:transparent; padding:30px 0;"
        )
        self._body_layout.addWidget(ph)
        self._body_layout.addStretch()

    def clear(self):
        while self._body_layout.count():
            item = self._body_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._add_placeholder()
        self._header.clear()

    def update_theme(self, is_dark: bool):
        bg_panel = "#1c1c1e" if is_dark else "#f5f0ea"
        b_border = "#3a3a3c" if is_dark else "#d4cfc8"
        self.setStyleSheet(f"""
            QFrame#NexusSidePanel {{
                background: {bg_panel};
                border-left: 1px solid {b_border};
            }}
        """)

