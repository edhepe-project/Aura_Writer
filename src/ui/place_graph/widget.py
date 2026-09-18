"""
widget.py — Orquestador principal del Atlas Literario (Grafo de Lugares).
Modularizado en models.py, items.py, physics.py y scene.py.
"""
from __future__ import annotations

import math
import random
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QLineEdit, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal

from core.models import Place, PlaceLink
from .models import PLACE_CATEGORY_COLORS, CONNECTION_STYLES
from .items import PlaceNodeItem, PlaceLinkItem
from .physics import compute_places_layout
from .scene import PlaceGraphScene, PlaceGraphView


class PlaceGraphWidget(QWidget):
    """
    Lienzo completo del Atlas Literario con toolbar, búsqueda interactiva,
    física orbital/constelación, árbol de estancias y leyenda semántica.
    """
    place_selected = pyqtSignal(str)
    place_double_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._places: list[Place] = []
        self._links: list[PlaceLink] = []
        self._node_map: dict[str, PlaceNodeItem] = {}
        self._setup_ui()

    @property
    def _link_items(self) -> list[PlaceLinkItem]:
        """Alias de compatibilidad: apunta a _scene._all_edges."""
        return self._scene._all_edges

    # ── UI ──────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Toolbar superior
        tb = QFrame()
        tb.setFixedHeight(50)
        tb.setStyleSheet("""
            QFrame { background-color: #161618; border-bottom: 1px solid #2c2c2e; }
            QLabel { color: #f2f2f7; font-weight: bold; font-size: 12px; }
            QLineEdit {
                background: #2c2c2e; color: #f2f2f7;
                border: 1px solid #3a3a3c; border-radius: 6px;
                padding: 4px 8px; font-size: 11px;
            }
            QComboBox {
                background: #2c2c2e; color: #f2f2f7;
                border: 1px solid #3a3a3c; border-radius: 6px;
                padding: 4px 8px; font-size: 11px;
            }
            QPushButton {
                background: #2c2c2e; color: #f2f2f7;
                border: 1px solid #3a3a3c; border-radius: 6px;
                padding: 5px 10px; font-size: 11px; font-weight: bold;
            }
            QPushButton:hover { background: #3a3a3c; border-color: #ffd60a; }
        """)
        tbl = QHBoxLayout(tb)
        tbl.setContentsMargins(14, 0, 14, 0)
        tbl.setSpacing(10)

        ico_lbl = QLabel("🗺️  ATLAS DE CONEXIONES")
        ico_lbl.setStyleSheet("color: #ffd60a; font-weight: bold; font-size: 12px;")
        tbl.addWidget(ico_lbl)
        tbl.addSpacing(12)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Buscar escenario...")
        self._search_input.setClearButtonEnabled(True)
        self._search_input.setMaximumWidth(180)
        self._search_input.textChanged.connect(self._on_search)
        tbl.addWidget(self._search_input)

        tbl.addWidget(QLabel("Vista:"))
        self._view_mode_combo = QComboBox()
        self._view_mode_combo.addItem("🌐 Red Geográfica", "network")
        self._view_mode_combo.addItem("🏛️  Árbol de Estancias", "tree")
        self._view_mode_combo.setMaximumWidth(175)
        self._view_mode_combo.currentIndexChanged.connect(self._on_view_mode_changed)
        tbl.addWidget(self._view_mode_combo)

        tbl.addStretch()

        self._btn_layout = QPushButton("⚡ Reorganizar")
        self._btn_layout.setToolTip("Distribuye los lugares con simulación orbital")
        self._btn_layout.clicked.connect(self.reorganize_layout)
        tbl.addWidget(self._btn_layout)

        btn_zoom_in = QPushButton("＋")
        btn_zoom_in.setFixedWidth(34)
        btn_zoom_in.clicked.connect(lambda: self._view.scale(1.2, 1.2))
        tbl.addWidget(btn_zoom_in)

        btn_zoom_out = QPushButton("－")
        btn_zoom_out.setFixedWidth(34)
        btn_zoom_out.clicked.connect(lambda: self._view.scale(1 / 1.2, 1 / 1.2))
        tbl.addWidget(btn_zoom_out)

        btn_fit = QPushButton("↺ Ajustar")
        btn_fit.clicked.connect(self._fit_to_view)
        tbl.addWidget(btn_fit)

        root.addWidget(tb)

        # Escena + Vista
        self._scene = PlaceGraphScene(self)
        self._scene.place_selected.connect(self.place_selected)
        self._scene.place_double_clicked.connect(self.place_double_clicked)
        self._scene.background_clicked.connect(self._on_background_clicked)

        self._view = PlaceGraphView(self._scene, self)
        root.addWidget(self._view, stretch=1)

        # Leyenda inferior
        root.addWidget(self._build_legend())

    def _build_legend(self) -> QFrame:
        bar = QFrame()
        bar.setFixedHeight(34)
        bar.setStyleSheet("""
            QFrame { background: #161618; border-top: 1px solid #2c2c2e; }
            QLabel { color: #8e8e93; font-size: 10px; padding: 0 6px; }
        """)
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(14, 0, 14, 0)
        bl.setSpacing(0)

        legend_items = [
            ("ruta",     "Ruta"),
            ("frontera", "Frontera"),
            ("portal",   "Portal"),
            ("río",      "Río"),
            ("camino",   "Camino"),
            ("comercio", "Comercio"),
        ]
        for key, display in legend_items:
            color = CONNECTION_STYLES[key]["color"]
            dot = QLabel("━")
            dot.setStyleSheet(f"color: {color}; font-size: 14px; padding: 0 2px;")
            lbl = QLabel(display)
            lbl.setStyleSheet("color: #8e8e93; font-size: 10px; padding-right: 10px;")
            bl.addWidget(dot)
            bl.addWidget(lbl)

        bl.addStretch()

        hier_dot = QLabel("╌╌")
        hier_dot.setStyleSheet("color: #bf5af2; font-size: 12px; padding: 0 2px;")
        hier_lbl = QLabel("Jerarquía (contiene)")
        hier_lbl.setStyleSheet("color: #8e8e93; font-size: 10px;")
        bl.addWidget(hier_dot)
        bl.addWidget(hier_lbl)

        return bar

    # ── Datos ───────────────────────────────────────────────────────────────

    def set_data(self, places: list[Place], links: list[PlaceLink]):
        self._places = list(places)
        self._links = list(links)
        self._rebuild_graph()

    def _on_view_mode_changed(self):
        self._rebuild_graph()

    def _on_background_clicked(self):
        pass

    # ── Construcción del Grafo ───────────────────────────────────────────────

    def _rebuild_graph(self):
        self._scene.clear()
        self._node_map.clear()
        self._scene._nodes.clear()
        self._scene._all_edges.clear()
        self._scene._adj.clear()
        self._scene._focused_id = None

        if not self._places:
            return

        mode = self._view_mode_combo.currentData() if hasattr(self, "_view_mode_combo") else "network"

        parent_map = {p.id: p.parent_place_id for p in self._places}
        children_map: dict[str, list[str]] = {p.id: [] for p in self._places}
        for p in self._places:
            if p.parent_place_id and p.parent_place_id in children_map:
                children_map[p.parent_place_id].append(p.id)

        depth_map: dict[str, int] = {}
        for p in self._places:
            d, cur, seen = 0, p.parent_place_id, set()
            while cur and cur not in seen:
                seen.add(cur); d += 1; cur = parent_map.get(cur, "")
            depth_map[p.id] = d

        # 1. Modo Árbol Jerárquico
        if mode == "tree":
            roots = [p for p in self._places
                     if not p.parent_place_id or p.parent_place_id not in depth_map]
            if not roots:
                roots = list(self._places)
            current_x = 0.0
            x_spacing, y_spacing = 180.0, 160.0

            def _layout_tree(nid: str, depth: int) -> float:
                nonlocal current_x
                child_ids = children_map.get(nid, [])
                place_obj = next((p for p in self._places if p.id == nid), None)
                if not place_obj:
                    return current_x
                if not child_ids:
                    nx = current_x; current_x += x_spacing
                else:
                    cxs = [_layout_tree(cid, depth + 1) for cid in child_ids]
                    nx = sum(cxs) / len(cxs)
                ny = depth * y_spacing
                node = PlaceNodeItem(place_obj, nx, ny,
                                     depth=depth, child_count=len(child_ids))
                self._scene.addItem(node)
                self._node_map[place_obj.id] = node
                self._scene._nodes[place_obj.id] = node
                self._scene._adj[place_obj.id] = set()
                return nx

            for r in roots:
                _layout_tree(r.id, 0)
                current_x += 80.0

            # En modo árbol, conectamos las ramas padre → hijo
            for p in self._places:
                if p.parent_place_id and p.parent_place_id in self._node_map and p.id in self._node_map:
                    na = self._node_map[p.parent_place_id]
                    nb = self._node_map[p.id]
                    h_link = PlaceLink(
                        place_id_a=p.parent_place_id,
                        place_id_b=p.id,
                        label="contiene",
                        connection_type="contiene",
                        bidirectional=False
                    )
                    item = PlaceLinkItem(h_link, na, nb, curvature=0.0)
                    self._scene.addItem(item)
                    self._scene._all_edges.append(item)
                    self._scene._adj.setdefault(p.parent_place_id, set()).add(p.id)
                    self._scene._adj.setdefault(p.id, set()).add(p.parent_place_id)

        # 2. Modo Red Geográfica
        else:
            positions = compute_places_layout(self._places, self._links)
            for place in self._places:
                pos = positions.get(place.id, (0.0, 0.0))
                depth = depth_map.get(place.id, 0)
                child_count = len(children_map.get(place.id, []))
                node = PlaceNodeItem(place, pos[0], pos[1], depth=depth, child_count=child_count)
                self._scene.addItem(node)
                self._node_map[place.id] = node
                self._scene._nodes[place.id] = node
                self._scene._adj[place.id] = set()

            # En Red Geográfica: dibujamos las conexiones geográficas reales con curvatura suave
            edge_idx: dict[frozenset, int] = {}
            seen_pairs: set[frozenset] = set()
            for link in self._links:
                pair = frozenset([link.place_id_a, link.place_id_b])
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                na = self._node_map.get(link.place_id_a)
                nb = self._node_map.get(link.place_id_b)
                if na and nb:
                    edge_idx[pair] = edge_idx.get(pair, 0) + 1
                    curv = 0.08 * (1 if edge_idx[pair] % 2 == 1 else -1)
                    item = PlaceLinkItem(link, na, nb, curvature=curv)
                    self._scene.addItem(item)
                    self._scene._all_edges.append(item)
                    self._scene._adj.setdefault(link.place_id_a, set()).add(link.place_id_b)
                    self._scene._adj.setdefault(link.place_id_b, set()).add(link.place_id_a)

        self._fit_to_view()

    # ── Reorganización y Búsqueda ───────────────────────────────────────────

    def reorganize_layout(self):
        """Recalcula la física orbital y reposiciona los nodos suavemente."""
        if not self._places:
            return
        positions = compute_places_layout(self._places, self._links)
        for place_id, (px, py) in positions.items():
            node = self._node_map.get(place_id)
            if node:
                node.setPos(px, py)

        for edge in self._scene._all_edges:
            edge._update_path()

        self._scene.update()
        self._fit_to_view()

    def _on_search(self, text: str):
        query = text.lower().strip()
        for node in self._node_map.values():
            match = not query or query in node.place.name.lower() or query in node.place.category.lower()
            node.setSelected(match if query else False)
            node.setOpacity(1.0 if (not query or match) else 0.18)

    def _fit_to_view(self):
        rect = self._scene.itemsBoundingRect()
        if not rect.isEmpty():
            self._view.fitInView(rect.adjusted(-90, -90, 90, 90),
                                 Qt.AspectRatioMode.KeepAspectRatio)
