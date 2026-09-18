"""
views.py — Construcción de vistas Compacta y Ficha Completa para NexusSidePanel.
"""

from typing import Callable
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QPushButton, QScrollArea, QTabWidget
)
from PyQt6.QtCore import Qt

from core.models import Character, CharacterRelation
from core.theme_manager import ThemeManager
from ui.relation_graph.side_panel.cards import _RelationCard


def build_compact_view(
    char: Character,
    my_rels: list[CharacterRelation],
    char_map: dict[str, Character],
    on_open_full_sheet: Callable[[], None],
    on_jump_to: Callable[[str], None]
) -> QWidget:
    """Construye la vista compacta (280px) del panel lateral."""
    is_dark = ThemeManager.is_dark()
    fg_desc = "rgba(242,242,247,0.85)" if is_dark else "#4a4a5a"
    fg_title = "#aeaeb2" if is_dark else "#7a7a8a"
    b_sep = "#3a3a3c" if is_dark else "#d4cfc8"

    new_body = QWidget()
    new_body.setStyleSheet("background: transparent;")
    body_layout = QVBoxLayout(new_body)
    body_layout.setContentsMargins(12, 10, 12, 12)
    body_layout.setSpacing(8)

    btn_sheet = QPushButton("📇  Ver Ficha Completa")
    btn_sheet.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_sheet.setStyleSheet(f"""
        QPushButton {{
            background: {'rgba(255, 214, 10, 0.12)' if is_dark else 'rgba(154, 92, 0, 0.08)'};
            color: {'#ffd60a' if is_dark else '#9a5c00'};
            border: 1px solid {'rgba(255, 214, 10, 0.35)' if is_dark else 'rgba(154, 92, 0, 0.25)'};
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 11px;
            font-weight: 700;
        }}
        QPushButton:hover {{
            background: {'rgba(255, 214, 10, 0.24)' if is_dark else 'rgba(154, 92, 0, 0.16)'};
            border-color: {'#ffd60a' if is_dark else '#9a5c00'};
        }}
    """)
    btn_sheet.clicked.connect(on_open_full_sheet)
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
            other_id = rel.char_id_b if rel.char_id_a == char.id else rel.char_id_a
            other = char_map.get(other_id)
            if not other:
                continue
            card = _RelationCard(rel, other, other_id, current_char_id=char.id)
            card.jump_to.connect(on_jump_to)
            body_layout.addWidget(card)

    body_layout.addStretch()
    return new_body


def build_full_sheet_view(
    char: Character,
    my_rels: list[CharacterRelation],
    char_map: dict[str, Character],
    on_jump_to: Callable[[str], None]
) -> QWidget:
    """Construye la vista de ficha completa integrada (430px con pestañas) del panel lateral."""
    is_dark = ThemeManager.is_dark()
    fg_desc = "rgba(242,242,247,0.85)" if is_dark else "#4a4a5a"
    fg_title = "#aeaeb2" if is_dark else "#7a7a8a"
    b_sep = "#3a3a3c" if is_dark else "#d4cfc8"

    new_body = QWidget()
    new_body.setStyleSheet("background: transparent;")
    body_layout = QVBoxLayout(new_body)
    body_layout.setContentsMargins(12, 10, 12, 12)
    body_layout.setSpacing(8)

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
            a_val = QLabel(v)
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

    # PESTAÑA 4: Relaciones
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
            other_id = rel.char_id_b if rel.char_id_a == char.id else rel.char_id_a
            other = char_map.get(other_id)
            if not other: continue
            card = _RelationCard(rel, other, other_id, current_char_id=char.id)
            card.jump_to.connect(on_jump_to)
            lay_rels.addWidget(card)

    lay_rels.addStretch()
    rels_scroll.setWidget(tab_rels)
    tab_rels_wrapper_lay.addWidget(rels_scroll)
    tabs.addTab(tab_rels_wrapper, f"👥 Relaciones ({len(my_rels)})")

    body_layout.addWidget(tabs)
    return new_body
