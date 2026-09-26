"""
Aura Writer — Tree Controller Mixin
Lógica de árbol narrativo: crear, eliminar, mover y renombrar nodos
(Obras, Libros, Capítulos, Media, Notas de Autor).
"""

import os
from PyQt6.QtWidgets import QInputDialog, QFileDialog
from core.models import Obra, Book, MediaNode, AuthorNote


class TreeControllerMixin:
    """Mixin para AuraMainWindow: gestión completa del árbol narrativo."""

    # ------------------------------------------------------------------
    # Añadir nodos
    # ------------------------------------------------------------------

    def _on_add_node(self, parent_id: str, parent_type: str, new_type: str):
        """Crea un nuevo nodo. Auto-crea contenedores intermedios si no existen."""
        meta = self.project_manager.metadata
        if not meta:
            return

        if new_type == "obra":
            title, ok = QInputDialog.getText(self, "Nueva Obra", "Título de la obra:")
            if ok and title.strip():
                chapter = self.project_manager.create_chapter("Prólogo")
                self.project_manager.write_chapter_content(
                    chapter.content_file, "<h1>Prólogo</h1><p>Tu historia comienza aquí…</p>"
                )
                book = Book(title="Libro I", capitulos=[chapter])
                meta.obras.append(Obra(title=title.strip(), libros=[book]))
                self._refresh_tree()
                self.outline_tree.select_node_by_id(chapter.id)
                self.statusBar().showMessage(f"Obra '{title}' añadida con su Libro y Prólogo ✓", 3000)

        elif new_type == "libro":
            title, ok = QInputDialog.getText(self, "Nuevo Libro", "Título del libro:")
            if not ok or not title.strip():
                return
            obra = self._resolve_obra(parent_id, parent_type)
            chapter = self.project_manager.create_chapter("Prólogo")
            self.project_manager.write_chapter_content(
                chapter.content_file, "<h1>Prólogo</h1><p>Tu historia comienza aquí…</p>"
            )
            new_book = Book(title=title.strip(), capitulos=[chapter])
            obra.libros.append(new_book)
            self._refresh_tree()
            self.outline_tree.select_node_by_id(chapter.id)
            self.statusBar().showMessage(f"Libro '{title}' añadido con su Prólogo ✓", 3000)

        elif new_type == "chapter":
            title, ok = QInputDialog.getText(self, "Nuevo Capítulo", "Título del capítulo:")
            if not ok or not title.strip():
                return
            libro = self._resolve_libro(parent_id, parent_type)
            chapter = self.project_manager.create_chapter(title.strip())
            # Escribir contenido inicial con el título como h1 y párrafo vacío de escritura
            self.project_manager.write_chapter_content(
                chapter.content_file,
                f"<h1>{title.strip()}</h1><p></p>"
            )
            libro.capitulos.append(chapter)
            if libro.content_order:
                libro.content_order.append({"type": "chapter", "id": chapter.id})
            self._refresh_tree()
            # Navegar al capítulo recién creado para que el editor lo cargue
            self.outline_tree.select_node_by_id(chapter.id)
            # Posicionar el cursor al final (en el párrafo vacío) con la fuente correcta
            from PyQt6.QtGui import QTextCursor
            cursor = self.editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.editor.setTextCursor(cursor)
            self.editor.setFocus()
            self.statusBar().showMessage(f"Capítulo '{title}' añadido ✓", 3000)

        elif new_type == "media":
            path, _ = QFileDialog.getOpenFileName(
                self, "Seleccionar imagen", "",
                "Imágenes (*.png *.jpg *.jpeg *.gif *.webp)"
            )
            if not path:
                return
            title, ok = QInputDialog.getText(
                self, "Media", "Título / Pie de foto (opcional):",
                text=os.path.splitext(os.path.basename(path))[0]
            )
            if not ok:
                return
            ext = os.path.splitext(path)[1]
            with open(path, "rb") as f:
                data = f.read()
            asset_name = self.project_manager.save_media_asset(data, ext)
            media = MediaNode(title=title.strip() or "Imagen", image_asset=asset_name,
                              caption=title.strip())
            self._insert_media_node(media, parent_id, parent_type, meta)
            self._refresh_tree()
            self.statusBar().showMessage(f"Media '{media.title}' añadida ✓", 3000)

        elif new_type == "author_note":
            title, ok = QInputDialog.getText(self, "Nota de Autor", "Título de la nota:")
            if not ok or not title.strip():
                return
            chapter = self._resolve_chapter(parent_id, parent_type)
            note = AuthorNote(title=title.strip())
            chapter.author_notes.append(note)
            self._refresh_tree()
            self.statusBar().showMessage(f"Nota '{title}' añadida ✓", 3000)

        # Marcar el proyecto como modificado tras cualquier inserción
        self._mark_dirty()

    def _insert_media_node(self, media, parent_id: str, parent_type: str, meta):
        """Inserta un nodo de media en el contenedor más cercano según contexto."""
        if parent_type == "universe":
            meta.medias.append(media)
        elif parent_type == "obra":
            obra = self._find_obra(parent_id)
            if obra:
                obra.medias.append(media)
            else:
                meta.medias.append(media)
        elif parent_type == "libro":
            libro = self._find_libro(parent_id)
            if libro:
                libro.medias.append(media)
                libro.content_order.append({"type": "media", "id": media.id})
                if len(libro.content_order) == 1:
                    for cap in libro.capitulos:
                        libro.content_order.insert(len(libro.content_order) - 1,
                                                   {"type": "chapter", "id": cap.id})
            else:
                meta.medias.append(media)
        elif parent_type == "chapter":
            chapter = self.project_manager.find_chapter(parent_id)
            if chapter:
                chapter.medias.append(media)
            else:
                meta.medias.append(media)
        else:
            chapter = (self.project_manager.find_chapter(parent_id)
                       or self._find_parent_chapter(parent_id))
            libro = self._find_libro(parent_id) or self._find_parent_libro(parent_id)
            obra = self._find_obra(parent_id) or self._find_parent_obra(parent_id)
            if chapter:
                chapter.medias.append(media)
            elif libro:
                libro.medias.append(media)
                libro.content_order.append({"type": "media", "id": media.id})
                if len(libro.content_order) == 1:
                    for cap in libro.capitulos:
                        libro.content_order.insert(len(libro.content_order) - 1,
                                                   {"type": "chapter", "id": cap.id})
            elif obra:
                obra.medias.append(media)
            else:
                meta.medias.append(media)

    # ------------------------------------------------------------------
    # Auto-creación de contenedores intermedios
    # ------------------------------------------------------------------

    def _resolve_obra(self, context_id: str, context_type: str):
        """Encuentra o crea la Obra destino. Nunca falla."""
        meta = self.project_manager.metadata
        obra = self._find_obra(context_id)
        if obra:
            return obra
        obra = self._find_parent_obra(context_id)
        if obra:
            return obra
        if meta.obras:
            return meta.obras[0]
        obra = Obra(title=meta.title)
        meta.obras.append(obra)
        return obra

    def _resolve_libro(self, context_id: str, context_type: str):
        """Encuentra o crea el Libro destino. Auto-crea Obra si falta."""
        libro = self._find_libro(context_id)
        if libro:
            return libro
        libro = self._find_parent_libro(context_id)
        if libro:
            return libro
        obra = self._resolve_obra(context_id, context_type)
        if obra.libros:
            return obra.libros[0]
        libro = Book(title="Libro I")
        obra.libros.append(libro)
        return libro

    def _resolve_chapter(self, context_id: str, context_type: str):
        """Encuentra o crea el Capítulo destino. Auto-crea Libro/Obra si faltan."""
        chapter = self.project_manager.find_chapter(context_id)
        if chapter:
            return chapter
        chapter = self._find_parent_chapter(context_id)
        if chapter:
            return chapter
        libro = self._resolve_libro(context_id, context_type)
        if libro.capitulos:
            return libro.capitulos[0]
        chapter = self.project_manager.create_chapter("Nuevo Capítulo")
        libro.capitulos.append(chapter)
        return chapter

    # ------------------------------------------------------------------
    # Eliminar nodos (mover a papelera)
    # ------------------------------------------------------------------

    def _on_delete_node(self, item_id: str, item_type: str):
        """Mueve un nodo del metadata a la papelera de reciclaje."""
        meta = self.project_manager.metadata
        if not meta:
            return

        obj = self._pluck_node(item_id, item_type)
        if not obj:
            return

        title = getattr(obj, "title", getattr(obj, "name", "Elemento"))

        from core.models import TrashedItem
        trashed = TrashedItem(
            original_id=item_id,
            item_type=item_type,
            title=title,
            data=obj.model_dump(mode="json")
        )
        if not hasattr(meta, "trash") or meta.trash is None:
            meta.trash = []
        meta.trash.append(trashed)

        if item_type == "chapter" and self._current_chapter and self._current_chapter.id == item_id:
            self._current_chapter = None
            self.editor.clear()

        self._mark_dirty()  # NEW-02: eliminar nodo debe marcar el proyecto como modificado
        self._refresh_tree()
        self.statusBar().showMessage(f"'{title}' movido a la papelera (puedes restaurarlo)", 4000)

    # ------------------------------------------------------------------
    # Extracción de nodos
    # ------------------------------------------------------------------

    def _pluck_node(self, item_id: str, item_type: str):
        """Extrae un objeto del metadata y lo devuelve (para moverlo o borrarlo)."""
        meta = self.project_manager.metadata
        if not meta:
            return None

        if item_type == "obra":
            for i, o in enumerate(meta.obras):
                if o.id == item_id:
                    return meta.obras.pop(i)
        elif item_type == "libro":
            for o in meta.obras:
                for i, l in enumerate(o.libros):
                    if l.id == item_id:
                        return o.libros.pop(i)
        elif item_type == "chapter":
            for o in meta.obras:
                for l in o.libros:
                    for i, c in enumerate(l.capitulos):
                        if c.id == item_id:
                            if l.content_order:
                                l.content_order = [e for e in l.content_order if e.get("id") != item_id]
                            return l.capitulos.pop(i)
        elif item_type == "media":
            for i, m in enumerate(meta.medias):
                if m.id == item_id:
                    return meta.medias.pop(i)
            for o in meta.obras:
                for i, m in enumerate(o.medias):
                    if m.id == item_id:
                        return o.medias.pop(i)
                for l in o.libros:
                    for i, m in enumerate(l.medias):
                        if m.id == item_id:
                            l.content_order = [e for e in l.content_order if e.get("id") != item_id]
                            return l.medias.pop(i)
                    for c in l.capitulos:
                        for i, m in enumerate(c.medias):
                            if m.id == item_id:
                                return c.medias.pop(i)
        elif item_type == "author_note":
            # Buscar en capítulos, libros y obras
            for o in meta.obras:
                for n in list(o.author_notes):
                    if n.id == item_id:
                        o.author_notes.remove(n)
                        return n
                for l in o.libros:
                    for n in list(l.author_notes):
                        if n.id == item_id:
                            l.author_notes.remove(n)
                            return n
                    for c in l.capitulos:
                        for i, n in enumerate(c.author_notes):
                            if n.id == item_id:
                                return c.author_notes.pop(i)
        return None

    # ------------------------------------------------------------------
    # Reordenamiento (Drag & Drop)
    # ------------------------------------------------------------------

    def _on_node_moved(self, src_id: str, src_type: str, target_id: str, target_type_raw: str):
        """Mueve un nodo con posición exacta (above / below / on) respecto al target."""
        meta = self.project_manager.metadata
        if not meta:
            return

        # Decodificar posición codificada en target_type ("libro:above" → target_type="libro", pos="above")
        if ":" in target_type_raw:
            target_type, position = target_type_raw.rsplit(":", 1)
        else:
            target_type, position = target_type_raw, "on"

        obj = self._pluck_node(src_id, src_type)
        if not obj:
            return

        if src_type == "obra":
            meta.obras.append(obj)

        elif src_type == "libro":
            obra = self._resolve_obra(target_id, target_type)
            obra.libros.append(obj)

        elif src_type == "chapter":
            # Siempre moverse dentro del libro que contiene el target
            libro = (self._find_libro(target_id)           # target ES el libro
                     or self._find_parent_libro(target_id)) # target es un capítulo hermano

            if not libro:
                self.statusBar().showMessage("No se pudo determinar el libro destino.", 3000)
                return

            # Añadir el capítulo al libro (ya fue extraído por _pluck_node)
            if obj not in libro.capitulos:
                libro.capitulos.append(obj)

            # Asegurarnos de que content_order existe
            if not libro.content_order:
                libro.content_order = [
                    {"type": "chapter", "id": c.id} for c in libro.capitulos
                ]

            # Quitar la entrada del origen en content_order (puede estar como antiguo)
            libro.content_order = [e for e in libro.content_order if e.get("id") != src_id]

            # Determinar índice de inserción
            if target_id == libro.id or target_type == "libro":
                # Soltado sobre el propio libro → al final
                insert_idx = len(libro.content_order)
            else:
                # Buscar posición del target en content_order
                target_idx = next(
                    (i for i, e in enumerate(libro.content_order) if e.get("id") == target_id),
                    None,
                )
                if target_idx is None:
                    insert_idx = len(libro.content_order)
                elif position == "above":
                    insert_idx = target_idx        # antes del target
                elif position == "below":
                    insert_idx = target_idx + 1    # después del target
                else:
                    insert_idx = target_idx + 1    # "on" → tratar como después

            libro.content_order.insert(insert_idx, {"type": "chapter", "id": src_id})

        elif src_type == "author_note":
            chapter = self._resolve_chapter(target_id, target_type)
            chapter.author_notes.append(obj)

        elif src_type == "media":
            if target_type in ("universe", "universe"):
                meta.medias.append(obj)
            elif target_type == "obra":
                obra = self._find_obra(target_id)
                if obra:
                    obra.medias.append(obj)
                else:
                    meta.medias.append(obj)
            elif target_type == "libro":
                libro = self._find_libro(target_id)
                if libro:
                    libro.medias.append(obj)
                    libro.content_order.append({"type": "media", "id": obj.id})
                else:
                    meta.medias.append(obj)
            elif target_type == "chapter":
                chapter = self.project_manager.find_chapter(target_id)
                if chapter:
                    chapter.medias.append(obj)
                else:
                    meta.medias.append(obj)
            else:
                chapter = (self.project_manager.find_chapter(target_id)
                           or self._find_parent_chapter(target_id))
                libro = self._find_libro(target_id) or self._find_parent_libro(target_id)
                obra  = self._find_obra(target_id)  or self._find_parent_obra(target_id)
                if chapter:
                    chapter.medias.append(obj)
                elif libro:
                    libro.medias.append(obj)
                    libro.content_order.append({"type": "media", "id": obj.id})
                elif obra:
                    obra.medias.append(obj)
                else:
                    meta.medias.append(obj)

        self._mark_dirty()
        self._refresh_tree()
        self.statusBar().showMessage("Elemento movido ✓", 3000)


    # ------------------------------------------------------------------
    # Renombrar nodos
    # ------------------------------------------------------------------

    def _on_rename_node(self, item_id: str, item_type: str, new_name: str):
        """Aplica el nuevo nombre al metadata."""
        meta = self.project_manager.metadata
        if not meta:
            return

        if item_type == "universe":
            meta.title = new_name
            self.setWindowTitle(f"Aura Writer - {new_name}")
        elif item_type == "obra":
            obra = self._find_obra(item_id)
            if obra:
                obra.title = new_name
        elif item_type == "libro":
            libro = self._find_libro(item_id)
            if libro:
                libro.title = new_name
        elif item_type == "chapter":
            chapter = self.project_manager.find_chapter(item_id)
            if chapter:
                chapter.title = new_name
        elif item_type == "media":
            media = self._find_media(item_id)
            if media:
                media.title = new_name
        elif item_type == "author_note":
            note = self._find_author_note(item_id)
            if note:
                note.title = new_name

        self.outline_tree.update_item_text(item_id, new_name)
        self._mark_dirty()  # FIX BUG-05: renombrar cualquier nodo debe activar guardado
        self.statusBar().showMessage(f"Renombrado a '{new_name}' ✓", 3000)

    def _refresh_tree(self):
        """Refresca el árbol preservando la vista."""
        if self.project_manager.metadata:
            self.outline_tree.populate_from_metadata(self.project_manager.metadata)
            self._refresh_char_dock()
            if hasattr(self, "_refresh_place_dock"):
                self._refresh_place_dock()
