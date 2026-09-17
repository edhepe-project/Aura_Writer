"""
Aura Writer — Character Controller Mixin
Gestion de personajes: sincronizacion, deteccion de menciones, dock y relaciones.
"""
from bs4 import BeautifulSoup
from PyQt6.QtWidgets import QMessageBox
from core.models import Chapter, Character


class CharacterControllerMixin:
    """Mixin para AuraMainWindow: personajes y dock de fichas."""

    def _on_character_added(self, char: Character):
        """Sincroniza el personaje creado/modificado en el CharacterDock al metadata."""
        if not self.project_manager.metadata:
            return
        meta = self.project_manager.metadata
        if not any(c.id == char.id for c in meta.characters):
            meta.characters.append(char)
            self.statusBar().showMessage(f"Personaje '{char.name}' anadido", 3000)
        self._sync_relations_to_metadata()
        self._dirty = True

    def _on_character_deleted(self, char_id: str):
        """Mueve a la papelera el personaje eliminado desde el CharacterDock."""
        if not self.project_manager.metadata:
            return
        meta = self.project_manager.metadata
        char_obj = next((c for c in meta.characters if c.id == char_id), None)
        if char_obj:
            from core.models import TrashedItem
            trashed = TrashedItem(
                original_id=char_id, item_type="character",
                title=char_obj.name, data=char_obj.model_dump(mode="json")
            )
            if not hasattr(meta, "trash") or meta.trash is None:
                meta.trash = []
            meta.trash.append(trashed)
        meta.characters = [c for c in meta.characters if c.id != char_id]
        meta.relations = [r for r in meta.relations
                          if r.char_id_a != char_id and r.char_id_b != char_id]
        self._dirty = True
        self.statusBar().showMessage("Personaje movido a la papelera", 3000)

    def _sync_relations_to_metadata(self):
        """Copia las relaciones del dock al metadata del proyecto."""
        if self.project_manager.metadata:
            self.project_manager.metadata.relations = self.char_dock.get_relations()

    def _on_graph_character_focused(self, char_id: str):
        """Enfoca la ficha del personaje al hacer doble clic en el grafo de relaciones."""
        self.char_dock.select_character_by_id(char_id)
        self.statusBar().showMessage("Personaje enfocado en el panel", 2000)

    def _on_graph_open_character_sheet(self, char_id: str):
        """Abre el editor completo del personaje desde el boton de edicion en el grafo."""
        from ui.character_edit_dialog import CharacterEditDialog
        if not self.project_manager.metadata:
            return
        meta = self.project_manager.metadata
        char = next((c for c in meta.characters if str(c.id) == str(char_id)), None)
        if not char:
            return

        char_rels = [r for r in meta.relations
                     if str(r.char_id_a) == str(char_id)
                     or str(r.char_id_b) == str(char_id)]

        dlg = CharacterEditDialog(
            character=char,
            obras=meta.obras,
            characters=meta.characters,
            relations=char_rels,
            parent=self
        )
        if dlg.exec():
            # Actualizar relaciones del personaje en el metadata
            other_rels = [r for r in meta.relations
                          if str(r.char_id_a) != str(char_id)
                          and str(r.char_id_b) != str(char_id)]
            meta.relations = other_rels + dlg.get_relations()
            self._dirty = True
            self.statusBar().showMessage(f"Personaje '{char.name}' actualizado", 3000)
            # Refrescar el grafo con los datos actualizados
            if self._graph_widget:
                self._graph_widget.build_from_metadata(meta)

    def _on_chapter_requested_from_dock(self, chapter_id: str):
        """Navega al capitulo solicitado desde la lista de apariciones del dock."""
        self._flush_content_to_metadata()
        chapter = self.project_manager.find_chapter(chapter_id)
        if chapter:
            self._load_chapter(chapter)
            self.outline_tree.select_item_by_id(chapter_id)
            self.statusBar().showMessage(f"Navegando a: {chapter.title}", 3000)

    def _detect_character_mentions(self, chapter: Chapter):
        """
        Escanea el texto del capitulo y registra automaticamente los personajes
        cuyo nombre o alias aparezca en el contenido.
        """
        if not self.project_manager.metadata or not chapter.content_file:
            return
        html = self.project_manager.read_chapter_content(chapter.content_file)
        text = BeautifulSoup(html, "lxml").get_text().lower()
        detected = set(chapter.characters_present)
        for char in self.project_manager.metadata.characters:
            terms = [char.name.lower()] + [a.lower() for a in char.aliases]
            if any(term and term in text for term in terms):
                detected.add(char.id)
        chapter.characters_present = list(detected)

    def _refresh_char_dock(self):
        """Actualiza el dock de personajes con los datos actuales del proyecto."""
        if not self.project_manager.metadata:
            return
        meta = self.project_manager.metadata
        self.char_dock.populate(meta.characters, meta.relations, meta.obras)
        active_id = self.char_dock.get_current_char_id()
        if active_id:
            appearances = [
                (cap, obra.title, libro.title)
                for obra in meta.obras
                for libro in obra.libros
                for cap in libro.capitulos
                if active_id in cap.characters_present
            ]
            self.char_dock.update_appearances(appearances)

    def _on_character_selected(self, char_id: str):
        """Muestra las apariciones del personaje seleccionado en el dock."""
        if not self.project_manager.metadata:
            return
        meta = self.project_manager.metadata
        appearances = [
            (cap, obra.title, libro.title)
            for obra in meta.obras
            for libro in obra.libros
            for cap in libro.capitulos
            if char_id in cap.characters_present
        ]
        self.char_dock.update_appearances(appearances)

    def _update_dock_context(self, item_id: str, item_type: str):
        """Actualiza el panel de contexto del dock segun el nodo seleccionado."""
        meta = self.project_manager.metadata
        if not meta:
            return
        char_map = {c.id: c for c in meta.characters}

        if item_type == "universe":
            total_caps = sum(len(l.capitulos) for o in meta.obras for l in o.libros)
            self.char_dock.update_context_for_universe(
                meta.title, meta.characters, total_caps, len(meta.obras)
            )
        elif item_type == "obra":
            obra = self._find_obra(item_id)
            if obra:
                ids, caps = set(), 0
                for lib in obra.libros:
                    caps += len(lib.capitulos)
                    for cap in lib.capitulos:
                        ids.update(cap.characters_present)
                self.char_dock.update_context_for_obra(
                    obra.title, [char_map[c] for c in ids if c in char_map], caps
                )
        elif item_type == "libro":
            libro = self._find_libro(item_id)
            if libro:
                obra = self._find_parent_obra(item_id)
                ids = set()
                for cap in libro.capitulos:
                    ids.update(cap.characters_present)
                self.char_dock.update_context_for_libro(
                    libro.title, obra.title if obra else "N/A",
                    [char_map[c] for c in ids if c in char_map], len(libro.capitulos)
                )
        elif item_type == "chapter":
            chapter = self.project_manager.find_chapter(item_id)
            if chapter:
                obra = self._find_parent_obra(item_id)
                libro = self._find_parent_libro(item_id)
                self.char_dock.update_context_for_chapter(
                    chapter.title,
                    [char_map[c] for c in chapter.characters_present if c in char_map],
                    obra.title if obra else "N/A",
                    libro.title if libro else "N/A"
                )