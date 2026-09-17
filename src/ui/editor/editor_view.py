"""
editor_view.py — El widget QTextEdit especializado de Aura Writer.
Gestiona:
- Tipografía de trabajo y zoom con normalización a 100%
- Espaciado armónico de párrafos y márgenes de página
- Atajos literarios (guion largo '—', punto medio '·', separadores, saltos de página)
- Integración de sonido mecánico Aura Singularity
"""
from __future__ import annotations

from PyQt6.QtWidgets import QTextEdit, QApplication
from PyQt6.QtGui import (
    QTextCharFormat, QTextFormat, QFont, QTextCursor, QImage,
    QTextImageFormat, QTextBlockFormat, QColor
)
from PyQt6.QtCore import Qt, QUrl
import uuid

from core.theme_manager import ThemeManager
from .context_menu import EditorContextMenu


class AuraEditor(QTextEdit):
    """Editor de texto enriquecido especializado para novelistas y escritores."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setPlaceholderText("Tu historia comienza aquí…")

        # Configuración de zoom y apariencia de trabajo
        self._zoom_percentage: int = 100
        self._zoom_in_progress: bool = False
        self._work_font_family: str = "Georgia"
        self._paper_style: str = "auto"
        self._load_appearance_preferences()

        # Margen de página nativo en el documento
        self.document().setDocumentMargin(35)
        self._paragraph_spacing: float = 8.0

        # Cache de imágenes para evitar destrucción por GC
        self._image_cache: list[QImage] = []

        # Menú contextual extendido
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    # ------------------------------------------------------------------
    # Apariencia, Zoom y Accesibilidad
    # ------------------------------------------------------------------

    def _load_appearance_preferences(self):
        """Carga las preferencias de visualización y accesibilidad del editor."""
        try:
            from core.config_manager import ConfigManager
            self._zoom_percentage = ConfigManager.get("editor_zoom", 100)
            self._work_font_family = ConfigManager.get("editor_font", "Georgia")
            self._paper_style = ConfigManager.get("editor_paper", "auto")
        except Exception:
            pass
        self._apply_appearance()

    def _apply_appearance(self):
        """Aplica la tipografía de trabajo y el estilo de papel (SIN tocar char formats del doc)."""
        font = QFont(self._work_font_family)
        font.setPointSizeF(12.0)
        self.setFont(font)
        self.document().setDefaultFont(font)

        paper_styles = {
            "blanco": "background-color: #ffffff; color: #1a1a1a; selection-background-color: #c7d2fe;",
            "sepia":  "background-color: #f4ecd8; color: #2d241e; selection-background-color: #e2d2b6;",
            "verde":  "background-color: #e8f0e6; color: #1c2e1c; selection-background-color: #c8dec4;",
            "noche":  "background-color: #1e1e20; color: #e0e0e0; selection-background-color: #4a4a4e;",
            "oled":   "background-color: #000000; color: #e6e6e6; selection-background-color: #333333;",
            "auto":   ""
        }
        style = paper_styles.get(self._paper_style, "")
        font_css = f"font-family: '{self._work_font_family}', serif;"
        if style:
            self.setStyleSheet(f"AuraEditor {{ {style} {font_css} border: none; border-radius: 6px; padding: 12px; }}")
        else:
            self.setStyleSheet(f"AuraEditor {{ {font_css} }}")

        self._apply_zoom()

    def _apply_zoom(self):
        if getattr(self, '_zoom_in_progress', False):
            return

        doc = self.document()
        if doc.isEmpty():
            return

        self._zoom_in_progress = True
        try:
            BASE_PT = 12.0
            factor = self._zoom_percentage / 100.0
            scaled_pt = BASE_PT * factor

            font = QFont(self._work_font_family)
            font.setPointSizeF(scaled_pt)
            self.setFont(font)
            doc.setDefaultFont(font)

            cursor = QTextCursor(doc)
            cursor.select(QTextCursor.SelectionType.Document)
            if cursor.hasSelection():
                fmt = QTextCharFormat()
                if abs(factor - 1.0) < 0.01:
                    fmt.clearProperty(QTextFormat.Property.FontPointSize)
                else:
                    fmt.setFontPointSize(scaled_pt)
                cursor.mergeCharFormat(fmt)
        finally:
            self._zoom_in_progress = False

    def get_content_html(self) -> str:
        """Devuelve el HTML normalizado a 100 % de zoom para guardar en disco."""
        if getattr(self, '_zoom_in_progress', False):
            return super().toHtml()
        if abs(self._zoom_percentage - 100) < 1:
            return super().toHtml()

        doc = self.document()
        self._zoom_in_progress = True
        try:
            cursor = QTextCursor(doc)
            cursor.select(QTextCursor.SelectionType.Document)
            if cursor.hasSelection():
                fmt = QTextCharFormat()
                fmt.clearProperty(QTextFormat.Property.FontPointSize)
                cursor.mergeCharFormat(fmt)
            html = super().toHtml()
        finally:
            self._zoom_in_progress = False

        self._apply_zoom()
        return html

    def _update_document_font(self, family: str):
        doc = self.document()
        if doc.isEmpty() or getattr(self, '_zoom_in_progress', False):
            return

        self._zoom_in_progress = True
        try:
            cursor = QTextCursor(doc)
            cursor.select(QTextCursor.SelectionType.Document)
            if cursor.hasSelection():
                fmt = QTextCharFormat()
                fmt.setFontFamily(family)
                try:
                    fmt.setFontFamilies([family])
                except Exception:
                    pass
                cursor.mergeCharFormat(fmt)
        finally:
            self._zoom_in_progress = False

        self._apply_zoom()

    def _apply_paragraph_spacing(self):
        doc = self.document()
        if doc.isEmpty():
            return
        block = doc.begin()
        while block.isValid():
            text = block.text()
            if "— Salto de Página —" not in text and "[ Página en Blanco ]" not in text:
                bfmt = block.blockFormat()
                if bfmt.bottomMargin() != self._paragraph_spacing:
                    bfmt.setBottomMargin(self._paragraph_spacing)
                    cursor = QTextCursor(block)
                    cursor.setBlockFormat(bfmt)
            block = block.next()

    def get_zoom_percentage(self) -> int:
        return self._zoom_percentage

    def set_zoom_percentage(self, percentage: int):
        self._zoom_percentage = max(50, min(300, percentage))
        self._apply_zoom()
        try:
            from core.config_manager import ConfigManager
            ConfigManager.set("editor_zoom", self._zoom_percentage)
        except Exception:
            pass

    def zoom_in(self):
        self.set_zoom_percentage(self._zoom_percentage + 10)

    def zoom_out(self):
        self.set_zoom_percentage(self._zoom_percentage - 10)

    def zoom_reset(self):
        self.set_zoom_percentage(100)

    def get_work_font_family(self) -> str:
        return self._work_font_family

    def set_work_font_family(self, family: str):
        self._work_font_family = family
        self._apply_appearance()
        self._update_document_font(family)
        try:
            from core.config_manager import ConfigManager
            ConfigManager.set("editor_font", family)
        except Exception:
            pass

    def get_paper_style(self) -> str:
        return self._paper_style

    def set_paper_style(self, style_id: str):
        self._paper_style = style_id
        self._apply_appearance()
        try:
            from core.config_manager import ConfigManager
            ConfigManager.set("editor_paper", style_id)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Formato de texto
    # ------------------------------------------------------------------

    def set_font_size(self, size):
        self.setFontPointSize(size)

    def set_bold(self):
        fmt = QTextCharFormat()
        current_weight = self.currentCharFormat().fontWeight()
        is_bold = (current_weight >= 600 or self.fontWeight() >= 600)
        fmt.setFontWeight(QFont.Weight.Normal if is_bold else QFont.Weight.Bold)
        self.mergeCurrentCharFormat(fmt)
        self.setFocus()

    def set_italic(self):
        fmt = QTextCharFormat()
        is_italic = self.currentCharFormat().fontItalic() or self.fontItalic()
        fmt.setFontItalic(not is_italic)
        self.mergeCurrentCharFormat(fmt)
        self.setFocus()

    def set_underline(self):
        fmt = QTextCharFormat()
        is_underline = self.currentCharFormat().fontUnderline() or self.fontUnderline()
        fmt.setFontUnderline(not is_underline)
        self.mergeCurrentCharFormat(fmt)
        self.setFocus()

    def set_strikethrough(self):
        fmt = QTextCharFormat()
        is_strike = self.currentCharFormat().fontStrikeOut()
        fmt.setFontStrikeOut(not is_strike)
        self.mergeCurrentCharFormat(fmt)
        self.setFocus()

    def clear_formatting(self):
        fmt = QTextCharFormat()
        family = getattr(self, '_work_font_family', 'Georgia')
        fmt.setFontFamily(family)
        try:
            fmt.setFontFamilies([family])
        except Exception:
            pass
        fmt.setFontPointSize(12)
        fmt.setFontWeight(QFont.Weight.Normal)
        fmt.setFontItalic(False)
        fmt.setFontUnderline(False)
        fmt.setFontStrikeOut(False)
        fmt.clearProperty(QTextFormat.Property.ForegroundBrush)
        cursor = self.textCursor()
        if cursor.hasSelection():
            cursor.setCharFormat(fmt)
        else:
            self.setCurrentCharFormat(fmt)
        self.setFocus()

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
        cursor.beginEditBlock()
        try:
            cursor.insertBlock()
            sep_block_fmt = cursor.blockFormat()
            sep_block_fmt.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cursor.setBlockFormat(sep_block_fmt)
            
            sep_fmt = QTextCharFormat()
            sep_fmt.setFontWeight(QFont.Weight.Bold)
            cursor.insertText("* * *", sep_fmt)
            
            cursor.insertBlock()
            body_block_fmt = cursor.blockFormat()
            body_block_fmt.setAlignment(Qt.AlignmentFlag.AlignLeft)
            cursor.setBlockFormat(body_block_fmt)
            
            clean_fmt = QTextCharFormat()
            family = getattr(self, '_work_font_family', 'Georgia')
            clean_fmt.setFontFamily(family)
            clean_fmt.setFontWeight(QFont.Weight.Normal)
            clean_fmt.setFontItalic(False)
            clean_fmt.setFontUnderline(False)
            clean_fmt.setFontStrikeOut(False)
            clean_fmt.clearProperty(QTextFormat.Property.ForegroundBrush)
            cursor.setCharFormat(clean_fmt)
        finally:
            cursor.endEditBlock()
            
        self.setTextCursor(cursor)
        self.setCurrentCharFormat(clean_fmt)
        self.ensureCursorVisible()
        self.setFocus()

    def insert_page_break(self):
        cursor = self.textCursor()
        family = getattr(self, '_work_font_family', 'Georgia')
        clean_fmt = QTextCharFormat()
        clean_fmt.setFontFamily(family)
        clean_fmt.setFontWeight(QFont.Weight.Normal)
        clean_fmt.setFontItalic(False)
        clean_fmt.setFontUnderline(False)
        clean_fmt.setFontStrikeOut(False)
        clean_fmt.clearProperty(QTextFormat.Property.ForegroundBrush)
        clean_fmt.clearProperty(QTextFormat.Property.FontPointSize)

        cursor.beginEditBlock()
        try:
            cursor.insertBlock()
            marker_bfmt = cursor.blockFormat()
            marker_bfmt.setAlignment(Qt.AlignmentFlag.AlignCenter)
            marker_bfmt.setTopMargin(16)
            marker_bfmt.setBottomMargin(16)
            cursor.setBlockFormat(marker_bfmt)

            marker_cfmt = QTextCharFormat()
            marker_cfmt.setFontFamily(family)
            marker_cfmt.setFontPointSize(10)
            marker_cfmt.setFontItalic(True)
            marker_cfmt.setForeground(QColor("#8e8e93"))
            cursor.insertText("— Salto de Página —", marker_cfmt)

            cursor.insertBlock()
            post_bfmt = cursor.blockFormat()
            post_bfmt.setAlignment(Qt.AlignmentFlag.AlignLeft)
            post_bfmt.setTopMargin(0)
            post_bfmt.setBottomMargin(0)
            cursor.setBlockFormat(post_bfmt)
            cursor.setCharFormat(clean_fmt)
        finally:
            cursor.endEditBlock()

        self.setTextCursor(cursor)
        self.setCurrentCharFormat(clean_fmt)
        self.ensureCursorVisible()
        self.setFocus()

    def insert_blank_page(self):
        cursor = self.textCursor()
        family = getattr(self, '_work_font_family', 'Georgia')
        clean_fmt = QTextCharFormat()
        clean_fmt.setFontFamily(family)
        clean_fmt.setFontWeight(QFont.Weight.Normal)
        clean_fmt.setFontItalic(False)
        clean_fmt.setFontUnderline(False)
        clean_fmt.setFontStrikeOut(False)
        clean_fmt.clearProperty(QTextFormat.Property.ForegroundBrush)
        clean_fmt.clearProperty(QTextFormat.Property.FontPointSize)

        cursor.beginEditBlock()
        try:
            cursor.insertBlock()
            marker_bfmt = cursor.blockFormat()
            marker_bfmt.setAlignment(Qt.AlignmentFlag.AlignCenter)
            marker_bfmt.setTopMargin(16)
            marker_bfmt.setBottomMargin(16)
            cursor.setBlockFormat(marker_bfmt)

            marker_cfmt = QTextCharFormat()
            marker_cfmt.setFontFamily(family)
            marker_cfmt.setFontPointSize(10)
            marker_cfmt.setFontItalic(True)
            marker_cfmt.setForeground(QColor("#8e8e93"))
            cursor.insertText("[ Página en Blanco ]", marker_cfmt)

            cursor.insertBlock()
            post_bfmt = cursor.blockFormat()
            post_bfmt.setAlignment(Qt.AlignmentFlag.AlignLeft)
            post_bfmt.setTopMargin(0)
            post_bfmt.setBottomMargin(0)
            cursor.setBlockFormat(post_bfmt)
            cursor.setCharFormat(clean_fmt)
        finally:
            cursor.endEditBlock()

        self.setTextCursor(cursor)
        self.setCurrentCharFormat(clean_fmt)
        self.ensureCursorVisible()
        self.setFocus()

    def insert_em_dash(self):
        self.insertPlainText("—")
        self.ensureCursorVisible()
        self.setFocus()

    def insert_middle_dot(self):
        self.insertPlainText("·")
        self.ensureCursorVisible()
        self.setFocus()

    # ------------------------------------------------------------------
    # Manejo de imágenes — inserción y portapapeles
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
            if source.hasText():
                self.textCursor().insertText(source.text())
            else:
                super().insertFromMimeData(source)

    def _insert_image_object(self, image: QImage, name: str = ""):
        if image.isNull():
            return

        self._image_cache.append(image)
        available_width = self.viewport().width() - 40
        max_width = min(available_width, 700)
        if max_width < 200:
            max_width = 700

        if image.width() > max_width:
            image = image.scaledToWidth(
                max_width, Qt.TransformationMode.SmoothTransformation
            )
            self._image_cache.append(image)

        if not name:
            name = f"img_{uuid.uuid4().hex[:8]}"
        safe_name = name.replace("\\", "/").split("/")[-1]
        resource_name = f"aura_{uuid.uuid4().hex[:6]}_{safe_name}"

        try:
            self.document().addResource(
                self.document().ResourceType.ImageResource,
                QUrl(resource_name), image
            )
        except Exception:
            return

        cursor = self.textCursor()
        cursor.insertBlock()
        block_fmt = cursor.blockFormat()
        block_fmt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cursor.setBlockFormat(block_fmt)

        img_fmt = QTextImageFormat()
        img_fmt.setName(resource_name)
        img_fmt.setWidth(image.width())
        img_fmt.setHeight(image.height())
        cursor.insertImage(img_fmt)

        cursor.insertBlock()
        block_fmt2 = cursor.blockFormat()
        block_fmt2.setAlignment(Qt.AlignmentFlag.AlignLeft)
        cursor.setBlockFormat(block_fmt2)

        self.setTextCursor(cursor)

    def _show_context_menu(self, pos):
        EditorContextMenu.show_menu(self, pos)

    # ------------------------------------------------------------------
    # Manejo de Teclado, Sonidos y Atajos
    # ------------------------------------------------------------------

    def keyPressEvent(self, e):  # noqa: N802
        event = e

        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not event.modifiers():
            try:
                from core.sound_manager import AuraSoundEngine
                engine = AuraSoundEngine.instance()
                if engine.enabled:
                    engine.on_key_pressed(text=event.text(), is_enter=True)
            except Exception:
                pass
            cursor = self.textCursor()
            if cursor.hasSelection():
                cursor.removeSelectedText()
            curr_bfmt = cursor.blockFormat()
            curr_text = cursor.block().text()
            if "— Salto de Página —" not in curr_text and "[ Página en Blanco ]" not in curr_text:
                curr_bfmt.setBottomMargin(self._paragraph_spacing)
                cursor.setBlockFormat(curr_bfmt)

            new_bfmt = QTextBlockFormat()
            new_bfmt.setAlignment(curr_bfmt.alignment())
            new_bfmt.setBottomMargin(self._paragraph_spacing)
            cursor.insertBlock(new_bfmt)
            self.setTextCursor(cursor)
            self.ensureCursorVisible()
            return

        try:
            from core.sound_manager import AuraSoundEngine
            engine = AuraSoundEngine.instance()
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
        except Exception as _snd_err:
            import logging
            logging.getLogger(__name__).debug("Fallo en sonido mecánico: %s", _snd_err)

        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            key = event.key()
            if key in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
                self.zoom_in()
                return
            elif key == Qt.Key.Key_0:
                self.zoom_reset()
                return
            elif key == Qt.Key.Key_B:
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
            elif key == Qt.Key.Key_V and (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                mime = QApplication.clipboard().mimeData()
                super().insertFromMimeData(mime)
                return

        if event.key() in (Qt.Key.Key_Minus, Qt.Key.Key_Underscore):
            if event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier):
                self.insert_em_dash()
                return

        if event.text() == "-":
            cursor = self.textCursor()
            if not cursor.hasSelection() and cursor.position() > 0:
                check = QTextCursor(cursor)
                check.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor, 1)
                if check.selectedText() == "-":
                    check.removeSelectedText()
                    check.insertText("—")
                    self.setTextCursor(check)
                    return

        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            cursor = self.textCursor()
            if cursor.hasSelection():
                super().keyPressEvent(event)
                return

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

    def wheelEvent(self, e):  # noqa: N802
        event = e
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            elif delta < 0:
                self.zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)
