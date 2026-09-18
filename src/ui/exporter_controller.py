"""
Aura Writer — Exporter Controller Mixin
Logica de exportacion: recoleccion de contenido, construccion de project_data y despacho.
"""
import os
import logging
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox
from ui.exporter_dialog import ExporterDialog
from tools.exporters import AuraExporter
from core.models import Book

log = logging.getLogger(__name__)


class ExporterControllerMixin:
    """Mixin para AuraMainWindow: coordinacion de exportacion de la obra."""

    def open_exporter(self):
        """Abre el dialogo de exportacion y lanza el proceso segun el formato elegido."""
        if not self.project_manager.metadata:
            QMessageBox.warning(self, "Exportar", "No hay un proyecto abierto.")
            return

        self._flush_content_to_metadata()

        # Detectar seleccion actual en el arbol para sugerir titulo
        indexes = self.outline_tree.selectionModel().selectedIndexes()
        selected_id, selected_type = None, None
        suggested_title = self.project_manager.metadata.title
        if indexes:
            item = self.outline_tree._model.itemFromIndex(indexes[0])
            selected_id = item.data(Qt.ItemDataRole.UserRole)
            selected_type = item.data(Qt.ItemDataRole.UserRole + 1)
            suggested_title = item.text()

        dialog = ExporterDialog(self.project_manager.metadata, suggested_title, self)
        if not dialog.exec():
            return

        config = dialog.get_config()
        if not config["output_path"]:
            QMessageBox.warning(self, "Exportar", "Debes elegir una ruta de salida.")
            return

        exporter = AuraExporter(config, self.project_manager.temp_dir)
        target_libros = self._collect_target_libros(selected_id, selected_type)
        project_data = self._build_project_data(target_libros, config)

        if not project_data["chapters"]:
            if self.editor.toPlainText().strip():
                project_data["chapters"].append({
                    "title": config.get("title", "Capitulo 1"),
                    "content": self.editor.toHtml(),
                    "medias": [], "author_notes": [],
                })
            else:
                QMessageBox.warning(self, "Sin Contenido", "No hay contenido para exportar.")
                return

        log.info("Exportando %d capitulo(s)", len(project_data["chapters"]))
        dispatch = {
            0: exporter.export_draft_docx,
            1: exporter.export_pdf_professional,
            2: exporter.export_epub,
        }
        fn = dispatch.get(config["type"])
        if fn:
            success, msg = fn(project_data, config["output_path"])
            if success:
                QMessageBox.information(self, "Exportacion Exitosa", msg)
            else:
                QMessageBox.critical(self, "Error de Exportacion", msg)

    def _collect_target_libros(self, selected_id, selected_type) -> list:
        """Determina que libros exportar segun el nodo seleccionado."""
        target = []
        if selected_type == "obra":
            obra = self._find_obra(selected_id)
            if obra:
                target.extend(obra.libros)
        elif selected_type == "libro":
            libro = self._find_libro(selected_id)
            if libro:
                target.append(libro)
        elif selected_type == "chapter":
            cap = self.project_manager.find_chapter(selected_id)
            if cap:
                target.append(Book(title="", capitulos=[cap]))
        else:
            for obra in self.project_manager.metadata.obras:
                target.extend(obra.libros)
        return target

    def _build_project_data(self, target_libros: list, config: dict) -> dict:
        """Construye el diccionario project_data con contenido intercalado capitulos/media."""
        project_data = {"items": []}
        include_notes = config.get("include_author_notes", False)

        for libro in target_libros:
            for entry_type, obj in self._build_ordered_items(libro):
                if entry_type == "chapter":
                    cap = obj
                    content = self.project_manager.read_chapter_content(cap.content_file)
                    media_items = [
                        {
                            "path": self.project_manager.get_media_asset_path(m.image_asset),
                            "caption": m.caption,
                            "position": m.position,
                        }
                        for m in cap.medias
                    ]
                    notes = [n.content for n in cap.author_notes if n.content] if include_notes else []
                    if content or media_items:
                        project_data["items"].append({
                            "type": "chapter",
                            "title": cap.title,
                            "libro_title": libro.title,
                            "content": content,
                            "medias": media_items,
                            "author_notes": notes,
                        })
                elif entry_type == "media":
                    m = obj
                    asset_path = self.project_manager.get_media_asset_path(m.image_asset)
                    if os.path.exists(asset_path):
                        project_data["items"].append({
                            "type": "full_page_media",
                            "path": asset_path,
                            "caption": m.caption,
                            "title": m.title,
                        })

        project_data["chapters"] = [
            it for it in project_data["items"] if it.get("type") == "chapter"
        ]
        return project_data