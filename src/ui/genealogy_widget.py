"""
genealogy_widget.py — Widget gráfico radial interactivo para visualizar la genealogía
y mapa de relaciones de un personaje en Aura Writer.
"""

from __future__ import annotations

import math

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsScene, QGraphicsView, QGraphicsEllipseItem,
    QGraphicsTextItem, QGraphicsLineItem, QGraphicsRectItem,
    QGraphicsItem
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QPen, QBrush, QPainter

from core.models import Character, CharacterRelation, RELATION_TYPES, RELATION_COLORS, RELATION_ICONS


class GenealogyWidget(QWidget):
    """
    Widget visual que dibuja un mapa conceptual radial centrado en un personaje,
    mostrando todas sus conexiones familiares, mentorías, rivalidades, etc.
    """

    def __init__(self, character: Character,
                 characters: list[Character] | None = None,
                 relations: list[CharacterRelation] | None = None,
                 parent=None):
        super().__init__(parent)
        self._char = character
        self._characters = list(characters or [])
        self._relations = list(relations or [])
        self._gen_zoom = 1.0

        self._build_ui()

    def set_data(self, character: Character,
                 characters: list[Character] | None = None,
                 relations: list[CharacterRelation] | None = None):
        """Actualiza los datos y redibuja el mapa."""
        self._char = character
        if characters is not None:
            self._characters = list(characters)
        if relations is not None:
            self._relations = list(relations)
        self._title_lbl.setText(f"MAPA DE RELACIONES DE {self._char.name.upper()}")
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Header
        header = QHBoxLayout()
        self._title_lbl = QLabel(f"MAPA DE RELACIONES DE {self._char.name.upper()}")
        self._title_lbl.setStyleSheet(
            "color: #8e8e93; font-size: 10px; font-weight: 700; "
            "letter-spacing: 0.5px; background: transparent;"
        )
        header.addWidget(self._title_lbl)
        header.addStretch()

        btn_refresh = QPushButton("🔄 Actualizar")
        btn_refresh.clicked.connect(self.refresh)
        header.addWidget(btn_refresh)
        layout.addLayout(header)

        # Escena y vista del grafo
        self._gen_scene = QGraphicsScene(self)
        self._gen_view = QGraphicsView(self._gen_scene)
        self._gen_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._gen_view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self._gen_view.setTransformationAnchor(
            QGraphicsView.ViewportAnchor.AnchorUnderMouse
        )
        self._gen_view.setViewportUpdateMode(
            QGraphicsView.ViewportUpdateMode.FullViewportUpdate
        )
        self._gen_view.setBackgroundBrush(QBrush(QColor("#141416")))
        self._gen_view.wheelEvent = self._gen_wheel_event
        layout.addWidget(self._gen_view, 1)

        # Leyenda
        legend = QHBoxLayout()
        for rtype in RELATION_TYPES:
            color = RELATION_COLORS.get(rtype, "#636366")
            icon = RELATION_ICONS.get(rtype, "●")
            lbl = QLabel(f"{icon} {rtype.capitalize()}")
            lbl.setStyleSheet(
                f"color:{color}; font-size:10px; font-weight:bold; padding:0 6px;"
            )
            legend.addWidget(lbl)
        legend.addStretch()
        layout.addLayout(legend)

        QTimer.singleShot(50, self.refresh)

    def _gen_wheel_event(self, event):
        """Zoom con rueda del mouse en la vista de genealogía."""
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self._gen_zoom *= factor
        if 0.2 < self._gen_zoom < 5.0:
            self._gen_view.scale(factor, factor)
        else:
            self._gen_zoom /= factor

    def refresh(self):
        """Construye el mapa conceptual radial centrado en el personaje."""
        self._gen_scene.clear()
        char_map = {c.id: c for c in self._characters}

        # Buscar personajes conectados
        connected_ids: set[str] = set()
        connected_rels: list[CharacterRelation] = []
        for rel in self._relations:
            other_id = None
            if rel.char_id_a == self._char.id:
                other_id = rel.char_id_b
            elif rel.char_id_b == self._char.id:
                other_id = rel.char_id_a
            if other_id and other_id in char_map:
                connected_ids.add(other_id)
                connected_rels.append(rel)

        if not connected_ids:
            msg = QGraphicsTextItem("Sin relaciones aún\n\nAñade relaciones en la pestaña 🔗")
            msg.setDefaultTextColor(QColor("#636366"))
            msg.setFont(QFont("Segoe UI", 13))
            self._gen_scene.addItem(msg)
            self._draw_center_node(0, 0)
            self._gen_view.fitInView(
                self._gen_scene.sceneRect().adjusted(-60, -60, 60, 60),
                Qt.AspectRatioMode.KeepAspectRatio
            )
            return

        # Layout radial
        center_x, center_y = 0.0, 0.0
        radius = 180 + len(connected_ids) * 12
        n = len(connected_ids)

        # Nodo central
        center_node_r = 32
        self._draw_center_node(center_x, center_y, center_node_r)

        # Nodos periféricos
        peripheral_nodes: dict[str, tuple[float, float]] = {}
        for i, cid in enumerate(sorted(connected_ids)):
            angle = (2 * math.pi * i / n) - math.pi / 2
            px = center_x + radius * math.cos(angle)
            py = center_y + radius * math.sin(angle)
            peripheral_nodes[cid] = (px, py)

            char = char_map[cid]
            self._draw_peripheral_node(char, px, py)

        # Aristas
        for rel in connected_rels:
            other_id = rel.char_id_b if rel.char_id_a == self._char.id else rel.char_id_a
            if other_id not in peripheral_nodes:
                continue
            px, py = peripheral_nodes[other_id]
            self._draw_edge(
                center_x, center_y, px, py,
                rel.relation_type, rel.label, rel.intensity
            )

        # Ajustar vista
        QTimer.singleShot(80, lambda: self._gen_view.fitInView(
            self._gen_scene.sceneRect().adjusted(-80, -80, 80, 80),
            Qt.AspectRatioMode.KeepAspectRatio
        ))

    def _draw_center_node(self, x: float, y: float, r: float = 32):
        """Dibuja el nodo central (personaje actual)."""
        halo_r = r + 6
        halo = QGraphicsEllipseItem(-halo_r, -halo_r, halo_r * 2, halo_r * 2)
        halo.setPos(x, y)
        halo_color = QColor("#5e5ce6")
        halo_color.setAlphaF(0.25)
        halo.setBrush(QBrush(halo_color))
        halo.setPen(QPen(Qt.PenStyle.NoPen))
        halo.setZValue(0)
        self._gen_scene.addItem(halo)

        node = QGraphicsEllipseItem(-r, -r, r * 2, r * 2)
        node.setPos(x, y)
        node.setBrush(QBrush(QColor("#5e5ce6")))
        node.setPen(QPen(QColor("#8b8bf5"), 3))
        node.setZValue(2)
        self._gen_scene.addItem(node)

        name = self._char.name
        initials = "".join(w[0].upper() for w in name.split()[:2]) if name else "?"
        lbl = QGraphicsTextItem(initials)
        lbl.setDefaultTextColor(Qt.GlobalColor.white)
        font = QFont("Segoe UI", int(r * 0.48))
        font.setBold(True)
        lbl.setFont(font)
        br = lbl.boundingRect()
        lbl.setPos(x - br.width() / 2, y - br.height() / 2)
        lbl.setZValue(3)
        self._gen_scene.addItem(lbl)

        name_lbl = QGraphicsTextItem(name)
        name_lbl.setDefaultTextColor(QColor("#f2f2f7"))
        name_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        nbr = name_lbl.boundingRect()
        name_lbl.setPos(x - nbr.width() / 2, y + r + 8)
        name_lbl.setZValue(3)
        self._gen_scene.addItem(name_lbl)

        role_lbl = QGraphicsTextItem(self._char.role)
        role_lbl.setDefaultTextColor(QColor("#8e8e93"))
        role_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Normal))
        rbr = role_lbl.boundingRect()
        role_lbl.setPos(x - rbr.width() / 2, y + r + 8 + nbr.height())
        role_lbl.setZValue(3)
        self._gen_scene.addItem(role_lbl)

    def _draw_peripheral_node(self, char: Character, x: float, y: float):
        """Dibuja un nodo periférico (personaje conectado)."""
        r = 22
        role_colors = {
            "Protagonista": "#ffd60a", "Antagonista": "#ff453a",
            "Misterioso":   "#bf5af2", "Secundario":  "#636366",
            "Otro":         "#48484a"
        }
        color = QColor(role_colors.get(char.role, "#636366"))

        node = QGraphicsEllipseItem(-r, -r, r * 2, r * 2)
        node.setPos(x, y)
        node.setBrush(QBrush(color.lighter(130)))
        node.setPen(QPen(color.darker(130), 2))
        node.setZValue(2)
        node.setToolTip(f"[{char.role}] {char.name}")
        node.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self._gen_scene.addItem(node)

        initials = "".join(w[0].upper() for w in char.name.split()[:2]) if char.name else "?"
        lbl = QGraphicsTextItem(initials)
        lbl.setDefaultTextColor(Qt.GlobalColor.white)
        font = QFont("Segoe UI", 9)
        font.setBold(True)
        lbl.setFont(font)
        br = lbl.boundingRect()
        lbl.setPos(x - br.width() / 2, y - br.height() / 2)
        lbl.setZValue(3)
        self._gen_scene.addItem(lbl)

        name_lbl = QGraphicsTextItem(char.name)
        name_lbl.setDefaultTextColor(QColor("#d1d1d6"))
        name_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        nbr = name_lbl.boundingRect()
        name_lbl.setPos(x - nbr.width() / 2, y + r + 4)
        name_lbl.setZValue(3)
        self._gen_scene.addItem(name_lbl)

    def _draw_edge(self, x1: float, y1: float, x2: float, y2: float,
                   relation_type: str, label: str, intensity: int):
        """Dibuja una arista con estilo por tipo de relación."""
        color_hex = RELATION_COLORS.get(relation_type, "#636366")
        color = QColor(color_hex)
        width = 1.5 + intensity * 0.4

        halo_color = QColor(color_hex)
        halo_color.setAlphaF(0.15)
        halo = QGraphicsLineItem(x1, y1, x2, y2)
        halo_pen = QPen(halo_color, width * 4)
        halo_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        halo.setPen(halo_pen)
        halo.setZValue(0)
        self._gen_scene.addItem(halo)

        line = QGraphicsLineItem(x1, y1, x2, y2)
        pen = QPen(color, width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        dash_patterns = {
            "pareja": None,
            "familiar": [8, 4],
            "descendiente": [2, 4],
            "rival": [10, 4, 2, 4],
            "mentor": [12, 3, 3, 3],
            "amigo": [6, 3],
            "otro": [2, 6],
        }
        dash = dash_patterns.get(relation_type)
        if dash:
            pen.setStyle(Qt.PenStyle.CustomDashLine)
            pen.setDashPattern(dash)
        line.setPen(pen)
        line.setZValue(1)
        self._gen_scene.addItem(line)

        icon = RELATION_ICONS.get(relation_type, "")
        display = f"{icon} {relation_type.capitalize()}"
        if label:
            display += f"\n{label}"

        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2

        text_item = QGraphicsTextItem(display)
        text_item.setDefaultTextColor(QColor(color_hex).lighter(150))
        text_item.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        tbr = text_item.boundingRect()
        text_item.setPos(mid_x - tbr.width() / 2, mid_y - tbr.height() / 2)
        text_item.setZValue(4)

        bg = QGraphicsRectItem(
            mid_x - tbr.width() / 2 - 4,
            mid_y - tbr.height() / 2 - 2,
            tbr.width() + 8,
            tbr.height() + 4
        )
        bg_color = QColor("#141416")
        bg_color.setAlphaF(0.85)
        bg.setBrush(QBrush(bg_color))
        border_color = QColor(color_hex)
        border_color.setAlphaF(0.4)
        bg.setPen(QPen(border_color, 1))
        bg.setZValue(3)

        self._gen_scene.addItem(bg)
        self._gen_scene.addItem(text_item)
