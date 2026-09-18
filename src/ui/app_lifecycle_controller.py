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
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage
import qtawesome as qta

from core.models import MediaNode
from core.theme_manager import ThemeManager
from ui.universe_map import UniverseMapWidget
from ui.relation_graph import RelationGraphWidget

if TYPE_CHECKING:
    from ui.main_window import AuraMainWindow

log = logging.getLogger(__name__)


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

    def _toggle_theme(self: "AuraMainWindow"):
        from PyQt6.QtWidgets import QApplication
        new_theme = ThemeManager.toggle(QApplication.instance())
        self._update_theme_action_label()
        if hasattr(self, "_refresh_toolbar_icons"):
            self._refresh_toolbar_icons()
        if hasattr(self, "char_dock") and self.char_dock is not None:
            self.char_dock.update_theme()
        if hasattr(self, "place_dock") and self.place_dock is not None:
            self.place_dock.update_theme()
        if hasattr(self, "_update_segmented_switcher_style"):
            self._update_segmented_switcher_style()
        if self._graph_widget is not None:
            self._graph_widget.update_theme(ThemeManager.is_dark())
        if self._graph_dialog is not None:
            bg_col = '#1c1c1e' if ThemeManager.is_dark() else '#f5f0ea'
            self._graph_dialog.setStyleSheet(f"QDialog {{ background-color: {bg_col}; }}")
        label = "Claro" if new_theme == "light" else "Oscuro"
        self.statusBar().showMessage(f"Tema cambiado a {label}", 3000)

    def _update_theme_action_label(self: "AuraMainWindow"):
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

    def toggle_zen_mode(self: "AuraMainWindow"):
        """Alterna el modo concentración (Zen Mode): oculta los paneles laterales para escribir sin distracciones."""
        is_zen = getattr(self, "_is_zen_mode", False)
        self._is_zen_mode = not is_zen

        if self._is_zen_mode:
            if hasattr(self, "main_splitter"):
                self._saved_splitter_sizes = self.main_splitter.sizes()

            if hasattr(self, "_outline_frame"):
                self._outline_frame.hide()
            if hasattr(self, "_inspector_frame"):
                self._inspector_frame.hide()

            if hasattr(self, "_zen_act"):
                self._zen_act.setChecked(True)
            self.statusBar().showMessage("🧘 Modo Zen activado (F11 para restaurar paneles)", 4000)
        else:
            if hasattr(self, "_outline_frame"):
                self._outline_frame.show()
            if hasattr(self, "_inspector_frame"):
                self._inspector_frame.show()

            if hasattr(self, "main_splitter") and hasattr(self, "_saved_splitter_sizes"):
                self.main_splitter.setSizes(self._saved_splitter_sizes)
            elif hasattr(self, "main_splitter"):
                self.main_splitter.setSizes([220, 800, 260])

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
        self.char_dock._save_current_card()
        self._sync_relations_to_metadata()
        if self._current_chapter:
            self._detect_character_mentions(self._current_chapter)
        self._flush_content_to_metadata()
        if self._current_chapter:
            try:
                self.project_manager.create_chapter_revision(
                    self._current_chapter.id,
                    description="Guardado automático"
                )
            except Exception as e:
                log.warning("No se pudo registrar la revisión del capítulo: %s", e)
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
            self._zoom_indicator.setText(f"🔍 {pct}%")
