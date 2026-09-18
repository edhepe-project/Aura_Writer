"""
Aura Writer — Ventana Principal
Ciclo de vida, construcción de UI y coordinación entre mixins especializados.

Herencia (MRO):
  AuraMainWindow
    <- MainMenuBuilderMixin      (menús, toolbar, acciones de formato)
    <- TreeControllerMixin       (árbol narrativo: crear/mover/eliminar nodos)
    <- NotesControllerMixin      (inspector de notas, finder helpers, preview media)
    <- SecurityControllerMixin   (bloqueo, 2FA, contraseña, papelera, búsqueda)
    <- UsbControllerMixin        (indicador USB, config, sync, estado)
    <- CharacterControllerMixin  (personajes, dock, detección de menciones)
    <- ExporterControllerMixin   (diálogo de exportación, recolección de datos)
    <- AppLifecycleMixin         (grafo, mapa, estadísticas, guardado, updater, zoom, zen)
    <- QMainWindow
"""

import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QFrame,
    QLabel, QStatusBar, QMessageBox, QTextEdit, QPushButton, QDialog,
    QListWidget,
)
from PyQt6.QtCore import Qt, QTimer

from ui.outline_tree import OutlineTree
from ui.editor import AuraEditor
from ui.character_dock import CharacterDock
from ui.relation_graph import RelationGraphWidget
from ui.main_menu_builder import MainMenuBuilderMixin
from ui.tree_controller import TreeControllerMixin
from ui.notes_controller import NotesControllerMixin
from ui.security_controller import SecurityControllerMixin
from ui.usb_controller import UsbControllerMixin
from ui.character_controller import CharacterControllerMixin
from ui.exporter_controller import ExporterControllerMixin
from ui.app_lifecycle_controller import AppLifecycleMixin

from core.project_manager import ProjectManager
from core.models import Chapter, AuthorNote

log = logging.getLogger(__name__)


class AuraMainWindow(
    MainMenuBuilderMixin,
    TreeControllerMixin,
    NotesControllerMixin,
    SecurityControllerMixin,
    UsbControllerMixin,
    CharacterControllerMixin,
    ExporterControllerMixin,
    AppLifecycleMixin,
    QMainWindow,
):
    """Ventana principal de Aura Writer (coordinador de mixins y construcción de interfaz)."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aura Writer - Nuevo Universo")
        self.resize(1280, 850)

        self.project_manager = ProjectManager()
        self._current_chapter: "Chapter | None" = None
        self._current_note: AuthorNote | None = None
        self._current_container = None
        self._dirty = False

        self.setup_ui()
        self.setup_menus()
        self.setup_toolbar()

        # Temporizador de estadísticas (debounced)
        self._stats_timer = QTimer(self)
        self._stats_timer.setSingleShot(True)
        self._stats_timer.timeout.connect(self._do_update_stats)

        self.editor.textChanged.connect(self._on_editor_text_changed)
        self.editor.currentCharFormatChanged.connect(self._update_format_actions)
        self.editor.cursorPositionChanged.connect(self._update_format_actions)

        # Auto-guardado cada 2 minutos
        self._autosave_timer = QTimer(self)
        self._autosave_timer.timeout.connect(self._auto_save)
        self._autosave_timer.start(120_000)

        # Reutilización de diálogo para apertura instantánea de grafo
        self._graph_dialog: QDialog | None = None
        self._graph_widget: RelationGraphWidget | None = None

    def setup_ui(self):
        """Construye todos los paneles y la barra de estado."""
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Panel izquierdo: Árbol de contenido
        outline_frame = QFrame()
        ol = QVBoxLayout(outline_frame)
        ol.setContentsMargins(6, 6, 6, 6)
        lbl = QLabel("UNIVERSO")
        lbl.setStyleSheet("font-weight: bold; color: #9b59b6; margin-bottom: 4px;")
        ol.addWidget(lbl)
        self.outline_tree = OutlineTree()
        self.outline_tree.item_selected.connect(self.on_item_selected)
        self.outline_tree.node_add_requested.connect(self._on_add_node)
        self.outline_tree.node_delete_requested.connect(self._on_delete_node)
        self.outline_tree.node_renamed.connect(self._on_rename_node)
        self.outline_tree.node_moved_requested.connect(self._on_node_moved)
        ol.addWidget(self.outline_tree)

        # Panel central: Editor
        editor_frame = QFrame()
        el = QVBoxLayout(editor_frame)
        el.setContentsMargins(0, 0, 0, 0)
        self.editor = AuraEditor()
        el.addWidget(self.editor)

        # Panel derecho: Inspector + Dock de personajes
        inspector_frame = QFrame()
        il = QVBoxLayout(inspector_frame)
        il.setContentsMargins(6, 6, 6, 6)
        il.setSpacing(6)

        il.addWidget(self._make_label("INSPECTOR", bold=True, color="#9b59b6"))
        il.addWidget(self._make_label("Notas del Capitulo:", size=11, color="#8e8e93"))

        self.notes_list = QListWidget()
        self.notes_list.setMaximumHeight(140)
        self.notes_list.currentItemChanged.connect(self._on_note_list_selection_changed)
        self.notes_list.itemDoubleClicked.connect(self._on_note_double_clicked)
        il.addWidget(self.notes_list)

        btn_row = QHBoxLayout()
        btn_add = QPushButton("+ Nota")
        btn_add.setStyleSheet("font-size:11px;padding:3px 8px;")
        btn_add.clicked.connect(self._on_inspector_add_note)
        btn_del = QPushButton("Eliminar")
        btn_del.setStyleSheet("font-size:11px;padding:3px 6px;")
        btn_del.clicked.connect(self._on_inspector_delete_note)
        btn_row.addWidget(btn_add)
        btn_row.addStretch()
        btn_row.addWidget(btn_del)
        il.addLayout(btn_row)

        self.inspector_notes = QTextEdit()
        self.inspector_notes.setReadOnly(True)
        self.inspector_notes.setPlaceholderText(
            "No hay notas.\nUsa '+ Nota' para crear una\no doble click para editar."
        )
        self.inspector_notes.setMaximumHeight(110)
        il.addWidget(self.inspector_notes, 1)

        self.char_dock = CharacterDock()
        self.char_dock.character_added.connect(self._on_character_added)
        self.char_dock.character_deleted.connect(self._on_character_deleted)
        self.char_dock.character_selected.connect(self._on_character_selected)
        self.char_dock.chapter_requested.connect(self._on_chapter_requested_from_dock)
        il.addWidget(self.char_dock, 1)

        self._outline_frame = outline_frame
        self._inspector_frame = inspector_frame

        self.main_splitter.addWidget(outline_frame)
        self.main_splitter.addWidget(editor_frame)
        self.main_splitter.addWidget(inspector_frame)
        self.main_splitter.setSizes([220, 800, 260])
        root.addWidget(self.main_splitter)

        # Barra de estado
        status = QStatusBar()
        self.setStatusBar(status)
        self._autosave_indicator = QLabel("Sin cambios")
        self._autosave_indicator.setStyleSheet("color:#636366;font-size:11px;padding:0 8px;")
        self._usb_indicator = QLabel("USB: No configurada")
        self._usb_indicator.setStyleSheet("color:#636366;font-size:11px;padding:0 8px;")

        # Indicador de Zoom interactivo en la barra de estado
        self._zoom_indicator = QPushButton(f"🔍 {self.editor.get_zoom_percentage()}%")
        self._zoom_indicator.setToolTip("Ajustar Zoom, Tipografía y Estilo de Papel (Ctrl+,)")
        self._zoom_indicator.setStyleSheet("border: none; color:#8e8e93; font-size:11px; padding: 2px 6px;")
        self._zoom_indicator.setCursor(Qt.CursorShape.PointingHandCursor)
        self._zoom_indicator.clicked.connect(self.open_editor_appearance_dialog)

        status.addPermanentWidget(self._autosave_indicator)
        status.addPermanentWidget(self._usb_indicator)
        status.addPermanentWidget(self._zoom_indicator)

    @staticmethod
    def _make_label(text: str, bold=False, size=0, color="") -> QLabel:
        """Crea un QLabel con estilo inline."""
        lbl = QLabel(text)
        styles = []
        if bold:
            styles.append("font-weight:bold;")
        if size:
            styles.append(f"font-size:{size}px;")
        if color:
            styles.append(f"color:{color};")
        styles.append("margin-bottom:2px;")
        lbl.setStyleSheet(" ".join(styles))
        return lbl

    def changeEvent(self, a0):  # noqa: N802  # Qt uses 'a0' in stubs
        """Devuelve el foco al editor al recuperar el foco desde Windows (Alt+Tab)."""
        event = a0
        super().changeEvent(event)
        if event.type() == event.Type.ActivationChange and self.isActiveWindow():
            if self._current_chapter and hasattr(self, "editor"):
                self.editor.setFocus()

    def on_item_selected(self, item_id: str, item_type: str):
        """Responde a la selección de un nodo en el árbol narrativo."""
        self._flush_content_to_metadata()
        meta = self.project_manager.metadata
        if not meta:
            return
        self._current_container = {
            "universe": lambda: meta,
            "obra":     lambda: self._find_obra(item_id),
            "libro":    lambda: self._find_libro(item_id),
            "chapter":  lambda: self.project_manager.find_chapter(item_id),
        }.get(item_type, lambda: None)()

        self._refresh_notes_list()
        self._update_dock_context(item_id, item_type)

        # Recordar el último nodo/capítulo seleccionado
        meta.last_selected_node_id = item_id

        if item_type == "chapter":
            chapter = self.project_manager.find_chapter(item_id)
            if chapter:
                self._load_chapter(chapter)
        elif item_type == "media":
            self._show_media_preview(item_id)

    def closeEvent(self, a0):  # noqa: N802  # Qt uses 'a0' in stubs
        event = a0
        if self.project_manager.metadata and self._dirty:
            reply = QMessageBox.question(
                self, "Guardar antes de salir",
                "Tienes cambios sin guardar. Deseas guardar antes de salir?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Save:
                self.save_project()
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
        if self.project_manager.metadata:
            self.project_manager.close_project()
        event.accept()