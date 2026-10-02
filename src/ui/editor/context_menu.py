"""
context_menu.py — Menú contextual estilizado con soporte para temas, inspección de imágenes
y sugerencias del corrector ortográfico.
"""
from __future__ import annotations

from PyQt6.QtWidgets import QMenu, QApplication
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QTextCursor, QTextImageFormat, QImage, QFont
import qtawesome as qta

from core.theme_manager import ThemeManager


class EditorContextMenu:
    """Generador y despachador del menú contextual de AuraEditor."""

    @staticmethod
    def show_menu(editor, pos):
        cursor = editor.cursorForPosition(pos)
        char_fmt = cursor.charFormat()

        menu = QMenu(editor)
        is_dark = ThemeManager.is_dark()

        _ic = "#d1d1d6" if is_dark else "#4a4a5a"
        _accent = "#ffd60a" if is_dark else "#d97706"
        _danger = "#ff453a" if is_dark else "#dc2626"
        _blue = "#32ade6" if is_dark else "#0284c7"
        _clean_ic = "#ff9f0a" if is_dark else "#d97706"
        _spell_c = "#ff453a"

        # ── Sugerencias ortográficas (si la palabra bajo el cursor tiene error) ──
        spell_error = None
        if hasattr(editor, '_spell_highlighter') and hasattr(editor, '_spell_checker'):
            # Obtener posición absoluta del clic en el documento
            click_pos = cursor.position()
            spell_error = editor._spell_highlighter.has_error_at(click_pos)

        if spell_error:
            # Título de sección (no seleccionable)
            title_act = menu.addAction(
                qta.icon("fa5s.spell-check", color=_spell_c),
                f"  ¿Quiso decir... ({spell_error.word})"
            )
            title_font = QFont()
            title_font.setBold(True)
            title_font.setPointSize(10)
            title_act.setFont(title_font)
            title_act.setEnabled(False)

            suggestion_actions = []
            sugs = spell_error.suggestions or (editor.spell_checker.suggestions(spell_error.word) if hasattr(editor, "spell_checker") else [])
            for sug in sugs[:5]:
                act = menu.addAction(
                    qta.icon("fa5s.check", color="#30d158"),
                    f"    {sug}"
                )
                suggestion_actions.append((act, sug))

            menu.addSeparator()
            act_ignore = menu.addAction(
                qta.icon("fa5s.eye-slash", color="#8e8e93"), "  Ignorar esta vez"
            )
            act_add_dict = menu.addAction(
                qta.icon("fa5s.plus-circle", color="#30d158"), "  Añadir al diccionario"
            )
            menu.addSeparator()

            chosen = menu.exec(editor.viewport().mapToGlobal(pos))
            if chosen:
                for act, sug in suggestion_actions:
                    if chosen == act:
                        editor.replace_spell_word(spell_error.start, spell_error.end, sug)
                        return
                if chosen == act_ignore:
                    editor._spell_checker.ignore_word(spell_error.word)
                    # Refrescar
                    editor._trigger_spell_check()
                    return
                if chosen == act_add_dict:
                    editor._spell_checker.add_to_personal_dictionary(spell_error.word)
                    # Bug #8: persistir al proyecto. El menú contextual no tiene acceso directo
                    # al ProjectManager, por lo que notificamos a través del SpellPanel si existe,
                    # o buscamos el ProjectManager subiendo la jerarquía de widgets.
                    word = spell_error.word
                    persisted = False
                    # Intentar via SpellPanel (tiene señal word_added_to_dict conectada al PM)
                    try:
                        parent = editor.parent()
                        while parent is not None:
                            if hasattr(parent, "spell_panel") and hasattr(parent.spell_panel, "word_added_to_dict"):
                                parent.spell_panel.word_added_to_dict.emit(word)
                                persisted = True
                                break
                            if hasattr(parent, "project_manager") and hasattr(parent.project_manager, "add_personal_word"):
                                parent.project_manager.add_personal_word(word)
                                persisted = True
                                break
                            parent = getattr(parent, "parent", lambda: None)()
                    except Exception:
                        pass
                    if not persisted:
                        import logging as _log
                        _log.getLogger(__name__).warning(
                            "add_to_dict desde menú contextual: no se pudo persistir '%s' al proyecto", word
                        )
                    editor._trigger_spell_check()
                    return
            else:
                return

        if char_fmt.isImageFormat():
            img_fmt = char_fmt.toImageFormat()

            act_delete = menu.addAction(qta.icon("fa5s.trash-alt", color=_danger), "Eliminar imagen")
            menu.addSeparator()
            act_resize_50 = menu.addAction(qta.icon("fa5s.compress-arrows-alt", color=_blue), "Redimensionar al 50%")
            act_resize_75 = menu.addAction(qta.icon("fa5s.expand-arrows-alt", color=_blue), "Redimensionar al 75%")
            act_resize_100 = menu.addAction(qta.icon("fa5s.arrows-alt", color=_blue), "Tamaño original (100%)")

            chosen = menu.exec(editor.viewport().mapToGlobal(pos))
            if chosen == act_delete:
                EditorContextMenu.delete_image_at_cursor(cursor)
            elif chosen == act_resize_50:
                EditorContextMenu.resize_image(editor, cursor, img_fmt, 0.5)
            elif chosen == act_resize_75:
                EditorContextMenu.resize_image(editor, cursor, img_fmt, 0.75)
            elif chosen == act_resize_100:
                EditorContextMenu.resize_image(editor, cursor, img_fmt, 1.0)
            return

        has_selection = editor.textCursor().hasSelection()
        can_undo = editor.document().isUndoAvailable()
        can_redo = editor.document().isRedoAvailable()
        clipboard = QApplication.clipboard()
        mime = clipboard.mimeData()
        can_paste = bool(mime and (mime.hasText() or mime.hasImage()))

        # Edición Estándar
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

        # Formato de Texto
        curr_fmt = editor.currentCharFormat()
        is_bold = (curr_fmt.fontWeight() >= 600 or editor.fontWeight() >= 600)
        is_italic = (curr_fmt.fontItalic() or editor.fontItalic())
        is_underline = (curr_fmt.fontUnderline() or editor.fontUnderline())
        is_strike = curr_fmt.fontStrikeOut()

        act_bold = menu.addAction(qta.icon("fa5s.bold", color=_accent if is_bold else _ic), "Negrita\tCtrl+B")
        act_bold.setCheckable(True)
        act_bold.setChecked(is_bold)

        act_italic = menu.addAction(qta.icon("fa5s.italic", color=_accent if is_italic else _ic), "Cursiva\tCtrl+I")
        act_italic.setCheckable(True)
        act_italic.setChecked(is_italic)

        act_underline = menu.addAction(qta.icon("fa5s.underline", color=_accent if is_underline else _ic), "Subrayado\tCtrl+U")
        act_underline.setCheckable(True)
        act_underline.setChecked(is_underline)

        act_strike = menu.addAction(qta.icon("fa5s.strikethrough", color=_accent if is_strike else _ic), "Tachado\tCtrl+K")
        act_strike.setCheckable(True)
        act_strike.setChecked(is_strike)

        act_clean = menu.addAction(qta.icon("fa5s.eraser", color=_clean_ic), "Limpiar formato\tCtrl+\\")

        menu.addSeparator()

        # Inserciones Especiales
        act_dot = menu.addAction(qta.icon("fa5s.circle", color=_accent), "Punto medio conlang (·)\tCtrl+.")
        act_dash = menu.addAction(qta.icon("fa5s.minus", color=_accent), "Raya de diálogo (—)\tCtrl+-")
        act_sep = menu.addAction(qta.icon("fa5s.asterisk", color=_accent), "Separador de escena (* * *)\tCtrl+Shift+S")
        act_pb = menu.addAction(qta.icon("fa5s.cut", color=_danger), "Salto de página")

        chosen = menu.exec(editor.viewport().mapToGlobal(pos))
        if not chosen:
            return

        if chosen == act_undo:
            editor.undo()
        elif chosen == act_redo:
            editor.redo()
        elif chosen == act_cut:
            editor.cut()
        elif chosen == act_copy:
            editor.copy()
        elif chosen == act_paste:
            editor.paste()
        elif chosen == act_delete:
            editor.textCursor().removeSelectedText()
        elif chosen == act_select_all:
            editor.selectAll()
        elif chosen == act_bold:
            editor.set_bold()
        elif chosen == act_italic:
            editor.set_italic()
        elif chosen == act_underline:
            editor.set_underline()
        elif chosen == act_strike:
            editor.set_strikethrough()
        elif chosen == act_clean:
            editor.clear_formatting()
        elif chosen == act_dot:
            editor.insert_middle_dot()
        elif chosen == act_dash:
            editor.insert_em_dash()
        elif chosen == act_sep:
            editor.insert_scene_separator()
        elif chosen == act_pb:
            editor.insert_page_break()

    @staticmethod
    def delete_image_at_cursor(cursor: QTextCursor):
        right_cursor = QTextCursor(cursor)
        right_cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 1)
        if right_cursor.charFormat().isImageFormat():
            right_cursor.removeSelectedText()
            return

        left_cursor = QTextCursor(cursor)
        left_cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor, 1)
        if left_cursor.charFormat().isImageFormat():
            left_cursor.removeSelectedText()

    @staticmethod
    def resize_image(editor, cursor: QTextCursor, img_fmt: QTextImageFormat, scale: float):
        name = img_fmt.name()
        original = None

        # 1. Intentar cargar desde data-URI si está incrustada en Base64
        if name.startswith("data:image"):
            try:
                _, b64 = name.split(",", 1)
                from PyQt6.QtCore import QByteArray
                img = QImage()
                if img.loadFromData(QByteArray.fromBase64(b64.encode("utf-8"))):
                    original = img
            except Exception:
                pass

        # 2. Si no es data-URI o falló, buscar en los recursos del documento Qt
        if original is None or original.isNull():
            resource = editor.document().resource(
                editor.document().ResourceType.ImageResource,
                QUrl(name)
            )
            if resource is not None:
                original = QImage(resource)

        # 3. Fallback: dimensiones actuales del formato si no pudimos extraer el QImage
        if original is None or original.isNull():
            base_w = img_fmt.width() or 400
            base_h = img_fmt.height() or 300
        else:
            base_w = original.width()
            base_h = original.height()

        new_w = int(base_w * scale)
        new_h = int(base_h * scale)

        available = editor.viewport().width() - 40
        if new_w > available and new_w > 0:
            ratio = available / new_w
            new_w = available
            new_h = int(new_h * ratio)

        # Buscar la imagen en la posición actual del cursor (derecha o izquierda)
        target_cursor = QTextCursor(cursor)
        target_cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 1)
        if not target_cursor.charFormat().isImageFormat():
            target_cursor = QTextCursor(cursor)
            target_cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor, 1)

        if target_cursor.charFormat().isImageFormat():
            new_fmt = QTextImageFormat()
            new_fmt.setName(img_fmt.name())
            new_fmt.setWidth(new_w)
            new_fmt.setHeight(new_h)
            target_cursor.removeSelectedText()
            target_cursor.insertImage(new_fmt)

