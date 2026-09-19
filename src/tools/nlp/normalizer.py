"""
normalizer.py — Normalización de texto para el detector de presencia.
Responsabilidad única: estandarizar variantes tipográficas de caracteres especiales
(apóstrofes curvos, espacios no separables, etc.) antes del análisis NLP.
"""
from __future__ import annotations

# Todas las variantes tipográficas de apóstrofe que pueden aparecer
# en texto generado por editores de texto enriquecido (Qt, Word, etc.)
_APOSTROPHE_VARIANTS: tuple[str, ...] = (
    "\u2019",  # ' RIGHT SINGLE QUOTATION MARK (el más común en editores)
    "\u2018",  # ' LEFT SINGLE QUOTATION MARK
    "\u02bc",  # ʼ MODIFIER LETTER APOSTROPHE (lingüística)
    "\u02bb",  # ʻ MODIFIER LETTER TURNED COMMA
    "\u0060",  # ` GRAVE ACCENT (usado como apóstrofe informalmente)
    "\u00b4",  # ´ ACUTE ACCENT
    "\u02c8",  # ˈ MODIFIER LETTER VERTICAL LINE
)

# Variantes de espacios no separables que pueden aparecer en el texto
_NBSP_VARIANTS: tuple[str, ...] = (
    "\u00a0",  # NO-BREAK SPACE
    "\u202f",  # NARROW NO-BREAK SPACE
    "\u2009",  # THIN SPACE
    "\u200b",  # ZERO WIDTH SPACE
    "\ufeff",  # ZERO WIDTH NO-BREAK SPACE (BOM)
)


def normalize_apostrophes(text: str) -> str:
    """
    Normaliza todas las variantes tipográficas de apóstrofe al apóstrofe
    recto ASCII estándar (U+0027).

    Esto garantiza que palabras de conlang como kael'nar, kael'nar o kael'nar
    sean tratadas como idénticas al comparar con el vocabulario personalizado.

    Args:
        text: Texto a normalizar.

    Returns:
        Texto con apóstrofes unificados a U+0027.
    """
    for variant in _APOSTROPHE_VARIANTS:
        if variant in text:
            text = text.replace(variant, "'")
    return text


def normalize_spaces(text: str) -> str:
    """
    Reemplaza variantes de espacios no separables por espacio ASCII estándar.

    Args:
        text: Texto a normalizar.

    Returns:
        Texto con espacios unificados.
    """
    for variant in _NBSP_VARIANTS:
        if variant in text:
            text = text.replace(variant, " ")
    return text


def normalize(text: str) -> str:
    """
    Aplica todas las normalizaciones en orden al texto dado.

    Orden de aplicación:
    1. Espacios no separables → espacio estándar
    2. Apóstrofes tipográficos → apóstrofe recto

    Args:
        text: Texto crudo proveniente del limpiador HTML.

    Returns:
        Texto completamente normalizado para el pipeline NLP.
    """
    text = normalize_spaces(text)
    text = normalize_apostrophes(text)
    return text
