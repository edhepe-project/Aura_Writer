from PyQt6.QtWidgets import QTextEdit, QMessageBox, QMenu, QInputDialog, QApplication
from PyQt6.QtGui import (QTextCharFormat, QFont, QTextCursor, QImage,
                         QTextImageFormat, QAction, QTextBlock)
from PyQt6.QtCore import Qt, QUrl, QMimeData
import os
import uuid
import qtawesome as qta
from core.theme_manager import ThemeManager


class AuraEditor(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setPlaceholderText("Tu historia comienza aquí…")

        # Fuente serif para escritores
        font = QFont("Georgia", 12)
        self.setFont(font)

        # Margen de página nativo en el documento (cero overhead en repintado)
        self.document().setDocumentMargin(35)


        # Cache de imágenes para evitar destrucción por GC
        self._image_cache: list[QImage] = []

        # Menú contextual extendido
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    # ------------------------------------------------------------------
    # Formato de texto
    # ------------------------------------------------------------------

    def set_font_size(self, size):
        self.setFontPointSize(size)

    def set_bold(self):
        """Alterna negrita en el texto seleccionado o en el punto de inserción."""
        fmt = QTextCharFormat()
        current_weight = self.currentCharFormat().fontWeight()
        is_bold = (current_weight >= 600 or self.fontWeight() >= 600)
        fmt.setFontWeight(QFont.Weight.Normal if is_bold else QFont.Weight.Bold)
        self.mergeCurrentCharFormat(fmt)
        self.setFocus()

    def set_italic(self):
        """Alterna cursiva en el texto seleccionado o en el punto de inserción."""
        fmt = QTextCharFormat()
        is_italic = self.currentCharFormat().fontItalic() or self.fontItalic()
        fmt.setFontItalic(not is_italic)
        self.mergeCurrentCharFormat(fmt)
        self.setFocus()

    def set_underline(self):
        """Alterna subrayado en el texto seleccionado o en el punto de inserción."""
        fmt = QTextCharFormat()
        is_underline = self.currentCharFormat().fontUnderline() or self.fontUnderline()
        fmt.setFontUnderline(not is_underline)
        self.mergeCurrentCharFormat(fmt)
        self.setFocus()

    def set_strikethrough(self):
        """Alterna tachado en el texto seleccionado o en el punto de inserción."""
        fmt = QTextCharFormat()
        is_strike = self.currentCharFormat().fontStrikeOut()
        fmt.setFontStrikeOut(not is_strike)
        self.mergeCurrentCharFormat(fmt)
        self.setFocus()

    def clear_formatting(self):
        """Restablece el texto seleccionado o cursor al formato editorial estándar (Georgia 12pt Normal)."""
        fmt = QTextCharFormat()
        fmt.setFontFamily("Georgia")
        fmt.setFontPointSize(12)
        fmt.setFontWeight(QFont.Weight.Normal)
        fmt.setFontItalic(False)
        fmt.setFontUnderline(False)
        fmt.setFontStrikeOut(False)
        cursor = self.textCursor()
        if cursor.hasSelection():
            cursor.setCharFormat(fmt)
        else:
            self.setCurrentCharFormat(fmt)
        self.setFocus()

    # ------------------------------------------------------------------
    # Alineaciones
    # ------------------------------------------------------------------

    def align_left(self):
        self.setAlignment(Qt.AlignmentFlag.AlignLeft)

    def align_center(self):
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def align_right(self):
        self.setAlignment(Qt.AlignmentFlag.AlignRight)

    def align_justify(self):
        self.setAlignment(Qt.AlignmentFlag.AlignJustify)

    # ------------------------------------------------------------------
    # Inserciones estructurales
    # ------------------------------------------------------------------

    def insert_scene_separator(self):
        cursor = self.textCursor()
        cursor.insertBlock()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Weight.Bold)
        cursor.insertText("* * *", fmt)
        cursor.insertBlock()
        self.setAlignment(Qt.AlignmentFlag.AlignLeft)

    def insert_page_break(self):
        """Inserta un salto de página para exportación PDF/EPUB."""
        cursor = self.textCursor()
        cursor.insertBlock()
        cursor.insertHtml(
            '<p style="page-break-after:always; text-align:center; color:#8e8e93;'
            ' margin:16px 0; border-top:1px dashed #a1a1aa; border-bottom:1px dashed #a1a1aa;'
            ' padding:4px 0; font-size:11px; font-style:italic; user-select:none;">'
            '— Salto de Página —</p>'
        )
        cursor.insertBlock()
        self.setFocus()

    def insert_blank_page(self):
        """Inserta una página en blanco para control de paginación editorial."""
        cursor = self.textCursor()
        cursor.insertBlock()
        cursor.insertHtml(
            '<p style="page-break-after:always; text-align:center; color:#8e8e93;'
            ' margin:20px 0; border:1px dashed #a1a1aa; border-radius:4px;'
            ' padding:12px 0; font-size:12px; font-style:italic; background:rgba(128,128,128,0.08); user-select:none;">'
            '[ Página en Blanco ]</p>'
        )
        cursor.insertBlock()
        self.setFocus()

    # ------------------------------------------------------------------
    # Manejo de imágenes — inserción
    # ------------------------------------------------------------------

    def canInsertFromMimeData(self, source):
        if source.hasImage() or source.hasUrls():
            return True
        return super().canInsertFromMimeData(source)

    def insertFromMimeData(self, source):
        if source.hasImage():
            image = source.imageData()
            if isinstance(image, QImage) and not image.isNull():
                self._insert_image_object(image)
        elif source.hasUrls():
            for url in source.urls():
                fp = url.toLocalFile()
                if fp.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    try:
                        with open(fp, "rb") as f:
                            data = f.read()
                        image = QImage()
                        image.loadFromData(data)
                        if not image.isNull():
                            self._insert_image_object(image, fp)
                    except Exception:
                        pass
        else:
            # Pegar solo texto plano para conservar el formato editorial (Georgia 12pt).
            # Ctrl+Shift+V permite pegar con formato rico si el usuario lo necesita.
            if source.hasText():
                self.textCursor().insertText(source.text())
            else:
                super().insertFromMimeData(source)

    def _insert_image_object(self, image: QImage, name: str = ""):
        """
        Inserta una imagen en un bloque propio, centrada, con ancho
        limitado al viewport real del editor.
        """
        if image.isNull():
            return

        # Guardar referencia para evitar destrucción por GC
        self._image_cache.append(image)

        # Limitar al ancho útil del editor (viewport - márgenes)
        available_width = self.viewport().width() - 40  # 20px margen a cada lado
        max_width = min(available_width, 700)
        if max_width < 200:
            max_width = 700  # fallback antes del primer render

        if image.width() > max_width:
            image = image.scaledToWidth(
                max_width, Qt.TransformationMode.SmoothTransformation
            )
            self._image_cache.append(image)

        # Nombre único para el recurso
        if not name:
            name = f"img_{uuid.uuid4().hex[:8]}"
        safe_name = name.replace("\\", "/").split("/")[-1]
        # Asegurar unicidad
        resource_name = f"aura_{uuid.uuid4().hex[:6]}_{safe_name}"

        try:
            self.document().addResource(
                self.document().ResourceType.ImageResource,
                QUrl(resource_name), image
            )
        except Exception:
            return

        cursor = self.textCursor()

        # Bloque nuevo antes de la imagen
        cursor.insertBlock()
        # Centrar la imagen
        block_fmt = cursor.blockFormat()
        block_fmt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cursor.setBlockFormat(block_fmt)

        # Insertar la imagen
        img_fmt = QTextImageFormat()
        img_fmt.setName(resource_name)
        img_fmt.setWidth(image.width())
        img_fmt.setHeight(image.height())
        cursor.insertImage(img_fmt)

        # Bloque nuevo después (para seguir escribiendo)
        cursor.insertBlock()
        # Restaurar alineación izquierda
        block_fmt2 = cursor.blockFormat()
        block_fmt2.setAlignment(Qt.AlignmentFlag.AlignLeft)
        cursor.setBlockFormat(block_fmt2)

        self.setTextCursor(cursor)

    # ------------------------------------------------------------------
    # Menú contextual estilizado adaptativo (Claro / Oscuro)
    # ------------------------------------------------------------------

    def _show_context_menu(self, pos):
        """Menú contextual con iconos temáticos de alto contraste en modo claro y oscuro."""
        cursor = self.cursorForPosition(pos)
        char_fmt = cursor.charFormat()

        menu = QMenu(self)
        is_dark = ThemeManager.is_dark()

        # Paleta de colores armoniosa según tema
        _ic = "#d1d1d6" if is_dark else "#4a4a5a"
        _accent = "#ffd60a" if is_dark else "#d97706"
        _danger = "#ff453a" if is_dark else "#dc2626"
        _blue = "#32ade6" if is_dark else "#0284c7"
        _clean_ic = "#ff9f0a" if is_dark else "#d97706"

        if char_fmt.isImageFormat():
            img_fmt = char_fmt.toImageFormat()

            act_delete = menu.addAction(qta.icon("fa5s.trash-alt", color=_danger), "Eliminar imagen")
            menu.addSeparator()
            act_resize_50 = menu.addAction(qta.icon("fa5s.compress-arrows-alt", color=_blue), "Redimensionar al 50%")
            act_resize_75 = menu.addAction(qta.icon("fa5s.expand-arrows-alt", color=_blue), "Redimensionar al 75%")
            act_resize_100 = menu.addAction(qta.icon("fa5s.arrows-alt", color=_blue), "Tamaño original (100%)")

            chosen = menu.exec(self.viewport().mapToGlobal(pos))
            if chosen == act_delete:
                self._delete_image_at_cursor(cursor)
            elif chosen == act_resize_50:
                self._resize_image(cursor, img_fmt, 0.5)
            elif chosen == act_resize_75:
                self._resize_image(cursor, img_fmt, 0.75)
            elif chosen == act_resize_100:
                self._resize_image(cursor, img_fmt, 1.0)
            return

        # Estado de selección y portapapeles
        has_selection = self.textCursor().hasSelection()
        can_undo = self.document().isUndoAvailable()
        can_redo = self.document().isRedoAvailable()
        clipboard = QApplication.clipboard()
        mime = clipboard.mimeData()
        can_paste = bool(mime and (mime.hasText() or mime.hasImage()))

        # ── Edición Estándar ──
        act_undo = menu.addAction(qta.icon("fa5s.undo", color=_ic if can_undo else (_ic + "55")), "Deshacer\tCtrl+Z")
        act_undo.setEnabled(can_undo)
        act_redo = menu.addAction(qta.icon("fa5s.redo", color=_ic if can_redo else (_ic + "55")), "Rehacer\tCtrl+Y")
        act_redo.setEnabled(can_redo)

        menu.addSeparator()

        act_cut = menu.addAction(qta.icon("fa5s.cut", color=_ic if has_selection else (_ic + "55")), "Cortar\tCtrl+X")
        act_cut.setEnabled(has_selection)
        act_copy = menu.addAction(qta.icon("fa5s.copy", color=_ic if has_selection else (_ic + "55")), "Copiar\tCtrl+C")
        act_copy.setEnabled(has_selection)
        act_paste = menu.addAction(qta.icon("fa5s.paste", color=_ic if can_paste else (_ic + "55")), "Pegar\tCtrl+V")
        act_paste.setEnabled(can_paste)
        act_delete = menu.addAction(qta.icon("fa5s.trash-alt", color=_danger if has_selection else (_ic + "55")), "Eliminar\tSupr")
        act_delete.setEnabled(has_selection)

        menu.addSeparator()

        act_select_all = menu.addAction(qta.icon("fa5s.th-large", color=_ic), "Seleccionar todo\tCtrl+A")

        menu.addSeparator()

        # ── Formato de Texto ──
        act_bold = menu.addAction(qta.icon("fa5s.bold", color=_ic), "Negrita\tCtrl+B")
        act_italic = menu.addAction(qta.icon("fa5s.italic", color=_ic), "Cursiva\tCtrl+I")
        act_underline = menu.addAction(qta.icon("fa5s.underline", color=_ic), "Subrayado\tCtrl+U")
        act_strike = menu.addAction(qta.icon("fa5s.strikethrough", color=_ic), "Tachado\tCtrl+K")
        act_clean = menu.addAction(qta.icon("fa5s.eraser", color=_clean_ic), "Limpiar formato\tCtrl+\\")

        menu.addSeparator()

        # ── Tipografía / Inserciones Especiales ──
        act_dot = menu.addAction(qta.icon("fa5s.circle", color=_accent), "Punto medio conlang (·)\tCtrl+.")
        act_dash = menu.addAction(qta.icon("fa5s.minus", color=_accent), "Raya de diálogo (—)\tCtrl+-")
        act_sep = menu.addAction(qta.icon("fa5s.asterisk", color=_accent), "Separador de escena (* * *)\tCtrl+Shift+S")

        chosen = menu.exec(self.viewport().mapToGlobal(pos))
        if not chosen:
            return

        if chosen == act_undo:
            self.undo()
        elif chosen == act_redo:
            self.redo()
        elif chosen == act_cut:
            self.cut()
        elif chosen == act_copy:
            self.copy()
        elif chosen == act_paste:
            self.paste()
        elif chosen == act_delete:
            self.textCursor().removeSelectedText()
        elif chosen == act_select_all:
            self.selectAll()
        elif chosen == act_bold:
            self.set_bold()
        elif chosen == act_italic:
            self.set_italic()
        elif chosen == act_underline:
            self.set_underline()
        elif chosen == act_strike:
            self.set_strikethrough()
        elif chosen == act_clean:
            self.clear_formatting()
        elif chosen == act_dot:
            self.insert_middle_dot()
        elif chosen == act_dash:
            self.insert_em_dash()
        elif chosen == act_sep:
            self.insert_scene_break()

    def _delete_image_at_cursor(self, cursor: QTextCursor):
        """Selecciona y borra el carácter de imagen bajo el cursor.
        Verifica el carácter a la derecha y luego a la izquierda del cursor.
        """
        # FIX BUG-07: el paso original usaba movePosition(..., 0) que es un no-op.
        # Ahora verificamos en ambas direcciones para detectar la imagen.

        # Intentar seleccionar el carácter a la derecha
        right_cursor = QTextCursor(cursor)
        right_cursor.movePosition(
            QTextCursor.MoveOperation.Right,
            QTextCursor.MoveMode.KeepAnchor, 1
        )
        if right_cursor.charFormat().isImageFormat():
            right_cursor.removeSelectedText()
            return

        # Si no había imagen a la derecha, intentar a la izquierda
        left_cursor = QTextCursor(cursor)
        left_cursor.movePosition(
            QTextCursor.MoveOperation.Left,
            QTextCursor.MoveMode.KeepAnchor, 1
        )
        if left_cursor.charFormat().isImageFormat():
            left_cursor.removeSelectedText()


    def _resize_image(self, cursor: QTextCursor, img_fmt: QTextImageFormat,
                      scale: float):
        """Redimensiona la imagen en el documento al porcentaje dado."""
        # Obtener la imagen original del recurso
        resource = self.document().resource(
            self.document().ResourceType.ImageResource,
            QUrl(img_fmt.name())
        )
        if resource is None:
            return

        original = QImage(resource)
        if original.isNull():
            return

        if scale >= 1.0:
            new_w = original.width()
            new_h = original.height()
        else:
            new_w = int(original.width() * scale)
            new_h = int(original.height() * scale)

        # Limitar al ancho del viewport
        available = self.viewport().width() - 40
        if new_w > available:
            ratio = available / new_w
            new_w = available
            new_h = int(new_h * ratio)

        # Seleccionar la imagen y reemplazar con nueva dimensión
        cursor.movePosition(QTextCursor.MoveOperation.Right,
                            QTextCursor.MoveMode.KeepAnchor, 1)
        if cursor.charFormat().isImageFormat():
            new_fmt = QTextImageFormat()
            new_fmt.setName(img_fmt.name())
            new_fmt.setWidth(new_w)
            new_fmt.setHeight(new_h)
            cursor.removeSelectedText()
            cursor.insertImage(new_fmt)

    def insert_em_dash(self):
        """Inserta la raya / guion largo (—) de diálogo literario."""
        self.textCursor().insertText("—")

    def insert_middle_dot(self):
        """Inserta el punto medio (·) para conlangs, morfología y fonética."""
        self.textCursor().insertText("·")
        self.setFocus()

    # ------------------------------------------------------------------
    # Borrado de imagen y atajos de escritura (Guion largo, etc.)
    # ------------------------------------------------------------------

    def keyPressEvent(self, event):
        """Intercepta Delete/Backspace para imágenes, atajos de guion largo, atajos de formato y auto-conversión de '--' a '—'."""
        # ── Motor de sonido Olivetti ──
        try:
            from core.sound_manager import OlivettiSoundEngine
            engine = OlivettiSoundEngine.instance()
            if engine.enabled:
                key = event.key()
                is_enter = key in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
                is_space = (key == Qt.Key.Key_Space)
                is_backspace = (key == Qt.Key.Key_Backspace)
                engine.on_key_pressed(
                    text=event.text(),
                    is_enter=is_enter,
                    is_space=is_space,
                    is_backspace=is_backspace
                )
        except Exception:
            pass

        # ── Atajos de formato y símbolos (Ctrl+B, Ctrl+I, Ctrl+U, Ctrl+K, Ctrl+\, Ctrl+.) ──
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            key = event.key()
            if key == Qt.Key.Key_B:
                self.set_bold()
                return
            elif key == Qt.Key.Key_I:
                self.set_italic()
                return
            elif key == Qt.Key.Key_U:
                self.set_underline()
                return
            elif key == Qt.Key.Key_K or (key == Qt.Key.Key_X and (event.modifiers() & Qt.KeyboardModifier.ShiftModifier)):
                self.set_strikethrough()
                return
            elif key == Qt.Key.Key_Backslash or (key == Qt.Key.Key_Space and (event.modifiers() & Qt.KeyboardModifier.ShiftModifier)):
                self.clear_formatting()
                return
            elif key == Qt.Key.Key_Period:
                self.insert_middle_dot()
                return
            # Ctrl+Shift+V → pegar con formato rico (fuente y estilos del origen)
            elif key == Qt.Key.Key_V and (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                from PyQt6.QtWidgets import QApplication
                mime = QApplication.clipboard().mimeData()
                super().insertFromMimeData(mime)
                return

        # ── Atajos directos para Raya / Guion largo (Ctrl+- o Alt+-) ──
        if event.key() in (Qt.Key.Key_Minus, Qt.Key.Key_Underscore):
            if event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier):
                self.insert_em_dash()
                return

        # ── Auto-conversión de doble guion '--' en raya '—' ──
        if event.text() == "-":
            cursor = self.textCursor()
            if not cursor.hasSelection() and cursor.position() > 0:
                check = QTextCursor(cursor)
                check.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor, 1)
                if check.selectedText() == "-":
                    check.removeSelectedText()
                    cursor.insertText("—")
                    return

        # ── Manejo de imágenes con Delete / Backspace ──
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            cursor = self.textCursor()
            # Si hay selección, dejar que el comportamiento normal actúe
            if cursor.hasSelection():
                super().keyPressEvent(event)
                return

            # Mirar el carácter delante (Delete) o detrás (Backspace)
            check_cursor = QTextCursor(cursor)
            if event.key() == Qt.Key.Key_Delete:
                check_cursor.movePosition(
                    QTextCursor.MoveOperation.Right,
                    QTextCursor.MoveMode.KeepAnchor, 1
                )
            else:
                check_cursor.movePosition(
                    QTextCursor.MoveOperation.Left,
                    QTextCursor.MoveMode.KeepAnchor, 1
                )

            if check_cursor.charFormat().isImageFormat():
                check_cursor.removeSelectedText()
                return

        super().keyPressEvent(event)
