"""
Aura Writer — Exporter Controller Mixin
Logica de exportacion: recoleccion de contenido, construccion de project_data y despacho.

MEJORA-2: Lee el alcance de exportación del propio diálogo (scope_type / scope_id)
           en lugar de inferirlo del nodo seleccionado en el árbol.
MEJORA-4: Ejecuta la exportación en un QThread worker con QProgressDialog para no
           bloquear la interfaz durante operaciones largas.
"""
import os
import logging
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QMessageBox, QProgressDialog
from ui.exporter_dialog import ExporterDialog
from tools.exporters import AuraExporter
from core.models import Book

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Worker thread — evita bloquear la UI durante la exportación (MEJORA-4)
# ---------------------------------------------------------------------------

class _ExportWorker(QThread):
    """Ejecuta una exportación en segundo plano y emite señales de resultado."""
    finished = pyqtSignal(bool, str)

    def __init__(self, fn, project_data: dict, output_path: str, parent=None):
        super().__init__(parent)
        self._fn = fn
        self._project_data = project_data
        self._output_path = output_path

    def run(self):
        try:
            success, msg = self._fn(self._project_data, self._output_path)
            self.finished.emit(success, msg)
        except Exception as exc:
            self.finished.emit(False, f"Error inesperado durante la exportación:\n{exc}")


# ---------------------------------------------------------------------------
# Mixin
# ---------------------------------------------------------------------------

class ExporterControllerMixin:
    """Mixin para AuraMainWindow: coordinacion de exportacion de la obra."""

    def open_exporter(self):
        """Abre el dialogo de exportacion y lanza el proceso segun el formato elegido."""
        if not self.project_manager.metadata:
            QMessageBox.warning(self, "Exportar", "No hay un proyecto abierto.")
            return

        self._flush_content_to_metadata()

        # Pasar el capítulo activo (si lo hay) para preseleccionarlo en el combo
        current_chapter = getattr(self, "_current_chapter", None)

        dialog = ExporterDialog(
            self.project_manager.metadata,
            current_chapter=current_chapter,
            parent=self,
        )
        if not dialog.exec():
            return

        config = dialog.get_config()
        if not config["output_path"]:
            QMessageBox.warning(self, "Exportar", "Debes elegir una ruta de salida.")
            return

        # Resolver alcance desde el diálogo (MEJORA-2)
        target_libros = self._collect_target_libros_from_config(config)

        exporter = AuraExporter(config, self.project_manager.temp_dir)
        project_data = self._build_project_data(target_libros, config)

        if not project_data["chapters"]:
            if self.editor.toPlainText().strip():
                project_data["chapters"].append({
                    "title": config.get("title", "Capítulo 1"),
                    "content": self.editor.toHtml(),
                    "medias": [], "author_notes": [],
                })
                project_data["items"] = project_data["chapters"][:]
            else:
                QMessageBox.warning(self, "Sin Contenido", "No hay contenido para exportar.")
                return

        log.info("Exportando %d capítulo(s)", len(project_data["chapters"]))

        dispatch = {
            0: exporter.export_draft_docx,
            1: exporter.export_pdf_professional,
            2: exporter.export_epub,
        }
        fn = dispatch.get(config["type"])
        if not fn:
            return

        # --- Barra de progreso + hilo worker (MEJORA-4) ---
        self._run_export_with_progress(fn, project_data, config["output_path"])

    # -----------------------------------------------------------------------
    # Scope resolution (MEJORA-2)
    # -----------------------------------------------------------------------

    def _collect_target_libros_from_config(self, config: dict) -> list:
        """Resuelve la lista de libros a exportar según scope_type / scope_id del diálogo."""
        scope_type = config.get("scope_type", "all")
        scope_id = config.get("scope_id")
        target = []

        if scope_type == "obra":
            obra = self._find_obra(scope_id)
            if obra:
                target.extend(obra.libros)
        elif scope_type == "libro":
            libro = self._find_libro(scope_id)
            if libro:
                target.append(libro)
        elif scope_type == "chapter":
            cap = self.project_manager.find_chapter(scope_id)
            if cap:
                target.append(Book(title="", capitulos=[cap]))
        else:
            # "all" — todo el universo
            for obra in self.project_manager.metadata.obras:
                target.extend(obra.libros)

        return target

    # Mantener compatibilidad con llamadas antiguas si las hubiera
    def _collect_target_libros(self, selected_id, selected_type) -> list:
        """Deprecated: usar _collect_target_libros_from_config."""
        config = {"scope_type": selected_type or "all", "scope_id": selected_id}
        return self._collect_target_libros_from_config(config)

    # -----------------------------------------------------------------------
    # Progress worker (MEJORA-4)
    # -----------------------------------------------------------------------

    def _run_export_with_progress(self, fn, project_data: dict, output_path: str):
        """Lanza la exportación en un hilo y muestra un QProgressDialog mientras dura."""
        num_chapters = len(project_data.get("chapters", []))
        progress = QProgressDialog(
            f"Exportando {num_chapters} capítulo(s)…\nEspera un momento.",
            "Cancelar",
            0, 0,   # min=max=0 → barra indeterminada (pulsante)
            self,
        )
        progress.setWindowTitle("Exportando…")
        progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.show()

        self._export_worker = _ExportWorker(fn, project_data, output_path, parent=self)

        def _on_finished(success: bool, msg: str):
            progress.close()
            if progress.wasCanceled():
                return
            if success:
                QMessageBox.information(self, "Exportación Exitosa", msg)
            else:
                QMessageBox.critical(self, "Error de Exportación", msg)

        def _on_canceled():
            # No hay forma de cancelar ReportLab/ebooklib a mitad de ejecución,
            # pero cerramos la barra y dejamos terminar el hilo silenciosamente.
            pass

        self._export_worker.finished.connect(_on_finished)
        progress.canceled.connect(_on_canceled)
        self._export_worker.start()

    # -----------------------------------------------------------------------
    # Project data builder
    # -----------------------------------------------------------------------

    def _build_project_data(self, target_libros: list, config: dict) -> dict:
        """Construye el diccionario project_data con contenido intercalado capítulos/media."""
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

        # Vista "chapters" como subconjunto para compatibilidad con consumidores legacy
        project_data["chapters"] = [
            it for it in project_data["items"] if it.get("type") == "chapter"
        ]

        # Aura Protect — Huella forense Zero-Width y firma criptográfica SHA-256
        if config.get("aura_protect", True):
            try:
                from tools.protection.aura_protect import (
                    compute_manuscript_sha256,
                    create_protection_signature,
                    inject_zero_width_watermark,
                )
                author = config.get("author", "")
                title = config.get("title", "")
                sha_hash = compute_manuscript_sha256(project_data, author, title)
                sig = create_protection_signature(author, title, sha_hash)

                project_data["protection_signature"] = sig
                project_data["sha256_hash"] = sha_hash

                for item in project_data["items"]:
                    if item.get("type") == "chapter" and item.get("content"):
                        item["content"] = inject_zero_width_watermark(item["content"], sig)
            except Exception as err:
                log.warning("No se pudo aplicar la protección Aura Protect: %s", err)

        return project_data