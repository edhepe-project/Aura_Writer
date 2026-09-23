"""
presence_panel.py - Panel lateral de control manual de presencias en el Atlas.

El autor ubica y mueve personajes entre escenarios de forma explicita.
El sistema es 100% manual: sin deteccion automatica NLP.

Diseno de UX:
  [Header de contexto]  -> lugar activo + capitulo seleccionado
  [Formulario]          -> 1. Personaje, 2. Estado, boton Colocar
  [PERSONAJES AQUI]     -> cards compactas con borde de color + boton Mover y Eliminar

  Card de personaje:
    [Av]  Nombre del Personaje   [estado combo]  [->]  [x]
          ^avatar circular       ^Presente/etc   ^Mover ^Quitar

NOTA TECNICA - PresenceMerger (tools/nlp/presence_merger.py)
Se usa PresenceMerger.merge_chapter_presences() SOLO para deduplicar presencias
manuales del mismo personaje en el mismo capitulo (ej: si el autor lo movio
varias veces y quedaron registros duplicados).

PARA RETOMAR EL MOTOR NLP EN EL FUTURO:
  - PresenceMerger consolidara presencias detectadas vs manuales.
  - La prioridad siempre sera: is_manual=True > automatica.
  - Ver presence_analyzer.py para el roadmap detallado de reactivacion.
"""
from __future__ import annotations
from typing import Optional, List, Dict

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QPushButton, QFrame, QComboBox, QSizePolicy, QDialog,
    QListWidget, QListWidgetItem, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from core.models import CharacterPresence, Character, Place
from core.theme_manager import ThemeManager


# Paleta de colores y emojis por tipo de presencia
_TYPE_INFO: dict[str, tuple[str, str, str]] = {
    "present":    ("Presente",    "#30d158", "bullet_green"),
    "transit":    ("En transito", "#0a84ff", "bullet_blue"),
    "departed":   ("Salida",      "#ff453a", "bullet_red"),
    "referenced": ("Mencion",     "#8e8e93", "bullet_gray"),
}

_STATUS_OPTIONS = [
    ("Presente",    "present"),
    ("En transito", "transit"),
    ("Salida",      "departed"),
]


# ---------------------------------------------------------------------------
#  Dialogo modal para elegir destino al mover un personaje
# ---------------------------------------------------------------------------
class _MoveCharacterDialog(QDialog):
    """Popup para elegir el destino al mover un personaje a otro escenario."""

    def __init__(self, char_name: str, places: list[Place], current_place_id: str,
                 is_dark: bool, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Mover personaje")
        self.setFixedSize(340, 260)
        self.selected_place_id: str | None = None

        bg   = "#1c1c1e" if is_dark else "#f5f0ea"
        fg   = "#f2f2f7" if is_dark else "#1c1c1e"
        card = "#2c2c2e" if is_dark else "#ffffff"
        bord = "#3a3a3c" if is_dark else "#d4cfc8"

        self.setStyleSheet(f"""
            QDialog  {{ background: {bg}; }}
            QLabel   {{ color: {fg}; font-size: 12px; }}
            QListWidget {{
                background: {card}; border: 1px solid {bord};
                border-radius: 6px; color: {fg}; font-size: 11px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 6px 10px;
                border-bottom: 1px solid {bord};
            }}
            QListWidget::item:selected {{
                background: #0a84ff; color: #fff; border-radius: 4px;
            }}
            QPushButton {{
                background: #0a84ff; color: #fff; border: none;
                border-radius: 6px; padding: 6px 14px; font-weight: bold;
            }}
            QPushButton:hover {{ background: #3399ff; }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel(f"A donde se mueve <b>{char_name}</b>?")
        title.setWordWrap(True)
        layout.addWidget(title)

        hint = QLabel("Selecciona el nuevo escenario y presiona Mover.")
        hint.setStyleSheet("font-size: 10px; color: #8e8e93;")
        layout.addWidget(hint)

        self._list = QListWidget()
        for p in places:
            if p.id != current_place_id:
                item = QListWidgetItem(f"  {p.name}")
                item.setData(Qt.ItemDataRole.UserRole, p.id)
                self._list.addItem(item)
        self._list.itemDoubleClicked.connect(self._accept_selection)
        layout.addWidget(self._list, stretch=1)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.button(QDialogButtonBox.StandardButton.Ok).setText("Mover aqui")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        btns.accepted.connect(self._accept_selection)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _accept_selection(self):
        item = self._list.currentItem()
        if item:
            self.selected_place_id = item.data(Qt.ItemDataRole.UserRole)
            self.accept()
        else:
            self.reject()


# ---------------------------------------------------------------------------
#  Card de personaje presente (fila horizontal compacta)
# ---------------------------------------------------------------------------
class PresenceItemWidget(QFrame):
    """
    Card horizontal que representa a un personaje ubicado en el lugar activo.

    Acciones visibles en la card:
      [combo estado]  ->  cambia el estado (Presente / En transito / Salida)
      [->]            ->  abre dialogo para mover al personaje a otro escenario
      [x]             ->  elimina la presencia del registro
    """
    presence_updated = pyqtSignal(str, str)   # char_id, new_type
    presence_removed = pyqtSignal(str)         # char_id
    presence_moved   = pyqtSignal(str, str)    # char_id, new_place_id

    def __init__(self, presence: CharacterPresence, char_name: str,
                 places: list[Place] = None, parent=None):
        super().__init__(parent)
        self.presence  = presence
        self.char_name = char_name
        self.places    = places or []
        self._setup_ui()

    def _setup_ui(self):
        is_dark = ThemeManager.is_dark()
        bg   = "#2c2c2e" if is_dark else "#ffffff"
        bord = "#3a3a3c" if is_dark else "#e0dbd3"
        fg   = "#f2f2f7" if is_dark else "#1c1c1e"

        p_type = self.presence.presence_type
        info   = _TYPE_INFO.get(p_type, ("?", "#8e8e93", "?"))
        color  = info[1]

        self.setStyleSheet(f"""
            PresenceItemWidget {{
                background: {bg};
                border: 1px solid {bord};
                border-left: 3px solid {color};
                border-radius: 8px;
            }}
        """)
        self.setFixedHeight(48)

        row = QHBoxLayout(self)
        row.setContentsMargins(10, 0, 8, 0)
        row.setSpacing(8)

        # Avatar circular con inicial del nombre
        av = QLabel(self.char_name[:1].upper() if self.char_name else "?")
        av.setFixedSize(30, 30)
        av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        av.setStyleSheet(f"""
            background: {color}22;
            color: {color};
            border: 1px solid {color}66;
            border-radius: 15px;
            font-weight: bold;
            font-size: 12px;
        """)
        row.addWidget(av)

        # Nombre del personaje
        name_lbl = QLabel(self.char_name)
        name_lbl.setStyleSheet(f"font-weight: 600; font-size: 12px; color: {fg};")
        row.addWidget(name_lbl, stretch=1)

        # Combo de estado (compacto, con color acorde)
        self.type_combo = QComboBox()
        self.type_combo.setFixedWidth(115)
        self.type_combo.setFixedHeight(26)
        for label, data in _STATUS_OPTIONS:
            self.type_combo.addItem(label, data)
        idx = self.type_combo.findData(p_type)
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)
        self.type_combo.setStyleSheet(f"""
            QComboBox {{
                background: {color}18;
                color: {color};
                border: 1px solid {color}55;
                border-radius: 5px;
                padding: 2px 6px;
                font-size: 10px;
                font-weight: bold;
            }}
            QComboBox::drop-down {{ border: none; width: 14px; }}
        """)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        row.addWidget(self.type_combo)

        # Boton Mover -> abre el dialogo de destino
        if self.places:
            btn_move = QPushButton("->")
            btn_move.setFixedSize(28, 28)
            btn_move.setToolTip("Mover este personaje a otro escenario")
            btn_move.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_move.setStyleSheet("""
                QPushButton {
                    background: #0a84ff22;
                    color: #0a84ff;
                    border: 1px solid #0a84ff55;
                    border-radius: 5px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover { background: #0a84ff44; border-color: #0a84ff; }
            """)
            btn_move.clicked.connect(self._on_move_clicked)
            row.addWidget(btn_move)

        # Boton Eliminar (x)
        btn_del = QPushButton("x")
        btn_del.setFixedSize(24, 24)
        btn_del.setToolTip("Quitar personaje de este lugar")
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #636366;
                border: none;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover { color: #ff453a; }
        """)
        btn_del.clicked.connect(
            lambda: self.presence_removed.emit(self.presence.character_id)
        )
        row.addWidget(btn_del)

    def _on_type_changed(self):
        new_type = self.type_combo.currentData()
        # Actualizar borde lateral con el color del nuevo estado
        info  = _TYPE_INFO.get(new_type, ("?", "#8e8e93", "?"))
        color = info[1]
        is_dark = ThemeManager.is_dark()
        bg   = "#2c2c2e" if is_dark else "#ffffff"
        bord = "#3a3a3c" if is_dark else "#e0dbd3"
        self.setStyleSheet(f"""
            PresenceItemWidget {{
                background: {bg};
                border: 1px solid {bord};
                border-left: 3px solid {color};
                border-radius: 8px;
            }}
        """)
        self.presence_updated.emit(self.presence.character_id, new_type)

    def _on_move_clicked(self):
        is_dark = ThemeManager.is_dark()
        dlg = _MoveCharacterDialog(
            char_name=self.char_name,
            places=self.places,
            current_place_id=self.presence.place_id,
            is_dark=is_dark,
            parent=self,
        )
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.selected_place_id:
            self.presence_moved.emit(self.presence.character_id, dlg.selected_place_id)


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

    def set_project_manager(self, pm):
        self._project_manager = pm

    # -- Construccion de la UI -----------------------------------------------

    def _setup_ui(self):
        is_dark   = ThemeManager.is_dark()
        fg_accent = "#ffd60a"
        fg_sec    = "#8e8e93"

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 6, 0, 4)
        root.setSpacing(10)

        # -- Bloque de contexto: lugar + capitulo activo ---------------------
        ctx_frame = QFrame()
        ctx_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 214, 10, 0.06);
                border: 1px solid rgba(255, 214, 10, 0.25);
                border-radius: 8px;
            }
        """)
        ctx_lay = QVBoxLayout(ctx_frame)
        ctx_lay.setContentsMargins(12, 8, 12, 8)
        ctx_lay.setSpacing(2)

        self.lbl_place_ctx = QLabel("Sin lugar seleccionado")
        self.lbl_place_ctx.setStyleSheet(
            f"font-weight: bold; font-size: 12px; color: {fg_accent};"
        )
        ctx_lay.addWidget(self.lbl_place_ctx)

        self.lbl_chapter_ctx = QLabel("Todos los capitulos")
        self.lbl_chapter_ctx.setStyleSheet(f"font-size: 10px; color: {fg_sec};")
        ctx_lay.addWidget(self.lbl_chapter_ctx)

        root.addWidget(ctx_frame)

        # -- Hint: seleccionar capitulo primero (visible solo en vista global) -
        self._chapter_hint = QFrame()
        self._chapter_hint.setStyleSheet("""
            QFrame {
                background: rgba(10, 132, 255, 0.07);
                border: 1px solid rgba(10, 132, 255, 0.25);
                border-radius: 8px;
            }
        """)
        hint_lay = QVBoxLayout(self._chapter_hint)
        hint_lay.setContentsMargins(12, 10, 12, 10)
        hint_lay.setSpacing(4)
        hint_icon = QLabel("Selecciona un capitulo para editar")
        hint_icon.setStyleSheet("font-weight: bold; font-size: 11px; color: #0a84ff;")
        hint_lay.addWidget(hint_icon)
        hint_desc = QLabel(
            "La vista Todos los capitulos es solo de lectura.\n"
            "Elige un capitulo especifico en la toolbar para\n"
            "colocar o mover personajes en este escenario."
        )
        hint_desc.setStyleSheet("font-size: 10px; color: #636366; line-height: 1.4;")
        hint_desc.setWordWrap(True)
        hint_lay.addWidget(hint_desc)
        root.addWidget(self._chapter_hint)
        self._chapter_hint.setVisible(False)  # oculto por defecto

        # -- Formulario de asignacion (solo visible con capitulo activo) ------
        self._form_frame = QFrame()
        self._form_frame.setStyleSheet("QFrame { background: transparent; border: none; }")
        form_lay = QVBoxLayout(self._form_frame)
        form_lay.setContentsMargins(0, 0, 0, 0)
        form_lay.setSpacing(6)

        # Paso 1: Seleccionar personaje
        form_lay.addWidget(self._step_label("1", "Selecciona el personaje"))
        self.combo_add_char = QComboBox()
        self.combo_add_char.setFixedHeight(30)
        self.combo_add_char.setToolTip("Personaje que quieres ubicar en este escenario")
        form_lay.addWidget(self.combo_add_char)

        # Paso 2: Estado inicial
        form_lay.addWidget(self._step_label("2", "Estado inicial"))
        self.combo_status = QComboBox()
        self.combo_status.setFixedHeight(30)
        for label, data in _STATUS_OPTIONS:
            self.combo_status.addItem(label, data)
        form_lay.addWidget(self.combo_status)

        # Boton confirmar
        self.btn_add = QPushButton("  Colocar personaje aqui")
        self.btn_add.setFixedHeight(34)
        self.btn_add.setToolTip(
            "Registrar la ubicacion del personaje en el capitulo seleccionado"
        )
        self.btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add.setStyleSheet("""
            QPushButton {
                background: #ffd60a;
                color: #000;
                font-weight: bold;
                font-size: 12px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover   { background: #ffe033; }
            QPushButton:pressed { background: #e6c009; }
            QPushButton:disabled {
                background: #3a3a3c;
                color: #636366;
            }
        """)
        self.btn_add.clicked.connect(self._on_add_character_manual)
        form_lay.addWidget(self.btn_add)

        root.addWidget(self._form_frame)

        # -- Separador y titulo de lista ------------------------------------
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #3a3a3c; margin: 2px 0;")
        root.addWidget(sep)

        self.lbl_list_title = QLabel("PERSONAJES AQUI AHORA")
        self.lbl_list_title.setStyleSheet(
            "font-size: 9px; font-weight: bold; color: #636366; letter-spacing: 0.8px;"
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
        """Etiqueta de paso numerado para el formulario."""
        lbl = QLabel(f"  {number}   {text}")
        lbl.setStyleSheet(
            "font-size: 10px; font-weight: bold; color: #8e8e93; letter-spacing: 0.3px;"
        )
        return lbl

    # -- Carga de datos -------------------------------------------------------

    def load_place(self, place: Optional[Place], chapter_id: Optional[str] = None):
        """Carga los personajes presentes en el lugar para el capitulo dado."""
        self._current_place      = place
        self._current_chapter_id = chapter_id

        self._clear_items()
        self._update_context_labels(place, chapter_id)
        self._populate_char_combo()

        # Mostrar u ocultar el formulario segun si hay capitulo seleccionado
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

        # NOTA: PresenceMerger se usa SOLO para deduplicar presencias manuales.
        # Cuando se reactive el motor NLP automatico, tambien consolidara
        # sugerencias automaticas con prioridad is_manual=True > automatica.
        if chapter_id is None:
            # Vista global: ultima ubicacion conocida de cada personaje
            from tools.nlp.presence_merger import PresenceMerger
            active = PresenceMerger.get_latest_character_locations(all_pres)
            place_presences = [p for p in active if p.place_id == place.id]
        else:
            # Vista de capitulo: deduplicar y filtrar por lugar
            from tools.nlp.presence_merger import PresenceMerger
            cap_pres = [
                p for p in all_pres
                if p.chapter_id == chapter_id
                and p.presence_type in ("present", "transit")
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

    def _update_context_labels(self, place: Optional[Place], chapter_id: Optional[str]):
        """Actualiza los labels del header de contexto."""
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
                            if raw:
                                cap_title = raw
                            elif c.in_world_order and c.in_world_order > 0:
                                cap_title = f"Capitulo {c.in_world_order}"
                            else:
                                cap_title = "Capitulo actual"
                            break

            self.lbl_chapter_ctx.setText(
                f"Asignando en: {cap_title}" if cap_title else "Todos los capitulos"
            )
        else:
            self.lbl_chapter_ctx.setText("Vista global - Todos los capitulos")

    def _populate_char_combo(self):
        """Puebla el combo de personajes disponibles."""
        self.combo_add_char.blockSignals(True)
        self.combo_add_char.clear()
        self.combo_add_char.addItem("-- Elige un personaje --", None)

        if self._project_manager and self._project_manager.metadata:
            chars = getattr(self._project_manager.metadata, "characters", [])
            for c in chars:
                self.combo_add_char.addItem(f"  {c.name}", c.id)

        self.combo_add_char.blockSignals(False)

    def _clear_items(self):
        while self.items_layout.count() > 0:
            item = self.items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _show_empty(self, message: str):
        lbl = QLabel(message)
        lbl.setStyleSheet(
            "color: #636366; font-style: italic; font-size: 11px; margin: 6px 2px;"
        )
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.items_layout.addWidget(lbl)

    # -- Acciones del usuario ------------------------------------------------

    def _on_add_character_manual(self):
        """Coloca manualmente un personaje en el lugar y capitulo actuales."""
        if not self._current_place or not self._project_manager:
            return

        char_id = self.combo_add_char.currentData()
        if not char_id:
            return

        status = self.combo_status.currentData() or "present"
        meta   = self._project_manager.metadata
        if not meta:
            return

        # Si estamos en vista global, asignar al primer capitulo disponible
        chapter_id = self._current_chapter_id or self._first_chapter_id(meta)

        if not hasattr(meta, "presences") or meta.presences is None:
            meta.presences = []

        # Limpiar presencias previas del mismo personaje en este capitulo
        # (evita duplicados si el autor reubica al personaje en el mismo cap)
        meta.presences = [
            p for p in meta.presences
            if not (p.character_id == char_id and p.chapter_id == chapter_id)
        ]

        new_p = CharacterPresence(
            character_id=char_id,
            place_id=self._current_place.id,
            chapter_id=chapter_id,
            presence_type=status,
            confidence=1.0,
            is_manual=True,
            matched_text="Ubicado manualmente por el autor",
        )
        meta.presences.append(new_p)

        self.load_place(self._current_place, chapter_id=self._current_chapter_id)
        self.presence_changed.emit()

    def _on_presence_moved(self, char_id: str, new_place_id: str):
        """Traslada al personaje del lugar actual al nuevo destino."""
        if not self._project_manager or not self._current_place:
            return
        meta = self._project_manager.metadata
        if not meta:
            return

        chapter_id = self._current_chapter_id or self._first_chapter_id(meta)

        if not hasattr(meta, "presences") or meta.presences is None:
            meta.presences = []

        # Marcar la presencia actual como 'departed' para conservar el historial
        for p in meta.presences:
            if (p.character_id == char_id
                    and p.chapter_id == chapter_id
                    and p.place_id == self._current_place.id):
                p.presence_type = "departed"
                p.matched_text  = f"Partio hacia {new_place_id}"

        # Crear presencia activa en el lugar destino
        new_p = CharacterPresence(
            character_id=char_id,
            place_id=new_place_id,
            chapter_id=chapter_id,
            presence_type="present",
            confidence=1.0,
            is_manual=True,
            matched_text="Trasladado manualmente por el autor",
        )
        meta.presences.append(new_p)

        self.load_place(self._current_place, chapter_id=self._current_chapter_id)
        self.presence_changed.emit()

    def _on_presence_type_updated(self, char_id: str, new_type: str):
        """Actualiza el tipo de presencia de un personaje en el lugar actual."""
        if not self._project_manager or not self._current_place:
            return
        meta       = self._project_manager.metadata
        chapter_id = self._current_chapter_id
        for p in getattr(meta, "presences", []):
            if (p.place_id == self._current_place.id
                    and p.character_id == char_id
                    and (chapter_id is None or p.chapter_id == chapter_id)):
                p.presence_type = new_type
        self.presence_changed.emit()

    def _on_presence_removed(self, char_id: str):
        """Elimina la presencia del personaje en el lugar y capitulo actual."""
        if not self._project_manager or not self._current_place:
            return
        meta       = self._project_manager.metadata
        chapter_id = self._current_chapter_id
        meta.presences = [
            p for p in getattr(meta, "presences", [])
            if not (
                p.place_id == self._current_place.id
                and p.character_id == char_id
                and (chapter_id is None or p.chapter_id == chapter_id)
            )
        ]
        self.load_place(self._current_place, chapter_id=chapter_id)
        self.presence_changed.emit()

    @staticmethod
    def _first_chapter_id(meta) -> str:
        """Retorna el ID del primer capitulo disponible como fallback."""
        for obra in getattr(meta, "obras", []):
            for libro in getattr(obra, "libros", []):
                if libro.capitulos:
                    return libro.capitulos[0].id
        return "cap_manual"


# ---------------------------------------------------------------------------
#  Panel de Historial de visitas (pestana "Historial")
# ---------------------------------------------------------------------------
class PlaceHistoryPanel(QWidget):
    """
    Historial cronologico de visitas al lugar seleccionado.
    Muestra presencias agrupadas por capitulo con headers colapsables.
    Los ultimos 3 capitulos se expanden automaticamente.
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
        root.setContentsMargins(0, 6, 0, 4)
        root.setSpacing(4)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_content = QWidget()
        self.items_layout   = QVBoxLayout(self.scroll_content)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(4)
        self.items_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.scroll_content)
        root.addWidget(self.scroll, stretch=1)

    def _clear_layout(self):
        while self.items_layout.count() > 0:
            item = self.items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def load_place(self, place: Optional[Place]):
        """Carga el historial completo agrupado por capitulo."""
        self._current_place = place
        self._clear_layout()

        if not place:
            lbl = QLabel("Selecciona un lugar en el mapa.")
            lbl.setStyleSheet("color: #8e8e93; font-style: italic; font-size: 11px;")
            self.items_layout.addWidget(lbl)
            return

        if not self._project_manager or not self._project_manager.metadata:
            return

        meta     = self._project_manager.metadata
        char_map: Dict[str, str] = {
            c.id: c.name for c in getattr(meta, "characters", [])
        }

        # Mapa capitulo_id -> (titulo, obra, orden_cronologico)
        cap_map: Dict[str, tuple] = {}
        for obra in meta.obras:
            for libro in obra.libros:
                for cap in libro.capitulos:
                    cap_map[cap.id] = (cap.title, obra.title, cap.in_world_order)

        all_pres: List[CharacterPresence] = getattr(meta, "presences", [])
        place_events = [p for p in all_pres if p.place_id == place.id]

        if not place_events:
            lbl = QLabel(
                "Ningun personaje tiene registro de haber visitado este lugar aun."
            )
            lbl.setStyleSheet(
                "color: #8e8e93; font-style: italic; font-size: 11px; margin-top: 6px;"
            )
            lbl.setWordWrap(True)
            self.items_layout.addWidget(lbl)
            return

        # Ordenar y agrupar por capitulo
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

        is_dark          = ThemeManager.is_dark()
        AUTO_EXPAND_LAST = 3
        expanded_ids     = set(group_order[-AUTO_EXPAND_LAST:])

        for cap_id in group_order:
            presences_in_cap = groups[cap_id]
            cap_title, obra_title, order = cap_map.get(
                cap_id, ("Capitulo desconocido", "", 0)
            )
            is_expanded = cap_id in expanded_ids
            is_latest   = cap_id == group_order[-1]

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

            # Filas compactas bajo el header
            rows_widget = QWidget()
            rows_lay    = QVBoxLayout(rows_widget)
            rows_lay.setContentsMargins(12, 2, 4, 4)
            rows_lay.setSpacing(3)

            for p in presences_in_cap:
                c_name = char_map.get(p.character_id, "Personaje desconocido")
                info   = _TYPE_INFO.get(p.presence_type, (p.presence_type, "#8e8e93", "?"))
                type_label, type_color = info[0], info[1]

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

                fg_text = "#f2f2f7" if is_dark else "#1c1c1e"
                name_lbl = QLabel(c_name)
                name_lbl.setStyleSheet(
                    f"font-size: 11px; font-weight: 600; color: {fg_text};"
                )
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
                    verb_lbl.setStyleSheet(
                        "font-size: 9px; color: #636366; font-style: italic;"
                    )
                    row_l.addWidget(verb_lbl)

                rows_lay.addWidget(row)

            rows_widget.setVisible(is_expanded)
            header.toggled.connect(rows_widget.setVisible)
            self.items_layout.addWidget(rows_widget)


# ---------------------------------------------------------------------------
#  Header colapsable de capitulo (usado por PlaceHistoryPanel)
# ---------------------------------------------------------------------------
class _ChapterGroupHeader(QFrame):
    """Header clickeable que colapsa/expande el grupo de presencias de un capitulo."""
    toggled = pyqtSignal(bool)

    def __init__(self, cap_title: str, obra_title: str, order: int,
                 count: int, expanded: bool, is_latest: bool, is_dark: bool,
                 parent=None):
        super().__init__(parent)
        self._expanded = expanded
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        accent = "#ffd60a" if is_latest else ("#5e5ce6" if is_dark else "#4f46e5")
        bg     = "#1e1e20" if is_dark else "#ede9e0"
        fg     = "#f2f2f7" if is_dark else "#1c1c1e"
        sub_fg = "#8e8e93" if is_dark else "#6e6e73"

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

        self._arrow = QLabel("v" if expanded else ">")
        self._arrow.setStyleSheet(
            f"color: {accent}; font-size: 12px; font-weight: bold;"
        )
        self._arrow.setFixedWidth(14)
        layout.addWidget(self._arrow)

        order_str = f"#{order}  " if order > 0 else ""
        title_lbl = QLabel(f"{order_str}{cap_title}")
        title_lbl.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {fg};")
        layout.addWidget(title_lbl, stretch=1)

        if obra_title:
            obra_lbl = QLabel(obra_title)
            obra_lbl.setStyleSheet(f"font-size: 9px; color: {sub_fg};")
            layout.addWidget(obra_lbl)

        n = count
        badge = QLabel(f"{n} {'personaje' if n == 1 else 'personajes'}")
        badge.setStyleSheet(f"""
            background: {accent}22; color: {accent};
            border: 1px solid {accent}55; border-radius: 3px;
            font-size: 9px; font-weight: bold; padding: 1px 5px;
        """)
        layout.addWidget(badge)

    def mousePressEvent(self, event):
        self._expanded = not self._expanded
        self._arrow.setText("v" if self._expanded else ">")
        self.toggled.emit(self._expanded)
        super().mousePressEvent(event)
