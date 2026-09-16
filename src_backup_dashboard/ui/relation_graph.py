"""
Grafo de Relaciones entre Personajes — Aura Writer.
Aristas elegantes: color + estilo de línea únicos por tipo de relación.
Doble clic en nodo → emite señal character_focused(char_id).
"""

import logging
import math
from PyQt6.QtWidgets import (QGraphicsScene, QGraphicsView, QGraphicsEllipseItem,
                             QGraphicsTextItem, QGraphicsPathItem, QGraphicsLineItem,
                             QGraphicsItem, QGraphicsRectItem,
                             QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
                             QComboBox, QPushButton)
from PyQt6.QtCore import Qt, QPointF, QRectF, QTimer, pyqtSignal
from PyQt6.QtGui import (QBrush, QPen, QColor, QFont, QPainter,
                         QPainterPath, QLinearGradient)
import networkx as nx

from core.models import (UniverseMetadata, Character, CharacterRelation,
                         RELATION_COLORS, RELATION_ICONS, RELATION_TYPES)

log = logging.getLogger(__name__)


# ── Paleta de 20 colores vibrantes para personajes ────────────────────
# Se asigna uno por cada personaje (por índice circular), siempre visibles
CHARACTER_PALETTE = [
    "#5e5ce6", "#bf5af2", "#ff375f", "#ff9f0a", "#ffd60a",
    "#30d158", "#32ade6", "#0a84ff", "#ac8e68", "#636366",
    "#ff6b81", "#a29bfe", "#fd79a8", "#6c5ce7", "#00b894",
    "#e17055", "#74b9ff", "#55efc4", "#fdcb6e", "#dfe6e9",
]


# ── Estilos de línea por tipo ──────────────────────────────────────────────
# Cada tipo tiene: color, penStyle, width_factor, etiqueta_display
RELATION_STYLES: dict[str, dict] = {
    "pareja": {
        "color":  "#ff79c6",        # rosa fucsia
        "style":  Qt.PenStyle.SolidLine,
        "width":  2.8,
        "dash":   None,
    },
    "familiar": {
        "color":  "#50fa7b",        # verde esmeralda
        "style":  Qt.PenStyle.DashLine,
        "width":  2.2,
        "dash":   [8, 4],
    },
    "descendiente": {
        "color":  "#8be9fd",        # cian claro
        "style":  Qt.PenStyle.DotLine,
        "width":  2.0,
        "dash":   [2, 4],
    },
    "rival": {
        "color":  "#ff5555",        # rojo vibrante
        "style":  Qt.PenStyle.DashDotLine,
        "width":  3.0,
        "dash":   [10, 4, 2, 4],
    },
    "mentor": {
        "color":  "#bd93f9",        # púrpura lavanda
        "style":  Qt.PenStyle.CustomDashLine,
        "width":  2.4,
        "dash":   [12, 3, 3, 3],
    },
    "amigo": {
        "color":  "#f1fa8c",        # amarillo cálido
        "style":  Qt.PenStyle.CustomDashLine,
        "width":  1.8,
        "dash":   [6, 3],
    },
    "otro": {
        "color":  "#6272a4",        # gris pizarrón
        "style":  Qt.PenStyle.DotLine,
        "width":  1.4,
        "dash":   [2, 6],
    },
}


def _make_pen(relation_type: str, intensity: int) -> QPen:
    """Construye un QPen premium para el tipo y nivel de intensidad dados."""
    style = RELATION_STYLES.get(relation_type, RELATION_STYLES["otro"])
    color = QColor(style["color"])
    width = style["width"] * (0.7 + intensity * 0.12)   # escala suave

    pen = QPen(color, width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)

    if style["style"] == Qt.PenStyle.CustomDashLine and style["dash"]:
        pen.setStyle(Qt.PenStyle.CustomDashLine)
        pen.setDashPattern(style["dash"])
    else:
        pen.setStyle(style["style"])

    return pen


class CharacterNode(QGraphicsEllipseItem):
    """Nodo circular de un personaje. Emite signal al doble clic via escena."""

    def __init__(self, char: Character, radius: float, obra_color: str,
                 is_crossover: bool, x: float, y: float):
        super().__init__(-radius, -radius, radius * 2, radius * 2)
        self.char_id = char.id
        self.char_name = char.name
        self.setPos(x, y)

        # Fondo del nodo con color de obra
        color = QColor(obra_color)
        self.setBrush(QBrush(color.lighter(125)))

        if is_crossover:
            # Borde dorado punteado para crossovers
            pen = QPen(QColor("#f1fa8c"), 3, Qt.PenStyle.DashLine)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        else:
            pen = QPen(color.darker(150), 2, Qt.PenStyle.SolidLine)
        self.setPen(pen)

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setZValue(2)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)

        # Tooltip
        tooltip_parts = [f"[{char.role}] {char.name}" if char.role else char.name]
        if char.description:
            tooltip_parts.append(char.description[:120])
        self.setToolTip("\n".join(tooltip_parts))

        # Iniciales del personaje
        initials = "".join(w[0].upper() for w in char.name.split()[:2]) if char.name else "?"
        lbl = QGraphicsTextItem(initials, self)
        lbl.setDefaultTextColor(Qt.GlobalColor.white)
        font = QFont("Segoe UI", max(8, int(radius * 0.5)))
        font.setBold(True)
        lbl.setFont(font)
        br = lbl.boundingRect()
        lbl.setPos(-br.width() / 2, -br.height() / 2)

        # Nombre completo debajo con sombra suave
        name_lbl = QGraphicsTextItem(char.name, self)
        name_lbl.setDefaultTextColor(QColor("#f8f8f2"))
        name_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        nbr = name_lbl.boundingRect()
        name_lbl.setPos(-nbr.width() / 2, radius + 3)

        self.edges: list = []

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            for edge in self.edges:
                edge.update_position()
        return super().itemChange(change, value)

    def mouseDoubleClickEvent(self, event):
        scene = self.scene()
        if scene and hasattr(scene, "_node_double_clicked"):
            scene._node_double_clicked(self.char_id)
        super().mouseDoubleClickEvent(event)


class RelationEdge(QGraphicsLineItem):
    """
    Arista entre personajes.
    Cada tipo de relación tiene color + estilo de línea únicos.
    Halo semitransparente para mejor visibilidad sobre el fondo oscuro.
    """

    def __init__(self, source: CharacterNode, target: CharacterNode,
                 label: str, intensity: int, relation_type: str = "otro"):
        super().__init__()
        self.source = source
        self.target = target
        self.relation_type = relation_type

        main_pen = _make_pen(relation_type, intensity)
        self.setPen(main_pen)
        self.setZValue(1)

        # Halo (línea más gruesa y semitransparente debajo)
        self._halo = QGraphicsLineItem()
        style_info = RELATION_STYLES.get(relation_type, RELATION_STYLES["otro"])
        halo_color = QColor(style_info["color"])
        halo_color.setAlphaF(0.18)
        halo_pen = QPen(halo_color, main_pen.widthF() * 4, Qt.PenStyle.SolidLine)
        halo_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self._halo.setPen(halo_pen)
        self._halo.setZValue(0)

        source.edges.append(self)
        target.edges.append(self)

        # Etiqueta con caja de fondo
        self._label_bg  = None
        self._label_item = None
        if label:
            icon = RELATION_ICONS.get(relation_type, "")
            display = f" {icon} {label} " if icon else f" {label} "
            self._label_item = QGraphicsTextItem(display)
            txt_color = QColor(style_info["color"]).lighter(140)
            self._label_item.setDefaultTextColor(txt_color)
            lbl_font = QFont("Segoe UI", 8, QFont.Weight.Bold)
            self._label_item.setFont(lbl_font)
            self._label_item.setZValue(3)

            # Fondo de la etiqueta
            self._label_bg = QGraphicsRectItem()
            bg_color = QColor("#1e1e2e")
            bg_color.setAlphaF(0.82)
            self._label_bg.setBrush(QBrush(bg_color))
            border_color = QColor(style_info["color"])
            border_color.setAlphaF(0.55)
            self._label_bg.setPen(QPen(border_color, 1))
            self._label_bg.setZValue(2)

        self.update_position()

    def add_to_scene(self, scene):
        """Añade el halo y la etiqueta a la escena."""
        scene.addItem(self._halo)
        if self._label_bg:
            scene.addItem(self._label_bg)
        if self._label_item:
            scene.addItem(self._label_item)

    def update_position(self):
        p1 = self.source.scenePos()
        p2 = self.target.scenePos()
        self.setLine(p1.x(), p1.y(), p2.x(), p2.y())
        self._halo.setLine(p1.x(), p1.y(), p2.x(), p2.y())
        if self._label_item:
            mid_x = (p1.x() + p2.x()) / 2
            mid_y = (p1.y() + p2.y()) / 2
            br = self._label_item.boundingRect()
            self._label_item.setPos(mid_x - br.width() / 2, mid_y - br.height() / 2)
            self._label_bg.setRect(
                mid_x - br.width() / 2 - 2,
                mid_y - br.height() / 2 - 1,
                br.width() + 4,
                br.height() + 2
            )


class GraphScene(QGraphicsScene):
    """Escena personalizada que emite señal al hacer doble clic en un nodo."""
    character_focused = pyqtSignal(str)  # char_id

    def _node_double_clicked(self, char_id: str):
        self.character_focused.emit(char_id)


class RelationGraphView(QGraphicsView):
    """Vista del grafo con zoom y pan."""

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


class RelationGraphWidget(QWidget):
    """Widget completo del grafo de relaciones entre personajes."""
    character_focused = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 0)
        layout.setSpacing(6)

        # ── Header con filtro ───────────────────────────────────
        header = QHBoxLayout()

        lbl = QLabel("RELACIONES ENTRE PERSONAJES")
        lbl.setStyleSheet("font-weight:700; font-size:11px; letter-spacing:1px;")
        header.addWidget(lbl)
        header.addStretch()

        self.filter_combo = QComboBox()
        self.filter_combo.setMinimumWidth(200)
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        header.addWidget(QLabel("Filtrar:"))
        header.addWidget(self.filter_combo)

        btn_fit = QPushButton("Ajustar")
        btn_fit.clicked.connect(self._fit_view)
        header.addWidget(btn_fit)

        layout.addLayout(header)

        # ── Escena y vista ───────────────────────────────────────────
        self._scene = GraphScene(self)
        self._scene.character_focused.connect(self.character_focused)
        self._view = RelationGraphView(self._scene, self)
        layout.addWidget(self._view)

        # ── Leyenda visual con muestra de línea real ─────────────────
        legend_frame = QFrame()
        legend_row = QHBoxLayout(legend_frame)
        legend_row.setContentsMargins(8, 3, 8, 3)
        legend_row.setSpacing(0)

        for rtype in RELATION_TYPES:
            info  = RELATION_STYLES.get(rtype, RELATION_STYLES["otro"])
            color = info["color"]
            icon  = RELATION_ICONS.get(rtype, "")

            pill = QFrame()
            pill.setFixedHeight(26)
            pill_layout = QHBoxLayout(pill)
            pill_layout.setContentsMargins(6, 2, 8, 2)
            pill_layout.setSpacing(5)

            line_sample = _LegendLine(color, info["style"], info["dash"], info["width"])
            line_sample.setFixedSize(34, 12)

            text_lbl = QLabel(f"{icon} {rtype.capitalize()}")
            text_lbl.setStyleSheet(f"color:{color}; font-size:10px; font-weight:bold;")

            pill_layout.addWidget(line_sample)
            pill_layout.addWidget(text_lbl)
            legend_row.addWidget(pill)

        legend_row.addStretch()
        layout.addWidget(legend_frame)

        self._meta: UniverseMetadata | None = None
        self._pending_fit = False

    def showEvent(self, event):
        """Al mostrarse (ventana emergente), ajustar la vista con retardo."""
        super().showEvent(event)
        if self._pending_fit:
            QTimer.singleShot(80, self._fit_view)

    def _fit_view(self):
        rect = self._scene.sceneRect()
        if not rect.isNull():
            self._view.fitInView(rect.adjusted(-70, -70, 70, 70),
                                 Qt.AspectRatioMode.KeepAspectRatio)

    def build_from_metadata(self, meta: UniverseMetadata):
        """Construye el grafo y los filtros a partir de los metadatos."""
        self._meta = meta
        self._populate_filters(meta)
        self._build_graph(meta)
        self._pending_fit = True
        QTimer.singleShot(60, self._fit_view)

    def _populate_filters(self, meta: UniverseMetadata):
        self.filter_combo.blockSignals(True)
        self.filter_combo.clear()
        self.filter_combo.addItem("Todas las Obras", "all")
        for obra in meta.obras:
            self.filter_combo.addItem(f"📖 {obra.title}", f"obra:{obra.id}")
        for ch in meta.characters:
            self.filter_combo.addItem(f"👤 {ch.name}", f"char:{ch.id}")
        # Filtrar por tipo de relación
        for rtype in RELATION_TYPES:
            icon = RELATION_ICONS.get(rtype, "")
            self.filter_combo.addItem(f"{icon} Solo: {rtype.capitalize()}", f"type:{rtype}")
        self.filter_combo.blockSignals(False)

    def _on_filter_changed(self, _index):
        if self._meta:
            self._build_graph(self._meta)

    def _build_graph(self, meta: UniverseMetadata):
        self._scene.clear()

        from core.theme_manager import ThemeManager
        bg_col = "#1c1c1e" if ThemeManager.is_dark() else "#f5f0ea"
        self._view.setBackgroundBrush(QBrush(QColor(bg_col)))

        filter_data = self.filter_combo.currentData() or "all"

        # Paleta de colores únicos por personaje (por índice)
        char_color_map: dict[str, str] = {
            ch.id: CHARACTER_PALETTE[i % len(CHARACTER_PALETTE)]
            for i, ch in enumerate(meta.characters)
        }

        crossover_ids = {ch.id for ch in meta.characters if len(ch.obra_ids) > 1}

        visible_char_ids: set[str] = set()
        filter_relations = list(meta.relations)

        if filter_data == "all":
            visible_char_ids = {ch.id for ch in meta.characters}
        elif filter_data.startswith("obra:"):
            obra_id = filter_data.split(":", 1)[1]
            visible_char_ids = {ch.id for ch in meta.characters if obra_id in ch.obra_ids}
            filter_relations = [r for r in meta.relations if r.obra_id in ("", obra_id)]
        elif filter_data.startswith("char:"):
            focus_id = filter_data.split(":", 1)[1]
            visible_char_ids.add(focus_id)
            for rel in meta.relations:
                if rel.char_id_a == focus_id:   visible_char_ids.add(rel.char_id_b)
                elif rel.char_id_b == focus_id: visible_char_ids.add(rel.char_id_a)
        elif filter_data.startswith("type:"):
            rtype = filter_data.split(":", 1)[1]
            filter_relations = [r for r in meta.relations if r.relation_type == rtype]
            for rel in filter_relations:
                visible_char_ids |= {rel.char_id_a, rel.char_id_b}

        char_map = {ch.id: ch for ch in meta.characters if ch.id in visible_char_ids}
        if not char_map:
            self._draw_empty_message("No hay personajes para mostrar con este filtro.")
            return

        G = nx.Graph()
        for cid in char_map:
            G.add_node(cid)

        visible_relations = []
        for rel in filter_relations:
            if rel.char_id_a in char_map and rel.char_id_b in char_map:
                G.add_edge(rel.char_id_a, rel.char_id_b)
                visible_relations.append(rel)

        # Layout
        if len(G.nodes) < 2:
            pos = {n: (0.0, 0.0) for n in G.nodes}
        else:
            try:
                pos = nx.kamada_kawai_layout(G)
            except Exception:
                try:
                    pos = nx.spring_layout(G, seed=42)
                except Exception:
                    nodes_list = list(G.nodes)
                    n = len(nodes_list)
                    pos = {nid: (math.cos(2*math.pi*i/max(n,1)),
                                 math.sin(2*math.pi*i/max(n,1)))
                           for i, nid in enumerate(nodes_list)}

        scale = 360

        chapter_counts: dict[str, int] = {}
        for obra in meta.obras:
            for libro in obra.libros:
                for cap in libro.capitulos:
                    for cid in cap.characters_present:
                        chapter_counts[cid] = chapter_counts.get(cid, 0) + 1
        max_count = max(chapter_counts.values()) if chapter_counts else 1

        # Crear nodos con color único por personaje
        gfx_nodes: dict[str, CharacterNode] = {}
        for cid, char in char_map.items():
            importance = chapter_counts.get(cid, 0)
            radius = 18 + (importance / max(max_count, 1)) * 22
            px, py = pos.get(cid, (0, 0))
            node = CharacterNode(char, radius,
                                 char_color_map.get(cid, "#636366"),
                                 cid in crossover_ids,
                                 px * scale, py * scale)
            self._scene.addItem(node)
            gfx_nodes[cid] = node

        # Crear aristas (halo primero, luego línea principal, luego etiqueta)
        for rel in visible_relations:
            if rel.char_id_a in gfx_nodes and rel.char_id_b in gfx_nodes:
                edge = RelationEdge(gfx_nodes[rel.char_id_a],
                                    gfx_nodes[rel.char_id_b],
                                    rel.label, rel.intensity,
                                    rel.relation_type)
                edge.add_to_scene(self._scene)  # primero halo y etiqueta
                self._scene.addItem(edge)        # luego línea principal encima

        self._view.fitInView(self._scene.sceneRect().adjusted(-70, -70, 70, 70),
                             Qt.AspectRatioMode.KeepAspectRatio)

    def _draw_empty_message(self, msg: str):
        item = QGraphicsTextItem(msg)
        item.setDefaultTextColor(QColor("#6272a4"))
        item.setFont(QFont("Segoe UI", 14))
        self._scene.addItem(item)


# ── Widget mini para la leyenda ─────────────────────────────────────

class _LegendLine(QFrame):
    """Mini widget que pinta una línea de muestra con el estilo del tipo."""

    def __init__(self, color: str, pen_style, dash_pattern, width: float, parent=None):
        super().__init__(parent)
        self._color = QColor(color)
        self._style = pen_style
        self._dash  = dash_pattern
        self._width = max(1.5, width)
        self.setStyleSheet("background:transparent;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(self._color, self._width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        if self._style == Qt.PenStyle.CustomDashLine and self._dash:
            pen.setStyle(Qt.PenStyle.CustomDashLine)
            pen.setDashPattern(self._dash)
        else:
            pen.setStyle(self._style)
        painter.setPen(pen)
        mid_y = self.height() // 2
        painter.drawLine(2, mid_y, self.width() - 2, mid_y)
        painter.end()
