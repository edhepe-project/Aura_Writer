"""
Aura Writer — Diálogo de Papelera de Reciclaje.

Permite ver los elementos eliminados (Obras, Libros, Capítulos, Notas, Medias),
restaurarlos a la estructura del proyecto o eliminarlos definitivamente.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QListWidget, QListWidgetItem, QPushButton,
                             QMessageBox, QTextEdit, QSplitter, QWidget)
from PyQt6.QtCore import Qt, pyqtSignal

from core.models import UniverseMetadata, TrashedItem, Obra, Book, Chapter, MediaNode, AuthorNote, Character


class TrashDialog(QDialog):
    """Diálogo de administración de la papelera de reciclaje."""
    item_restored = pyqtSignal(str, str)   # (item_id, item_type)

    TYPE_LABELS = {
        "obra": ("📚 Obra", "#e67e22"),
        "libro": ("📖 Libro", "#d4a017"),
        "chapter": ("📑 Capítulo", "#27ae60"),
        "media": ("🖼️ Media", "#3498db"),
        "author_note": ("📝 Nota de Autor", "#95a5a6"),
        "character": ("👤 Personaje", "#9b59b6"),
    }

    def __init__(self, project_manager, parent=None):
        super().__init__(parent)
        self.pm = project_manager
        self.meta: UniverseMetadata = project_manager.metadata

        self.setWindowTitle("🗑️ Papelera de Reciclaje — Aura Writer")
        self.resize(750, 480)
        self.setMinimumSize(600, 380)

        self._setup_ui()
        self._populate_list()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # ── Encabezado ───────────────────────────────────────────────
        header_layout = QHBoxLayout()
        title_lbl = QLabel("<b style='font-size:15px;'>🗑️ Papelera de Reciclaje</b>")
        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet("color: #8e8e93; font-size: 12px;")
        header_layout.addWidget(title_lbl)
        header_layout.addSpacing(10)
        header_layout.addWidget(self.count_lbl)
        header_layout.addStretch()
        root.addLayout(header_layout)

        # ── Splitter principal: Lista | Vista previa ──────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Panel izquierdo: lista de elementos
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        self.items_list = QListWidget()
        self.items_list.itemSelectionChanged.connect(self._on_selection_changed)
        left_layout.addWidget(self.items_list)
        splitter.addWidget(left_widget)

        # Panel derecho: vista previa y detalles
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)

        self.preview_title = QLabel("<b>Detalles del elemento</b>")
        self.preview_info = QLabel("Selecciona un elemento de la lista para ver sus detalles.")
        self.preview_info.setWordWrap(True)
        self.preview_info.setStyleSheet("color: #8e8e93; font-size: 12px;")

        self.preview_content = QTextEdit()
        self.preview_content.setReadOnly(True)
        self.preview_content.setPlaceholderText("Vista previa de contenido…")

        right_layout.addWidget(self.preview_title)
        right_layout.addWidget(self.preview_info)
        right_layout.addWidget(self.preview_content)
        splitter.addWidget(right_widget)

        splitter.setSizes([380, 320])
        root.addWidget(splitter, 1)

        # ── Barra de botones de acción ───────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_empty = QPushButton("🧹 Vaciar Papelera")
        self.btn_empty.setStyleSheet("color: #ff453a; font-weight: bold;")
        self.btn_empty.clicked.connect(self._empty_trash)
        btn_layout.addWidget(self.btn_empty)

        btn_layout.addStretch()

        self.btn_delete_perm = QPushButton("🗑️ Eliminar Definitivamente")
        self.btn_delete_perm.clicked.connect(self._delete_selected_permanently)
        btn_layout.addWidget(self.btn_delete_perm)

        self.btn_restore = QPushButton("♻️ Restaurar Elemento")
        self.btn_restore.setStyleSheet("background-color: #30d158; color: white; font-weight: bold; padding: 6px 16px;")
        self.btn_restore.clicked.connect(self._restore_selected)
        btn_layout.addWidget(self.btn_restore)

        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)

        root.addLayout(btn_layout)

    def _populate_list(self):
        """Rellena la lista con los elementos actualmente en la papelera."""
        self.items_list.clear()
        trash = getattr(self.meta, "trash", [])
        self.count_lbl.setText(f"({len(trash)} elemento{'s' if len(trash) != 1 else ''})")

        for item in reversed(trash):
            type_label, _ = self.TYPE_LABELS.get(item.item_type, (item.item_type, "#95a5a6"))
            del_time = item.deleted_at.strftime("%d/%m/%Y %H:%M") if hasattr(item.deleted_at, 'strftime') else str(item.deleted_at)[:16]
            
            list_item = QListWidgetItem(f"{type_label}: {item.title}\n   📅 Eliminado: {del_time}")
            list_item.setData(Qt.ItemDataRole.UserRole, item.id)
            self.items_list.addItem(list_item)

        has_items = len(trash) > 0
        self.btn_empty.setEnabled(has_items)
        self.btn_restore.setEnabled(False)
        self.btn_delete_perm.setEnabled(False)

        if not has_items:
            self.preview_title.setText("<b>Papelera vacía</b>")
            self.preview_info.setText("No hay elementos eliminados en este proyecto.")
            self.preview_content.clear()

    def _get_selected_trashed_item(self) -> TrashedItem | None:
        row = self.items_list.currentRow()
        if row < 0:
            return None
        list_item = self.items_list.item(row)
        if not list_item:
            return None
        item_id = list_item.data(Qt.ItemDataRole.UserRole)
        for t in self.meta.trash:
            if t.id == item_id:
                return t
        return None

    def _on_selection_changed(self):
        item = self._get_selected_trashed_item()
        if not item:
            self.btn_restore.setEnabled(False)
            self.btn_delete_perm.setEnabled(False)
            return

        self.btn_restore.setEnabled(True)
        self.btn_delete_perm.setEnabled(True)

        type_label, _ = self.TYPE_LABELS.get(item.item_type, (item.item_type, "#95a5a6"))
        self.preview_title.setText(f"<b>{type_label}: {item.title}</b>")
        
        del_time = item.deleted_at.strftime("%d/%m/%Y %H:%M:%S") if hasattr(item.deleted_at, 'strftime') else str(item.deleted_at)
        self.preview_info.setText(f"ID original: {item.original_id}\nEliminado el: {del_time}")

        # Intentar mostrar vista previa según el tipo
        self.preview_content.clear()
        data = item.data or {}

        if item.item_type == "chapter":
            cfile = data.get("content_file", "")
            if cfile:
                content = self.pm.read_chapter_content(cfile)
                self.preview_content.setHtml(content)
            else:
                self.preview_content.setPlainText(f"Capítulo '{item.title}' (sin archivo de contenido).")
        elif item.item_type == "author_note":
            self.preview_content.setPlainText(data.get("content", ""))
        elif item.item_type == "character":
            desc = data.get("description", "")
            notes = data.get("notes", "")
            self.preview_content.setPlainText(f"Descripción:\n{desc}\n\nNotas:\n{notes}")
        elif item.item_type == "libro":
            caps = data.get("capitulos", [])
            cap_titles = [c.get("title", "Sin título") for c in caps]
            self.preview_content.setPlainText(
                f"Libro con {len(caps)} capítulo(s):\n" + "\n".join(f" - {t}" for t in cap_titles)
            )
        elif item.item_type == "obra":
            libros = data.get("libros", [])
            self.preview_content.setPlainText(
                f"Obra con {len(libros)} libro(s)."
            )
        else:
            self.preview_content.setPlainText(f"Elemento: {item.title}")

    def _restore_selected(self):
        """Restaura el elemento seleccionado a la estructura viva del proyecto."""
        item = self._get_selected_trashed_item()
        if not item:
            return

        data = item.data or {}
        itype = item.item_type

        try:
            if itype == "obra":
                obj = Obra.model_validate(data)
                self.meta.obras.append(obj)
            elif itype == "libro":
                obj = Book.model_validate(data)
                if self.meta.obras:
                    self.meta.obras[0].libros.append(obj)
                else:
                    nueva_obra = Obra(title=self.meta.title, libros=[obj])
                    self.meta.obras.append(nueva_obra)
            elif itype == "chapter":
                obj = Chapter.model_validate(data)
                # Intentar ubicar en el primer libro disponible
                if self.meta.obras and self.meta.obras[0].libros:
                    target_libro = self.meta.obras[0].libros[0]
                    target_libro.capitulos.append(obj)
                    if target_libro.content_order:
                        target_libro.content_order.append({"type": "chapter", "id": obj.id})
                else:
                    target_libro = Book(title="Libro I", capitulos=[obj])
                    nueva_obra = Obra(title=self.meta.title, libros=[target_libro])
                    self.meta.obras.append(nueva_obra)
            elif itype == "media":
                obj = MediaNode.model_validate(data)
                self.meta.medias.append(obj)
            elif itype == "author_note":
                obj = AuthorNote.model_validate(data)
                self.meta.author_notes.append(obj)
            elif itype == "character":
                obj = Character.model_validate(data)
                self.meta.characters.append(obj)

            # Quitar de la papelera
            self.meta.trash = [t for t in self.meta.trash if t.id != item.id]
            self.pm.save_project()

            self._populate_list()
            self.item_restored.emit(item.original_id, itype)
            QMessageBox.information(
                self, "Restaurado",
                f"✅ '{item.title}' ha sido restaurado con éxito a tu proyecto."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error al Restaurar", f"No se pudo restaurar el elemento: {e}")

    def _delete_selected_permanently(self):
        """Elimina definitivamente el elemento de la papelera."""
        item = self._get_selected_trashed_item()
        if not item:
            return

        reply = QMessageBox.question(
            self, "Eliminar Definitivamente",
            f"¿Estás seguro de que deseas eliminar definitivamente '{item.title}'?\n\n"
            "Esta acción NO se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.meta.trash = [t for t in self.meta.trash if t.id != item.id]
            self.pm.save_project()
            self._populate_list()

    def _empty_trash(self):
        """Vacía todos los elementos de la papelera."""
        if not self.meta.trash:
            return

        reply = QMessageBox.question(
            self, "Vaciar Papelera",
            f"¿Estás seguro de que deseas vaciar toda la papelera ({len(self.meta.trash)} elementos)?\n\n"
            "Todos los elementos eliminados se borrarán permanentemente.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.meta.trash = []
            self.pm.save_project()
            self._populate_list()
            QMessageBox.information(self, "Papelera vacía", "La papelera ha sido vaciada por completo.")
