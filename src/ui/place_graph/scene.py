"""
scene.py — Escena y Vista interactiva de Alto Rendimiento para el Grafo de Lugares.
"""
from __future__ import annotations

from typing import Optional

from PyQt6.QtWidgets import (
    QGraphicsScene, QGraphicsView, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import (
    QPainter, QBrush, QColor, QTransform
)

from core.theme_manager import ThemeManager
from .items import PlaceNodeItem, PlaceLinkItem, PresenceBadgeItem, PresenceOverflowBadgeItem


class PlaceGraphScene(QGraphicsScene):
    """
    Escena interactiva del Atlas de Lugares.
    Gestiona foco inteligente, iluminación de adyacencias y desvanecimiento de nodos secundarios.
    """
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
        # Presencias: place_id → lista de PresenceBadgeItem
        self._presence_badges: dict[str, list[PresenceBadgeItem]] = {}

    def _node_clicked(self, place_id: str):
        self._set_focus(place_id)
        self.place_selected.emit(place_id)

    def _node_double_clicked(self, place_id: str):
        self.place_double_clicked.emit(place_id)

    def _set_focus(self, place_id: str | None):
        if not place_id:
            self.clear_selection_and_focus()
            return
        self._focused_id = place_id
        neighbors = self._adj.get(place_id, set())
        connected = {place_id} | neighbors

        # 1. Nodos: el enfocado resalta, vecinos activos, resto atenuado
        for nid, node in self._nodes.items():
            if nid == place_id:
                node.set_focused(True, False)
            elif nid in connected:
                node.set_focused(False, False)
            else:
                node.set_focused(False, True)

        # 2. Aristas: solo las conectadas se iluminan con glow
        for edge in self._all_edges:
            is_mine = (edge.node_a.place.id == place_id or
                       edge.node_b.place.id == place_id)
            if is_mine:
                edge.set_active_focus(True, False)
            else:
                edge.set_active_focus(False, True)

    def clear_selection_and_focus(self):
        self._focused_id = None
        for node in self._nodes.values():
            node.set_focused(False, False)
        for edge in self._all_edges:
            edge.set_active_focus(False, False)
        self.background_clicked.emit()

    def load_presences(
        self,
        presences: list,
        chapter_id: str | None = None,
        character_map: dict | None = None,
        chapter_order_map: dict | None = None,
    ) -> None:
        """
        Renderiza badges de presencia de personajes sobre los nodos de lugar.
        Garantiza la regla fundamental: UN PERSONAJE SOLO ESTÁ EN 1 LUGAR A LA VEZ.

        Args:
            presences: Lista de CharacterPresence del universo.
            chapter_id: Si se proporciona, filtra solo las presencias de ese capítulo.
                        Si es None (vista global), resuelve la última ubicación física
                        conocida de cada personaje respetando el orden cronológico.
            character_map: dict {char_id: Character} para obtener el nombre.
            chapter_order_map: dict {chapter_id: order} para la resolución cronológica.
        """
        self._clear_presence_badges()

        if chapter_id is not None:
            # Filtrar por el capítulo seleccionado (1 presencia por personaje)
            from tools.nlp.presence_merger import PresenceMerger
            cap_presences = [
                p for p in presences
                if p.chapter_id == chapter_id and p.presence_type in ("present", "transit")
            ]
            filtered = PresenceMerger.merge_chapter_presences(cap_presences)
        else:
            # Vista "Todos los capítulos": resolver la ÚLTIMA ubicación conocida de cada personaje
            from tools.nlp.presence_merger import PresenceMerger
            filtered = PresenceMerger.get_latest_character_locations(
                presences, chapter_order_map=chapter_order_map
            )

        # Agrupar por lugar
        by_place: dict[str, list] = {}
        for presence in filtered:
            by_place.setdefault(presence.place_id, []).append(presence)

        # Renderizar badges en cada nodo
        for place_id, place_presences in by_place.items():
            node = self._nodes.get(place_id)
            if not node:
                continue

            badges = []
            total_count = len(place_presences)
            
            # Si hay más de 3 personajes, mostrar los primeros 3 y 1 badge contador (+N)
            max_individual = 3 if total_count > 4 else total_count

            for i, presence in enumerate(place_presences[:max_individual]):
                char_initial = "?"
                char_full_name = ""
                if character_map:
                    char = character_map.get(presence.character_id)
                    if char:
                        char_initial = char.name[0].upper()
                        char_full_name = char.name

                badge = PresenceBadgeItem(
                    initial=char_initial,
                    confidence=presence.confidence,
                    presence_type=presence.presence_type,
                    index=i,
                    character_name=char_full_name,
                    parent=node,
                )
                badges.append(badge)

            # Badge de multitud si hay excedente (+N)
            if total_count > max_individual:
                overflow_count = total_count - max_individual
                remaining_presences = place_presences[max_individual:]
                remaining_names = []
                for p in remaining_presences:
                    if character_map and p.character_id in character_map:
                        remaining_names.append(character_map[p.character_id].name)
                    else:
                        remaining_names.append("Personaje")

                overflow_badge = PresenceOverflowBadgeItem(
                    overflow_count=overflow_count,
                    remaining_names=remaining_names,
                    index=max_individual,
                    parent=node,
                )
                badges.append(overflow_badge)

            self._presence_badges[place_id] = badges

    def _clear_presence_badges(self) -> None:
        """Elimina todos los badges de presencia actuales de la escena."""
        for badge_list in self._presence_badges.values():
            for badge in badge_list:
                try:
                    # badge.scene() lanza RuntimeError si el objeto C++ ya fue
                    # destruido por scene.clear() antes de que se limpiara el dict.
                    if badge.scene():
                        self.removeItem(badge)
                except RuntimeError:
                    # El objeto C++ subyacente ya fue destruido — ignorar de forma segura.
                    pass
        self._presence_badges.clear()


class PlaceGraphView(QGraphicsView):
    """
    Vista de alto rendimiento con paneo fluido, zoom centrado y fondo adaptativo al tema.
    """
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
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        self._press_pos = None
        self.update_theme()

    def update_theme(self):
        is_dark = ThemeManager.is_dark()
        bg_color = "#121214" if is_dark else "#f5f0ea"
        self.setBackgroundBrush(QBrush(QColor(bg_color)))
        self.setStyleSheet(f"QGraphicsView {{ background: {bg_color}; border: none; }}")
        self.viewport().update()

    def drawBackground(self, painter: QPainter | None, rect: QRectF):
        if painter is None:
            return
        is_dark = ThemeManager.is_dark()
        bg_color = QColor("#121214" if is_dark else "#f5f0ea")
        painter.fillRect(rect, bg_color)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = event.pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if event.button() == Qt.MouseButton.LeftButton and self._press_pos is not None:
            dist = (event.pos() - self._press_pos).manhattanLength()
            self._press_pos = None
            if dist < 6:
                scene_pos = self.mapToScene(event.pos())
                item = self.scene().itemAt(scene_pos, self.transform()) if self.scene() else None
                if not isinstance(item, PlaceNodeItem):
                    if hasattr(self.scene(), "clear_selection_and_focus"):
                        self.scene().clear_selection_and_focus()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta == 0:
            return
        factor = 1.15 if delta > 0 else (1.0 / 1.15)
        self.scale(factor, factor)
        event.accept()
