"""
genealogy_widget.py — Motor Profesional de Árbol Genealógico y Pedigree Jerárquico por Subárboles.
Organiza todas las ramas ancestrales y descendientes de forma matemáticamente aislada:
- Cada pareja de progenitores se centra exclusivamente sobre sus respectivos hijos.
- Cada subárbol familiar (paterno, materno, ramas colaterales) respeta sus límites sin cruzarse jamás.
- Trazado y Resplandor de Linaje: Al hacer clic en cualquier personaje, se ilumina con resplandor dorado
  toda su ruta directa de ancestros hasta la raíz del clan.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsScene, QGraphicsView, QGraphicsItem,
    QGraphicsTextItem, QGraphicsPathItem
)
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import (
    QFont, QColor, QPen, QBrush, QPainter, QPainterPath, QPolygonF
)

from core.models import Character, CharacterRelation
from core.theme_manager import ThemeManager


class FlowchartCardItem(QGraphicsItem):
    """Nodo interactivo estilo Diagrama de Flujo con soporte para resplandor de linaje ancestral."""

    def __init__(self, character: Character, generation_level: int = 0,
                 node_type: str = "member", is_central: bool = False,
                 custom_tag: str = "", on_click=None, parent=None):
        super().__init__(parent)
        self.character = character
        self.generation_level = generation_level
        self.node_type = node_type
        self.is_central = is_central
        self.custom_tag = custom_tag
        self.on_click = on_click

        self.width = 200.0 if not is_central else 215.0
        self.height = 74.0 if not is_central else 80.0

        self.setAcceptHoverEvents(True)
        self.setZValue(20 if is_central else 10)
        self._hovered = False
        self._is_selected = False
        self._is_in_lineage = False
        self._is_dimmed = False

    def boundingRect(self) -> QRectF:
        return QRectF(-self.width / 2 - 12, -self.height / 2 - 12, self.width + 24, self.height + 24)

    def hoverEnterEvent(self, event):
        self._hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.on_click:
            self.on_click(self.character.id)
            event.accept()
        else:
            super().mousePressEvent(event)

    def paint(self, painter: QPainter | None, option, widget=None):
        if painter is None:
            return

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        is_dark = ThemeManager.is_dark()
        card_rect = QRectF(-self.width / 2, -self.height / 2, self.width, self.height)

        # Atenuación si no forma parte del linaje seleccionado
        if self._is_dimmed:
            painter.setOpacity(0.28)
        else:
            painter.setOpacity(1.0)

        # Paleta de roles
        role_colors = {
            "Protagonista": "#f59e0b",
            "Antagonista":  "#ef4444",
            "Misterioso":   "#a855f7",
            "Secundario":   "#3b82f6",
            "Otro":         "#64748b"
        }
        role_color = QColor(role_colors.get(self.character.role, "#64748b"))

        # Configuración por tipo de nodo
        if self.is_central:
            bg_hex = ("#2e1065" if is_dark else "#ede9fe") if self._hovered else ("#1e1b4b" if is_dark else "#f5f3ff")
            border_hex = (
                ("#a5b4fc" if is_dark else "#4338ca") if self._hovered else ("#818cf8" if is_dark else "#4f46e5")
            )
            border_width = 3.5 if self._hovered else 2.5
            header_text = self.custom_tag or "★ PERSONAJE PRINCIPAL"
            hdr_hex = ("#6366f1" if is_dark else "#4f46e5") if self._hovered else ("#4f46e5" if is_dark else "#6366f1")
        elif self.generation_level < 0:
            bg_hex = ("#14532d" if is_dark else "#dcfce7") if self._hovered else ("#142d1f" if is_dark else "#f0fdf4")
            border_hex = "#16a34a" if self._hovered else "#22c55e"
            border_width = 2.5 if self._hovered else 1.8
            header_text = self.custom_tag or "PROGENITOR / PADRE"
            hdr_hex = ("#15803d" if is_dark else "#16a34a") if self._hovered else ("#166534" if is_dark else "#22c55e")
        elif self.node_type == "partner":
            bg_hex = ("#701a75" if is_dark else "#fce7f3") if self._hovered else ("#311327" if is_dark else "#fdf2f8")
            border_hex = "#db2777" if self._hovered else "#ec4899"
            border_width = 2.5 if self._hovered else 1.8
            header_text = self.custom_tag or "💍 PAREJA / CÓNYUGE"
            hdr_hex = ("#be185d" if is_dark else "#db2777") if self._hovered else ("#9d174d" if is_dark else "#ec4899")
        elif self.node_type == "sibling":
            bg_hex = ("#1e3a8a" if is_dark else "#dbeafe") if self._hovered else ("#172554" if is_dark else "#eff6ff")
            border_hex = "#2563eb" if self._hovered else "#3b82f6"
            border_width = 2.5 if self._hovered else 1.8
            header_text = self.custom_tag or "HERMANO(A)"
            hdr_hex = ("#1e40af" if is_dark else "#2563eb") if self._hovered else ("#1d4ed8" if is_dark else "#3b82f6")
        else:  # descendant / child / grandchild
            bg_hex = ("#134e4a" if is_dark else "#ccfbf1") if self._hovered else ("#142d27" if is_dark else "#f0fdfa")
            border_hex = "#0d9488" if self._hovered else "#14b8a6"
            border_width = 2.5 if self._hovered else 1.8
            header_text = self.custom_tag or "DESCENDIENTE / HIJO"
            hdr_hex = ("#115e59" if is_dark else "#0d9488") if self._hovered else ("#0f766e" if is_dark else "#14b8a6")

        # ── RESPLANDOR DORADO DE LINAJE ACTIVO / SELECCIONADO ──────────
        if self._is_selected:
            border_hex = "#fbbf24"
            border_width = 3.6
            hdr_hex = "#d97706"
            for offset, alpha in [(8, 30), (5, 60), (2, 100)]:
                glow_rect = card_rect.adjusted(-offset, -offset, offset, offset)
                glow_path = QPainterPath()
                glow_path.addRoundedRect(glow_rect, 10, 10)
                painter.fillPath(glow_path, QBrush(QColor(251, 191, 36, alpha)))
        elif self._is_in_lineage:
            border_hex = "#f59e0b"
            border_width = 2.8
            for offset, alpha in [(6, 25), (3, 50)]:
                glow_rect = card_rect.adjusted(-offset, -offset, offset, offset)
                glow_path = QPainterPath()
                glow_path.addRoundedRect(glow_rect, 10, 10)
                painter.fillPath(glow_path, QBrush(QColor(245, 158, 11, alpha)))
        elif self._hovered:
            glow_c = QColor(border_hex)
            for offset, alpha in [(6, 25), (4, 45), (2, 75)]:
                glow_rect = card_rect.adjusted(-offset, -offset, offset, offset)
                glow_path = QPainterPath()
                glow_path.addRoundedRect(glow_rect, 10, 10)
                painter.fillPath(glow_path, QBrush(QColor(glow_c.red(), glow_c.green(), glow_c.blue(), alpha)))
        elif self.is_central:
            b_col = QColor(border_hex)
            for offset, alpha in [(4, 15), (2, 35)]:
                glow_rect = card_rect.adjusted(-offset, -offset, offset, offset)
                glow_path = QPainterPath()
                glow_path.addRoundedRect(glow_rect, 9, 9)
                painter.fillPath(
                    glow_path,
                    QBrush(QColor(b_col.red(), b_col.green(), b_col.blue(), alpha))
                )
        else:
            shadow_rect = card_rect.adjusted(2, 3, 2, 3)
            shadow_path = QPainterPath()
            shadow_path.addRoundedRect(shadow_rect, 8, 8)
            painter.fillPath(shadow_path, QBrush(QColor(0, 0, 0, 45 if is_dark else 20)))

        # Caja principal
        box_path = QPainterPath()
        box_path.addRoundedRect(card_rect, 8, 8)
        painter.fillPath(box_path, QBrush(QColor(bg_hex)))
        painter.setPen(QPen(QColor(border_hex), border_width))
        painter.drawPath(box_path)

        # Header tag superior
        header_height = 18.0
        header_rect = QRectF(card_rect.left(), card_rect.top(), card_rect.width(), header_height)
        header_path = QPainterPath()
        header_path.moveTo(card_rect.left() + 8, card_rect.top())
        header_path.lineTo(card_rect.right() - 8, card_rect.top())
        header_path.arcTo(card_rect.right() - 16, card_rect.top(), 16, 16, 90, -90)
        header_path.lineTo(card_rect.right(), card_rect.top() + header_height)
        header_path.lineTo(card_rect.left(), card_rect.top() + header_height)
        header_path.lineTo(card_rect.left(), card_rect.top() + 8)
        header_path.arcTo(card_rect.left(), card_rect.top(), 16, 16, 180, -90)
        header_path.closeSubpath()

        painter.fillPath(header_path, QBrush(QColor(hdr_hex)))
        painter.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
        painter.setPen(QColor("#ffffff"))
        painter.drawText(header_rect.adjusted(4, 0, -4, 0), Qt.AlignmentFlag.AlignCenter, header_text)

        # Avatar circular
        avatar_r = 16 if not self.is_central else 18
        avatar_cx = card_rect.left() + 12 + avatar_r
        avatar_cy = card_rect.top() + header_height + (card_rect.height() - header_height) / 2
        avatar_rect = QRectF(avatar_cx - avatar_r, avatar_cy - avatar_r, avatar_r * 2, avatar_r * 2)

        painter.setPen(QPen(role_color, 1.5))
        painter.setBrush(QBrush(role_color.darker(160) if is_dark else role_color.lighter(170)))
        painter.drawEllipse(avatar_rect)

        initials = "".join(w[0].upper() for w in self.character.name.split()[:2]) if self.character.name else "?"
        painter.setFont(QFont("Segoe UI", 9 if not self.is_central else 10, QFont.Weight.Bold))
        painter.setPen(QColor("#ffffff" if is_dark else role_color.darker(140)))
        painter.drawText(avatar_rect, Qt.AlignmentFlag.AlignCenter, initials)

        # Nombre y Rol
        text_x = avatar_cx + avatar_r + 8
        text_w = card_rect.right() - text_x - 6
        content_y = card_rect.top() + header_height + 4

        name_rect = QRectF(text_x, content_y, text_w, 20)
        role_rect = QRectF(text_x, content_y + 18, text_w, 16)

        painter.setFont(QFont("Segoe UI", 9 if not self.is_central else 10, QFont.Weight.Bold))
        painter.setPen(QColor("#f4f4f5" if is_dark else "#18181b"))
        elided_name = painter.fontMetrics().elidedText(self.character.name, Qt.TextElideMode.ElideRight, int(text_w))
        painter.drawText(name_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, elided_name)

        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
        painter.setPen(QColor(role_color.name()))
        painter.drawText(
            role_rect,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            self.character.role.upper()
        )


class FlowchartConnectorItem(QGraphicsItem):
    """Conector ortogonal de diagrama de flujo con soporte para trazado y resplandor de linaje."""

    def __init__(self, start_pt: QPointF, end_pt: QPointF, mid_y: float,
                 color: str = "#64748b", has_arrow: bool = True,
                 edge_keys: list[tuple[str, str]] | None = None, parent=None):
        super().__init__(parent)
        self.start_pt = start_pt
        self.end_pt = end_pt
        self.mid_y = mid_y
        self.base_color = color
        self.has_arrow = has_arrow
        self.edge_keys = edge_keys or []

        self._is_highlighted = False
        self._is_dimmed = False
        self.setZValue(2)

    def boundingRect(self) -> QRectF:
        min_x = min(self.start_pt.x(), self.end_pt.x()) - 15
        max_x = max(self.start_pt.x(), self.end_pt.x()) + 15
        min_y = min(self.start_pt.y(), self.end_pt.y()) - 15
        max_y = max(self.start_pt.y(), self.end_pt.y()) + 15
        return QRectF(min_x, min_y, max_x - min_x, max_y - min_y)

    def paint(self, painter: QPainter | None, option, widget=None):
        if painter is None:
            return

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        if self._is_dimmed:
            painter.setOpacity(0.2)
        else:
            painter.setOpacity(1.0)

        path = QPainterPath()
        path.moveTo(self.start_pt)
        path.lineTo(self.start_pt.x(), self.mid_y)
        path.lineTo(self.end_pt.x(), self.mid_y)
        path.lineTo(self.end_pt)

        if self._is_highlighted:
            for w, alpha in [(8.0, 35), (5.0, 75)]:
                glow_pen = QPen(QColor(251, 191, 36, alpha), w)
                glow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                glow_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                painter.setPen(glow_pen)
                painter.drawPath(path)

            pen = QPen(QColor("#fbbf24"), 3.2)
        else:
            pen = QPen(QColor(self.base_color), 2.0)

        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawPath(path)

        if self.has_arrow:
            arrow = QPolygonF()
            x, y = self.end_pt.x(), self.end_pt.y()
            arrow.append(QPointF(x, y))
            arrow.append(QPointF(x - 5, y - 7))
            arrow.append(QPointF(x + 5, y - 7))

            fill_col = QColor("#fbbf24" if self._is_highlighted else self.base_color)
            painter.setBrush(QBrush(fill_col))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPolygon(arrow)


class GenealogyWidget(QWidget):
    """
    Widget visual de Árbol Genealógico y Pedigree Jerárquico por Subárboles.
    Dispone de forma limpia y matemáticamente separada todas las ramas familiares (paternas, maternas, etc.).
    Permite hacer clic en cualquier miembro para iluminar toda la ruta directa de su linaje ancestral.
    """

    character_switched = pyqtSignal(str)

    def __init__(self, character: Character,
                 characters: list[Character] | None = None,
                 relations: list[CharacterRelation] | None = None,
                 parent=None):
        super().__init__(parent)
        self._char = character
        self._characters = list(characters or [])
        self._relations = list(relations or [])
        self._gen_zoom = 1.0
        self._selected_lineage_char_id: str | None = None

        self._card_items: dict[str, FlowchartCardItem] = {}
        self._connector_items: list[FlowchartConnectorItem] = []
        self._parent_map: dict[str, list[str]] = {}

        self._build_ui()

    def set_data(self, character: Character,
                 characters: list[Character] | None = None,
                 relations: list[CharacterRelation] | None = None):
        """Actualiza los datos y redibuja el árbol genealógico completo."""
        self._char = character
        if characters is not None:
            self._characters = list(characters)
        if relations is not None:
            self._relations = list(relations)
        self._selected_lineage_char_id = None
        self._title_lbl.setText(f"LINAJE: {self._char.name.upper()}")
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Barra superior con navegación y trazado de linaje
        header = QHBoxLayout()
        header.setSpacing(8)

        self._title_lbl = QLabel(f"LINAJE: {self._char.name.upper()}")
        self._title_lbl.setStyleSheet(
            "color: #8e8e93; font-size: 12px; font-weight: 800; "
            "letter-spacing: 0.5px; background: transparent; padding-left: 2px;"
        )
        header.addWidget(self._title_lbl)

        self._btn_reset_highlight = QPushButton("✕ Quitar Filtro")
        self._btn_reset_highlight.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_reset_highlight.setToolTip("Quitar resplandor de linaje y mostrar todo el árbol normalmente")
        self._btn_reset_highlight.setStyleSheet(
            "QPushButton { font-size: 11px; font-weight: 600; padding: 3px 10px; "
            "background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); "
            "border-radius: 5px; } QPushButton:hover { background: rgba(239, 68, 68, 0.25); color: #ffffff; }"
        )
        self._btn_reset_highlight.clicked.connect(self._clear_lineage_highlight)
        self._btn_reset_highlight.setVisible(False)
        header.addWidget(self._btn_reset_highlight)

        header.addStretch(1)

        btn_fit = QPushButton("🔍 Centrar")
        btn_fit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_fit.setToolTip("Ajustar y centrar el diagrama en pantalla")
        btn_fit.clicked.connect(self._fit_tree_view)
        header.addWidget(btn_fit)

        btn_refresh = QPushButton("🔄 Recargar")
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh.setToolTip("Recalcular y redibujar el árbol")
        btn_refresh.clicked.connect(self.refresh)
        header.addWidget(btn_refresh)
        layout.addLayout(header)

        # Escena y vista gráfica
        is_dark = ThemeManager.is_dark()
        self._gen_scene = QGraphicsScene(self)
        self._gen_view = QGraphicsView(self._gen_scene)
        self._gen_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._gen_view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self._gen_view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self._gen_view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        bg_col = "#141416" if is_dark else "#f8f9fa"
        self._gen_view.setBackgroundBrush(QBrush(QColor(bg_col)))
        self._gen_view.wheelEvent = self._gen_wheel_event
        self._gen_scene.mousePressEvent = self._on_scene_mouse_press
        layout.addWidget(self._gen_view, 1)

        # Leyenda de flujo familiar
        legend = QHBoxLayout()
        legend_items = [
            ("🟩 Progenitores / Ancestros", "#22c55e"),
            ("🟪 Personaje Principal", "#6366f1"),
            ("💖 Pareja / Cónyuge", "#ec4899"),
            ("🟦 Hermanos", "#3b82f6"),
            ("🟨 Descendientes / Hijos", "#14b8a6"),
            ("✨ Linaje Iluminado", "#fbbf24")
        ]
        for name, col in legend_items:
            lbl = QLabel(name)
            lbl.setStyleSheet(f"color:{col}; font-size:10px; font-weight:bold; padding:0 8px;")
            legend.addWidget(lbl)
        legend.addStretch()
        layout.addLayout(legend)

        QTimer.singleShot(60, self.refresh)

    def _on_scene_mouse_press(self, event):
        item = self._gen_scene.itemAt(event.scenePos(), self._gen_view.transform())
        if item is None or isinstance(item, FlowchartConnectorItem):
            self._clear_lineage_highlight()
        QGraphicsScene.mousePressEvent(self._gen_scene, event)

    def _gen_wheel_event(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self._gen_zoom *= factor
        if 0.2 < self._gen_zoom < 5.0:
            self._gen_view.scale(factor, factor)
        else:
            self._gen_zoom /= factor

    def _fit_tree_view(self):
        rect = self._gen_scene.sceneRect()
        if not rect.isNull() and rect.isValid():
            self._gen_view.fitInView(rect.adjusted(-60, -60, 60, 60), Qt.AspectRatioMode.KeepAspectRatio)

    def _on_card_clicked(self, char_id: str):
        if self._selected_lineage_char_id == char_id:
            self._clear_lineage_highlight()
            return

        self._selected_lineage_char_id = char_id
        char_map = {c.id: c for c in self._characters}

        ancestors_set: set[str] = set()
        active_edges_set: set[tuple[str, str]] = set()

        def _trace_up(curr_id: str, visited: set[str]):
            parents = self._parent_map.get(curr_id, [])
            for p_id in parents:
                if p_id not in visited:
                    visited.add(p_id)
                    ancestors_set.add(p_id)
                    active_edges_set.add((curr_id, p_id))
                    _trace_up(p_id, visited)

        _trace_up(char_id, {char_id})
        all_active_nodes = ancestors_set | {char_id}

        for cid, card in self._card_items.items():
            card._is_selected = (cid == char_id)
            card._is_in_lineage = (cid in ancestors_set)
            card._is_dimmed = (cid not in all_active_nodes)
            card.update()

        for conn in self._connector_items:
            has_match = any(e in active_edges_set for e in conn.edge_keys)
            conn._is_highlighted = has_match
            conn._is_dimmed = not has_match
            conn.update()

        curr_name = char_map.get(char_id, self._char).name
        if ancestors_set:
            self._title_lbl.setText(f"LINAJE ACTIVO: {curr_name.upper()} ➔ ANCESTROS ({len(ancestors_set)})")
        else:
            self._title_lbl.setText(f"LINAJE: {curr_name.upper()} (RAÍZ)")

        self._btn_reset_highlight.setVisible(True)
        self._gen_scene.update()

    def _clear_lineage_highlight(self):
        self._selected_lineage_char_id = None
        self._btn_reset_highlight.setVisible(False)
        for card in self._card_items.values():
            card._is_selected = False
            card._is_in_lineage = False
            card._is_dimmed = False
            card.update()

        for conn in self._connector_items:
            conn._is_highlighted = False
            conn._is_dimmed = False
            conn.update()

        self._title_lbl.setText(f"LINAJE: {self._char.name.upper()}")
        self._gen_scene.update()

    def refresh(self):
        """Construye el árbol genealógico completo mediante el motor jerárquico por subárboles."""
        self._gen_scene.clear()
        self._card_items.clear()
        self._connector_items.clear()
        self._parent_map.clear()
        self._selected_lineage_char_id = None
        self._btn_reset_highlight.setVisible(False)

        is_dark = ThemeManager.is_dark()
        bg_col = "#141416" if is_dark else "#f8f9fa"
        self._gen_view.setBackgroundBrush(QBrush(QColor(bg_col)))
        char_map = {c.id: c for c in self._characters}

        # ── 1. MAPEO COMPLETO DE PROGENITORES Y DESCENDIENTES ──────────
        child_to_parents: dict[str, list[str]] = {}
        parent_to_children: dict[str, list[str]] = {}

        for rel in self._relations:
            if rel.relation_type == "descendiente":
                c_id, p_id = rel.char_id_a, rel.char_id_b
                child_to_parents.setdefault(c_id, []).append(p_id)
                parent_to_children.setdefault(p_id, []).append(c_id)

        self._parent_map = child_to_parents

        # Pareja y Hermanos del personaje principal
        partners: list[str] = []
        siblings: list[str] = []

        for rel in self._relations:
            if rel.char_id_a != self._char.id and rel.char_id_b != self._char.id:
                continue
            other_id = rel.char_id_b if rel.char_id_a == self._char.id else rel.char_id_a
            if other_id not in char_map:
                continue

            if rel.relation_type == "pareja":
                partners.append(other_id)
            elif rel.relation_type == "familiar":
                siblings.append(other_id)

        # ── 2. CONSTANTES DE DISTRIBUCIÓN DEL MOTOR DE SUBÁRBOLES ──────
        CARD_W = 200.0
        CARD_H = 74.0
        V_GAP = 140.0
        PAIR_GAP = 24.0
        BRANCH_GAP = 60.0

        node_coords: dict[str, tuple[float, float]] = {}

        # ── 3. MOTOR RECURSIVO DE SUBÁRBOLES DE ANCESTROS ───────────────
        def _layout_ancestor_subtree(
            cid: str, current_y: float, visited: set[str] | None = None
        ) -> tuple[float, dict[str, tuple[float, float]]]:
            if visited is None:
                visited = set()
            if cid in visited:
                return CARD_W, {cid: (0.0, current_y)}
            visited.add(cid)

            parents = [p for p in child_to_parents.get(cid, []) if p not in visited]
            if not parents:
                return CARD_W, {cid: (0.0, current_y)}

            if len(parents) == 1:
                p_id = parents[0]
                p_width, p_coords = _layout_ancestor_subtree(p_id, current_y - V_GAP, set(visited))
                coords = {cid: (0.0, current_y)}
                for k, (kx, ky) in p_coords.items():
                    coords[k] = (kx, ky)
                return max(CARD_W, p_width), coords

            # 2+ Padres (Pareja de progenitores)
            p1_id, p2_id = parents[0], parents[1]
            p1_w, p1_coords = _layout_ancestor_subtree(p1_id, current_y - V_GAP, set(visited))
            p2_w, p2_coords = _layout_ancestor_subtree(p2_id, current_y - V_GAP, set(visited))

            gap = max(PAIR_GAP, BRANCH_GAP)
            total_w = p1_w + gap + p2_w

            p1_center_x = -total_w / 2 + p1_w / 2
            p2_center_x = total_w / 2 - p2_w / 2

            coords = {cid: (0.0, current_y)}
            for k, (kx, ky) in p1_coords.items():
                coords[k] = (p1_center_x + kx, ky)
            for k, (kx, ky) in p2_coords.items():
                coords[k] = (p2_center_x + kx, ky)

            return total_w, coords

        _, anc_coords = _layout_ancestor_subtree(self._char.id, 0.0)
        for cid, (cx, cy) in anc_coords.items():
            node_coords[cid] = (cx, cy)

        # ── 4. AGREGAR HERMANOS Y PAREJA EN Y=0 ────────────────────────
        if siblings:
            leftmost_x = min([x for x, y in node_coords.values() if y == 0.0] + [0.0]) - CARD_W / 2
            for i, s_id in enumerate(siblings):
                sx = leftmost_x - 40.0 - CARD_W / 2 - i * (CARD_W + 40.0)
                node_coords[s_id] = (sx, 0.0)

        if partners:
            rightmost_x = max([x for x, y in node_coords.values() if y == 0.0] + [0.0]) + CARD_W / 2
            p_id = partners[0]
            node_coords[p_id] = (rightmost_x + 80.0 + CARD_W / 2, 0.0)

        # ── 5. MOTOR RECURSIVO DE SUBÁRBOLES DE DESCENDIENTES ───────────
        main_children = parent_to_children.get(self._char.id, [])

        def _layout_descendant_subtree(
            cid: str, current_y: float, visited: set[str] | None = None
        ) -> tuple[float, dict[str, tuple[float, float]]]:
            if visited is None:
                visited = set()
            if cid in visited:
                return CARD_W, {cid: (0.0, current_y)}
            visited.add(cid)

            children = [ch for ch in parent_to_children.get(cid, []) if ch not in visited]
            if not children:
                return CARD_W, {cid: (0.0, current_y)}

            child_subtrees = []
            total_w = 0.0
            for ch_id in children:
                cw, ccoords = _layout_descendant_subtree(ch_id, current_y + V_GAP, set(visited))
                child_subtrees.append((ch_id, cw, ccoords))
                total_w += cw
            total_w += (len(children) - 1) * BRANCH_GAP

            coords = {cid: (0.0, current_y)}
            start_x = -total_w / 2
            for ch_id, cw, ccoords in child_subtrees:
                ch_center_x = start_x + cw / 2
                for k, (kx, ky) in ccoords.items():
                    coords[k] = (ch_center_x + kx, ky)
                start_x += cw + BRANCH_GAP

            return total_w, coords

        if main_children:
            ch_subtrees = []
            tot_ch_w = 0.0
            for ch_id in main_children:
                cw, ccoords = _layout_descendant_subtree(ch_id, V_GAP)
                ch_subtrees.append((ch_id, cw, ccoords))
                tot_ch_w += cw
            tot_ch_w += (len(main_children) - 1) * BRANCH_GAP

            p_x = node_coords[partners[0]][0] if partners else node_coords[self._char.id][0]
            desc_center_x = (node_coords[self._char.id][0] + p_x) / 2
            start_x = desc_center_x - tot_ch_w / 2
            for ch_id, cw, ccoords in ch_subtrees:
                ch_center_x = start_x + cw / 2
                for k, (kx, ky) in ccoords.items():
                    node_coords[k] = (ch_center_x + kx, ky)
                start_x += cw + BRANCH_GAP

        # ── 6. RENDERIZAR TARJETAS EN ESCENA ───────────────────────────
        ancestor_tags = {
            1: "PROGENITOR",
            2: "ABUELO(A)",
            3: "BISABUELO(A)",
            4: "TATARABUELO(A)",
            5: "TRASTATARABUELO(A)"
        }
        desc_tags = {
            1: "HIJO(A)",
            2: "NIETO(A)",
            3: "BISNIETO(A)",
            4: "TATARANIETO(A)",
            5: "TRASTATARANIETO(A)"
        }

        for cid, (cx, cy) in node_coords.items():
            ch = char_map.get(cid)
            if not ch:
                continue
            is_central = (cid == self._char.id)
            gen_idx = int(round(cy / V_GAP))

            if is_central:
                tag = "★ PERSONAJE PRINCIPAL"
                node_type = "central"
            elif gen_idx < 0:
                dist = abs(gen_idx)
                tag = ancestor_tags.get(dist, f"ANCESTRO (-{dist})")
                node_type = "ancestor" if dist == 1 else "grandparent"
            elif gen_idx == 0:
                if cid in partners:
                    tag = "💍 CÓNYUGE / PAREJA"
                    node_type = "partner"
                else:
                    tag = "HERMANO(A)"
                    node_type = "sibling"
            else:
                tag = desc_tags.get(gen_idx, f"DESCENDIENTE (+{gen_idx})")
                node_type = "descendant" if gen_idx == 1 else "grandchild"

            card = FlowchartCardItem(
                ch, generation_level=gen_idx, node_type=node_type,
                is_central=is_central, custom_tag=tag, on_click=self._on_card_clicked
            )
            card.setPos(cx, cy)
            self._gen_scene.addItem(card)
            self._card_items[cid] = card

        # Puente de pareja
        if partners and partners[0] in node_coords:
            p_id = partners[0]
            c_x = node_coords[self._char.id][0]
            p_x = node_coords[p_id][0]
            self._draw_horizontal_bridge(
                c_x + (CARD_W / 2), 0.0,
                p_x - (CARD_W / 2), 0.0,
                label="💍 Pareja", color="#ec4899"
            )

        # ── 7. RENDERIZAR CONEXIONES ORTOGONALES AISLADAS POR PAREJA ────
        parent_pairs: dict[tuple[str, ...], list[str]] = {}
        for cid, (cx, cy) in node_coords.items():
            p_ids = tuple(sorted([p for p in child_to_parents.get(cid, []) if p in node_coords]))
            if p_ids:
                parent_pairs.setdefault(p_ids, []).append(cid)

        # Si hay hermanos que no tienen relación descendiente directa registrada, asociarlos a los padres de char_id
        if siblings and self._char.id in node_coords:
            p_ids = tuple(sorted([p for p in child_to_parents.get(self._char.id, []) if p in node_coords]))
            if p_ids:
                for s_id in siblings:
                    # Solo si el hermano no tiene ya sus propios padres mapeados en parent_pairs
                    s_parents = tuple(sorted([p for p in child_to_parents.get(s_id, []) if p in node_coords]))
                    if not s_parents and s_id not in parent_pairs.get(p_ids, []):
                        parent_pairs.setdefault(p_ids, []).append(s_id)

        for p_ids, c_ids in parent_pairs.items():
            if len(p_ids) == 1:
                p_id = p_ids[0]
                px, py = node_coords[p_id]
                origin_x, origin_y = px, py + CARD_H / 2
                trunk_edges = [(cid, p_id) for cid in c_ids]
            elif len(p_ids) == 2:
                p1_id, p2_id = p_ids[0], p_ids[1]
                p1_x, p1_y = node_coords[p1_id]
                p2_x, p2_y = node_coords[p2_id]

                bridge_y = p1_y + CARD_H / 2 + 18.0
                # Segmentos desde cada progenitor al puente horizontal
                p1_edges = [(cid, p1_id) for cid in c_ids]
                p2_edges = [(cid, p2_id) for cid in c_ids]

                self._draw_connector_line(
                    p1_x, p1_y + CARD_H / 2, p1_x, bridge_y, color="#22c55e", edge_keys=p1_edges
                )
                self._draw_connector_line(
                    p2_x, p2_y + CARD_H / 2, p2_x, bridge_y, color="#22c55e", edge_keys=p2_edges
                )

                origin_x = (p1_x + p2_x) / 2
                origin_y = bridge_y

                # Puente izquierdo hacia el centro
                self._draw_connector_line(
                    p1_x, bridge_y, origin_x, bridge_y, color="#22c55e", edge_keys=p1_edges
                )
                # Puente derecho hacia el centro
                self._draw_connector_line(
                    p2_x, bridge_y, origin_x, bridge_y, color="#22c55e", edge_keys=p2_edges
                )
                trunk_edges = [(cid, pid) for cid in c_ids for pid in p_ids]
            else:
                continue

            first_child_y = node_coords[c_ids[0]][1]
            child_top_y = first_child_y - (41.0 if self._char.id in c_ids and len(c_ids) == 1 else CARD_H / 2)
            bus_y = (origin_y + child_top_y) / 2

            # Línea vertical del centro del puente hacia el bus de hijos
            self._draw_connector_line(origin_x, origin_y, origin_x, bus_y, color="#22c55e", edge_keys=trunk_edges)

            # Para cada hijo, trazar su tramo horizontal desde origin_x hasta su posición x
            for cid in c_ids:
                cx, cy = node_coords[cid]
                c_top = cy - (41.0 if cid == self._char.id else CARD_H / 2)
                single_child_edges = [(cid, pid) for pid in p_ids]

                # Tramo horizontal específico del hijo
                if cx != origin_x:
                    self._draw_connector_line(
                        origin_x, bus_y, cx, bus_y, color="#22c55e", edge_keys=single_child_edges
                    )

                # Flecha vertical descendiendo a la tarjeta del hijo
                self._draw_connector_arrow(cx, bus_y, cx, c_top, color="#22c55e", edge_keys=single_child_edges)

        QTimer.singleShot(80, self._fit_tree_view)

    def _draw_connector_line(self, x1: float, y1: float, x2: float, y2: float,
                             color: str = "#22c55e", edge_keys: list[tuple[str, str]] | None = None):
        conn = FlowchartConnectorItem(
            QPointF(x1, y1), QPointF(x2, y2), mid_y=(y1 + y2) / 2,
            color=color, has_arrow=False, edge_keys=edge_keys
        )
        self._gen_scene.addItem(conn)
        self._connector_items.append(conn)

    def _draw_connector_arrow(self, x1: float, y1: float, x2: float, y2: float,
                              color: str = "#22c55e", edge_keys: list[tuple[str, str]] | None = None):
        conn = FlowchartConnectorItem(
            QPointF(x1, y1), QPointF(x2, y2), mid_y=(y1 + y2) / 2,
            color=color, has_arrow=True, edge_keys=edge_keys
        )
        self._gen_scene.addItem(conn)
        self._connector_items.append(conn)

    def _draw_horizontal_bridge(self, x1: float, y1: float, x2: float, y2: float, label: str, color: str):
        # Línea rosa/púrpura sutil de conexión matrimonial con estilo punteado o continuo fino
        conn = FlowchartConnectorItem(
            QPointF(x1, y1), QPointF(x2, y2), mid_y=(y1 + y2) / 2,
            color=color, has_arrow=False
        )
        self._gen_scene.addItem(conn)
        self._connector_items.append(conn)

        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        is_dark = ThemeManager.is_dark()

        # Pequeño círculo/anillo discreto con icono de alianza en lugar de una píldora gigante de texto
        ring_r = 9.0
        ring_rect = QRectF(mid_x - ring_r, mid_y - ring_r, ring_r * 2, ring_r * 2)
        ring_path = QPainterPath()
        ring_path.addEllipse(ring_rect)

        ring_bg = QGraphicsPathItem(ring_path)
        ring_bg.setBrush(QBrush(QColor("#18181b" if is_dark else "#ffffff")))
        ring_bg.setPen(QPen(QColor(color), 1.6))
        ring_bg.setZValue(25)
        ring_bg.setToolTip("Pareja / Matrimonio")
        self._gen_scene.addItem(ring_bg)

        # Icono o símbolo minimalista dentro del aro
        symbol_item = QGraphicsTextItem("💍")
        symbol_item.setFont(QFont("Segoe UI Emoji", 7))
        sbr = symbol_item.boundingRect()
        symbol_item.setPos(mid_x - sbr.width() / 2, mid_y - sbr.height() / 2)
        symbol_item.setZValue(26)
        symbol_item.setToolTip("Pareja / Matrimonio")
        self._gen_scene.addItem(symbol_item)
