"""
widget.py — Orquestador principal del Atlas Literario (Grafo Planetario de Lugares).
Modularizado en models.py, items.py, physics.py y scene.py.
"""
from __future__ import annotations

import math
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame, QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from core.models import Place, PlaceLink
from core.theme_manager import ThemeManager
from .models import PLACE_CATEGORY_COLORS, CONNECTION_STYLES
from .items import PlaceNodeItem, PlaceLinkItem
from .physics import compute_places_layout
from .scene import PlaceGraphScene, PlaceGraphView


class PlaceGraphWidget(QWidget):
    """
    Lienzo planetario del Atlas Literario con toolbar, búsqueda interactiva,
    sistema solar orbital y leyenda semántica de rutas.
    """
    place_selected = pyqtSignal(str)
    place_double_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._places: list[Place] = []
        self._links: list[PlaceLink] = []
        self._node_map: dict[str, PlaceNodeItem] = {}
        self._project_manager = None   # se asigna desde el controlador externo
        self._setup_ui()

    @property
    def _link_items(self) -> list[PlaceLinkItem]:
        """Alias de compatibilidad: apunta a _scene._all_edges."""
        return self._scene._all_edges

    # ── UI ──────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        is_dark = ThemeManager.is_dark()
        bg_bar = "#161618" if is_dark else "#e8e4dc"
        border_col = "#2c2c2e" if is_dark else "#d4cfc8"
        fg_col = "#f2f2f7" if is_dark else "#1c1c1e"
        btn_bg = "#2c2c2e" if is_dark else "#ded8ce"
        btn_hover = "#3a3a3c" if is_dark else "#d0c9bd"
        input_bg = "#2c2c2e" if is_dark else "#ffffff"

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Toolbar superior
        tb = QFrame()
        tb.setFixedHeight(46)
        tb.setStyleSheet(f"""
            QFrame {{ background-color: {bg_bar}; border-bottom: 1px solid {border_col}; }}
            QLabel {{ color: {fg_col}; font-weight: bold; font-size: 11px; }}
            QLineEdit {{
                background: {input_bg}; color: {fg_col};
                border: 1px solid {border_col}; border-radius: 6px;
                padding: 4px 8px; font-size: 11px;
            }}
            QLineEdit:focus {{
                border: 1px solid #ffd60a;
            }}
            QComboBox {{
                background: {input_bg}; color: {fg_col};
                border: 1px solid {border_col}; border-radius: 6px;
                padding: 3px 8px; font-size: 11px;
            }}
            QPushButton {{
                background: {btn_bg}; color: {fg_col};
                border: 1px solid {border_col}; border-radius: 6px;
                padding: 4px 8px; font-size: 11px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {btn_hover}; border-color: #ffd60a; }}
        """)
        tbl = QHBoxLayout(tb)
        tbl.setContentsMargins(10, 0, 10, 0)
        tbl.setSpacing(8)

        # Título compacto con icono
        ico_lbl = QLabel("🗺️ ATLAS")
        ico_lbl.setStyleSheet("color: #ffd60a; font-weight: bold; font-size: 12px; letter-spacing: 0.5px;")
        tbl.addWidget(ico_lbl)

        # Buscador con tamaño fijo y visible
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("🔍 Buscar escenario...")
        self._search_input.setClearButtonEnabled(True)
        self._search_input.setFixedWidth(160)
        self._search_input.textChanged.connect(self._on_search)
        tbl.addWidget(self._search_input)

        tbl.addStretch()

        # Botón Reorganizar órbitas
        self._btn_layout = QPushButton("⚡ Órbitas")
        self._btn_layout.setToolTip("Reorganizar órbitas y sistemas planetarios")
        self._btn_layout.clicked.connect(self.reorganize_layout)
        tbl.addWidget(self._btn_layout)

        # Botón Analizar Presencia
        self._btn_analyze = QPushButton("🔍 Analizar")
        self._btn_analyze.setToolTip(
            "Analiza el texto de los capítulos para detectar dónde están los personajes"
        )
        self._btn_analyze.clicked.connect(self._on_analyze_clicked)
        tbl.addWidget(self._btn_analyze)

        # Selector de capítulo
        self._chapter_combo = QComboBox()
        self._chapter_combo.setFixedWidth(150)
        self._chapter_combo.setToolTip("Filtrar presencias por capítulo")
        self._chapter_combo.addItem("📖 Todos los cap.", None)
        self._chapter_combo.currentIndexChanged.connect(self._on_chapter_filter_changed)
        tbl.addWidget(self._chapter_combo)

        # Separador visual
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setStyleSheet(f"color: {border_col};")
        tbl.addWidget(sep)

        # Controles de Zoom
        btn_zoom_in = QPushButton("＋")
        btn_zoom_in.setFixedSize(26, 26)
        btn_zoom_in.setToolTip("Acercar zoom")
        btn_zoom_in.clicked.connect(lambda: self._view.scale(1.2, 1.2))
        tbl.addWidget(btn_zoom_in)

        btn_zoom_out = QPushButton("－")
        btn_zoom_out.setFixedSize(26, 26)
        btn_zoom_out.setToolTip("Alejar zoom")
        btn_zoom_out.clicked.connect(lambda: self._view.scale(1 / 1.2, 1 / 1.2))
        tbl.addWidget(btn_zoom_out)

        btn_fit = QPushButton("↺")
        btn_fit.setFixedSize(26, 26)
        btn_fit.setToolTip("Ajustar al centro")
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
        is_dark = ThemeManager.is_dark()
        bg_bar = "#161618" if is_dark else "#e8e4dc"
        border_col = "#2c2c2e" if is_dark else "#d4cfc8"
        lbl_col = "#8e8e93" if is_dark else "#5c5c60"

        bar = QFrame()
        bar.setFixedHeight(34)
        bar.setStyleSheet(f"""
            QFrame {{ background: {bg_bar}; border-top: 1px solid {border_col}; }}
            QLabel {{ color: {lbl_col}; font-size: 10px; padding: 0 6px; }}
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
            lbl.setStyleSheet(f"color: {lbl_col}; font-size: 10px; padding-right: 10px;")
            bl.addWidget(dot)
            bl.addWidget(lbl)

        bl.addStretch()

        hier_dot = QLabel("╌╌")
        hier_dot.setStyleSheet("color: #bf5af2; font-size: 12px; padding: 0 2px;")
        hier_lbl = QLabel("Órbita (Estancia/Interior)")
        hier_lbl.setStyleSheet(f"color: {lbl_col}; font-size: 10px;")
        bl.addWidget(hier_dot)
        bl.addWidget(hier_lbl)

        return bar

    # ── Datos ───────────────────────────────────────────────────────────────

    def set_data(self, places: list[Place], links: list[PlaceLink]):
        self._places = list(places)
        self._links = list(links)
        self._rebuild_graph()

    def set_project_manager(self, pm) -> None:
        """Conecta el widget con el ProjectManager para acceder a presencias y capítulos."""
        self._project_manager = pm
        self._refresh_chapter_combo()

    def _refresh_chapter_combo(self) -> None:
        """Actualiza el combo de capítulos con los del proyecto actual."""
        self._chapter_combo.blockSignals(True)
        self._chapter_combo.clear()
        self._chapter_combo.addItem("📖 Todos los capítulos", None)

        pm = self._project_manager
        if pm and pm.metadata:
            for obra in pm.metadata.obras:
                for libro in obra.libros:
                    for cap in libro.capitulos:
                        self._chapter_combo.addItem(cap.title, cap.id)

        self._chapter_combo.blockSignals(False)

    def load_presences(self, chapter_id: str | None = None) -> None:
        """Renderiza los badges de presencia en el Atlas para el capítulo dado o la última ubicación global."""
        pm = self._project_manager
        if not pm or not pm.metadata:
            return

        character_map = {c.id: c for c in pm.metadata.characters}
        
        # Mapa de orden cronológico de capítulos
        chapter_order_map = {}
        idx = 0
        for obra in pm.metadata.obras:
            for libro in obra.libros:
                for cap in libro.capitulos:
                    idx += 1
                    chapter_order_map[cap.id] = cap.in_world_order if cap.in_world_order > 0 else idx

        self._scene.load_presences(
            pm.metadata.presences,
            chapter_id=chapter_id,
            character_map=character_map,
            chapter_order_map=chapter_order_map,
        )

    def _on_analyze_clicked(self) -> None:
        """Analiza todos los capítulos del proyecto en busca de presencias."""
        pm = self._project_manager
        if not pm or not pm.metadata:
            QMessageBox.warning(self, "Sin proyecto", "Abre un proyecto primero.")
            return

        try:
            from tools.nlp import PresenceAnalyzer
        except ImportError:
            QMessageBox.warning(
                self, "Módulo no disponible",
                "El módulo de análisis NLP no está disponible."
            )
            return

        analyzer = PresenceAnalyzer(
            characters=pm.metadata.characters,
            places=pm.metadata.places,
            custom_vocabulary=pm.metadata.custom_vocabulary,
        )

        # Preservar presencias manuales (is_manual=True)
        manual_presences = [p for p in pm.metadata.presences if p.is_manual]
        new_presences = list(manual_presences)

        # Analizar todos los capítulos
        for obra in pm.metadata.obras:
            for libro in obra.libros:
                for cap in libro.capitulos:
                    if not cap.content_file:
                        continue
                    html = pm.read_chapter_content(cap.content_file)
                    detected = analyzer.analyze_chapter(cap, html)
                    new_presences.extend(detected)

        pm.metadata.presences = new_presences
        pm.save_project()

        # Refrescar el Atlas con las nuevas presencias
        chapter_id = self._chapter_combo.currentData()
        self.load_presences(chapter_id)

        total = len(new_presences) - len(manual_presences)
        QMessageBox.information(
            self, "✅ Análisis completado",
            f"Se detectaron {total} presencia(s) de personajes en el Atlas."
        )

    def _on_chapter_filter_changed(self, _index: int) -> None:
        """Actualiza los badges al cambiar el capítulo seleccionado."""
        chapter_id = self._chapter_combo.currentData()
        self.load_presences(chapter_id)

    def _on_background_clicked(self):
        pass

    # ── Construcción del Grafo Planetario ────────────────────────────────────

    def _rebuild_graph(self):
        self._scene.clear()
        self._node_map.clear()
        self._scene._nodes.clear()
        self._scene._all_edges.clear()
        self._scene._adj.clear()
        self._scene._focused_id = None

        if not self._places:
            return

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

        # Calcular posiciones planetarias
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

        # 1. Enlaces orbitales (Planeta Padre → Luna/Estancia)
        edge_idx: dict[frozenset, int] = {}
        for p in self._places:
            if p.parent_place_id and p.parent_place_id in self._node_map and p.id in self._node_map:
                na = self._node_map[p.parent_place_id]
                nb = self._node_map[p.id]
                h_link = PlaceLink(
                    place_id_a=p.parent_place_id,
                    place_id_b=p.id,
                    label="órbita",
                    connection_type="contiene",
                    bidirectional=False
                )
                pair = frozenset([p.parent_place_id, p.id])
                edge_idx[pair] = edge_idx.get(pair, 0) + 1
                curv = 0.12 * (1 if edge_idx[pair] % 2 == 1 else -1)
                item = PlaceLinkItem(h_link, na, nb, curvature=curv)
                self._scene.addItem(item)
                self._scene._all_edges.append(item)
                self._scene._adj.setdefault(p.parent_place_id, set()).add(p.id)
                self._scene._adj.setdefault(p.id, set()).add(p.parent_place_id)

        # 2. Enlaces de Rutas Geográficas manuales
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
                curv = 0.16 * (1 if edge_idx[pair] % 2 == 1 else -1)
                item = PlaceLinkItem(link, na, nb, curvature=curv)
                self._scene.addItem(item)
                self._scene._all_edges.append(item)
                self._scene._adj.setdefault(link.place_id_a, set()).add(link.place_id_b)
                self._scene._adj.setdefault(link.place_id_b, set()).add(link.place_id_a)

        self._fit_to_view()

    # ── Reorganización y Búsqueda ───────────────────────────────────────────

    def reorganize_layout(self):
        """Recalcula la física planetaria y actualiza el grafo."""
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
