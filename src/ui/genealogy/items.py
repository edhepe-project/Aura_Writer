"""
items.py — Elementos gráficos del Árbol Genealógico:
- FlowchartCardItem: Tarjeta de personaje interactiva con estados de hover, selección y linaje.
- FlowchartConnectorItem: Conector ortogonal con soporte para resplandor y flechas.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QGraphicsItem, QGraphicsPathItem, QGraphicsTextItem
)
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import (
    QFont, QColor, QPen, QBrush, QPainter, QPainterPath, QPolygonF
)

from core.models import Character
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
            header_text = self.custom_tag or "PAREJA / CÓNYUGE"
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

        # Resplandor dorado de linaje activo / seleccionado
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
            hdr_hex = "#b45309"
            glow_c = QColor("#f59e0b")
            for offset, alpha in [(6, 25), (3, 50)]:
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
