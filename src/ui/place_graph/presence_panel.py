"""
presence_panel.py — Panel lateral de inspección y control de presencias en el Atlas.
Responsabilidad única: Mostrar lista de personajes detectados/confirmados en el lugar
seleccionado, permitiendo al autor confirmar, cambiar estado o remover presencias.
"""
from __future__ import annotations
from typing import Optional, List, Dict

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QPushButton, QFrame, QComboBox, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from core.models import CharacterPresence, Character, Place
from core.theme_manager import ThemeManager


class PresenceItemWidget(QFrame):
    """Fila visual que representa a un personaje ubicado en el lugar."""
    presence_updated = pyqtSignal(str, str) # char_id, new_type
    presence_removed = pyqtSignal(str)      # char_id

    def __init__(self, presence: CharacterPresence, char_name: str, parent=None):
        super().__init__(parent)
        self.presence = presence
        self.char_name = char_name
        self._setup_ui()

    def _setup_ui(self):
        is_dark = ThemeManager.is_dark()
        bg_card = "#2c2c2e" if is_dark else "#f2f0eb"
        border_col = "#3a3a3c" if is_dark else "#dcd6cd"

        self.setStyleSheet(f"""
            PresenceItemWidget {{
                background-color: {bg_card};
                border: 1px solid {border_col};
                border-radius: 6px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        # Avatar inicial
        initial_lbl = QLabel(self.char_name[:1].upper() if self.char_name else "?")
        initial_lbl.setFixedSize(26, 26)
        initial_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        initial_lbl.setStyleSheet("""
            background-color: #ffd60a22;
            color: #ffd60a;
            border: 1px solid #ffd60a;
            border-radius: 13px;
            font-weight: bold;
            font-size: 11px;
        """)
        layout.addWidget(initial_lbl)

        # Nombre y detalle
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        name_lbl = QLabel(self.char_name)
        name_lbl.setStyleSheet("font-weight: bold; font-size: 11px;")
        info_layout.addWidget(name_lbl)

        conf_pct = int(self.presence.confidence * 100)
        detail_lbl = QLabel(f"Confianza: {conf_pct}%")
        detail_lbl.setStyleSheet("font-size: 9px; color: #8e8e93;")
        info_layout.addWidget(detail_lbl)
        layout.addLayout(info_layout, stretch=1)

        # Combo de tipo de presencia
        self.type_combo = QComboBox()
        self.type_combo.setFixedWidth(95)
        self.type_combo.addItem("Presente", "present")
        self.type_combo.addItem("En tránsito", "transit")
        self.type_combo.addItem("Salida", "departed")

        idx = self.type_combo.findData(self.presence.presence_type)
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        layout.addWidget(self.type_combo)

        # Botón descartar
        btn_del = QPushButton("✕")
        btn_del.setFixedSize(22, 22)
        btn_del.setToolTip("Quitar presencia")
        btn_del.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #8e8e93;
                border: none;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                color: #ff453a;
            }
        """)
        btn_del.clicked.connect(lambda: self.presence_removed.emit(self.presence.character_id))
        layout.addWidget(btn_del)

    def _on_type_changed(self):
        new_type = self.type_combo.currentData()
        self.presence_updated.emit(self.presence.character_id, new_type)


class PresencePanel(QWidget):
    """
    Panel de personajes presentes en la escena del lugar seleccionado.
    """
    presence_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_place: Optional[Place] = None
        self._project_manager = None
        self._setup_ui()

    def set_project_manager(self, pm):
        self._project_manager = pm

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 8, 4, 4)
        root.setSpacing(8)

        # Área de Scroll
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_content = QWidget()
        self.items_layout = QVBoxLayout(self.scroll_content)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(6)
        self.items_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.scroll_content)
        root.addWidget(self.scroll, stretch=1)

    def load_place(self, place: Optional[Place], chapter_id: Optional[str] = None):
        """Carga los personajes presentes en el lugar dado para el capítulo seleccionado."""
        self._current_place = place
        
        while self.items_layout.count() > 0:
            item = self.items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not place:
            empty = QLabel("Selecciona un lugar en el mapa.")
            empty.setStyleSheet("color: #8e8e93; font-style: italic; font-size: 11px;")
            self.items_layout.addWidget(empty)
            return

        if not self._project_manager or not self._project_manager.metadata:
            return

        meta = self._project_manager.metadata
        char_map = {c.id: c.name for c in getattr(meta, "characters", [])}
        all_presences: List[CharacterPresence] = getattr(meta, "presences", [])

        # Si chapter_id es None (Todos los capítulos), mostrar la última ubicación resuelta
        if chapter_id is None:
            from tools.nlp.presence_merger import PresenceMerger
            active_presences = PresenceMerger.get_latest_character_locations(all_presences)
            place_presences = [p for p in active_presences if p.place_id == place.id]
        else:
            from tools.nlp.presence_merger import PresenceMerger
            cap_presences = [
                p for p in all_presences
                if p.chapter_id == chapter_id and p.presence_type in ("present", "transit")
            ]
            merged_cap = PresenceMerger.merge_chapter_presences(cap_presences)
            place_presences = [p for p in merged_cap if p.place_id == place.id]

        if not place_presences:
            empty = QLabel("No hay personajes presentes aquí en esta escena.")
            empty.setStyleSheet("color: #8e8e93; font-style: italic; font-size: 11px; margin-top: 6px;")
            empty.setWordWrap(True)
            self.items_layout.addWidget(empty)
            return

        for presence in place_presences:
            c_name = char_map.get(presence.character_id, "Personaje desconocido")
            widget = PresenceItemWidget(presence, c_name, self.scroll_content)
            widget.presence_updated.connect(self._on_presence_type_updated)
            widget.presence_removed.connect(self._on_presence_removed)
            self.items_layout.addWidget(widget)

    def _on_presence_type_updated(self, char_id: str, new_type: str):
        if not self._project_manager or not self._current_place:
            return
        meta = self._project_manager.metadata
        for p in getattr(meta, "presences", []):
            if p.place_id == self._current_place.id and p.character_id == char_id:
                p.presence_type = new_type
        self.presence_changed.emit()

    def _on_presence_removed(self, char_id: str):
        if not self._project_manager or not self._current_place:
            return
        meta = self._project_manager.metadata
        meta.presences = [
            p for p in getattr(meta, "presences", [])
            if not (p.place_id == self._current_place.id and p.character_id == char_id)
        ]
        self.load_place(self._current_place)
        self.presence_changed.emit()


class PlaceHistoryPanel(QWidget):
    """
    Pestaña de Historial de Visitas y Pasaje:
    Muestra la cronología de todos los personajes que pasaron, estuvieron
    o salieron de este lugar a lo largo de los capítulos de la obra.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_place: Optional[Place] = None
        self._project_manager = None
        self._setup_ui()

    def set_project_manager(self, pm):
        self._project_manager = pm

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 8, 4, 4)
        root.setSpacing(8)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_content = QWidget()
        self.items_layout = QVBoxLayout(self.scroll_content)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(6)
        self.items_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.scroll_content)
        root.addWidget(self.scroll, stretch=1)

    def load_place(self, place: Optional[Place]):
        """Carga el historial completo de apariciones del lugar."""
        self._current_place = place

        while self.items_layout.count() > 0:
            item = self.items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not place:
            empty = QLabel("Selecciona un lugar en el mapa.")
            empty.setStyleSheet("color: #8e8e93; font-style: italic; font-size: 11px;")
            self.items_layout.addWidget(empty)
            return

        if not self._project_manager or not self._project_manager.metadata:
            return

        meta = self._project_manager.metadata
        char_map = {c.id: c.name for c in getattr(meta, "characters", [])}
        
        # Mapear títulos de capítulos y obras
        cap_map = {}
        for obra in meta.obras:
            for libro in obra.libros:
                for cap in libro.capitulos:
                    cap_map[cap.id] = (cap.title, obra.title, cap.in_world_order)

        all_presences: List[CharacterPresence] = getattr(meta, "presences", [])
        place_events = [p for p in all_presences if p.place_id == place.id]

        if not place_events:
            empty = QLabel("Ningún personaje tiene registro de haber visitado este lugar aún.")
            empty.setStyleSheet("color: #8e8e93; font-style: italic; font-size: 11px; margin-top: 6px;")
            empty.setWordWrap(True)
            self.items_layout.addWidget(empty)
            return

        # Ordenar eventos cronológicamente
        def _get_sort_key(p: CharacterPresence):
            info = cap_map.get(p.chapter_id, ("", "", 0))
            return (info[2] or p.in_world_order, p.created_at)

        sorted_events = sorted(place_events, key=_get_sort_key)

        is_dark = ThemeManager.is_dark()
        bg_card = "#2c2c2e" if is_dark else "#f2f0eb"
        border_col = "#3a3a3c" if is_dark else "#dcd6cd"

        for p in sorted_events:
            c_name = char_map.get(p.character_id, "Personaje")
            cap_title, obra_title, order = cap_map.get(p.chapter_id, ("Capítulo desconocido", "", 0))
            
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {bg_card};
                    border: 1px solid {border_col};
                    border-radius: 6px;
                    padding: 4px;
                }}
            """)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(8, 6, 8, 6)
            cl.setSpacing(3)

            # Fila superior: Nombre y Estado
            top_h = QHBoxLayout()
            name_lbl = QLabel(f"<b>{c_name}</b>")
            name_lbl.setStyleSheet("font-size: 11px;")
            top_h.addWidget(name_lbl)
            top_h.addStretch()

            type_info = {
                "present": ("Presente / Llegada", "#ffd60a"),
                "transit": ("En Tránsito", "#0a84ff"),
                "departed": ("Partida / Salida", "#ff453a"),
                "referenced": ("Mención", "#8e8e93"),
            }.get(p.presence_type, (p.presence_type, "#ffd60a"))

            pill = QLabel(type_info[0])
            pill.setStyleSheet(f"""
                background-color: {type_info[1]}22;
                color: {type_info[1]};
                border: 1px solid {type_info[1]}66;
                border-radius: 3px;
                font-size: 9px;
                font-weight: bold;
                padding: 1px 4px;
            """)
            top_h.addWidget(pill)
            cl.addLayout(top_h)

            # Fila inferior: Capítulo y Obra
            order_prefix = f"#{order} " if order > 0 else ""
            cap_lbl = QLabel(f"📖 {order_prefix}{cap_title} ({obra_title})" if obra_title else f"📖 {order_prefix}{cap_title}")
            cap_lbl.setStyleSheet("font-size: 10px; color: #8e8e93;")
            cl.addWidget(cap_lbl)

            if p.verb_matched:
                verb_lbl = QLabel(f"<i>Verbo detectado: \"{p.verb_matched}\"</i>")
                verb_lbl.setStyleSheet("font-size: 9px; color: #8e8e93; font-style: italic;")
                cl.addWidget(verb_lbl)

            self.items_layout.addWidget(card)

