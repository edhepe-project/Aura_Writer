"""
Package ui.relation_graph: High-performance interactive visual relationship graph.
"""
from .widget import RelationGraphWidget
from .models import CharacterMetrics, CHARACTER_PALETTE, RELATION_STYLES
from .items import CharacterNode, RelationEdge, CleanBackground
from .scene import GraphScene, RelationGraphView
from .side_panel import NexusSidePanel
from .toolbar import _GraphToolbar

__all__ = [
    "RelationGraphWidget",
    "CharacterMetrics",
    "CHARACTER_PALETTE",
    "RELATION_STYLES",
    "CharacterNode",
    "RelationEdge",
    "CleanBackground",
    "GraphScene",
    "RelationGraphView",
    "NexusSidePanel",
    "_GraphToolbar",
]
