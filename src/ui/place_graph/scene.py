"""
scene.py — Escena y Vista interactiva de Alto Rendimiento para el Grafo de Lugares.
"""
from __future__ import annotations

from typing import Optional

from PyQt6.QtWidgets import (
    QGraphicsScene, QGraphicsView, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import (
    QPainter, QBrush, QColor, QTransform
)

from .items import PlaceNodeItem, PlaceLinkItem


class PlaceGraphScene(QGraphicsScene):
    """
    Escena interactiva del Atlas de Lugares.
    Gestiona foco inteligente, iluminación de adyacencias y desvanecimiento de nodos secundarios.
    """
    place_selected = pyqtSignal(str)
    place_double_clicked = pyqtSignal(str)
    background_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.BspTreeIndex)
        self._focused_id: str | None = None
        self._nodes: dict[str, PlaceNodeItem] = {}
        self._all_edges: list[PlaceLinkItem] = []
        self._adj: dict[str, set[str]] = {}

    def _node_clicked(self, place_id: str):
        self._set_focus(place_id)
        self.place_selected.emit(place_id)

    def _node_double_clicked(self, place_id: str):
        self.place_double_clicked.emit(place_id)

    def _set_focus(self, place_id: str | None):
        if not place_id:
            self.clear_selection_and_focus()
            return
        self._focused_id = place_id
        neighbors = self._adj.get(place_id, set())
        connected = {place_id} | neighbors

        # 1. Nodos: el enfocado resalta, vecinos activos, resto atenuado
        for nid, node in self._nodes.items():
            if nid == place_id:
                node.set_focused(True, False)
            elif nid in connected:
                node.set_focused(False, False)
            else:
                node.set_focused(False, True)

        # 2. Aristas: solo las conectadas se iluminan con glow
        for edge in self._all_edges:
            is_mine = (edge.node_a.place.id == place_id or
                       edge.node_b.place.id == place_id)
            if is_mine:
                edge.set_active_focus(True, False)
            else:
                edge.set_active_focus(False, True)

    def clear_selection_and_focus(self):
        self._focused_id = None
        for node in self._nodes.values():
            node.set_focused(False, False)
        for edge in self._all_edges:
            edge.set_active_focus(False, False)
        self.background_clicked.emit()


class PlaceGraphView(QGraphicsView):
    """
    Vista de alto rendimiento con paneo fluido, zoom centrado y fondo cósmico oscuro.
    """
    def __init__(self, scene: PlaceGraphScene, parent=None):
        super().__init__(scene, parent)
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
        self.setBackgroundBrush(QBrush(QColor("#0d0d0f")))
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        self.setStyleSheet("QGraphicsView { background: #0d0d0f; border: none; }")
        self._press_pos = None

    def drawBackground(self, painter: QPainter | None, rect: QRectF):
        if painter is None:
            return
        painter.fillRect(rect, QColor("#0d0d0f"))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = event.pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if event.button() == Qt.MouseButton.LeftButton and self._press_pos is not None:
            dist = (event.pos() - self._press_pos).manhattanLength()
            self._press_pos = None
            if dist < 6:
                scene_pos = self.mapToScene(event.pos())
                item = self.scene().itemAt(scene_pos, self.transform()) if self.scene() else None
                if not isinstance(item, PlaceNodeItem):
                    if hasattr(self.scene(), "clear_selection_and_focus"):
                        self.scene().clear_selection_and_focus()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta == 0:
            return
        factor = 1.15 if delta > 0 else (1.0 / 1.15)
        self.scale(factor, factor)
        event.accept()
