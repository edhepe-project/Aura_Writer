"""
dialog.py — Diálogo modal principal del Atlas Literario y Grafo de Lugares.
Incluye panel lateral con detalles de conexiones, creación y eliminación de rutas geográficas con sincronización y guardado automático.
"""
from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSplitter, QComboBox, QLineEdit, QMessageBox, QListWidget, QListWidgetItem,
    QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
import qtawesome as qta

from core.models import Place, PlaceLink, UniverseMetadata, CONNECTION_TYPES, CONNECTION_COLORS
from core.theme_manager import ThemeManager
from .models import CONNECTION_STYLES
from .widget import PlaceGraphWidget
from .presence_panel import PresencePanel, PlaceHistoryPanel


class PlaceGraphDialog(QDialog):
    """
    Diálogo interactivo para explorar el Atlas del Universo (Grafo de Escenarios y Conexiones).
    """
    place_selected_for_focus = pyqtSignal(str)  # place_id

    def __init__(self, project_manager, parent=None):
        super().__init__(parent)
        self.pm = project_manager
        self.setWindowTitle("🗺️ Atlas Literario — Grafo de Lugares & Conexiones")
        self.resize(1200, 720)
        self.setMinimumSize(900, 520)
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowMinimizeButtonHint
        )

        self._selected_place_id: str | None = None
        self._data_loaded: bool = False
        self._setup_ui()
        # NO llamar _load_data() aqui — se difiere al showEvent
        # para que el dialogo aparezca inmediatamente con el overlay de carga
        # en lugar de quedarse en blanco mientras construye el grafo.

    def showEvent(self, event):
        super().showEvent(event)
        from PyQt6.QtCore import QTimer
        if not self._data_loaded:
            self._data_loaded = True
            # Cargar datos tras el primer pintado del dialogo:
            # el usuario ve el overlay de carga, no una ventana en blanco.
            QTimer.singleShot(0, self._load_data)
        else:
            # Reaperturas: solo reajustar la camara
            QTimer.singleShot(50, self._graph_widget._fit_to_view)

    def _setup_ui(self):
        is_dark = ThemeManager.is_dark()
        bg_main = "#1c1c1e" if is_dark else "#f5f0ea"
        bg_panel = "#2c2c2e" if is_dark else "#ffffff"
        fg_title = "#f2f2f7" if is_dark else "#1c1c1e"
        b_border = "#3a3a3c" if is_dark else "#d4cfc8"

        self.setStyleSheet(f"""
            QDialog {{ background-color: {bg_main}; }}
            QFrame#panel {{ background-color: {bg_panel}; border-left: 1px solid {b_border}; }}
            QLineEdit, QComboBox {{
                background-color: {'#3a3a3c' if is_dark else '#fbf9f5'};
                color: {fg_title};
                border: 1px solid {b_border};
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 11px;
            }}
            QPushButton {{
                background-color: {'#3a3a3c' if is_dark else '#e8e4dc'};
                color: {fg_title};
                border: 1px solid {b_border};
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {'#48484a' if is_dark else '#ded8ce'};
            }}
            QListWidget {{
                background-color: {'#232326' if is_dark else '#faf7f2'};
                border: 1px solid {b_border};
                border-radius: 6px;
                color: {fg_title};
                font-size: 11px;
            }}
            QListWidget::item {{
                padding: 4px 6px;
                border-bottom: 1px solid {'#2c2c2e' if is_dark else '#eee9e0'};
            }}
            QListWidget::item:selected {{
                background-color: #0a84ff;
                color: #ffffff;
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)

        # Grafo a la izquierda
        self._graph_widget = PlaceGraphWidget(self)
        self._graph_widget.place_selected.connect(self._on_place_selected)
        self._graph_widget.place_double_clicked.connect(self._on_place_double_clicked)
        self._graph_widget.chapter_changed.connect(self._on_chapter_changed_in_toolbar)
        splitter.addWidget(self._graph_widget)

        # Panel lateral con pestañas: Rutas, Presencia e Historial
        panel = QFrame()
        panel.setObjectName("panel")
        panel.setFixedWidth(360)
        pl = QVBoxLayout(panel)
        pl.setContentsMargins(10, 10, 10, 10)
        pl.setSpacing(8)

        # Encabezado común del lugar
        title_lbl = QLabel("INFORMACIÓN DE ESCENARIO")
        t_font = QFont()
        t_font.setBold(True)
        t_font.setPointSize(9)
        title_lbl.setFont(t_font)
        pl.addWidget(title_lbl)

        self._info_name = QLabel("Selecciona un lugar en el mapa")
        self._info_name.setStyleSheet("font-size: 13px; font-weight: bold; color: #0a84ff;")
        self._info_name.setWordWrap(True)
        pl.addWidget(self._info_name)

        self._info_desc = QLabel("Haz clic en cualquier astro para ver sus rutas, presencia actual e historial de visitas.")
        self._info_desc.setStyleSheet("font-size: 11px; color: #8e8e93;")
        self._info_desc.setWordWrap(True)
        pl.addWidget(self._info_desc)

        # Tab Widget: Rutas vs Presencia vs Historial
        self._tabs = QTabWidget()
        
        # Pestaña 1: Rutas y Conexiones
        routes_tab = QWidget()
        rtl = QVBoxLayout(routes_tab)
        rtl.setContentsMargins(4, 8, 4, 4)
        rtl.setSpacing(8)

        rtl.addWidget(QLabel("<b>Conexiones & Rutas activas:</b>"))
        self._connections_list = QListWidget()
        self._connections_list.itemSelectionChanged.connect(self._on_connection_selection_changed)
        rtl.addWidget(self._connections_list)

        # Botón para eliminar la ruta seleccionada
        self._btn_delete_link = QPushButton("🗑️ Eliminar Ruta Seleccionada")
        self._btn_delete_link.setEnabled(False)
        self._btn_delete_link.setStyleSheet("""
            QPushButton { color: #ff453a; border-color: #5c2020; }
            QPushButton:hover { background-color: #5c2020; color: #ffffff; }
            QPushButton:disabled { color: #636366; border-color: #3a3a3c; }
        """)
        self._btn_delete_link.clicked.connect(self._delete_selected_connection)
        rtl.addWidget(self._btn_delete_link)

        # Formulario para conectar lugares
        form_frame = QFrame()
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(0, 4, 0, 0)
        form_layout.setSpacing(6)

        form_layout.addWidget(QLabel("<b>Añadir nueva ruta:</b>"))

        form_layout.addWidget(QLabel("Origen:"))
        self._combo_source_place = QComboBox()
        self._combo_source_place.currentIndexChanged.connect(self._on_source_combo_changed)
        form_layout.addWidget(self._combo_source_place)

        form_layout.addWidget(QLabel("Destino:"))
        self._combo_target_place = QComboBox()
        form_layout.addWidget(self._combo_target_place)

        form_layout.addWidget(QLabel("Tipo de Ruta:"))
        self._combo_conn_type = QComboBox()
        for ctype in CONNECTION_TYPES:
            self._combo_conn_type.addItem(ctype.capitalize(), ctype)
        form_layout.addWidget(self._combo_conn_type)

        self._input_conn_label = QLineEdit()
        self._input_conn_label.setPlaceholderText("Nombre de la ruta/vínculo (opcional)...")
        form_layout.addWidget(self._input_conn_label)

        btn_add_link = QPushButton("➕ Conectar Lugares")
        btn_add_link.clicked.connect(self._add_connection)
        form_layout.addWidget(btn_add_link)
        rtl.addWidget(form_frame)
        self._tabs.addTab(routes_tab, "🛣️ Rutas")

        # Pestaña 2: Presencia de Personajes en Escena
        self._presence_panel = PresencePanel(self)
        self._presence_panel.set_project_manager(self.pm)
        self._presence_panel.presence_changed.connect(self._on_presence_changed_in_panel)
        self._tabs.addTab(self._presence_panel, "👤 En Escena")

        # Pestaña 3: Historial de Visitas y Pasaje
        self._history_panel = PlaceHistoryPanel(self)
        self._history_panel.set_project_manager(self.pm)
        self._tabs.addTab(self._history_panel, "📜 Historial")

        pl.addWidget(self._tabs, stretch=1)

        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.accept)
        pl.addWidget(btn_close)

        splitter.addWidget(panel)
        root.addWidget(splitter)

    def _on_chapter_changed_in_toolbar(self, chapter_id: str | None):
        """Actualiza la presencia e historial del lugar seleccionado cuando cambia el capítulo activo en la toolbar."""
        if self._selected_place_id and self.pm and self.pm.metadata:
            place = next((p for p in getattr(self.pm.metadata, "places", []) if p.id == self._selected_place_id), None)
            if place:
                self._presence_panel.load_place(place, chapter_id=chapter_id)
                self._history_panel.load_place(place)

    def _on_presence_changed_in_panel(self):
        """Refresca los badges en el grafo y la pestaña Historial cuando el usuario modifica una presencia."""
        if self.pm:
            self.pm.save_project()
        chapter_id = self._graph_widget._chapter_combo.currentData()
        self._graph_widget.load_presences(chapter_id)
        if self._selected_place_id:
            place = next((p for p in getattr(self.pm.metadata, "places", []) if p.id == self._selected_place_id), None)
            if place:
                self._history_panel.load_place(place)

    def _load_data(self):
        if not self.pm or not self.pm.metadata:
            return
        meta: UniverseMetadata = self.pm.metadata
        places = getattr(meta, "places", [])
        links = getattr(meta, "place_links", [])

        self._graph_widget.set_project_manager(self.pm)
        self._graph_widget.set_data(places, links)
        self._presence_panel.set_project_manager(self.pm)
        self._history_panel.set_project_manager(self.pm)
        self._refresh_combos()

    def _refresh_combos(self):
        meta: UniverseMetadata = self.pm.metadata
        places = getattr(meta, "places", []) if meta else []

        curr_src = self._combo_source_place.currentData()
        curr_tgt = self._combo_target_place.currentData()

        self._combo_source_place.blockSignals(True)
        self._combo_source_place.clear()
        self._combo_target_place.clear()

        for p in places:
            self._combo_source_place.addItem(p.name, p.id)
            self._combo_target_place.addItem(p.name, p.id)

        if self._selected_place_id:
            idx = self._combo_source_place.findData(self._selected_place_id)
            if idx >= 0:
                self._combo_source_place.setCurrentIndex(idx)
        elif curr_src:
            idx = self._combo_source_place.findData(curr_src)
            if idx >= 0:
                self._combo_source_place.setCurrentIndex(idx)

        if curr_tgt and curr_tgt != self._combo_source_place.currentData():
            idx = self._combo_target_place.findData(curr_tgt)
            if idx >= 0:
                self._combo_target_place.setCurrentIndex(idx)

        self._combo_source_place.blockSignals(False)

    def _on_source_combo_changed(self):
        src_id = self._combo_source_place.currentData()
        if src_id and src_id != self._selected_place_id:
            self._on_place_selected(src_id)

    def _on_place_selected(self, place_id: str):
        self._selected_place_id = place_id
        meta = self.pm.metadata
        places = getattr(meta, "places", [])
        links = getattr(meta, "place_links", [])
        place = next((p for p in places if p.id == place_id), None)
        if not place:
            return

        self._combo_source_place.blockSignals(True)
        idx = self._combo_source_place.findData(place_id)
        if idx >= 0:
            self._combo_source_place.setCurrentIndex(idx)
        self._combo_source_place.blockSignals(False)

        self._info_name.setText(f"📍 {place.name}")
        desc = place.description or place.lore_history or place.climate_atmosphere or "Sin detalles registrados."
        self._info_desc.setText(desc[:180] + ("..." if len(desc) > 180 else ""))

        self._connections_list.clear()
        self._btn_delete_link.setEnabled(False)
        place_names = {p.id: p.name for p in places}

        # 1. Mostrar planeta superior si es una estancia
        if place.parent_place_id and place.parent_place_id in place_names:
            parent_item = QListWidgetItem(f"🪐 Órbita de: {place_names[place.parent_place_id]}")
            parent_item.setForeground(QColor("#0a84ff"))
            parent_item.setData(Qt.ItemDataRole.UserRole, None)  # no eliminable como ruta libre
            self._connections_list.addItem(parent_item)

        # 2. Mostrar estancias o satélites orbitando
        sub_places = [p for p in places if p.parent_place_id == place_id]
        if sub_places:
            for sp in sub_places:
                sp_item = QListWidgetItem(f"🌙 Satélite/Estancia: {sp.name} ({sp.category})")
                sp_item.setForeground(QColor("#bf5af2"))
                sp_item.setData(Qt.ItemDataRole.UserRole, None)
                self._connections_list.addItem(sp_item)

        # 3. Conexiones de rutas manuales (eliminables)
        for lk in links:
            other_id = None
            if lk.place_id_a == place_id:
                other_id = lk.place_id_b
            elif lk.place_id_b == place_id:
                other_id = lk.place_id_a

            if other_id and other_id in place_names:
                lbl = f"━ {place_names[other_id]} ({lk.connection_type})"
                if lk.label:
                    lbl += f" — {lk.label}"
                link_item = QListWidgetItem(lbl)
                style_color = CONNECTION_STYLES.get(lk.connection_type, {}).get("color", "#30d158")
                link_item.setForeground(QColor(style_color))
                link_item.setData(Qt.ItemDataRole.UserRole, lk)  # Asignamos el objeto PlaceLink
                self._connections_list.addItem(link_item)

        if self._connections_list.count() == 0:
            empty_item = QListWidgetItem("Sin conexiones ni estancias vinculadas.")
            empty_item.setData(Qt.ItemDataRole.UserRole, None)
            self._connections_list.addItem(empty_item)

        # 4. Actualizar panel de presencia en escena e historial
        chapter_id = self._graph_widget._chapter_combo.currentData()
        self._presence_panel.load_place(place, chapter_id=chapter_id)
        self._history_panel.load_place(place)

    def _on_connection_selection_changed(self):
        item = self._connections_list.currentItem()
        is_route = item is not None and item.data(Qt.ItemDataRole.UserRole) is not None
        self._btn_delete_link.setEnabled(is_route)

    def _delete_selected_connection(self):
        item = self._connections_list.currentItem()
        if not item:
            return
        link_to_delete: PlaceLink | None = item.data(Qt.ItemDataRole.UserRole)
        if not link_to_delete:
            return

        meta: UniverseMetadata = self.pm.metadata
        if not meta or not hasattr(meta, "place_links"):
            return

        # Confirmación
        ans = QMessageBox.question(
            self,
            "Eliminar Ruta",
            f"¿Deseas eliminar la conexión entre estos lugares?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ans != QMessageBox.StandardButton.Yes:
            return

        # Filtrar enlace eliminado
        meta.place_links = [
            lk for lk in meta.place_links
            if not (
                (lk.place_id_a == link_to_delete.place_id_a and lk.place_id_b == link_to_delete.place_id_b) or
                (lk.place_id_a == link_to_delete.place_id_b and lk.place_id_b == link_to_delete.place_id_a)
            )
        ]

        # Guardar en proyecto
        if hasattr(self.pm, "save_metadata") and getattr(self.pm, "temp_dir", None):
            try:
                self.pm.save_metadata()
            except Exception:
                pass

        # Recargar grafo y panel
        self._graph_widget.set_data(meta.places, meta.place_links)
        if self._selected_place_id:
            self._on_place_selected(self._selected_place_id)

    def _on_place_double_clicked(self, place_id: str):
        self.place_selected_for_focus.emit(place_id)

    def _add_connection(self):
        source_id = self._combo_source_place.currentData() or self._selected_place_id
        if not source_id:
            QMessageBox.information(self, "Aviso", "Selecciona un lugar de origen.")
            return

        target_id = self._combo_target_place.currentData()
        if not target_id or target_id == source_id:
            QMessageBox.warning(self, "Aviso", "Selecciona un lugar de destino diferente al de origen.")
            return

        meta: UniverseMetadata = self.pm.metadata
        if not hasattr(meta, "place_links") or meta.place_links is None:
            meta.place_links = []

        # Comprobar si ya existe
        existing = any(
            (lk.place_id_a == source_id and lk.place_id_b == target_id) or
            (lk.place_id_b == source_id and lk.place_id_a == target_id)
            for lk in meta.place_links
        )
        if existing:
            QMessageBox.information(self, "Aviso", "Ya existe una ruta o conexión entre estos dos lugares.")
            return

        new_link = PlaceLink(
            place_id_a=source_id,
            place_id_b=target_id,
            label=self._input_conn_label.text().strip(),
            connection_type=self._combo_conn_type.currentData(),
            bidirectional=True
        )
        meta.place_links.append(new_link)
        self._input_conn_label.clear()

        # Guardar cambios en el proyecto si tiene carpeta activa
        if hasattr(self.pm, "save_metadata") and getattr(self.pm, "temp_dir", None):
            try:
                self.pm.save_metadata()
            except Exception:
                pass

        # Recargar grafo y panel
        self._graph_widget.set_data(meta.places, meta.place_links)
        self._on_place_selected(source_id)
