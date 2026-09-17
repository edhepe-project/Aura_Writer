"""
RelationGraphWidget: High-performance interactive visual relationship graph.
Modularized implementation orchestrating toolbar, scene, view, side panel, and physics layout.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThreadPool
from .models import CharacterMetrics
from .physics import compute_graph_layout, calculate_metrics, LayoutWorker
from .scene import GraphScene, RelationGraphView
from .side_panel import NexusSidePanel
from .toolbar import _GraphToolbar


class RelationGraphWidget(QWidget):
    """
    Main widget displaying characters and relations in an interactive 2D graph with:
    - Dynamic orbital rendering and glowing focus states
    - Search completer bar and relationship type filtering
    - Interactive details side panel with fast direct navigation
    - Apple-inspired dark/light theme integration
    """
    character_clicked = pyqtSignal(str)   # char_id
    character_focused = pyqtSignal(str)   # char_id (abrir ficha al hacer doble clic)
    add_relation_requested = pyqtSignal()
    open_character_sheet = pyqtSignal(str) # char_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._characters = []
        self._relations = []
        self._chapters = []
        self._meta = None
        self._metrics_map: dict[str, CharacterMetrics] = {}
        self._current_filter: str = "Todos"
        self._active_focus_id: str | None = None
        self._is_dark_theme: bool = True

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self._root_layout = root

        # Toolbar
        self._toolbar = _GraphToolbar(self)
        self._toolbar.filter_changed.connect(self._on_filter_changed)
        self._toolbar.search_submitted.connect(self._on_search_submitted)
        self._toolbar.character_selected.connect(self._on_character_dropdown_selected)
        self._toolbar.show_all_edges_toggled.connect(self._on_show_all_edges_toggled)
        self._toolbar.zoom_in_requested.connect(self._on_zoom_in)
        self._toolbar.zoom_out_requested.connect(self._on_zoom_out)
        self._toolbar.zoom_fit_requested.connect(self._on_zoom_fit)
        root.addWidget(self._toolbar)

        # Content: Graph View + Side Panel
        content_widget = QWidget(self)
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self._scene = GraphScene(self)
        self._scene.node_clicked.connect(self._on_node_clicked)
        self._scene.node_double_clicked.connect(self._on_node_double_clicked)
        self._scene.character_focused.connect(self.character_focused.emit)
        self._scene.background_clicked.connect(self._on_background_clicked)

        self._view = RelationGraphView(self._scene, content_widget)
        content_layout.addWidget(self._view, stretch=1)

        self._side_panel = NexusSidePanel(content_widget)
        self._side_panel.open_sheet_requested.connect(self._on_open_sheet)
        self._side_panel.add_relation_requested.connect(self.add_relation_requested.emit)
        self._side_panel.jump_to_character_requested.connect(self._jump_to_character)
        content_layout.addWidget(self._side_panel)

        root.addWidget(content_widget, stretch=1)

        # Barra Inferior de Leyenda de Relaciones (Memoria ultra-ligera y fácil lectura)
        self._legend_bar = self._build_legend_bar()
        root.addWidget(self._legend_bar)

    def _build_legend_bar(self) -> QWidget:
        from PyQt6.QtWidgets import QLabel, QFrame
        from core.models import RELATION_ICONS
        from .models import RELATION_STYLES

        bar = QFrame(self)
        bar.setFixedHeight(34)
        is_dark = self._is_dark_theme
        bg_bar = "#161618" if is_dark else "#ede8e1"
        b_border = "#2c2c2e" if is_dark else "#d4cfc8"
        tip_bg = "#2c2c2e" if is_dark else "#faf7f3"
        tip_fg = "#f2f2f7" if is_dark else "#1a1a2e"
        tip_b = "#3a3a3c" if is_dark else "#c4bfb8"

        bar.setStyleSheet(f"""
            QToolTip {{
                background-color: {tip_bg};
                color: {tip_fg};
                border: 1px solid {tip_b};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }}
            QFrame {{
                background-color: {bg_bar};
                border-top: 1px solid {b_border};
            }}
        """)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(10)

        title = QLabel("LÍNEAS:")
        fg_title = "#8e8e93" if is_dark else "#7a7a8a"
        title.setStyleSheet(f"color: {fg_title}; font-size: 10px; font-weight: 800; letter-spacing: 0.5px;")
        layout.addWidget(title)

        # Tipos de relación compactos
        legend_types = [
            ("pareja", "Pareja"),
            ("familiar", "Familiar"),
            ("descendiente", "Descend."),
            ("amigo", "Amigo"),
            ("mentor", "Mentor"),
            ("rival", "Rival"),
            ("otro", "Otro"),
        ]

        for r_key, r_name in legend_types:
            style = RELATION_STYLES.get(r_key, RELATION_STYLES["otro"])
            color = style["color"]
            icon = RELATION_ICONS.get(r_key, "•")

            item_widget = QWidget(bar)
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(0, 0, 0, 0)
            item_layout.setSpacing(4)

            # Muestra de línea
            line_sample = QFrame(item_widget)
            line_sample.setFixedSize(14, 3)
            line_sample.setStyleSheet(f"background-color: {color}; border-radius: 1px;")
            item_layout.addWidget(line_sample)

            lbl = QLabel(f"{icon} {r_name}", item_widget)
            fg_item = "#d1d1d6" if is_dark else "#2c2c2e"
            lbl.setStyleSheet(f"color: {fg_item}; font-size: 10.5px; font-weight: 600;")
            item_layout.addWidget(lbl)
            layout.addWidget(item_widget)

        layout.addStretch()

        # Separador vertical
        sep = QFrame(bar)
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"background-color: {b_border}; max-height: 14px;")
        layout.addWidget(sep)

        # Leyenda de Jerarquía Geométrica Compacta con Tooltip
        geom_title = QLabel("JERARQUÍA:", bar)
        geom_title.setStyleSheet(f"color: {fg_title}; font-size: 10px; font-weight: 800; letter-spacing: 0.5px;")
        geom_title.setToolTip(
            "Escala Geométrica por Conexiones:\n"
            "▲ 3L (1-2) | ⯁ 4L (3-5) | ⬟ 5L (6-9)\n"
            "⬢ 6L (10-14) | ⬡ 7L (15-22) | 🛑 8L (23-35)\n"
            "💎 10L (36-55) | 🔷 12L (56-79) | 🔮 20L (80-99)\n"
            "● Círculo Radiante (100+ conexiones / Núcleo Mítico)"
        )
        layout.addWidget(geom_title)

        geom_chips = [
            ("▲", "3L"),
            ("⯁", "4L"),
            ("⬢", "6L"),
            ("🛑", "8L"),
            ("💎", "10L"),
            ("●", "100+"),
        ]
        for symbol, g_label in geom_chips:
            g_lbl = QLabel(f"{symbol} {g_label}", bar)
            g_lbl.setStyleSheet(f"color: {'#a1a1a6' if is_dark else '#48484a'}; font-size: 10.5px; font-weight: 600;")
            g_lbl.setToolTip("Pasa el cursor sobre JERARQUÍA para ver todos los niveles detallados.")
            layout.addWidget(g_lbl)

        return bar

    # ------------------------------------------------------------------
    # Data Loading & Layout
    # ------------------------------------------------------------------
    def build_from_metadata(self, meta):
        """Construye el grafo directamente a partir de UniverseMetadata."""
        self._meta = meta
        self._characters = meta.characters or []
        self._relations = meta.relations or []
        self._metrics_map = calculate_metrics(meta)
        self._populate_filters()
        self._rebuild_graph()

    def set_data(self, characters: list, relations: list, chapters: list = None):
        """
        Load characters and relations directly (fallback/generic mode).
        """
        self._characters = characters or []
        self._relations = relations or []
        self._chapters = chapters or []

        # Convert simple list format if needed
        chap_counts = {}
        for cap in (chapters or []):
            present = cap.get("characters_present", []) if isinstance(cap, dict) else getattr(cap, "characters_present", [])
            for cid in present:
                chap_counts[str(cid)] = chap_counts.get(str(cid), 0) + 1

        conn_counts = {}
        int_sums = {}
        for rel in self._relations:
            a = str(rel.get("source") if isinstance(rel, dict) else getattr(rel, "char_id_a", getattr(rel, "source", "")))
            b = str(rel.get("target") if isinstance(rel, dict) else getattr(rel, "char_id_b", getattr(rel, "target", "")))
            intensity = int(rel.get("intensity", 3) if isinstance(rel, dict) else getattr(rel, "intensity", 3))
            conn_counts[a] = conn_counts.get(a, 0) + 1
            conn_counts[b] = conn_counts.get(b, 0) + 1
            ival = max(1, intensity) / 5.0
            int_sums[a] = int_sums.get(a, 0.0) + ival
            int_sums[b] = int_sums.get(b, 0.0) + ival

        self._metrics_map = {}
        for ch in self._characters:
            cid = str(ch.get("id") if isinstance(ch, dict) else getattr(ch, "id", ""))
            role = str(ch.get("role") if isinstance(ch, dict) else getattr(ch, "role", ""))
            self._metrics_map[cid] = CharacterMetrics(
                char_id=cid,
                chapters_count=chap_counts.get(cid, 0),
                connections_count=conn_counts.get(cid, 0),
                intensity_sum=int_sums.get(cid, 0.0),
                role=role
            )

        self._populate_filters()
        self._rebuild_graph()

    def _populate_filters(self):
        current = self._toolbar.combo.currentText()
        self._toolbar.combo.blockSignals(True)
        self._toolbar.combo.clear()
        self._toolbar.combo.addItem("Todos")

        types = sorted(set(
            (r.get("relation_type", "") if isinstance(r, dict) else getattr(r, "relation_type", ""))
            for r in self._relations
            if (r.get("relation_type") if isinstance(r, dict) else getattr(r, "relation_type", None))
        ))
        for t in types:
            self._toolbar.combo.addItem(t)

        idx = self._toolbar.combo.findText(current)
        if idx >= 0:
            self._toolbar.combo.setCurrentIndex(idx)
        else:
            self._toolbar.combo.setCurrentIndex(0)
            self._current_filter = "Todos"
        self._toolbar.combo.blockSignals(False)

        names = [
            (c.get("name", "") if isinstance(c, dict) else getattr(c, "name", ""))
            for c in self._characters
            if (c.get("name") if isinstance(c, dict) else getattr(c, "name", None))
        ]
        self._toolbar.set_completer_model(names)
        self._toolbar.set_characters_list(self._characters)

    def _rebuild_graph(self):
        # Filter relations and corresponding active characters
        if self._current_filter == "Todos":
            filtered_relations = self._relations
            filtered_characters = self._characters
        else:
            filtered_relations = [
                r for r in self._relations
                if (r.get("relation_type") if isinstance(r, dict) else getattr(r, "relation_type", "")) == self._current_filter
            ]
            active_ids = set()
            for r in filtered_relations:
                src = str(r.get("source") if isinstance(r, dict) else getattr(r, "char_id_a", getattr(r, "source", "")))
                tgt = str(r.get("target") if isinstance(r, dict) else getattr(r, "char_id_b", getattr(r, "target", "")))
                if src: active_ids.add(src)
                if tgt: active_ids.add(tgt)
            
            filtered_characters = [
                c for c in self._characters
                if str(c.get("id") if isinstance(c, dict) else getattr(c, "id", "")) in active_ids
            ]

        # Prepare char_map & rel_objs for compute_graph_layout
        char_map = {}
        for c in filtered_characters:
            cid = str(c.get("id") if isinstance(c, dict) else getattr(c, "id", ""))
            char_map[cid] = c

        rel_objs = []
        for r in filtered_relations:
            if isinstance(r, dict):
                robj = type("SimpleRel", (), {
                    "char_id_a": str(r.get("source", "")),
                    "char_id_b": str(r.get("target", "")),
                    "relation_type": str(r.get("relation_type", "otro")),
                    "label": str(r.get("label", "")),
                    "intensity": int(r.get("intensity", 3))
                })()
                rel_objs.append(robj)
            else:
                rel_objs.append(r)

        positions, core_radius = compute_graph_layout(
            char_map,
            self._metrics_map,
            rel_objs
        )
        self._apply_layout_result(positions, filtered_characters, filtered_relations)

    def _apply_layout_result(self, positions: dict, filtered_characters: list, filtered_relations: list):
        # Populate scene
        self._scene.populate(
            characters=filtered_characters,
            relations=filtered_relations,
            positions=positions,
            metrics_map=self._metrics_map,
            is_dark=self._is_dark_theme
        )

        # Sincronizar estado de la casilla 'Mostrar todas las líneas'
        if hasattr(self, "_toolbar") and hasattr(self._toolbar, "chk_show_all"):
            self._scene.set_show_all_edges(self._toolbar.chk_show_all.isChecked())

        # Auto-fit: deferred so Qt processes layout events first
        QTimer.singleShot(100, self._view.fit_all)

        # Re-apply active focus if preserved
        if self._active_focus_id:
            self._scene._set_focus(self._active_focus_id)
            char = next((c for c in self._characters if str(c.get("id") if isinstance(c, dict) else getattr(c, "id", "")) == str(self._active_focus_id)), None)
            if char:
                rels = [r for r in self._relations if str(r.get("source") if isinstance(r, dict) else getattr(r, "char_id_a", getattr(r, "source", ""))) == str(self._active_focus_id) or str(r.get("target") if isinstance(r, dict) else getattr(r, "char_id_b", getattr(r, "target", ""))) == str(self._active_focus_id)]
                m = self._metrics_map.get(str(self._active_focus_id), CharacterMetrics())
                self._side_panel.display_character(char, rels, self._characters, m)
            else:
                self._side_panel.display_empty()
        else:
            self._side_panel.display_empty()

    # ------------------------------------------------------------------
    # User Interactions & Search
    # ------------------------------------------------------------------
    def _on_filter_changed(self, filter_text: str):
        self._current_filter = filter_text or "Todos"
        self._rebuild_graph()

    def _on_search_submitted(self, query: str):
        query = query.strip().lower()
        if not query:
            return
        match = next((c for c in self._characters if query in (c.get("name", "").lower() if isinstance(c, dict) else getattr(c, "name", "").lower())), None)
        if match:
            char_id = str(match.get("id") if isinstance(match, dict) else getattr(match, "id", ""))
            self._jump_to_character(char_id)

    def _on_character_dropdown_selected(self, char_id: str):
        if char_id:
            self._jump_to_character(char_id)
        else:
            self._on_background_clicked()

    def _jump_to_character(self, char_id: str):
        """Vuela la cámara al personaje y hace zoom en su radio de influencia (él + vecinos directos)."""
        self._active_focus_id = char_id
        self._toolbar.select_character_id(char_id)
        self._scene._set_focus(char_id)
        self.character_clicked.emit(char_id)

        node = self._scene.get_node(char_id)
        if node:
            # FIX #4: Usar _adj_nodes (siempre poblado) en lugar de _scene._edges (casi siempre vacío)
            neighbor_ids = self._scene._adj_nodes.get(char_id, set())
            neighbor_nodes = [
                self._scene._nodes[nid]
                for nid in neighbor_ids
                if nid in self._scene._nodes
            ]
            # Animar cámara al radio de influencia
            self._view.center_on_character(node, neighbor_nodes, animate=True)

        char = next((c for c in self._characters if str(c.get("id") if isinstance(c, dict) else getattr(c, "id", "")) == str(char_id)), None)
        if char:
            rels = [r for r in self._relations if str(r.get("source") if isinstance(r, dict) else getattr(r, "char_id_a", getattr(r, "source", ""))) == str(char_id) or str(r.get("target") if isinstance(r, dict) else getattr(r, "char_id_b", getattr(r, "target", ""))) == str(char_id)]
            m = self._metrics_map.get(str(char_id), CharacterMetrics())
            self._side_panel.display_character(char, rels, self._characters, m)


    def _on_node_clicked(self, char_id: str):
        self._active_focus_id = char_id
        self._toolbar.select_character_id(char_id)
        self.character_clicked.emit(char_id)
        char = next((c for c in self._characters if str(c.get("id") if isinstance(c, dict) else getattr(c, "id", "")) == str(char_id)), None)
        if char:
            rels = [r for r in self._relations if str(r.get("source") if isinstance(r, dict) else getattr(r, "char_id_a", getattr(r, "source", ""))) == str(char_id) or str(r.get("target") if isinstance(r, dict) else getattr(r, "char_id_b", getattr(r, "target", ""))) == str(char_id)]
            m = self._metrics_map.get(str(char_id), CharacterMetrics())
            self._side_panel.display_character(char, rels, self._characters, m)

    def _on_node_double_clicked(self, char_id: str):
        self.open_character_sheet.emit(char_id)
        self.character_focused.emit(char_id)

    def _on_open_sheet(self, char_id: str):
        self.open_character_sheet.emit(char_id)
        self.character_focused.emit(char_id)

    def _on_background_clicked(self):
        self._active_focus_id = None
        self._toolbar.select_character_id("")
        self._scene._set_focus(None)
        self._side_panel.display_empty()

    def _on_show_all_edges_toggled(self, checked: bool):
        self._scene.set_show_all_edges(checked)

    def _on_zoom_in(self):
        self._view.scale(1.25, 1.25)

    def _on_zoom_out(self):
        self._view.scale(0.8, 0.8)

    def _on_zoom_fit(self):
        self._view.fit_all()

    # ------------------------------------------------------------------
    # Theme Support
    # ------------------------------------------------------------------
    def _update_legend_bar_theme(self, is_dark: bool):
        if hasattr(self, "_legend_bar") and self._legend_bar is not None and hasattr(self, "_root_layout"):
            self._root_layout.removeWidget(self._legend_bar)
            self._legend_bar.setParent(None)
            self._legend_bar.deleteLater()
            self._legend_bar = self._build_legend_bar()
            self._root_layout.addWidget(self._legend_bar)

    def update_theme(self, is_dark: bool):
        self._is_dark_theme = is_dark
        self._toolbar.update_theme(is_dark)
        self._side_panel.update_theme(is_dark)
        self._scene.update_theme(is_dark)
        self._update_legend_bar_theme(is_dark)

