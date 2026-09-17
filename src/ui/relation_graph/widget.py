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

        # Toolbar
        self._toolbar = _GraphToolbar(self)
        self._toolbar.filter_changed.connect(self._on_filter_changed)
        self._toolbar.search_submitted.connect(self._on_search_submitted)
        self._toolbar.character_selected.connect(self._on_character_dropdown_selected)
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

        if len(filtered_characters) > 150:
            worker = LayoutWorker(char_map, self._metrics_map, rel_objs)
            worker.signals.finished.connect(lambda pos, cr: self._apply_layout_result(pos, filtered_characters, filtered_relations))
            QThreadPool.globalInstance().start(worker)
        else:
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
        """Focus on character node, center view, and update side panel."""
        self._active_focus_id = char_id
        self._toolbar.select_character_id(char_id)
        node = self._scene.get_node(char_id)
        if node:
            self._view.centerOn(node)
        self._scene._set_focus(char_id)
        self.character_clicked.emit(char_id)

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

    def _on_zoom_in(self):
        self._view.scale(1.25, 1.25)

    def _on_zoom_out(self):
        self._view.scale(0.8, 0.8)

    def _on_zoom_fit(self):
        self._view.fit_all()

    # ------------------------------------------------------------------
    # Theme Support
    # ------------------------------------------------------------------
    def update_theme(self, is_dark: bool):
        self._is_dark_theme = is_dark
        self._toolbar.update_theme(is_dark)
        self._side_panel.update_theme(is_dark)
        self._scene.update_theme(is_dark)

