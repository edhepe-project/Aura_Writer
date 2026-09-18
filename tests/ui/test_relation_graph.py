"""Tests para el grafo de relaciones de personajes."""
import pytest
from PyQt6.QtCore import Qt
from ui.relation_graph.widget import RelationGraphWidget
from core.models import Character, CharacterRelation

def test_relation_graph_initialization(qtbot):
    widget = RelationGraphWidget()
    qtbot.addWidget(widget)
    assert widget is not None
    assert widget._scene is not None
    assert widget._view is not None

def test_relation_graph_set_data(qtbot, sample_universe):
    widget = RelationGraphWidget()
    qtbot.addWidget(widget)
    
    widget.set_data(sample_universe.characters, sample_universe.relations)
    
    # Nodos creados en la escena
    assert len(widget._scene._nodes) == len(sample_universe.characters)
    # Relaciones guardadas en la estructura de adyacencia
    assert sum(len(rels) for rels in widget._scene._raw_relations.values()) == len(sample_universe.relations) * 2

def test_relation_graph_build_from_metadata(qtbot, sample_universe):
    widget = RelationGraphWidget()
    qtbot.addWidget(widget)
    
    widget.build_from_metadata(sample_universe)
    assert len(widget._scene._nodes) == len(sample_universe.characters)
    
    # Habilitar vista global de líneas y verificar que se instancian las aristas en _all_edges
    widget._scene.set_show_all_edges(True)
    assert len(widget._scene._all_edges) == len(sample_universe.relations)

def test_relation_graph_node_selection_signal(qtbot, sample_universe):
    widget = RelationGraphWidget()
    qtbot.addWidget(widget)
    widget.build_from_metadata(sample_universe)
    
    node = list(widget._scene._nodes.values())[0]
    
    with qtbot.waitSignal(widget._scene.character_focused, timeout=1000) as blocker:
        widget._scene.character_focused.emit(node.char_id)
        
    assert blocker.args[0] == node.char_id
