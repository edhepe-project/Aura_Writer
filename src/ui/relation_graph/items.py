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
    QPainterPath, QRadialGradient, QPolygonF,
)
from core.models import Character, RELATION_ICONS
from core.theme_manager import ThemeManager
from .models import CharacterMetrics, RELATION_STYLES, get_race, bezier_path


# ── Generador de Formas Geométricas Precalculadas ──────────────────────────

_SHAPE_SIDES = {
    "triangle": 3,
    "diamond": 4,
    "pentagon": 5,
    "hexagon": 6,
    "heptagon": 7,
    "octagon": 8,
    "decagon": 10,
    "dodecagon": 12,
    "icosagon": 20,
}


def _get_polygon(shape: str, radius: float) -> QPolygonF:
    """Genera polígonos regulares centrados en (0,0) con vértice superior orientado hacia arriba."""
    if shape == "diamond":
        w = radius * 0.90
        h = radius * 1.15
        return QPolygonF([
            QPointF(0, -h),
            QPointF(w, 0),
            QPointF(0, h),
            QPointF(-w, 0),
        ])

    sides = _SHAPE_SIDES.get(shape, 3)
    offset = -math.pi / 2
    return QPolygonF([
        QPointF(radius * math.cos(offset + i * 2.0 * math.pi / sides),
                radius * math.sin(offset + i * 2.0 * math.pi / sides))
        for i in range(sides)
    ])



# ── Nodo de Personaje de Alto Rendimiento con Mutación Geométrica ──────────

class CharacterNode(QGraphicsEllipseItem):
    """
    Nodo de Personaje ultra optimizado:
    - Renderiza formas geométricas mutables (Triángulo, Rombo, Pentágono, Hexágono, Círculo)
    - Dibuja figura, iniciales, nombre, raza y halos dentro de un único paint()
    - Cero QGraphicsItems hijos para eliminar overhead
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
        self._shape    = getattr(metrics, "shape", "circle")
        self._is_focused = False
        self._is_dimmed = False

        self.setPos(x, y)

        # Rendimiento: nodos fijos (sin arrastre) para eliminar callbacks continuos
        # El layout fisico ya calcula la posicion optima de cada nodo.
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, False)
        self.setCacheMode(QGraphicsItem.CacheMode.NoCache)
        self.setZValue(10 if self._tier == "core" else (7 if self._tier == "primary" else 5))
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)

        # Precalcular fuentes e iniciales con jerarquía contundente
        self._initials = "".join([part[0].upper() for part in self.char_name.split()[:2]]) if self.char_name else "?"
        fsize = 14 if self._tier == "core" else (10 if self._tier == "primary" else 8)
        self._font_initials = QFont("Segoe UI", fsize, QFont.Weight.Bold)
        
        name_fsize = 11 if self._tier == "core" else (9 if self._tier == "primary" else 8)
        name_weight = QFont.Weight.Bold if self._tier in ("core", "primary") else QFont.Weight.Normal
        self._font_name = QFont("Segoe UI", name_fsize, name_weight)
        self._font_race = QFont("Segoe UI", 8)
        self._font_name_large = QFont("Segoe UI", 12 if self._tier == "core" else 10, QFont.Weight.Bold)

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
        # Bounding box ampliado para contener aura difusa, anillo, nombre y raza
        extra_h = 38 if self.char_race else 26
        extra_w = max(45.0, r + 65.0)
        return QRectF(-extra_w, -r - 30, extra_w * 2, (r * 2) + extra_h + 36)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        
        r = self._radius
        c = self._color
        is_dark = ThemeManager.is_dark()
        lod = option.levelOfDetailFromTransform(painter.worldTransform()) if hasattr(option, "levelOfDetailFromTransform") else 1.0

        # Opacidad reducida si otro nodo está seleccionado
        if self._is_dimmed and not self._is_focused:
            painter.setOpacity(0.12)
        else:
            painter.setOpacity(1.0)

        shape = self._shape

        # 1. Aura Luminosa Etérea (Glow difuso suave escalonado por importancia)
        if lod >= 0.15:
            if self._is_focused:
                aura_spread = r * 0.75 + 16.0
                aura_alpha = 0.55
            elif shape == "circle":
                aura_spread = r * 0.65 + 14.0
                aura_alpha = 0.45
            elif self._tier == "core":
                aura_spread = r * 0.50 + 10.0
                aura_alpha = 0.35
            elif self._tier == "primary":
                aura_spread = r * 0.40 + 6.0
                aura_alpha = 0.22
            else:
                aura_spread = r * 0.30 + 4.0
                aura_alpha = 0.14

            aura_r = r + aura_spread
            hgrad = QRadialGradient(0, 0, aura_r)
            
            c_inner = QColor(c)
            c_inner.setAlphaF(aura_alpha)
            c_mid = QColor(c)
            c_mid.setAlphaF(aura_alpha * 0.40)
            c_outer = QColor(c)
            c_outer.setAlphaF(0.0)

            inner_stop = max(0.20, min(0.70, (r - 2.0) / aura_r))
            hgrad.setColorAt(0.00, c_inner)
            hgrad.setColorAt(inner_stop, c_inner)
            hgrad.setColorAt((inner_stop + 1.0) / 2.0, c_mid)
            hgrad.setColorAt(1.00, c_outer)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(hgrad))
            if shape == "circle":
                painter.drawEllipse(QPointF(0, 0), aura_r, aura_r)
            else:
                painter.drawPolygon(_get_polygon(shape, aura_r))

        # 2. Cuerpo de la figura principal con gradiente tipo gema
        grad = QRadialGradient(-r * 0.35, -r * 0.35, r * 1.35)
        if self._tier == "core":
            grad.setColorAt(0.00, QColor("#ffffff"))
            grad.setColorAt(0.35, c.lighter(160))
            grad.setColorAt(0.75, c)
            grad.setColorAt(1.00, c.darker(140))
        else:
            grad.setColorAt(0.00, c.lighter(140))
            grad.setColorAt(0.60, c)
            grad.setColorAt(1.00, c.darker(150))

        painter.setBrush(QBrush(grad))
        border_pen = QPen(c.lighter(160) if self._tier == "core" else c.lighter(130), 2.0 if self._tier == "core" else 1.2)
        painter.setPen(border_pen)
        if shape == "circle":
            painter.drawEllipse(QPointF(0, 0), r, r)
        else:
            painter.drawPolygon(_get_polygon(shape, r))

        # 3. Anillo de enfoque / selección
        if self._is_focused:
            ring_r = r + 7
            painter.setPen(QPen(c.lighter(180), 3.0))
            painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            if shape == "circle":
                painter.drawEllipse(QPointF(0, 0), ring_r, ring_r)
            else:
                painter.drawPolygon(_get_polygon(shape, ring_r))

        # 4. Iniciales centradas en el nodo
        should_draw_initials = (self._tier == "core") or (self._tier == "primary" and lod >= 0.30) or (lod >= 0.50) or self._is_focused
        if should_draw_initials:
            painter.setFont(self._font_initials)
            painter.setPen(QPen(QColor("#ffffff")))
            painter.drawText(QRectF(-r, -r, r * 2, r * 2), Qt.AlignmentFlag.AlignCenter, self._initials)

        # 5. Nombre del personaje — Claramente legible sin importar el zoom
        show_name = (self._tier in ("core", "primary")) or self._is_focused or (lod >= 0.35 and not self._is_dimmed) or (lod >= 0.70)
        if show_name:
            font_to_use = self._font_name_large if (lod < 0.40 or self._is_focused) else self._font_name
            painter.setFont(font_to_use)
            name_col = QColor("#ffffff" if is_dark else "#111118")
            if self._is_dimmed and not self._is_focused:
                name_col.setAlphaF(0.35)
            painter.setPen(QPen(name_col))
            
            text_w = max(240.0, r * 4.5)
            name_rect = QRectF(-text_w / 2, r + 5, text_w, 24)
            painter.drawText(name_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, self.char_name)

            # 6. Raza / Subetiqueta
            if self.char_race and (self._is_focused or (lod >= 0.45 and self._tier in ("core", "primary")) or (lod >= 0.80)):
                painter.setFont(self._font_race)
                tag_col = c.lighter(165) if is_dark else c.darker(140)
                tag_col.setAlphaF(0.90)
                painter.setPen(QPen(tag_col))
                race_rect = QRectF(-text_w / 2, r + 24, text_w, 16)
                painter.drawText(race_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, self.char_race)

    def set_focused_ring(self, on: bool, dim_others: bool = False):
        self._is_focused = on
        self._is_dimmed = dim_others
        self.update()

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
    Arista de relación ultra-optimizada:
    - Trazo de bezier curvo de alto rendimiento en un único QGraphicsItem
    - Renderiza su propio glow y etiqueta en paint() sin crear miles de QGraphicsTextItems
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
        self._glow_color = QColor(style["glow"])
        
        self._idle_width = 0.85
        self._active_width = max(2.2, min(3.4, style["width"] + (intensity - 3) * 0.25))
        self._is_active = False
        self._is_dimmed = False

        pen = QPen(self._base_color, self._idle_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        if style["dash"]:
            pen.setStyle(Qt.PenStyle.CustomDashLine)
            pen.setDashPattern(style["dash"])
        self.setPen(pen)
        self.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self.setZValue(2)
        # Ocultas en estado global/reposo para evitar el efecto telaraña y maximizar FPS
        self.setVisible(False)

        # Precalcular etiqueta
        self._display_label = ""
        if label:
            icon = RELATION_ICONS.get(relation_type, "")
            self._display_label = f"{icon} {label}" if icon else label
        
        self._label_font = QFont("Segoe UI", 9, QFont.Weight.Bold)
        self._mid_point = QPointF(0, 0)

        source.edges.append(self)
        target.edges.append(self)
        self.update_position()

    def boundingRect(self) -> QRectF:
        br = super().boundingRect()
        if self._is_active or self._display_label:
            return br.adjusted(-24, -24, 24, 24)
        return br

    def update_position(self):
        p1 = self.source.scenePos()
        p2 = self.target.scenePos()
        r1 = getattr(self.source, "_radius", 0.0)
        r2 = getattr(self.target, "_radius", 0.0)
        path = bezier_path(p1, p2, self._curvature, r1=r1, r2=r2)
        self.setPath(path)
        self._mid_point = path.pointAtPercent(0.5)

    def set_active_focus(self, active: bool, dim_others: bool = False):
        self._is_active = active
        self._is_dimmed = dim_others
        pen = QPen(self.pen())
        if active:
            pen.setWidthF(self._active_width)
            self.setPen(pen)
            self.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            self.setOpacity(1.0)
            self.setZValue(8)
            self.setVisible(True)
        elif dim_others:
            pen.setWidthF(self._idle_width)
            self.setPen(pen)
            self.setOpacity(0.18)
            self.setZValue(2)
            self.setVisible(True)
        else:
            # Estado normal reposo
            pen.setWidthF(self._idle_width)
            self.setPen(pen)
            self.setOpacity(0.75)
            self.setZValue(3)
            self.setVisible(True)
        self.update()

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        path = self.path()
        if path.isEmpty():
            return

        # NUNCA rellenar la curva abierta (evita triángulos verdes gigantes)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # 1. Glow exterior fino de la relación seleccionada (solo si está activa)
        if self._is_active:
            glow_pen = QPen(self._glow_color, self._active_width * 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.save()
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(glow_pen)
            painter.setOpacity(0.40)
            painter.drawPath(path)
            painter.restore()

        # 2. Línea de relación nítida
        line_pen = QPen(self.pen())
        painter.setPen(line_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)

        # 3. Etiqueta con el tipo de relación sobre la línea (si está activa o en reposo)
        display_txt = self._display_label or self.relation_type.capitalize()
        if display_txt and not self._is_dimmed:
            is_dark = ThemeManager.is_dark()
            painter.save()
            painter.setFont(self._label_font)
            
            fm = painter.fontMetrics()
            tw = fm.horizontalAdvance(display_txt)
            th = fm.height()
            
            mx, my = self._mid_point.x(), self._mid_point.y()
            rect = QRectF(mx - tw / 2 - 6, my - th / 2 - 3, tw + 12, th + 6)
            
            bg_col = QColor("#1c1c1e" if is_dark else "#faf7f3")
            bg_col.setAlphaF(0.96 if self._is_active else 0.85)
            border_col = QColor(self._base_color)
            border_col.setAlphaF(0.90 if self._is_active else 0.50)
            
            painter.setBrush(QBrush(bg_col))
            painter.setPen(QPen(border_col, 1.4 if self._is_active else 1.0))
            painter.drawRoundedRect(rect, 4, 4)
            
            txt_col = self._base_color.lighter(160) if is_dark else self._base_color.darker(160)
            painter.setPen(QPen(txt_col))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, display_txt)
            painter.restore()


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
