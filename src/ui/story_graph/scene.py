"""
Escena gráfica interactiva QGraphicsScene para el Cronograma Narrativo.
Gestiona el canvas, creación por doble clic, conexiones por arrastre y selección.
"""

from PyQt6.QtWidgets import QGraphicsScene, QGraphicsSceneMouseEvent, QMenu
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QPainterPath
from PyQt6.QtCore import Qt, pyqtSignal as Signal, QPointF, QRectF

from core.models import StoryBlock, StoryArc
from ui.story_graph.items import StoryNodeItem, StoryArcItem


class StoryGraphScene(QGraphicsScene):
    node_selected = Signal(str)            # block_id
    node_double_clicked = Signal(str)     # block_id
    node_created = Signal(float, float)    # x, y
    connection_created = Signal(str, str) # from_block_id, to_block_id
    node_moved = Signal(str, float, float)# block_id, x, y
    node_deleted = Signal(str)            # block_id
    arc_deleted = Signal(str)             # arc_id
    request_full_connection = Signal(str) # from_block_id
    navigate_to_chapter = Signal(str)     # chapter_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackgroundBrush(QBrush(QColor("#1e1e1e")))
        self.setSceneRect(-5000, -5000, 10000, 10000)

        self._node_items = {}  # block_id -> StoryNodeItem
        self._arc_items = {}   # arc_id -> StoryArcItem

        # Estado de conexión drag & drop
        self._connecting_source_item = None
        self._temp_line_item = None

    def drawBackground(self, painter: QPainter | None, rect: QRectF):
        if painter is None: return
        super().drawBackground(painter, rect)

        from core.theme_manager import ThemeManager
        # Rejilla suave de fondo (grid dots)
        grid_color = "#2a2a2c" if ThemeManager.is_dark() else "#d1d5db"
        painter.setPen(QPen(QColor(grid_color), 1.0))
        grid_size = 30
        left = int(rect.left()) - (int(rect.left()) % grid_size)
        top = int(rect.top()) - (int(rect.top()) % grid_size)

        for x in range(left, int(rect.right()), grid_size):
            for y in range(top, int(rect.bottom()), grid_size):
                painter.drawPoint(x, y)

    def load_graph(self, blocks: list[StoryBlock], arcs: list[StoryArc], chapter_lookup: dict | None = None):
        """Carga el grafo. chapter_lookup: {chapter_id: chapter_title}"""
        self.clear()
        self._node_items.clear()
        self._arc_items.clear()
        _lookup = chapter_lookup or {}

        for b in blocks:
            chapter_title = _lookup.get(b.chapter_id, "") if b.chapter_id else ""
            item = StoryNodeItem(b, chapter_title=chapter_title)
            item.signals.moved.connect(self._on_node_moved)
            item.signals.selected.connect(self._on_node_selected)
            self.addItem(item)
            self._node_items[b.id] = item

        for a in arcs:
            if a.from_block in self._node_items and a.to_block in self._node_items:
                src = self._node_items[a.from_block]
                tgt = self._node_items[a.to_block]
                arc_item = StoryArcItem(a, src, tgt)
                self.addItem(arc_item)
                self._arc_items[a.id] = arc_item

    def _on_node_moved(self, block_id: str, x: float, y: float):
        # Actualizar arcos conectados
        for arc_item in self._arc_items.values():
            if arc_item.arc.from_block == block_id or arc_item.arc.to_block == block_id:
                arc_item.update_path()
        self.node_moved.emit(block_id, x, y)

    def _on_node_selected(self, block_id: str):
        self.node_selected.emit(block_id)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent | None):
        if event is None: return
        item = self.itemAt(event.scenePos(), self.views()[0].transform() if self.views() else None)
        if isinstance(item, StoryNodeItem):
            block = item.block
            # Si el bloque está 'escrito' y tiene capítulo asignado: navegar
            if block.status == "escrito" and block.chapter_id:
                self.navigate_to_chapter.emit(block.chapter_id)
            else:
                # Comportamiento normal: abrir panel lateral
                self.node_double_clicked.emit(block.id)
        elif item is None:
            pos = event.scenePos()
            self.node_created.emit(pos.x(), pos.y())
        super().mouseDoubleClickEvent(event)

    def drawForeground(self, painter: QPainter | None, rect: QRectF):
        if painter is None: return
        super().drawForeground(painter, rect)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent | None):
        if event is None: return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent | None):
        if event is None: return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent | None):
        if event is None: return
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        item = self.itemAt(event.scenePos(), self.views()[0].transform() if self.views() else None)
        menu = QMenu()
        if isinstance(item, StoryNodeItem):
            act_connect = menu.addAction("Conectar con...")
            act_del = menu.addAction("Eliminar Bloque")
            res = menu.exec(event.screenPos())
            if res == act_del:
                self.node_deleted.emit(item.block.id)
            elif res == act_connect:
                self.request_full_connection.emit(item.block.id)
        elif isinstance(item, StoryArcItem):
            act_del = menu.addAction("Eliminar Conexión")
            res = menu.exec(event.screenPos())
            if res == act_del:
                self.arc_deleted.emit(item.arc.id)
        else:
            act_new = menu.addAction("Nuevo Bloque Aquí")
            res = menu.exec(event.screenPos())
            if res == act_new:
                pos = event.scenePos()
                self.node_created.emit(pos.x(), pos.y())
