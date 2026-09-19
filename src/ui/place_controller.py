"""
place_controller.py — Mixin para AuraMainWindow: gestión integral de Lugares & Escenarios y sincronización.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

from core.models import Place, TrashedItem
from ui.place_dialog import PlaceEditDialog

if TYPE_CHECKING:
    from ui.main_window import AuraMainWindow


class PlaceControllerMixin:
    """Mixin para AuraMainWindow que maneja eventos del PlaceDock y diálogos de Lugares."""

    def _on_place_added(self: "AuraMainWindow", place: Place):
        """Sincroniza un nuevo lugar creado en el PlaceDock con el metadata del proyecto."""
        if not self.project_manager.metadata:
            return
        meta = self.project_manager.metadata
        if not hasattr(meta, "places") or meta.places is None:
            meta.places = []
        if not any(p.id == place.id for p in meta.places):
            meta.places.append(place)
            self.statusBar().showMessage(f"Lugar '{place.name}' creado", 3000)
        self._dirty = True

    def _on_place_updated(self: "AuraMainWindow", place: Place):
        """Actualiza un lugar modificado en el metadata del proyecto."""
        if not self.project_manager.metadata:
            return
        meta = self.project_manager.metadata
        if not hasattr(meta, "places") or meta.places is None:
            meta.places = []
        idx = next((i for i, p in enumerate(meta.places) if p.id == place.id), None)
        if idx is not None:
            meta.places[idx] = place
            self.statusBar().showMessage(f"Lugar '{place.name}' actualizado", 3000)
        else:
            meta.places.append(place)
        self._dirty = True

    def _on_place_deleted(self: "AuraMainWindow", place_id: str):
        """Mueve a la papelera un lugar eliminado desde el PlaceDock."""
        if not self.project_manager.metadata:
            return
        meta = self.project_manager.metadata
        if not hasattr(meta, "places") or meta.places is None:
            meta.places = []

        place_obj = next((p for p in meta.places if p.id == place_id), None)
        if place_obj:
            trashed = TrashedItem(
                original_id=place_id,
                item_type="place",
                title=place_obj.name,
                data=place_obj.model_dump(mode="json")
            )
            if not hasattr(meta, "trash") or meta.trash is None:
                meta.trash = []
            meta.trash.append(trashed)

        meta.places = [p for p in meta.places if p.id != place_id]
        self._dirty = True
        self.statusBar().showMessage("Lugar movido a la papelera", 3000)

    def _on_place_selected(self: "AuraMainWindow", place_id: str):
        """Responde a la selección de un lugar en el PlaceDock."""
        pass

    def _refresh_place_dock(self: "AuraMainWindow"):
        """Recarga la lista de lugares en el PlaceDock y las apariciones en capítulos."""
        if not hasattr(self, "place_dock") or self.place_dock is None:
            return
        if not self.project_manager.metadata:
            self.place_dock.populate([])
            self.place_dock.update_chapters_data([])
            return
        self.place_dock.set_project_manager(self.project_manager)
        meta = self.project_manager.metadata
        self.place_dock.populate(getattr(meta, "places", []))
        chapters_data = [
            (cap, obra.title, libro.title)
            for obra in meta.obras
            for libro in obra.libros
            for cap in libro.capitulos
        ]
        self.place_dock.update_chapters_data(chapters_data)

    def open_place_edit_dialog(self: "AuraMainWindow", place_id: str | None = None):
        """Abre la ventana de edición/creación de un lugar."""
        if not self.project_manager.metadata:
            return
        meta = self.project_manager.metadata
        places = getattr(meta, "places", [])
        place = next((p for p in places if p.id == place_id), None) if place_id else None

        dlg = PlaceEditDialog(
            place=place,
            all_places=places,
            project_manager=self.project_manager,
            parent=self
        )
        dlg.place_saved.connect(self._on_place_dialog_saved_from_menu)
        dlg.exec()

    def _on_place_dialog_saved_from_menu(self: "AuraMainWindow", saved_place: Place):
        """Maneja el guardado de un lugar cuando el diálogo se abrió de forma externa."""
        if not self.project_manager.metadata:
            return
        meta = self.project_manager.metadata
        if not hasattr(meta, "places") or meta.places is None:
            meta.places = []
        idx = next((i for i, p in enumerate(meta.places) if p.id == saved_place.id), None)
        if idx is not None:
            meta.places[idx] = saved_place
        else:
            meta.places.append(saved_place)
        self._dirty = True
        self._refresh_place_dock()
        if hasattr(self, "place_dock") and self.place_dock:
            self.place_dock.select_place_by_id(saved_place.id)

    def open_timeline_dialog(self: "AuraMainWindow"):
        """Abre la ventana interactiva de Cronología / Timeline del Universo."""
        if not self.project_manager.metadata:
            return
        from ui.timeline import TimelineDialog
        dlg = TimelineDialog(self.project_manager, parent=self)
        dlg.navigate_to_chapter.connect(self._on_chapter_requested_from_dock)
        dlg.exec()

    def open_place_graph_dialog(self: "AuraMainWindow"):
        """Abre el Atlas Literario (Grafo de Lugares y Conexiones)."""
        if not self.project_manager.metadata:
            return
        from ui.place_graph import PlaceGraphDialog
        dlg = PlaceGraphDialog(self.project_manager, parent=self)
        dlg.place_selected_for_focus.connect(self._on_graph_place_focused)
        dlg.exec()

    def _on_graph_place_focused(self: "AuraMainWindow", place_id: str):
        """Enfoca y selecciona el lugar en el panel inspector PlaceDock."""
        self._switch_inspector_tab("places")
        if hasattr(self, "place_dock") and self.place_dock:
            self.place_dock.select_place_by_id(place_id)

    def open_vocabulary_dialog(self: "AuraMainWindow"):
        """Abre el gestor de Vocabulario y Conlang del Universo."""
        if not self.project_manager.metadata:
            return
        from ui.vocabulary_dialog import VocabularyDialog
        dlg = VocabularyDialog(self.project_manager, parent=self)
        if dlg.exec():
            self._dirty = True



