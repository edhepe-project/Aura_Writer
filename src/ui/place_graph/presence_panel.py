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
    presence_updated = pyqtSignal(str, str)     # char_id, new_type
    presence_removed = pyqtSignal(str)          # char_id
    presence_moved = pyqtSignal(str, str)       # char_id, new_place_id

    def __init__(self, presence: CharacterPresence, char_name: str, places: list[Place] = None, parent=None):
        super().__init__(parent)
        self.presence = presence
        self.char_name = char_name
        self.places = places or []
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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Fila superior: Avatar, Nombre, Estado y Eliminar
        row1 = QHBoxLayout()
        row1.setSpacing(6)

        # Avatar inicial
        initial_lbl = QLabel(self.char_name[:1].upper() if self.char_name else "?")
        initial_lbl.setFixedSize(24, 24)
        initial_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        initial_lbl.setStyleSheet("""
            background-color: #ffd60a22;
            color: #ffd60a;
            border: 1px solid #ffd60a;
            border-radius: 12px;
            font-weight: bold;
            font-size: 11px;
        """)
        row1.addWidget(initial_lbl)

        # Nombre
        name_lbl = QLabel(self.char_name)
        name_lbl.setStyleSheet("font-weight: bold; font-size: 11px;")
        row1.addWidget(name_lbl, stretch=1)

        # Combo de tipo de presencia
        self.type_combo = QComboBox()
        self.type_combo.setFixedWidth(90)
        self.type_combo.addItem("Presente", "present")
        self.type_combo.addItem("En tránsito", "transit")
        self.type_combo.addItem("Salida", "departed")

        idx = self.type_combo.findData(self.presence.presence_type)
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        row1.addWidget(self.type_combo)

        # Botón descartar
        btn_del = QPushButton("✕")
        btn_del.setFixedSize(20, 20)
        btn_del.setToolTip("Quitar personaje de este lugar")
        btn_del.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #8e8e93;
                border: none;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { color: #ff453a; }
        """)
        btn_del.clicked.connect(lambda: self.presence_removed.emit(self.presence.character_id))
        row1.addWidget(btn_del)
        layout.addLayout(row1)

        # Fila inferior: Mover a otro escenario
        if self.places:
            row2 = QHBoxLayout()
            row2.setSpacing(4)

            lbl_move = QLabel("📍 Mover a:")
            lbl_move.setStyleSheet("font-size: 9px; color: #8e8e93;")
            row2.addWidget(lbl_move)

            self.move_combo = QComboBox()
            self.move_combo.setToolTip("Trasladar este personaje a otro lugar en esta escena")
            self.move_combo.setStyleSheet("font-size: 10px; padding: 2px 4px;")
            self.move_combo.addItem("Seleccionar destino...", "")

            for p in self.places:
                if p.id != self.presence.place_id:
                    self.move_combo.addItem(f"→ {p.name}", p.id)

            self.move_combo.currentIndexChanged.connect(self._on_move_changed)
            row2.addWidget(self.move_combo, stretch=1)
            layout.addLayout(row2)

    def _on_type_changed(self):
        new_type = self.type_combo.currentData()
        self.presence_updated.emit(self.presence.character_id, new_type)

    def _on_move_changed(self):
        target_place_id = self.move_combo.currentData()
        if target_place_id:
            self.presence_moved.emit(self.presence.character_id, target_place_id)


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

        # Formulario para añadir presencia manualmente
        add_box = QFrame()
        add_box.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 214, 10, 0.06);
                border: 1px dashed rgba(255, 214, 10, 0.3);
                border-radius: 6px;
            }
        """)
        add_layout = QVBoxLayout(add_box)
        add_layout.setContentsMargins(8, 6, 8, 6)
        add_layout.setSpacing(4)

        self.lbl_cap_status = QLabel("📌 Asignando en: 📖 Todos los cap.")
        self.lbl_cap_status.setStyleSheet("font-size: 10px; font-weight: bold; color: #ffd60a;")
        add_layout.addWidget(self.lbl_cap_status)

        abl = QHBoxLayout()
        abl.setContentsMargins(0, 0, 0, 0)
        abl.setSpacing(6)

        self.combo_add_char = QComboBox()
        self.combo_add_char.setToolTip("Seleccionar personaje para ubicar en este escenario")
        abl.addWidget(self.combo_add_char, stretch=1)

        btn_add = QPushButton("➕ Ubicar")
        btn_add.setToolTip("Ubicar personaje seleccionado en este lugar")
        btn_add.setStyleSheet("""
            QPushButton {
                background-color: #ffd60a;
                color: #000000;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QPushButton:hover { background-color: #ffe033; }
        """)
        btn_add.clicked.connect(self._on_add_character_manual)
        abl.addWidget(btn_add)
        add_layout.addLayout(abl)

        root.addWidget(add_box)

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
        self._current_chapter_id = chapter_id
        
        while self.items_layout.count() > 0:
            item = self.items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Actualizar etiqueta del capítulo activo
        if self._project_manager and self._project_manager.metadata:
            meta = self._project_manager.metadata
            cap_title = None
            if chapter_id:
                for obra in getattr(meta, "obras", []):
                    for libro in getattr(obra, "libros", []):
                        for c in getattr(libro, "capitulos", []):
                            if c.id == chapter_id:
                                cap_title = f"Cap. {c.in_world_order}: {c.title}"
                                break

            if cap_title:
                self.lbl_cap_status.setText(f"📌 Asignando en: {cap_title}")
            else:
                self.lbl_cap_status.setText("📌 Asignando en: 📖 Todos los capítulos (Global)")

        # Poblar el combo de personajes
        self.combo_add_char.clear()
        if self._project_manager and self._project_manager.metadata:
            chars = getattr(self._project_manager.metadata, "characters", [])
            for c in chars:
                self.combo_add_char.addItem(f"👤 {c.name}", c.id)

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

        all_places = getattr(meta, "places", [])

        for presence in place_presences:
            c_name = char_map.get(presence.character_id, "Personaje desconocido")
            widget = PresenceItemWidget(presence, c_name, places=all_places, parent=self.scroll_content)
            widget.presence_updated.connect(self._on_presence_type_updated)
            widget.presence_removed.connect(self._on_presence_removed)
            widget.presence_moved.connect(self._on_presence_moved)
            self.items_layout.addWidget(widget)

    def _on_presence_moved(self, char_id: str, new_place_id: str):
        """Traslada el personaje del lugar actual al nuevo lugar de destino."""
        if not self._project_manager or not self._current_place:
            return
        meta = self._project_manager.metadata
        if not meta:
            return

        chapter_id = getattr(self, "_current_chapter_id", None)
        if not chapter_id:
            for obra in getattr(meta, "obras", []):
                for libro in getattr(obra, "libros", []):
                    if libro.capitulos:
                        chapter_id = libro.capitulos[0].id
                        break
                if chapter_id:
                    break

        if not chapter_id:
            chapter_id = "cap_manual"

        if not hasattr(meta, "presences") or meta.presences is None:
            meta.presences = []

        # 1. En lugar de borrar sin dejar rastro, marcar la presencia previa en este capítulo como 'departed' (Salida)
        #    para conservar el registro histórico en el lugar donde estuvo antes.
        for p in meta.presences:
            if p.character_id == char_id and p.chapter_id == chapter_id and p.place_id == self._current_place.id:
                p.presence_type = "departed"
                p.matched_text = f"Partió hacia {new_place_id}"

        # 2. Crear nueva presencia activa 'present' en el nuevo lugar de destino
        new_p = CharacterPresence(
            character_id=char_id,
            place_id=new_place_id,
            chapter_id=chapter_id,
            presence_type="present",
            confidence=1.0,
            is_manual=True,
            matched_text="Trasladado manualmente por el autor"
        )
        meta.presences.append(new_p)

        self.load_place(self._current_place, chapter_id=self._current_chapter_id)
        self.presence_changed.emit()

    def _on_add_character_manual(self):
        """Añade manualmente un personaje al lugar y capítulo actual."""
        if not self._current_place or not self._project_manager:
            return
        char_id = self.combo_add_char.currentData()
        if not char_id:
            return

        meta = self._project_manager.metadata
        if not meta:
            return

        chapter_id = getattr(self, "_current_chapter_id", None)
        if not chapter_id:
            # Si se está en "Todos los capítulos", tomar el primer capítulo disponible
            for obra in getattr(meta, "obras", []):
                for libro in getattr(obra, "libros", []):
                    if libro.capitulos:
                        chapter_id = libro.capitulos[0].id
                        break
                if chapter_id:
                    break

        if not chapter_id:
            chapter_id = "cap_manual"

        # Remover cualquier presencia previa del mismo personaje en ese capítulo
        if not hasattr(meta, "presences") or meta.presences is None:
            meta.presences = []

        meta.presences = [
            p for p in meta.presences
            if not (p.character_id == char_id and p.chapter_id == chapter_id)
        ]

        # Agregar nueva presencia manual
        new_presence = CharacterPresence(
            character_id=char_id,
            place_id=self._current_place.id,
            chapter_id=chapter_id,
            presence_type="present",
            confidence=1.0,
            is_manual=True,
            matched_text="Asignado manualmente por el autor"
        )
        meta.presences.append(new_presence)
        
        # Recargar y emitir señal para refrescar el mapa de escenarios
        self.load_place(self._current_place, chapter_id=self._current_chapter_id)
        self.presence_changed.emit()

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
        self.load_place(self._current_place, chapter_id=getattr(self, "_current_chapter_id", None))
        self.presence_changed.emit()


class PlaceHistoryPanel(QWidget):
    """
    Pestaña de Historial de Visitas y Pasaje.
    Muestra la cronología agrupada por capítulo (headers colapsables).
    Los últimos 3 capítulos se expanden automáticamente.
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
        self.items_layout.setSpacing(4)
        self.items_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.scroll_content)
        root.addWidget(self.scroll, stretch=1)

    # ------------------------------------------------------------------
    def _clear_layout(self):
        while self.items_layout.count() > 0:
            item = self.items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def load_place(self, place: Optional[Place]):
        """Carga el historial completo agrupado por capítulo."""
        self._current_place = place
        self._clear_layout()

        if not place:
            lbl = QLabel("Selecciona un lugar en el mapa.")
            lbl.setStyleSheet("color: #8e8e93; font-style: italic; font-size: 11px;")
            self.items_layout.addWidget(lbl)
            return

        if not self._project_manager or not self._project_manager.metadata:
            return

        meta = self._project_manager.metadata
        char_map: Dict[str, str] = {c.id: c.name for c in getattr(meta, "characters", [])}

        # Mapa capítulo_id → (título, obra, orden)
        cap_map: Dict[str, tuple] = {}
        for obra in meta.obras:
            for libro in obra.libros:
                for cap in libro.capitulos:
                    cap_map[cap.id] = (cap.title, obra.title, cap.in_world_order)

        all_presences: List[CharacterPresence] = getattr(meta, "presences", [])
        place_events = [p for p in all_presences if p.place_id == place.id]

        if not place_events:
            lbl = QLabel("Ningún personaje tiene registro de haber visitado este lugar aún.")
            lbl.setStyleSheet("color: #8e8e93; font-style: italic; font-size: 11px; margin-top: 6px;")
            lbl.setWordWrap(True)
            self.items_layout.addWidget(lbl)
            return

        # ── Ordenar y agrupar por capítulo ──────────────────────────────────
        def _sort_key(p: CharacterPresence):
            info = cap_map.get(p.chapter_id, ("", "", 0))
            return (info[2] or p.in_world_order, p.created_at)

        sorted_events = sorted(place_events, key=_sort_key)

        groups: Dict[str, List[CharacterPresence]] = {}
        group_order: List[str] = []
        for p in sorted_events:
            if p.chapter_id not in groups:
                groups[p.chapter_id] = []
                group_order.append(p.chapter_id)
            groups[p.chapter_id].append(p)

        is_dark = ThemeManager.is_dark()
        AUTO_EXPAND_LAST = 3
        expanded_ids = set(group_order[-AUTO_EXPAND_LAST:])

        TYPE_INFO = {
            "present":    ("Presente",  "#ffd60a"),
            "transit":    ("Tránsito",  "#0a84ff"),
            "departed":   ("Salida",    "#ff453a"),
            "referenced": ("Mención",   "#8e8e93"),
        }

        for cap_id in group_order:
            presences_in_cap = groups[cap_id]
            cap_title, obra_title, order = cap_map.get(cap_id, ("Capítulo desconocido", "", 0))
            is_expanded = cap_id in expanded_ids
            is_latest   = cap_id == group_order[-1]

            # ── Header colapsable ────────────────────────────────────────────
            header = _ChapterGroupHeader(
                cap_title=cap_title,
                obra_title=obra_title,
                order=order,
                count=len(presences_in_cap),
                expanded=is_expanded,
                is_latest=is_latest,
                is_dark=is_dark,
            )
            self.items_layout.addWidget(header)

            # ── Filas compactas de presencias ────────────────────────────────
            rows_widget = QWidget()
            rows_layout = QVBoxLayout(rows_widget)
            rows_layout.setContentsMargins(12, 2, 4, 4)
            rows_layout.setSpacing(3)

            for p in presences_in_cap:
                c_name = char_map.get(p.character_id, "Personaje desconocido")
                type_label, type_color = TYPE_INFO.get(p.presence_type, (p.presence_type, "#ffd60a"))

                row = QFrame()
                row_bg = "#242426" if is_dark else "#f5f2ec"
                row.setStyleSheet(f"""
                    QFrame {{
                        background: {row_bg};
                        border: none;
                        border-left: 2px solid {type_color}66;
                        border-radius: 3px;
                    }}
                """)
                row_l = QHBoxLayout(row)
                row_l.setContentsMargins(8, 4, 8, 4)
                row_l.setSpacing(6)

                av = QLabel(c_name[:1].upper())
                av.setFixedSize(20, 20)
                av.setAlignment(Qt.AlignmentFlag.AlignCenter)
                av.setStyleSheet(f"""
                    background: {type_color}22;
                    color: {type_color};
                    border: 1px solid {type_color}66;
                    border-radius: 10px;
                    font-weight: bold;
                    font-size: 9px;
                """)
                row_l.addWidget(av)

                fg = "#f2f2f7" if is_dark else "#1c1c1e"
                name_lbl = QLabel(c_name)
                name_lbl.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {fg};")
                row_l.addWidget(name_lbl, stretch=1)

                pill = QLabel(type_label)
                pill.setStyleSheet(f"""
                    background: {type_color}22;
                    color: {type_color};
                    border: 1px solid {type_color}55;
                    border-radius: 3px;
                    font-size: 9px;
                    font-weight: bold;
                    padding: 1px 5px;
                """)
                row_l.addWidget(pill)

                if p.verb_matched:
                    verb_lbl = QLabel(f'"{p.verb_matched}"')
                    verb_lbl.setStyleSheet("font-size: 9px; color: #636366; font-style: italic;")
                    row_l.addWidget(verb_lbl)

                rows_layout.addWidget(row)

            rows_widget.setVisible(is_expanded)
            header.toggled.connect(rows_widget.setVisible)
            self.items_layout.addWidget(rows_widget)


# ── Header colapsable de capítulo ───────────────────────────────────────────

class _ChapterGroupHeader(QFrame):
    """Header colapsable para agrupar presencias de un mismo capítulo."""
    toggled = pyqtSignal(bool)

    def __init__(self, cap_title: str, obra_title: str, order: int,
                 count: int, expanded: bool, is_latest: bool, is_dark: bool,
                 parent=None):
        super().__init__(parent)
        self._expanded = expanded
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        accent  = "#ffd60a" if is_latest else ("#5e5ce6" if is_dark else "#4f46e5")
        bg      = "#1e1e20" if is_dark else "#ede9e0"
        fg      = "#f2f2f7" if is_dark else "#1c1c1e"
        sub_fg  = "#8e8e93" if is_dark else "#6e6e73"

        self.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: 1px solid {accent}44;
                border-radius: 6px;
            }}
            QFrame:hover {{ border-color: {accent}88; }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 7, 10, 7)
        layout.setSpacing(6)

        self._arrow = QLabel("▾" if expanded else "▸")
        self._arrow.setStyleSheet(f"color: {accent}; font-size: 12px; font-weight: bold;")
        self._arrow.setFixedWidth(14)
        layout.addWidget(self._arrow)

        order_str = f"#{order} · " if order > 0 else ""
        title_lbl = QLabel(f"{order_str}{cap_title}")
        title_lbl.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {fg};")
        layout.addWidget(title_lbl, stretch=1)

        if obra_title:
            obra_lbl = QLabel(obra_title)
            obra_lbl.setStyleSheet(f"font-size: 9px; color: {sub_fg};")
            layout.addWidget(obra_lbl)

        badge = QLabel(f"{count} {'personaje' if count == 1 else 'personajes'}")
        badge.setStyleSheet(f"""
            background: {accent}22; color: {accent};
            border: 1px solid {accent}55; border-radius: 3px;
            font-size: 9px; font-weight: bold; padding: 1px 5px;
        """)
        layout.addWidget(badge)

    def mousePressEvent(self, event):
        self._expanded = not self._expanded
        self._arrow.setText("▾" if self._expanded else "▸")
        self.toggled.emit(self._expanded)
        super().mousePressEvent(event)

