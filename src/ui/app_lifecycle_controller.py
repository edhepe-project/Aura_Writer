"""
app_lifecycle_controller.py — Mixin para gestión de ciclo de vida, guardado, estadísticas y ventanas emergentes principales.
"""

from __future__ import annotations
import os
import logging
from datetime import datetime
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QImage
import qtawesome as qta

from core.models import MediaNode
from core.theme_manager import ThemeManager
from ui.universe_map import UniverseMapWidget
from ui.relation_graph import RelationGraphWidget

if TYPE_CHECKING:
    from ui.main_window import AuraMainWindow

log = logging.getLogger(__name__)


class _SaveWorker(QThread):
    """Hilo de trabajo para el guardado/cifrado asincrónico del proyecto."""
    finished = pyqtSignal(str)   # mensaje de éxito / error
    saved_ok = pyqtSignal()      # emitida solo si éxito
    save_failed = pyqtSignal(str)  # mensaje de error si falló

    def __init__(self, project_manager):
        super().__init__()
        self._pm = project_manager

    def run(self):
        try:
            self._pm.save_project()
            self.saved_ok.emit()
        except Exception as e:
            self.save_failed.emit(str(e))


class AppLifecycleMixin:
    """
    Mixin para AuraMainWindow que maneja:
    - Grafo de relaciones y mapa mental (ventanas modales)
    - Guardado de proyecto y auto-guardado
    - Estadísticas en tiempo real del editor
    - Inserción de imágenes y comparador de capítulos
    - Comprobación de actualizaciones y About
    - Control de zoom y apariencia
    - Cambio de tema y Modo Zen
    """

    def _warmup_background_modules(self: "AuraMainWindow"):
        """
        Precarga silenciosa en segundo plano de módulos pesados (Atlas Literario,
        Cronograma Narrativo, etc.) para que cuando el usuario haga clic en ellos
        por primera vez abran de forma 100% instantánea.
        """
        try:
            import ui.place_graph
            import ui.story_graph
            import qtawesome as qta
            qta.icon("fa5s.search-plus")
            qta.icon("fa5s.map-marked-alt")
            qta.icon("fa5s.compress-arrows-alt")
            qta.icon("fa5s.th")
            log.debug("Precarga silenciosa de módulos finalizada con éxito.")
        except Exception as e:
            log.debug("Warmup silencioso en segundo plano omitido: %s", e)

    def open_relation_graph(self: "AuraMainWindow"):
        """Abre el Grafo de Relaciones al instante sin parpadeos."""
        if not self.project_manager.metadata:
            QMessageBox.warning(self, "Relaciones", "No hay un proyecto abierto.")
            return
        self._sync_relations_to_metadata()

        is_dark = ThemeManager.is_dark()
        bg_col = '#1c1c1e' if is_dark else '#f5f0ea'

        if self._graph_dialog is None or self._graph_widget is None:
            dlg = QDialog(self)
            dlg.setWindowTitle("Relaciones entre Personajes")
            dlg.setWindowFlags(
                Qt.WindowType.Window |
                Qt.WindowType.WindowMinMaxButtonsHint |
                Qt.WindowType.WindowCloseButtonHint
            )
            from PyQt6.QtWidgets import QApplication
            screen = QApplication.primaryScreen().availableGeometry()
            w = min(1360, int(screen.width() * 0.92))
            h = min(860, int(screen.height() * 0.90))
            dlg.resize(w, h)
            dlg.setStyleSheet(f"QDialog {{ background-color: {bg_col}; }}")
            layout = QVBoxLayout(dlg)
            layout.setContentsMargins(0, 0, 0, 0)
            gw = RelationGraphWidget(dlg)
            gw.character_focused.connect(self._on_graph_character_focused)
            gw.open_character_sheet.connect(self._on_graph_open_character_sheet)
            layout.addWidget(gw)
            self._graph_dialog = dlg
            self._graph_widget = gw

        self._graph_dialog.setStyleSheet(f"QDialog {{ background-color: {bg_col}; }}")
        self._graph_widget.update_theme(is_dark)
        self._graph_widget.build_from_metadata(self.project_manager.metadata)
        self._graph_dialog.exec()

    def open_universe_map(self: "AuraMainWindow"):
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

    def _on_map_chapter_requested(self: "AuraMainWindow", chapter_id: str, dlg: QDialog):
        """Cierra el mapa y abre el capítulo al hacer doble clic en un nodo."""
        self._flush_content_to_metadata()
        chapter = self.project_manager.find_chapter(chapter_id)
        if chapter:
            dlg.accept()
            self._load_chapter(chapter)

    # ------------------------------------------------------------------
    # Tema y Modo Zen
    # ------------------------------------------------------------------

    def _switch_to_theme(self: "AuraMainWindow", theme_name: str):
        from PyQt6.QtWidgets import QApplication
        ThemeManager.apply(QApplication.instance(), theme_name)
        self._update_theme_action_label()
        # Los widgets reactivos se actualizan automáticamente vía ThemeManager.signals.theme_changed
        # Solo actualizamos lo que no está conectado a la señal aún
        if hasattr(self, "_refresh_toolbar_icons"):
            self._refresh_toolbar_icons()
        if hasattr(self, "_update_segmented_switcher_style"):
            self._update_segmented_switcher_style()
        if self._graph_dialog is not None:
            bg_colors = {'dark': '#1c1c1e', 'light': '#f5f0ea', 'sepia': '#f4ecd8'}
            bg_col = bg_colors.get(theme_name, '#1c1c1e')
            self._graph_dialog.setStyleSheet(f"QDialog {{ background-color: {bg_col}; }}")
        labels = {
            "dark": "Oscuro (Dark Slate)",
            "light": "Claro (Lienzo Papel)",
            "sepia": "Sepia (Pergamino)"
        }
        self.statusBar().showMessage(f"Tema activo: {labels.get(theme_name, theme_name)}", 3000)

    def _toggle_theme(self: "AuraMainWindow"):
        from PyQt6.QtWidgets import QApplication
        new_theme = ThemeManager.toggle(QApplication.instance())
        self._update_theme_action_label()
        # Los widgets reactivos se actualizan automáticamente vía ThemeManager.signals.theme_changed
        if hasattr(self, "_refresh_toolbar_icons"):
            self._refresh_toolbar_icons()
        if hasattr(self, "_update_segmented_switcher_style"):
            self._update_segmented_switcher_style()
        if self._graph_dialog is not None:
            bg_colors = {'dark': '#1c1c1e', 'light': '#f5f0ea', 'sepia': '#f4ecd8'}
            bg_col = bg_colors.get(new_theme, '#1c1c1e')
            self._graph_dialog.setStyleSheet(f"QDialog {{ background-color: {bg_col}; }}")
        labels = {
            "dark": "Oscuro (Dark Slate)",
            "light": "Claro (Lienzo Papel)",
            "sepia": "Sepia (Pergamino)"
        }
        self.statusBar().showMessage(f"Tema cambiado a {labels.get(new_theme, new_theme)}", 3000)

    def _update_theme_action_label(self: "AuraMainWindow"):
        cur = ThemeManager.current()
        
        # Actualizar checkmarks en el submenú de temas
        if hasattr(self, "_act_theme_dark"): self._act_theme_dark.setChecked(cur == "dark")
        if hasattr(self, "_act_theme_light"): self._act_theme_light.setChecked(cur == "light")
        if hasattr(self, "_act_theme_sepia"): self._act_theme_sepia.setChecked(cur == "sepia")

        if cur == "dark":
            self._theme_act.setText("Alternar a Tema Claro")
        elif cur == "light":
            self._theme_act.setText("Alternar a Tema Sepia")
        else:
            self._theme_act.setText("Alternar a Tema Oscuro")

    def toggle_zen_mode(self: "AuraMainWindow"):
        """Alterna el modo concentración (Zen Mode): oculta los paneles laterales para escribir sin distracciones."""
        is_zen = getattr(self, "_is_zen_mode", False)
        self._is_zen_mode = not is_zen

        if self._is_zen_mode:
            if hasattr(self, "main_splitter"):
                self._saved_splitter_sizes = self.main_splitter.sizes()

            # Ocultar panel izquierdo (splitter vertical con árbol + inspector)
            if hasattr(self, "_left_splitter"):
                self._left_splitter.hide()
            elif hasattr(self, "_outline_frame"):
                self._outline_frame.hide()
            if hasattr(self, "_inspector_frame"):
                self._inspector_frame.hide()

            # Ocultar panel derecho (personajes / lugares)
            if hasattr(self, "main_splitter") and self.main_splitter.count() >= 3:
                self.main_splitter.widget(2).hide()

            if hasattr(self, "_zen_act"):
                self._zen_act.setChecked(True)
            self.statusBar().showMessage("🧘 Modo Zen activado (F11 para restaurar paneles)", 4000)
        else:
            # Restaurar panel izquierdo
            if hasattr(self, "_left_splitter"):
                self._left_splitter.show()
            elif hasattr(self, "_outline_frame"):
                self._outline_frame.show()
            if hasattr(self, "_inspector_frame"):
                self._inspector_frame.show()

            # Restaurar panel derecho
            if hasattr(self, "main_splitter") and self.main_splitter.count() >= 3:
                self.main_splitter.widget(2).show()

            if hasattr(self, "main_splitter") and hasattr(self, "_saved_splitter_sizes"):
                self.main_splitter.setSizes(self._saved_splitter_sizes)
            elif hasattr(self, "main_splitter"):
                self.main_splitter.setSizes([240, 790, 250])

            if hasattr(self, "_zen_act"):
                self._zen_act.setChecked(False)
            self.statusBar().showMessage("Modo Zen desactivado.", 3000)

    # ------------------------------------------------------------------
    # Estadísticas del editor
    # ------------------------------------------------------------------

    def _on_editor_text_changed(self: "AuraMainWindow"):
        self._dirty = True
        self._stats_timer.start(300)

    def _do_update_stats(self: "AuraMainWindow"):
        doc = self.editor.document()
        chars = max(0, doc.characterCount() - 1)
        if chars == 0:
            self.statusBar().showMessage("Palabras: 0 | Caracteres: 0 | Lectura: ~0 min")
            return
        words = len(self.editor.toPlainText().split())
        mins = max(1, words // 200)

        if not hasattr(self, "_session_start_words"):
            self._session_start_words = words
        session_diff = words - self._session_start_words
        session_sign = f"+{session_diff}" if session_diff > 0 else f"{session_diff}"

        self.statusBar().showMessage(
            f"Capítulo: {words} palabras ({session_sign} en sesión) | Caracteres: {chars} | Lectura: ~{mins} min"
        )

    def update_stats(self: "AuraMainWindow"):
        self._do_update_stats()

    # ------------------------------------------------------------------
    # Guardado y persistencia
    # ------------------------------------------------------------------

    def save_project(self: "AuraMainWindow"):
        if not self.project_manager.metadata:
            self.statusBar().showMessage("No hay proyecto abierto.", 3000)
            return
        # Evitar guardados paralelos
        if getattr(self, "_save_worker_active", False):
            log.debug("Guardado ya en curso, se omite.")
            return
        
        self.char_dock._save_current_card()
        self._sync_relations_to_metadata()
        if self._current_chapter:
            self._detect_character_mentions(self._current_chapter)
            self._detect_place_mentions(self._current_chapter)
        self._flush_content_to_metadata()
        if self._current_chapter:
            try:
                self.project_manager.create_chapter_revision(
                    self._current_chapter.id,
                    description="Guardado automático"
                )
            except Exception as e:
                log.warning("No se pudo registrar la revisión del capítulo: %s", e)

        # Indicador visual de guardado en progreso
        self._autosave_indicator.setText("⏳ Guardando...")
        self._autosave_indicator.setStyleSheet("color:#ffd60a;font-size:11px;padding:0 8px;")
        self._save_worker_active = True

        worker = _SaveWorker(self.project_manager)

        def _on_saved():
            self._save_worker_active = False
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

        def _on_failed(err: str):
            self._save_worker_active = False
            self._autosave_indicator.setText("⚠ Error al guardar")
            self._autosave_indicator.setStyleSheet("color:#ff453a;font-size:11px;padding:0 8px;")
            log.error("Error al guardar: %s", err)
            QMessageBox.critical(self, "Error al Guardar", err)

        worker.saved_ok.connect(_on_saved)
        worker.save_failed.connect(_on_failed)
        # Mantener referencia al worker para evitar que sea recolectado por GC
        self._active_save_worker = worker
        worker.start()

    def _flush_content_to_metadata(self: "AuraMainWindow"):
        """Persiste el contenido del editor y la nota activa al metadata."""
        if self._current_chapter and self._current_chapter.content_file:
            html = (self.editor.get_content_html()
                    if hasattr(self.editor, "get_content_html")
                    else self.editor.toHtml())
            self.project_manager.write_chapter_content(
                self._current_chapter.content_file, html
            )
        if self._current_note:
            self._current_note.content = self.inspector_notes.toPlainText()

    def _mark_dirty(self: "AuraMainWindow"):
        self._dirty = True

    def _auto_save(self: "AuraMainWindow"):
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

    def insert_media(self: "AuraMainWindow"):
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
    # Mesa de Cotejo / Comparador de Capítulos
    # ------------------------------------------------------------------

    def open_chapter_comparator(self: "AuraMainWindow"):
        """Abre la Mesa de Cotejo para comparar y afinar dos capítulos lado a lado."""
        if not self.project_manager.metadata:
            QMessageBox.warning(self, "Mesa de Cotejo", "Abre un proyecto primero.")
            return

        self._flush_content_to_metadata()

        from ui.comparator import ChapterComparatorDialog
        dlg = ChapterComparatorDialog(
            project_manager=self.project_manager,
            initial_chapter=self._current_chapter,
            parent=self
        )
        dlg.exec()

        self._refresh_tree()

        if self._current_chapter and self._current_chapter.content_file:
            html = self.project_manager.read_chapter_content(self._current_chapter.content_file)
            self.editor.blockSignals(True)
            self.editor.setHtml(html)
            if hasattr(self.editor, "_apply_paragraph_spacing"):
                self.editor._apply_paragraph_spacing()
            self.editor.blockSignals(False)
            self.update_stats()

    # ------------------------------------------------------------------
    # Historial de Versiones y Diff
    # ------------------------------------------------------------------

    def open_chapter_history(self: "AuraMainWindow"):
        """Abre el diálogo de historial de versiones y diff del capítulo actual."""
        if not self.project_manager.metadata:
            QMessageBox.warning(self, "Historial de Versiones", "Abre un proyecto primero.")
            return

        if not self._current_chapter:
            QMessageBox.warning(self, "Historial de Versiones", "Selecciona un capítulo primero.")
            return

        self._flush_content_to_metadata()

        from ui.history_diff_dialog import ChapterHistoryDiffDialog
        dlg = ChapterHistoryDiffDialog(
            project_manager=self.project_manager,
            chapter=self._current_chapter,
            parent=self
        )

        def _on_restored(cid: str):
            if self._current_chapter and self._current_chapter.id == cid:
                html = self.project_manager.read_chapter_content(self._current_chapter.content_file)
                self.editor.blockSignals(True)
                self.editor.setHtml(html)
                if hasattr(self.editor, "_apply_paragraph_spacing"):
                    self.editor._apply_paragraph_spacing()
                self.editor.blockSignals(False)
                self.update_stats()
                self._mark_dirty()

        dlg.revision_restored.connect(_on_restored)
        dlg.exec()

    # ------------------------------------------------------------------
    # Ayuda y Actualizaciones
    # ------------------------------------------------------------------

    def check_for_updates_manual(self: "AuraMainWindow"):
        from core.updater import UpdateCheckWorker
        from ui.update_dialog import UpdateDialog

        self.statusBar().showMessage("Buscando actualizaciones...", 3000)
        self._manual_update_worker = UpdateCheckWorker(self)

        def _on_finish(has_update: bool, release_info: dict, err: str):
            if has_update:
                dlg = UpdateDialog(release_info, self)
                dlg.exec()
            elif err:
                QMessageBox.warning(
                    self, "Buscar Actualizaciones",
                    f"No se pudo comprobar si hay actualizaciones:\n{err}"
                )
            else:
                from version import __version__
                QMessageBox.information(
                    self, "Buscar Actualizaciones",
                    f"¡Estás al día!\nAura Writer v{__version__} es la versión más reciente."
                )

        self._manual_update_worker.check_finished.connect(_on_finish)
        self._manual_update_worker.start()

    def _check_updates_silently(self: "AuraMainWindow"):
        from core.updater import UpdateCheckWorker
        from ui.update_dialog import UpdateDialog

        self._silent_update_worker = UpdateCheckWorker(self)

        def _on_finish(has_update: bool, release_info: dict, err: str):
            if has_update and not err:
                dlg = UpdateDialog(release_info, self)
                dlg.exec()

        self._silent_update_worker.check_finished.connect(_on_finish)
        self._silent_update_worker.start()

    def open_project_website(self: "AuraMainWindow"):
        import webbrowser
        from version import APP_URL
        webbrowser.open(APP_URL)

    def show_about_dialog(self: "AuraMainWindow"):
        from version import __version__, APP_NAME, APP_AUTHOR, APP_URL
        text = (
            f"<h2>{APP_NAME} v{__version__}</h2>"
            f"<p><b>Autor:</b> {APP_AUTHOR}</p>"
            f"<p><b>Propósito:</b> Suite de escritura creativa, diseño narrativo y seguridad de grado autor.</p>"
            f"<p><b>Sitio Web:</b> <a href='{APP_URL}'>{APP_URL}</a></p>"
            f"<hr>"
            f"<p><small>Cifrado AES-256-GCM • Llave Maestra de Aplicación • TOTP 2FA • Motor de Resonancia 528 Hz.</small></p>"
        )
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(f"Acerca de {APP_NAME}")
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(text)
        try:
            msg_box.setIconPixmap(qta.icon("fa5s.feather-alt", color="#d4a017").pixmap(48, 48))
        except Exception:
            pass
        msg_box.exec()

    # ------------------------------------------------------------------
    # Accesibilidad, Zoom y Apariencia del Editor
    # ------------------------------------------------------------------

    def open_editor_appearance_dialog(self: "AuraMainWindow"):
        from ui.editor_appearance_dialog import EditorAppearanceDialog
        dlg = EditorAppearanceDialog(self.editor, self)
        dlg.appearance_changed.connect(self._update_zoom_indicator)
        dlg.exec()
        self._update_zoom_indicator()

    def _on_zoom_in(self: "AuraMainWindow"):
        self.editor.zoom_in()
        self._update_zoom_indicator()

    def _on_zoom_out(self: "AuraMainWindow"):
        self.editor.zoom_out()
        self._update_zoom_indicator()

    def _on_zoom_reset(self: "AuraMainWindow"):
        self.editor.zoom_reset()
        self._update_zoom_indicator()

    def _update_zoom_indicator(self: "AuraMainWindow"):
        if hasattr(self, "_zoom_indicator"):
            pct = self.editor.get_zoom_percentage()
            self._zoom_indicator.setText(f"{pct}%")
