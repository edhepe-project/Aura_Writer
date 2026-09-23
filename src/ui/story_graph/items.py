"""
Elementos gráficos interactivos para el Grafo del Cronograma Narrativo.
StoryNodeItem (nodo del evento) y StoryArcItem (flecha causal dirigida).
"""

import math
from PyQt6.QtWidgets import (
    QGraphicsItem, QGraphicsRectItem, QGraphicsPathItem, QGraphicsEllipseItem,
    QStyleOptionGraphicsItem, QWidget
)
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPainterPath, QPolygonF, QFontMetrics
)
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal as Signal, QObject

from core.models import StoryBlock, StoryArc
from ui.story_graph.models import STATUS_CONFIG, TONE_CONFIG, ARC_TYPE_CONFIG


class StoryNodeSignals(QObject):
    moved = Signal(str, float, float)     # block_id, x, y
    selected = Signal(str)               # block_id
    connect_requested = Signal(str)       # from_block_id


from PyQt6.QtWidgets import QGraphicsDropShadowEffect

class StoryNodeItem(QGraphicsRectItem):
    """Nodo gráfico que representa un StoryBlock (Tarjeta Premium)."""

    NODE_WIDTH = 250.0
    MIN_HEIGHT = 130.0

    def __init__(self, block: StoryBlock, chapter_title: str = ""):
        super().__init__()
        self.block = block
        self.chapter_title = chapter_title  # Título del capítulo vinculado (si existe)
        self.signals = StoryNodeSignals()
        self._hovered = False
        
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)
        
        
        # Altura dinámica: si tiene capítulo vinculado, se añade una fila extra
        self._has_chapter = bool(chapter_title and block.status == "escrito")
        self.setRect(0, 0, self.NODE_WIDTH, self.MIN_HEIGHT + (20 if self._has_chapter else 0))
        self.setPos(block.x, block.y)

        # Efecto de sombra premium
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 180))
        self.setGraphicsEffect(shadow)

    def update_data(self, block: StoryBlock, chapter_title: str = ""):
        self.block = block
        self.chapter_title = chapter_title
        self._has_chapter = bool(chapter_title and block.status == "escrito")
        self.setRect(0, 0, self.NODE_WIDTH, self.MIN_HEIGHT + (20 if self._has_chapter else 0))
        self.update()

    def boundingRect(self) -> QRectF:
        # Añadir margen para el borde de selección y sombra
        return self.rect().adjusted(-5.0, -5.0, 5.0, 5.0)

    def hoverEnterEvent(self, event):
        self._hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            pos = self.pos()
            self.block.x = pos.x()
            self.block.y = pos.y()
            self.signals.moved.emit(self.block.id, pos.x(), pos.y())
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            if value:
                self.signals.selected.emit(self.block.id)
        return super().itemChange(change, value)

    def get_output_port_pos(self) -> QPointF:
        """Punto de origen para crear conexiones (borde derecho central)."""
        r = self.rect()
        return self.mapToScene(QPointF(r.width(), r.height() / 2.0))

    def get_input_port_pos(self) -> QPointF:
        """Punto de destino de conexiones (borde izquierdo central)."""
        r = self.rect()
        return self.mapToScene(QPointF(0, r.height() / 2.0))

    def paint(self, painter: QPainter | None, option: QStyleOptionGraphicsItem | None, widget: QWidget | None = None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        lod = option.levelOfDetailFromTransform(painter.worldTransform())

        # Config de estado y tono
        cfg = STATUS_CONFIG.get(self.block.status, STATUS_CONFIG["idea"])
        tone_cfg = TONE_CONFIG.get(self.block.tone, TONE_CONFIG["neutro"])
        
        bg_col = QColor(cfg["bg_color"])
        border_col = QColor(tone_cfg["color"]) # El borde indica el tono

        if self.isSelected():
            border_col = QColor("#ffffff")
            pen_width = 2.5
        elif self._hovered:
            border_col = border_col.lighter(130)
            pen_width = 1.5
        else:
            border_col = QColor("#3a3a3c") # Borde sutil por defecto
            pen_width = 1.0

        r = self.rect()

        if lod < 0.25:
            # Nivel 3: Vista Estructural (Guion horizontal delgado + círculo)
            dash_height = 8.0
            dash_rect = QRectF(r.x(), r.y() + (r.height() - dash_height) / 2.0, r.width(), dash_height)
            
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(tone_cfg["color"]).darker(150)))
            
            path = QPainterPath()
            path.addRoundedRect(dash_rect, 4.0, 4.0)
            painter.drawPath(path)
            
            # Dibujamos un círculo central del color del estado
            painter.setBrush(QBrush(bg_col))
            painter.setPen(QPen(QColor(tone_cfg["color"]), 2.0))
            center_x = r.x() + r.width() / 2.0
            center_y = r.y() + r.height() / 2.0
            painter.drawEllipse(QPointF(center_x, center_y), 16, 16)
            return

        elif lod < 0.6:
            # Nivel 2: Píldora (Solo Título)
            pill_height = 40.0
            pill_rect = QRectF(r.x(), r.y() + (r.height() - pill_height) / 2.0, r.width(), pill_height)
            
            from PyQt6.QtGui import QLinearGradient
            grad = QLinearGradient(0, pill_rect.y(), 0, pill_rect.bottom())
            grad.setColorAt(0.0, bg_col.lighter(110))
            grad.setColorAt(1.0, bg_col.darker(120))

            path = QPainterPath()
            path.addRoundedRect(pill_rect, 12.0, 12.0)

            painter.setPen(QPen(border_col, pen_width))
            painter.setBrush(QBrush(grad))
            painter.drawPath(path)

            painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            painter.setPen(QColor(cfg["text_color"]))
            
            header_text = f"{cfg['badge']} {self.block.title}"
            metrics = QFontMetrics(painter.font())
            elided_title = metrics.elidedText(header_text, Qt.TextElideMode.ElideRight, int(pill_rect.width() - 28))
            painter.drawText(QRectF(pill_rect.x() + 14, pill_rect.y(), pill_rect.width() - 28, pill_rect.height()), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_title)
            return

        # Nivel 1: Tarjeta Premium Completa
        from PyQt6.QtGui import QLinearGradient
        grad = QLinearGradient(0, 0, 0, self.MIN_HEIGHT)
        grad.setColorAt(0.0, bg_col.lighter(110))
        grad.setColorAt(1.0, bg_col.darker(120))

        path = QPainterPath()
        path.addRoundedRect(r, 12.0, 12.0)

        painter.setPen(QPen(border_col, pen_width))
        painter.setBrush(QBrush(grad))
        painter.drawPath(path)

        # 1. Cabecera (Badge estado + Título)
        painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        painter.setPen(QColor(cfg["text_color"]))
        
        header_text = f"{cfg['badge']} {self.block.title}"
        metrics = QFontMetrics(painter.font())
        elided_title = metrics.elidedText(header_text, Qt.TextElideMode.ElideRight, int(r.width() - 20))
        painter.drawText(QRectF(14, 10, r.width() - 28, 24), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_title)

        # Línea divisoria suave
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1.0))
        painter.drawLine(QPointF(14, 38), QPointF(r.width() - 14, 38))

        # 2. Sinopsis
        painter.setFont(QFont("Segoe UI", 9))
        painter.setPen(QColor("#d1d1d6"))
        synopsis_text = self.block.synopsis if self.block.synopsis else "Sin sinopsis detallada..."
        painter.drawText(QRectF(14, 46, r.width() - 28, 50), Qt.TextFlag.TextWordWrap, synopsis_text)

        # 3. Footer: Tono y Temas
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(tone_cfg["color"])))
        painter.drawEllipse(QPointF(20, r.height() - 16), 4, 4)

        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        painter.setPen(QColor("#a1a1a6"))
        painter.drawText(QRectF(30, r.height() - 24, 100, 16), Qt.AlignmentFlag.AlignVCenter, tone_cfg["label"].upper())

        # Temas contador
        if self.block.themes:
            tags_text = " • ".join(self.block.themes[:2])
            if len(self.block.themes) > 2:
                tags_text += " ..."
            painter.setFont(QFont("Segoe UI", 8))
            painter.setPen(QColor("#8e8e93"))
            painter.drawText(QRectF(120, r.height() - (44 if self._has_chapter else 24), r.width() - 134, 16), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, tags_text)

        # 4. Capítulo vinculado (solo si escrito + chapter asignado)
        if self._has_chapter:
            chapter_row_y = r.height() - 22

            # Fondo de la fila de capítulo (levemente diferente)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(255, 214, 10, 25)))
            chapter_bg = QPainterPath()
            chapter_bg.addRoundedRect(QRectF(0, chapter_row_y - 4, r.width(), 26), 0, 0)
            painter.drawPath(chapter_bg)

            # Icono + texto
            painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            painter.setPen(QColor("#ffd60a"))
            metrics = QFontMetrics(painter.font())
            elided_ch = metrics.elidedText(f"📖 {self.chapter_title}", Qt.TextElideMode.ElideRight, int(r.width() - 20))
            painter.drawText(QRectF(12, chapter_row_y, r.width() - 24, 18), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, elided_ch)

            # Indicador de "doble clic para ir"
            painter.setFont(QFont("Segoe UI", 7))
            painter.setPen(QColor("#8e8e93"))
            painter.drawText(QRectF(0, chapter_row_y, r.width() - 10, 18), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, "↩ doble clic")


class StoryArcItem(QGraphicsPathItem):
    """Línea de conexión orientada (flecha) entre dos StoryNodeItem."""

    def __init__(self, arc: StoryArc, source_item: StoryNodeItem, target_item: StoryNodeItem):
        super().__init__()
        self.arc = arc
        self.source_item = source_item
        self.target_item = target_item

        self.setZValue(-1)  # Detrás de los nodos
        self.setAcceptHoverEvents(True)
        self._hovered = False
        self.update_path()

    def update_path(self):
        p1 = self.source_item.get_output_port_pos()
        p2 = self.target_item.get_input_port_pos()

        # Usar Curva de Bézier Cúbica Horizontal (Estilo Node Editor)
        # Esto genera la forma de "S" suave en lugar de una comba de saltar.
        dx = abs(p2.x() - p1.x()) * 0.5
        # Si el nodo destino está a la izquierda (hacia atrás), forzamos un loop visual más pronunciado
        if p2.x() < p1.x():
            dx = max(dx, 80.0)
        else:
            dx = max(dx, 40.0)

        ctrl1 = QPointF(p1.x() + dx, p1.y())
        ctrl2 = QPointF(p2.x() - dx, p2.y())

        self.curve_path = QPainterPath()
        self.curve_path.moveTo(p1)
        self.curve_path.cubicTo(ctrl1, ctrl2, p2)
        
        self.arrow_head = QPolygonF()

        if not self.curve_path.isEmpty() and p1 != p2:
            # La tangente de la curva en el punto p2 (t=1) viene dada por el vector de ctrl2 a p2
            angle = math.atan2(p2.y() - ctrl2.y(), p2.x() - ctrl2.x())
            
            arrow_size = 10.0
            arrow_p1 = QPointF(
                p2.x() - arrow_size * math.cos(angle - math.pi / 6),
                p2.y() - arrow_size * math.sin(angle - math.pi / 6)
            )
            arrow_p2 = QPointF(
                p2.x() - arrow_size * math.cos(angle + math.pi / 6),
                p2.y() - arrow_size * math.sin(angle + math.pi / 6)
            )
            
            self.arrow_head = QPolygonF([p2, arrow_p1, arrow_p2])
            
            full_path = QPainterPath(self.curve_path)
            full_path.addPolygon(self.arrow_head)
            self.setPath(full_path)

    def paint(self, painter: QPainter | None, option: QStyleOptionGraphicsItem | None, widget: QWidget | None = None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cfg = ARC_TYPE_CONFIG.get(self.arc.arc_type, ARC_TYPE_CONFIG["main"])
        col = QColor(cfg["color"])
        
        # Hacemos las líneas un poco más gruesas para que luzcan premium
        base_width = cfg["width"] + 1.0
        
        if self._hovered:
            col = QColor("#ffffff")
            width = base_width + 1.5
        else:
            width = base_width

        pen = QPen(col, width)
        # Suavizar las uniones de las líneas
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        
        if cfg["style"] == "dash":
            pen.setStyle(Qt.PenStyle.DashLine)
        elif cfg["style"] == "dot":
            pen.setStyle(Qt.PenStyle.DotLine)
        elif cfg["style"] == "dashdot":
            pen.setStyle(Qt.PenStyle.DashDotLine)

        # Efecto de Brillo/Sombra Suave detrás de la línea (solo si no es punteada y no se superpone feo)
        if cfg["style"] == "solid" and not self._hovered:
            glow_pen = QPen(QColor(col.red(), col.green(), col.blue(), 40), width + 4)
            glow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(glow_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(self.curve_path)

        # Línea Principal
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(self.curve_path)
        
        # Punta de Flecha
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(col))
        if not self.arrow_head.isEmpty():
            painter.drawPolygon(self.arrow_head)

    def hoverEnterEvent(self, event):
        self._hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._hovered = False
        self.update()
        super().hoverLeaveEvent(event)
