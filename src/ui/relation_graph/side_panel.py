"""
Módulo de Panel Lateral: NexusSidePanel, _PanelHeader, _RelationCard y Ficha Completa Integrada.
"""

from typing import Optional, Dict, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QPushButton, QScrollArea, QTabWidget,
    QGridLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal
import qtawesome as qta

from core.models import Character, CharacterRelation, RELATION_ICONS
from core.theme_manager import ThemeManager
from .models import CharacterMetrics, RELATION_STYLES, get_race


# ── Cabecera del Panel ───────────────────────────────────────────────────────

class _PanelHeader(QFrame):
    edit_requested = pyqtSignal()
    close_full_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PanelHeaderWidget")
        self.setFixedHeight(105)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(14, 10, 14, 8)
        self._layout.setSpacing(3)

        # Fila superior: Nombre + Botones de Acción
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(6)

        self._name_lbl = QLabel("—")
        self._name_lbl.setWordWrap(True)
        top_row.addWidget(self._name_lbl, 1)

        self._btn_edit = QPushButton()
        self._btn_edit.setFixedSize(28, 28)
        self._btn_edit.setToolTip("Editar personaje en diálogo completo")
        self._btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_edit.clicked.connect(self.edit_requested.emit)
        top_row.addWidget(self._btn_edit)

        self._btn_close_full = QPushButton()
        self._btn_close_full.setFixedSize(28, 28)
        self._btn_close_full.setToolTip("Volver a vista de relaciones compacta")
        self._btn_close_full.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_close_full.clicked.connect(self.close_full_requested.emit)
        self._btn_close_full.hide()
        top_row.addWidget(self._btn_close_full)

        self._layout.addLayout(top_row)

        self._sub_lbl = QLabel("")
        self._layout.addWidget(self._sub_lbl)

        self._metric_lbl = QLabel("")
        self._layout.addWidget(self._metric_lbl)

        self.update_theme(ThemeManager.is_dark())

    def update_theme(self, is_dark: bool):
        fg_main = "#f2f2f7" if is_dark else "#1a1a2e"
        fg_sub  = "rgba(212,160,23,0.95)" if is_dark else "#9a5c00"
        fg_meta = "#8e8e93" if is_dark else "#7a7a8a"
        bg_hdr  = "#242426" if is_dark else "#ede8e1"
        b_border= "#3a3a3c" if is_dark else "#d4cfc8"
        tip_bg  = "#2c2c2e" if is_dark else "#faf7f3"
        tip_fg  = "#f2f2f7" if is_dark else "#1a1a2e"
        tip_b   = "#3a3a3c" if is_dark else "#c4bfb8"
        btn_e_bg = "rgba(255, 214, 10, 0.12)" if is_dark else "rgba(154, 92, 0, 0.08)"
        btn_e_hbg = "rgba(255, 214, 10, 0.25)" if is_dark else "rgba(154, 92, 0, 0.16)"
        btn_e_b = "rgba(255, 214, 10, 0.3)" if is_dark else "rgba(154, 92, 0, 0.25)"

        self.setStyleSheet(f"""
            QToolTip {{
                background-color: {tip_bg};
                color: {tip_fg};
                border: 1px solid {tip_b};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }}
            QFrame#PanelHeaderWidget {{
                background: {bg_hdr};
                border-bottom: 1px solid {b_border};
            }}
        """)
        self._name_lbl.setStyleSheet(
            f"color: {fg_main}; font-size: 15px; font-weight: 800; background:transparent;"
        )
        self._sub_lbl.setStyleSheet(
            f"color: {fg_sub}; font-size: 11px; font-weight:600; background:transparent;"
        )
        self._metric_lbl.setStyleSheet(
            f"color: {fg_meta}; font-size: 10px; background:transparent;"
        )

        self._btn_edit.setIcon(qta.icon("fa5s.edit", color="#ffd60a" if is_dark else "#9a5c00"))
        self._btn_edit.setStyleSheet(f"""
            QToolTip {{
                background-color: {tip_bg};
                color: {tip_fg};
                border: 1px solid {tip_b};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }}
            QPushButton {{
                background: {btn_e_bg};
                border: 1px solid {btn_e_b};
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background: {btn_e_hbg};
            }}
        """)

        self._btn_close_full.setIcon(qta.icon("fa5s.times", color="#f2f2f7" if is_dark else "#1a1a2e"))
        self._btn_close_full.setStyleSheet(f"""
            QToolTip {{
                background-color: {tip_bg};
                color: {tip_fg};
                border: 1px solid {tip_b};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }}
            QPushButton {{
                background: {'rgba(255, 255, 255, 0.08)' if is_dark else 'rgba(0, 0, 0, 0.06)'};
                border: 1px solid {b_border};
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background: rgba(239, 68, 68, 0.3);
                border-color: #ef4444;
            }}
        """)

    def set_character(self, char: Character, metrics: Optional[CharacterMetrics], is_full: bool = False):
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

        self._btn_close_full.setVisible(is_full)

    def clear(self):
        self._name_lbl.setText("—")
        self._sub_lbl.setText("")
        self._metric_lbl.setText("")
        self._btn_close_full.hide()


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

        bg_card = "rgba(255,255,255,0.06)" if is_dark else "rgba(0,0,0,0.04)"
        bg_card_h = "rgba(255,255,255,0.12)" if is_dark else "rgba(0,0,0,0.08)"
        fg_name = "#f2f2f7" if is_dark else "#1a1a2e"
        btn_bg = "rgba(212,160,23,0.18)" if is_dark else "rgba(154,92,0,0.12)"
        btn_border = "rgba(212,160,23,0.35)" if is_dark else "rgba(154,92,0,0.30)"
        btn_fg = "#ffd60a" if is_dark else "#9a5c00"
        tip_bg = "#2c2c2e" if is_dark else "#faf7f3"
        tip_fg = "#f2f2f7" if is_dark else "#1a1a2e"
        tip_border = "#3a3a3c" if is_dark else "#c4bfb8"

        self.setFixedHeight(48)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(f"Ver a {other.name} en el grafo y destacar sus conexiones")
        self.setStyleSheet(f"""
            QToolTip {{
                background-color: {tip_bg};
                color: {tip_fg};
                border: 1px solid {tip_border};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }}
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
            QToolTip {{
                background-color: {tip_bg};
                color: {tip_fg};
                border: 1px solid {tip_border};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }}
            QPushButton {{
                background-color: {btn_bg};
                border: 1px solid {btn_border};
                border-radius: 5px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {'rgba(212,160,23,0.45)' if is_dark else 'rgba(154,92,0,0.25)'};
                border-color: {'#ffd60a' if is_dark else '#9a5c00'};
            }}
        """)
        _oid = other_id
        btn.clicked.connect(lambda: self.jump_to.emit(_oid))
        row.addWidget(btn)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.jump_to.emit(self.other_id)
        super().mousePressEvent(event)


# ── Panel Lateral Desplegable ────────────────────────────────────────────────

class NexusSidePanel(QFrame):
    jump_to = pyqtSignal(str)
    jump_to_character_requested = pyqtSignal(str)
    open_sheet_requested = pyqtSignal(str)
    add_relation_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mode = "compact"  # "compact" (280px) o "full" (430px)
        self.setFixedWidth(280)
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
        self._scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
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
        self._current_char = char
        self._current_relations = rel_objs
        self._char_map = char_map
        self.show_character(char, rel_objs, char_map)

    def display_empty(self):
        self.clear()

    def _on_edit_clicked(self):
        if self._current_char:
            self.open_sheet_requested.emit(str(self._current_char.id))

    def _on_close_full(self):
        self._mode = "compact"
        self.setFixedWidth(280)
        if self._current_char:
            self.show_character(self._current_char, self._current_relations, self._char_map)

    def _on_open_full_sheet(self):
        self._mode = "full"
        self.setFixedWidth(430)
        if self._current_char:
            self.show_character(self._current_char, self._current_relations, self._char_map)

    def show_character(self, char: Character, relations: list[CharacterRelation],
                        char_map: dict[str, Character]):
        self._current_char = char
        self._current_relations = relations
        self._char_map = char_map
        
        m = self._metrics_map.get(str(char.id))
        is_full = (self._mode == "full")
        self._header.set_character(char, m, is_full=is_full)

        is_dark = ThemeManager.is_dark()
        fg_desc = "rgba(242,242,247,0.85)" if is_dark else "#4a4a5a"
        fg_title= "#aeaeb2" if is_dark else "#7a7a8a"
        b_sep   = "#3a3a3c" if is_dark else "#d4cfc8"

        new_body = QWidget()
        new_body.setStyleSheet("background: transparent;")
        body_layout = QVBoxLayout(new_body)
        body_layout.setContentsMargins(12, 10, 12, 12)
        body_layout.setSpacing(8)

        my_rels = [
            r for r in relations
            if str(r.char_id_a) == str(char.id) or str(r.char_id_b) == str(char.id)
        ]

        if not is_full:
            # ─────────────────────────────────────────────────────────────
            # MODO COMPACTO (280px)
            # ─────────────────────────────────────────────────────────────
            btn_sheet = QPushButton("📇  Ver Ficha Completa")
            btn_sheet.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_sheet.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 214, 10, 0.12);
                    color: #ffd60a;
                    border: 1px solid rgba(255, 214, 10, 0.35);
                    border-radius: 6px;
                    padding: 8px 12px;
                    font-size: 11px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background: rgba(255, 214, 10, 0.24);
                    border-color: #ffd60a;
                }
            """ if is_dark else """
                QPushButton {
                    background: rgba(154, 92, 0, 0.08);
                    color: #9a5c00;
                    border: 1px solid rgba(154, 92, 0, 0.25);
                    border-radius: 6px;
                    padding: 8px 12px;
                    font-size: 11px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background: rgba(154, 92, 0, 0.16);
                }
            """)
            btn_sheet.clicked.connect(self._on_open_full_sheet)
            body_layout.addWidget(btn_sheet)

            if char.description:
                desc = QLabel(char.description[:180] + ("…" if len(char.description) > 180 else ""))
                desc.setWordWrap(True)
                desc.setStyleSheet(
                    f"color: {fg_desc}; font-size:11px; "
                    f"background: transparent; line-height: 140%;"
                )
                body_layout.addWidget(desc)

            sep_row = QHBoxLayout()
            sep_lbl = QLabel(f"RELACIONES ({len(my_rels)})")
            sep_lbl.setStyleSheet(
                f"color: {fg_title}; font-size:10px; font-weight:800; letter-spacing:1px; background:transparent;"
            )
            sep_row.addWidget(sep_lbl)
            sep_row.addStretch()
            body_layout.addLayout(sep_row)

            sep = QFrame()
            sep.setFixedHeight(1)
            sep.setStyleSheet(f"background: {b_sep}; border:none;")
            body_layout.addWidget(sep)

            if not my_rels:
                empty = QLabel("Sin relaciones registradas")
                empty.setStyleSheet(f"color: {fg_title}; font-size:11px; background:transparent; padding:12px 0;")
                body_layout.addWidget(empty)
            else:
                for rel in my_rels:
                    other_id = str(rel.char_id_b if str(rel.char_id_a) == str(char.id) else rel.char_id_a)
                    other = char_map.get(other_id)
                    if not other: continue
                    card = _RelationCard(rel, other, other_id)
                    card.jump_to.connect(self._on_jump_to)
                    body_layout.addWidget(card)

            body_layout.addStretch()

        else:
            # ─────────────────────────────────────────────────────────────
            # MODO FICHA COMPLETA INTEGRADA (430px)
            # ─────────────────────────────────────────────────────────────
            tab_pane_bg = "rgba(0,0,0,0.15)" if is_dark else "rgba(255,255,255,0.4)"
            accent = "#ffd60a" if is_dark else "#9a5c00"
            tabs = QTabWidget()
            tabs.setStyleSheet(f"""
                QTabWidget::pane {{
                    border: 1px solid {b_sep};
                    border-radius: 6px;
                    background: {tab_pane_bg};
                }}
                QTabBar::tab {{
                    background: transparent;
                    color: {fg_title};
                    padding: 6px 10px;
                    font-size: 11px;
                    font-weight: 600;
                    border-bottom: 2px solid transparent;
                }}
                QTabBar::tab:selected {{
                    color: {accent};
                    border-bottom: 2px solid {accent};
                }}
            """)

            # PESTAÑA 1: Perfil & Esencia Narrativa
            ess_scroll = QScrollArea()
            ess_scroll.setWidgetResizable(True)
            ess_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            ess_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
            tab_essence = QWidget()
            tab_essence.setStyleSheet("background: transparent;")
            lay_ess = QVBoxLayout(tab_essence)
            lay_ess.setContentsMargins(10, 10, 10, 10)
            lay_ess.setSpacing(8)

            def _add_field(title: str, val: str, icon_str: str = "->"):
                if not val: return
                f_frame = QFrame()
                f_frame.setStyleSheet("background: rgba(255,255,255,0.04); border-radius: 5px;")
                f_lay = QVBoxLayout(f_frame)
                f_lay.setContentsMargins(6, 4, 6, 4)
                f_lay.setSpacing(2)
                lbl_t = QLabel(f"{icon_str} {title.upper()}")
                lbl_t.setStyleSheet(f"color: {accent}; font-size: 9px; font-weight: 800; letter-spacing: 0.5px;")
                lbl_v = QLabel(val)
                lbl_v.setWordWrap(True)
                lbl_v.setStyleSheet(f"color: {fg_desc}; font-size: 11px;")
                f_lay.addWidget(lbl_t)
                f_lay.addWidget(lbl_v)
                lay_ess.addWidget(f_frame)

            _add_field("Deseo Motivador (Propósito)", char.driving_desire, "🎯")
            _add_field("Miedo más Profundo", char.deepest_fear, "⚡")
            _add_field("Valores y Creencias", char.core_values, "⚖️")
            _add_field("Arco de Transformación", char.transformation_arc, "🔄")
            _add_field("Voz y Tono", char.distinctive_voice, "🗣️")
            _add_field("Símbolo o Metáfora", char.symbol_metaphor, "✨")

            # Datos biográficos en grid
            bio_parts = []
            if char.age: bio_parts.append(f"Edad: {char.age}")
            if char.birth_date: bio_parts.append(f"Nacimiento: {char.birth_date}")
            if char.birthplace: bio_parts.append(f"Origen: {char.birthplace}")
            if char.aliases: bio_parts.append(f"Aliases: {', '.join(char.aliases)}")
            if bio_parts:
                _add_field("Biografía", "  |  ".join(bio_parts), "📌")

            lay_ess.addStretch()
            ess_scroll.setWidget(tab_essence)
            tabs.addTab(ess_scroll, "Esencia")

            # PESTAÑA 2: Descripcion & Notas
            desc_scroll = QScrollArea()
            desc_scroll.setWidgetResizable(True)
            desc_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            desc_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
            tab_desc = QWidget()
            tab_desc.setStyleSheet("background: transparent;")
            lay_desc = QVBoxLayout(tab_desc)
            lay_desc.setContentsMargins(10, 10, 10, 10)
            lay_desc.setSpacing(10)

            lbl_d_t = QLabel("DESCRIPCION GENERAL")
            lbl_d_t.setStyleSheet(f"color: {accent}; font-size: 10px; font-weight: 800;")
            lay_desc.addWidget(lbl_d_t)

            lbl_d_v = QLabel(char.description or "Sin descripcion registrada.")
            lbl_d_v.setWordWrap(True)
            lbl_d_v.setStyleSheet(f"color: {fg_desc}; font-size: 11px; line-height: 140%;")
            lay_desc.addWidget(lbl_d_v)

            if char.notes:
                lbl_n_t = QLabel("NOTAS PRIVADAS DEL AUTOR")
                lbl_n_t.setStyleSheet("color: #38bdf8; font-size: 10px; font-weight: 800; margin-top: 10px;")
                lay_desc.addWidget(lbl_n_t)
                lbl_n_v = QLabel(char.notes)
                lbl_n_v.setWordWrap(True)
                lbl_n_v.setStyleSheet(f"color: {fg_desc}; font-size: 11px; line-height: 140%;")
                lay_desc.addWidget(lbl_n_v)

            lay_desc.addStretch()
            desc_scroll.setWidget(tab_desc)
            tabs.addTab(desc_scroll, "Historia")

            # PESTAÑA 3: Atributos Personalizados
            attrs_scroll = QScrollArea()
            attrs_scroll.setWidgetResizable(True)
            attrs_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            attrs_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
            tab_attrs = QWidget()
            tab_attrs.setStyleSheet("background: transparent;")
            lay_attrs = QVBoxLayout(tab_attrs)
            lay_attrs.setContentsMargins(10, 10, 10, 10)
            lay_attrs.setSpacing(6)

            if char.custom_attributes:
                for k, v in char.custom_attributes.items():
                    a_frame = QFrame()
                    a_frame.setStyleSheet("background: rgba(255,255,255,0.04); border-radius: 5px;")
                    a_lay = QHBoxLayout(a_frame)
                    a_lay.setContentsMargins(8, 5, 8, 5)
                    a_key = QLabel(k)
                    a_key.setStyleSheet("color: #a855f7; font-size: 11px; font-weight: 700;")
                    a_val = QLabel(str(v))
                    a_val.setWordWrap(True)
                    a_val.setStyleSheet(f"color: {fg_desc}; font-size: 11px;")
                    a_lay.addWidget(a_key)
                    a_lay.addStretch()
                    a_lay.addWidget(a_val)
                    lay_attrs.addWidget(a_frame)
            else:
                lbl_no_attr = QLabel("Sin atributos personalizados.")
                lbl_no_attr.setStyleSheet(f"color: {fg_title}; font-size: 11px; padding: 12px 0;")
                lay_attrs.addWidget(lbl_no_attr)

            lay_attrs.addStretch()
            attrs_scroll.setWidget(tab_attrs)
            tabs.addTab(attrs_scroll, "Atributos")

            # PESTAÑA 4: 👥 Relaciones (con scroll propio para muchas conexiones)
            tab_rels_wrapper = QWidget()
            tab_rels_wrapper_lay = QVBoxLayout(tab_rels_wrapper)
            tab_rels_wrapper_lay.setContentsMargins(0, 0, 0, 0)
            tab_rels_wrapper_lay.setSpacing(0)

            rels_scroll = QScrollArea()
            rels_scroll.setWidgetResizable(True)
            rels_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            rels_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

            tab_rels = QWidget()
            tab_rels.setStyleSheet("background: transparent;")
            lay_rels = QVBoxLayout(tab_rels)
            lay_rels.setContentsMargins(10, 10, 10, 10)
            lay_rels.setSpacing(6)

            if not my_rels:
                empty = QLabel("Sin relaciones registradas")
                empty.setStyleSheet(f"color: {fg_title}; font-size: 11px; padding:12px 0;")
                lay_rels.addWidget(empty)
            else:
                for rel in my_rels:
                    other_id = str(rel.char_id_b if str(rel.char_id_a) == str(char.id) else rel.char_id_a)
                    other = char_map.get(other_id)
                    if not other: continue
                    card = _RelationCard(rel, other, other_id)
                    card.jump_to.connect(self._on_jump_to)
                    lay_rels.addWidget(card)

            lay_rels.addStretch()
            rels_scroll.setWidget(tab_rels)
            tab_rels_wrapper_lay.addWidget(rels_scroll)
            tabs.addTab(tab_rels_wrapper, f"👥 Relaciones ({len(my_rels)})")

            body_layout.addWidget(tabs)

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
        self.setFixedWidth(280)
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



