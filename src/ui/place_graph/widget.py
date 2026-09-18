"""
widget.py — Atlas Literario: Grafo de Lugares & Conexiones.

Nivel visual idéntico al Grafo de Relaciones:
  - Fondo negro profundo con drawBackground personalizado
  - Nodos con gradiente radial tipo gema y halo luminoso por categoría
  - Aristas Bézier con glow activo al enfocar
  - Foco / dimming interactivo al seleccionar un nodo
  - Zoom suave con rueda del ratón
  - Tooltips ricos y leyenda inferior de tipos de conexión
"""
from __future__ import annotations

import math
import random
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGraphicsView, QGraphicsScene,
    QGraphicsItem, QGraphicsEllipseItem, QGraphicsPathItem, QLabel,
    QPushButton, QComboBox, QLineEdit, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF, QTimeLine, QEasingCurve
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QCursor,
    QPainterPath, QRadialGradient, QTransform
)
import qtawesome as qta

from core.models import (
    Place, PlaceLink, PLACE_ICONS, CONNECTION_COLORS, CONNECTION_TYPES
)
from core.theme_manager import ThemeManager

# ── Paleta de colores por categoría (misma filosofía que CHARACTER_PALETTE) ──
PLACE_CATEGORY_COLORS: dict[str, str] = {
    "Reino / Nación":      "#ffd60a",   # dorado soberano
    "Ciudad / Poblado":    "#0a84ff",   # azul urbano
    "Fortaleza / Castillo":"#ff453a",   # rojo fortaleza
    "Taberna / Interior":  "#ff9f0a",   # ámbar cálido
    "Mazmorra / Cueva":    "#bf5af2",   # violeta oscuro
    "Naturaleza / Bosque": "#30d158",   # verde esmeralda
    "Región Mágica":       "#64d2ff",   # cian etéreo
    "Planeta / Espacio":   "#5e5ce6",   # índigo galáctico
    "Otro":                "#8e8e93",   # gris neutro
}

# Estilos de aristas por tipo de conexión
CONNECTION_STYLES: dict[str, dict] = {
    "ruta":      {"color": "#30d158", "glow": "#30d158", "dash": None,       "width": 1.8},
    "frontera":  {"color": "#ff453a", "glow": "#ff453a", "dash": [6.0, 4.0], "width": 2.0},
    "portal":    {"color": "#bf5af2", "glow": "#bf5af2", "dash": [2.0, 3.0], "width": 2.2},
    "río":       {"color": "#0a84ff", "glow": "#0a84ff", "dash": [8.0, 3.0], "width": 1.6},
    "camino":    {"color": "#ffd60a", "glow": "#ffd60a", "dash": [4.0, 4.0], "width": 1.6},
    "comercio":  {"color": "#ff9f0a", "glow": "#ff9f0a", "dash": None,       "width": 1.8},
    "contiene":  {"color": "#bf5af2", "glow": "#bf5af2", "dash": [3.0, 3.0], "width": 1.4},
    "otro":      {"color": "#8e8e93", "glow": "#8e8e93", "dash": None,       "width": 1.4},
}


# ═════════════════════════════════════════════════════════════════════════════
# Nodo gráfico de Lugar
# ═════════════════════════════════════════════════════════════════════════════

class PlaceNodeItem(QGraphicsEllipseItem):
    """
    Nodo de Lugar con renderizado premium idéntico al CharacterNode del grafo de relaciones:
    - Halo luminoso radial difuso
    - Cuerpo con gradiente tipo gema
    - Icono centrado de categoría
    - Nombre bajo el nodo
    - Estado focused / dimmed
    """

    def __init__(self, place: Place, x: float, y: float,
                 depth: int = 0, child_count: int = 0, parent=None):
        # Radio según jerarquía: raíces más grandes, estancias más compactas
        radius = max(18.0, 34.0 - depth * 5.0)
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
        self.setZValue(10 if depth == 0 else 7)

        # Tooltip
        parts = [f"📍 {place.name}", f"Categoría: {place.category}"]
        if place.climate_atmosphere:
            parts.append(f"Clima: {place.climate_atmosphere[:80]}")
        if place.lore_history:
            parts.append(f"Lore: {place.lore_history[:100]}")
        if child_count:
            parts.append(f"Contiene: {child_count} estancia(s)")
        self.setToolTip("\n".join(parts))

        # Fuentes precalculadas
        self._font_icon = QFont("Segoe UI Emoji", int(radius * 0.55))
        self._font_name = QFont("Segoe UI", 10 if depth == 0 else 9,
                                QFont.Weight.Bold if depth == 0 else QFont.Weight.Normal)
        self._font_badge = QFont("Segoe UI", 8, QFont.Weight.Bold)
        self._icon_str = PLACE_ICONS.get(place.category, "📍")

    def boundingRect(self) -> QRectF:
        r = self.radius
        return QRectF(-r - 20, -r - 20, (r + 20) * 2, (r + 20) * 2 + 36)

    def set_focused(self, focused: bool, dimmed: bool = False):
        self._is_focused = focused
        self._is_dimmed = dimmed
        self.setZValue(14 if focused else (10 if not dimmed else 5))
        self.update()

    def paint(self, painter: QPainter | None, option, widget=None):
        if painter is None:
            return
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        r = self.radius
        c = self._color

        # Opacidad global
        if self._is_dimmed and not self._is_focused:
            painter.setOpacity(0.12)
        else:
            painter.setOpacity(1.0)

        # 1. Halo / Aura luminosa (gradiente radial difuso)
        aura_mult = 0.70 if self._is_focused else (0.50 if self.depth == 0 else 0.35)
        aura_alpha = 0.50 if self._is_focused else (0.35 if self.depth == 0 else 0.20)
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

        # 2. Cuerpo principal con gradiente tipo gema
        grad = QRadialGradient(-r * 0.35, -r * 0.35, r * 1.35)
        if self.depth == 0:
            grad.setColorAt(0.00, QColor("#ffffff"))
            grad.setColorAt(0.30, c.lighter(160))
            grad.setColorAt(0.75, c)
            grad.setColorAt(1.00, c.darker(145))
        else:
            grad.setColorAt(0.00, c.lighter(140))
            grad.setColorAt(0.60, c)
            grad.setColorAt(1.00, c.darker(155))

        border_pen = QPen(
            c.lighter(165) if self.depth == 0 else c.lighter(130),
            2.2 if self.depth == 0 else 1.4
        )
        painter.setPen(border_pen)
        painter.setBrush(QBrush(grad))
        painter.drawEllipse(QPointF(0, 0), r, r)

        # 3. Anillo de enfoque
        if self._is_focused:
            ring_pen = QPen(c.lighter(190), 3.0)
            painter.setPen(ring_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPointF(0, 0), r + 7, r + 7)

        # 4. Icono centrado
        painter.setFont(self._font_icon)
        painter.setPen(QPen(QColor("#ffffff")))
        painter.drawText(QRectF(-r, -r, r * 2, r * 2),
                         Qt.AlignmentFlag.AlignCenter, self._icon_str)

        # 5. Badge de hijos en esquina superior derecha
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

        # 6. Nombre del lugar (debajo del círculo)
        show_name = self._is_focused or self.depth == 0 or not self._is_dimmed
        if show_name:
            name_col = QColor("#f2f2f7")
            if self._is_dimmed and not self._is_focused:
                name_col.setAlphaF(0.30)
            painter.setFont(self._font_name)
            painter.setPen(QPen(name_col))
            text_w = max(200.0, r * 5)
            painter.drawText(
                QRectF(-text_w / 2, r + 6, text_w, 26),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                self.place.name
            )

            # Subcategoría en color de categoría si está enfocado
            if self._is_focused:
                sub_col = QColor(c.lighter(160))
                sub_col.setAlphaF(0.90)
                sub_font = QFont("Segoe UI", 8)
                painter.setFont(sub_font)
                painter.setPen(QPen(sub_col))
                painter.drawText(
                    QRectF(-text_w / 2, r + 28, text_w, 18),
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


# ═════════════════════════════════════════════════════════════════════════════
# Arista Bézier de Conexión Geográfica
# ═════════════════════════════════════════════════════════════════════════════

def _bezier_path(p1: QPointF, p2: QPointF, curvature: float = 0.18,
                 r1: float = 0.0, r2: float = 0.0) -> QPainterPath:
    """Curva Bézier cuadrática entre dos puntos con offset en los bordes de los nodos."""
    dx = p2.x() - p1.x()
    dy = p2.y() - p1.y()
    dist = math.hypot(dx, dy) or 1.0
    # Offset del borde del nodo origen
    ux, uy = dx / dist, dy / dist
    sp = QPointF(p1.x() + ux * r1, p1.y() + uy * r1)
    ep = QPointF(p2.x() - ux * r2, p2.y() - uy * r2)
    # Control point perpendicular al segmento
    perp_x = -dy / dist * dist * curvature
    perp_y =  dx / dist * dist * curvature
    mid = QPointF((sp.x() + ep.x()) / 2 + perp_x,
                  (sp.y() + ep.y()) / 2 + perp_y)
    path = QPainterPath(sp)
    path.quadTo(mid, ep)
    return path


class PlaceLinkItem(QGraphicsPathItem):
    """
    Arista de conexión geográfica con Bézier y glow activo,
    idéntica en calidad al RelationEdge del grafo de personajes.
    """
    def __init__(self, link: PlaceLink, node_a: PlaceNodeItem, node_b: PlaceNodeItem,
                 curvature: float = 0.12):
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
        self.setZValue(2)
        self.setOpacity(0.55)

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
            pen.setWidthF(self._base_width + 1.4)
            self.setPen(pen)
            self.setOpacity(1.0)
            self.setZValue(8)
        elif dimmed:
            pen.setWidthF(self._base_width)
            self.setPen(pen)
            self.setOpacity(0.12)
            self.setZValue(2)
        else:
            pen.setWidthF(self._base_width)
            self.setPen(pen)
            self.setOpacity(0.55)
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

        # 1. Glow exterior (solo si está activa)
        if self._is_active:
            glow_pen = QPen(self._glow_color, (self._base_width + 1.4) * 3.5)
            glow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            glow_c = QColor(self._glow_color)
            glow_c.setAlphaF(0.28)
            glow_pen.setColor(glow_c)
            if self._dash:
                glow_pen.setStyle(Qt.PenStyle.CustomDashLine)
                glow_pen.setDashPattern(self._dash)
            painter.setPen(glow_pen)
            painter.drawPath(path)

        # 2. Línea principal
        main_pen = QPen(self._base_color,
                        self._base_width + 1.4 if self._is_active else self._base_width)
        main_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        if self._dash:
            main_pen.setStyle(Qt.PenStyle.CustomDashLine)
            main_pen.setDashPattern(self._dash)
        painter.setPen(main_pen)
        painter.drawPath(path)

        # 3. Etiqueta en el punto medio
        if self._is_active and self._label:
            mid = path.pointAtPercent(0.5)
            painter.setFont(self._label_font)
            lc = QColor(self._base_color.lighter(175))
            lc.setAlphaF(0.95)
            painter.setPen(QPen(lc))
            painter.drawText(
                QRectF(mid.x() - 55, mid.y() - 14, 110, 18),
                Qt.AlignmentFlag.AlignCenter,
                self._label
            )


# ═════════════════════════════════════════════════════════════════════════════
# Escena
# ═════════════════════════════════════════════════════════════════════════════

class PlaceGraphScene(QGraphicsScene):
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
            self._clear_focus()
            return
        self._focused_id = place_id
        neighbors = self._adj.get(place_id, set())
        connected = {place_id} | neighbors

        for nid, node in self._nodes.items():
            if nid == place_id:
                node.set_focused(True, False)
            elif nid in connected:
                node.set_focused(False, False)
            else:
                node.set_focused(False, True)

        for edge in self._all_edges:
            is_mine = (edge.node_a.place.id == place_id or
                       edge.node_b.place.id == place_id)
            if is_mine:
                edge.set_active_focus(True, False)
            else:
                edge.set_active_focus(False, True)

    def _clear_focus(self):
        self._focused_id = None
        for node in self._nodes.values():
            node.set_focused(False, False)
        for edge in self._all_edges:
            edge.set_active_focus(False, False)

    def mousePressEvent(self, event):
        view = self.views()[0] if self.views() else None
        item = self.itemAt(event.scenePos(), view.transform() if view else QTransform())
        if not isinstance(item, PlaceNodeItem):
            self._clear_focus()
            self.background_clicked.emit()
        super().mousePressEvent(event)


# ═════════════════════════════════════════════════════════════════════════════
# Vista
# ═════════════════════════════════════════════════════════════════════════════

class PlaceGraphView(QGraphicsView):
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

    def drawBackground(self, painter: QPainter | None, rect: QRectF):
        if painter is None:
            return
        painter.fillRect(rect, QColor("#0d0d0f"))

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        factor = 1.15 if delta > 0 else (1 / 1.15)
        self.scale(factor, factor)
        event.accept()


# ═════════════════════════════════════════════════════════════════════════════
# Widget principal: PlaceGraphWidget
# ═════════════════════════════════════════════════════════════════════════════

class PlaceGraphWidget(QWidget):
    """
    Lienzo completo del Atlas Literario con toolbar, búsqueda,
    spring layout y foco interactivo. Mismo nivel visual que RelationGraphWidget.
    """
    place_selected = pyqtSignal(str)
    place_double_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._places: list[Place] = []
        self._links: list[PlaceLink] = []
        self._node_map: dict[str, PlaceNodeItem] = {}
        self._setup_ui()

    @property
    def _link_items(self) -> list[PlaceLinkItem]:
        """Alias de compatibilidad: apunta a _scene._all_edges."""
        return self._scene._all_edges

    # ── UI ──────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Toolbar oscura superior
        tb = QFrame()
        tb.setFixedHeight(50)
        tb.setStyleSheet("""
            QFrame { background-color: #161618; border-bottom: 1px solid #2c2c2e; }
            QLabel { color: #f2f2f7; font-weight: bold; font-size: 12px; }
            QLineEdit {
                background: #2c2c2e; color: #f2f2f7;
                border: 1px solid #3a3a3c; border-radius: 6px;
                padding: 4px 8px; font-size: 11px;
            }
            QComboBox {
                background: #2c2c2e; color: #f2f2f7;
                border: 1px solid #3a3a3c; border-radius: 6px;
                padding: 4px 8px; font-size: 11px;
            }
            QPushButton {
                background: #2c2c2e; color: #f2f2f7;
                border: 1px solid #3a3a3c; border-radius: 6px;
                padding: 5px 12px; font-size: 11px; font-weight: bold;
            }
            QPushButton:hover { background: #3a3a3c; }
        """)
        tbl = QHBoxLayout(tb)
        tbl.setContentsMargins(14, 0, 14, 0)
        tbl.setSpacing(10)

        ico_lbl = QLabel("🗺️  ATLAS DE CONEXIONES")
        ico_lbl.setStyleSheet("color: #ffd60a; font-weight: bold; font-size: 12px;")
        tbl.addWidget(ico_lbl)
        tbl.addSpacing(12)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Buscar escenario...")
        self._search_input.setClearButtonEnabled(True)
        self._search_input.setMaximumWidth(180)
        self._search_input.textChanged.connect(self._on_search)
        tbl.addWidget(self._search_input)

        tbl.addWidget(QLabel("Vista:"))
        self._view_mode_combo = QComboBox()
        self._view_mode_combo.addItem("🌐 Red Geográfica", "network")
        self._view_mode_combo.addItem("🏛️  Árbol de Estancias", "tree")
        self._view_mode_combo.setMaximumWidth(175)
        self._view_mode_combo.currentIndexChanged.connect(self._on_view_mode_changed)
        tbl.addWidget(self._view_mode_combo)

        tbl.addStretch()

        self._btn_layout = QPushButton("⚡ Reorganizar")
        self._btn_layout.setToolTip("Distribuye los lugares con simulación de fuerzas")
        self._btn_layout.clicked.connect(self.reorganize_layout)
        tbl.addWidget(self._btn_layout)

        btn_zoom_in = QPushButton("＋")
        btn_zoom_in.setFixedWidth(34)
        btn_zoom_in.clicked.connect(lambda: self._view.scale(1.2, 1.2))
        tbl.addWidget(btn_zoom_in)

        btn_zoom_out = QPushButton("－")
        btn_zoom_out.setFixedWidth(34)
        btn_zoom_out.clicked.connect(lambda: self._view.scale(1 / 1.2, 1 / 1.2))
        tbl.addWidget(btn_zoom_out)

        btn_fit = QPushButton("↺ Ajustar")
        btn_fit.clicked.connect(self._fit_to_view)
        tbl.addWidget(btn_fit)

        root.addWidget(tb)

        # Escena + Vista
        self._scene = PlaceGraphScene(self)
        self._scene.place_selected.connect(self.place_selected)
        self._scene.place_double_clicked.connect(self.place_double_clicked)
        self._scene.background_clicked.connect(self._on_background_clicked)

        self._view = PlaceGraphView(self._scene, self)
        root.addWidget(self._view, stretch=1)

        # Leyenda inferior
        root.addWidget(self._build_legend())

    def _build_legend(self) -> QFrame:
        bar = QFrame()
        bar.setFixedHeight(34)
        bar.setStyleSheet("""
            QFrame { background: #161618; border-top: 1px solid #2c2c2e; }
            QLabel { color: #8e8e93; font-size: 10px; padding: 0 6px; }
        """)
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(14, 0, 14, 0)
        bl.setSpacing(0)

        legend_items = [
            ("ruta",     "Ruta"),
            ("frontera", "Frontera"),
            ("portal",   "Portal"),
            ("río",      "Río"),
            ("camino",   "Camino"),
            ("comercio", "Comercio"),
        ]
        for key, display in legend_items:
            color = CONNECTION_STYLES[key]["color"]
            dot = QLabel("━")
            dot.setStyleSheet(f"color: {color}; font-size: 14px; padding: 0 2px;")
            lbl = QLabel(display)
            lbl.setStyleSheet("color: #8e8e93; font-size: 10px; padding-right: 10px;")
            bl.addWidget(dot)
            bl.addWidget(lbl)

        bl.addStretch()

        # Jerarquía
        hier_dot = QLabel("╌╌")
        hier_dot.setStyleSheet("color: #bf5af2; font-size: 12px; padding: 0 2px;")
        hier_lbl = QLabel("Jerarquía (contiene)")
        hier_lbl.setStyleSheet("color: #8e8e93; font-size: 10px;")
        bl.addWidget(hier_dot)
        bl.addWidget(hier_lbl)

        return bar

    # ── Datos ───────────────────────────────────────────────────────────────

    def set_data(self, places: list[Place], links: list[PlaceLink]):
        self._places = list(places)
        self._links = list(links)
        self._rebuild_graph()

    def _on_view_mode_changed(self):
        self._rebuild_graph()

    def _on_background_clicked(self):
        pass  # ya gestionado en la escena

    # ── Construcción del grafo ───────────────────────────────────────────────

    def _rebuild_graph(self):
        self._scene.clear()
        self._node_map.clear()
        self._scene._nodes.clear()
        self._scene._all_edges.clear()
        self._scene._adj.clear()
        self._scene._focused_id = None

        if not self._places:
            return

        mode = self._view_mode_combo.currentData() if hasattr(self, "_view_mode_combo") else "network"

        # Precalcular jerarquías
        parent_map = {p.id: p.parent_place_id for p in self._places}
        children_map: dict[str, list[str]] = {p.id: [] for p in self._places}
        for p in self._places:
            if p.parent_place_id and p.parent_place_id in children_map:
                children_map[p.parent_place_id].append(p.id)

        depth_map: dict[str, int] = {}
        for p in self._places:
            d, cur, seen = 0, p.parent_place_id, set()
            while cur and cur not in seen:
                seen.add(cur); d += 1; cur = parent_map.get(cur, "")
            depth_map[p.id] = d

        # ── Posicionamiento ──────────────────────────────────────────────────
        if mode == "tree":
            roots = [p for p in self._places
                     if not p.parent_place_id or p.parent_place_id not in depth_map]
            if not roots:
                roots = list(self._places)
            current_x = 0.0
            x_spacing, y_spacing = 160.0, 150.0

            def _layout_tree(nid: str, depth: int) -> float:
                nonlocal current_x
                child_ids = children_map.get(nid, [])
                place_obj = next((p for p in self._places if p.id == nid), None)
                if not place_obj:
                    return current_x
                if not child_ids:
                    nx = current_x; current_x += x_spacing
                else:
                    cxs = [_layout_tree(cid, depth + 1) for cid in child_ids]
                    nx = sum(cxs) / len(cxs)
                ny = depth * y_spacing
                node = PlaceNodeItem(place_obj, nx, ny,
                                     depth=depth, child_count=len(child_ids))
                self._scene.addItem(node)
                self._node_map[place_obj.id] = node
                self._scene._nodes[place_obj.id] = node
                self._scene._adj[place_obj.id] = set()
                return nx

            for r in roots:
                _layout_tree(r.id, 0)
                current_x += 60.0

        else:  # network — posición inicial aleatoria con jitter para evitar degeneración
            count = len(self._places)
            # Radio base generoso para que los nodos arranquen con espacio
            ring_r = max(300, count * 65)
            for i, place in enumerate(self._places):
                angle = (2 * math.pi / count) * i - math.pi / 2
                jitter_r = ring_r * 0.18
                x = ring_r * math.cos(angle) + random.uniform(-jitter_r, jitter_r)
                y = ring_r * math.sin(angle) + random.uniform(-jitter_r, jitter_r)
                depth = depth_map.get(place.id, 0)
                child_count = len(children_map.get(place.id, []))
                node = PlaceNodeItem(place, x, y, depth=depth, child_count=child_count)
                self._scene.addItem(node)
                self._node_map[place.id] = node
                self._scene._nodes[place.id] = node
                self._scene._adj[place.id] = set()

        # ── Aristas de jerarquía (padre → hijo) ─────────────────────────────
        edge_idx: dict[frozenset, int] = {}
        for p in self._places:
            if p.parent_place_id and p.parent_place_id in self._node_map and p.id in self._node_map:
                na = self._node_map[p.parent_place_id]
                nb = self._node_map[p.id]
                h_link = PlaceLink(
                    place_id_a=p.parent_place_id,
                    place_id_b=p.id,
                    label="contiene",
                    connection_type="contiene",
                    bidirectional=False
                )
                pair = frozenset([p.parent_place_id, p.id])
                edge_idx[pair] = edge_idx.get(pair, 0) + 1
                # Curvatura alternada para separar aristas paralelas
                curv = 0.10 * (1 if edge_idx[pair] % 2 == 1 else -1)
                item = PlaceLinkItem(h_link, na, nb, curvature=curv)
                self._scene.addItem(item)
                self._scene._all_edges.append(item)
                self._scene._adj.setdefault(p.parent_place_id, set()).add(p.id)
                self._scene._adj.setdefault(p.id, set()).add(p.parent_place_id)
                na.edges.append(item)
                nb.edges.append(item)

        # ── Aristas de conexiones geográficas ────────────────────────────────
        seen_pairs: set[frozenset] = set()
        for link in self._links:
            pair = frozenset([link.place_id_a, link.place_id_b])
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            na = self._node_map.get(link.place_id_a)
            nb = self._node_map.get(link.place_id_b)
            if na and nb:
                edge_idx[pair] = edge_idx.get(pair, 0) + 1
                curv = 0.14 * (1 if edge_idx[pair] % 2 == 1 else -1)
                item = PlaceLinkItem(link, na, nb, curvature=curv)
                self._scene.addItem(item)
                self._scene._all_edges.append(item)
                self._scene._adj.setdefault(link.place_id_a, set()).add(link.place_id_b)
                self._scene._adj.setdefault(link.place_id_b, set()).add(link.place_id_a)
                na.edges.append(item)
                nb.edges.append(item)

        # En modo red: ejecutar layout inteligente automáticamente
        # En modo árbol: solo ajustar vista (el árbol ya tiene posición calculada)
        if mode == "network" and len(self._places) > 1:
            self.reorganize_layout()
        else:
            self._fit_to_view()

    # ── Layout de Constelación (4 fases) ────────────────────────────────────

    def reorganize_layout(self):
        """
        Layout en 4 fases para efecto 'constelación':
          1. Detectar componentes conexas y ubicarlas en regiones separadas.
          2. Spring-Embedder fuerte con distancia mínima garantizada entre nodos.
          3. Refinamiento: refuerzo de separación mínima.
          4. Anti-cruce: intercambio de posiciones para reducir cruces visibles.
        """
        nodes = list(self._node_map.values())
        n = len(nodes)
        if n < 2:
            if n == 1:
                self._fit_to_view()
            return

        ids = [nd.place.id for nd in nodes]

        # Construir adyacencia completa (conexiones + jerarquías)
        adj: dict[str, set[str]] = {pid: set() for pid in ids}
        for lk in self._links:
            if lk.place_id_a in adj and lk.place_id_b in adj:
                adj[lk.place_id_a].add(lk.place_id_b)
                adj[lk.place_id_b].add(lk.place_id_a)
        for p in self._places:
            if p.parent_place_id and p.parent_place_id in adj and p.id in adj:
                adj[p.parent_place_id].add(p.id)
                adj[p.id].add(p.parent_place_id)

        # ── Fase 1: Componentes conexas → regiones distintas ─────────────────
        visited: set[str] = set()
        components: list[list[str]] = []
        for pid in ids:
            if pid not in visited:
                comp: list[str] = []
                queue = [pid]
                while queue:
                    cur = queue.pop(0)
                    if cur in visited:
                        continue
                    visited.add(cur)
                    comp.append(cur)
                    for nb in adj.get(cur, []):
                        if nb not in visited and nb in adj:
                            queue.append(nb)
                components.append(comp)

        num_comp = len(components)
        # Radio de cada componente proporcional a su tamaño
        def _comp_radius(size: int) -> float:
            return max(160.0, size * 90.0)

        # Distribuir componentes en espiral para que no se solapen
        comp_centers: list[tuple[float, float]] = []
        if num_comp == 1:
            comp_centers = [(0.0, 0.0)]
        else:
            for ci in range(num_comp):
                r_comp = _comp_radius(len(components[ci]))
                # Colocar componentes en círculo amplio
                angle = (2 * math.pi / num_comp) * ci
                gap = r_comp * 2.2  # espacio entre centros de componentes
                cx = gap * math.cos(angle)
                cy = gap * math.sin(angle)
                comp_centers.append((cx, cy))

        pos: dict[str, list[float]] = {}
        for ci, comp in enumerate(components):
            cx, cy = comp_centers[ci]
            nc = len(comp)
            r = _comp_radius(nc)
            for j, pid in enumerate(comp):
                if nc == 1:
                    px, py = cx, cy
                else:
                    angle = (2 * math.pi / nc) * j + random.uniform(-0.15, 0.15)
                    px = cx + r * math.cos(angle) + random.uniform(-12, 12)
                    py = cy + r * math.sin(angle) + random.uniform(-12, 12)
                pos[pid] = [px, py]

        # ── Fase 2: Spring-Embedder fuerte ───────────────────────────────────
        # Distancia mínima garantizada entre bordes de nodos
        min_node_dist = 160.0
        # Distancia ideal de resorte (más grande = más espacio)
        k = max(min_node_dist * 1.6, 220.0)
        iterations = 180

        # Lista de aristas para atracción (sin duplicados)
        attract_pairs: list[tuple[str, str]] = []
        seen_a: set[frozenset] = set()
        for lk in self._links:
            p = frozenset([lk.place_id_a, lk.place_id_b])
            if p not in seen_a and lk.place_id_a in pos and lk.place_id_b in pos:
                seen_a.add(p)
                attract_pairs.append((lk.place_id_a, lk.place_id_b))
        for pl in self._places:
            if pl.parent_place_id and pl.parent_place_id in pos and pl.id in pos:
                p = frozenset([pl.parent_place_id, pl.id])
                if p not in seen_a:
                    seen_a.add(p)
                    attract_pairs.append((pl.parent_place_id, pl.id))

        for step in range(iterations):
            disp: dict[str, list[float]] = {pid: [0.0, 0.0] for pid in ids}
            # Temperatura decreciente: más movimiento al principio, estabiliza al final
            t_ratio = 1.0 - step / iterations
            temp = k * (t_ratio ** 1.4)  # enfriamiento suave

            # Repulsión O(n²) con refuerzo de distancia mínima
            for i in range(n):
                uid = ids[i]
                for j in range(i + 1, n):
                    vid = ids[j]
                    dx = pos[uid][0] - pos[vid][0]
                    dy = pos[uid][1] - pos[vid][1]
                    dist = math.hypot(dx, dy) or 0.01

                    if dist < min_node_dist:
                        # Fuerza de separación extra muy fuerte (spring comprimido)
                        force = (k * k) / dist + (min_node_dist - dist) ** 2 * 0.8
                    else:
                        force = (k * k) / dist

                    ux, uy = dx / dist, dy / dist
                    disp[uid][0] += ux * force
                    disp[uid][1] += uy * force
                    disp[vid][0] -= ux * force
                    disp[vid][1] -= uy * force

            # Atracción solo entre nodos conectados
            for a_id, b_id in attract_pairs:
                dx = pos[a_id][0] - pos[b_id][0]
                dy = pos[a_id][1] - pos[b_id][1]
                dist = math.hypot(dx, dy) or 0.01
                force = (dist * dist) / k
                ux, uy = dx / dist, dy / dist
                disp[a_id][0] -= ux * force
                disp[a_id][1] -= uy * force
                disp[b_id][0] += ux * force
                disp[b_id][1] += uy * force

            # Aplicar con límite de temperatura (evita oscilaciones)
            for pid in ids:
                dx, dy = disp[pid]
                d = math.hypot(dx, dy) or 0.01
                move = min(d, temp)
                pos[pid][0] += (dx / d) * move
                pos[pid][1] += (dy / d) * move

        # ── Fase 3: Refinamiento — refuerzo de separación mínima ─────────────
        for _ in range(30):
            changed = False
            for i in range(n):
                uid = ids[i]
                for j in range(i + 1, n):
                    vid = ids[j]
                    dx = pos[uid][0] - pos[vid][0]
                    dy = pos[uid][1] - pos[vid][1]
                    dist = math.hypot(dx, dy) or 0.01
                    if dist < min_node_dist:
                        push = (min_node_dist - dist) / 2.0 + 2.0
                        ux, uy = dx / dist, dy / dist
                        pos[uid][0] += ux * push
                        pos[uid][1] += uy * push
                        pos[vid][0] -= ux * push
                        pos[vid][1] -= uy * push
                        changed = True
            if not changed:
                break

        # ── Fase 4: Anti-cruce (solo grafos ≤ 25 nodos para evitar lentitud) ─
        if n <= 25 and attract_pairs:
            def _segments_cross(p1, p2, p3, p4) -> bool:
                """True si los segmentos p1-p2 y p3-p4 se intersectan (interior)."""
                d1x = p2[0] - p1[0]; d1y = p2[1] - p1[1]
                d2x = p4[0] - p3[0]; d2y = p4[1] - p3[1]
                cross = d1x * d2y - d1y * d2x
                if abs(cross) < 1e-8:
                    return False
                t = ((p3[0] - p1[0]) * d2y - (p3[1] - p1[1]) * d2x) / cross
                u = ((p3[0] - p1[0]) * d1y - (p3[1] - p1[1]) * d1x) / cross
                return 0.02 < t < 0.98 and 0.02 < u < 0.98

            def _count_crossings() -> int:
                count = 0
                m = len(attract_pairs)
                for i in range(m):
                    a1, a2 = attract_pairs[i]
                    for j in range(i + 1, m):
                        b1, b2 = attract_pairs[j]
                        if len({a1, a2, b1, b2}) < 4:
                            continue
                        if _segments_cross(pos[a1], pos[a2], pos[b1], pos[b2]):
                            count += 1
                return count

            current = _count_crossings()
            for _pass in range(8):
                improved = False
                for i in range(n):
                    for j in range(i + 1, n):
                        uid, vid = ids[i], ids[j]
                        # Intercambiar posiciones
                        pos[uid], pos[vid] = pos[vid], pos[uid]
                        nc = _count_crossings()
                        if nc < current:
                            current = nc
                            improved = True
                        else:
                            pos[uid], pos[vid] = pos[vid], pos[uid]  # revertir
                if not improved or current == 0:
                    break

        # ── Aplicar posiciones finales ─────────────────────────────────────
        for nd in nodes:
            p = pos.get(nd.place.id)
            if p:
                nd.setPos(p[0], p[1])

        self._scene.update()
        self._fit_to_view()

    # ── Búsqueda ─────────────────────────────────────────────────────────────

    def _on_search(self, text: str):
        query = text.lower().strip()
        for node in self._node_map.values():
            match = not query or query in node.place.name.lower() or query in node.place.category.lower()
            node.setSelected(match if query else False)
            node.setOpacity(1.0 if (not query or match) else 0.18)

    # ── Utilidades ───────────────────────────────────────────────────────────

    def _fit_to_view(self):
        rect = self._scene.itemsBoundingRect()
        if not rect.isEmpty():
            self._view.fitInView(rect.adjusted(-80, -80, 80, 80),
                                 Qt.AspectRatioMode.KeepAspectRatio)
