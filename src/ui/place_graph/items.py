"""
items.py — Items gráficos para el Grafo de Lugares (Nodos y Aristas).
Renderizado idéntico en calidad, curvas Bézier y resplandor al Grafo de Relaciones.
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
from core.theme_manager import ThemeManager
from .models import PLACE_CATEGORY_COLORS, CONNECTION_STYLES, CATEGORY_TIERS, TIER_NODE_RADIUS


def bezier_path(p1: QPointF, p2: QPointF, curv: float = 0.16,
                r1: float = 0.0, r2: float = 0.0) -> QPainterPath:
    """
    Genera una curva Bézier suave y elegante (idéntica a RelationGraph)
    que nace y termina exactamente en el perímetro/borde de cada nodo esférico.
    """
    dx = p2.x() - p1.x()
    dy = p2.y() - p1.y()
    dist = math.hypot(dx, dy)
    if dist < 1.0:
        return QPainterPath()

    # Vector normal perpendicular para la curvatura
    nx = -dy / dist * dist * curv
    ny =  dx / dist * dist * curv
    ctrl = QPointF((p1.x() + p2.x()) / 2 + nx, (p1.y() + p2.y()) / 2 + ny)

    # Recortar punto inicial al borde del nodo 1
    if r1 > 0:
        v1x, v1y = ctrl.x() - p1.x(), ctrl.y() - p1.y()
        d1 = max(math.hypot(v1x, v1y), 1.0)
        start_pt = QPointF(p1.x() + (v1x / d1) * r1, p1.y() + (v1y / d1) * r1)
    else:
        start_pt = p1

    # Recortar punto final al borde del nodo 2
    if r2 > 0:
        v2x, v2y = ctrl.x() - p2.x(), ctrl.y() - p2.y()
        d2 = max(math.hypot(v2x, v2y), 1.0)
        end_pt = QPointF(p2.x() + (v2x / d2) * r2, p2.y() + (v2y / d2) * r2)
    else:
        end_pt = p2

    path = QPainterPath(start_pt)
    path.quadTo(ctrl, end_pt)
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
        # Debe cubrir el aura máxima en estado enfocado (aura_mult=0.85) + margen de etiqueta
        max_aura = r + r * 0.85 + 10 + 8  # +8px margen antialiasing
        hw = max(max_aura, r + 26)         # garantizar que también cubra la etiqueta
        label_h = 50                        # nombre + subcategoría debajo del nodo
        return QRectF(-hw, -hw, hw * 2, hw * 2 + label_h)

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
        # Suprimir el rectángulo de selección estilo sistema operativo que dibuja Qt.
        # Usamos nuestro propio anillo circular enfocado en su lugar.
        if option is not None and hasattr(option, 'state'):
            from PyQt6.QtWidgets import QStyle
            option.state &= ~QStyle.StateFlag.State_Selected
            option.state &= ~QStyle.StateFlag.State_HasFocus

        r = self.radius
        c = self._color

        # Opacidad según estado de foco (siempre visible)
        if self._is_dimmed and not self._is_focused:
            painter.setOpacity(0.35)
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
        show_name = True
        if show_name:
            is_dark = ThemeManager.is_dark()
            name_col = QColor("#f2f2f7" if is_dark else "#1c1c1e")
            if self._is_dimmed and not self._is_focused:
                name_col.setAlphaF(0.40)
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
                sub_col = QColor(c.lighter(160) if is_dark else c.darker(140))
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
    Arista de conexión geográfica con arco Bézier suave, glow y foco dinámico
    (Idéntica a RelationEdge del grafo de relaciones).
    """
    def __init__(self, link: PlaceLink, node_a: PlaceNodeItem, node_b: PlaceNodeItem,
                 curvature: float = 0.16):
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
        self._idle_width = 1.0
        self._active_width = 2.4
        self._is_active = False
        self._is_dimmed = False
        self._label = getattr(link, "label", "") or conn_type

        pen = QPen(self._base_color, self._idle_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        if self._dash:
            pen.setStyle(Qt.PenStyle.CustomDashLine)
            pen.setDashPattern(self._dash)
        self.setPen(pen)
        self.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self.setZValue(3)
        self.setOpacity(0.50)

        self._label_font = QFont("Segoe UI", 8, QFont.Weight.Bold)
        self._update_path()

        node_a.edges.append(self)
        node_b.edges.append(self)

    def _update_path(self):
        p1 = self.node_a.pos()
        p2 = self.node_b.pos()
        path = bezier_path(p1, p2, self._curvature,
                           self.node_a.radius, self.node_b.radius)
        self.setPath(path)

    def set_active_focus(self, active: bool, dimmed: bool = False):
        self._is_active = active
        self._is_dimmed = dimmed
        pen = QPen(self.pen())
        if active:
            pen.setWidthF(self._active_width)
            self.setPen(pen)
            self.setOpacity(1.0)
            self.setZValue(9)
        elif dimmed:
            pen.setWidthF(self._idle_width)
            self.setPen(pen)
            self.setOpacity(0.18)
            self.setZValue(2)
        else:
            pen.setWidthF(self._idle_width)
            self.setPen(pen)
            self.setOpacity(0.50)
            self.setZValue(3)
        self.update()

    def boundingRect(self) -> QRectF:
        return super().boundingRect().adjusted(-50, -50, 50, 50)

    def paint(self, painter: QPainter | None, option, widget=None):
        if painter is None:
            return
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        path = self.path()
        if path.isEmpty():
            return
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # 1. Glow exterior elegante al estar en foco
        if self._is_active:
            glow_pen = QPen(self._glow_color, self._active_width * 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.save()
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(glow_pen)
            painter.setOpacity(0.40)
            painter.drawPath(path)
            painter.restore()

        # 2. Línea principal limpia
        main_pen = QPen(self._base_color,
                        self._active_width if self._is_active else self._idle_width)
        main_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        if self._dash:
            main_pen.setStyle(Qt.PenStyle.CustomDashLine)
            main_pen.setDashPattern(self._dash)
        painter.setPen(main_pen)
        painter.drawPath(path)

        # 3. Etiqueta informativa centrada en la curva (con badge pill estilizado)
        if self._is_active and self._label:
            painter.save()
            painter.setFont(self._label_font)
            is_dark = ThemeManager.is_dark()
            fm = painter.fontMetrics()
            tw = fm.horizontalAdvance(self._label)
            th = fm.height()
            mid = path.pointAtPercent(0.5)

            rect = QRectF(mid.x() - tw / 2 - 8, mid.y() - th / 2 - 3, tw + 16, th + 6)
            bg_col = QColor("#1c1c1e" if is_dark else "#faf7f3")
            bg_col.setAlphaF(0.96)
            border_col = QColor(self._base_color)
            border_col.setAlphaF(0.90)

            painter.setBrush(QBrush(bg_col))
            painter.setPen(QPen(border_col, 1.4))
            painter.drawRoundedRect(rect, 4, 4)

            txt_col = self._base_color.lighter(160) if is_dark else self._base_color.darker(160)
            painter.setPen(QPen(txt_col))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._label)
            painter.restore()


class PresenceBadgeItem(QGraphicsEllipseItem):
    """
    Badge pequeño que representa la presencia de un personaje sobre un nodo de lugar.

    Diseño:
      - Círculo de 12px de diámetro con la inicial del personaje
      - Borde sólido si confidence ≥ 0.75 (presencia confirmada/detectada)
      - Borde punteado si confidence < 0.75 (sugerencia pendiente de confirmar)
      - Se posiciona en arco alrededor del borde del nodo padre
      - Completamente transparente al mouse (no interfiere con clics en el nodo)

    IMPORTANTE: setAcceptedMouseButtons(NoButton) garantiza que todos los eventos
    de mouse pasen al nodo padre sin modificación — no rompe ninguna lógica existente.
    """

    _BADGE_RADIUS = 7.5          # radio del badge en px
    _PRESENT_COLOR = QColor("#ffd60a")      # dorado: presente
    _TRANSIT_COLOR = QColor("#0a84ff")      # azul: en tránsito
    _DEPARTED_COLOR = QColor("#ff453a")     # rojo/naranja: salida / partida
    _SUGGESTED_COLOR = QColor("#8e8e93")    # gris: baja confianza / sugerencia

    def __init__(
        self,
        initial: str,
        confidence: float,
        presence_type: str = "present",
        index: int = 0,
        character_name: str = "",
        parent: QGraphicsItem | None = None,
    ):
        r = self._BADGE_RADIUS
        super().__init__(-r, -r, r * 2, r * 2, parent)

        self._initial = initial[:1].upper() if initial else "?"
        self._confidence = confidence
        self._presence_type = presence_type
        self._is_confirmed = confidence >= 0.70

        if character_name:
            type_label = "Presente" if presence_type == "present" else ("En tránsito" if presence_type == "transit" else "Salida")
            self.setToolTip(f"{character_name} ({type_label} - {int(confidence*100)}%)")

        # ── Posición: arco alrededor del borde del nodo padre ─────────────
        import math
        parent_radius = getattr(parent, "radius", 22.0) if parent else 22.0
        # Distribuir badges cada 32° empezando desde arriba-derecha
        angle_deg = -65 + index * 32
        angle_rad = math.radians(angle_deg)
        offset_x = math.cos(angle_rad) * (parent_radius + r + 3)
        offset_y = math.sin(angle_rad) * (parent_radius + r + 3)
        self.setPos(offset_x, offset_y)

        # ── Transparente completamente al mouse salvo para tooltip ─────────
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setZValue(20)   # siempre encima del nodo

    def _get_color(self) -> QColor:
        if not self._is_confirmed:
            return self._SUGGESTED_COLOR
        if self._presence_type == "transit":
            return self._TRANSIT_COLOR
        if self._presence_type == "departed":
            return self._DEPARTED_COLOR
        return self._PRESENT_COLOR

    def paint(self, painter: QPainter | None, option, widget=None):
        if painter is None:
            return
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        color = self._get_color()
        r = self._BADGE_RADIUS

        # Sombra / resplandor suave
        glow = QRadialGradient(0, 0, r + 3)
        glow.setColorAt(0.0, QColor(color.red(), color.green(), color.blue(), 100))
        glow.setColorAt(1.0, QColor(color.red(), color.green(), color.blue(), 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(glow))
        painter.drawEllipse(QRectF(-r - 3, -r - 3, (r + 3) * 2, (r + 3) * 2))

        # Fondo del badge
        painter.setBrush(QBrush(color.darker(190)))
        if self._is_confirmed:
            pen_style = Qt.PenStyle.DashLine if self._presence_type == "transit" else Qt.PenStyle.SolidLine
            painter.setPen(QPen(color, 1.5, pen_style))
        else:
            painter.setPen(QPen(color, 1.2, Qt.PenStyle.DotLine))

        painter.drawEllipse(QRectF(-r, -r, r * 2, r * 2))

        # Inicial del personaje
        font = QFont("Inter", int(r * 0.85), QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QPen(color.lighter(180)))
        painter.drawText(
            QRectF(-r, -r, r * 2, r * 2),
            Qt.AlignmentFlag.AlignCenter,
            self._initial,
        )
        painter.restore()


class PresenceOverflowBadgeItem(QGraphicsEllipseItem):
    """
    Badge contador de multitud (+N) cuando hay más de 3 personajes en un mismo lugar.
    Muestra los personajes restantes en tooltip y mantiene la escena limpia y legible.
    """
    _BADGE_RADIUS = 8.0
    _COLOR = QColor("#5856d6")  # Púrpura / Índigo sofisticado para multitudes

    def __init__(
        self,
        overflow_count: int,
        remaining_names: list[str],
        index: int = 3,
        parent: QGraphicsItem | None = None,
    ):
        r = self._BADGE_RADIUS
        super().__init__(-r, -r, r * 2, r * 2, parent)

        self._count = overflow_count
        self._text = f"+{overflow_count}"

        if remaining_names:
            names_preview = "\n• ".join(remaining_names[:10])
            if len(remaining_names) > 10:
                names_preview += f"\n... y {len(remaining_names) - 10} más"
            self.setToolTip(f"👥 {overflow_count} personajes más presentes aquí:\n• {names_preview}")

        # ── Posición: arco continuo después del 3er badge ─────────────
        parent_radius = getattr(parent, "radius", 22.0) if parent else 22.0
        angle_deg = -65 + index * 32
        angle_rad = math.radians(angle_deg)
        offset_x = math.cos(angle_rad) * (parent_radius + r + 3)
        offset_y = math.sin(angle_rad) * (parent_radius + r + 3)
        self.setPos(offset_x, offset_y)

        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setZValue(21)

    def paint(self, painter: QPainter | None, option, widget=None):
        if painter is None:
            return
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        color = self._COLOR
        r = self._BADGE_RADIUS

        # Resplandor sutil
        glow = QRadialGradient(0, 0, r + 3)
        glow.setColorAt(0.0, QColor(color.red(), color.green(), color.blue(), 120))
        glow.setColorAt(1.0, QColor(color.red(), color.green(), color.blue(), 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(glow))
        painter.drawEllipse(QRectF(-r - 3, -r - 3, (r + 3) * 2, (r + 3) * 2))

        # Fondo
        painter.setBrush(QBrush(color.darker(180)))
        painter.setPen(QPen(color.lighter(130), 1.4))
        painter.drawEllipse(QRectF(-r, -r, r * 2, r * 2))

        # Texto +N
        font = QFont("Inter", int(r * 0.75), QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QPen(QColor("#ffffff")))
        painter.drawText(
            QRectF(-r, -r, r * 2, r * 2),
            Qt.AlignmentFlag.AlignCenter,
            self._text,
        )
        painter.restore()

