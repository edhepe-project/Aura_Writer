"""
Aura Writer — Ventana Principal
Ciclo de vida, construccion de UI y coordinacion entre mixins especializados.

Herencia (MRO):
  AuraMainWindow
    <- MainMenuBuilderMixin   (menus, toolbar, acciones de formato)
    <- TreeControllerMixin    (arbol narrativo: crear/mover/eliminar nodos)
    <- NotesControllerMixin   (inspector de notas, finder helpers, preview media)
    <- SecurityControllerMixin(bloqueo, 2FA, contrasena, papelera, busqueda)
    <- UsbControllerMixin     (indicador USB, config, sync, estado)
    <- CharacterControllerMixin(personajes, dock, deteccion de menciones)
    <- ExporterControllerMixin (dialogo de exportacion, recoleccion de datos)
    <- QMainWindow
"""

import os
import sys
import logging
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QFrame,
    QLabel, QStatusBar, QMessageBox, QTextEdit, QPushButton, QDialog,
    QFileDialog, QListWidget,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QTextCharFormat, QImage
import qtawesome as qta

from ui.outline_tree import OutlineTree
from ui.editor import AuraEditor
from ui.character_dock import CharacterDock
from ui.universe_map import UniverseMapWidget
from ui.relation_graph import RelationGraphWidget
from ui.main_menu_builder import MainMenuBuilderMixin
from ui.tree_controller import TreeControllerMixin
from ui.notes_controller import NotesControllerMixin
from ui.security_controller import SecurityControllerMixin
from ui.usb_controller import UsbControllerMixin
from ui.character_controller import CharacterControllerMixin
from ui.exporter_controller import ExporterControllerMixin

from core.project_manager import ProjectManager
from core.models import Chapter, MediaNode, AuthorNote, Obra, Book, Character
from core.theme_manager import ThemeManager

log = logging.getLogger(__name__)


class AuraMainWindow(
    MainMenuBuilderMixin,
    TreeControllerMixin,
    NotesControllerMixin,
    SecurityControllerMixin,
    UsbControllerMixin,
    CharacterControllerMixin,
    ExporterControllerMixin,
    QMainWindow,
):
    """Ventana principal de Aura Writer (coordinador de mixins)."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aura Writer - Nuevo Universo")
        self.resize(1280, 850)

        self.project_manager = ProjectManager()
        self._current_chapter: Chapter | None = None
        self._current_note: AuthorNote | None = None
        self._current_container = None
        self._dirty = False

        self.setup_ui()
        self.setup_menus()
        self.setup_toolbar()

        # Temporizador de estadisticas (debounced)
        self._stats_timer = QTimer(self)
        self._stats_timer.setSingleShot(True)
        self._stats_timer.timeout.connect(self._do_update_stats)

        self.editor.textChanged.connect(self._on_editor_text_changed)
        self.editor.currentCharFormatChanged.connect(self._update_format_actions)

        # Auto-guardado cada 2 minutos
        self._autosave_timer = QTimer(self)
        self._autosave_timer.timeout.connect(self._auto_save)
        self._autosave_timer.start(120_000)

        # Monitor USB cada 15 segundos
        self._usb_monitor_timer = QTimer(self)
        self._usb_monitor_timer.timeout.connect(self._update_usb_indicator)
        self._usb_monitor_timer.start(15_000)

    # ------------------------------------------------------------------
    # Construccion de la interfaz
    # ------------------------------------------------------------------

    def setup_ui(self):
        """Construye todos los paneles y la barra de estado."""
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Panel izquierdo: Arbol de contenido
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
        status.addPermanentWidget(self._autosave_indicator)
        status.addPermanentWidget(self._usb_indicator)

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

    # ------------------------------------------------------------------
    # Ventanas emergentes (Mapa y Grafo)
    # ------------------------------------------------------------------

    def open_universe_map(self):
        """Abre el Mapa Mental en una ventana emergente."""
        if not self.project_manager.metadata:
            QMessageBox.warning(self, "Mapa Mental", "No hay un proyecto abierto.")
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("Mapa Mental del Universo")
        dlg.resize(1100, 760)
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(0, 0, 0, 0)
        map_widget = UniverseMapWidget(dlg)
        map_widget.chapter_requested.connect(lambda cid: self._on_map_chapter_requested(cid, dlg))
        layout.addWidget(map_widget)
        map_widget.build_from_metadata(self.project_manager.metadata)
        dlg.exec()

    def open_relation_graph(self):
        """Abre el Grafo de Relaciones en una ventana emergente."""
        if not self.project_manager.metadata:
            QMessageBox.warning(self, "Relaciones", "No hay un proyecto abierto.")
            return
        self._sync_relations_to_metadata()
        dlg = QDialog(self)
        dlg.setWindowTitle("Relaciones entre Personajes")
        dlg.resize(1100, 750)
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(0, 0, 0, 0)
        graph_widget = RelationGraphWidget(dlg)
        graph_widget.character_focused.connect(self._on_graph_character_focused)
        layout.addWidget(graph_widget)
        graph_widget.build_from_metadata(self.project_manager.metadata)
        dlg.exec()

    def _on_map_chapter_requested(self, chapter_id: str, dlg: QDialog):
        """Cierra el mapa y abre el capitulo al hacer doble clic en un nodo."""
        self._flush_content_to_metadata()
        chapter = self.project_manager.find_chapter(chapter_id)
        if chapter:
            dlg.accept()
            self._load_chapter(chapter)

    # ------------------------------------------------------------------
    # Tema
    # ------------------------------------------------------------------

    def _toggle_theme(self):
        from PyQt6.QtWidgets import QApplication
        new_theme = ThemeManager.toggle(QApplication.instance())
        self._update_theme_action_label()
        if hasattr(self, "_refresh_toolbar_icons"):
            self._refresh_toolbar_icons()
        label = "Claro" if new_theme == "light" else "Oscuro"
        self.statusBar().showMessage(f"Tema cambiado a {label}", 3000)

    def _update_theme_action_label(self):
        if ThemeManager.is_dark():
            self._theme_act.setText("Cambiar a Tema Claro")
            if hasattr(self, "_theme_btn_action"):
                self._theme_btn_action.setText("Claro")
                self._theme_btn_action.setIcon(qta.icon("fa5s.sun", color="#ffd60a"))
        else:
            self._theme_act.setText("Cambiar a Tema Oscuro")
            if hasattr(self, "_theme_btn_action"):
                self._theme_btn_action.setText("Oscuro")
                self._theme_btn_action.setIcon(qta.icon("fa5s.moon", color="#32ade6"))

    def toggle_zen_mode(self):
        """Alterna el modo concentración (Zen Mode): oculta los paneles laterales para escribir sin distracciones."""
        is_zen = getattr(self, "_is_zen_mode", False)
        self._is_zen_mode = not is_zen

        if self._is_zen_mode:
            # Guardar anchos del splitter antes de colapsar
            if hasattr(self, "main_splitter"):
                self._saved_splitter_sizes = self.main_splitter.sizes()

            # Ocultar paneles laterales
            if hasattr(self, "_outline_frame"):
                self._outline_frame.hide()
            if hasattr(self, "_inspector_frame"):
                self._inspector_frame.hide()

            if hasattr(self, "_zen_act"):
                self._zen_act.setChecked(True)
            self.statusBar().showMessage("🧘 Modo Zen activado (F11 para restaurar paneles)", 4000)
        else:
            # Restaurar paneles laterales
            if hasattr(self, "_outline_frame"):
                self._outline_frame.show()
            if hasattr(self, "_inspector_frame"):
                self._inspector_frame.show()

            # Restaurar anchos del splitter
            if hasattr(self, "main_splitter") and hasattr(self, "_saved_splitter_sizes"):
                self.main_splitter.setSizes(self._saved_splitter_sizes)
            elif hasattr(self, "main_splitter"):
                self.main_splitter.setSizes([220, 800, 260])

            if hasattr(self, "_zen_act"):
                self._zen_act.setChecked(False)
            self.statusBar().showMessage("Modo Zen desactivado.", 3000)

    # ------------------------------------------------------------------
    # Estadisticas del editor
    # ------------------------------------------------------------------

    def _on_editor_text_changed(self):
        self._dirty = True
        self._stats_timer.start(300)

    def _do_update_stats(self):
        doc = self.editor.document()
        chars = max(0, doc.characterCount() - 1)
        if chars == 0:
            self.statusBar().showMessage("Palabras: 0 | Caracteres: 0 | Lectura: ~0 min")
            return
        words = len(self.editor.toPlainText().split())
        mins = max(1, words // 200)

        # Contador de palabras de la sesión
        if not hasattr(self, "_session_start_words"):
            self._session_start_words = words
        session_diff = words - self._session_start_words
        session_sign = f"+{session_diff}" if session_diff > 0 else f"{session_diff}"

        self.statusBar().showMessage(
            f"Capítulo: {words} palabras ({session_sign} en sesión) | Caracteres: {chars} | Lectura: ~{mins} min"
        )

    def update_stats(self):
        self._do_update_stats()

    # ------------------------------------------------------------------
    # Guardado
    # ------------------------------------------------------------------

    def save_project(self):
        if not self.project_manager.metadata:
            self.statusBar().showMessage("No hay proyecto abierto.", 3000)
            return
        self.char_dock._save_current_card()
        self._sync_relations_to_metadata()
        if self._current_chapter:
            self._detect_character_mentions(self._current_chapter)
        self._flush_content_to_metadata()
        try:
            self.project_manager.save_project()
            self._dirty = False
            now = datetime.now().strftime("%H:%M:%S")
            self._autosave_indicator.setText(f"Guardado: {now}")
            self._autosave_indicator.setStyleSheet("color:#30d158;font-size:11px;padding:0 8px;")
            usb_err = self.project_manager.last_usb_error
            if self.project_manager.usb_sync.is_configured():
                msg = f"Guardado local | USB: {usb_err}" if usb_err else "Guardado (local + USB)"
                self.statusBar().showMessage(msg, 5000 if usb_err else 3000)
            else:
                self.statusBar().showMessage("Proyecto guardado", 3000)
            self._update_usb_indicator()

        except Exception as e:
            log.exception("Error al guardar")
            QMessageBox.critical(self, "Error al Guardar", str(e))

    def _flush_content_to_metadata(self):
        """Persiste el contenido del editor y la nota activa al metadata."""
        if self._current_chapter and self._current_chapter.content_file:
            self.project_manager.write_chapter_content(
                self._current_chapter.content_file, self.editor.toHtml()
            )
        if self._current_note:
            self._current_note.content = self.inspector_notes.toPlainText()

    def _mark_dirty(self):
        self._dirty = True

    def _auto_save(self):
        """Auto-guardado silencioso cada 2 minutos."""
        if not self._dirty or not self.project_manager.metadata:
            return
        if self.project_manager.is_locked:
            return
        try:
            self.save_project()
            log.info("Auto-guardado ejecutado")
        except Exception:
            log.exception("Error durante auto-guardado")

    # ------------------------------------------------------------------
    # Insertar imagen desde el editor
    # ------------------------------------------------------------------

    def insert_media(self):
        if not self._current_chapter:
            QMessageBox.warning(self, "Insertar Imagen", "Selecciona un capitulo primero.")
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar imagen", "",
            "Imagenes (*.png *.jpg *.jpeg *.gif *.webp)"
        )
        if not path:
            return
        ext = os.path.splitext(path)[1]
        with open(path, "rb") as f:
            data = f.read()
        asset_name = self.project_manager.save_media_asset(data, ext)
        media = MediaNode(title=os.path.basename(path), image_asset=asset_name)
        self._current_chapter.medias.append(media)
        img = QImage()
        img.loadFromData(data)
        if img.isNull():
            QMessageBox.critical(self, "Error", "El archivo de imagen esta corrupto.")
            return
        self.editor._insert_image_object(img, asset_name)
        self._refresh_tree()
        self.statusBar().showMessage(f"Imagen anadida: {media.title}", 3000)

    # ------------------------------------------------------------------
    # Seleccion de nodos en el arbol
    # ------------------------------------------------------------------

    def on_item_selected(self, item_id: str, item_type: str):
        """Responde a la seleccion de un nodo en el arbol narrativo."""
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

        if item_type == "chapter":
            chapter = self.project_manager.find_chapter(item_id)
            if chapter:
                self._load_chapter(chapter)
        elif item_type == "media":
            self._show_media_preview(item_id)

    # ------------------------------------------------------------------
    # Cierre de la aplicacion
    # ------------------------------------------------------------------

    def closeEvent(self, event):
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