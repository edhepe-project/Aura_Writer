"""
editor_view.py — El widget QTextEdit especializado de Aura Writer.
Gestiona:
- Tipografía de trabajo y zoom con normalización a 100%
- Espaciado armónico de párrafos y márgenes de página
- Atajos literarios (guion largo '—', punto medio '·', separadores, saltos de página)
- Integración de sonido mecánico Aura Singularity
- Corrector ortográfico offline integrado (AuraSpellChecker + SpellHighlighter)
"""
from __future__ import annotations

import re
from PyQt6.QtWidgets import QTextEdit, QApplication
from PyQt6.QtGui import (
    QTextCharFormat, QTextFormat, QFont, QTextCursor, QImage,
    QTextImageFormat, QTextBlockFormat, QColor, QTextDocument
)
from PyQt6.QtCore import Qt, QUrl, QTimer
import os
import uuid

from core.theme_manager import ThemeManager
from core.spell_checker import AuraSpellChecker
from .context_menu import EditorContextMenu
from .spell_highlighter import SpellHighlighter


class AuraEditor(QTextEdit):
    """Editor de texto enriquecido especializado para novelistas y escritores."""

    # Paso de zoom por clic / rueda de ratón (en puntos porcentuales)
    ZOOM_STEP: int = 10

    # ──────────────────────────────────────────────────────────────────
    # Carga de HTML
    # ──────────────────────────────────────────────────────────────────

    def setHtml(self, html: str) -> None:  # noqa: N802
        """Carga HTML saneando los colores que Qt embebe en el tag <body>.

        Cuando Qt genera HTML con toHtml(), escribe los colores del widget en el
        atributo style del <body> (ej. ``<body style=" color:#e0e0e0;">``).  Al
        recargar ese HTML, Qt restaura esos colores como color de texto por
        defecto del documento — ignorando por completo el stylesheet del widget.
        Esto es la causa raíz de que el texto aparezca con un color incorrecto
        al cambiar de tema o de papel.

        Este override elimina color y background-color EXCLUSIVAMENTE del tag
        <body>, preservando cualquier color que el usuario haya aplicado
        intencionalmente en elementos individuales (span, p, etc.).
        """
        def _strip_body_colors(match: re.Match) -> str:
            before = match.group(1)          # '<body ... style="'
            style  = match.group(2)          # contenido del atributo style
            after  = match.group(3)          # '"'
            # Eliminar solo las propiedades color y background-color
            cleaned = re.sub(
                r'\b(background-color|color)\s*:[^;]+;?\s*',
                '',
                style,
                flags=re.IGNORECASE
            )
            return before + cleaned + after

        clean = re.sub(
            r'(<body\b[^>]*?\bstyle\s*=\s*")([^"]*?)(")',
            _strip_body_colors,
            html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        super().setHtml(clean)

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

        # ── Corrector ortográfico ──────────────────────────────────────────
        self._spell_checker = AuraSpellChecker(language="es", parent=self)
        self._spell_highlighter = SpellHighlighter(self.document())
        self._spell_checker.errors_ready.connect(self._on_spell_errors)

        # Timer de debounce: espera 600ms sin escribir antes de revisar
        self._spell_timer = QTimer(self)
        self._spell_timer.setSingleShot(True)
        self._spell_timer.setInterval(600)
        self._spell_timer.timeout.connect(self._trigger_spell_check)
        self.textChanged.connect(self._on_text_changed_for_spell)

        # ── Conectar al gestor de temas para refrescar el lienzo silenciosamente ─
        ThemeManager.signals.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, theme_name: str = ""):
        """Refresca la apariencia del editor al cambiar el tema sin re-escalar zoom innecesariamente."""
        style    = self._build_paper_style(self._paper_style)
        font_css = f"font-family: '{self._work_font_family}', serif; font-size: 12pt;"
        # Siempre incluimos color: explícito para evitar el quirk de herencia de Qt.
        self.setStyleSheet(
            f"AuraEditor {{ {style} {font_css} border: none; border-radius: 6px; padding: 12px; }}"
        )

        # Eliminar colores de texto embebidos en los fragmentos del documento
        # para que el stylesheet sea la única fuente de verdad del color del texto.
        self._clear_document_text_colors()

        # ── Sinónimos (Thesaurus) ──────────────────────────────────────────
        try:
            from core.thesaurus import AuraThesaurus
            AuraThesaurus.get_instance().preload_async()
        except Exception:
            pass

    # ──────────────────────────────────────────────────────────────────
    # Estilo de Papel
    # ──────────────────────────────────────────────────────────────────

    # Colores de fondo de cada estilo de papel.
    # Única fuente de verdad: SOLO fondos, sin colores de texto.
    # Los colores de texto se calculan dinámicamente por luminosidad en _build_paper_style().
    PAPER_BACKGROUNDS = {
        "blanco": "#ffffff",
        "sepia":  "#f4ecd8",
        "verde":  "#e8f0e6",
        "noche":  "#1e1e20",
        "oled":   "#000000",
        "auto":   None,
    }

    @staticmethod
    def _luminance(hex_color: str) -> float:
        """Calcula la luminancia relativa (0.0–1.0) de un color hexadecimal.

        Usa la fórmula perceptual sRGB según WCAG 2.1 para determinar
        si un fondo es oscuro o claro y elegir el texto con máximo contraste.
        """
        hex_color = hex_color.lstrip("#")
        r, g, b = (int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
        def lin(c: float) -> float:
            return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
        return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)

    def _build_paper_style(self, paper_id: str) -> str:
        """Genera el fragmento CSS para el estilo de papel solicitado.

        Siempre devuelve un string CSS completo con color, background-color y
        selection-background-color — nunca vacío.  Esto es crítico para evitar
        el quirk de Qt en el que un widget con setStyleSheet() propio bloquea
        la herencia del color del stylesheet global aunque no lo especifique.

        Fuentes de color sin hardcoding:
        - "auto"         → tokens del tema activo vía ThemeManager.color()
        - Papel claro    → fg_primary / selection_bg del tema light
        - Papel oscuro   → fg_primary / selection_bg del tema dark
        """
        bg_hex = self.PAPER_BACKGROUNDS.get(paper_id)

        if not bg_hex:   # paper_id == "auto" o desconocido
            # Modo automático: tomar colores del tema ACTIVO en tiempo real
            bg  = ThemeManager.color("bg_input")
            fg  = ThemeManager.color("fg_primary")
            sel = ThemeManager.color("selection_bg")
        else:
            bg  = bg_hex
            lum = self._luminance(bg_hex)
            if lum < 0.18:   # Papel oscuro
                fg  = ThemeManager._theme_data("dark")["palette"]["fg_primary"]
                sel = ThemeManager._theme_data("dark")["palette"]["selection_bg"]
            else:            # Papel claro
                fg  = ThemeManager._theme_data("light")["palette"]["fg_primary"]
                sel = ThemeManager._theme_data("light")["palette"]["selection_bg"]

        return (
            f"background-color: {bg}; "
            f"color: {fg}; "
            f"selection-background-color: {sel};"
        )

    def _clear_document_text_colors(self):
        """Elimina los colores de texto (ForegroundBrush) embebidos en los fragmentos del documento.

        Esto evita que colores hardcodeados de temas/papeles anteriores (guardados
        dentro del HTML de los capítulos) interfieran con el color definido por el
        stylesheet activo del widget.

        NOTA: No toca negritas, cursivas, subrayados ni tamaños de fuente — solo el color.
        Preserva los colores en marcadores estructurales (Salto de Página, Página en Blanco).
        Restaura el estado de modificación del documento para no generar guardados falsos.
        """
        doc = self.document()
        if doc.isEmpty():
            return

        if getattr(self, '_color_clear_in_progress', False):
            return
        self._color_clear_in_progress = True
        # Preservar el estado de modificación para no disparar guardados innecesarios
        was_modified = doc.isModified()
        try:
            block = doc.begin()
            while block.isValid():
                block_text = block.text()
                # Preservar los colores de los marcadores estructurales del editor
                is_marker = ("— Salto de Página —" in block_text or
                             "[ Página en Blanco ]" in block_text)
                if not is_marker:
                    it = block.begin()
                    while not it.atEnd():
                        frag = it.fragment()
                        if frag.isValid():
                            char_fmt = frag.charFormat()
                            if char_fmt.hasProperty(QTextFormat.Property.ForegroundBrush):
                                c = QTextCursor(doc)
                                c.setPosition(frag.position())
                                c.setPosition(
                                    frag.position() + frag.length(),
                                    QTextCursor.MoveMode.KeepAnchor
                                )
                                clear_fmt = QTextCharFormat()
                                clear_fmt.clearProperty(QTextFormat.Property.ForegroundBrush)
                                c.mergeCharFormat(clear_fmt)
                        it += 1
                block = block.next()
        finally:
            self._color_clear_in_progress = False
            doc.setModified(was_modified)

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
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("No se pudieron cargar las preferencias de apariencia: %s", e)
        self._apply_appearance()

    def _apply_appearance(self):
        """Aplica la tipografía de trabajo y el estilo de papel (SIN tocar char formats del doc)."""
        font = QFont(self._work_font_family)
        font.setPointSizeF(12.0)
        self.setFont(font)
        self.document().setDefaultFont(font)

        style    = self._build_paper_style(self._paper_style)
        font_css = f"font-family: '{self._work_font_family}', serif; font-size: 12pt;"
        # Siempre color: explícito — evita el quirk de herencia de stylesheet en Qt.
        self.setStyleSheet(
            f"AuraEditor {{ {style} {font_css} border: none; border-radius: 6px; padding: 12px; }}"
        )

        # Limpiar colores de texto embebidos para evitar conflictos entre el
        # papel activo y colores residuales de temas/papeles anteriores.
        self._clear_document_text_colors()

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
                # SIEMPRE incluir la familia en el merge para que nunca se pise
                # lo que _update_document_font acaba de escribir en los fragmentos.
                fmt.setFontFamily(self._work_font_family)
                try:
                    fmt.setFontFamilies([self._work_font_family])
                except Exception:
                    pass
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
        if doc.isEmpty():
            return
        # Usa un flag dedicado para no interferir con _zoom_in_progress
        if getattr(self, '_font_update_in_progress', False):
            return

        self._font_update_in_progress = True
        try:
            # 1. Aplicar mediante selección completa (actualiza el formato base del bloque)
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

            # 2. Recorrer cada fragmento e imponer la familia incondicionalmente.
            # En Qt6, fontFamily() puede devolver '' si la fuente fue asignada
            # via fontFamilies(), por lo que NO comparamos — siempre sobrescribimos.
            block = doc.begin()
            while block.isValid():
                it = block.begin()
                while not it.atEnd():
                    frag = it.fragment()
                    if frag.isValid():
                        c = QTextCursor(doc)
                        c.setPosition(frag.position())
                        c.setPosition(frag.position() + frag.length(),
                                      QTextCursor.MoveMode.KeepAnchor)
                        new_fmt = QTextCharFormat()
                        new_fmt.setFontFamily(family)
                        try:
                            new_fmt.setFontFamilies([family])
                        except Exception:
                            pass
                        c.mergeCharFormat(new_fmt)
                    it += 1
                block = block.next()
        finally:
            self._font_update_in_progress = False

        # Sincronizar solo el zoom (size). NO llamar _apply_appearance() de nuevo
        # porque eso desencadenaría _apply_zoom() que pisaría los formatos recién escritos.
        # _apply_appearance() ya fue llamado por set_work_font_family() ANTES de llegar aquí.
        # Solo necesitamos re-escalar si el zoom no está al 100%.
        if abs(self._zoom_percentage - 100) >= 1:
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
                # Normalizar topMargin a 0 y asegurar el bottomMargin deseado
                # para evitar espaciados excesivos causados por estilos por defecto de h1 / párrafos HTML
                modified = False
                if bfmt.topMargin() != 0:
                    bfmt.setTopMargin(0)
                    modified = True
                if bfmt.bottomMargin() != self._paragraph_spacing:
                    bfmt.setBottomMargin(self._paragraph_spacing)
                    modified = True
                if modified:
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
        self.set_zoom_percentage(self._zoom_percentage + self.ZOOM_STEP)

    def zoom_out(self):
        self.set_zoom_percentage(self._zoom_percentage - self.ZOOM_STEP)

    def zoom_reset(self):
        self.set_zoom_percentage(100)

    def get_work_font_family(self) -> str:
        return self._work_font_family

    def set_work_font_family(self, family: str):
        self._work_font_family = family
        self._apply_appearance()
        self._update_document_font(family)
        # Actualiza el formato del cursor actual para que el próximo texto
        # que se escriba (incluso en doc vacío) use la nueva fuente de inmediato
        cur_fmt = self.currentCharFormat()
        cur_fmt.setFontFamily(family)
        try:
            cur_fmt.setFontFamilies([family])
        except Exception:
            pass
        self.setCurrentCharFormat(cur_fmt)
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

    def _insert_image_object(self, image: QImage, name: str = "", caption: str = ""):
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

        # Convertir a Base64 para que se guarde de forma nativa en el HTML
        from PyQt6.QtCore import QByteArray, QBuffer, QIODevice
        ba = QByteArray()
        buffer = QBuffer(ba)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        image.save(buffer, "PNG")
        b64_data = ba.toBase64().data().decode("utf-8")
        if name:
            safe_name = os.path.basename(name)
            resource_name = f"data:image/png;asset={safe_name};base64,{b64_data}"
        else:
            resource_name = f"data:image/png;base64,{b64_data}"

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

        # Pie de foto (caption) — si se proporcionó
        if caption:
            cursor.insertBlock()
            cap_fmt = cursor.blockFormat()
            cap_fmt.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cursor.setBlockFormat(cap_fmt)
            char_fmt = QTextCharFormat()
            char_fmt.setFontItalic(True)
            char_fmt.setFontPointSize(9)
            cursor.setCharFormat(char_fmt)
            cursor.insertText(caption)
            # Restaurar formato normal
            normal_fmt = QTextCharFormat()
            cursor.setCharFormat(normal_fmt)

        cursor.insertBlock()
        block_fmt2 = cursor.blockFormat()
        block_fmt2.setAlignment(Qt.AlignmentFlag.AlignLeft)
        cursor.setBlockFormat(block_fmt2)

        self.setTextCursor(cursor)

    def remove_image_by_source(self, name_or_asset: str) -> bool:
        """Busca y elimina del documento de texto una imagen que coincida con name_or_asset."""
        if not name_or_asset:
            return False
        doc = self.document()
        block = doc.begin()
        removed = False
        while block.isValid():
            it = block.begin()
            while not it.atEnd():
                frag = it.fragment()
                if frag.isValid():
                    fmt = frag.charFormat()
                    if fmt.isImageFormat():
                        img_fmt = fmt.toImageFormat()
                        img_name = img_fmt.name()
                        # Coincidencia directa por asset_name o data-URI
                        if name_or_asset in img_name:
                            c = QTextCursor(doc)
                            c.setPosition(frag.position())
                            c.setPosition(frag.position() + frag.length(), QTextCursor.MoveMode.KeepAnchor)
                            c.removeSelectedText()
                            removed = True
                            break
                it += 1
            if removed:
                break
            block = block.next()

        if removed:
            self.document().setModified(True)
        return removed

    def remove_image_by_raw_data(self, raw_bytes: bytes) -> bool:
        """Elimina una imagen del documento comparando los bytes base64."""
        if not raw_bytes:
            return False
        from PyQt6.QtCore import QByteArray
        b64 = QByteArray(raw_bytes).toBase64().data().decode("utf-8")
        prefix = b64[:50]  # Suficiente para identificar únicamente la imagen
        return self.remove_image_by_source(prefix)

    def _show_context_menu(self, pos):
        EditorContextMenu.show_menu(self, pos)

    # ------------------------------------------------------------------
    # Corrector Ortográfico
    # ------------------------------------------------------------------

    @property
    def spell_checker(self) -> AuraSpellChecker:
        """Acceso al motor del corrector ortográfico."""
        return self._spell_checker

    @property
    def spell_highlighter(self) -> SpellHighlighter:
        """Acceso al highlighter de subrayado rojo."""
        return self._spell_highlighter

    def _on_text_changed_for_spell(self):
        """Reinicia el timer de debounce en cada cambio de texto."""
        if self._spell_checker.enabled:
            self._spell_timer.start()

    def cleanup(self):
        """Detiene timers y recursos en segundo plano antes de destruir el editor."""
        if hasattr(self, "_spell_timer"):
            self._spell_timer.stop()
        if hasattr(self, "_spell_checker"):
            self._spell_checker.stop()

    def _trigger_spell_check(self):
        """Lanza la revisión en segundo plano con el texto plano actual."""
        if self._spell_checker.enabled:
            self._spell_checker.check_async(self.toPlainText())

    def _on_spell_errors(self, errors):
        """Recibe los errores del checker y actualiza el highlighter."""
        self._spell_highlighter.set_errors(errors)

    def navigate_to_spell_error(self, start: int, end: int):
        """Posiciona el cursor del editor en el error ortográfico indicado."""
        cursor = QTextCursor(self.document())
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()
        self.setFocus()

        # Breve destello para señalar la palabra
        selection = QTextEdit.ExtraSelection()
        hl = QColor("#ff453a")
        hl.setAlpha(80)
        selection.format.setBackground(hl)
        selection.cursor = cursor
        self.setExtraSelections([selection])
        QTimer.singleShot(1200, self.clear_highlight)

    def replace_spell_word(self, start: int, end: int, new_word: str):
        """Reemplaza la palabra con error por la nueva palabra sugerida."""
        cursor = QTextCursor(self.document())
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        cursor.insertText(new_word)
        self.setTextCursor(cursor)

    def open_thesaurus(self, word: str = ""):
        """Abre el diálogo de sinónimos para el término indicado o el seleccionado."""
        if not word:
            cursor = self.textCursor()
            if cursor.hasSelection():
                word = cursor.selectedText().strip()
            else:
                temp_c = QTextCursor(cursor)
                temp_c.select(QTextCursor.SelectionType.WordUnderCursor)
                word = temp_c.selectedText().strip()

        clean_word = "".join(c for c in word if c.isalpha() or c == "-")

        def _on_replace(replacement: str):
            cursor = self.textCursor()
            if not cursor.hasSelection():
                cursor.select(QTextCursor.SelectionType.WordUnderCursor)
            cursor.insertText(replacement)
            self.setTextCursor(cursor)

        from ui.thesaurus_dialog import ThesaurusDialog
        dialog = ThesaurusDialog(initial_word=clean_word, on_replace=_on_replace, parent=self)
        dialog.exec()

    # ------------------------------------------------------------------
    # Manejo de Teclado, Sonidos y Atajos
    # ------------------------------------------------------------------

    def keyPressEvent(self, e):  # noqa: N802
        event = e

        # Atajo Shift+F7 para Diccionario de Sinónimos
        if event.key() == Qt.Key.Key_F7 and (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            self.open_thesaurus()
            event.accept()
            return

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

    # ------------------------------------------------------------------
    # Búsqueda y Resaltado Visual Dinámico
    # ------------------------------------------------------------------

    def find_and_highlight(self, query: str, is_regex: bool = False, case_sensitive: bool = False) -> bool:
        """
        Busca el texto, selecciona la primera coincidencia, desplaza la vista hacia ella
        y aplica un destello visual de halo dorado/amarillo elegante.
        """
        if not query or not query.strip():
            return False

        doc = self.document()
        flags = QTextDocument.FindFlag(0)
        if case_sensitive:
            flags |= QTextDocument.FindFlag.FindCaseSensitively

        cursor = QTextCursor()
        if is_regex:
            import re
            re_flags = 0 if case_sensitive else re.IGNORECASE
            try:
                rx = re.compile(query, re_flags)
                # Buscar usando regex en texto plano
                text = self.toPlainText()
                m = rx.search(text)
                if m:
                    cursor = QTextCursor(doc)
                    cursor.setPosition(m.start())
                    cursor.setPosition(m.end(), QTextCursor.MoveMode.KeepAnchor)
            except Exception:
                cursor = doc.find(query, 0, flags)
        else:
            cursor = doc.find(query, 0, flags)

        if not cursor.isNull() and cursor.hasSelection():
            # 1. Posicionar el cursor y asegurar visibilidad
            self.setTextCursor(cursor)
            self.ensureCursorVisible()

            # 2. Aplicar halo visual con ExtraSelection
            hl_bg = QColor(ThemeManager.color("accent"))
            hl_bg.setAlpha(120)

            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(hl_bg)
            selection.cursor = cursor
            self.setExtraSelections([selection])

            # 3. Desvanecer destello después de 1.8 segundos
            if not hasattr(self, "_highlight_timer"):
                # Bug #4: crear el timer solo UNA vez — antes se recreaba cuando no estaba activo
                self._highlight_timer = QTimer(self)
                self._highlight_timer.setSingleShot(True)
                self._highlight_timer.timeout.connect(self.clear_highlight)

            if self._highlight_timer.isActive():
                self._highlight_timer.stop()

            self._highlight_timer.start(1800)
            self.setFocus()
            return True

        return False

    def clear_highlight(self):
        """Limpia cualquier selección extra de destello visual."""
        self.setExtraSelections([])
