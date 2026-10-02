"""
Mapa Mental del Universo — QGraphicsScene + QGraphicsView con NetworkX spring_layout.
Permite conectar elementos de distintas Obras, arrastrar nodos, zoom, pan,
y doble clic en un nodo → abre ese Capítulo en el editor.
"""

import math
import logging
from PyQt6.QtWidgets import (QGraphicsScene, QGraphicsView, QGraphicsPathItem,
                             QGraphicsTextItem, QGraphicsItem, QWidget,
                             QVBoxLayout, QLabel, QHBoxLayout,
                             QPushButton, QLineEdit, QCompleter, QMenu,
                             QMessageBox, QInputDialog)
from PyQt6.QtCore import Qt, QPointF, QTimer, pyqtSignal, QRectF, QStringListModel
from PyQt6.QtGui import QBrush, QPen, QColor, QFont, QPainter, QPainterPath, QPolygonF
from core.models import UniverseMetadata

log = logging.getLogger(__name__)

class UniverseMapScene(QGraphicsScene):
    """Escena con grid dots y anillos orbitales de referencia."""

    # Lista de (cx, cy, radio) para los anillos de cada sistema
    orbital_rings: list[tuple[float, float, float]] = []

    def drawBackground(self, painter: QPainter | None, rect: QRectF):
        if painter is None: return
        super().drawBackground(painter, rect)
        
        from core.theme_manager import ThemeManager
        is_dark = ThemeManager.is_dark()
        
        # ---- Grid dots ----
        grid_color = "#252527" if is_dark else "#d1d5db"
        painter.setPen(QPen(QColor(grid_color), 1.2))
        grid_size = 40
        left = int(rect.left()) - (int(rect.left()) % grid_size)
        top  = int(rect.top())  - (int(rect.top())  % grid_size)
        points = []
        for x in range(left, int(rect.right()), grid_size):
            for y in range(top, int(rect.bottom()), grid_size):
                points.append(QPointF(float(x), float(y)))
        if points:
            painter.drawPoints(points)
        
        # ---- Anillos orbitales de cada sistema ----
        if self.orbital_rings:
            ring_col = QColor("#ffffff" if is_dark else "#000000")
            ring_col.setAlphaF(0.12)  # visible pero sutil
            pen = QPen(ring_col, 1.2, Qt.PenStyle.DashLine)
            pen.setDashPattern([4, 6])
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            for cx, cy, r in self.orbital_rings:
                painter.drawEllipse(QPointF(cx, cy), r, r)

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
    "universe": 62,   # enorme y prominente
    "obra":     46,   # sol del sistema
    "libro":    30,   # planeta
    "chapter":  18,   # luna
    "media":    16,
}


class MapNode(QGraphicsPathItem):
    """Nodo fijo en el mapa mental. Siempre circular, tamaño según jerarquía."""

    def __init__(self, node_id: str, node_type: str, label: str,
                 x: float, y: float, radius: float):
        super().__init__()
        self.node_id = node_id
        self.node_type = node_type
        self.setPos(x, y)

        # Siempre circular
        path = QPainterPath()
        path.addEllipse(-radius, -radius, radius * 2, radius * 2)
        self.setPath(path)

        bg  = QColor(NODE_COLORS.get(node_type, "#2c2c2e"))
        self._color = bg
        brd = QColor(NODE_BORDER_COLORS.get(node_type, "#636366"))
        self.setBrush(QBrush(bg))
        pen = QPen(brd, 2 if node_type != "universe" else 3)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        self.setPen(pen)

        # NO movable – el layout es fijo
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)  # Habilitar hover
        self.setZValue(2)

        self.setToolTip(label)  # Tooltip limpio con el título completo

        # ---- Etiqueta centrada dentro del nodo ----
        txt_color = NODE_TEXT_COLORS.get(node_type, "#f2f2f7")
        self._full_label = label  # guardar título completo

        # Tamaño de fuente proporcional al radio; mínimo 7pt
        font_size = max(7, int(radius * 0.40))
        font = QFont("Segoe UI", font_size)
        font.setBold(True)

        # Calcular cuántos caracteres caben en el diámetro
        # aprox: cada carácter ocupa ~font_size * 0.65 px
        char_w = font_size * 0.65
        # Usar 95% del diámetro y ser más generosos (+2 chars de margen)
        max_chars = max(4, int((radius * 2 * 0.95) / char_w))
        self._display_label = label if len(label) <= max_chars else label[:max_chars - 1] + "…"
        self._radius = radius
        self._txt_color = QColor(txt_color)
        self._font = font

        self._label = QGraphicsTextItem(self._display_label, self)
        self._label.setDefaultTextColor(self._txt_color)
        self._label.setFont(font)
        br = self._label.boundingRect()
        self._label.setPos(-br.width() / 2, -br.height() / 2)

        self.edges: list = []

        # Glow effect
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        self._shadow = QGraphicsDropShadowEffect()
        self._shadow.setBlurRadius(20)
        self._shadow.setOffset(0, 0)
        self._shadow.setColor(QColor(0, 0, 0, 0))
        self.setGraphicsEffect(self._shadow)

    def set_focused(self, focused: bool, dimmed: bool):
        if focused:
            self._shadow.setColor(self._color)
            self._shadow.setBlurRadius(40)
            self.setZValue(10)
            self.setOpacity(1.0)
        elif dimmed:
            self._shadow.setColor(QColor(0, 0, 0, 0))
            self.setZValue(1)
            self.setOpacity(0.18)
        else:
            self._shadow.setColor(QColor(0, 0, 0, 0))
            self.setZValue(2)
            self.setOpacity(1.0)

    def hoverEnterEvent(self, event):
        """Al pasar el mouse: mostrar título completo sobre el nodo."""
        self._label.setPlainText(self._full_label)
        br = self._label.boundingRect()
        self._label.setPos(-br.width() / 2, -br.height() / 2)
        # Activar brillo sutil
        self._shadow.setColor(self._color)
        self._shadow.setBlurRadius(28)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """Al salir el mouse: restaurar etiqueta truncada."""
        self._label.setPlainText(self._display_label)
        br = self._label.boundingRect()
        self._label.setPos(-br.width() / 2, -br.height() / 2)
        # Apagar brillo si no está en foco
        self._shadow.setColor(QColor(0, 0, 0, 0))
        super().hoverLeaveEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            for edge in self.edges:
                edge.update_position()
        return super().itemChange(change, value)

# Alias para compatibilidad con código existente
DraggableNode = MapNode


class BranchEdge(QGraphicsPathItem):
    """Arista entre dos nodos con curvas Bézier y soporte para enlaces transversales."""

    def __init__(self, source: DraggableNode, target: DraggableNode, label: str = ""):
        super().__init__()
        self.source = source
        self.target = target
        self._is_link = bool(label)
        
        # Grosor y color de línea por nivel jerárquico del nodo origen
        src_type = source.node_type
        if src_type == "universe":
            line_w, line_alpha = 2.5, 0.75
        elif src_type == "obra":
            line_w, line_alpha = 1.8, 0.60
        else:
            line_w, line_alpha = 1.2, 0.45

        from core.theme_manager import ThemeManager
        is_dark = ThemeManager.is_dark()
        
        if self._is_link:
            color = QColor("#ff375f" if is_dark else "#ff2d55") # Neón
            pen = QPen(color, 2.0, Qt.PenStyle.DashLine)
        else:
            base = QColor("#ffffff" if is_dark else "#000000")
            base.setAlphaF(line_alpha)
            pen = QPen(base, line_w, Qt.PenStyle.SolidLine)
            
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        self.setPen(pen)
        self.setZValue(1)

        self._label_item = None
        if label:
            self._label_item = QGraphicsTextItem(label, self)
            self._label_item.setDefaultTextColor(QColor("#ff375f" if is_dark else "#ff2d55"))
            self._label_item.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))

        source.edges.append(self)
        target.edges.append(self)
        self.update_position()

    def set_focused(self, focused: bool, dimmed: bool):
        opacity = 1.0
        if focused:
            self.setZValue(5)
            pen = self.pen()
            pen.setWidthF(3.0)
            self.setPen(pen)
        elif dimmed:
            opacity = 0.15
            self.setZValue(0)
            pen = self.pen()
            pen.setWidthF(1.5)
            self.setPen(pen)
        else:
            self.setZValue(1)
            pen = self.pen()
            pen.setWidthF(1.5 if not self._is_link else 2.0)
            self.setPen(pen)
            
        self.setOpacity(opacity)
        if self._label_item:
            self._label_item.setOpacity(opacity)

    def update_position(self):
        p1 = self.source.scenePos()
        p2 = self.target.scenePos()
        
        path = QPainterPath()
        path.moveTo(p1)
        path.lineTo(p2)
        self.setPath(path)
        
        if self._label_item:
            mid = QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
            self._label_item.setPos(mid)


class UniverseMapView(QGraphicsView):
    """Vista del mapa mental con zoom y pan."""
    chapter_requested = pyqtSignal(str)
    node_clicked = pyqtSignal(str)
    background_clicked = pyqtSignal()

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
            
    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if isinstance(item, DraggableNode):
            self.node_clicked.emit(item.node_id)
        elif isinstance(item, QGraphicsTextItem):
            parent = item.parentItem()
            if isinstance(parent, DraggableNode):
                self.node_clicked.emit(parent.node_id)
        else:
            self.background_clicked.emit()
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        item = self.itemAt(event.pos())
        if isinstance(item, DraggableNode) and item.node_type == "chapter":
            self.chapter_requested.emit(item.node_id)
        elif isinstance(item, QGraphicsTextItem):
            parent = item.parentItem()
            if isinstance(parent, DraggableNode) and parent.node_type == "chapter":
                self.chapter_requested.emit(parent.node_id)
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        widget = self.parent()
        if not isinstance(widget, UniverseMapWidget):
            super().contextMenuEvent(event)
            return

        # Si se hace clic derecho en una arista/línea sutil existente
        if isinstance(item, BranchEdge) and item._is_link:
            menu = QMenu(self)
            action_del = menu.addAction(f"❌ Eliminar enlace: {item.source._full_label} ↔ {item.target._full_label}")
            if menu.exec(event.globalPos()) == action_del:
                widget.remove_link_between(item.source.node_id, item.target.node_id)
            return

        node = None
        if isinstance(item, DraggableNode):
            node = item
        elif isinstance(item, QGraphicsTextItem) and isinstance(item.parentItem(), DraggableNode):
            node = item.parentItem()

        if node and node.node_id != "universe_root":
            menu = QMenu(self)
            action_link = menu.addAction(f"🔗 Conectar '{node._full_label}' con...")
            
            # Buscar si el nodo ya tiene enlaces sutiles activos para ofrecer eliminación
            existing_links = widget.get_links_for_node(node.node_id)
            del_actions = {}
            if existing_links:
                menu.addSeparator()
                sub_menu = menu.addMenu("❌ Eliminar conexión sutil...")
                for link, other_label, other_id in existing_links:
                    lbl = f"Eliminar: {node._full_label} ↔ {other_label}"
                    act = sub_menu.addAction(lbl)
                    del_actions[act] = (link, other_id)

            selected_action = menu.exec(event.globalPos())
            if selected_action == action_link:
                widget.start_linking_node(node.node_id)
            elif selected_action in del_actions:
                link, other_id = del_actions[selected_action]
                widget.remove_link(link)
        else:
            super().contextMenuEvent(event)


class UniverseMapWidget(QWidget):
    """Widget completo del mapa mental del universo."""
    chapter_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._meta: UniverseMetadata | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        header = QHBoxLayout()
        lbl = QLabel("MAPA MENTAL DEL UNIVERSO")
        lbl.setStyleSheet("font-weight:700; font-size:11px; letter-spacing:1px;")
        header.addWidget(lbl)

        self._search_bar = QLineEdit()
        self._search_bar.setPlaceholderText("Buscar capítulo, libro u obra...")
        self._search_bar.setMaximumWidth(250)
        self._search_bar.setStyleSheet("""
            QLineEdit {
                background: rgba(0, 0, 0, 0.1);
                border: 1px solid rgba(128, 128, 128, 0.3);
                border-radius: 4px;
                padding: 4px 8px;
            }
        """)
        self._completer_model = QStringListModel()
        self._completer = QCompleter(self._completer_model, self)
        self._completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._search_bar.setCompleter(self._completer)
        self._search_bar.returnPressed.connect(self._on_search_entered)
        self._completer.activated.connect(self._on_search_activated)
        
        header.addStretch()
        header.addWidget(self._search_bar)

        btn_fit = QPushButton("Ajustar vista")
        btn_fit.clicked.connect(self._fit_view)
        header.addWidget(btn_fit)
        layout.addLayout(header)

        self._scene = UniverseMapScene(self)
        self._view = UniverseMapView(self._scene, self)
        self._view.chapter_requested.connect(self.chapter_requested)
        self._view.node_clicked.connect(self._on_node_clicked)
        self._view.background_clicked.connect(self._on_background_clicked)
        layout.addWidget(self._view)

        self._nodes: dict[str, DraggableNode] = {}
        self._edges: list[BranchEdge] = []
        self._parents: dict[str, str] = {} # child_id -> parent_id
        self._node_names: dict[str, str] = {} # lowercase_title -> node_id
        self._pending_fit = False

    def start_linking_node(self, source_id: str):
        """Abre diálogo para crear un enlace transversal desde source_id a otro nodo con orden jerárquico limpio sin emojis."""
        if not self._meta:
            return

        source_node = self._nodes.get(source_id)
        if not source_node:
            return

        display_labels = []
        id_list = []

        # Recorrer secuencialmente en orden de historia (Obra -> sus Libros -> sus Capítulos)
        for o_idx, obra in enumerate(self._meta.obras):
            if obra.id != source_id and obra.id != "universe_root":
                display_labels.append(f"OBRA: {obra.title}")
                id_list.append(obra.id)

            for l_idx, libro in enumerate(obra.libros):
                if libro.id != source_id and libro.id != "universe_root":
                    display_labels.append(f"  └─ Libro: {libro.title}  [{obra.title}]")
                    id_list.append(libro.id)

                for c_idx, cap in enumerate(libro.capitulos):
                    if cap.id != source_id and cap.id != "universe_root":
                        display_labels.append(f"      └─ Capítulo: {cap.title}  [{obra.title} / {libro.title}]")
                        id_list.append(cap.id)

        if not display_labels:
            QMessageBox.information(self, "Conectar Nodos", "No hay otros nodos disponibles para conectar.")
            return

        dest_display, ok1 = QInputDialog.getItem(
            self, "Conectar Nodos",
            f"Selecciona el nodo a conectar con '{source_node._full_label}':",
            display_labels, 0, False
        )
        if not ok1 or not dest_display:
            return

        dest_index = display_labels.index(dest_display)
        dest_id = id_list[dest_index]
        dest_node = self._nodes.get(dest_id)
        dest_clean_name = dest_node._full_label if dest_node else dest_display

        rel_label, ok2 = QInputDialog.getText(
            self, "Etiqueta del Enlace",
            f"Relación sutil entre '{source_node._full_label}' y '{dest_clean_name}' (opcional):",
            QLineEdit.EchoMode.Normal, "Conexión sutil"
        )
        if not ok2:
            return

        from core.models import UniverseLink
        new_link = UniverseLink(source_id=source_id, target_id=dest_id, label=rel_label.strip())
        self._meta.universe_links.append(new_link)

        # Reconstruir el mapa para reflejar el nuevo enlace neón
        self.build_from_metadata(self._meta)

        # Persistir cambios en el proyecto si es posible
        parent_window = self.window()
        if hasattr(parent_window, "save_project"):
            parent_window.save_project()

        QMessageBox.information(self, "Enlace Creado", f"Se ha creado el enlace sutil entre '{source_node._full_label}' y '{dest_clean_name}'.")

    def get_links_for_node(self, node_id: str) -> list[tuple]:
        """Devuelve los enlaces transversales conectados a este nodo en formato (UniverseLink, other_label, other_id)."""
        if not self._meta or not self._meta.universe_links:
            return []
        res = []
        for link in self._meta.universe_links:
            other_id = None
            if link.source_id == node_id:
                other_id = link.target_id
            elif link.target_id == node_id:
                other_id = link.source_id

            if other_id and other_id in self._nodes:
                other_label = self._nodes[other_id]._full_label
                res.append((link, other_label, other_id))
        return res

    def remove_link(self, link):
        """Elimina un objeto UniverseLink de la metadata y actualiza el mapa."""
        if not self._meta or link not in self._meta.universe_links:
            return
        self._meta.universe_links.remove(link)
        self.build_from_metadata(self._meta)
        parent_window = self.window()
        if hasattr(parent_window, "save_project"):
            parent_window.save_project()

    def remove_link_between(self, src_id: str, dst_id: str):
        """Elimina el enlace transversal entre dos nodos específicos."""
        if not self._meta:
            return
        to_remove = [
            l for l in self._meta.universe_links
            if (l.source_id == src_id and l.target_id == dst_id) or
               (l.source_id == dst_id and l.target_id == src_id)
        ]
        for l in to_remove:
            self._meta.universe_links.remove(l)
        if to_remove:
            self.build_from_metadata(self._meta)
            parent_window = self.window()
            if hasattr(parent_window, "save_project"):
                parent_window.save_project()

    def _on_search_entered(self):
        self._navigate_to_node(self._search_bar.text())
        
    def _on_search_activated(self, text: str):
        self._navigate_to_node(text)
        
    def _navigate_to_node(self, query: str):
        q = query.strip().lower()
        node_id = self._node_names.get(q)
        if node_id and node_id in self._nodes:
            # Seleccionar nodo y enfocar
            self._on_node_clicked(node_id)
            node = self._nodes[node_id]
            # Centrar vista animada o directa (usamos centerOn)
            self._view.centerOn(node)

    def _on_node_clicked(self, node_id: str):
        # Determinar toda la rama: ascendientes y descendientes
        branch_ids = {node_id}
        
        # Hacia arriba (ancestros)
        curr = node_id
        while curr in self._parents:
            curr = self._parents[curr]
            branch_ids.add(curr)
            
        # Hacia abajo (descendientes)
        def get_descendants(nid: str):
            for child, parent in self._parents.items():
                if parent == nid and child not in branch_ids:
                    branch_ids.add(child)
                    get_descendants(child)
        get_descendants(node_id)
        
        # Aplicar foco a los nodos
        for nid, node in self._nodes.items():
            if nid in branch_ids:
                node.set_focused(True, False)
            else:
                node.set_focused(False, True)
                
        # Aplicar foco a las aristas
        for edge in self._edges:
            if edge.source.node_id in branch_ids and edge.target.node_id in branch_ids:
                edge.set_focused(True, False)
            else:
                edge.set_focused(False, True)

    def _on_background_clicked(self):
        for node in self._nodes.values():
            node.set_focused(False, False)
        for edge in self._edges:
            edge.set_focused(False, False)

    def showEvent(self, a0):
        """Al mostrarse, ajustar la vista con un pequeño retardo para que
        el layout haya terminado de calcularse."""
        event = a0
        super().showEvent(event)
        if self._pending_fit:
            QTimer.singleShot(80, self._fit_view)

    def _fit_view(self):
        rect = self._scene.sceneRect()
        if not rect.isNull():
            self._view.fitInView(rect.adjusted(-80, -80, 80, 80),
                                 Qt.AspectRatioMode.KeepAspectRatio)

    def build_from_metadata(self, meta: UniverseMetadata):
        """Construye el mapa en layout RADIAL HACIA AFUERA:
        - Universo en el centro.
        - Obras en anillo 1, cada una con su sector angular.
        - Libros en anillo 2, dentro del sector de su Obra.
        - Capítulos en anillo 3, dentro del subsector de su Libro.
        Todo se expande desde el centro hacia el exterior.
        """
        self._meta = meta
        self._scene.clear()
        self._nodes.clear()
        self._edges.clear()
        self._parents.clear()
        self._node_names.clear()

        from core.theme_manager import ThemeManager
        bg_col = "#1c1c1e" if ThemeManager.is_dark() else "#f5f0ea"
        self._view.setBackgroundBrush(QBrush(QColor(bg_col)))

        uid = "universe_root"
        pos:         dict[str, tuple[float, float]] = {uid: (0.0, 0.0)}
        node_types:  dict[str, str]                 = {uid: "universe"}
        node_labels: dict[str, str]                 = {uid: meta.title}
        edges:       list[tuple[str, str, str]]     = []

        # ---- Radios de cada anillo ----
        R1 = 200   # Obras
        R2 = 390   # Libros
        R3 = 560   # Capítulos

        # Anillos concéntricos limpios centrados en el universo
        self._scene.orbital_rings = [
            (0.0, 0.0, float(R1)),
            (0.0, 0.0, float(R2)),
            (0.0, 0.0, float(R3)),
        ]

        n_obras = max(len(meta.obras), 1)
        sector_size = 2 * math.pi / n_obras  # sector angular por Obra

        for i, obra in enumerate(meta.obras):
            # Centro del sector de esta Obra
            obra_sector = 2 * math.pi * i / n_obras - math.pi / 2

            # Posición de la Obra en R1
            pos[obra.id]         = (math.cos(obra_sector) * R1,
                                    math.sin(obra_sector) * R1)
            node_types[obra.id]  = "obra"
            node_labels[obra.id] = obra.title
            edges.append((uid, obra.id, ""))
            self._parents[obra.id] = uid

            n_libros = len(obra.libros)
            libro_spread = sector_size * 0.75  # 75% del sector para los libros

            for j, libro in enumerate(obra.libros):
                # Ángulo del libro dentro del sector de su Obra
                if n_libros == 1:
                    libro_angle = obra_sector
                else:
                    libro_angle = (obra_sector - libro_spread / 2
                                   + libro_spread * (j + 0.5) / n_libros)

                pos[libro.id]         = (math.cos(libro_angle) * R2,
                                         math.sin(libro_angle) * R2)
                node_types[libro.id]  = "libro"
                node_labels[libro.id] = libro.title
                edges.append((obra.id, libro.id, ""))
                self._parents[libro.id] = obra.id

                n_caps = len(libro.capitulos)
                # Subsector del libro: proporción del sector total
                lib_sector_w = (libro_spread / max(n_libros, 1)) * 0.80

                for k, cap in enumerate(libro.capitulos):
                    if n_caps == 1:
                        cap_angle = libro_angle
                    else:
                        cap_angle = (libro_angle - lib_sector_w / 2
                                     + lib_sector_w * (k + 0.5) / n_caps)

                    pos[cap.id]         = (math.cos(cap_angle) * R3,
                                           math.sin(cap_angle) * R3)
                    node_types[cap.id]  = "chapter"
                    node_labels[cap.id] = cap.title
                    edges.append((libro.id, cap.id, ""))
                    self._parents[cap.id] = libro.id

        # Links transversales del universo
        all_ids = set(node_types.keys())
        for link in meta.universe_links:
            if link.source_id in all_ids and link.target_id in all_ids:
                edges.append((link.source_id, link.target_id, link.label))

        if len(node_types) <= 1:
            return

        search_list = []

        # Crear nodos
        for nid, (px, py) in pos.items():
            ntype  = node_types.get(nid, "chapter")
            label  = node_labels.get(nid, nid[:8])
            radius = NODE_SIZES.get(ntype, 20)
            node_item = DraggableNode(nid, ntype, label, px, py, radius)
            self._scene.addItem(node_item)
            self._nodes[nid] = node_item

            if ntype != "universe":
                self._node_names[label.lower()] = nid
                search_list.append(label)

        self._completer_model.setStringList(search_list)

        # Crear aristas
        for src, dst, label in edges:
            if src in self._nodes and dst in self._nodes:
                edge = BranchEdge(self._nodes[src], self._nodes[dst], label)
                self._scene.addItem(edge)
                self._edges.append(edge)

        # Ajustar vista
        self._pending_fit = True
        QTimer.singleShot(50, self._fit_view)

