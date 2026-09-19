"""
text_cleaner.py — Convierte HTML de capítulos a texto plano limpio.
Responsabilidad única: HTML → str limpio, sin tags ni entidades HTML.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser


class _HTMLStripper(HTMLParser):
    """Parser minimalista que extrae solo el texto de un documento HTML."""

    def __init__(self):
        super().__init__()
        self._parts: list[str] = []
        self._skip_tags = {"style", "script", "head"}
        self._current_skip = 0

    def handle_starttag(self, tag: str, attrs):
        if tag.lower() in self._skip_tags:
            self._current_skip += 1
        # Añadir salto de línea en elementos de bloque para separar oraciones
        if tag.lower() in {"p", "br", "div", "h1", "h2", "h3", "h4", "li"}:
            self._parts.append("\n")

    def handle_endtag(self, tag: str):
        if tag.lower() in self._skip_tags:
            self._current_skip = max(0, self._current_skip - 1)

    def handle_data(self, data: str):
        if self._current_skip == 0:
            self._parts.append(data)

    def handle_entityref(self, name: str):
        """Convierte entidades HTML comunes a texto."""
        _ENTITIES = {"amp": "&", "lt": "<", "gt": ">", "nbsp": " ",
                     "quot": '"', "apos": "'"}
        if self._current_skip == 0:
            self._parts.append(_ENTITIES.get(name, ""))

    def handle_charref(self, name: str):
        """Convierte referencias numéricas &#160; → carácter."""
        if self._current_skip == 0:
            try:
                code = int(name[1:], 16) if name.startswith("x") else int(name)
                self._parts.append(chr(code))
            except (ValueError, OverflowError):
                pass

    def get_text(self) -> str:
        return "".join(self._parts)


def html_to_text(html: str) -> str:
    """
    Convierte HTML de un capítulo de Aura Writer a texto plano.

    - Elimina todos los tags HTML
    - Convierte entidades HTML (&amp;, &nbsp;, etc.)
    - Inserta saltos de línea en elementos de bloque (p, br, div...)
    - Colapsa espacios múltiples en uno solo
    - Preserva separación de oraciones con punto + espacio

    Args:
        html: Contenido HTML crudo del capítulo.

    Returns:
        Texto plano normalizado, listo para análisis NLP.
    """
    if not html or not html.strip():
        return ""

    stripper = _HTMLStripper()
    stripper.feed(html)
    text = stripper.get_text()

    # Colapsar múltiples espacios en blanco (preservar saltos de línea)
    text = re.sub(r"[ \t]+", " ", text)
    # Colapsar múltiples saltos de línea en uno solo
    text = re.sub(r"\n{2,}", "\n", text)
    # Asegurar que cada línea termina con un espacio para facilitar tokenización
    text = re.sub(r"\n", " ", text)
    # Colapsar espacios finales
    text = text.strip()

    return text
