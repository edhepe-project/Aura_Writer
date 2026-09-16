import os
from core.project_manager import ProjectManager

def test_comparator_chapter_persistence(temp_workspace, dummy_password):
    project_path = os.path.join(temp_workspace, "test_compare.aura")
    pm = ProjectManager()
    pm.create_new_project("Novela Dual", "Autor", dummy_password, project_path)

    # Crear dos capítulos
    cap1 = pm.create_chapter("Capítulo 1 - Original")
    cap2 = pm.create_chapter("Capítulo 1 - Alternativo")
    
    libro = pm.metadata.obras[0].libros[0]
    libro.capitulos.extend([cap1, cap2])

    pm.write_chapter_content(cap1.content_file, "<p>El sol brillaba con fuerza.</p>")
    pm.write_chapter_content(cap2.content_file, "<p>La lluvia caía intensamente.</p>")
    pm.save_project()

    # Simular edición bidireccional desde la mesa de cotejo
    pm.write_chapter_content(cap1.content_file, "<p>El sol brillaba con fuerza en el desierto.</p>")
    pm.write_chapter_content(cap2.content_file, "<p>La lluvia caía intensamente en la colina.</p>")
    pm.save_project()

    # Reabrir y verificar coherencia
    pm2 = ProjectManager()
    pm2.open_project(project_path, dummy_password)
    
    c1 = pm2.find_chapter(cap1.id)
    c2 = pm2.find_chapter(cap2.id)

    assert "en el desierto" in pm2.read_chapter_content(c1.content_file)
    assert "en la colina" in pm2.read_chapter_content(c2.content_file)
