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
from ui.place_dock import PlaceDock
from ui.relation_graph import RelationGraphWidget
from ui.main_menu_builder import MainMenuBuilderMixin
from ui.tree_controller import TreeControllerMixin
from ui.notes_controller import NotesControllerMixin
from ui.security_controller import SecurityControllerMixin
from ui.usb_controller import UsbControllerMixin
from ui.character_controller import CharacterControllerMixin
from ui.place_controller import PlaceControllerMixin
from ui.exporter_controller import ExporterControllerMixin
from ui.app_lifecycle_controller import AppLifecycleMixin
from ui.spell_panel import SpellPanel

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
    PlaceControllerMixin,
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

        # ── Panel izquierdo: Árbol + Inspector (splitter vertical) ──────────────
        from PyQt6.QtWidgets import QStackedWidget

        left_splitter = QSplitter(Qt.Orientation.Vertical)
        left_splitter.setChildrenCollapsible(False)

        # Sección superior izquierda: Árbol de la novela
        outline_frame = QFrame()
        ol = QVBoxLayout(outline_frame)
        ol.setContentsMargins(6, 6, 6, 6)
        ol.setSpacing(4)
        lbl = QLabel("UNIVERSO")
        lbl.setStyleSheet("font-weight: bold; color: #9b59b6; margin-bottom: 4px;")
        ol.addWidget(lbl)
        self.outline_tree = OutlineTree()
        self.outline_tree.item_selected.connect(self.on_item_selected)
        self.outline_tree.item_double_clicked.connect(self._on_tree_item_double_clicked)
        self.outline_tree.node_add_requested.connect(self._on_add_node)
        self.outline_tree.node_delete_requested.connect(self._on_delete_node)
        self.outline_tree.node_renamed.connect(self._on_rename_node)
        self.outline_tree.node_moved_requested.connect(self._on_node_moved)
        ol.addWidget(self.outline_tree)
        outline_frame.setMinimumHeight(120)
        left_splitter.addWidget(outline_frame)

        # Sección inferior izquierda: Inspector de Notas
        inspector_frame = QFrame()
        il = QVBoxLayout(inspector_frame)
        il.setContentsMargins(6, 8, 6, 6)
        il.setSpacing(5)

        il.addWidget(self._make_label("INSPECTOR", bold=True, color="#9b59b6"))
        il.addWidget(self._make_label("Notas del Capítulo:", size=11, color="#8e8e93"))

        self.notes_list = QListWidget()
        self.notes_list.setMinimumHeight(60)
        self.notes_list.setMaximumHeight(130)
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
        self.inspector_notes.setMinimumHeight(70)
        il.addWidget(self.inspector_notes, 1)

        inspector_frame.setMinimumHeight(80)
        left_splitter.addWidget(inspector_frame)

        # Proporciones iniciales del splitter izquierdo (árbol:inspector = 65:35)
        left_splitter.setSizes([420, 220])

        # ── Panel central: Editor ────────────────────────────────────────────────
        editor_frame = QFrame()
        el = QVBoxLayout(editor_frame)
        el.setContentsMargins(0, 0, 0, 0)
        self.editor = AuraEditor()
        el.addWidget(self.editor)

        # ── Panel derecho: Dock de Personajes / Lugares ──────────────────────────
        right_frame = QFrame()
        rl = QVBoxLayout(right_frame)
        rl.setContentsMargins(6, 6, 6, 6)
        rl.setSpacing(6)

        self.char_dock = CharacterDock()
        self.char_dock.character_added.connect(self._on_character_added)
        self.char_dock.character_deleted.connect(self._on_character_deleted)
        self.char_dock.character_selected.connect(self._on_character_selected)
        self.char_dock.chapter_requested.connect(self._on_chapter_requested_from_dock)

        self.place_dock = PlaceDock(project_manager=self.project_manager)
        self.place_dock.place_added.connect(self._on_place_added)
        self.place_dock.place_updated.connect(self._on_place_updated)
        self.place_dock.place_deleted.connect(self._on_place_deleted)
        self.place_dock.place_selected.connect(self._on_place_selected)
        self.place_dock.chapter_requested.connect(self._on_chapter_requested_from_dock)

        # Segmented Switcher [ 👤 Personajes ] | [ 🏰 Lugares ] | [ ✓ Corrector ]
        switcher_frame = QFrame()
        switcher_layout = QHBoxLayout(switcher_frame)
        switcher_layout.setContentsMargins(0, 0, 0, 4)
        switcher_layout.setSpacing(4)

        self._btn_tab_chars = QPushButton("Personajes")
        self._btn_tab_chars.setCheckable(True)
        self._btn_tab_chars.setChecked(True)
        self._btn_tab_chars.clicked.connect(lambda: self._switch_inspector_tab("characters"))

        self._btn_tab_places = QPushButton("Lugares")
        self._btn_tab_places.setCheckable(True)
        self._btn_tab_places.setChecked(False)
        self._btn_tab_places.clicked.connect(lambda: self._switch_inspector_tab("places"))

        self._btn_tab_spell = QPushButton("Corrector")
        self._btn_tab_spell.setCheckable(True)
        self._btn_tab_spell.setChecked(False)
        self._btn_tab_spell.clicked.connect(lambda: self._switch_inspector_tab("spell"))

        switcher_layout.addWidget(self._btn_tab_chars, 1)
        switcher_layout.addWidget(self._btn_tab_places, 1)
        switcher_layout.addWidget(self._btn_tab_spell, 1)
        rl.addWidget(switcher_frame)

        # ── Panel de Corrección Ortográfica ──────────────────────────────────
        self.spell_panel = SpellPanel(checker=self.editor.spell_checker)
        self.spell_panel.navigate_to_error.connect(self.editor.navigate_to_spell_error)
        self.spell_panel.replace_word.connect(self.editor.replace_spell_word)
        self.spell_panel.word_added_to_dict.connect(self.project_manager.add_personal_word)
        self.spell_panel.word_ignored.connect(lambda w: self.editor._trigger_spell_check())
        self.spell_panel.recheck_requested.connect(self.editor._trigger_spell_check)
        self.editor.spell_checker.errors_ready.connect(self.spell_panel.update_errors)

        # QStackedWidget con Personajes (0), Lugares (1), Corrector (2)
        self._dock_stack = QStackedWidget()
        self._dock_stack.addWidget(self.char_dock)   # index 0
        self._dock_stack.addWidget(self.place_dock)  # index 1
        self._dock_stack.addWidget(self.spell_panel) # index 2
        rl.addWidget(self._dock_stack, 1)

        self._update_segmented_switcher_style()

        self._outline_frame = outline_frame
        self._inspector_frame = inspector_frame
        self._left_splitter = left_splitter

        self.main_splitter.addWidget(left_splitter)
        self.main_splitter.addWidget(editor_frame)
        self.main_splitter.addWidget(right_frame)
        self.main_splitter.setSizes([240, 790, 250])
        root.addWidget(self.main_splitter)

        # Barra de estado
        status = QStatusBar()
        self.setStatusBar(status)
        self._autosave_indicator = QLabel("Sin cambios")
        self._autosave_indicator.setStyleSheet("color:#636366;font-size:11px;padding:0 8px;")
        self._usb_indicator = QLabel("USB: No configurada")
        self._usb_indicator.setStyleSheet("color:#636366;font-size:11px;padding:0 8px;")

        # Indicador de Zoom interactivo en la barra de estado
        self._zoom_indicator = QPushButton(f"{self.editor.get_zoom_percentage()}%")
        self._zoom_indicator.setToolTip("Ajustar Zoom, Tipografía y Estilo de Papel (Ctrl+,)")
        self._zoom_indicator.setStyleSheet("border: none; color:#8e8e93; font-size:11px; padding: 2px 6px;")
        self._zoom_indicator.setCursor(Qt.CursorShape.PointingHandCursor)
        self._zoom_indicator.clicked.connect(self.open_editor_appearance_dialog)

        # Indicador de Lugar activo en la barra de estado
        self._place_status_indicator = QLabel("")
        self._place_status_indicator.setStyleSheet("color:#8e8e93;font-size:11px;padding:0 8px;")

        # Indicador de Corrector Ortográfico interactivo en la barra de estado
        self._spell_status_indicator = QPushButton("✓ Ortografía OK")
        self._spell_status_indicator.setToolTip("Corrector ortográfico activo (0 errores). Clic para abrir el panel.")
        self._spell_status_indicator.setStyleSheet("border: none; color: #30d158; font-size: 11px; padding: 2px 8px;")
        self._spell_status_indicator.setCursor(Qt.CursorShape.PointingHandCursor)
        self._spell_status_indicator.clicked.connect(self._on_spell_indicator_clicked)

        # Timer de animación para escaneo ortográfico en segundo plano
        self._spell_anim_timer = QTimer(self)
        self._spell_anim_timer.setInterval(180)
        self._spell_anim_timer.timeout.connect(self._on_spell_anim_tick)
        self._spell_anim_frame = 0

        self.editor.spell_checker.checking_started.connect(self._on_spell_checking_started)
        self.editor.spell_checker.errors_ready.connect(self._on_spell_checking_finished)
        self.editor.spell_checker.check_error.connect(self._on_spell_checking_error)

        status.addPermanentWidget(self._place_status_indicator)
        status.addPermanentWidget(self._spell_status_indicator)
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

    def _switch_inspector_tab(self, tab: str):
        """Alterna el panel inspector entre [Personajes], [Lugares] y [Corrector]."""
        self._btn_tab_chars.setChecked(tab == "characters")
        self._btn_tab_places.setChecked(tab == "places")
        self._btn_tab_spell.setChecked(tab == "spell")

        if tab == "places":
            self._dock_stack.setCurrentWidget(self.place_dock)
            self._refresh_place_dock()
        elif tab == "spell":
            self._dock_stack.setCurrentWidget(self.spell_panel)
            # El panel ya está enlazado con signals/slots al editor
        else:
            self._dock_stack.setCurrentWidget(self.char_dock)
            self._refresh_char_dock()
        self._update_segmented_switcher_style()

    # ── Métodos para animación e indicador del corrector en status bar ──────

    SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def _on_spell_checking_started(self):
        """Se activa cuando el hilo en segundo plano comienza a revisar el texto."""
        self._spell_anim_frame = 0
        self._spell_anim_timer.start()
        self._spell_status_indicator.setText("⏳ Revisando...")
        self._spell_status_indicator.setStyleSheet("border: none; color: #ffd60a; font-size: 11px; padding: 2px 8px;")
        self._spell_status_indicator.setToolTip("Revisando ortografía en segundo plano...")

    def _on_spell_anim_tick(self):
        """Avanza la animación del spinner mientras revisa."""
        self._spell_anim_frame = (self._spell_anim_frame + 1) % len(self.SPINNER_FRAMES)
        symbol = self.SPINNER_FRAMES[self._spell_anim_frame]
        self._spell_status_indicator.setText(f"{symbol} Revisando...")

    def _on_spell_checking_finished(self, errors: list):
        """Se activa al terminar la revisión en segundo plano."""
        self._spell_anim_timer.stop()
        if not hasattr(self, "editor") or not hasattr(self.editor, "spell_checker") or not self.editor.spell_checker.enabled:
            self._spell_status_indicator.setText("Ortografía desc.")
            self._spell_status_indicator.setStyleSheet("border: none; color: #8e8e93; font-size: 11px; padding: 2px 8px;")
            self._spell_status_indicator.setToolTip("Corrector ortográfico desactivado")
            return

        if not errors:
            self._spell_status_indicator.setText("✓ Ortografía OK")
            self._spell_status_indicator.setStyleSheet("border: none; color: #30d158; font-size: 11px; padding: 2px 8px;")
            self._spell_status_indicator.setToolTip("Corrector ortográfico activo (0 errores). Clic para abrir el panel.")
        else:
            n = len(errors)
            s_plural = "s" if n != 1 else ""
            self._spell_status_indicator.setText(f"⚠ {n} falta{s_plural}")
            self._spell_status_indicator.setStyleSheet("border: none; color: #ff453a; font-weight: bold; font-size: 11px; padding: 2px 8px;")
            self._spell_status_indicator.setToolTip(f"{n} error{'es' if n != 1 else ''} ortográfico{'s' if n != 1 else ''}. Clic para ver panel de corrección.")

    def _on_spell_checking_error(self, err_msg: str):
        """Maneja errores no críticos en el worker."""
        self._spell_anim_timer.stop()
        self._spell_status_indicator.setText("⚠ Ortografía")
        self._spell_status_indicator.setStyleSheet("border: none; color: #ff9f0a; font-size: 11px; padding: 2px 8px;")

    def _on_spell_indicator_clicked(self):
        """Al hacer clic en el indicador, conmuta hacia el panel de ortografía."""
        if hasattr(self, "_dock_stack") and hasattr(self, "spell_panel"):
            if self._dock_stack.currentWidget() == self.spell_panel:
                self._switch_inspector_tab("characters")
            else:
                self._switch_inspector_tab("spell")

    def _update_segmented_switcher_style(self):
        """Aplica estilo moderno tipo iOS / macOS Segmented Control a los botones de personajes/lugares."""
        from core.theme_manager import ThemeManager
        is_dark = ThemeManager.is_dark()
        active_bg = "#3a3a3c" if is_dark else "#ffffff"
        inactive_bg = "transparent"
        border = "#48484a" if is_dark else "#d1cdc7"
        fg_active = "#ffd60a" if is_dark else "#d97706"
        fg_inactive = "#8e8e93" if is_dark else "#6e6e73"

        base_style = f"""
            QPushButton {{
                border: 1px solid {border};
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: 600;
            }}
        """
        chars_checked = self._btn_tab_chars.isChecked()
        self._btn_tab_chars.setStyleSheet(base_style + f"""
            QPushButton {{
                background-color: {active_bg if chars_checked else inactive_bg};
                color: {fg_active if chars_checked else fg_inactive};
                border: {f'1px solid {fg_active}' if chars_checked else f'1px solid {border}'};
            }}
        """)
        places_checked = self._btn_tab_places.isChecked()
        self._btn_tab_places.setStyleSheet(base_style + f"""
            QPushButton {{
                background-color: {active_bg if places_checked else inactive_bg};
                color: {fg_active if places_checked else fg_inactive};
                border: {f'1px solid {fg_active}' if places_checked else f'1px solid {border}'};
            }}
        """)
        spell_checked = self._btn_tab_spell.isChecked()
        self._btn_tab_spell.setStyleSheet(base_style + f"""
            QPushButton {{
                background-color: {active_bg if spell_checked else inactive_bg};
                color: {fg_active if spell_checked else fg_inactive};
                border: {f'1px solid {fg_active}' if spell_checked else f'1px solid {border}'};
            }}
        """)

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
        elif item_type in ("universe", "obra", "libro"):
            container_obj = self._current_container
            self._load_container_synopsis(item_type, container_obj)

    def _on_tree_item_double_clicked(self, item_id: str, item_type: str):
        """Responde al doble clic en un nodo del árbol. Los nodos 'media' abren
        su previsualización solo cuando el usuario hace doble clic explícito."""
        if item_type == "media":
            self._show_media_preview(item_id)

    def closeEvent(self, a0):  # noqa: N802  # Qt uses 'a0' in stubs
        event = a0

        # 1. Detener timers y tareas en segundo plano
        if hasattr(self, "_autosave_timer"):
            self._autosave_timer.stop()
        if hasattr(self, "_stats_timer"):
            self._stats_timer.stop()
        if hasattr(self, "_spell_anim_timer"):
            self._spell_anim_timer.stop()
        if hasattr(self, "editor"):
            try:
                self.editor.cleanup()
            except Exception:
                pass

        # 2. Si hay un worker de guardado activo en segundo plano, esperar a que termine
        if getattr(self, "_active_save_worker", None) and self._active_save_worker.isRunning():
            self._active_save_worker.wait(5000)

        # 3. Preguntar al usuario si desea guardar cambios pendientes
        if self.project_manager.metadata and self._dirty:
            reply = QMessageBox.question(
                self, "Guardar antes de salir",
                "Tienes cambios sin guardar. ¿Deseas guardar antes de salir?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Save:
                saved = self.save_project(sync=True)
                if not saved:
                    event.ignore()
                    return
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return

        # 4. Esperar nuevamente por seguridad antes de destruir la sesión temporal
        if getattr(self, "_active_save_worker", None) and self._active_save_worker.isRunning():
            self._active_save_worker.wait(5000)

        # 5. Cerrar y limpiar sesión temporal del proyecto
        if self.project_manager.metadata:
            self.project_manager.close_project()

        # 6. Limpiar workers del pool global de hilos
        from PyQt6.QtCore import QThreadPool
        from PyQt6.QtWidgets import QApplication
        try:
            QThreadPool.globalInstance().clear()
            QThreadPool.globalInstance().waitForDone(500)
        except Exception:
            pass

        event.accept()
        # Obs. #14: QApplication.quit() es redundante después de event.accept() en Qt6
        # — Qt termina el loop automáticamente cuando se cierra la última ventana principal.