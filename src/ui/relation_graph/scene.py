"""
Módulo de Escena y Vista Gráfica: GraphScene y RelationGraphView.
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QGraphicsScene, QGraphicsView, QGraphicsItem,
    QGraphicsEllipseItem, QGraphicsTextItem, QFrame,
)
from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QPainter

from core.models import Character
from core.theme_manager import ThemeManager
from .models import DIM_ALPHA, CHARACTER_PALETTE, CharacterMetrics
from .items import CharacterNode, RelationEdge, CleanBackground


# ── Escena Gráfica ────────────────────────────────────────────────────────────

class GraphScene(QGraphicsScene):
    character_focused = pyqtSignal(str)
    character_clicked = pyqtSignal(str)
    node_clicked = pyqtSignal(str)
    node_double_clicked = pyqtSignal(str)
    background_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.BspTreeIndex)
        self.setBspTreeDepth(14)
        self._focused_id: Optional[str] = None
        self._nodes: dict[str, CharacterNode] = {}
        self._edges: list[RelationEdge] = []
        self._bg_item: Optional[CleanBackground] = None

    def populate(self, characters: list, relations: list, positions: dict, metrics_map: dict, is_dark: bool = True):
        self.clear()
        self._nodes.clear()
        self._edges.clear()

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

        # Add clean background with appropriate bounds
        self._bg_item = CleanBackground(QRectF(min_x, min_y, bound_w, bound_h), is_dark=is_dark)
        self.addItem(self._bg_item)

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

        # 2. Create edges (with LOD handling for high counts)
        show_all_labels = len(relations) < 400
        for rel in relations:
            if isinstance(rel, dict):
                src_id = str(rel.get("source") or rel.get("char_id_a") or "")
                tgt_id = str(rel.get("target") or rel.get("char_id_b") or "")
                label = rel.get("label", "") if show_all_labels else ""
                intensity = int(rel.get("intensity", 3))
                rel_type = str(rel.get("relation_type", "otro"))
            else:
                src_id = str(getattr(rel, "char_id_a", getattr(rel, "source", "")))
                tgt_id = str(getattr(rel, "char_id_b", getattr(rel, "target", "")))
                label = getattr(rel, "label", "") if show_all_labels else ""
                intensity = int(getattr(rel, "intensity", 3))
                rel_type = str(getattr(rel, "relation_type", "otro"))

            if src_id in self._nodes and tgt_id in self._nodes and src_id != tgt_id:
                edge = RelationEdge(self._nodes[src_id], self._nodes[tgt_id], label, intensity, rel_type)
                edge.add_to_scene(self)
                self.addItem(edge)
                self._edges.append(edge)

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
        connected = {char_id}
        for e in self._edges:
            if e.source.char_id == char_id: connected.add(e.target.char_id)
            elif e.target.char_id == char_id: connected.add(e.source.char_id)

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

        for edge in self._edges:
            is_adj = (edge.source.char_id == char_id or edge.target.char_id == char_id)
            edge.set_active_focus(active=is_adj, dim_others=True)

    def _clear_focus(self):
        self._focused_id = None
        for node in self._nodes.values():
            node.setZValue(10 if node.metrics.tier == "core" else (7 if node.metrics.tier == "primary" else 5))
            node.set_focused_ring(False, dim_others=False)
        for edge in self._edges:
            edge.set_active_focus(active=False, dim_others=False)

    def update_theme(self, is_dark: bool):
        if self._bg_item:
            self._bg_item._is_dark = is_dark
            self._bg_item.update()
        for node in self._nodes.values():
            node.update()

    def mousePressEvent(self, event):
        from PyQt6.QtGui import QTransform
        t = self.views()[0].transform() if self.views() else QTransform()
        item = self.itemAt(event.scenePos(), t)
        is_node = isinstance(item, CharacterNode)
        if not is_node:
            self._clear_focus()
            self.background_clicked.emit()
            self.character_clicked.emit("")
        super().mousePressEvent(event)


# ── Vista de Alto Rendimiento ─────────────────────────────────────────────────

class RelationGraphView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.BoundingRectViewportUpdate)
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing, True)
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontSavePainterState, True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        bg = "#1c1c1e" if ThemeManager.is_dark() else "#f5f0ea"
        self.setBackgroundBrush(QBrush(QColor(bg)))
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setFocusPolicy(Qt.FocusPolicy.WheelFocus)

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
        """Ajustar todos los nodos de la escena a la vista de manera instantánea."""
        scene = self.scene()
        if scene:
            nodes = getattr(scene, "_nodes", {})
            if nodes:
                xs = [n.pos().x() for n in nodes.values()]
                ys = [n.pos().y() for n in nodes.values()]
                if xs and ys:
                    rect = QRectF(min(xs) - 80, min(ys) - 80, (max(xs) - min(xs)) + 160, (max(ys) - min(ys)) + 160)
                    self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
                    return
            r = scene.sceneRect()
            if not r.isEmpty():
                self.fitInView(r, Qt.AspectRatioMode.KeepAspectRatio)

    def mouseDoubleClickEvent(self, event):
        """Ignora el reseteo automático de vista para preservar la posición del usuario."""
        super().mouseDoubleClickEvent(event)


