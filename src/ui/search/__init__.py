"""
src/ui/search — Subpaquete modularizado para el Buscador Global de Aura Writer.
"""

from ui.search.engine import SearchEngine, escape_html, highlight_text, extract_snippet
from ui.search.card import SearchResultCard
from ui.search.dialog import SearchDialog

__all__ = [
    "SearchEngine",
    "SearchResultCard",
    "SearchDialog",
    "escape_html",
    "highlight_text",
    "extract_snippet",
]
