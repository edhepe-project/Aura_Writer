"""
widget.py — Visualizador interactivo de Atlas / Grafo de Lugares y Conexiones del Universo.
Renderiza lugares como nodos topológicos y las conexiones geográficas (PlaceLink) como aristas con curvatura.
Incluye algoritmo de distribución por fuerzas (Spring Layout / Fruchterman-Reingold simplificado).
"""
from __future__ import annotations
import math
import random
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGraphicsView, QGraphicsScene,
    QGraphicsItem, QGraphicsEllipseItem, QGraphicsLineItem, QLabel,
    QPushButton, QComboBox, QLineEdit, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QCursor, QPainterPath
)
import qtawesome as qta

from core.models import (
    Place, PlaceLink, UniverseMetadata, PLACE_ICONS,
    CONNECTION_COLORS, CONNECTION_TYPES
)
from core.theme_manager import ThemeManager


class PlaceNodeItem(QGraphicsEllipseItem):
    """Nodo gráfico que representa un Lugar o Escenario."""
    def __init__(self, place: Place, x: float, y: float, depth: int = 0, child_count: int = 0, parent=None):
        # Escalar tamaño según jerarquía (lugares padre más grandes, estancias hijas más compactas)
        radius = max(20.0, 32.0 - (depth * 4.0))
        super().__init__(-radius, -radius, radius * 2, radius * 2, parent)
        self.place = place
        self.radius = radius
        self.depth = depth
        self.child_count = child_count
        self.setPos(x, y)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._hovered = False

    def hoverEnterEvent(self, event):
        self._hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        is_dark = ThemeManager.is_dark()

        base_color = QColor("#0a84ff" if self.isSelected() else ("#30d158" if self._hovered else ("#bf5af2" if self.child_count > 0 else "#3a3a3c")))
        fill_color = QColor("#2c2c2e" if is_dark else "#ffffff")

        # Halo si está seleccionado o hovered
        if self.isSelected() or self._hovered:
            halo_pen = QPen(QColor(base_color.red(), base_color.green(), base_color.blue(), 80), 8)
            painter.setPen(halo_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(self.rect())

        # Círculo principal
        painter.setPen(QPen(base_color, 2.5 if self.child_count == 0 else 3.5))
        painter.setBrush(QBrush(fill_color))
        painter.drawEllipse(self.rect())

        # Icono / Categoría
        icon_str = PLACE_ICONS.get(self.place.category, "📍")
        painter.setPen(QPen(QColor("#ffffff" if is_dark else "#1c1c1e")))
        f_icon = QFont("Segoe UI Emoji", int(self.radius * 0.55))
        painter.setFont(f_icon)
        painter.drawText(QRectF(-self.radius, -self.radius, self.radius * 2, self.radius * 2),
                         Qt.AlignmentFlag.AlignCenter, icon_str)

        # Si contiene estancias/sublugares, dibujar badge de conteo en la esquina superior derecha
        if self.child_count > 0:
            badge_r = 9.0
            bx = self.radius * 0.65
            by = -self.radius * 0.65
            painter.setBrush(QBrush(QColor("#bf5af2")))
            painter.setPen(QPen(QColor("#ffffff"), 1.5))
            painter.drawEllipse(QPointF(bx, by), badge_r, badge_r)
            painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            painter.setPen(QPen(QColor("#ffffff")))
            painter.drawText(QRectF(bx - badge_r, by - badge_r, badge_r * 2, badge_r * 2),
                             Qt.AlignmentFlag.AlignCenter, str(self.child_count))

        # Nombre del Lugar debajo
        f_name = QFont("Segoe UI", 9, QFont.Weight.Bold if self.depth == 0 else QFont.Weight.Normal)
        painter.setFont(f_name)
        painter.setPen(QPen(QColor("#f2f2f7" if is_dark else "#1c1c1e")))
        name_rect = QRectF(-75, self.radius + 4, 150, 30)
        painter.drawText(name_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, self.place.name)



class PlaceLinkItem(QGraphicsItem):
    """Arista gráfica entre dos lugares con estilo según tipo de conexión geográfica."""
    def __init__(self, link: PlaceLink, node_a: PlaceNodeItem, node_b: PlaceNodeItem):
        super().__init__()
        self.link = link
        self.node_a = node_a
        self.node_b = node_b
        self.setZValue(-1)

    def boundingRect(self) -> QRectF:
        p1 = self.node_a.pos()
        p2 = self.node_b.pos()
        return QRectF(p1, p2).normalized().adjusted(-30, -30, 30, 30)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        p1 = self.node_a.pos()
        p2 = self.node_b.pos()

        color_hex = self.link.color or CONNECTION_COLORS.get(self.link.connection_type, "#8e8e93")
        pen_color = QColor(color_hex)

        is_hierarchy = self.link.connection_type == "contiene"
        if is_hierarchy:
            pen_color = QColor("#bf5af2")
            pen_style = Qt.PenStyle.DotLine
            pen_width = 2.2
        elif self.link.connection_type in ["portal", "frontera"]:
            pen_style = Qt.PenStyle.DashLine
            pen_width = 2.0
        else:
            pen_style = Qt.PenStyle.SolidLine
            pen_width = 2.0

        painter.setPen(QPen(pen_color, pen_width, pen_style))
        painter.drawLine(p1, p2)

        # Si tiene etiqueta, dibujarla en el punto medio
        if self.link.label:
            mid = (p1 + p2) / 2
            f = QFont("Segoe UI", 8, QFont.Weight.Bold if is_hierarchy else QFont.Weight.Normal)
            painter.setFont(f)
            painter.setPen(QPen(pen_color))
            painter.drawText(QRectF(mid.x() - 60, mid.y() - 15, 120, 20),
                             Qt.AlignmentFlag.AlignCenter, self.link.label)



class PlaceGraphScene(QGraphicsScene):
    place_selected = pyqtSignal(str)
    place_double_clicked = pyqtSignal(str)

    def mousePressEvent(self, event):
        item = self.itemAt(event.scenePos(), self.views()[0].transform()) if self.views() else None
        if isinstance(item, PlaceNodeItem):
            self.place_selected.emit(item.place.id)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        item = self.itemAt(event.scenePos(), self.views()[0].transform()) if self.views() else None
        if isinstance(item, PlaceNodeItem):
            self.place_double_clicked.emit(item.place.id)
        super().mouseDoubleClickEvent(event)


class PlaceGraphWidget(QWidget):
    """
    Lienzo completo del Grafo de Lugares con barra de herramientas,
    búsqueda, reorganización automática con Spring Layout y zoom.
    """
    place_selected = pyqtSignal(str)
    place_double_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._places: list[Place] = []
        self._links: list[PlaceLink] = []
        self._node_map: dict[str, PlaceNodeItem] = {}
        self._link_items: list[PlaceLinkItem] = []

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar superior
        tb = QFrame()
        tbl = QHBoxLayout(tb)
        tbl.setContentsMargins(12, 8, 12, 8)
        tbl.setSpacing(10)

        tbl.addWidget(QLabel("🗺️ ATLAS DE CONEXIONES"))

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Buscar lugar o estancia...")
        self._search_input.setClearButtonEnabled(True)
        self._search_input.setMaximumWidth(180)
        self._search_input.textChanged.connect(self._on_search)
        tbl.addWidget(self._search_input)

        # Modo de visualización: Red Topológica o Árbol Jerárquico de Estancias
        tbl.addWidget(QLabel("Vista:"))
        self._view_mode_combo = QComboBox()
        self._view_mode_combo.addItem("🌐 Red Geográfica", "network")
        self._view_mode_combo.addItem("🏛️ Árbol de Estancias", "tree")
        self._view_mode_combo.currentIndexChanged.connect(self._on_view_mode_changed)
        tbl.addWidget(self._view_mode_combo)

        tbl.addStretch()

        # Botón Reorganizar (Spring Layout)
        self._btn_layout = QPushButton("⚡ Reorganizar")
        self._btn_layout.setToolTip("Distribuye los lugares de forma armónica usando simulación de fuerzas")
        self._btn_layout.clicked.connect(self.reorganize_layout)
        tbl.addWidget(self._btn_layout)


        # Zoom controls
        btn_zoom_in = QPushButton("➕")
        btn_zoom_in.setFixedWidth(32)
        btn_zoom_in.clicked.connect(lambda: self._view.scale(1.2, 1.2))
        tbl.addWidget(btn_zoom_in)

        btn_zoom_out = QPushButton("➖")
        btn_zoom_out.setFixedWidth(32)
        btn_zoom_out.clicked.connect(lambda: self._view.scale(1 / 1.2, 1 / 1.2))
        tbl.addWidget(btn_zoom_out)

        btn_fit = QPushButton("↺ Ajustar")
        btn_fit.clicked.connect(self._fit_to_view)
        tbl.addWidget(btn_fit)

        layout.addWidget(tb)

        # Escena y Vista
        self._scene = PlaceGraphScene(self)
        self._scene.place_selected.connect(self.place_selected)
        self._scene.place_double_clicked.connect(self.place_double_clicked)

        self._view = QGraphicsView(self._scene)
        self._view.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self._view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self._view.setFrameShape(QFrame.Shape.NoFrame)

        layout.addWidget(self._view, stretch=1)
        self._apply_theme()

    def _apply_theme(self):
        is_dark = ThemeManager.is_dark()
        bg = "#1c1c1e" if is_dark else "#f4f1eb"
        self._view.setBackgroundBrush(QBrush(QColor(bg)))

    def set_data(self, places: list[Place], links: list[PlaceLink]):
        self._places = list(places)
        self._links = list(links)
        self._rebuild_graph()

    def _on_view_mode_changed(self):
        self._rebuild_graph()

    def _rebuild_graph(self):
        self._scene.clear()
        self._node_map.clear()
        self._link_items.clear()

        if not self._places:
            return

        mode = self._view_mode_combo.currentData() if hasattr(self, "_view_mode_combo") else "network"

        # Precalcular mapa de jerarquías y conteo de estancias/sublugares hijos
        parent_map = {p.id: p.parent_place_id for p in self._places}
        children_map = {p.id: [] for p in self._places}
        for p in self._places:
            if p.parent_place_id and p.parent_place_id in children_map:
                children_map[p.parent_place_id].append(p.id)

        # Calcular profundidad (depth) de cada lugar
        depth_map = {}
        for p in self._places:
            d = 0
            cur = p.parent_place_id
            seen = set()
            while cur and cur not in seen:
                seen.add(cur)
                d += 1
                cur = parent_map.get(cur, "")
            depth_map[p.id] = d

        if mode == "tree":
            # ── VISTA JERÁRQUICA: Árbol de Estancias (Raíz arriba o izquierda) ──
            # Encontrar raíces (lugares sin contenedor padre o cuyo padre no existe)
            roots = [p for p in self._places if not p.parent_place_id or p.parent_place_id not in depth_map]
            if not roots:
                roots = list(self._places)

            current_x = 0.0
            x_spacing = 160.0
            y_spacing = 140.0

            def layout_sub_tree(node_id: str, depth: int) -> float:
                nonlocal current_x
                child_ids = children_map.get(node_id, [])
                place_obj = next((p for p in self._places if p.id == node_id), None)
                if not place_obj:
                    return current_x

                if not child_ids:
                    # Hoja (estancia terminal)
                    node_x = current_x
                    current_x += x_spacing
                else:
                    # Padre: ubicar centrado sobre sus estancias hijas
                    child_x_positions = []
                    for cid in child_ids:
                        child_x_positions.append(layout_sub_tree(cid, depth + 1))
                    node_x = sum(child_x_positions) / len(child_x_positions)

                node_y = depth * y_spacing
                node_item = PlaceNodeItem(
                    place=place_obj,
                    x=node_x,
                    y=node_y,
                    depth=depth,
                    child_count=len(child_ids),
                    parent=None
                )
                self._scene.addItem(node_item)
                self._node_map[place_obj.id] = node_item
                return node_x

            for r in roots:
                layout_sub_tree(r.id, 0)
                current_x += 40.0

        else:
            # ── VISTA RED GEOGRÁFICA: Layout Circular inicial o con fuerzas ──
            count = len(self._places)
            radius = max(180, count * 35)
            for i, place in enumerate(self._places):
                angle = (2 * math.pi / count) * i
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
                child_count = len(children_map.get(place.id, []))
                depth = depth_map.get(place.id, 0)
                node = PlaceNodeItem(place, x, y, depth=depth, child_count=child_count)
                self._scene.addItem(node)
                self._node_map[place.id] = node

        # ── Añadir Aristas de Jerarquía Estructural (Padre -> Estancia Hija) ──
        for p in self._places:
            if p.parent_place_id and p.parent_place_id in self._node_map and p.id in self._node_map:
                na = self._node_map[p.parent_place_id]
                nb = self._node_map[p.id]
                # Crear arista visual de contención/estancia
                h_link = PlaceLink(
                    place_id_a=p.parent_place_id,
                    place_id_b=p.id,
                    label="contiene",
                    connection_type="contiene",
                    bidirectional=False
                )
                item = PlaceLinkItem(h_link, na, nb)
                self._scene.addItem(item)
                self._link_items.append(item)

        # ── Añadir Aristas de Conexiones Geográficas Explícitas (PlaceLink) ──
        for link in self._links:
            na = self._node_map.get(link.place_id_a)
            nb = self._node_map.get(link.place_id_b)
            if na and nb:
                item = PlaceLinkItem(link, na, nb)
                self._scene.addItem(item)
                self._link_items.append(item)

        # Ajustar vista
        self._fit_to_view()


    def reorganize_layout(self):
        """Aplica un layout de fuerzas (Spring-Embedder) para distribuir los nodos de forma orgánica."""
        if not self._places or len(self._places) < 2:
            return

        nodes = list(self._node_map.values())
        k = 120.0  # distancia ideal de resorte
        iterations = 50

        # Crear mapa de adyacencias
        adj = {p.id: set() for p in self._places}
        for lk in self._links:
            if lk.place_id_a in adj and lk.place_id_b in adj:
                adj[lk.place_id_a].add(lk.place_id_b)
                adj[lk.place_id_b].add(lk.place_id_a)

        positions = {n.place.id: [n.pos().x(), n.pos().y()] for n in nodes}

        for step in range(iterations):
            disp = {p.id: [0.0, 0.0] for p in self._places}

            # Repulsión entre todos los pares
            for i in range(len(nodes)):
                u_id = nodes[i].place.id
                u_pos = positions[u_id]
                for j in range(i + 1, len(nodes)):
                    v_id = nodes[j].place.id
                    v_pos = positions[v_id]
                    dx = u_pos[0] - v_pos[0]
                    dy = u_pos[1] - v_pos[1]
                    dist = math.hypot(dx, dy) or 0.1
                    force = (k * k) / dist
                    fx = (dx / dist) * force
                    fy = (dy / dist) * force
                    disp[u_id][0] += fx
                    disp[u_id][1] += fy
                    disp[v_id][0] -= fx
                    disp[v_id][1] -= fy

            # Atracción por conexiones
            for lk in self._links:
                if lk.place_id_a in positions and lk.place_id_b in positions:
                    u_pos = positions[lk.place_id_a]
                    v_pos = positions[lk.place_id_b]
                    dx = u_pos[0] - v_pos[0]
                    dy = u_pos[1] - v_pos[1]
                    dist = math.hypot(dx, dy) or 0.1
                    force = (dist * dist) / k
                    fx = (dx / dist) * force
                    fy = (dy / dist) * force
                    disp[lk.place_id_a][0] -= fx
                    disp[lk.place_id_a][1] -= fy
                    disp[lk.place_id_b][0] += fx
                    disp[lk.place_id_b][1] += fy

            # Aplicar desplazamiento amortiguado
            temp = 1.0 - (step / iterations)
            for p_id, d in disp.items():
                positions[p_id][0] += d[0] * 0.05 * temp
                positions[p_id][1] += d[1] * 0.05 * temp

        # Actualizar posiciones en la escena
        for n in nodes:
            pos = positions[n.place.id]
            n.setPos(pos[0], pos[1])

        self._scene.update()
        self._fit_to_view()

    def _on_search(self, text: str):
        query = text.lower().strip()
        for node in self._node_map.values():
            match = not query or query in node.place.name.lower()
            node.setSelected(match if query else False)
            node.setOpacity(1.0 if match else 0.25)

    def _fit_to_view(self):
        items_rect = self._scene.itemsBoundingRect()
        if not items_rect.isEmpty():
            self._view.fitInView(items_rect.adjusted(-50, -50, 50, 50), Qt.AspectRatioMode.KeepAspectRatio)
