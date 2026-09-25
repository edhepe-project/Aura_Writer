"""
presence_panel.py - Panel lateral de control manual de presencias en el Atlas.

El autor ubica y mueve personajes entre escenarios de forma explicita.
El sistema es 100% manual: sin deteccion automatica NLP.

Modulos relacionados:
  presence_item.py  -- _MoveCharacterDialog + PresenceItemWidget
  history_panel.py  -- PlaceHistoryPanel + _ChapterGroupHeader
"""
from __future__ import annotations
from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea,
    QPushButton, QFrame, QComboBox,
)
from PyQt6.QtCore import Qt, pyqtSignal

from core.models import CharacterPresence, Place
from core.theme_manager import ThemeManager
from .presence_item import PresenceItemWidget, _STATUS_OPTIONS

# Re-exportar para compatibilidad con imports existentes
from .presence_item import PresenceItemWidget               # noqa: F401
from .history_panel import PlaceHistoryPanel                # noqa: F401


# ---------------------------------------------------------------------------
#  Panel principal de presencias (pestana "En Escena")
# ---------------------------------------------------------------------------
class PresencePanel(QWidget):
    """
    Panel de gestion manual de personajes en el lugar seleccionado del Atlas.

    Flujo de uso del autor:
      1. Clic en un lugar del mapa -> el panel muestra el header con ese lugar.
      2. Seleccionar el capitulo en la toolbar (o dejar 'Todos').
      3. En el formulario: elegir personaje + estado inicial -> Colocar.
      4. Las cards aparecen con boton '->' para mover y 'x' para quitar.
    """

    presence_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_place: Optional[Place]    = None
        self._current_chapter_id: Optional[str] = None
        self._project_manager                   = None
        self._setup_ui()

    def set_project_manager(self, pm) -> None:
        self._project_manager = pm

    # -- Construccion de la UI -----------------------------------------------

    def _setup_ui(self) -> None:
        is_dark = ThemeManager.is_dark()
        fg_accent = "#ffd60a" if is_dark else "#d97706"
        fg_sec    = "#8e8e93" if is_dark else "#64748b"
        ctx_bg    = "rgba(255, 214, 10, 0.08)" if is_dark else "rgba(217, 119, 6, 0.08)"
        ctx_bord  = "rgba(255, 214, 10, 0.3)" if is_dark else "rgba(217, 119, 6, 0.3)"

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 6, 0, 4)
        root.setSpacing(10)

        # -- Bloque de contexto: lugar + capitulo activo ---------------------
        ctx_frame = QFrame()
        ctx_frame.setStyleSheet(f"""
            QFrame {{
                background: {ctx_bg};
                border: 1px solid {ctx_bord};
                border-radius: 8px;
            }}
        """)
        ctx_lay = QVBoxLayout(ctx_frame)
        ctx_lay.setContentsMargins(12, 8, 12, 8)
        ctx_lay.setSpacing(2)

        self.lbl_place_ctx = QLabel("Sin lugar seleccionado")
        self.lbl_place_ctx.setStyleSheet(
            f"font-weight: bold; font-size: 12px; color: {fg_accent};"
        )
        ctx_lay.addWidget(self.lbl_place_ctx)

        self.lbl_chapter_ctx = QLabel("Todos los capítulos")
        self.lbl_chapter_ctx.setStyleSheet(f"font-size: 10px; color: {fg_sec};")
        ctx_lay.addWidget(self.lbl_chapter_ctx)
        root.addWidget(ctx_frame)

        # -- Hint: seleccionar capitulo primero ------------------------------
        hint_bg   = "rgba(10, 132, 255, 0.08)" if is_dark else "rgba(37, 99, 235, 0.08)"
        hint_bord = "rgba(10, 132, 255, 0.3)" if is_dark else "rgba(37, 99, 235, 0.3)"
        hint_fg   = "#0a84ff" if is_dark else "#2563eb"
        hint_sub  = "#8e8e93" if is_dark else "#64748b"

        self._chapter_hint = QFrame()
        self._chapter_hint.setStyleSheet(f"""
            QFrame {{
                background: {hint_bg};
                border: 1px solid {hint_bord};
                border-radius: 8px;
            }}
        """)
        hint_lay = QVBoxLayout(self._chapter_hint)
        hint_lay.setContentsMargins(12, 10, 12, 10)
        hint_lay.setSpacing(4)
        hint_icon = QLabel("Selecciona un capítulo para editar")
        hint_icon.setStyleSheet(f"font-weight: bold; font-size: 11px; color: {hint_fg};")
        hint_lay.addWidget(hint_icon)
        hint_desc = QLabel(
            "La vista Todos los capítulos es solo de lectura.\n"
            "Elige un capítulo específico en la toolbar para\n"
            "colocar o mover personajes en este escenario."
        )
        hint_desc.setStyleSheet(f"font-size: 10px; color: {hint_sub};")
        hint_desc.setWordWrap(True)
        hint_lay.addWidget(hint_desc)
        root.addWidget(self._chapter_hint)
        self._chapter_hint.setVisible(False)

        # -- Formulario de asignacion ----------------------------------------
        self._form_frame = QFrame()
        self._form_frame.setStyleSheet("QFrame { background: transparent; border: none; }")
        form_lay = QVBoxLayout(self._form_frame)
        form_lay.setContentsMargins(0, 0, 0, 0)
        form_lay.setSpacing(6)

        form_lay.addWidget(self._step_label("1", "Selecciona el personaje"))
        self.combo_add_char = QComboBox()
        self.combo_add_char.setFixedHeight(30)
        self.combo_add_char.setToolTip("Personaje que quieres ubicar en este escenario")
        form_lay.addWidget(self.combo_add_char)

        form_lay.addWidget(self._step_label("2", "Estado inicial"))
        self.combo_status = QComboBox()
        self.combo_status.setFixedHeight(30)
        for label, data in _STATUS_OPTIONS:
            self.combo_status.addItem(label, data)
        form_lay.addWidget(self.combo_status)

        btn_bg     = "#ffd60a" if is_dark else "#d97706"
        btn_fg     = "#000000" if is_dark else "#ffffff"
        btn_hover  = "#ffe033" if is_dark else "#b45309"
        btn_press  = "#e6c009" if is_dark else "#92400e"
        btn_dis_bg = "#2c2c2e" if is_dark else "#e5e7eb"
        btn_dis_fg = "#636366" if is_dark else "#9ca3af"

        self.btn_add = QPushButton("  Colocar personaje aquí")
        self.btn_add.setFixedHeight(34)
        self.btn_add.setToolTip("Registrar la ubicación del personaje en el capítulo seleccionado")
        self.btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add.setStyleSheet(f"""
            QPushButton {{
                background: {btn_bg}; color: {btn_fg}; font-weight: bold;
                font-size: 12px; border: none; border-radius: 8px;
            }}
            QPushButton:hover   {{ background: {btn_hover}; }}
            QPushButton:pressed {{ background: {btn_press}; }}
            QPushButton:disabled {{ background: {btn_dis_bg}; color: {btn_dis_fg}; }}
        """)
        self.btn_add.clicked.connect(self._on_add_character_manual)
        form_lay.addWidget(self.btn_add)
        root.addWidget(self._form_frame)

        # -- Separador y titulo de lista ------------------------------------
        sep_col = "#3a3a3c" if is_dark else "#e2e8f0"
        title_col = "#636366" if is_dark else "#64748b"
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {sep_col}; margin: 2px 0;")
        root.addWidget(sep)

        self.lbl_list_title = QLabel("PERSONAJES AQUÍ AHORA")
        self.lbl_list_title.setStyleSheet(
            f"font-size: 9px; font-weight: bold; color: {title_col}; letter-spacing: 0.8px;"
        )
        root.addWidget(self.lbl_list_title)

        # -- Area de scroll con las cards -----------------------------------
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_content = QWidget()
        self.items_layout   = QVBoxLayout(self.scroll_content)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(5)
        self.items_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.scroll_content)
        root.addWidget(self.scroll, stretch=1)

    @staticmethod
    def _step_label(number: str, text: str) -> QLabel:
        lbl = QLabel(f"  {number}   {text}")
        lbl.setStyleSheet(
            "font-size: 10px; font-weight: bold; color: #8e8e93; letter-spacing: 0.3px;"
        )
        return lbl

    # -- Carga de datos -------------------------------------------------------

    def load_place(self, place: Optional[Place], chapter_id: Optional[str] = None) -> None:
        """Carga los personajes presentes en el lugar para el capitulo dado."""
        self._current_place      = place
        self._current_chapter_id = chapter_id

        self._clear_items()
        self._update_context_labels(place, chapter_id)
        self._populate_char_combo()

        has_chapter = chapter_id is not None
        self._form_frame.setVisible(has_chapter)
        self._chapter_hint.setVisible(not has_chapter)

        if not place:
            self._show_empty("Selecciona un lugar en el mapa.")
            self.btn_add.setEnabled(False)
            return

        self.btn_add.setEnabled(has_chapter)

        if not self._project_manager or not self._project_manager.metadata:
            return

        meta     = self._project_manager.metadata
        char_map = {c.id: c.name for c in getattr(meta, "characters", [])}
        all_pres: List[CharacterPresence] = getattr(meta, "presences", [])

        if chapter_id is None:
            from tools.nlp.presence_merger import PresenceMerger
            active = PresenceMerger.get_latest_character_locations(all_pres)
            place_presences = [p for p in active if p.place_id == place.id]
        else:
            from tools.nlp.presence_merger import PresenceMerger
            cap_pres = [
                p for p in all_pres
                if p.chapter_id == chapter_id and p.presence_type in ("present", "transit")
            ]
            merged = PresenceMerger.merge_chapter_presences(cap_pres)
            place_presences = [p for p in merged if p.place_id == place.id]

        if not place_presences:
            if chapter_id is None:
                self._show_empty("Ningun personaje tiene registro aqui todavia.")
            else:
                self._show_empty(
                    "Ningun personaje esta aqui en este capitulo.\n"
                    "Usa el formulario de arriba para anadirlos."
                )
            return

        all_places = getattr(meta, "places", [])
        for presence in place_presences:
            c_name = char_map.get(presence.character_id, "Personaje desconocido")
            widget = PresenceItemWidget(
                presence, c_name, places=all_places, parent=self.scroll_content
            )
            widget.presence_updated.connect(self._on_presence_type_updated)
            widget.presence_removed.connect(self._on_presence_removed)
            widget.presence_moved.connect(self._on_presence_moved)
            self.items_layout.addWidget(widget)

    def _update_context_labels(self, place: Optional[Place], chapter_id: Optional[str]) -> None:
        if place:
            self.lbl_place_ctx.setText(f"  {place.name}")
        else:
            self.lbl_place_ctx.setText("Sin lugar seleccionado")

        if self._project_manager and self._project_manager.metadata and chapter_id:
            meta      = self._project_manager.metadata
            cap_title = None
            for obra in getattr(meta, "obras", []):
                for libro in getattr(obra, "libros", []):
                    for c in getattr(libro, "capitulos", []):
                        if c.id == chapter_id:
                            raw = (c.title or "").strip()
                            cap_title = raw or (
                                f"Capitulo {c.in_world_order}" if c.in_world_order else "Capitulo actual"
                            )
                            break
            self.lbl_chapter_ctx.setText(
                f"Asignando en: {cap_title}" if cap_title else "Todos los capitulos"
            )
        else:
            self.lbl_chapter_ctx.setText("Vista global - Todos los capitulos")

    def _populate_char_combo(self) -> None:
        self.combo_add_char.blockSignals(True)
        self.combo_add_char.clear()
        self.combo_add_char.addItem("-- Elige un personaje --", None)
        if self._project_manager and self._project_manager.metadata:
            chars = getattr(self._project_manager.metadata, "characters", [])
            for c in chars:
                self.combo_add_char.addItem(f"  {c.name}", c.id)
        self.combo_add_char.blockSignals(False)

    def _clear_items(self) -> None:
        while self.items_layout.count() > 0:
            item = self.items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _show_empty(self, message: str) -> None:
        lbl = QLabel(message)
        lbl.setStyleSheet("color: #636366; font-style: italic; font-size: 11px; margin: 6px 2px;")
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.items_layout.addWidget(lbl)

    # -- Acciones del usuario ------------------------------------------------

    def _on_add_character_manual(self) -> None:
        if not self._current_place or not self._project_manager:
            return
        char_id = self.combo_add_char.currentData()
        if not char_id:
            return
        status = self.combo_status.currentData() or "present"
        meta   = self._project_manager.metadata
        if not meta:
            return
        chapter_id = self._current_chapter_id or self._first_chapter_id(meta)
        if not hasattr(meta, "presences") or meta.presences is None:
            meta.presences = []
        meta.presences = [
            p for p in meta.presences
            if not (p.character_id == char_id and p.chapter_id == chapter_id)
        ]
        new_p = CharacterPresence(
            character_id=char_id, place_id=self._current_place.id,
            chapter_id=chapter_id, presence_type=status,
            confidence=1.0, is_manual=True,
            matched_text="Ubicado manualmente por el autor",
        )
        meta.presences.append(new_p)
        self.load_place(self._current_place, chapter_id=self._current_chapter_id)
        self.presence_changed.emit()

    def _on_presence_moved(self, char_id: str, new_place_id: str) -> None:
        if not self._project_manager or not self._current_place:
            return
        meta = self._project_manager.metadata
        if not meta:
            return
        chapter_id = self._current_chapter_id or self._first_chapter_id(meta)
        if not hasattr(meta, "presences") or meta.presences is None:
            meta.presences = []
        for p in meta.presences:
            if (p.character_id == char_id and p.chapter_id == chapter_id
                    and p.place_id == self._current_place.id):
                p.presence_type = "departed"
                p.matched_text  = f"Partio hacia {new_place_id}"
        new_p = CharacterPresence(
            character_id=char_id, place_id=new_place_id,
            chapter_id=chapter_id, presence_type="present",
            confidence=1.0, is_manual=True,
            matched_text="Trasladado manualmente por el autor",
        )
        meta.presences.append(new_p)
        self.load_place(self._current_place, chapter_id=self._current_chapter_id)
        self.presence_changed.emit()

    def _on_presence_type_updated(self, char_id: str, new_type: str) -> None:
        if not self._project_manager or not self._current_place:
            return
        meta       = self._project_manager.metadata
        chapter_id = self._current_chapter_id
        for p in getattr(meta, "presences", []):
            if (p.place_id == self._current_place.id and p.character_id == char_id
                    and (chapter_id is None or p.chapter_id == chapter_id)):
                p.presence_type = new_type
        self.presence_changed.emit()

    def _on_presence_removed(self, char_id: str) -> None:
        if not self._project_manager or not self._current_place:
            return
        meta       = self._project_manager.metadata
        chapter_id = self._current_chapter_id
        meta.presences = [
            p for p in getattr(meta, "presences", [])
            if not (p.place_id == self._current_place.id and p.character_id == char_id
                    and (chapter_id is None or p.chapter_id == chapter_id))
        ]
        self.load_place(self._current_place, chapter_id=chapter_id)
        self.presence_changed.emit()

    @staticmethod
    def _first_chapter_id(meta) -> str:
        for obra in getattr(meta, "obras", []):
            for libro in getattr(obra, "libros", []):
                if libro.capitulos:
                    return libro.capitulos[0].id
        return "cap_manual"
