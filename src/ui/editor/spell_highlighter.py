"""
spell_highlighter.py — QSyntaxHighlighter que pinta subrayado rojo ondulado
bajo las palabras con errores ortográficos en AuraEditor.

Flujo:
1. AuraEditor conecta el corrector al highlighter.
2. Cada vez que el corrector emite errors_ready, el highlighter actualiza
   su tabla interna de errores y llama a rehighlight().
3. highlightBlock() marca cada fragmento con error usando QTextCharFormat
   con UnderlineStyle.WaveUnderline en rojo.
"""
from __future__ import annotations

import logging
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt6.QtCore import Qt

from core.spell_checker import SpellError

log = logging.getLogger(__name__)


class SpellHighlighter(QSyntaxHighlighter):
    """
    Aplica subrayado ondulado rojo bajo las palabras con errores ortográficos.

    Se instancia pasándole el QTextDocument del editor:
        highlighter = SpellHighlighter(editor.document())
    """

    UNDERLINE_COLOR = QColor("#ff453a")  # Rojo iOS-style

    def __init__(self, document):
        super().__init__(document)
        # Lista de errores ordenada por posición (actualizada desde el checker)
        self._errors: list[SpellError] = []
        # Huella del último set de errores para evitar rehighlight innecesario
        self._errors_fingerprint: frozenset[tuple[int, int, str]] = frozenset()

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def set_errors(self, errors: list[SpellError]):
        """
        Actualiza la lista de errores y redibuja todo el documento.
        Llamar desde el slot conectado a AuraSpellChecker.errors_ready.
        Solo llama rehighlight() si los errores cambiaron (evita parpadeo).
        """
        new_fingerprint = frozenset((e.start, e.end, e.word) for e in errors)
        if new_fingerprint == self._errors_fingerprint:
            return  # Sin cambios: no repintar
        self._errors = errors
        self._errors_fingerprint = new_fingerprint
        self.rehighlight()

    def clear_errors(self):
        """Elimina todos los subrayados (por ejemplo, al desactivar el corrector)."""
        if not self._errors:
            return  # Ya estaba limpio
        self._errors = []
        self._errors_fingerprint = frozenset()
        self.rehighlight()

    def has_error_at(self, pos: int) -> SpellError | None:
        """
        Devuelve el SpellError que contiene la posición dada,
        o None si no hay error en esa posición.
        Usado por el menú contextual para ofrecer sugerencias.
        """
        for err in self._errors:
            if err.start <= pos < err.end:
                return err
        return None

    # ------------------------------------------------------------------
    # QSyntaxHighlighter interface
    # ------------------------------------------------------------------

    def highlightBlock(self, text: str):
        """
        Qt llama este método bloque a bloque (párrafo a párrafo).
        Calculamos el desplazamiento del bloque en el documento completo
        y buscamos qué errores caen dentro de este bloque.
        """
        if not self._errors:
            return

        # Posición absoluta donde empieza este bloque en el documento
        block_start = self.currentBlock().position()
        block_end = block_start + len(text)

        fmt = QTextCharFormat()
        fmt.setUnderlineColor(self.UNDERLINE_COLOR)
        fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.WaveUnderline)
        # No tocamos color de texto: solo el subrayado
        fmt.setFontUnderline(True)

        for err in self._errors:
            # ¿Hay solapamiento entre el error y este bloque?
            if err.end <= block_start or err.start >= block_end:
                continue

            # Coordenadas relativas al bloque
            rel_start = max(err.start - block_start, 0)
            rel_end   = min(err.end - block_start, len(text))
            length    = rel_end - rel_start

            if length > 0:
                self.setFormat(rel_start, length, fmt)
