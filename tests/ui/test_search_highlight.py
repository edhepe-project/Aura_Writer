import pytest
from PyQt6.QtCore import Qt
from ui.editor.editor_view import AuraEditor
from ui.search.dialog import SearchDialog

def test_editor_find_and_highlight(qtbot):
    editor = AuraEditor()
    qtbot.addWidget(editor)
    
    text = "El caballero desenvainó su espada reluciente y marchó hacia el castillo encantado."
    editor.setPlainText(text)
    
    found = editor.find_and_highlight("castillo")
    assert found is True
    assert editor.textCursor().selectedText() == "castillo"
    assert len(editor.extraSelections()) == 1
    
    # Limpieza
    editor.clear_highlight()
    assert len(editor.extraSelections()) == 0

def test_search_dialog_ui_interaction(qtbot, sample_universe):
    from core.project_manager import ProjectManager
    pm = ProjectManager()
    pm.metadata = sample_universe
    
    dialog = SearchDialog(pm)
    qtbot.addWidget(dialog)
    
    dialog.search_input.setText("Arthur")
    dialog.perform_search()
    
    # Debe encontrar al personaje Arthur Pendragon
    assert dialog._cards_layout.count() > 1
