"""
src/ui/relation_graph/side_panel — Subpaquete modularizado para el panel lateral del grafo de relaciones.
"""

from ui.relation_graph.side_panel.cards import _PanelHeader, _RelationCard
from ui.relation_graph.side_panel.views import build_compact_view, build_full_sheet_view
from ui.relation_graph.side_panel.panel import NexusSidePanel

__all__ = [
    "_PanelHeader",
    "_RelationCard",
    "build_compact_view",
    "build_full_sheet_view",
    "NexusSidePanel",
]
