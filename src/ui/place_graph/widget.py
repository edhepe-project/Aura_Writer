"""
widget.py — Orquestador principal del Atlas Literario (Grafo Planetario de Lugares).
Modularizado en models.py, items.py, physics.py y scene.py.
"""
from __future__ import annotations

import math
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame, QComboBox, QMessageBox, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot

from core.models import Place, PlaceLink
from core.theme_manager import ThemeManager
from .models import PLACE_CATEGORY_COLORS, CONNECTION_STYLES
from .items import PlaceNodeItem, PlaceLinkItem
from .physics import compute_places_layout
from .scene import PlaceGraphScene, PlaceGraphView
from .layout_worker import _LayoutWorker


class PlaceGraphWidget(QWidget):
    """
    Lienzo planetario del Atlas Literario con toolbar, búsqueda interactiva,
    sistema solar orbital y leyenda semántica de rutas.
    """
    place_selected = pyqtSignal(str)
    place_double_clicked = pyqtSignal(str)
    chapter_changed = pyqtSignal(object)  # chapter_id (str | None)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._places: list[Place] = []
        self._links: list[PlaceLink] = []
        self._node_map: dict[str, PlaceNodeItem] = {}
        self._project_manager = None
        self._layout_worker: "_LayoutWorker | None" = None  # hilo de fisica activo
        self._setup_ui()
        self._apply_theme()
        ThemeManager.signals.theme_changed.connect(self._apply_theme)

    @property
    def _link_items(self) -> list[PlaceLinkItem]:
        """Alias de compatibilidad: apunta a _scene._all_edges."""
        return self._scene._all_edges

    # ── UI ──────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Toolbar superior (estilo estándar como en el story_graph)
        from PyQt6.QtWidgets import QToolBar, QWidget, QSizePolicy
        tb = QToolBar()
        tb.setMovable(False)
        tb.setFloatable(False)

        # Título compacto
        ico_lbl = QLabel(" ATLAS GEOGRÁFICO ")
        ico_lbl.setStyleSheet("font-weight: bold; font-size: 11px; letter-spacing: 0.5px;")
        tb.addWidget(ico_lbl)
        
        tb.addSeparator()

        # Buscador
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Buscar escenario...")
        self._search_input.setClearButtonEnabled(True)
        self._search_input.setFixedWidth(160)
        self._search_input.textChanged.connect(self._on_search)
        tb.addWidget(self._search_input)

        # Checkbox: Órbitas activas (mostrar/ocultar aristas)
        from PyQt6.QtWidgets import QCheckBox
        self._edges_visible = True
        self._chk_edges = QCheckBox(" Órbitas ")
        self._chk_edges.setChecked(True)
        self._chk_edges.setToolTip("Mostrar / Ocultar las líneas de conexión entre lugares")
        self._chk_edges.setCursor(Qt.CursorShape.PointingHandCursor)
        self._chk_edges.stateChanged.connect(self._toggle_edges)
        tb.addWidget(self._chk_edges)
        
        tb.addSeparator()

        # Selector de capítulo
        self._chapter_combo = QComboBox()
        self._chapter_combo.setFixedWidth(150)
        self._chapter_combo.setToolTip("Filtrar presencias por capítulo")
        self._chapter_combo.addItem("📖 Todos los cap.", None)
        self._chapter_combo.currentIndexChanged.connect(self._on_chapter_filter_changed)
        tb.addWidget(self._chapter_combo)

        # Filtro por personaje
        self._char_filter_combo = QComboBox()
        self._char_filter_combo.setFixedWidth(130)
        self._char_filter_combo.setToolTip("Resaltar trayectoria de un personaje")
        self._char_filter_combo.addItem("👤 Todos", None)
        self._char_filter_combo.currentIndexChanged.connect(self._on_char_filter_changed)
        tb.addWidget(self._char_filter_combo)

        # Espaciador para empujar los controles a los lados
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tb.addWidget(spacer)

        # Controles de Zoom y Ajuste
        from PyQt6.QtGui import QAction
        import qtawesome as qta
        
        self.act_zoom_in = QAction(qta.icon("fa5s.search-plus"), "Zoom +", self)
        self.act_zoom_in.setToolTip("Acercar zoom")
        self.act_zoom_in.triggered.connect(lambda: self._view.scale(1.2, 1.2))
        tb.addAction(self.act_zoom_in)

        self.act_zoom_out = QAction(qta.icon("fa5s.search-minus"), "Zoom -", self)
        self.act_zoom_out.setToolTip("Alejar zoom")
        self.act_zoom_out.triggered.connect(lambda: self._view.scale(1 / 1.2, 1 / 1.2))
        tb.addAction(self.act_zoom_out)

        self.act_fit = QAction(qta.icon("fa5s.compress-arrows-alt"), "Ajustar", self)
        self.act_fit.setToolTip("Ajustar al centro / Encuadrar todo")
        self.act_fit.triggered.connect(self._fit_to_view)
        tb.addAction(self.act_fit)

        tb.addSeparator()

        # Boton Cuadricula de Presencias (como acción)
        self.act_grid = QAction(qta.icon("fa5s.th"), "Cuadrícula", self)
        self.act_grid.setToolTip("Abrir la Cuadrícula de Presencias (personajes x capítulos)")
        self.act_grid.triggered.connect(self._open_presence_grid)
        tb.addAction(self.act_grid)

        root.addWidget(tb)
        self.tb = tb


        # -- Contenedor con QStackedWidget: Overlay de carga + Vista --------
        self._stack = QStackedWidget()

        # Capa 0: Overlay de carga (se muestra mientras calcula el layout)
        self._overlay = QFrame()
        overlay_lay = QVBoxLayout(self._overlay)
        overlay_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._loading_lbl = QLabel("Calculando mapa orbital...")
        overlay_lay.addWidget(self._loading_lbl)
        self._stack.addWidget(self._overlay)        # index 0

        # Capa 1: Escena + Vista real
        graph_container = QWidget()
        gc_lay = QVBoxLayout(graph_container)
        gc_lay.setContentsMargins(0, 0, 0, 0)
        gc_lay.setSpacing(0)

        self._scene = PlaceGraphScene(self)
        self._scene.place_selected.connect(self.place_selected)
        self._scene.place_double_clicked.connect(self.place_double_clicked)
        self._scene.background_clicked.connect(self._on_background_clicked)

        self._view = PlaceGraphView(self._scene, self)
        gc_lay.addWidget(self._view, stretch=1)
        self._stack.addWidget(graph_container)  # index 1

        root.addWidget(self._stack, stretch=1)

        # Leyenda inferior
        root.addWidget(self._build_legend())

        # Mostrar overlay al inicio hasta que los datos lleguen
        self._stack.setCurrentIndex(0)


    def _build_legend(self) -> QFrame:
        self.bar = QFrame()
        self.bar.setFixedHeight(34)
        bl = QHBoxLayout(self.bar)
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
            if not hasattr(self, "_legend_labels"):
                self._legend_labels = []
            self._legend_labels.append(lbl)
            bl.addWidget(dot)
            bl.addWidget(lbl)

        bl.addStretch()

        hier_dot = QLabel("╌╌")
        hier_dot.setStyleSheet("color: #bf5af2; font-size: 12px; padding: 0 2px;")
        self.hier_lbl = QLabel("Órbita (Estancia/Interior)")
        
        bl.addWidget(hier_dot)
        bl.addWidget(self.hier_lbl)

        return self.bar

    def _apply_theme(self):
        import qtawesome as qta
        tc = ThemeManager.theme_colors()
        bg_bar = tc["bg_card"]
        border_col = tc["border"]
        fg_col = tc["fg_text"]
        input_bg = tc["bg_input"]
        accent = tc["accent"]
        lbl_col = tc["sub_text"]

        # 1) Toolbar general
        self.setStyleSheet(f"""
            QToolBar {{
                background-color: {bg_bar};
                border-bottom: 1px solid {border_col};
                padding: 4px;
            }}
            QLineEdit {{
                background-color: {input_bg};
                color: {fg_col};
                border: 1px solid {border_col};
                border-radius: 4px;
                padding: 3px 6px;
            }}
            QComboBox {{
                background-color: {input_bg};
                color: {fg_col};
                border: 1px solid {border_col};
                border-radius: 4px;
                padding: 3px 6px;
            }}
            QCheckBox {{
                color: {fg_col};
                font-weight: bold;
            }}
            QLabel {{
                color: {fg_col};
            }}
            QPushButton {{
                background-color: {tc["bg_card"]};
                color: {fg_col};
                border: 1px solid {border_col};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QPushButton:hover {{
                background-color: {tc["border"]};
            }}
        """)
        
        self._overlay.setStyleSheet(f"background-color: {tc['bg_main']};")
        self._loading_lbl.setStyleSheet(f"color: {accent}; font-weight: bold; font-size: 14px;")
        
        if hasattr(self, "act_zoom_in"):
            self.act_zoom_in.setIcon(qta.icon("fa5s.search-plus", color=fg_col))
            self.act_zoom_out.setIcon(qta.icon("fa5s.search-minus", color=fg_col))
            self.act_fit.setIcon(qta.icon("fa5s.compress-arrows-alt", color=fg_col))
            self.act_grid.setIcon(qta.icon("fa5s.th", color=accent))
        
        if hasattr(self, "bar"):
            self.bar.setStyleSheet(f"""
                QFrame {{ background: {bg_bar}; border-top: 1px solid {border_col}; }}
                QLabel {{ color: {lbl_col}; font-size: 10px; padding: 0 6px; }}
            """)
            self.hier_lbl.setStyleSheet(f"color: {lbl_col}; font-size: 10px;")
            
        for lbl in getattr(self, "_legend_labels", []):
            lbl.setStyleSheet(f"color: {lbl_col}; font-size: 10px; padding-right: 10px;")

        if hasattr(self._scene, "update_theme"):
            self._scene.update_theme()

    # ── Datos ───────────────────────────────────────────────────────────────

    def set_data(self, places: list[Place], links: list[PlaceLink]):
        self._places = list(places)
        self._links = list(links)
        self._rebuild_graph()

    def set_project_manager(self, pm) -> None:
        """Conecta el widget con el ProjectManager para acceder a presencias y capítulos."""
        self._project_manager = pm
        self._refresh_chapter_combo()
        self._refresh_char_filter_combo()

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

    def _refresh_char_filter_combo(self) -> None:
        """Actualiza el combo de personajes para el filtro del Atlas."""
        self._char_filter_combo.blockSignals(True)
        self._char_filter_combo.clear()
        self._char_filter_combo.addItem("👤 Todos", None)

        pm = self._project_manager
        if pm and pm.metadata:
            _ROLE_ORDER = {"Protagonista": 0, "Antagonista": 1, "Secundario": 2, "Misterioso": 3, "Otro": 4}
            chars = sorted(
                pm.metadata.characters,
                key=lambda c: (_ROLE_ORDER.get(c.role, 5), (c.name or "").lower())
            )
            for char in chars:
                self._char_filter_combo.addItem(f"👤 {char.name}", char.id)

        self._char_filter_combo.blockSignals(False)

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
        self.chapter_changed.emit(chapter_id)
        # Re-aplicar filtro de personaje si estaba activo
        char_id = self._char_filter_combo.currentData()
        if char_id:
            self._apply_char_filter(char_id)

    def _on_char_filter_changed(self, _index: int) -> None:
        """Resalta la trayectoria del personaje seleccionado en el Atlas."""
        char_id = self._char_filter_combo.currentData()
        self._apply_char_filter(char_id)

    def _apply_char_filter(self, char_id: str | None) -> None:
        """
        Resalta los nodos donde el personaje tiene presencia y atenúa el resto.
        Si char_id es None, restaura todos los nodos a opacidad completa.
        """
        if not char_id:
            for node in self._node_map.values():
                node.setOpacity(1.0)
            return

        pm = self._project_manager
        if not pm or not pm.metadata:
            return

        chapter_id = self._chapter_combo.currentData()
        all_presences = getattr(pm.metadata, "presences", [])

        # Filtrar presencias del personaje (aplicando capítulo si hay uno activo)
        char_presences = [
            p for p in all_presences
            if p.character_id == char_id
            and (chapter_id is None or p.chapter_id == chapter_id)
        ]
        active_place_ids = {p.place_id for p in char_presences}

        for place_id, node in self._node_map.items():
            node.setOpacity(1.0 if place_id in active_place_ids else 0.18)

    def _on_background_clicked(self):
        pass

    # ── Construcción del Grafo Planetario ────────────────────────────────────

    def _rebuild_graph(self):
        """
        Inicia la reconstruccion del grafo en dos fases:
          1. Limpia la escena y muestra el overlay de carga (instantaneo, en el hilo principal).
          2. Lanza un QThread que calcula compute_places_layout() en background.
          3. Al terminar el hilo, _on_layout_ready() construye nodos/edges y oculta el overlay.
        Esto evita que la UI se congele durante el calculo de fisica orbital.
        """
        # Limpiar estado anterior
        # IMPORTANTE: limpiar _presence_badges ANTES de scene.clear().
        # scene.clear() destruye los QGraphicsItem en C++, pero las referencias
        # Python en _presence_badges siguen vivas y causarian RuntimeError
        # si _clear_presence_badges() las toca despues.
        self._scene._presence_badges.clear()
        self._scene.clear()
        self._node_map.clear()
        self._scene._nodes.clear()
        self._scene._all_edges.clear()
        self._scene._adj.clear()
        self._scene._focused_id = None

        if not self._places:
            self._stack.setCurrentIndex(1)  # mostrar grafo vacio
            return

        # Para un rendimiento instantáneo (0ms de retardo), si hay un número estándar de lugares
        # calculamos las posiciones directamente en el hilo principal sin pasar por el overlay ni el QThread.
        if len(self._places) <= 120:
            positions = compute_places_layout(self._places, self._links)
            self._on_layout_ready(positions)
            return

        # Mostrar overlay únicamente para grafos gigantescos (>120 lugares)
        self._stack.setCurrentIndex(0)

        # Cancelar hilo previo si sigue vivo
        if self._layout_worker and self._layout_worker.isRunning():
            self._layout_worker.quit()
            self._layout_worker.wait(200)

        self._layout_worker = _LayoutWorker(self._places, self._links)
        self._layout_worker.layout_ready.connect(self._on_layout_ready)
        self._layout_worker.start()

    @pyqtSlot(dict)
    def _on_layout_ready(self, positions: dict):
        """Recibe las posiciones calculadas por el hilo y construye el grafo en el hilo principal."""
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

        for place in self._places:
            pos = positions.get(place.id, (0.0, 0.0))
            depth = depth_map.get(place.id, 0)
            child_count = len(children_map.get(place.id, []))
            node = PlaceNodeItem(place, pos[0], pos[1], depth=depth, child_count=child_count)
            self._scene.addItem(node)
            self._node_map[place.id] = node
            self._scene._nodes[place.id] = node
            self._scene._adj[place.id] = set()

        # 1. Enlaces orbitales (Planeta Padre -> Luna/Estancia)
        edge_idx: dict[frozenset, int] = {}
        for p in self._places:
            if p.parent_place_id and p.parent_place_id in self._node_map and p.id in self._node_map:
                na = self._node_map[p.parent_place_id]
                nb = self._node_map[p.id]
                h_link = PlaceLink(
                    place_id_a=p.parent_place_id,
                    place_id_b=p.id,
                    label="orbita",
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

        # 2. Enlaces de Rutas Geograficas manuales
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

        # Mostrar el grafo y ajustar camara
        self._stack.setCurrentIndex(1)
        self._fit_to_view()
        # Cargar presencias con el capitulo activo (si hay proyecto)
        if self._project_manager:
            chapter_id = self._chapter_combo.currentData()
            self.load_presences(chapter_id)


    # ── Reorganización y Búsqueda ───────────────────────────────────────────

    def reorganize_layout(self):
        """Recalcula la fisica planetaria en background y actualiza el grafo sin bloquear la UI."""
        if not self._places:
            return

        # Mostrar overlay mientras recalcula
        self._stack.setCurrentIndex(0)

        if self._layout_worker and self._layout_worker.isRunning():
            self._layout_worker.quit()
            self._layout_worker.wait(200)

        self._layout_worker = _LayoutWorker(self._places, self._links)
        self._layout_worker.layout_ready.connect(self._on_reorganize_ready)
        self._layout_worker.start()

    @pyqtSlot(dict)
    def _on_reorganize_ready(self, positions: dict):
        """Aplica las nuevas posiciones al grafo tras reorganizar."""
        for place_id, (px, py) in positions.items():
            node = self._node_map.get(place_id)
            if node:
                node.setPos(px, py)

        for edge in self._scene._all_edges:
            edge._update_path()
            edge.setVisible(self._edges_visible)

        self._scene.update()
        self._stack.setCurrentIndex(1)
        self._fit_to_view()
        char_id = self._char_filter_combo.currentData()
        if char_id:
            self._apply_char_filter(char_id)


    def _toggle_edges(self) -> None:
        """Muestra u oculta todas las aristas (órbitas + rutas) del Atlas."""
        self._edges_visible = self._chk_edges.isChecked()

        for edge in self._scene._all_edges:
            edge.setVisible(self._edges_visible)

    def _on_search(self, text: str):
        """Filtra y resalta nodos por nombre o categoría del lugar."""
        query = text.lower().strip()
        char_id = self._char_filter_combo.currentData()

        for node in self._node_map.values():
            if not query:
                # Al limpiar el buscador, restaurar según el filtro de personaje activo
                if char_id:
                    # Dejar que _apply_char_filter se encargue de la opacidad
                    pass
                else:
                    node.set_focused(False, False)
                    node.setOpacity(1.0)
            else:
                place = node.place
                match = query in place.name.lower() or query in place.category.lower()
                # Resaltar coincidencias con foco, atenuar el resto
                node.set_focused(match, not match)
                node.setOpacity(1.0 if match else 0.18)

        # Si se limpió el buscador y hay filtro de personaje, reaplicarlo
        if not query and char_id:
            self._apply_char_filter(char_id)

    def _fit_to_view(self):
        rect = self._scene.itemsBoundingRect()
        if not rect.isEmpty():
            self._view.fitInView(rect.adjusted(-90, -90, 90, 90),
                                 Qt.AspectRatioMode.KeepAspectRatio)

    def _open_presence_grid(self):
        """Abre la Cuadricula de Presencias (personajes x capitulos)."""
        if not self._project_manager:
            return
        from ui.presence_grid import PresenceGridDialog
        dlg = PresenceGridDialog(self._project_manager, parent=self)
        dlg.exec()
        # Recargar el atlas con los datos actualizados por la cuadricula
        self._rebuild_graph()


# ─────────────────────────────────────────────────────────────────────────────
#  Worker: calcula el layout de física orbital en un hilo secundario
