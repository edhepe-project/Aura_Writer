"""
Widget orquestador principal para el Grafo del Cronograma Narrativo.
Integra Toolbar, QGraphicsView interactivo y StorySidePanel.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QToolBar, QGraphicsView,
    QInputDialog, QComboBox, QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QMessageBox
)
from PyQt6.QtGui import QPainter, QIcon, QFont, QAction, QColor
from PyQt6.QtCore import Qt, pyqtSignal as Signal, QTimer

from core.models import UniverseMetadata, StoryBlock, StoryArc
from ui.story_graph.scene import StoryGraphScene
from ui.story_graph.side_panel import StorySidePanel
from ui.story_graph.layout_worker import StoryLayoutWorker
from ui.story_graph.models import ARC_TYPE_CONFIG


class ConnectionDialog(QDialog):
    """Diálogo para configurar el tipo y etiqueta de una nueva conexión causal."""
    def __init__(self, source_id=None, all_blocks=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nueva Conexión Narrativa")
        self.resize(320, 180)
        self.setStyleSheet("""
            QDialog { background-color: #2c2c2e; color: #ffffff; }
            QLabel { color: #ffffff; font-weight: bold; }
            QComboBox, QLineEdit { background-color: #1c1c1e; color: #ffffff; border: 1px solid #3a3a3c; border-radius: 4px; padding: 6px; }
        """)

        layout = QFormLayout(self)
        
        self.target_combo = None
        if source_id and all_blocks:
            self.target_combo = QComboBox()
            for b in all_blocks:
                if b.id != source_id:
                    self.target_combo.addItem(b.title, b.id)
            layout.addRow("Conectar a:", self.target_combo)

        self.type_combo = QComboBox()
        for k, v in ARC_TYPE_CONFIG.items():
            self.type_combo.addItem(v["label"], k)

        self.label_edit = QLineEdit()
        self.label_edit.setPlaceholderText("Ej: Causa directa, Traición...")

        layout.addRow("Tipo de Relación:", self.type_combo)
        layout.addRow("Etiqueta (opcional):", self.label_edit)

        bbox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bbox.accepted.connect(self.accept)
        bbox.rejected.connect(self.reject)
        layout.addRow(bbox)

    def get_data(self):
        target_id = self.target_combo.currentData() if self.target_combo else None
        return target_id, self.type_combo.currentData(), self.label_edit.text().strip()


class InteractiveGraphicsView(QGraphicsView):
    """Vista personalizada para soportar zoom con la rueda del ratón."""
    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.scale(1.15, 1.15)
        else:
            self.scale(1 / 1.15, 1 / 1.15)


class StoryGraphWidget(QWidget):
    metadata_changed = Signal()
    navigate_to_chapter = Signal(str)  # chapter_id — para navegación desde doble clic

    def __init__(self, metadata: UniverseMetadata, parent=None):
        super().__init__(parent)
        self.metadata = metadata
        self._setup_ui()
        self._reload_graph()

    def showEvent(self, a0):
        super().showEvent(a0)
        # Re-aplicar tema por si cambió entre sesiones
        self._apply_theme()
        # Ajustar vista automáticamente poco después de que el widget se muestra
        QTimer.singleShot(100, self._fit_in_view)


    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Toolbar superior
        toolbar = QToolBar()
        from core.theme_manager import ThemeManager
        _is_dark = ThemeManager.is_dark()
        _tb_bg   = "#1c1c1e" if _is_dark else "#f0f0f2"
        _tb_sep  = "#2c2c2e" if _is_dark else "#d1d5db"
        _btn_bg  = "#2c2c2e" if _is_dark else "#e5e7eb"
        _btn_fg  = "#ffffff" if _is_dark else "#1c1c1e"
        _btn_hov = "#3a3a3c" if _is_dark else "#d1d5db"
        toolbar.setStyleSheet(f"""
            QToolBar {{
                background-color: {_tb_bg};
                border-bottom: 1px solid {_tb_sep};
                padding: 4px;
                spacing: 8px;
            }}
            QToolButton {{
                background-color: {_btn_bg};
                color: {_btn_fg};
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }}
            QToolButton:hover {{
                background-color: {_btn_hov};
            }}
        """)

        act_add_node = QAction("✨ Nuevo Bloque", self)
        act_add_node.triggered.connect(self._on_add_block_clicked)
        toolbar.addAction(act_add_node)

        act_relayout = QAction("🔄 Organizar Grafo", self)
        act_relayout.triggered.connect(self._on_relayout_clicked)
        toolbar.addAction(act_relayout)

        toolbar.addSeparator()

        act_zoom_in = QAction("🔍+", self)
        act_zoom_in.triggered.connect(lambda: self.view.scale(1.2, 1.2))
        toolbar.addAction(act_zoom_in)

        act_zoom_out = QAction("🔍-", self)
        act_zoom_out.triggered.connect(lambda: self.view.scale(0.8, 0.8))
        toolbar.addAction(act_zoom_out)

        act_reset_zoom = QAction("🎯 Ajustar Vista", self)
        act_reset_zoom.triggered.connect(self._fit_in_view)
        toolbar.addAction(act_reset_zoom)

        main_layout.addWidget(toolbar)

        # 2. Área central (Canvas + SidePanel)
        center_widget = QWidget()
        center_layout = QHBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        # Escena y Vista
        self.scene = StoryGraphScene(self)
        self.scene.node_created.connect(self._on_node_created)
        self.scene.connection_created.connect(self._on_connection_created)
        self.scene.node_selected.connect(self._on_node_selected)
        self.scene.node_moved.connect(self._on_node_moved)
        self.scene.node_deleted.connect(self._on_node_deleted)
        self.scene.arc_deleted.connect(self._on_arc_deleted)
        self.scene.request_full_connection.connect(self._on_full_connection_requested)
        self.scene.navigate_to_chapter.connect(self.navigate_to_chapter)  # burbujear

        self.view = InteractiveGraphicsView(self.scene)
        self.view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)
        self.view.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontSavePainterState)
        self.view.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing)
        self._apply_theme()

    def _apply_theme(self):
        """Aplica colores de fondo según el tema activo (claro u oscuro)."""
        from core.theme_manager import ThemeManager
        from PyQt6.QtGui import QBrush
        is_dark = ThemeManager.is_dark()
        bg_color = "#121214" if is_dark else "#f5f5f7"
        self.view.setStyleSheet(f"QGraphicsView {{ border: none; background-color: {bg_color}; }}")
        self.scene.setBackgroundBrush(QBrush(QColor(bg_color)))

        center_layout.addWidget(self.view, stretch=1)

        # Panel lateral
        self.side_panel = StorySidePanel(self)
        self.side_panel.block_updated.connect(self._on_block_updated)
        self.side_panel.block_deleted.connect(self._on_node_deleted)
        center_layout.addWidget(self.side_panel)

        main_layout.addWidget(center_widget)

    def _reload_graph(self):
        # Construir lookup {chapter_id: chapter_title} para mostrar en las tarjetas
        chapter_lookup = {}
        for obra in self.metadata.obras:
            for libro in obra.libros:
                for cap in libro.capitulos:
                    chapter_lookup[cap.id] = cap.title
        self.scene.load_graph(self.metadata.story_blocks, self.metadata.story_arcs, chapter_lookup)

    def _fit_in_view(self):
        items_rect = self.scene.itemsBoundingRect()
        if not items_rect.isEmpty():
            self.view.fitInView(items_rect.adjusted(-50, -50, 50, 50), Qt.AspectRatioMode.KeepAspectRatio)

    def _on_node_created(self, x: float, y: float):
        title, ok = QInputDialog.getText(self, "Nuevo Bloque Narrativo", "Título del evento o capítulo:")
        if ok and title.strip():
            new_block = StoryBlock(
                title=title.strip(),
                x=x,
                y=y
            )
            self.metadata.story_blocks.append(new_block)
            self.metadata_changed.emit()
            self._reload_graph()
            self._on_node_selected(new_block.id)

    def _on_add_block_clicked(self):
        center = self.view.mapToScene(self.view.viewport().rect().center())
        self._on_node_created(center.x(), center.y())

    def _on_connection_created(self, from_id: str, to_id: str):
        # Evitar conexiones duplicadas o auto-conexiones
        for a in self.metadata.story_arcs:
            if a.from_block == from_id and a.to_block == to_id:
                return

        dlg = ConnectionDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            _, arc_type, label = dlg.get_data()
            new_arc = StoryArc(
                from_block=from_id,
                to_block=to_id,
                arc_type=arc_type,
                label=label
            )
            self.metadata.story_arcs.append(new_arc)
            self.metadata_changed.emit()
            self._reload_graph()

    def _on_full_connection_requested(self, from_id: str):
        other_blocks = [b for b in self.metadata.story_blocks if b.id != from_id]
        if not other_blocks:
            QMessageBox.information(self, "Sin destinos", "No hay otros bloques para conectar. Crea otro bloque primero.")
            return
            
        dlg = ConnectionDialog(source_id=from_id, all_blocks=self.metadata.story_blocks, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            to_id, arc_type, label = dlg.get_data()
            if to_id:
                for a in self.metadata.story_arcs:
                    if a.from_block == from_id and a.to_block == to_id:
                        return
                
                new_arc = StoryArc(
                    from_block=from_id,
                    to_block=to_id,
                    arc_type=arc_type,
                    label=label
                )
                self.metadata.story_arcs.append(new_arc)
                self.metadata_changed.emit()
                self._reload_graph()

    def _get_all_chapters(self) -> list:
        """Retorna lista plana de (label, chapter_id) desde toda la jerarquía Obra>Libro>Capítulo."""
        result = []
        for obra in self.metadata.obras:
            for libro in obra.libros:
                for cap in libro.capitulos:
                    label = f"{obra.title} › {libro.title} › {cap.title}"
                    result.append((label, cap.id))
        return result

    def _on_node_selected(self, block_id: str):
        block = next((b for b in self.metadata.story_blocks if b.id == block_id), None)
        if block:
            self.side_panel.load_block(
                block,
                characters=self.metadata.characters,
                places=self.metadata.places,
                chapters=self._get_all_chapters()
            )

    def _on_node_moved(self, block_id: str, x: float, y: float):
        block = next((b for b in self.metadata.story_blocks if b.id == block_id), None)
        if block:
            block.x = x
            block.y = y
            self.metadata_changed.emit()

    def _on_block_updated(self, updated_block: StoryBlock):
        self.metadata_changed.emit()
        self._reload_graph()
        self._on_node_selected(updated_block.id)

    def _on_node_deleted(self, block_id: str):
        self.metadata.story_blocks = [b for b in self.metadata.story_blocks if b.id != block_id]
        self.metadata.story_arcs = [a for a in self.metadata.story_arcs if a.from_block != block_id and a.to_block != block_id]
        self.metadata_changed.emit()
        self.side_panel.hide()
        self._reload_graph()

    def _on_arc_deleted(self, arc_id: str):
        self.metadata.story_arcs = [a for a in self.metadata.story_arcs if a.id != arc_id]
        self.metadata_changed.emit()
        self._reload_graph()

    def _on_relayout_clicked(self):
        self.worker = StoryLayoutWorker(self.metadata.story_blocks, self.metadata.story_arcs)
        self.worker.layout_finished.connect(self._apply_layout_positions)
        self.worker.start()

    def _apply_layout_positions(self, positions: dict):
        for b in self.metadata.story_blocks:
            if b.id in positions:
                b.x, b.y = positions[b.id]
        self.metadata_changed.emit()
        self._reload_graph()
        self._fit_in_view()
