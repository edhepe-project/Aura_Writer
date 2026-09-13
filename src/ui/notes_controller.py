"""
Aura Writer — Notes Controller Mixin
Gestión del inspector de notas de autor y utilidades de búsqueda
(finder helpers, media preview, carga de notas/capítulos).
"""

import os
from PyQt6.QtWidgets import (QInputDialog, QMessageBox, QDialog, QVBoxLayout,
                              QHBoxLayout, QLabel, QLineEdit, QPushButton,
                              QScrollArea, QListWidgetItem)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from core.models import Obra, Book, Chapter, MediaNode, AuthorNote


class NotesControllerMixin:
    """Mixin para AuraMainWindow: notas de autor, búsquedas y preview de media."""

    # ------------------------------------------------------------------
    # Inspector de notas
    # ------------------------------------------------------------------

    def _refresh_notes_list(self, select_id: str = None):
        self.notes_list.blockSignals(True)
        self.notes_list.clear()

        if self._current_container and hasattr(self._current_container, "author_notes"):
            for note in self._current_container.author_notes:
                item = QListWidgetItem(note.title)
                item.setData(Qt.ItemDataRole.UserRole, note.id)
                self.notes_list.addItem(item)

            if select_id:
                for i in range(self.notes_list.count()):
                    item = self.notes_list.item(i)
                    if item.data(Qt.ItemDataRole.UserRole) == select_id:
                        self.notes_list.setCurrentItem(item)
                        item.setSelected(True)
                        break
            elif self.notes_list.count() > 0:
                item = self.notes_list.item(0)
                self.notes_list.setCurrentItem(item)
                item.setSelected(True)

        self.notes_list.blockSignals(False)
        self._on_note_list_selection_changed()

    def _on_note_list_selection_changed(self):
        if self._current_note:
            self._current_note.content = self.inspector_notes.toPlainText()

        selectedItems = self.notes_list.selectedItems()
        if not selectedItems:
            self._current_note = None
            self.inspector_notes.clear()
            self.inspector_notes.setPlaceholderText("Selecciona una nota o crea una...")
            return

        note_id = selectedItems[0].data(Qt.ItemDataRole.UserRole)
        note = self._find_author_note(note_id)
        if note:
            self._current_note = note
            self.inspector_notes.setPlainText(note.content)

    def _on_inspector_add_note(self):
        if not self._current_container or not hasattr(self._current_container, "author_notes"):
            QMessageBox.warning(self, "Aviso", "Selecciona una Obra, Libro o Capítulo primero.")
            return

        title, ok = QInputDialog.getText(self, "Nueva Nota", "Título de la nota:")
        if ok and title:
            from core.models import AuthorNote
            new_note = AuthorNote(title=title)
            self._current_container.author_notes.append(new_note)
            self._mark_dirty()  # FIX BUG-04: nota nueva debe activar guardado
            self._refresh_notes_list(select_id=new_note.id)
            self.inspector_notes.setFocus()

    def _on_inspector_delete_note(self):
        selectedItems = self.notes_list.selectedItems()
        if not selectedItems:
            return

        note_id = selectedItems[0].data(Qt.ItemDataRole.UserRole)
        note_title = selectedItems[0].text()

        reply = QMessageBox.question(
            self, "Eliminar Nota",
            f"¿Eliminar la nota '{note_title}' permanentemente?"
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self._current_note and self._current_note.id == note_id:
                self._current_note = None
                self.inspector_notes.clear()
            self._current_container.author_notes = [
                n for n in self._current_container.author_notes if n.id != note_id
            ]
            self._mark_dirty()  # FIX BUG-03: eliminación de nota debe activar guardado
            self._refresh_notes_list()

    def _load_author_note(self, note_id: str):
        note = self._find_author_note(note_id)
        if note:
            self._current_note = note
            self.inspector_notes.setPlainText(note.content)
            self.statusBar().showMessage(f"Nota: {note.title}")

    # ------------------------------------------------------------------
    # Carga de capítulo
    # ------------------------------------------------------------------

    def _load_chapter(self, chapter: Chapter):
        self._current_chapter = chapter
        html = self.project_manager.read_chapter_content(chapter.content_file)
        self.editor.setHtml(html)
        self.statusBar().showMessage(f"Editando: {chapter.title}")
        self._detect_character_mentions(chapter)
        self._refresh_char_dock()

    # ------------------------------------------------------------------
    # Preview de media
    # ------------------------------------------------------------------

    def _show_media_preview(self, media_id: str):
        """Muestra la imagen en un diálogo de previsualización dedicado."""
        media = self._find_media(media_id)
        if not media or not media.image_asset:
            return

        path = self.project_manager.get_media_asset_path(media.image_asset)
        if not os.path.exists(path):
            QMessageBox.warning(self, "Media", "El archivo de imagen no se encontró.")
            return

        pixmap = QPixmap(path)
        if pixmap.isNull():
            QMessageBox.warning(self, "Media", "No se pudo cargar la imagen.")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(f"🖼️  {media.title}")
        dlg.setMinimumSize(500, 400)
        dlg.resize(min(pixmap.width() + 80, 900), min(pixmap.height() + 180, 700))
        dlg.setStyleSheet("""
            QDialog { background: #1c1c1e; }
            QLabel { color: #f2f2f7; }
            QLineEdit {
                background: #2c2c2e; color: #f2f2f7; border: 1px solid #3a3a3c;
                border-radius: 6px; padding: 8px; font-size: 13px;
            }
            QPushButton {
                background: #3a3a3c; color: #f2f2f7; border: none;
                border-radius: 6px; padding: 8px 16px; font-size: 12px;
            }
            QPushButton:hover { background: #48484a; }
        """)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: #1c1c1e; }")
        img_label = QLabel()
        img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        max_w = min(dlg.width() - 40, 850)
        max_h = min(dlg.height() - 150, 600)
        scaled = pixmap.scaled(max_w, max_h,
                               Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)
        img_label.setPixmap(scaled)
        scroll.setWidget(img_label)
        layout.addWidget(scroll, 1)

        title_label = QLabel(f"<b style='color:#aaa; font-size:11px;'>TÍTULO:</b>  "
                             f"<span style='font-size:14px;'>{media.title}</span>")
        layout.addWidget(title_label)

        caption_row = QHBoxLayout()
        caption_label = QLabel("Pie de foto:")
        caption_label.setStyleSheet("font-size: 12px; color: #8e8e93;")
        caption_edit = QLineEdit(media.caption)
        caption_edit.setPlaceholderText("Escribe un pie de foto para la exportación…")
        caption_row.addWidget(caption_label)
        caption_row.addWidget(caption_edit, 1)
        layout.addLayout(caption_row)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_save = QPushButton("💾  Guardar y cerrar")
        btn_save.clicked.connect(dlg.accept)
        btn_cancel = QPushButton("Cerrar")
        btn_cancel.clicked.connect(dlg.reject)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

        result = dlg.exec()
        if result == QDialog.DialogCode.Accepted:
            new_caption = caption_edit.text().strip()
            if new_caption != media.caption:
                media.caption = new_caption
                self._mark_dirty()  # FIX BUG-06: cambio de caption debe activar guardado
                self.statusBar().showMessage(f"Pie de foto actualizado: '{new_caption}' ✓", 3000)
                return

        self.statusBar().showMessage(f"Media: {media.title}", 3000)

    # ------------------------------------------------------------------
    # Finder helpers (búsquedas por ID en el metadata)
    # ------------------------------------------------------------------

    def _find_obra(self, obra_id: str) -> "Obra | None":
        if not self.project_manager.metadata:
            return None
        for obra in self.project_manager.metadata.obras:
            if obra.id == obra_id:
                return obra
        return None

    def _find_libro(self, libro_id: str) -> "Book | None":
        if not self.project_manager.metadata:
            return None
        for obra in self.project_manager.metadata.obras:
            for libro in obra.libros:
                if libro.id == libro_id:
                    return libro
        return None

    def _find_media(self, media_id: str) -> "MediaNode | None":
        if not self.project_manager.metadata:
            return None
        meta = self.project_manager.metadata
        for m in meta.medias:
            if m.id == media_id:
                return m
        for obra in meta.obras:
            for m in obra.medias:
                if m.id == media_id:
                    return m
            for libro in obra.libros:
                for m in libro.medias:
                    if m.id == media_id:
                        return m
                for cap in libro.capitulos:
                    for m in cap.medias:
                        if m.id == media_id:
                            return m
        return None

    def _find_author_note(self, note_id: str) -> "AuthorNote | None":
        if not self.project_manager.metadata:
            return None
        meta = self.project_manager.metadata
        for n in meta.author_notes:
            if n.id == note_id:
                return n
        for obra in meta.obras:
            for n in obra.author_notes:
                if n.id == note_id:
                    return n
            for libro in obra.libros:
                for n in libro.author_notes:
                    if n.id == note_id:
                        return n
                for cap in libro.capitulos:
                    for note in cap.author_notes:
                        if note.id == note_id:
                            return note
        return None

    def _find_parent_obra(self, child_id: str) -> "Obra | None":
        """Busca la Obra que contiene un nodo hijo (libro, capítulo, media, nota)."""
        if not self.project_manager.metadata:
            return None
        for obra in self.project_manager.metadata.obras:
            # FIX INC-03: incluir author_notes directas de la obra
            for n in obra.author_notes:
                if n.id == child_id:
                    return obra
            for m in obra.medias:
                if m.id == child_id:
                    return obra
            for libro in obra.libros:
                if libro.id == child_id:
                    return obra
                for m in libro.medias:
                    if m.id == child_id:
                        return obra
                for cap in libro.capitulos:
                    if cap.id == child_id:
                        return obra
                    for m in cap.medias:
                        if m.id == child_id:
                            return obra
                    for n in cap.author_notes:
                        if n.id == child_id:
                            return obra
        return None


    def _find_parent_libro(self, child_id: str) -> "Book | None":
        """Busca el Libro que contiene un nodo hijo."""
        if not self.project_manager.metadata:
            return None
        for obra in self.project_manager.metadata.obras:
            for libro in obra.libros:
                for m in libro.medias:
                    if m.id == child_id:
                        return libro
                for cap in libro.capitulos:
                    if cap.id == child_id:
                        return libro
                    for m in cap.medias:
                        if m.id == child_id:
                            return libro
                    for n in cap.author_notes:
                        if n.id == child_id:
                            return libro
        return None

    def _find_parent_chapter(self, child_id: str) -> "Chapter | None":
        """Busca el Capítulo que contiene un nodo hijo (media o nota)."""
        if not self.project_manager.metadata:
            return None
        for obra in self.project_manager.metadata.obras:
            for libro in obra.libros:
                for cap in libro.capitulos:
                    for m in cap.medias:
                        if m.id == child_id:
                            return cap
                    for n in cap.author_notes:
                        if n.id == child_id:
                            return cap
        return None

    # ------------------------------------------------------------------
    # Utilidad de orden de contenido (usada por el exportador)
    # ------------------------------------------------------------------

    def _build_ordered_items(self, libro: Book) -> list:
        """
        Retorna una lista de tuplas (tipo, objeto) en el orden correcto para exportar.
        Si content_order está definido se usa; si no, capítulos en orden y luego medias.
        """
        result = []
        if libro.content_order:
            cap_map = {c.id: c for c in libro.capitulos}
            media_map = {m.id: m for m in libro.medias}
            rendered = set()
            for entry in libro.content_order:
                eid = entry.get("id")
                etype = entry.get("type")
                if etype == "chapter" and eid in cap_map:
                    result.append(("chapter", cap_map[eid]))
                    rendered.add(eid)
                elif etype == "media" and eid in media_map:
                    result.append(("media", media_map[eid]))
                    rendered.add(eid)
            for cap in libro.capitulos:
                if cap.id not in rendered:
                    result.append(("chapter", cap))
            for m in libro.medias:
                if m.id not in rendered:
                    result.append(("media", m))
        else:
            for cap in libro.capitulos:
                result.append(("chapter", cap))
            for m in libro.medias:
                result.append(("media", m))
        return result
