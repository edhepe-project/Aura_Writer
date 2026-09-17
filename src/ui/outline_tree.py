from PyQt6.QtWidgets import (QTreeView, QAbstractItemView, QMenu, QInputDialog,
                             QMessageBox)
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt, pyqtSignal
import qtawesome as qta

from core.models import UniverseMetadata


class OutlineTree(QTreeView):
    """
    Árbol de estructura del universo con:
    - Menú contextual completo (añadir CUALQUIER tipo, eliminar, renombrar)
    - Drag & drop para reordenar
    - Edición de nombres directo (doble clic o F2)
    """
    item_selected = pyqtSignal(str, str)              # (id, type)
    node_add_requested = pyqtSignal(str, str, str)     # (parent_id, parent_type, new_type)
    node_delete_requested = pyqtSignal(str, str)       # (id, type)
    node_renamed = pyqtSignal(str, str, str)           # (id, type, new_name)
    node_moved_requested = pyqtSignal(str, str, str, str) # (src_id, src_type, target_id, target_type)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._model = QStandardItemModel()
        self._model.setHorizontalHeaderLabels(["Universo Narrativo"])
        self.setModel(self._model)

        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDropIndicatorShown(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setHeaderHidden(True)
        self.setRootIsDecorated(False)
        self.setAnimated(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        self.clicked.connect(self._on_clicked)

        # Iconos
        self.icons = {}
        try:
            self.icons = {
                "universe":    qta.icon("fa5s.globe",        color="#9b59b6"),
                "obra":        qta.icon("fa5s.book-open",    color="#e67e22"),
                "libro":       qta.icon("fa5s.book",         color="#d4a017"),
                "chapter":     qta.icon("fa5s.bookmark",     color="#27ae60"),
                "media":       qta.icon("fa5s.image",        color="#3498db"),
                "author_note": qta.icon("fa5s.sticky-note",  color="#95a5a6"),
            }
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Población
    # ------------------------------------------------------------------

    def populate_from_metadata(self, meta: UniverseMetadata):
        self._model.blockSignals(True)  # evitar señales falsas de itemChanged
        self._model.clear()
        self._model.setHorizontalHeaderLabels(["Universo Narrativo"])

        root = self._model.invisibleRootItem()
        universe_item = self._make("universe", meta.title, "universe_root")
        root.appendRow(universe_item)

        # Imágenes a nivel universo
        for media in meta.medias:
            universe_item.appendRow(self._make("media", media.title, media.id))

        # Renderizar Obras completas en la jerarquía
        for obra in meta.obras:
            obra_item = self._make("obra", obra.title, obra.id)
            universe_item.appendRow(obra_item)

            # Medias a nivel obra (mapas, portadas de saga)
            for media in obra.medias:
                obra_item.appendRow(self._make("media", media.title, media.id))

            for libro in obra.libros:
                libro_item = self._make("libro", libro.title, libro.id)
                obra_item.appendRow(libro_item)

                # Renderizar hijos del libro en orden (content_order)
                if libro.content_order:
                    cap_map = {c.id: c for c in libro.capitulos}
                    media_map = {m.id: m for m in libro.medias}
                    rendered = set()
                    for entry in libro.content_order:
                        eid = entry.get("id")
                        etype = entry.get("type")
                        if etype == "chapter" and eid in cap_map:
                            cap = cap_map[eid]
                            cap_item = self._make("chapter", cap.title, cap.id)
                            libro_item.appendRow(cap_item)
                            for media in cap.medias:
                                cap_item.appendRow(self._make("media", media.title, media.id))
                            rendered.add(eid)
                        elif etype == "media" and eid in media_map:
                            m = media_map[eid]
                            libro_item.appendRow(self._make("media", m.title, m.id))
                            rendered.add(eid)
                    # Agregar cualquier ítem no referenciado en content_order
                    for cap in libro.capitulos:
                        if cap.id not in rendered:
                            cap_item = self._make("chapter", cap.title, cap.id)
                            libro_item.appendRow(cap_item)
                            for media in cap.medias:
                                cap_item.appendRow(self._make("media", media.title, media.id))
                    for m in libro.medias:
                        if m.id not in rendered:
                            libro_item.appendRow(self._make("media", m.title, m.id))
                else:
                    # Sin content_order: capítulos primero, luego medias del libro
                    for cap in libro.capitulos:
                        cap_item = self._make("chapter", cap.title, cap.id)
                        libro_item.appendRow(cap_item)
                        for media in cap.medias:
                            cap_item.appendRow(self._make("media", media.title, media.id))
                    for m in libro.medias:
                        libro_item.appendRow(self._make("media", m.title, m.id))

        self._model.blockSignals(False)
        self.expandAll()

    def select_node_by_id(self, target_id: str) -> bool:
        """Busca y selecciona visualmente el nodo con el ID dado en el árbol."""
        def _search_item(parent_item):
            for row in range(parent_item.rowCount()):
                child = parent_item.child(row)
                if child:
                    if child.data(Qt.ItemDataRole.UserRole) == target_id:
                        idx = child.index()
                        self.setCurrentIndex(idx)
                        self.selectionModel().select(idx, self.selectionModel().SelectionFlag.ClearAndSelect)
                        self.item_selected.emit(target_id, child.data(Qt.ItemDataRole.UserRole + 1))
                        return True
                    if _search_item(child):
                        return True
            return False

        root = self._model.invisibleRootItem()
        return _search_item(root)

    def select_first_chapter(self) -> bool:
        """Busca y selecciona el primer capítulo del árbol narrativo."""
        def _search_first_chap(parent_item):
            for row in range(parent_item.rowCount()):
                child = parent_item.child(row)
                if child:
                    node_type = child.data(Qt.ItemDataRole.UserRole + 1)
                    if node_type == "chapter":
                        node_id = child.data(Qt.ItemDataRole.UserRole)
                        idx = child.index()
                        self.setCurrentIndex(idx)
                        self.selectionModel().select(idx, self.selectionModel().SelectionFlag.ClearAndSelect)
                        self.item_selected.emit(node_id, "chapter")
                        return True
                    if _search_first_chap(child):
                        return True
            return False

        root = self._model.invisibleRootItem()
        return _search_first_chap(root)

    def clear(self):
        self._model.clear()

    # ------------------------------------------------------------------
    # Menú contextual completo
    # ------------------------------------------------------------------

    def _show_context_menu(self, position):
        index = self.indexAt(position)
        if not index.isValid():
            return

        item = self._model.itemFromIndex(index)
        item_id = item.data(Qt.ItemDataRole.UserRole)
        item_type = item.data(Qt.ItemDataRole.UserRole + 1)

        menu = QMenu(self)

        # ── Sección: Añadir (opciones contextuales según el tipo de nodo) ───────
        add_menu = menu.addMenu("➕ Añadir…")

        if item_type == "universe":
            add_menu.addAction("🏛️ Nueva Obra / Saga", lambda: self.node_add_requested.emit(
                item_id, item_type, "obra"))

        if item_type in ("universe", "obra"):
            add_menu.addAction("📘 Nuevo Libro", lambda: self.node_add_requested.emit(
                item_id, item_type, "libro"))

        if item_type in ("universe", "obra", "libro", "chapter"):
            add_menu.addAction("📑 Nuevo Capítulo", lambda: self.node_add_requested.emit(
                item_id, item_type, "chapter"))

        add_menu.addSeparator()
        add_menu.addAction("🖼️ Media (Imagen / Mapa)", lambda: self.node_add_requested.emit(
            item_id, item_type, "media"))

        menu.addSeparator()

        # ── Renombrar ────────────────────────────────────
        menu.addAction("✏️ Renombrar", lambda: self._start_rename(index))

        # ── Eliminar (no se puede eliminar el nodo universo raíz) ──────────
        if item_type != "universe":
            menu.addAction("🗑️ Eliminar", lambda: self._request_delete(item_id, item_type, item.text()))

        menu.exec(self.viewport().mapToGlobal(position))

    # ------------------------------------------------------------------
    # Renombrar
    # ------------------------------------------------------------------

    def _start_rename(self, index):
        """Abre un diálogo amplio y legible para renombrar cualquier elemento."""
        if not index.isValid():
            return
        item = self._model.itemFromIndex(index)
        if not item:
            return

        item_id = item.data(Qt.ItemDataRole.UserRole)
        item_type = item.data(Qt.ItemDataRole.UserRole + 1)
        current_name = item.text()

        type_labels = {
            "universe": "del Universo",
            "obra": "de la Obra",
            "libro": "del Libro",
            "chapter": "del Capítulo",
            "media": "del Archivo Multimedia",
            "author_note": "de la Nota",
        }
        lbl = type_labels.get(item_type, "del elemento")

        new_name, ok = QInputDialog.getText(
            self, "Renombrar",
            f"Nuevo nombre {lbl}:",
            text=current_name
        )
        if ok and new_name.strip() and new_name.strip() != current_name:
            self.node_renamed.emit(item_id, item_type, new_name.strip())

    def keyPressEvent(self, event):
        """Permite renombrar con F2 y eliminar con Supr/Delete."""
        if event.key() == Qt.Key.Key_F2:
            indexes = self.selectedIndexes()
            if indexes:
                self._start_rename(indexes[0])
                return
        elif event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            indexes = self.selectedIndexes()
            if indexes:
                item = self._model.itemFromIndex(indexes[0])
                if item:
                    item_id = item.data(Qt.ItemDataRole.UserRole)
                    item_type = item.data(Qt.ItemDataRole.UserRole + 1)
                    if item_type != "universe":
                        self._request_delete(item_id, item_type, item.text())
                        return
        super().keyPressEvent(event)

    # ------------------------------------------------------------------
    # Eliminar
    # ------------------------------------------------------------------

    def _request_delete(self, item_id: str, item_type: str, name: str):
        labels = {
            "obra": "la Obra", "libro": "el Libro", "chapter": "el Capítulo",
            "media": "la Media", "author_note": "la Nota",
        }
        label = labels.get(item_type, "el elemento")

        reply = QMessageBox.question(
            self, "Eliminar",
            f"¿Seguro que deseas eliminar {label} '{name}'?\n\n"
            f"Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.node_delete_requested.emit(item_id, item_type)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _make(self, item_type: str, text: str, item_id: str) -> QStandardItem:
        item = QStandardItem(text)
        item.setData(item_id,   Qt.ItemDataRole.UserRole)
        item.setData(item_type, Qt.ItemDataRole.UserRole + 1)
        if item_type in self.icons:
            item.setIcon(self.icons[item_type])
        # NO ItemIsEditable por defecto — solo se activa al renombrar
        item.setFlags(
            Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsDragEnabled
            | Qt.ItemFlag.ItemIsDropEnabled
        )
        return item

    def select_item_by_id(self, target_id: str):
        """Busca un ítem por ID en todo el árbol, lo selecciona y hace scroll."""
        match = self._find_item_recursive(self._model.invisibleRootItem(), target_id)
        if match:
            index = match.index()
            self.setCurrentIndex(index)
            self.scrollTo(index)

    def update_item_text(self, target_id: str, new_text: str):
        """Actualiza el texto visible de un ítem por ID sin necesidad de reconstruir todo el árbol."""
        match = self._find_item_recursive(self._model.invisibleRootItem(), target_id)
        if match:
            match.setText(new_text)

    def _find_item_recursive(self, parent: QStandardItem, target_id: str):
        """Busca recursivamente un QStandardItem cuyo UserRole == target_id."""
        for row in range(parent.rowCount()):
            child = parent.child(row)
            if child is None:
                continue
            if child.data(Qt.ItemDataRole.UserRole) == target_id:
                return child
            found = self._find_item_recursive(child, target_id)
            if found:
                return found
        return None

    def _on_clicked(self, index):
        item = self._model.itemFromIndex(index)
        if item is None:
            return
        item_id   = item.data(Qt.ItemDataRole.UserRole)
        item_type = item.data(Qt.ItemDataRole.UserRole + 1)
        self.item_selected.emit(item_id, item_type)

    # ------------------------------------------------------------------
    # Drag and Drop Override
    # ------------------------------------------------------------------

    def dropEvent(self, e):
        """Intercepta el soltado para manejar el reordenamiento con posición exacta."""
        event = e
        drop_pos = event.position().toPoint()
        drop_index = self.indexAt(drop_pos)
        drop_indicator = self.dropIndicatorPosition()  # Above / Below / OnItem / OnViewport

        selected = self.selectedIndexes()
        if not selected:
            event.ignore()
            return

        source_index = selected[0]
        source_item = self._model.itemFromIndex(source_index)
        if not source_item:
            event.ignore()
            return

        source_id   = source_item.data(Qt.ItemDataRole.UserRole)
        source_type = source_item.data(Qt.ItemDataRole.UserRole + 1)

        target_id   = "universe_root"
        target_type = "universe"
        # "above" = insertar antes del target; "below" = insertar después; "on" = dentro
        position    = "on"

        if drop_index.isValid():
            target_item = self._model.itemFromIndex(drop_index)
            if target_item:
                target_id   = target_item.data(Qt.ItemDataRole.UserRole)
                target_type = target_item.data(Qt.ItemDataRole.UserRole + 1)

            ind = drop_indicator
            if ind == QAbstractItemView.DropIndicatorPosition.AboveItem:
                position = "above"
            elif ind == QAbstractItemView.DropIndicatorPosition.BelowItem:
                position = "below"
            else:
                position = "on"

        if source_id and target_id and source_id != target_id:
            # Emitimos source_id, source_type, target_id, target_type, position
            # (5 parámetros; el signal acepta 4 → añadimos position como parte de target_type)
            self.node_moved_requested.emit(
                source_id,
                source_type,
                target_id,
                f"{target_type}:{position}",  # ← codificamos posición aquí
            )

        # Ignoramos el comportamiento por defecto de QTreeView (que destruye metadatos)
        event.ignore()

