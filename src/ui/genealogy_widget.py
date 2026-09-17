"""
genealogy_widget.py — Módulo retrocompatible que expone GenealogyWidget.
Importa desde el paquete modular `src.ui.genealogy`.
"""
from ui.genealogy.widget import GenealogyWidget
from ui.genealogy.items import FlowchartCardItem, FlowchartConnectorItem
from ui.genealogy.layout_engine import GenealogyLayoutEngine

__all__ = ["GenealogyWidget", "FlowchartCardItem", "FlowchartConnectorItem", "GenealogyLayoutEngine"]
