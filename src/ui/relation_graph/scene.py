"""
Módulo de Escena y Vista Gráfica: GraphScene y RelationGraphView.
"""

from typing import Optional, Dict, Set, List
from PyQt6.QtWidgets import (
    QGraphicsScene, QGraphicsView, QGraphicsItem,
    QGraphicsEllipseItem, QGraphicsTextItem, QFrame,
)
from PyQt6.QtCore import Qt, QRectF, QPointF, QTimeLine, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QPainter, QTransform, QSurfaceFormat

try:
    from PyQt6.QtOpenGLWidgets import QOpenGLWidget
    _OPENGL_AVAILABLE = True
except Exception:
    _OPENGL_AVAILABLE = False

from core.models import Character
from core.theme_manager import ThemeManager
from .models import DIM_ALPHA, CHARACTER_PALETTE, CharacterMetrics
from .items import CharacterNode, RelationEdge, CleanBackground


# ── Escena Gráfica de Alto Rendimiento ────────────────────────────────────────

class GraphScene(QGraphicsScene):
    character_focused = pyqtSignal(str)
    character_clicked = pyqtSignal(str)
    node_clicked = pyqtSignal(str)
    node_double_clicked = pyqtSignal(str)
    background_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.BspTreeIndex)
        self.setBspTreeDepth(16)
        self._focused_id: Optional[str] = None
        self._nodes: dict[str, CharacterNode] = {}
        self._edges: list[RelationEdge] = []
        # Índices de adyacencia O(1) para navegación instantánea
        self._adj_nodes: Dict[str, Set[str]] = {}
        self._adj_edges: Dict[str, List[RelationEdge]] = {}

    def populate(self, characters: list, relations: list, positions: dict, metrics_map: dict, is_dark: bool = True):
        self.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.NoIndex)
        self.clear()
        self._nodes.clear()
        self._edges.clear()
        self._adj_nodes.clear()
        self._adj_edges.clear()

        # Dynamic bounding calculation
        min_x, max_x = -1000.0, 1000.0
        min_y, max_y = -1000.0, 1000.0
        if positions:
            xs = [p[0] for p in positions.values()]
            ys = [p[1] for p in positions.values()]
            min_x, max_x = min(xs) - 400.0, max(xs) + 400.0
            min_y, max_y = min(ys) - 400.0, max(ys) + 400.0

        bound_w = max(4000.0, max_x - min_x)
        bound_h = max(4000.0, max_y - min_y)
        self.setSceneRect(min_x, min_y, bound_w, bound_h)

        # 1. Create nodes
        for idx, char_data in enumerate(characters):
            if isinstance(char_data, dict):
                char = Character(**{k: v for k, v in char_data.items() if k in Character.__annotations__})
            else:
                char = char_data
            
            char_id = str(char.id)
            metrics = metrics_map.get(char_id, CharacterMetrics())
            color = CHARACTER_PALETTE[idx % len(CHARACTER_PALETTE)]
            pos = positions.get(char_id, (0.0, 0.0))

            node = CharacterNode(char, metrics, color, pos[0], pos[1])
            self.addItem(node)
            self._nodes[char_id] = node
            self._adj_nodes[char_id] = set()
            self._adj_edges[char_id] = []

        # 2. Store relation records & determine LOD mode (visible global edges if <= 100 relations)
        self._raw_relations: Dict[str, List[tuple]] = {}  # char_id -> [(other_id, label, intensity, rel_type)]
        self._all_edges: List[RelationEdge] = []
        
        seen_global_pairs = set()
        for rel in relations:
            if isinstance(rel, dict):
                src_id = str(rel.get("source") or rel.get("char_id_a") or "")
                tgt_id = str(rel.get("target") or rel.get("char_id_b") or "")
                label = rel.get("label", "")
                intensity = int(rel.get("intensity", 3))
                rel_type = str(rel.get("relation_type", "otro"))
            else:
                src_id = str(getattr(rel, "char_id_a", getattr(rel, "source", "")))
                tgt_id = str(getattr(rel, "char_id_b", getattr(rel, "target", "")))
                label = getattr(rel, "label", "")
                intensity = int(getattr(rel, "intensity", 3))
                rel_type = str(getattr(rel, "relation_type", "otro"))

            if src_id in self._nodes and tgt_id in self._nodes and src_id != tgt_id:
                self._adj_nodes[src_id].add(tgt_id)
                self._adj_nodes[tgt_id].add(src_id)
                self._raw_relations.setdefault(src_id, []).append((tgt_id, label, intensity, rel_type))
                self._raw_relations.setdefault(tgt_id, []).append((src_id, label, intensity, rel_type))

                # Si el grafo tiene una cantidad manejable (<= 100 relaciones), creamos la arista visible globalmente
                pair_key = tuple(sorted([src_id, tgt_id]))
                if pair_key not in seen_global_pairs and len(relations) <= 100:
                    seen_global_pairs.add(pair_key)
                    s_node = self._nodes[src_id]
                    t_node = self._nodes[tgt_id]
                    edge = RelationEdge(s_node, t_node, label, intensity, rel_type)
                    self.addItem(edge)
                    edge.set_active_focus(active=False, dim_others=False)
                    self._all_edges.append(edge)

        self.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.BspTreeIndex)

    def get_node(self, char_id: str) -> Optional[CharacterNode]:
        return self._nodes.get(str(char_id))

    def _node_clicked(self, char_id: str):
        self._set_focus(char_id)
        self.node_clicked.emit(char_id)
        self.character_clicked.emit(char_id)

    def _node_double_clicked(self, char_id: str):
        self.node_double_clicked.emit(char_id)
        self.character_focused.emit(char_id)

    def _set_focus(self, char_id: Optional[str]):
        if not char_id:
            self._clear_focus()
            return

        self._focused_id = char_id
        neighbors = self._adj_nodes.get(char_id, set())
        connected = {char_id} | neighbors

        # 1. Ajuste visual de los nodos
        for nid, node in self._nodes.items():
            if nid == char_id:
                node.setZValue(12)
                node.set_focused_ring(True, dim_others=False)
            elif nid in connected:
                node.setZValue(8)
                node.set_focused_ring(False, dim_others=False)
            else:
                node.setZValue(4)
                node.set_focused_ring(False, dim_others=True)

        # 2. Aristas: Si ya existen aristas globales, destacamos las del nodo y atenuamos las demás
        if self._all_edges:
            for edge in self._all_edges:
                is_connected = (edge.source == self._nodes.get(char_id) or edge.target == self._nodes.get(char_id))
                if is_connected:
                    edge.set_active_focus(active=True, dim_others=False)
                else:
                    edge.set_active_focus(active=False, dim_others=True)
        else:
            # Modo masivo (> 100 relaciones): Instanciación Lazy exclusiva del nodo seleccionado
            for edge in self._edges:
                self.removeItem(edge)
            self._edges.clear()

            src_node = self._nodes.get(char_id)
            if src_node:
                seen_pairs = set()
                for other_id, label, intensity, rel_type in self._raw_relations.get(char_id, []):
                    if other_id not in self._nodes or other_id in seen_pairs:
                        continue
                    seen_pairs.add(other_id)
                    tgt_node = self._nodes[other_id]
                    edge = RelationEdge(src_node, tgt_node, label, intensity, rel_type)
                    self.addItem(edge)
                    edge.set_active_focus(active=True, dim_others=False)
                    self._edges.append(edge)

    def _clear_focus(self):
        self._focused_id = None
        # Restaurar aristas globales a estado normal de reposo
        if self._all_edges:
            for edge in self._all_edges:
                edge.set_active_focus(active=False, dim_others=False)
        else:
            for edge in self._edges:
                self.removeItem(edge)
            self._edges.clear()

        for node in self._nodes.values():
            node.setZValue(10 if node.metrics.tier == "core" else (7 if node.metrics.tier == "primary" else 5))
            node.set_focused_ring(False, dim_others=False)

    def set_show_all_edges(self, show_all: bool):
        """Alterna dinámicamente entre ver todas las líneas globales o solo las de foco."""
        self._show_all_edges_enabled = show_all
        if self._all_edges:
            for edge in self._all_edges:
                if show_all:
                    if self._focused_id:
                        is_connected = (edge.source == self._nodes.get(self._focused_id) or edge.target == self._nodes.get(self._focused_id))
                        edge.set_active_focus(active=is_connected, dim_others=not is_connected)
                    else:
                        edge.set_active_focus(active=False, dim_others=False)
                else:
                    if self._focused_id:
                        is_connected = (edge.source == self._nodes.get(self._focused_id) or edge.target == self._nodes.get(self._focused_id))
                        if is_connected:
                            edge.set_active_focus(active=True, dim_others=False)
                        else:
                            edge.setVisible(False)
                    else:
                        edge.setVisible(False)

    def update_theme(self, is_dark: bool):
        for node in self._nodes.values():
            node.update()
        for edge in self._edges:
            edge.update()
        for edge in self._all_edges:
            edge.update()

    def clear_selection_and_focus(self):
        self._clear_focus()
        self.background_clicked.emit()
        self.character_clicked.emit("")

    def mousePressEvent(self, event):
        super().mousePressEvent(event)


# ── Vista de Alto Rendimiento con Aceleración Adaptativa ───────────────────────

class RelationGraphView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        
        bg_color = "#1c1c1e" if ThemeManager.is_dark() else "#f5f0ea"
        self.setStyleSheet(f"QGraphicsView {{ background-color: {bg_color}; border: none; }}")

        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.BoundingRectViewportUpdate)
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing, True)
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontSavePainterState, True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QBrush(QColor(bg_color)))
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        self._press_pos = None
        # Animación de cámara suave
        self._anim_timeline: Optional[QTimeLine] = None
        self._anim_start_transform: Optional[QTransform] = None
        self._anim_target_center: Optional[QPointF] = None
        self._anim_target_zoom: float = 1.0

    def drawBackground(self, painter: QPainter, rect: QRectF):
        bg = "#1c1c1e" if ThemeManager.is_dark() else "#f5f0ea"
        painter.fillRect(rect, QColor(bg))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = event.pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if event.button() == Qt.MouseButton.LeftButton and self._press_pos is not None:
            dist = (event.pos() - self._press_pos).manhattanLength()
            self._press_pos = None
            # Solo si fue un clic estático (sin arrastrar el lienzo con la manita)
            if dist < 6:
                scene_pos = self.mapToScene(event.pos())
                item = self.scene().itemAt(scene_pos, self.transform()) if self.scene() else None
                if not isinstance(item, CharacterNode):
                    if hasattr(self.scene(), "clear_selection_and_focus"):
                        self.scene().clear_selection_and_focus()

    # ── Zoom ──────────────────────────────────────────────────────────────────
    _ZOOM_MIN = 0.005
    _ZOOM_MAX = 50.0
    _ZOOM_STEP = 1.22

    def current_zoom(self) -> float:
        return self.transform().m11()

    def zoom_in(self):
        self._apply_zoom(self._ZOOM_STEP)

    def zoom_out(self):
        self._apply_zoom(1.0 / self._ZOOM_STEP)

    def _apply_zoom(self, factor: float):
        curr = self.current_zoom()
        new_zoom = curr * factor
        if self._ZOOM_MIN <= new_zoom <= self._ZOOM_MAX:
            self.scale(factor, factor)

    def wheelEvent(self, event):
        """Rueda del ratón = zoom centrado bajo el cursor."""
        delta = event.angleDelta().y()
        if delta == 0:
            return
        steps = delta / 120.0
        factor = self._ZOOM_STEP ** steps
        self._apply_zoom(factor)
        event.accept()

    def keyPressEvent(self, event):
        key = event.key()
        mod = event.modifiers()
        if key in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
            self.zoom_in()
        elif key == Qt.Key.Key_Minus:
            self.zoom_out()
        elif key == Qt.Key.Key_0 and mod & Qt.KeyboardModifier.ControlModifier:
            self.resetTransform()
        else:
            super().keyPressEvent(event)

    def fit_all(self):
        """Ajustar vista: encuadra automáticamente todo el grafo dentro del viewport."""
        scene = self.scene()
        if not scene:
            return
        rect = scene.itemsBoundingRect()
        if rect.isValid() and not rect.isEmpty() and rect.width() > 50:
            self.fitInView(rect.adjusted(-80, -80, 80, 80), Qt.AspectRatioMode.KeepAspectRatio)
        else:
            self.resetTransform()

    def center_on_character(self, node, neighbors: list, animate: bool = True):
        """
        Centra y hace zoom al radio de influencia del personaje:
        el nodo seleccionado + todos sus vecinos directos.
        Si animate=True hace una transición suave (~350ms).
        """
        all_nodes = [node] + [n for n in neighbors if n is not None]
        if not all_nodes:
            return

        xs = [n.pos().x() for n in all_nodes]
        ys = [n.pos().y() for n in all_nodes]
        pad = max(120.0, node._radius * 4)
        rect = QRectF(
            min(xs) - pad, min(ys) - pad,
            (max(xs) - min(xs)) + pad * 2,
            (max(ys) - min(ys)) + pad * 2
        )
        # Calcular zoom necesario para que el rect quepa en la viewport
        vw = self.viewport().width()  or 800
        vh = self.viewport().height() or 600
        zoom_x = vw / rect.width()  if rect.width()  > 0 else 1.0
        zoom_y = vh / rect.height() if rect.height() > 0 else 1.0
        target_zoom = min(zoom_x, zoom_y, self._ZOOM_MAX) * 0.88  # pequeño margen
        target_zoom = max(target_zoom, self._ZOOM_MIN)
        target_center = rect.center()

        if not animate:
            self.resetTransform()
            self.scale(target_zoom, target_zoom)
            self.centerOn(target_center)
            return

        # Detener animación anterior si existe
        if self._anim_timeline and self._anim_timeline.state() != QTimeLine.State.NotRunning:
            self._anim_timeline.stop()

        self._anim_start_transform = QTransform(self.transform())
        self._anim_start_center    = QPointF(self.mapToScene(self.viewport().rect().center()))
        self._anim_target_center   = target_center
        self._anim_target_zoom     = target_zoom

        tl = QTimeLine(380, self)
        tl.setUpdateInterval(16)   # ~60fps
        tl.valueChanged.connect(self._on_anim_step)
        tl.setEasingCurve = lambda *_: None   # usamos interpolación manual
        self._anim_timeline = tl
        tl.start()

    def _on_anim_step(self, t: float):
        """t va de 0.0 a 1.0 (ease-out suave)."""
        # Ease-out cúbico: rápido al inicio, lento al final
        t = 1.0 - (1.0 - t) ** 3
        start_zoom = self._anim_start_transform.m11() if self._anim_start_transform else self.current_zoom()
        zoom_now   = start_zoom + (self._anim_target_zoom - start_zoom) * t
        cx_start   = self._anim_start_center.x()  if self._anim_start_center  else 0.0
        cy_start   = self._anim_start_center.y()  if self._anim_start_center  else 0.0
        cx_now     = cx_start + (self._anim_target_center.x() - cx_start) * t
        cy_now     = cy_start + (self._anim_target_center.y() - cy_start) * t

        self.resetTransform()
        self.scale(zoom_now, zoom_now)
        self.centerOn(QPointF(cx_now, cy_now))

    def mouseDoubleClickEvent(self, event):
        """Ignora el reseteo automático de vista para preservar la posición del usuario."""
        super().mouseDoubleClickEvent(event)


