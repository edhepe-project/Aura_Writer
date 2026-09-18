"""Tests de UI para AuraEditor."""
import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor, QFont
from ui.editor.editor_view import AuraEditor

def test_editor_initialization(qtbot):
    editor = AuraEditor()
    qtbot.addWidget(editor)
    assert editor is not None
    assert editor.get_zoom_percentage() == 100
    assert editor.document().documentMargin() == 35

def test_editor_typing_and_text(qtbot):
    editor = AuraEditor()
    qtbot.addWidget(editor)
    
    test_text = "El caballero desenvainó su espada reluciente."
    editor.setPlainText(test_text)
    assert editor.toPlainText() == test_text

def test_editor_zoom_in_out_reset(qtbot):
    editor = AuraEditor()
    qtbot.addWidget(editor)
    editor.setPlainText("Texto para probar zoom.")
    
    initial_zoom = editor.get_zoom_percentage()
    editor.zoom_in()
    assert editor.get_zoom_percentage() == initial_zoom + 10
    
    editor.zoom_out()
    assert editor.get_zoom_percentage() == initial_zoom
    
    editor.set_zoom_percentage(150)
    assert editor.get_zoom_percentage() == 150
    editor.zoom_reset()
    assert editor.get_zoom_percentage() == 100

def test_editor_formatting_bold_italic(qtbot):
    editor = AuraEditor()
    qtbot.addWidget(editor)
    editor.setPlainText("Palabra")
    
    # Seleccionar texto
    cursor = editor.textCursor()
    cursor.select(QTextCursor.SelectionType.Document)
    editor.setTextCursor(cursor)
    
    editor.set_bold()
    fmt = editor.currentCharFormat()
    assert fmt.fontWeight() == QFont.Weight.Bold or fmt.fontWeight() >= 600
    
    editor.set_italic()
    fmt = editor.currentCharFormat()
    assert fmt.fontItalic() is True

def test_editor_paper_style(qtbot):
    editor = AuraEditor()
    qtbot.addWidget(editor)
    
    editor.set_paper_style("sepia")
    assert editor.get_paper_style() == "sepia"
    assert "background-color: #f4ecd8" in editor.styleSheet()
    
    editor.set_paper_style("noche")
    assert editor.get_paper_style() == "noche"
    assert "background-color: #1e1e20" in editor.styleSheet()
