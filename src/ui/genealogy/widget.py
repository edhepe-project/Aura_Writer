"""
widget.py — Orquestador Visual del Árbol Genealógico y Pedigree Jerárquico.
Maneja la escena gráfica, vistas de zoom/pan y trazado interactivo de linaje.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsScene, QGraphicsView, QGraphicsPathItem, QGraphicsTextItem
)
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import (
    QFont, QColor, QPen, QBrush, QPainter, QPainterPath
)

from core.models import Character, CharacterRelation
from core.theme_manager import ThemeManager
from .items import FlowchartCardItem, FlowchartConnectorItem
from .layout_engine import GenealogyLayoutEngine


class GenealogyWidget(QWidget):
    """
    Widget visual de Árbol Genealógico y Pedigree Jerárquico por Subárboles.
    Dispone de forma limpia y matemáticamente separada todas las ramas familiares (paternas, maternas, etc.).
    Permite hacer clic en cualquier miembro para iluminar toda la ruta directa de su linaje ancestral.
    """

    character_switched = pyqtSignal(str)

    def __init__(self, character: Character,
                 characters: list[Character] | None = None,
                 relations: list[CharacterRelation] | None = None,
                 parent=None):
        super().__init__(parent)
        self._char = character
        self._characters = list(characters or [])
        self._relations = list(relations or [])
        self._gen_zoom = 1.0
        self._selected_lineage_char_id: str | None = None

        self._card_items: dict[str, FlowchartCardItem] = {}
        self._connector_items: list[FlowchartConnectorItem] = []
        self._parent_map: dict[str, list[str]] = {}

        self._build_ui()

    def set_data(self, character: Character,
                 characters: list[Character] | None = None,
                 relations: list[CharacterRelation] | None = None):
        """Actualiza los datos y redibuja el árbol genealógico completo."""
        self._char = character
        if characters is not None:
            self._characters = list(characters)
        if relations is not None:
            self._relations = list(relations)
        self._selected_lineage_char_id = None
        self._title_lbl.setText(f"LINAJE: {self._char.name.upper()}")
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Barra superior con navegación y trazado de linaje
        header = QHBoxLayout()
        header.setSpacing(8)

        self._title_lbl = QLabel(f"LINAJE: {self._char.name.upper()}")
        self._title_lbl.setStyleSheet(
            "color: #8e8e93; font-size: 12px; font-weight: 800; "
            "letter-spacing: 0.5px; background: transparent; padding-left: 2px;"
        )
        header.addWidget(self._title_lbl)

        self._btn_reset_highlight = QPushButton("✕ Quitar Filtro")
        self._btn_reset_highlight.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_reset_highlight.setToolTip("Quitar resplandor de linaje y mostrar todo el árbol normalmente")
        self._btn_reset_highlight.setStyleSheet(
            "QPushButton { font-size: 11px; font-weight: 600; padding: 3px 10px; "
            "background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); "
            "border-radius: 5px; } QPushButton:hover { background: rgba(239, 68, 68, 0.25); color: #ffffff; }"
        )
        self._btn_reset_highlight.clicked.connect(self._clear_lineage_highlight)
        self._btn_reset_highlight.setVisible(False)
        header.addWidget(self._btn_reset_highlight)

        header.addStretch(1)

        btn_fit = QPushButton("Centrar")
        btn_fit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_fit.setToolTip("Ajustar y centrar el diagrama en pantalla")
        btn_fit.clicked.connect(self._fit_tree_view)
        header.addWidget(btn_fit)

        btn_refresh = QPushButton("Recargar")
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh.setToolTip("Recalcular y redibujar el árbol")
        btn_refresh.clicked.connect(self.refresh)
        header.addWidget(btn_refresh)
        layout.addLayout(header)

        # Escena y vista gráfica
        is_dark = ThemeManager.is_dark()
        self._gen_scene = QGraphicsScene(self)
        self._gen_view = QGraphicsView(self._gen_scene)
        self._gen_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._gen_view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self._gen_view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self._gen_view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        bg_col = "#141416" if is_dark else "#f8f9fa"
        self._gen_view.setBackgroundBrush(QBrush(QColor(bg_col)))
        self._gen_view.wheelEvent = self._gen_wheel_event
        self._gen_scene.mousePressEvent = self._on_scene_mouse_press
        layout.addWidget(self._gen_view, 1)

        # Leyenda de flujo familiar
        legend = QHBoxLayout()
        legend_items = [
            ("Progenitores / Ancestros", "#22c55e"),
            ("Personaje Principal", "#6366f1"),
            ("Pareja / Cónyuge", "#ec4899"),
            ("Hermanos", "#3b82f6"),
            ("Descendientes / Hijos", "#14b8a6"),
            ("Linaje Iluminado", "#fbbf24")
        ]
        for name, col in legend_items:
            lbl = QLabel(name)
            lbl.setStyleSheet(f"color:{col}; font-size:10px; font-weight:bold; padding:0 8px;")
            legend.addWidget(lbl)
        legend.addStretch()
        layout.addLayout(legend)

        QTimer.singleShot(60, self.refresh)

    def _on_scene_mouse_press(self, event):
        item = self._gen_scene.itemAt(event.scenePos(), self._gen_view.transform())
        if item is None or isinstance(item, FlowchartConnectorItem):
            self._clear_lineage_highlight()
        QGraphicsScene.mousePressEvent(self._gen_scene, event)

    def _gen_wheel_event(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self._gen_zoom *= factor
        if 0.2 < self._gen_zoom < 5.0:
            self._gen_view.scale(factor, factor)
        else:
            self._gen_zoom /= factor

    def _fit_tree_view(self):
        rect = self._gen_scene.sceneRect()
        if not rect.isNull() and rect.isValid():
            self._gen_view.fitInView(rect.adjusted(-60, -60, 60, 60), Qt.AspectRatioMode.KeepAspectRatio)

    def _on_card_clicked(self, char_id: str):
        if self._selected_lineage_char_id == char_id:
            self._clear_lineage_highlight()
            return

        self._selected_lineage_char_id = char_id
        char_map = {c.id: c for c in self._characters}

        ancestors_set: set[str] = set()
        active_edges_set: set[tuple[str, str]] = set()

        def _trace_up(curr_id: str, visited: set[str]):
            parents = self._parent_map.get(curr_id, [])
            for p_id in parents:
                if p_id not in visited:
                    visited.add(p_id)
                    ancestors_set.add(p_id)
                    active_edges_set.add((curr_id, p_id))
                    _trace_up(p_id, visited)

        _trace_up(char_id, {char_id})
        all_active_nodes = ancestors_set | {char_id}

        for cid, card in self._card_items.items():
            card._is_selected = (cid == char_id)
            card._is_in_lineage = (cid in ancestors_set)
            card._is_dimmed = (cid not in all_active_nodes)
            card.update()

        for conn in self._connector_items:
            has_match = any(e in active_edges_set for e in conn.edge_keys)
            conn._is_highlighted = has_match
            conn._is_dimmed = not has_match
            conn.update()

        curr_name = char_map.get(char_id, self._char).name
        if ancestors_set:
            self._title_lbl.setText(f"LINAJE ACTIVO: {curr_name.upper()} ➔ ANCESTROS ({len(ancestors_set)})")
        else:
            self._title_lbl.setText(f"LINAJE: {curr_name.upper()} (RAÍZ)")

        self._btn_reset_highlight.setVisible(True)
        self._gen_scene.update()

    def _clear_lineage_highlight(self):
        self._selected_lineage_char_id = None
        self._btn_reset_highlight.setVisible(False)

        for card in self._card_items.values():
            card._is_selected = False
            card._is_in_lineage = False
            card._is_dimmed = False
            card.update()

        for conn in self._connector_items:
            conn._is_highlighted = False
            conn._is_dimmed = False
            conn.update()

        self._title_lbl.setText(f"LINAJE: {self._char.name.upper()}")
        self._gen_scene.update()

    def refresh(self):
        """Construye el árbol genealógico completo mediante el motor jerárquico por subárboles."""
        self._gen_scene.clear()
        self._card_items.clear()
        self._connector_items.clear()
        self._parent_map.clear()
        self._selected_lineage_char_id = None
        self._btn_reset_highlight.setVisible(False)

        is_dark = ThemeManager.is_dark()
        bg_col = "#141416" if is_dark else "#f8f9fa"
        self._gen_view.setBackgroundBrush(QBrush(QColor(bg_col)))
        char_map = {c.id: c for c in self._characters}

        # 1. Calcular disposición espacial con el Layout Engine
        node_coords, child_to_parents, parent_to_children, partners, siblings = GenealogyLayoutEngine.compute_layout(
            self._char, self._characters, self._relations
        )
        self._parent_map = child_to_parents

        CARD_W = GenealogyLayoutEngine.CARD_W
        CARD_H = GenealogyLayoutEngine.CARD_H
        V_GAP = GenealogyLayoutEngine.V_GAP

        # 2. Renderizar tarjetas en la escena
        ancestor_tags = {
            1: "PROGENITOR",
            2: "ABUELO(A)",
            3: "BISABUELO(A)",
            4: "TATARABUELO(A)",
            5: "TRASTATARABUELO(A)"
        }
        desc_tags = {
            1: "HIJO(A)",
            2: "NIETO(A)",
            3: "BISNIETO(A)",
            4: "TATARANIETO(A)",
            5: "TRASTATARANIETO(A)"
        }

        for cid, (cx, cy) in node_coords.items():
            ch = char_map.get(cid)
            if not ch:
                continue
            is_central = (cid == self._char.id)
            gen_idx = int(round(cy / V_GAP))

            if is_central:
                tag = "★ PERSONAJE PRINCIPAL"
                node_type = "central"
            elif gen_idx < 0:
                dist = abs(gen_idx)
                tag = ancestor_tags.get(dist, f"ANCESTRO (-{dist})")
                node_type = "ancestor" if dist == 1 else "grandparent"
            elif gen_idx == 0:
                if cid in partners:
                    tag = "PAREJA / CÓNYUGE"
                    node_type = "partner"
                else:
                    tag = "HERMANO(A)"
                    node_type = "sibling"
            else:
                tag = desc_tags.get(gen_idx, f"DESCENDIENTE (+{gen_idx})")
                node_type = "descendant" if gen_idx == 1 else "grandchild"

            card = FlowchartCardItem(
                ch, generation_level=gen_idx, node_type=node_type,
                is_central=is_central, custom_tag=tag, on_click=self._on_card_clicked
            )
            card.setPos(cx, cy)
            self._gen_scene.addItem(card)
            self._card_items[cid] = card

        # Puente de pareja
        if partners and partners[0] in node_coords:
            p_id = partners[0]
            c_x = node_coords[self._char.id][0]
            p_x = node_coords[p_id][0]
            self._draw_horizontal_bridge(
                c_x + (CARD_W / 2), 0.0,
                p_x - (CARD_W / 2), 0.0,
                label="Pareja", color="#ec4899"
            )

        # 3. Renderizar conexiones ortogonales aisladas por pareja
        parent_pairs: dict[tuple[str, ...], list[str]] = {}
        for cid, (cx, cy) in node_coords.items():
            p_ids = tuple(sorted([p for p in child_to_parents.get(cid, []) if p in node_coords]))
            if p_ids:
                parent_pairs.setdefault(p_ids, []).append(cid)

        # Si hay hermanos asociados a los padres
        if siblings and self._char.id in node_coords:
            p_ids = tuple(sorted([p for p in child_to_parents.get(self._char.id, []) if p in node_coords]))
            if p_ids:
                for s_id in siblings:
                    s_parents = tuple(sorted([p for p in child_to_parents.get(s_id, []) if p in node_coords]))
                    if not s_parents and s_id not in parent_pairs.get(p_ids, []):
                        parent_pairs.setdefault(p_ids, []).append(s_id)

        for p_ids, c_ids in parent_pairs.items():
            if len(p_ids) == 1:
                p_id = p_ids[0]
                px, py = node_coords[p_id]
                origin_x, origin_y = px, py + CARD_H / 2
                trunk_edges = [(cid, p_id) for cid in c_ids]
            elif len(p_ids) == 2:
                p1_id, p2_id = p_ids[0], p_ids[1]
                p1_x, p1_y = node_coords[p1_id]
                p2_x, p2_y = node_coords[p2_id]

                bridge_y = p1_y + CARD_H / 2 + 18.0
                p1_edges = [(cid, p1_id) for cid in c_ids]
                p2_edges = [(cid, p2_id) for cid in c_ids]

                self._draw_connector_line(
                    p1_x, p1_y + CARD_H / 2, p1_x, bridge_y, color="#22c55e", edge_keys=p1_edges
                )
                self._draw_connector_line(
                    p2_x, p2_y + CARD_H / 2, p2_x, bridge_y, color="#22c55e", edge_keys=p2_edges
                )

                origin_x = (p1_x + p2_x) / 2
                origin_y = bridge_y

                self._draw_connector_line(
                    p1_x, bridge_y, origin_x, bridge_y, color="#22c55e", edge_keys=p1_edges
                )
                self._draw_connector_line(
                    p2_x, bridge_y, origin_x, bridge_y, color="#22c55e", edge_keys=p2_edges
                )
                trunk_edges = [(cid, pid) for cid in c_ids for pid in p_ids]
            else:
                continue

            first_child_y = node_coords[c_ids[0]][1]
            child_top_y = first_child_y - (41.0 if self._char.id in c_ids and len(c_ids) == 1 else CARD_H / 2)
            bus_y = (origin_y + child_top_y) / 2

            self._draw_connector_line(origin_x, origin_y, origin_x, bus_y, color="#22c55e", edge_keys=trunk_edges)

            for cid in c_ids:
                cx, cy = node_coords[cid]
                c_top = cy - (41.0 if cid == self._char.id else CARD_H / 2)
                single_child_edges = [(cid, pid) for pid in p_ids]

                if cx != origin_x:
                    self._draw_connector_line(
                        origin_x, bus_y, cx, bus_y, color="#22c55e", edge_keys=single_child_edges
                    )

                self._draw_connector_arrow(cx, bus_y, cx, c_top, color="#22c55e", edge_keys=single_child_edges)

        QTimer.singleShot(80, self._fit_tree_view)

    def _draw_connector_line(self, x1: float, y1: float, x2: float, y2: float,
                             color: str = "#22c55e", edge_keys: list[tuple[str, str]] | None = None):
        conn = FlowchartConnectorItem(
            QPointF(x1, y1), QPointF(x2, y2), mid_y=(y1 + y2) / 2,
            color=color, has_arrow=False, edge_keys=edge_keys
        )
        self._gen_scene.addItem(conn)
        self._connector_items.append(conn)

    def _draw_connector_arrow(self, x1: float, y1: float, x2: float, y2: float,
                              color: str = "#22c55e", edge_keys: list[tuple[str, str]] | None = None):
        conn = FlowchartConnectorItem(
            QPointF(x1, y1), QPointF(x2, y2), mid_y=(y1 + y2) / 2,
            color=color, has_arrow=True, edge_keys=edge_keys
        )
        self._gen_scene.addItem(conn)
        self._connector_items.append(conn)

    def _draw_horizontal_bridge(self, x1: float, y1: float, x2: float, y2: float, label: str, color: str):
        conn = FlowchartConnectorItem(
            QPointF(x1, y1), QPointF(x2, y2), mid_y=(y1 + y2) / 2,
            color=color, has_arrow=False
        )
        self._gen_scene.addItem(conn)
        self._connector_items.append(conn)

        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        is_dark = ThemeManager.is_dark()

        ring_r = 9.0
        ring_rect = QRectF(mid_x - ring_r, mid_y - ring_r, ring_r * 2, ring_r * 2)
        ring_path = QPainterPath()
        ring_path.addEllipse(ring_rect)

        ring_bg = QGraphicsPathItem(ring_path)
        ring_bg.setBrush(QBrush(QColor("#18181b" if is_dark else "#ffffff")))
        ring_bg.setPen(QPen(QColor(color), 1.6))
        ring_bg.setZValue(25)
        ring_bg.setToolTip("Pareja / Matrimonio")
        self._gen_scene.addItem(ring_bg)
