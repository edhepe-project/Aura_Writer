"""
cards.py — Tarjetas interactivas y cabecera del panel lateral del grafo (NexusSidePanel).
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal
import qtawesome as qta

from core.models import Character, CharacterRelation, RELATION_ICONS
from core.theme_manager import ThemeManager
from ui.relation_graph.models import CharacterMetrics, RELATION_STYLES, get_race


class _PanelHeader(QFrame):
    """Cabecera superior del panel lateral que muestra nombre, rol, métricas y acciones."""
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
        if race:       parts.append(f"{race}")
        if char.role:  parts.append(f"{char.role}")
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


class _RelationCard(QFrame):
    """Tarjeta individual que representa una relación entre personajes con soporte de navegación."""
    jump_to = pyqtSignal(str)

    def __init__(self, rel: CharacterRelation, other: Character, other_id: str, current_char_id: str = "", parent=None):
        super().__init__(parent)
        self.other_id = other_id
        rtype = rel.relation_type
        style = RELATION_STYLES.get(rtype, RELATION_STYLES["otro"])
        color = style["color"]
        icon = RELATION_ICONS.get(rtype, "👥")
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

        # Determinar etiqueta direccional relativa al personaje seleccionado
        if rtype == "descendiente":
            if current_char_id and getattr(rel, "char_id_a", None) == current_char_id:
                label_text = f"Hijo/a de → {other.name}"
            elif current_char_id and getattr(rel, "char_id_b", None) == current_char_id:
                label_text = f"Progenitor de → {other.name}"
            else:
                label_text = rel.label if rel.label else "Descendiente"
        elif rtype == "mentor":
            if current_char_id and getattr(rel, "char_id_a", None) == current_char_id:
                label_text = f"Mentor de → {other.name}"
            elif current_char_id and getattr(rel, "char_id_b", None) == current_char_id:
                label_text = f"Aprendiz de → {other.name}"
            else:
                label_text = rel.label if rel.label else "Mentoría"
        elif rtype == "pareja":
            label_text = f"Pareja de → {other.name}" if not rel.label else rel.label
        elif rtype == "familiar":
            label_text = f"Familiar de → {other.name}" if not rel.label else rel.label
        elif rtype == "amigo":
            label_text = f"Amigo/a de → {other.name}" if not rel.label else rel.label
        elif rtype == "rival":
            label_text = f"Rival de → {other.name}" if not rel.label else rel.label
        else:
            label_text = rel.label if rel.label else rtype.capitalize()

        display_text = f"{icon} {label_text}".strip() if icon else label_text
        rel_lbl = QLabel(display_text)
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

    def mousePressEvent(self, a0):
        event = a0
        if event.button() == Qt.MouseButton.LeftButton:
            self.jump_to.emit(self.other_id)
        super().mousePressEvent(event)
