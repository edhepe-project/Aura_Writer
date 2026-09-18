import pytest
import os
from PyQt6.QtCore import Qt
from core.project_manager import ProjectManager
from core.models import Chapter
from ui.history_diff_dialog import ChapterHistoryDiffDialog

def test_chapter_revision_lifecycle(temp_workspace, dummy_password):
    project_path = os.path.join(temp_workspace, "test_revisions.aura")
    pm = ProjectManager()
    pm.create_new_project("Novela Épica", "Autor", dummy_password, project_path)
    
    chapter = pm.create_chapter("Capítulo 1", "<p>Versión Original 1.0</p>")
    pm.metadata.obras[0].libros[0].capitulos.append(chapter)
    pm.save_project()
    
    # Crear primera revisión
    rev1 = pm.create_chapter_revision(chapter.id, description="Borrador inicial")
    assert rev1 is not None
    assert len(chapter.revisions) == 1
    
    # Modificar contenido y crear segunda revisión
    pm.write_chapter_content(chapter.content_file, "<p>Versión Modificada 2.0 con más detalles.</p>")
    rev2 = pm.create_chapter_revision(chapter.id, description="Borrador con detalles")
    assert rev2 is not None
    assert len(chapter.revisions) == 2
    assert rev2.id != rev1.id
    
    # Restaurar a rev1
    success = pm.restore_chapter_revision(chapter.id, rev1.id)
    assert success is True
    restored_content = pm.read_chapter_content(chapter.content_file)
    assert "<p>Versión Original 1.0</p>" in restored_content

def test_history_diff_dialog_ui(qtbot, temp_workspace, dummy_password):
    project_path = os.path.join(temp_workspace, "test_dialog.aura")
    pm = ProjectManager()
    pm.create_new_project("Novela Diálogo", "Autor", dummy_password, project_path)
    
    chapter = pm.create_chapter("Capítulo Único", "<p>Texto base.</p>")
    pm.metadata.obras[0].libros[0].capitulos.append(chapter)
    
    # Crear una revisión
    pm.create_chapter_revision(chapter.id, description="Snapshot 1")
    # Modificar contenido actual
    pm.write_chapter_content(chapter.content_file, "<p>Texto base modificado.</p>")
    
    dialog = ChapterHistoryDiffDialog(pm, chapter)
    qtbot.addWidget(dialog)
    
    assert dialog.list_revisions.count() == 1
    assert dialog.btn_restore.isEnabled() is True
    assert "<ins" in dialog.diff_browser.toHtml() or "modificado" in dialog.diff_browser.toPlainText()
