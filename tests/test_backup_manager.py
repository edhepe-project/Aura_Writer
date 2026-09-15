import pytest
import os
from core.backup_manager import BackupManager

def test_backup_creation_and_pruning(temp_workspace):
    project_file = os.path.join(temp_workspace, "novela.aura")
    with open(project_file, "wb") as f:
        f.write(b"CONTENIDO DUMMY AURA V2")

    # Crear múltiples backups con límite de 3
    for _ in range(5):
        BackupManager.create_backup(project_file, max_backups=3)

    backups = BackupManager.list_backups(project_file)
    assert len(backups) <= 3
    for b in backups:
        assert os.path.exists(b)
        assert b.endswith(".bak")

def test_backup_nonexistent_file_returns_none(temp_workspace):
    non_existent = os.path.join(temp_workspace, "no_existe.aura")
    assert BackupManager.create_backup(non_existent) is None
    assert BackupManager.list_backups(non_existent) == []
