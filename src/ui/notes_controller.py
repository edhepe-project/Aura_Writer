"""
Aura Writer — Notes Controller Mixin
Gestión del inspector de notas de autor y utilidades de búsqueda
(finder helpers, media preview, carga de notas/capítulos).
"""

import os
import re
from PyQt6.QtWidgets import (QInputDialog, QMessageBox, QDialog, QVBoxLayout,
                              QHBoxLayout, QLabel, QLineEdit, QPushButton,
                              QScrollArea, QListWidgetItem)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from core.models import Obra, Book, Chapter, MediaNode, AuthorNote


class NotesControllerMixin:
    """Mixin para AuraMainWindow: notas de autor, búsquedas y preview de media."""
    _current_chapter: "Chapter | None" = None

    # ------------------------------------------------------------------
    # Inspector de notas
    # ------------------------------------------------------------------

    def _refresh_notes_list(self, select_id: str = None):
        """Recarga la lista de notas del inspector."""
        self.notes_list.blockSignals(True)
        self.notes_list.clear()

        if self._current_container and hasattr(self._current_container, "author_notes"):
            for note in self._current_container.author_notes:
                item = QListWidgetItem(f"{note.title}")
                item.setData(Qt.ItemDataRole.UserRole, note.id)
                item.setToolTip("Doble click para ver y editar")
                self.notes_list.addItem(item)

            if select_id:
                for i in range(self.notes_list.count()):
                    item = self.notes_list.item(i)
                    if item.data(Qt.ItemDataRole.UserRole) == select_id:
                        self.notes_list.setCurrentItem(item)
                        break
            elif self.notes_list.count() > 0:
                self.notes_list.setCurrentItem(self.notes_list.item(0))

        self.notes_list.blockSignals(False)
        self._update_note_preview()

    def _update_note_preview(self):
        """Actualiza el preview de texto en el inspector con la nota seleccionada."""
        item = self.notes_list.currentItem()
        if item is None:
            self._current_note = None
            self.inspector_notes.clear()
            self.inspector_notes.setPlaceholderText(
                "No hay notas.\nUsa '+ Nota' para crear una o\ndoble click para editar."
            )
            return
        note_id = item.data(Qt.ItemDataRole.UserRole)
        note = self._find_author_note(note_id)
        if note:
            self._current_note = note
            preview = note.content.strip()
            if not preview:
                preview = "(sin contenido — doble click para editar)"
            self.inspector_notes.setPlainText(preview)
        else:
            self.inspector_notes.clear()

    def _on_note_list_selection_changed(self, current=None, previous=None):
        """Actualiza el preview cuando cambia la selección."""
        self._update_note_preview()

    def _on_note_double_clicked(self, item):
        """Abre el NoteEditorDialog al hacer doble click en una nota."""
        note_id = item.data(Qt.ItemDataRole.UserRole)
        note = self._find_author_note(note_id)
        if not note:
            return

        from ui.note_editor_dialog import NoteEditorDialog
        dlg = NoteEditorDialog(note, parent=self)
        result = dlg.exec()

        if result == QDialog.DialogCode.Accepted:
            if dlg.was_deleted:
                # Eliminar la nota
                if self._current_note and self._current_note.id == note_id:
                    self._current_note = None
                self._current_container.author_notes = [
                    n for n in self._current_container.author_notes
                    if n.id != note_id
                ]
                self._mark_dirty()
                self._refresh_notes_list()
            else:
                # Guardar cambios (el dialog ya modificó note.title y note.content)
                self._mark_dirty()
                self._refresh_notes_list(select_id=note_id)
                self.statusBar().showMessage(f"Nota guardada: {note.title}")

    def _on_inspector_add_note(self):
        """Crea una nueva nota y abre directamente el editor."""
        from core.models import Chapter
        if not self._current_container or not isinstance(self._current_container, Chapter):
            QMessageBox.warning(
                self, "Aviso",
                "Las notas de autor solo están permitidas dentro de los capítulos.\n"
                "Por favor, selecciona un Capítulo primero."
            )
            return

        title, ok = QInputDialog.getText(self, "Nueva Nota", "Título de la nota:")
        if ok and title:
            from core.models import AuthorNote
            from ui.note_editor_dialog import NoteEditorDialog
            new_note = AuthorNote(title=title)
            self._current_container.author_notes.append(new_note)
            self._mark_dirty()
            self._refresh_notes_list(select_id=new_note.id)
            # Abrir el editor inmediatamente
            dlg = NoteEditorDialog(new_note, parent=self)
            result = dlg.exec()
            if result == QDialog.DialogCode.Accepted:
                if dlg.was_deleted:
                    self._current_container.author_notes = [
                        n for n in self._current_container.author_notes
                        if n.id != new_note.id
                    ]
                self._mark_dirty()
                self._refresh_notes_list()

    def _on_inspector_delete_note(self):
        """Elimina la nota seleccionada (botón Eliminar del panel)."""
        item = self.notes_list.currentItem()
        if not item:
            return
        note_id   = item.data(Qt.ItemDataRole.UserRole)
        note_title = item.text()

        reply = QMessageBox.question(
            self, "Eliminar Nota",
            f"¿Eliminar la nota «{note_title}» permanentemente?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self._current_note and self._current_note.id == note_id:
                self._current_note = None
            self._current_container.author_notes = [
                n for n in self._current_container.author_notes if n.id != note_id
            ]
            self._mark_dirty()
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
        self._current_container_type = "chapter"
        self._current_container_obj = chapter
        html = self.project_manager.read_chapter_content(chapter.content_file)

        # Cancelar cualquier revision ortografica pendiente del capitulo anterior
        if hasattr(self.editor, '_spell_timer'):
            self.editor._spell_timer.stop()

        # Bloquear actualizaciones visuales para evitar el salto de línea
        # que produce Qt al recorrer y modificar formatos de párrafo tras setHtml()
        self.editor.setUpdatesEnabled(False)
        try:
            self.editor.setHtml(html)
            # Colocar cursor al inicio en silencio (sin scroll)
            cursor = self.editor.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            self.editor.setTextCursor(cursor)
            # Reaplicar estilo visual (papel, fuente base, zoom) al HTML cargado
            if hasattr(self.editor, "_apply_appearance"):
                self.editor._apply_appearance()
            # Propagar la familia de tipografía activa al texto del HTML cargado
            if hasattr(self.editor, "_update_document_font"):
                self.editor._update_document_font(self.editor._work_font_family)
            # Aplicar espaciado armónico de párrafo a los párrafos cargados
            if hasattr(self.editor, "_apply_paragraph_spacing"):
                self.editor._apply_paragraph_spacing()
            # Forzar scroll al inicio de forma silenciosa antes de mostrar
            self.editor.verticalScrollBar().setValue(0)
            self.editor.document().setModified(False)
        finally:
            self.editor.setUpdatesEnabled(True)

        self.statusBar().showMessage(f"Editando: {chapter.title}")
        self._detect_character_mentions(chapter)
        self._detect_place_mentions(chapter)
        self._refresh_char_dock()
        self._refresh_place_dock()

        # Actualizar indicador de lugar activo en barra de estado
        if hasattr(self, "_place_status_indicator"):
            if chapter.places_present and self.project_manager.metadata:
                places = getattr(self.project_manager.metadata, "places", [])
                p_names = [p.name for p in places if p.id in chapter.places_present]
                if p_names:
                    txt = (p_names[0] if len(p_names) == 1 else f"{p_names[0]} (+{len(p_names)-1})")
                    self._place_status_indicator.setText(txt)
                else:
                    self._place_status_indicator.setText("")
            else:
                self._place_status_indicator.setText("")

        self.editor.setFocus()

    def _load_container_synopsis(self, container_type: str, container_obj):
        """Carga la ficha / sinopsis de un Universo, Obra o Libro con formato
        completamente uniforme y sin herencias del editor de capitulos."""
        self._current_chapter = None
        self._current_container_type = container_type
        self._current_container_obj = container_obj

        if not container_obj:
            return

        raw_synopsis = getattr(container_obj, "synopsis", "") or ""

        # Limpiar si el texto guardado anteriormente contenia cabeceras duplicadas
        if "<h1" in raw_synopsis:
            if '<div id="synopsis-body">' in raw_synopsis:
                raw_synopsis = raw_synopsis.split('<div id="synopsis-body">')[-1].split('</div>')[0]
            elif '<hr' in raw_synopsis:
                raw_synopsis = raw_synopsis.split('<hr')[-1].split('>', 1)[-1]
            raw_synopsis = raw_synopsis.strip()

        title = getattr(container_obj, "title", "Sin Titulo")

        if container_type == "universe":
            header_subtitle = "Sinopsis del Universo Narrativo"
            badge = "Autor: " + getattr(container_obj, "author", "Sin registrar")
        elif container_type == "obra":
            header_subtitle = "Sinopsis de la Obra"
            num_libros = len(getattr(container_obj, "libros", []))
            badge = f"Contiene {num_libros} libro(s)"
        elif container_type == "libro":
            header_subtitle = "Sinopsis del Libro"
            num_caps = len(getattr(container_obj, "capitulos", []))
            badge = f"Contiene {num_caps} capitulo(s)"
        else:
            header_subtitle = "Resumen"
            badge = ""

        # Normalizar contenido guardado: eliminar sangrias, margenes e inline styles de color antiguos
        if raw_synopsis.startswith("<"):
            # Quitar cualquier text-indent / margin-left inline que haya quedado guardado
            raw_synopsis = re.sub(r'text-indent\s*:\s*[^;]+;?', 'text-indent:0;', raw_synopsis)
            raw_synopsis = re.sub(r'margin-left\s*:\s*[^;]+;?', 'margin-left:0;', raw_synopsis)
            # Eliminar atributos color: ... inline viejos para que responda al CSS dinámico
            raw_synopsis = re.sub(r'color\s*:\s*[^;]+;?', '', raw_synopsis)
            content_html = raw_synopsis
        else:
            paragraphs = raw_synopsis.split("\n\n") if raw_synopsis else []
            content_html = "".join(
                "<p>" + p.replace("\n", "<br>") + "</p>"
                for p in paragraphs if p.strip()
            )
            if not content_html:
                content_html = '<p class="placeholder">Escribe aquí la sinopsis, premisa o notas generales...</p>'

        # Obtener tema y papel activo para ajustar los colores del HTML estático
        from core.theme_manager import ThemeManager
        paper = getattr(self.editor, "_paper_style", "auto")
        is_dark_theme = ThemeManager.is_dark()
        
        # Determinar si la vista del editor es oscura según el papel o el tema
        if paper == "oled":
            paper_type = "oled"
        elif paper == "noche":
            paper_type = "noche"
        elif paper in ("blanco", "sepia", "verde"):
            paper_type = paper
        else: # auto
            paper_type = "dark" if is_dark_theme else "light"

        if paper_type == "oled":
            text_color = "#f4f4f5"
            h1_color = "#ffffff"
            sub_color = "#38bdf8"
            badge_color = "#a1a1aa"
            border_color = "#27272a"
            placeholder_color = "#71717a"
        elif paper_type in ("noche", "dark"):
            text_color = "#e4e4e7"
            h1_color = "#ffffff"
            sub_color = "#60a5fa"
            badge_color = "#a1a1aa"
            border_color = "#3f3f46"
            placeholder_color = "#8e8e93"
        elif paper_type == "sepia":
            text_color = "#2d241e"
            h1_color = "#1c1510"
            sub_color = "#0284c7"
            badge_color = "#78716c"
            border_color = "#d6c7b2"
            placeholder_color = "#78716c"
        elif paper_type == "verde":
            text_color = "#1c2e1c"
            h1_color = "#0f1c0f"
            sub_color = "#0284c7"
            badge_color = "#526e52"
            border_color = "#c2d6c0"
            placeholder_color = "#526e52"
        else: # blanco / light
            text_color = "#1f2937"
            h1_color = "#111827"
            sub_color = "#2563eb"
            badge_color = "#4b5563"
            border_color = "#e5e7eb"
            placeholder_color = "#6b7280"

        work_font = getattr(self.editor, "_work_font_family", "Georgia")

        # CSS y estilos directos inline para garantizar que el motor de texto de Qt
        # respete los colores independientemente de cualquier herencia previa
        full_html = (
            '<!DOCTYPE html>\n'
            '<html><head><style>\n'
            '* { box-sizing: border-box; }\n'
            'body { margin: 0; padding: 0;'
            f' font-family: "{work_font}", Georgia, serif;'
            f' font-size: 15px; line-height: 1.6; color: {text_color}; }}\n'
            '#synopsis-wrapper { max-width: 780px; margin: 0 auto; padding: 10px 20px 40px 20px; }\n'
            '#synopsis-wrapper * { text-indent: 0 !important; margin-left: 0 !important; padding-left: 0 !important; }\n'
            f'#synopsis-wrapper h1 {{ margin-top: 0; margin-bottom: 4px; font-size: 26px; font-weight: 700; line-height: 1.2; color: {h1_color}; }}\n'
            f'#synopsis-wrapper .synopsis-meta {{ color: {sub_color}; font-weight: 600; font-size: 13px; margin-top: 0; margin-bottom: 12px; }}\n'
            f'#synopsis-wrapper .synopsis-meta span {{ color: {badge_color}; font-weight: normal; }}\n'
            f'#synopsis-wrapper hr {{ border: 0; border-top: 1px solid {border_color}; margin: 12px 0 20px 0; }}\n'
            f'#synopsis-wrapper p {{ margin-top: 0; margin-bottom: 12px; line-height: 1.6; color: {text_color}; }}\n'
            f'#synopsis-wrapper p.placeholder {{ color: {placeholder_color}; font-style: italic; }}\n'
            '</style></head><body>\n'
            '<div id="synopsis-wrapper">\n'
            f'    <h1 style="color:{h1_color}; margin-top:0; margin-bottom:4px; font-size:26px; font-weight:700;">{title}</h1>\n'
            f'    <p class="synopsis-meta" style="color:{sub_color}; font-weight:600; font-size:13px; margin-top:0; margin-bottom:12px;">{header_subtitle} &nbsp;&bull;&nbsp; <span style="color:{badge_color}; font-weight:normal;">{badge}</span></p>\n'
            f'    <hr style="border:0; border-top:1px solid {border_color}; margin:12px 0 20px 0;">\n'
            '    <div id="synopsis-body">\n'
            f'        {content_html}\n'
            '    </div>\n'
            '</div>\n'
            '</body></html>'
        )

        self.editor.setUpdatesEnabled(False)
        try:
            self.editor.setHtml(full_html)
            # Solo aplicar apariencia visual (papel, zoom).
            # NO llamar _apply_paragraph_spacing ni _update_document_font ya que
            # esos metodos recorren bloque por bloque y rompen la uniformidad del HTML.
            if hasattr(self.editor, "_apply_appearance"):
                self.editor._apply_appearance()
            self.editor.verticalScrollBar().setValue(0)
            self.editor.document().setModified(False)
        finally:
            self.editor.setUpdatesEnabled(True)

        self.statusBar().showMessage(f"Sinopsis: {title}")


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
        dlg.setWindowTitle(f"{media.title}")
        dlg.setMinimumSize(500, 400)
        dlg.resize(min(pixmap.width() + 80, 900), min(pixmap.height() + 180, 700))

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
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
