"""
items.py — Items gráficos para el Grafo de Lugares (Nodos y Aristas).
"""
from __future__ import annotations

import math
from typing import Optional

from PyQt6.QtWidgets import (
    QGraphicsItem, QGraphicsEllipseItem, QGraphicsPathItem
)
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QCursor,
    QPainterPath, QRadialGradient
)

from core.models import Place, PlaceLink, PLACE_ICONS
from .models import PLACE_CATEGORY_COLORS, CONNECTION_STYLES, CATEGORY_TIERS, TIER_NODE_RADIUS


def _bezier_path(p1: QPointF, p2: QPointF, curvature: float = 0.08,
                 r1: float = 0.0, r2: float = 0.0) -> QPainterPath:
    """
    Curva Bézier cuadrática sutil y elegante entre dos puntos.
    La deflexión perpendicular está acotada para evitar arcos desmedidos.
    """
    dx = p2.x() - p1.x()
    dy = p2.y() - p1.y()
    dist = math.hypot(dx, dy)
    if dist < 1.0:
        return QPainterPath()

    ux, uy = dx / dist, dy / dist
    sp = QPointF(p1.x() + ux * r1, p1.y() + uy * r1)
    ep = QPointF(p2.x() - ux * r2, p2.y() - uy * r2)

    offset = min(max(dist * curvature, -25.0), 25.0)
    perp_x = -uy * offset
    perp_y =  ux * offset
    mid = QPointF((sp.x() + ep.x()) / 2 + perp_x,
                  (sp.y() + ep.y()) / 2 + perp_y)
    
    path = QPainterPath(sp)
    path.quadTo(mid, ep)
    return path


class PlaceNodeItem(QGraphicsEllipseItem):
    """
    Nodo gráfico de Lugar con estilo gema luminosa y escala astronómica por Tier:
      - Tier 0: Sol / Macro-Mundo (R=42px)
      - Tier 1: Reino / Nación (R=32px)
      - Tier 2: Ciudad / Poblado (R=25px)
      - Tier 3: Puntos de Interés / Lunas (R=18px)
    """

    def __init__(self, place: Place, x: float, y: float,
                 depth: int = 0, child_count: int = 0, parent=None):
        self.tier = CATEGORY_TIERS.get(place.category, 3)
        radius = TIER_NODE_RADIUS.get(self.tier, max(18.0, 34.0 - depth * 5.0))

        super().__init__(-radius, -radius, radius * 2, radius * 2, parent)
        self.place = place
        self.radius = radius
        self.depth = depth
        self.child_count = child_count
        self._color_str = PLACE_CATEGORY_COLORS.get(place.category, "#8e8e93")
        self._color = QColor(self._color_str)
        self._is_focused = False
        self._is_dimmed = False
        self.edges: list[PlaceLinkItem] = []

        self.setPos(x, y)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setZValue(12 if self.tier <= 1 else (8 if self.tier == 2 else 5))

        # Tooltip informativo
        parts = [f"📍 {place.name}", f"Categoría: {place.category}"]
        if place.climate_atmosphere:
            parts.append(f"Clima: {place.climate_atmosphere[:80]}")
        if place.lore_history:
            parts.append(f"Lore: {place.lore_history[:100]}")
        if child_count:
            parts.append(f"Contiene: {child_count} lugar(es)")
        self.setToolTip("\n".join(parts))

        # Tipografía adaptada al tamaño del astro
        self._font_icon = QFont("Segoe UI Emoji", int(radius * 0.52))
        self._font_name = QFont("Segoe UI", 10 if self.tier <= 1 else 9,
                                QFont.Weight.Bold if self.tier <= 1 else QFont.Weight.Normal)
        self._font_badge = QFont("Segoe UI", 8, QFont.Weight.Bold)
        self._icon_str = PLACE_ICONS.get(place.category, "📍")

    def boundingRect(self) -> QRectF:
        r = self.radius
        return QRectF(-r - 26, -r - 26, (r + 26) * 2, (r + 26) * 2 + 42)

    def set_focused(self, focused: bool, dimmed: bool = False):
        self._is_focused = focused
        self._is_dimmed = dimmed
        self.setZValue(16 if focused else (12 if self.tier <= 1 else (8 if not dimmed else 4)))
        self.update()

    def paint(self, painter: QPainter | None, option, widget=None):
        if painter is None:
            return
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        r = self.radius
        c = self._color

        # Opacidad según estado de foco
        if self._is_dimmed and not self._is_focused:
            painter.setOpacity(0.15)
        else:
            painter.setOpacity(1.0)

        # 1. Halo difuso / Corona Solar
        aura_mult = 0.85 if self._is_focused else (0.60 if self.tier == 0 else (0.45 if self.tier == 1 else 0.25))
        aura_alpha = 0.60 if self._is_focused else (0.45 if self.tier == 0 else (0.35 if self.tier == 1 else 0.20))
        aura_r = r + r * aura_mult + 10

        hgrad = QRadialGradient(0, 0, aura_r)
        c_inner = QColor(c)
        c_inner.setAlphaF(aura_alpha)
        c_mid = QColor(c)
        c_mid.setAlphaF(aura_alpha * 0.35)
        c_outer = QColor(c)
        c_outer.setAlphaF(0.0)
        inner_stop = max(0.20, min(0.65, (r - 2.0) / aura_r))
        hgrad.setColorAt(0.00, c_inner)
        hgrad.setColorAt(inner_stop, c_inner)
        hgrad.setColorAt((inner_stop + 1.0) / 2.0, c_mid)
        hgrad.setColorAt(1.00, c_outer)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(hgrad))
        painter.drawEllipse(QPointF(0, 0), aura_r, aura_r)

        # 2. Esfera gema con gradiente radial
        grad = QRadialGradient(-r * 0.35, -r * 0.35, r * 1.35)
        if self.tier <= 1:
            grad.setColorAt(0.00, QColor("#ffffff"))
            grad.setColorAt(0.25, c.lighter(165))
            grad.setColorAt(0.70, c)
            grad.setColorAt(1.00, c.darker(150))
        else:
            grad.setColorAt(0.00, c.lighter(145))
            grad.setColorAt(0.60, c)
            grad.setColorAt(1.00, c.darker(155))

        border_pen = QPen(
            c.lighter(170) if self.tier <= 1 else c.lighter(135),
            2.5 if self.tier == 0 else (2.0 if self.tier == 1 else 1.4)
        )
        painter.setPen(border_pen)
        painter.setBrush(QBrush(grad))
        painter.drawEllipse(QPointF(0, 0), r, r)

        # 3. Anillo de selección exterior si está enfocado
        if self._is_focused:
            focus_pen = QPen(QColor("#ffffff"), 2.0)
            painter.setPen(focus_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPointF(0, 0), r + 4.5, r + 4.5)

        # 4. Icono central
        painter.setFont(self._font_icon)
        painter.setPen(QPen(QColor("#ffffff")))
        painter.drawText(QRectF(-r, -r, r * 2, r * 2),
                         Qt.AlignmentFlag.AlignCenter, self._icon_str)

        # 5. Badge numérico de hijos / satélites contenidos
        if self.child_count > 0:
            badge_r = 9.0
            bx = r * 0.65
            by = -r * 0.65
            painter.setPen(QPen(QColor("#ffffff"), 1.5))
            painter.setBrush(QBrush(QColor("#bf5af2")))
            painter.drawEllipse(QPointF(bx, by), badge_r, badge_r)
            painter.setFont(self._font_badge)
            painter.setPen(QPen(QColor("#ffffff")))
            painter.drawText(
                QRectF(bx - badge_r, by - badge_r, badge_r * 2, badge_r * 2),
                Qt.AlignmentFlag.AlignCenter, str(self.child_count)
            )

        # 6. Nombre del lugar debajo del nodo
        show_name = self._is_focused or self.tier <= 1 or not self._is_dimmed
        if show_name:
            name_col = QColor("#f2f2f7")
            if self._is_dimmed and not self._is_focused:
                name_col.setAlphaF(0.35)
            painter.setFont(self._font_name)
            painter.setPen(QPen(name_col))
            text_w = max(220.0, r * 5)
            painter.drawText(
                QRectF(-text_w / 2, r + 6, text_w, 24),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                self.place.name
            )

            # Sub-etiqueta de categoría si está seleccionado
            if self._is_focused:
                sub_col = QColor(c.lighter(160))
                sub_col.setAlphaF(0.92)
                sub_font = QFont("Segoe UI", 8)
                painter.setFont(sub_font)
                painter.setPen(QPen(sub_col))
                painter.drawText(
                    QRectF(-text_w / 2, r + 26, text_w, 16),
                    Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                    self.place.category
                )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            scene = self.scene()
            if scene and hasattr(scene, "_node_clicked"):
                scene._node_clicked(self.place.id)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event:
            scene = self.scene()
            if scene and hasattr(scene, "_node_double_clicked"):
                scene._node_double_clicked(self.place.id)
            event.accept()


class PlaceLinkItem(QGraphicsPathItem):
    """
    Arista de conexión geográfica con arco Bézier suave, glow y foco dinámico.
    """
    def __init__(self, link: PlaceLink, node_a: PlaceNodeItem, node_b: PlaceNodeItem,
                 curvature: float = 0.08):
        super().__init__()
        self.link = link
        self.node_a = node_a
        self.node_b = node_b
        self._curvature = curvature

        conn_type = getattr(link, "connection_type", "otro") or "otro"
        style = CONNECTION_STYLES.get(conn_type, CONNECTION_STYLES["otro"])
        color_hex = (getattr(link, "color", "") or "") or style["color"]
        self._base_color = QColor(color_hex)
        self._glow_color = QColor(style["glow"])
        self._dash = style["dash"]
        self._base_width = style["width"]
        self._is_active = False
        self._is_dimmed = False
        self._label = getattr(link, "label", "") or conn_type

        pen = QPen(self._base_color, self._base_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        if self._dash:
            pen.setStyle(Qt.PenStyle.CustomDashLine)
            pen.setDashPattern(self._dash)
        self.setPen(pen)
        self.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self.setZValue(3)
        self.setOpacity(0.40)

        self._label_font = QFont("Segoe UI", 8, QFont.Weight.Bold
                                 if conn_type == "contiene" else QFont.Weight.Normal)
        self._update_path()

        node_a.edges.append(self)
        node_b.edges.append(self)

    def _update_path(self):
        p1 = self.node_a.pos()
        p2 = self.node_b.pos()
        path = _bezier_path(p1, p2, self._curvature,
                            self.node_a.radius, self.node_b.radius)
        self.setPath(path)

    def set_active_focus(self, active: bool, dimmed: bool = False):
        self._is_active = active
        self._is_dimmed = dimmed
        pen = QPen(self.pen())
        if active:
            pen.setWidthF(self._base_width + 1.2)
            self.setPen(pen)
            self.setOpacity(1.0)
            self.setZValue(8)
        elif dimmed:
            pen.setWidthF(self._base_width)
            self.setPen(pen)
            self.setOpacity(0.08)
            self.setZValue(1)
        else:
            pen.setWidthF(self._base_width)
            self.setPen(pen)
            self.setOpacity(0.40)
            self.setZValue(3)
        self.update()

    def boundingRect(self) -> QRectF:
        return super().boundingRect().adjusted(-20, -20, 20, 20)

    def paint(self, painter: QPainter | None, option, widget=None):
        if painter is None:
            return
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        path = self.path()
        if path.isEmpty():
            return
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # 1. Glow exterior cuando la arista está en foco
        if self._is_active:
            glow_pen = QPen(self._glow_color, (self._base_width + 1.2) * 3.0)
            glow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            glow_c = QColor(self._glow_color)
            glow_c.setAlphaF(0.28)
            glow_pen.setColor(glow_c)
            if self._dash:
                glow_pen.setStyle(Qt.PenStyle.CustomDashLine)
                glow_pen.setDashPattern(self._dash)
            painter.setPen(glow_pen)
            painter.drawPath(path)

        # 2. Trazo de la línea principal
        main_pen = QPen(self._base_color,
                        self._base_width + 1.2 if self._is_active else self._base_width)
        main_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        if self._dash:
            main_pen.setStyle(Qt.PenStyle.CustomDashLine)
            main_pen.setDashPattern(self._dash)
        painter.setPen(main_pen)
        painter.drawPath(path)

        # 3. Etiqueta informativa en el centro
        if self._is_active and self._label:
            mid = path.pointAtPercent(0.5)
            painter.setFont(self._label_font)
            lc = QColor(self._base_color.lighter(175))
            lc.setAlphaF(0.95)
            painter.setPen(QPen(lc))
            painter.drawText(
                QRectF(mid.x() - 60, mid.y() - 14, 120, 18),
                Qt.AlignmentFlag.AlignCenter,
                self._label
            )
