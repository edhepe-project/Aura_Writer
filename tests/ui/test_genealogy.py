"""Tests para el árbol genealógico de personajes."""
import pytest
from PyQt6.QtCore import Qt
from ui.genealogy.widget import GenealogyWidget

def test_genealogy_widget_initialization(qtbot, sample_universe):
    char = sample_universe.characters[0]
    widget = GenealogyWidget(
        character=char,
        characters=sample_universe.characters,
        relations=sample_universe.relations
    )
    qtbot.addWidget(widget)
    
    assert widget is not None
    assert widget._char.id == char.id
    assert len(widget._characters) == len(sample_universe.characters)

def test_genealogy_set_data(qtbot, sample_universe):
    char1 = sample_universe.characters[0]
    char2 = sample_universe.characters[2] # Lancelot
    
    widget = GenealogyWidget(
        character=char1,
        characters=sample_universe.characters,
        relations=sample_universe.relations
    )
    qtbot.addWidget(widget)
    
    widget.set_data(char2, sample_universe.characters, sample_universe.relations)
    assert widget._char.id == char2.id
    assert widget._title_lbl.text() == f"LINAJE: {char2.name.upper()}"

def test_genealogy_character_switched_signal(qtbot, sample_universe):
    char = sample_universe.characters[0]
    widget = GenealogyWidget(
        character=char,
        characters=sample_universe.characters,
        relations=sample_universe.relations
    )
    qtbot.addWidget(widget)
    
    target_id = "char_4"
    with qtbot.waitSignal(widget.character_switched, timeout=1000) as blocker:
        widget.character_switched.emit(target_id)
        
    assert blocker.args[0] == target_id
