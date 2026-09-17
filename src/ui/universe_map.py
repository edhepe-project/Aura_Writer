"""
Mapa Mental del Universo — QGraphicsScene + QGraphicsView con NetworkX spring_layout.
Permite conectar elementos de distintas Obras, arrastrar nodos, zoom, pan,
y doble clic en un nodo → abre ese Capítulo en el editor.
"""

import math
import logging
from PyQt6.QtWidgets import (QGraphicsScene, QGraphicsView, QGraphicsEllipseItem,
                             QGraphicsTextItem, QGraphicsLineItem, QWidget,
                             QVBoxLayout, QLabel, QGraphicsItem, QHBoxLayout,
                             QPushButton)
from PyQt6.QtCore import Qt, QRectF, QPointF, QTimer, pyqtSignal
from PyQt6.QtGui import QBrush, QPen, QColor, QFont, QPainter
from core.models import UniverseMetadata

log = logging.getLogger(__name__)

# Colores claros por tipo de nodo (visibles sobre #1c1c1e)
NODE_COLORS = {
    "universe": "#5e5ce6",   # índigo
    "obra":     "#bf5af2",   # violeta
    "libro":    "#0a84ff",   # azul
    "chapter":  "#30d158",   # verde
    "media":    "#ffd60a",   # amarillo
}

NODE_BORDER_COLORS = {
    "universe": "#a7a5f0",
    "obra":     "#e0a0fc",
    "libro":    "#64acff",
    "chapter":  "#6ee88f",
    "media":    "#ffe566",
}

# Texto blanco sobre todos los nodos (máximo contraste)
NODE_TEXT_COLORS = {
    "universe": "#ffffff",
    "obra":     "#ffffff",
    "libro":    "#ffffff",
    "chapter":  "#ffffff",
    "media":    "#1c1c1e",   # oscuro sobre amarillo
}

NODE_SIZES = {
    "universe": 52,
    "obra":     40,
    "libro":    30,
    "chapter":  22,
    "media":    18,
}


class DraggableNode(QGraphicsEllipseItem):
    """Nodo arrastrable en el mapa mental."""

    def __init__(self, node_id: str, node_type: str, label: str,
                 x: float, y: float, radius: float):
        super().__init__(-radius, -radius, radius * 2, radius * 2)
        self.node_id = node_id
        self.node_type = node_type
        self.setPos(x, y)

        bg   = QColor(NODE_COLORS.get(node_type, "#2c2c2e"))
        brd  = QColor(NODE_BORDER_COLORS.get(node_type, "#636366"))
        self.setBrush(QBrush(bg))
        pen = QPen(brd, 2)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        self.setPen(pen)

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setZValue(2)

        self.setToolTip(f"{node_type.upper()}: {label}")

        # Etiqueta con color único por tipo
        txt_color = NODE_TEXT_COLORS.get(node_type, "#f2f2f7")
        self._label = QGraphicsTextItem(label, self)
        self._label.setDefaultTextColor(QColor(txt_color))
        font = QFont("Segoe UI", max(7, int(radius * 0.42)))
        font.setBold(True)
        self._label.setFont(font)
        br = self._label.boundingRect()
        self._label.setPos(-br.width() / 2, -br.height() / 2)

        self.edges: list = []

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            for edge in self.edges:
                edge.update_position()
        return super().itemChange(change, value)


class LabeledEdge(QGraphicsLineItem):
    """Arista entre dos nodos."""

    def __init__(self, source: DraggableNode, target: DraggableNode, label: str = ""):
        super().__init__()
        self.source = source
        self.target = target
        pen = QPen(QColor("#48484a"), 1.5, Qt.PenStyle.SolidLine)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.setPen(pen)
        self.setZValue(1)

        self._label_item = None
        if label:
            self._label_item = QGraphicsTextItem(label, self)
            self._label_item.setDefaultTextColor(QColor("#636366"))
            self._label_item.setFont(QFont("Segoe UI", 8))

        source.edges.append(self)
        target.edges.append(self)
        self.update_position()

    def update_position(self):
        p1 = self.source.scenePos()
        p2 = self.target.scenePos()
        self.setLine(p1.x(), p1.y(), p2.x(), p2.y())
        if self._label_item:
            mid = QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
            self._label_item.setPos(mid)


class UniverseMapView(QGraphicsView):
    """Vista del mapa mental con zoom y pan."""
    chapter_requested = pyqtSignal(str)

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        from core.theme_manager import ThemeManager

        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        bg_col = "#1c1c1e" if ThemeManager.is_dark() else "#f5f0ea"
        self.setBackgroundBrush(QBrush(QColor(bg_col)))
        self._zoom = 1.0

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self._zoom *= factor
        if 0.15 < self._zoom < 6.0:
            self.scale(factor, factor)
        else:
            self._zoom /= factor

    def mouseDoubleClickEvent(self, event):
        item = self.itemAt(event.pos())
        if isinstance(item, DraggableNode) and item.node_type == "chapter":
            self.chapter_requested.emit(item.node_id)
        elif isinstance(item, QGraphicsTextItem):
            parent = item.parentItem()
            if isinstance(parent, DraggableNode) and parent.node_type == "chapter":
                self.chapter_requested.emit(parent.node_id)
        super().mouseDoubleClickEvent(event)


class UniverseMapWidget(QWidget):
    """Widget completo del mapa mental del universo."""
    chapter_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        header = QHBoxLayout()
        lbl = QLabel("MAPA MENTAL DEL UNIVERSO")
        lbl.setStyleSheet("font-weight:700; font-size:11px; letter-spacing:1px;")
        header.addWidget(lbl)

        btn_fit = QPushButton("Ajustar vista")
        btn_fit.clicked.connect(self._fit_view)
        header.addStretch()
        header.addWidget(btn_fit)
        layout.addLayout(header)

        self._scene = QGraphicsScene(self)
        self._view = UniverseMapView(self._scene, self)
        self._view.chapter_requested.connect(self.chapter_requested)
        layout.addWidget(self._view)

        self._nodes: dict[str, DraggableNode] = {}
        self._pending_fit = False

    def showEvent(self, event):
        """Al mostrarse, ajustar la vista con un pequeño retardo para que
        el layout haya terminado de calcularse."""
        super().showEvent(event)
        if self._pending_fit:
            QTimer.singleShot(80, self._fit_view)

    def _fit_view(self):
        rect = self._scene.sceneRect()
        if not rect.isNull():
            self._view.fitInView(rect.adjusted(-80, -80, 80, 80),
                                 Qt.AspectRatioMode.KeepAspectRatio)

    def build_from_metadata(self, meta: UniverseMetadata):
        """Construye el mapa mental con layout radial concéntrico."""
        self._scene.clear()
        self._nodes.clear()

        from core.theme_manager import ThemeManager
        bg_col = "#1c1c1e" if ThemeManager.is_dark() else "#f5f0ea"
        self._view.setBackgroundBrush(QBrush(QColor(bg_col)))

        uid = "universe_root"
        node_types:  dict[str, str] = {uid: "universe"}
        node_labels: dict[str, str] = {uid: meta.title}

        ring1: list[str] = []
        ring2: list[tuple[str, int]] = []
        edges: list[tuple[str, str, str]] = []

        for obra in meta.obras:
            for libro in obra.libros:
                libro_idx = len(ring1)
                ring1.append(libro.id)
                node_types[libro.id]  = "libro"
                node_labels[libro.id] = libro.title
                edges.append((uid, libro.id, ""))

                for cap in libro.capitulos:
                    ring2.append((cap.id, libro_idx))
                    node_types[cap.id]  = "chapter"
                    node_labels[cap.id] = cap.title
                    edges.append((libro.id, cap.id, ""))

        all_ids = set(node_types.keys())
        for link in meta.universe_links:
            if link.source_id in all_ids and link.target_id in all_ids:
                edges.append((link.source_id, link.target_id, link.label))

        if not node_types:
            return

        # Posiciones radiales
        RING_RADII = [0, 200, 420]
        pos: dict[str, tuple[float, float]] = {uid: (0.0, 0.0)}

        n1 = len(ring1)
        for i, nid in enumerate(ring1):
            angle = 2 * math.pi * i / max(n1, 1) - math.pi / 2
            pos[nid] = (math.cos(angle) * RING_RADII[1],
                        math.sin(angle) * RING_RADII[1])

        if ring2:
            for parent_idx in range(n1):
                children = [(nid, i) for i, (nid, pidx) in enumerate(ring2)
                            if pidx == parent_idx]
                if not children:
                    continue
                parent_angle = 2 * math.pi * parent_idx / max(n1, 1) - math.pi / 2
                spread = (2 * math.pi / max(n1, 1)) * 0.8
                nc = len(children)
                for j, (nid, _) in enumerate(children):
                    a = parent_angle - spread/2 + spread * (j + 0.5) / max(nc, 1)
                    pos[nid] = (math.cos(a) * RING_RADII[2],
                                math.sin(a) * RING_RADII[2])

        # Crear nodos
        for nid, (px, py) in pos.items():
            ntype  = node_types.get(nid, "chapter")
            label  = node_labels.get(nid, nid[:8])
            radius = NODE_SIZES.get(ntype, 22)
            node_item = DraggableNode(nid, ntype, label, px, py, radius)
            self._scene.addItem(node_item)
            self._nodes[nid] = node_item

        # Crear aristas
        for src, dst, label in edges:
            if src in self._nodes and dst in self._nodes:
                edge = LabeledEdge(self._nodes[src], self._nodes[dst], label)
                self._scene.addItem(edge)

        # Marcar para ajustar cuando el widget sea visible
        self._pending_fit = True
        # Intentar ajustar inmediatamente también (por si ya es visible)
        QTimer.singleShot(50, self._fit_view)
