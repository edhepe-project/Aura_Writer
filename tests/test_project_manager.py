import pytest
import os
from core.project_manager import ProjectManager

def test_create_and_open_project(temp_workspace, dummy_password):
    project_path = os.path.join(temp_workspace, "mi_novela.aura")

    pm = ProjectManager()
    pm.create_new_project(
        name="Mi Primera Novela",
        author="Escritor Fantasma",
        password=dummy_password,
        export_path=project_path
    )

    assert os.path.exists(project_path)
    assert not pm.is_locked
    assert pm.metadata.title == "Mi Primera Novela"

    # Ahora abrimos el proyecto con una nueva instancia
    pm2 = ProjectManager()
    pm2.open_project(project_path, dummy_password)
    assert not pm2.is_locked
    assert pm2.metadata.title == "Mi Primera Novela"
    assert pm2.metadata.author == "Escritor Fantasma"
    assert len(pm2.metadata.obras) == 1

def test_open_with_wrong_password_raises(temp_workspace, dummy_password):
    project_path = os.path.join(temp_workspace, "segura.aura")
    pm = ProjectManager()
    pm.create_new_project("Secreto", "Autor", dummy_password, project_path)

    pm2 = ProjectManager()
    with pytest.raises(ValueError, match="Contraseña incorrecta o archivo corrupto"):
        pm2.open_project(project_path, "clave_incorrecta")
