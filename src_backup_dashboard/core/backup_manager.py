import os
import shutil
import glob
import logging
from datetime import datetime

log = logging.getLogger(__name__)

class BackupManager:
    """
    Gestiona copias de respaldo automáticas y rotativas de proyectos .aura.
    Las copias se guardan en un subdirectorio '.backups' adyacente al archivo del proyecto.
    """

    DEFAULT_MAX_BACKUPS = 10

    @classmethod
    def get_backup_dir(cls, project_path: str) -> str:
        base_dir = os.path.dirname(os.path.abspath(project_path))
        project_name = os.path.splitext(os.path.basename(project_path))[0]
        backup_dir = os.path.join(base_dir, ".backups", project_name)
        os.makedirs(backup_dir, exist_ok=True)
        return backup_dir

    @classmethod
    def create_backup(cls, project_path: str, max_backups: int = DEFAULT_MAX_BACKUPS) -> str | None:
        """
        Crea una copia de respaldo timestamped del archivo de proyecto actual
        y aplica rotación para mantener a lo sumo `max_backups`.
        """
        if not project_path or not os.path.isfile(project_path):
            return None

        try:
            backup_dir = cls.get_backup_dir(project_path)
            project_base = os.path.basename(project_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{project_base}.{timestamp}.bak"
            backup_path = os.path.join(backup_dir, backup_filename)

            # Copiar preservando metadatos
            shutil.copy2(project_path, backup_path)
            log.info("Backup creado con éxito: %s", backup_path)

            cls.prune_backups(backup_dir, project_base, max_backups)
            return backup_path
        except Exception as e:
            log.error("Error al crear copia de seguridad: %s", e)
            return None

    @classmethod
    def list_backups(cls, project_path: str) -> list[str]:
        """Devuelve la lista de rutas de respaldos disponibles, ordenadas de más reciente a más antigua."""
        if not project_path:
            return []
        backup_dir = cls.get_backup_dir(project_path)
        project_base = os.path.basename(project_path)
        pattern = os.path.join(backup_dir, f"{project_base}.*.bak")
        backups = glob.glob(pattern)
        backups.sort(key=os.path.getmtime, reverse=True)
        return backups

    @classmethod
    def prune_backups(cls, backup_dir: str, project_base: str, max_backups: int):
        """Elimina las copias más antiguas si se supera el límite."""
        pattern = os.path.join(backup_dir, f"{project_base}.*.bak")
        backups = glob.glob(pattern)
        backups.sort(key=os.path.getmtime, reverse=True)

        if len(backups) > max_backups:
            for old_backup in backups[max_backups:]:
                try:
                    os.remove(old_backup)
                    log.info("Backup antiguo purgado: %s", old_backup)
                except OSError as e:
                    log.warning("No se pudo eliminar backup antiguo %s: %s", old_backup, e)
