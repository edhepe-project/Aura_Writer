import os
import json
import logging
import shutil
import tempfile
import atexit
import glob
from core.security import SecurityManager
from core.usb import USBSync, USBNotFoundError, USBSyncError
from core.models import UniverseMetadata, Obra, Book, Chapter, ChapterRevision

log = logging.getLogger(__name__)


class ProjectManager:
    def __init__(self):
        self.current_project_path: str | None = None
        self.temp_dir: str | None = None
        self.metadata: UniverseMetadata | None = None
        self.is_locked = True
        self.password: str | None = None
        self._totp_secret: str = ""          # secreto TOTP en memoria para cifrado V3
        self.usb_sync: USBSync = USBSync()
        self._last_usb_error: str = ""

        # Limpiar carpetas huérfanas de sesiones anteriores
        self.cleanup_orphaned_temp_dirs()
        # Asegurar limpieza al salir del proceso
        atexit.register(self._cleanup_on_exit)

    # ------------------------------------------------------------------
    # Ciclo de vida del proyecto
    # ------------------------------------------------------------------

    def create_new_project(self, name: str, author: str, password: str, export_path: str):
        """Crea un nuevo universo con una Obra, un Libro y un Capítulo de ejemplo."""
        self.temp_dir = tempfile.mkdtemp(prefix="aura_")
        self.password = password
        self.current_project_path = export_path

        os.makedirs(os.path.join(self.temp_dir, "content"), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, "assets"), exist_ok=True)

        chapter = Chapter(title="Prólogo", content_file="chap_1.html")
        book = Book(title="Libro I", capitulos=[chapter])
        obra = Obra(title=name, libros=[book])

        self.metadata = UniverseMetadata(title=name, author=author, obras=[obra])
        self._write_content(chapter.content_file,
                            "<h1>Prólogo</h1><p>Bienvenido a tu nueva obra…</p>")
        self.is_locked = False
        self.save_project()
        log.info("Proyecto nuevo creado: %s", export_path)

    def open_project(self, file_path: str, password: str, totp_code: str = ""):
        """
        Abre un proyecto existente descifrándolo en un directorio temporal.

        Args:
            file_path:  Ruta del archivo .aura.
            password:   Contraseña del usuario.
            totp_code:  Código TOTP de 6 dígitos o código de recuperación.
                        Requerido para proyectos V3 (3FA). Ignorado para V1/V2.
        """
        self.temp_dir = tempfile.mkdtemp(prefix="aura_")
        try:
            # Detectar si es formato V1 y migrar a V2 automáticamente
            with open(file_path, 'rb') as f:
                header = f.read(6)
            needs_v1_migration = not (SecurityManager.is_v2_format(header)
                                      or SecurityManager.is_v3_format(header))

            SecurityManager.unpackage_project(password, file_path, self.temp_dir,
                                              totp_code=totp_code)
            self.password = password
            self.current_project_path = file_path
            self.load_metadata()
            self.is_locked = False

            # Cargar secreto TOTP en memoria (para re-cifrar en V3 al guardar)
            if self.metadata and self.metadata.totp_enabled and self.metadata.totp_secret:
                self._totp_secret = self.metadata.totp_secret
            else:
                self._totp_secret = ""

            # Migrar V1 → V2 (re-cifrar con llave maestra)
            if needs_v1_migration:
                log.info("Migrando archivo V1 → V2 (llave maestra)...")
                self.save_project()  # Re-guardar en formato V2 (o V3 si ya tiene TOTP)
                log.info("Migración V1→V2 completada: %s", file_path)

            # Inicializar sincronización USB
            self.usb_sync = USBSync(file_path)

            log.info("Proyecto abierto: %s", file_path)
        except Exception as e:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            self.temp_dir = None
            raise ValueError("Contraseña incorrecta o archivo corrupto.") from e

    def save_project(self):
        """Cifra el estado actual al archivo local Y sincroniza con USB."""
        if self.is_locked or not self.current_project_path:
            log.warning("save_project() llamado sin proyecto abierto.")
            return
        self.save_metadata()
        SecurityManager.package_project(
            self.password, self.temp_dir, self.current_project_path,
            totp_secret=self._totp_secret  # V3 si hay TOTP, V2 si no
        )
        fmt = "V3 (3FA)" if self._totp_secret else "V2"
        log.info("Proyecto guardado en formato %s (local): %s", fmt, self.current_project_path)

        # ── Respaldo automático rotativo ────────────────────────────
        try:
            from core.backup_manager import BackupManager
            BackupManager.create_backup(self.current_project_path)
        except Exception as e:
            log.warning("No se pudo generar el backup automático: %s", e)

        # ── Sincronizar con USB si está configurado ──────────────────
        self._last_usb_error = ""
        if self.usb_sync.is_configured():
            try:
                usb_path = self.usb_sync.sync_to_usb(self.current_project_path)
                self.usb_sync.save_config(self.current_project_path)
                log.info("Proyecto sincronizado con USB: %s", usb_path)
            except USBNotFoundError:
                self._last_usb_error = "USB no conectada"
                log.info("USB no conectada — guardado solo local")
            except USBSyncError as e:
                self._last_usb_error = str(e)
                log.warning("Error de sincronización USB: %s", e)

    @property
    def last_usb_error(self) -> str:
        """Último error de sincronización USB (vacío si todo OK)."""
        return self._last_usb_error

    def import_from_usb(self) -> str:
        """
        Copia el archivo .aura de la USB al path local de forma atómica.

        Pasos:
          1. Verifica que USB esté conectada y el archivo exista.
          2. Hace backup del archivo local (.aura.bak), sobreescribiendo el anterior.
          3. Copia USB → local.tmp, verifica SHA-256 y renombra atómicamente.
          4. Retorna la ruta del backup.

        Raises:
            USBNotFoundError: USB no conectada.
            USBSyncError: Error durante la copia o si el archivo no existe en USB.
        """
        if not self.usb_sync.is_configured():
            raise USBSyncError("Sincronización USB no configurada.")

        drive = self.usb_sync.find_configured_drive()
        if not drive:
            raise USBNotFoundError(
                f"USB '{self.usb_sync.volume_label}' no está conectada."
            )

        usb_path = os.path.join(drive.path, self.usb_sync.usb_filename)
        if not os.path.exists(usb_path):
            raise USBSyncError(
                f"El archivo '{self.usb_sync.usb_filename}' no existe en la USB."
            )

        local_path = self.current_project_path
        if not local_path:
            raise USBSyncError("No hay proyecto local abierto.")

        # Backup del archivo local actual
        backup_path = local_path + ".bak"
        if os.path.exists(local_path):
            try:
                shutil.copy2(local_path, backup_path)
                log.info("Backup local creado: %s", backup_path)
            except Exception as e:
                raise USBSyncError(f"No se pudo crear backup local: {e}") from e

        # Copia atómica USB → local
        temp_path = local_path + ".tmp"
        try:
            shutil.copy2(usb_path, temp_path)

            # Verificar integridad
            usb_hash = self.usb_sync.compute_file_hash(usb_path)
            temp_hash = self.usb_sync.compute_file_hash(temp_path)
            if usb_hash != temp_hash:
                os.remove(temp_path)
                raise USBSyncError(
                    "Verificación de integridad fallida al importar desde USB."
                )

            os.replace(temp_path, local_path)
            log.info("Importado desde USB: %s → %s (hash: %s...)",
                     usb_path, local_path, usb_hash[:12])
            return backup_path

        except (USBSyncError, USBNotFoundError):
            raise
        except Exception as e:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
            raise USBSyncError(f"Error al importar desde USB: {e}") from e

    def change_password(self, new_password: str):
        """Cambia la contraseña del proyecto activo y re-cifra el archivo."""
        if self.is_locked or not self.current_project_path:
            raise ValueError("No hay un proyecto abierto.")
        self.password = new_password
        self.save_project()
        log.info("Contraseña del proyecto cambiada con éxito.")

    def close_project(self):
        """Limpia el directorio temporal y cierra la sesión."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.temp_dir = None
        self.password = None
        self.is_locked = True
        self.metadata = None
        self.current_project_path = None

    def _cleanup_on_exit(self):
        """Hook atexit: asegura que el directorio temporal actual se elimine al cerrar."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    @staticmethod
    def cleanup_orphaned_temp_dirs():
        """Busca y elimina carpetas temporales aura_* huérfanas de sesiones previas (>2h de antigüedad)."""
        import time
        system_temp = tempfile.gettempdir()
        pattern = os.path.join(system_temp, "aura_*")
        now = time.time()
        for folder in glob.glob(pattern):
            if os.path.isdir(folder):
                try:
                    mtime = os.path.getmtime(folder)
                    # Solo eliminar si fue creada/modificada hace más de 2 horas
                    if now - mtime > 7200:
                        shutil.rmtree(folder, ignore_errors=True)
                except Exception as e:
                    log.debug("No se pudo eliminar carpeta temporal %s: %s", folder, e)

    # ------------------------------------------------------------------
    # Metadatos
    # ------------------------------------------------------------------

    def load_metadata(self):
        meta_path = os.path.join(self.temp_dir, "meta.json")
        with open(meta_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.metadata = UniverseMetadata.from_dict(data)

    def save_metadata(self):
        meta_path = os.path.join(self.temp_dir, "meta.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata.to_dict(), f, indent=4, ensure_ascii=False)

    # ------------------------------------------------------------------
    # Contenido de capítulos
    # ------------------------------------------------------------------

    def _write_content(self, filename: str, html: str):
        path = os.path.join(self.temp_dir, "content", filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)

    def read_chapter_content(self, content_file: str) -> str:
        """Lee el HTML de un capítulo. Retorna '' si no existe."""
        if not content_file:
            return ""
        path = os.path.join(self.temp_dir, "content", content_file)
        if not os.path.exists(path):
            return ""
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def write_chapter_content(self, content_file: str, html: str):
        """Guarda el HTML del editor en el archivo del capítulo."""
        self._write_content(content_file, html)

    def trigger_presence_analysis(self, chapter_id: str, html: str) -> None:
        """
        Dispara el análisis de presencia de un capítulo en background.

        Llamar después de un guardado MANUAL (Ctrl+S), nunca en auto-guardado.
        El análisis corre en AnalyzerThread — no bloquea la UI.

        El resultado se entrega a través del callback registrado con
        set_presence_analysis_callback().

        Args:
            chapter_id: ID del capítulo que acaba de guardarse.
            html: HTML del capítulo (ya guardado en disco).
        """
        if not self.metadata:
            return

        # Buscar el capítulo en todos los libros
        chapter = self.find_chapter(chapter_id)
        if not chapter:
            log.warning("trigger_presence_analysis: capítulo '%s' no encontrado", chapter_id)
            return

        try:
            from tools.nlp.analyzer_thread import SingleChapterAnalyzerThread
        except ImportError:
            log.debug("tools.nlp no disponible — análisis de presencia omitido")
            return

        thread = SingleChapterAnalyzerThread(
            chapter=chapter,
            html=html,
            characters=self.metadata.characters,
            places=self.metadata.places,
            custom_vocabulary=self.metadata.custom_vocabulary,
        )
        thread.analysis_done.connect(
            lambda presences: self._on_chapter_analysis_done(chapter_id, presences)
        )
        thread.analysis_error.connect(
            lambda msg: log.warning("Análisis de presencia falló: %s", msg)
        )
        # Guardar referencia para evitar que el GC destruya el thread
        self._analysis_threads = getattr(self, "_analysis_threads", [])
        self._analysis_threads.append(thread)
        thread.finished.connect(lambda: self._cleanup_thread(thread))
        thread.start()
        log.debug("AnalyzerThread iniciado para capítulo '%s'", chapter.title)

    def _on_chapter_analysis_done(
        self, chapter_id: str, new_presences: list
    ) -> None:
        """
        Callback del AnalyzerThread cuando termina el análisis.
        Actualiza presences en metadata y notifica a los listeners.
        """
        if not self.metadata:
            return

        # Preservar presencias manuales y de otros capítulos
        preserved = [
            p for p in self.metadata.presences
            if p.is_manual or p.chapter_id != chapter_id
        ]
        self.metadata.presences = preserved + new_presences
        log.info(
            "Presencias actualizadas: capítulo '%s' → %d nuevas",
            chapter_id, len(new_presences)
        )

        # Notificar al callback registrado (PlaceGraphWidget u otro listener)
        callback = getattr(self, "_presence_callback", None)
        if callback:
            try:
                callback(chapter_id, new_presences)
            except Exception as e:
                log.warning("presence_callback error: %s", e)

    def set_presence_analysis_callback(self, callback) -> None:
        """
        Registra un callback que se llama cuando el análisis termina.

        Signature del callback:
            def on_presences_ready(chapter_id: str, presences: list) -> None

        Uso (desde PlaceGraphWidget):
            pm.set_presence_analysis_callback(self._on_presences_ready)
        """
        self._presence_callback = callback

    def _cleanup_thread(self, thread) -> None:
        """Elimina el thread de la lista de referencias cuando termina."""
        threads = getattr(self, "_analysis_threads", [])
        if thread in threads:
            threads.remove(thread)

    # ------------------------------------------------------------------
    # Historial de Revisiones de Capítulos
    # ------------------------------------------------------------------

    def create_chapter_revision(
        self,
        chapter_id: str,
        description: str = "Revisión automática",
        max_revisions: int = 30
    ) -> ChapterRevision | None:
        """
        Crea una instantánea histórica del contenido actual del capítulo.
        Almacena el archivo HTML en content/revisions/ y actualiza la lista de revisiones.
        """
        chapter = self.find_chapter(chapter_id)
        if not chapter or not chapter.content_file:
            return None

        current_html = self.read_chapter_content(chapter.content_file)
        if not current_html.strip():
            return None

        # Si la última revisión tiene exactamente el mismo contenido, no duplicar
        if chapter.revisions:
            last_rev = chapter.revisions[-1]
            last_html = self.read_chapter_revision_content(last_rev)
            if last_html == current_html:
                return last_rev

        import uuid as _uuid
        rev_dir = os.path.join(self.temp_dir, "content", "revisions")
        os.makedirs(rev_dir, exist_ok=True)
        rev_filename = f"rev_{_uuid.uuid4().hex[:10]}.html"
        rev_path = os.path.join(rev_dir, rev_filename)

        with open(rev_path, "w", encoding="utf-8") as f:
            f.write(current_html)

        revision = ChapterRevision(
            content_file=rev_filename,
            description=description
        )
        chapter.revisions.append(revision)

        # Rotación: Podar revisiones antiguas si superan el límite
        if len(chapter.revisions) > max_revisions:
            excess = len(chapter.revisions) - max_revisions
            for old_rev in chapter.revisions[:excess]:
                old_path = os.path.join(rev_dir, old_rev.content_file)
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except OSError:
                        pass
            chapter.revisions = chapter.revisions[excess:]

        return revision

    def read_chapter_revision_content(self, revision: ChapterRevision) -> str:
        """Lee el contenido HTML de una revisión específica."""
        if not revision or not revision.content_file:
            return ""
        path = os.path.join(self.temp_dir, "content", "revisions", revision.content_file)
        if not os.path.exists(path):
            return ""
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def restore_chapter_revision(self, chapter_id: str, revision_id: str) -> bool:
        """
        Restaura el contenido de un capítulo al estado de una revisión seleccionada.
        Crea automáticamente una revisión de respaldo del estado previo antes de restaurar.
        """
        chapter = self.find_chapter(chapter_id)
        if not chapter:
            return False

        target_rev = next((r for r in chapter.revisions if r.id == revision_id), None)
        if not target_rev:
            return False

        rev_html = self.read_chapter_revision_content(target_rev)
        if not rev_html:
            return False

        # Guardar snapshot previo como salvaguarda
        self.create_chapter_revision(chapter_id, description="Copia de seguridad antes de restaurar")

        # Restaurar al archivo actual
        self.write_chapter_content(chapter.content_file, rev_html)
        return True

    # ------------------------------------------------------------------
    # Assets (imágenes)
    # ------------------------------------------------------------------

    def save_media_asset(self, image_bytes: bytes, ext: str = ".png") -> str:
        """Guarda una imagen en assets/ y retorna el nombre del archivo."""
        import uuid as _uuid
        filename = f"media_{_uuid.uuid4().hex[:8]}{ext}"
        assets_dir = os.path.join(self.temp_dir, "assets")
        os.makedirs(assets_dir, exist_ok=True)
        path = os.path.join(assets_dir, filename)
        with open(path, "wb") as f:
            f.write(image_bytes)
        return filename

    def read_media_asset(self, asset_name: str) -> bytes:
        """Lee los bytes de una imagen guardada en assets/."""
        path = os.path.join(self.temp_dir, "assets", asset_name)
        if not os.path.exists(path):
            return b""
        with open(path, "rb") as f:
            return f.read()

    def get_media_asset_path(self, asset_name: str) -> str:
        """Retorna la ruta absoluta del archivo de media."""
        return os.path.join(self.temp_dir, "assets", asset_name)

    # ------------------------------------------------------------------
    # Utilidades de búsqueda
    # ------------------------------------------------------------------

    def find_chapter(self, chapter_id: str) -> Chapter | None:
        """Busca un capítulo por ID en toda la jerarquía."""
        if not self.metadata:
            return None
        for obra in self.metadata.obras:
            for libro in obra.libros:
                for cap in libro.capitulos:
                    if cap.id == chapter_id:
                        return cap
        return None

    def create_chapter(self, title: str, content: str = "") -> Chapter:
        """Crea un capítulo nuevo con su archivo de contenido."""
        import uuid as _uuid
        content_dir = os.path.join(self.temp_dir, "content")
        os.makedirs(content_dir, exist_ok=True)
        content_file = f"chap_{_uuid.uuid4().hex[:8]}.html"
        chapter = Chapter(title=title, content_file=content_file)
        self._write_content(content_file, f"<h1>{title}</h1>{content}")
        return chapter

    def collect_all_chapters(self) -> list[tuple[Chapter, str]]:
        """Retorna una lista de (capítulo, título_del_libro) para el exportador."""
        result = []
        if not self.metadata:
            return result
        for obra in self.metadata.obras:
            for libro in obra.libros:
                for cap in libro.capitulos:
                    result.append((cap, libro.title))
        return result

    # ------------------------------------------------------------------
    # 2FA (TOTP)
    # ------------------------------------------------------------------

    def is_2fa_enabled(self) -> bool:
        """Verifica si el proyecto tiene 2FA activado."""
        return bool(self.metadata and self.metadata.totp_enabled and self.metadata.totp_secret)

    def verify_totp(self, code: str) -> bool:
        """Verifica un código TOTP contra el secreto del proyecto."""
        if not self.is_2fa_enabled():
            return True  # Si no hay 2FA, siempre pasa
        from core.totp_manager import TOTPManager
        return TOTPManager.verify_code(self.metadata.totp_secret, code)

    def use_recovery_code(self, code: str) -> bool:
        """Usa un código de recuperación (un solo uso). Retorna True si fue válido."""
        if not self.is_2fa_enabled():
            return False
        from core.totp_manager import TOTPManager
        success, remaining = TOTPManager.verify_recovery_code(
            code, self.metadata.totp_recovery_codes
        )
        if success:
            self.metadata.totp_recovery_codes = remaining
            self.save_project()
        return success

    def enable_2fa(self, secret: str, recovery_codes: list[str]):
        """Activa 2FA en el proyecto actual y migra el archivo a formato V3 (3FA)."""
        if not self.metadata:
            return
        self.metadata.totp_enabled = True
        self.metadata.totp_secret = secret
        self.metadata.totp_recovery_codes = recovery_codes

        # Guardar secreto en memoria para que save_project use V3
        self._totp_secret = secret
        self.save_project()  # Ahora guarda en V3 automáticamente
        log.info("2FA activado y archivo migrado a formato V3 (3FA) para el proyecto")

    def disable_2fa(self):
        """Desactiva 2FA del proyecto actual y vuelve al formato V2."""
        if not self.metadata:
            return
        self.metadata.totp_enabled = False
        self.metadata.totp_secret = ""
        self.metadata.totp_recovery_codes = []

        # Limpiar secreto en memoria → save_project usará V2 en adelante
        self._totp_secret = ""
        self.save_project()  # Ahora guarda en V2 (sin TOTP en KDF)
        log.info("2FA desactivado y archivo vuelto a formato V2 para el proyecto")
