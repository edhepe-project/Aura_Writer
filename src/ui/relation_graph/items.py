"""
Módulo de Elementos Gráficos: Nodos de Personaje, Aristas y Fondo.
"""

import math
from typing import Optional
from PyQt6.QtWidgets import (
    QGraphicsScene, QGraphicsEllipseItem, QGraphicsTextItem,
    QGraphicsPathItem, QGraphicsItem, QGraphicsRectItem,
)
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import (
    QBrush, QPen, QColor, QFont, QPainter,
    QPainterPath, QRadialGradient,
)
from core.models import Character, RELATION_ICONS
from core.theme_manager import ThemeManager
from .models import CharacterMetrics, RELATION_STYLES, get_race, bezier_path


# ── Nodo de Personaje de Alto Rendimiento ──────────────────────────────────

class CharacterNode(QGraphicsEllipseItem):
    """
    Nodo de Personaje ultra optimizado:
    - Dibuja esfera, iniciales, nombre, raza y anillos dentro de un único paint()
    - Cero QGraphicsItems hijos para eliminar overhead de 3500+ nodos
    - Soporta DeviceCoordinateCache / ItemCoordinateCache
    """
    def __init__(self, char: Character, metrics: CharacterMetrics, color: str, x: float, y: float):
        radius = metrics.base_radius
        super().__init__(-radius, -radius, radius * 2, radius * 2)
        self.char_id   = char.id
        self.char_name = char.name or "?"
        self.char_race = get_race(char) or ""
        self.metrics   = metrics
        self._radius   = radius
        self._color_str = color
        self._color    = QColor(color)
        self._tier     = metrics.tier
        self._is_focused = False
        self._is_dimmed = False

        self.setPos(x, y)

        # Habilitar optimizaciones de rendimiento
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setCacheMode(QGraphicsItem.CacheMode.ItemCoordinateCache)
        self.setZValue(10 if self._tier == "core" else (7 if self._tier == "primary" else 5))
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)

        # Precalcular fuentes e iniciales
        self._initials = "".join([part[0].upper() for part in self.char_name.split()[:2]]) if self.char_name else "?"
        fsize = 11 if self._tier == "core" else (9 if self._tier == "primary" else 7)
        self._font_initials = QFont("Segoe UI", fsize, QFont.Weight.Bold)
        
        name_fsize = 10 if self._tier == "core" else (9 if self._tier == "primary" else 8)
        name_weight = QFont.Weight.Bold if self._tier == "core" else QFont.Weight.DemiBold
        self._font_name = QFont("Segoe UI", name_fsize, name_weight)
        self._font_race = QFont("Segoe UI", 8)

        # Tooltip rápido
        parts = [f"{self.char_name}"]
        if self.char_race: parts.append(f"Raza: {self.char_race}")
        if char.role:      parts.append(f"Rol: {char.role}")
        parts.append(f"Apariciones: {metrics.chapters_count} cap. | Conexiones: {metrics.connections_count}")
        if char.description: parts.append(char.description[:120])
        self.setToolTip("\n".join(parts))

        self.edges: list = []

    def boundingRect(self) -> QRectF:
        r = self._radius
        # Bounding box ampliado para contener halo, anillo, nombre y raza
        extra_h = 36 if self.char_race else 24
        extra_w = max(40.0, r + 50.0)
        return QRectF(-extra_w, -r - 16, extra_w * 2, (r * 2) + extra_h + 20)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        
        r = self._radius
        c = self._color
        is_dark = ThemeManager.is_dark()

        # Opacidad reducida si otro nodo está seleccionado
        if self._is_dimmed and not self._is_focused:
            painter.setOpacity(0.20)
        else:
            painter.setOpacity(1.0)

        # 1. Halo exterior para core / primary o cuando está enfocado
        if self._is_focused or self._tier in ("core", "primary"):
            halo_r = r + (16 if self._is_focused else (12 if self._tier == "core" else 7))
            hgrad = QRadialGradient(0, 0, halo_r)
            h1 = QColor(c)
            h1.setAlphaF(0.0)
            h2 = QColor(c)
            h2.setAlphaF(0.40 if self._is_focused else (0.24 if self._tier == "core" else 0.14))
            hgrad.setColorAt(0.55, h1)
            hgrad.setColorAt(0.85, h2)
            hgrad.setColorAt(1.00, h1)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(hgrad))
            painter.drawEllipse(QPointF(0, 0), halo_r, halo_r)

        # 2. Esfera principal con gradiente
        grad = QRadialGradient(-r * 0.35, -r * 0.35, r * 1.35)
        if self._tier == "core":
            grad.setColorAt(0.00, QColor("#ffffff"))
            grad.setColorAt(0.40, c.lighter(155))
            grad.setColorAt(0.80, c)
            grad.setColorAt(1.00, c.darker(135))
        else:
            grad.setColorAt(0.00, c.lighter(150))
            grad.setColorAt(0.60, c)
            grad.setColorAt(1.00, c.darker(150))

        painter.setBrush(QBrush(grad))
        painter.setPen(QPen(c.lighter(140), 1.2))
        painter.drawEllipse(QPointF(0, 0), r, r)

        # 3. Anillo de enfoque / selección
        if self._is_focused:
            ring_r = r + 6
            painter.setPen(QPen(c.lighter(170), 2.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPointF(0, 0), ring_r, ring_r)

        # 4. Iniciales centradas en el nodo
        painter.setFont(self._font_initials)
        painter.setPen(QPen(QColor("#ffffff")))
        painter.drawText(QRectF(-r, -r, r * 2, r * 2), Qt.AlignmentFlag.AlignCenter, self._initials)

        # 5. Nombre debajo del nodo
        painter.setFont(self._font_name)
        name_col = QColor("#ffffff" if is_dark else "#111118")
        painter.setPen(QPen(name_col))
        
        # Ancho holgado para el texto
        text_w = max(140.0, r * 3)
        name_rect = QRectF(-text_w / 2, r + 3, text_w, 18)
        painter.drawText(name_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, self.char_name)

        # 6. Raza / Subetiqueta
        if self.char_race:
            painter.setFont(self._font_race)
            tag_col = c.lighter(165) if is_dark else c.darker(140)
            tag_col.setAlphaF(0.95)
            painter.setPen(QPen(tag_col))
            race_rect = QRectF(-text_w / 2, r + 18, text_w, 16)
            painter.drawText(race_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, self.char_race)

    def set_focused_ring(self, on: bool, dim_others: bool = False):
        self._is_focused = on
        self._is_dimmed = dim_others
        self.update()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            for edge in self.edges:
                edge.update_position()
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        scene = self.scene()
        if scene and hasattr(scene, "_node_clicked"):
            scene._node_clicked(self.char_id)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        scene = self.scene()
        if scene and hasattr(scene, "_node_double_clicked"):
            scene._node_double_clicked(self.char_id)
        super().mouseDoubleClickEvent(event)


# ── Arista de Relación Fina y Elegante (Estilo Órbita) ───────────────────────

class RelationEdge(QGraphicsPathItem):
    """
    Arista optimizada:
    - Trazo de bezier curvo de alto rendimiento
    - Dibuja glow dinámicamente sin duplicar items cuando está inactivo
    """
    def __init__(self, source: CharacterNode, target: CharacterNode,
                 label: str, intensity: int, relation_type: str = "otro",
                 curvature: float = 0.16):
        super().__init__()
        self.source = source
        self.target = target
        self.relation_type = relation_type
        self.label_text = label
        self._curvature = curvature
        self._intensity = intensity

        style = RELATION_STYLES.get(relation_type, RELATION_STYLES["otro"])
        self._style = style
        self._base_color = QColor(style["color"])
        
        # Grosor base ultra sutil (estilo órbita estelar)
        self._idle_width = 0.85
        self._active_width = max(1.8, min(2.8, style["width"] + (intensity - 3) * 0.18))

        pen = QPen(self._base_color, self._idle_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        if style["dash"]:
            pen.setStyle(Qt.PenStyle.CustomDashLine)
            pen.setDashPattern(style["dash"])
        self.setPen(pen)
        self.setZValue(2)
        self.setOpacity(0.35)

        # Glow exterior ligero
        self._glow1 = QGraphicsPathItem()
        g1 = QColor(style["glow"])
        self._glow1.setPen(QPen(g1, self._active_width * 3.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        self._glow1.setZValue(1)
        self._glow1.setOpacity(0.0)

        # Etiqueta opcional
        self._label_item: Optional[QGraphicsTextItem] = None
        self._label_bg:   Optional[QGraphicsRectItem] = None
        if label:
            icon = RELATION_ICONS.get(relation_type, "")
            display = f" {icon} {label} " if icon else f" {label} "
            self._label_item = QGraphicsTextItem(display)
            tc = QColor(style["color"]).lighter(140) if ThemeManager.is_dark() else QColor(style["color"]).darker(150)
            self._label_item.setDefaultTextColor(tc)
            self._label_item.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
            self._label_item.setZValue(6)
            self._label_item.setOpacity(0.35)

            self._label_bg = QGraphicsRectItem()
            bg = QColor("#1c1c1e") if ThemeManager.is_dark() else QColor("#faf7f3")
            bg.setAlphaF(0.92)
            self._label_bg.setBrush(QBrush(bg))
            bc = QColor(style["color"])
            bc.setAlphaF(0.40)
            self._label_bg.setPen(QPen(bc, 1))
            self._label_bg.setZValue(5)
            self._label_bg.setOpacity(0.35)

        source.edges.append(self)
        target.edges.append(self)
        self.update_position()

    def add_to_scene(self, scene: QGraphicsScene):
        scene.addItem(self._glow1)
        if self._label_bg:
            scene.addItem(self._label_bg)
        if self._label_item:
            scene.addItem(self._label_item)

    def update_position(self):
        p1 = self.source.scenePos()
        p2 = self.target.scenePos()
        path = bezier_path(p1, p2, self._curvature)
        self.setPath(path)
        self._glow1.setPath(path)
        if self._label_item and self._label_bg:
            mid = path.pointAtPercent(0.5)
            br = self._label_item.boundingRect()
            self._label_item.setPos(mid.x() - br.width() / 2, mid.y() - br.height() / 2)
            self._label_bg.setRect(
                mid.x() - br.width() / 2 - 2, mid.y() - br.height() / 2 - 1,
                br.width() + 4, br.height() + 2
            )

    def set_active_focus(self, active: bool, dim_others: bool = False):
        pen = QPen(self.pen())
        if active:
            pen.setWidthF(self._active_width)
            self.setPen(pen)
            self.setOpacity(1.0)
            self.setZValue(7)
            self._glow1.setOpacity(0.45)
            self._glow1.setZValue(6)
            if self._label_item:
                self._label_item.setVisible(True)
                self._label_item.setOpacity(1.0)
            if self._label_bg:
                self._label_bg.setVisible(True)
                self._label_bg.setOpacity(1.0)
        elif dim_others:
            pen.setWidthF(self._idle_width)
            self.setPen(pen)
            self.setOpacity(0.04)
            self.setZValue(1)
            self._glow1.setOpacity(0.0)
            if self._label_item:  self._label_item.setOpacity(0.02)
            if self._label_bg:    self._label_bg.setOpacity(0.02)
        else:
            pen.setWidthF(self._idle_width)
            self.setPen(pen)
            self.setOpacity(0.35)
            self.setZValue(2)
            self._glow1.setOpacity(0.0)
            if self._label_item:  self._label_item.setOpacity(0.35)
            if self._label_bg:    self._label_bg.setOpacity(0.35)


# ── Fondo Espacioso y Limpio (Optimizador de Pintura) ─────────────────────────

class CleanBackground(QGraphicsRectItem):
    def __init__(self, rect: QRectF, is_dark: bool):
        super().__init__(rect)
        self._is_dark = is_dark
        self.setZValue(-20)
        self.setPen(QPen(Qt.PenStyle.NoPen))
        self.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemClipsToShape, False)

    def paint(self, painter, option, widget=None):
        """Pinta puntos sutiles únicamente dentro del área expuesta / visible."""
        exposed = option.exposedRect if hasattr(option, "exposedRect") else self.rect()
        if exposed.isEmpty():
            return
            
        dot_col = QColor(255, 255, 255, 14) if self._is_dark else QColor(0, 0, 0, 10)
        painter.setBrush(QBrush(dot_col))
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        step = 40
        
        start_x = math.floor(exposed.left() / step) * step
        end_x   = math.ceil(exposed.right() / step) * step
        start_y = math.floor(exposed.top() / step) * step
        end_y   = math.ceil(exposed.bottom() / step) * step
        
        x = start_x
        while x <= end_x:
            y = start_y
            while y <= end_y:
                painter.drawEllipse(QPointF(x, y), 0.9, 0.9)
                y += step
            x += step
