"""
search_dialog.py — Re-exportación para retrocompatibilidad hacia src/ui/search.
"""

from ui.search import (
    SearchEngine,
    SearchResultCard,
    SearchDialog,
    escape_html,
    highlight_text,
    extract_snippet,
)

__all__ = [
    "SearchEngine",
    "SearchResultCard",
    "SearchDialog",
    "escape_html",
    "highlight_text",
    "extract_snippet",
]
