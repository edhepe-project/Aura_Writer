"""
thesaurus.py — Motor de sinónimos offline (Thesaurus) para Aura Writer.

Utiliza la base de datos de OpenThesaurus (formato MyThes th_es_ES_v2.dat)
para proporcionar sinónimos y alternativas léxicas 100% offline y de alto rendimiento.
"""
from __future__ import annotations

import logging
import os
import sys
import threading
from pathlib import Path

log = logging.getLogger(__name__)


def match_case(template: str, text: str) -> str:
    """
    Aplica el estilo de mayúsculas/minúsculas de 'template' a 'text'.
    Ejemplos:
      - template='Caminar', text='andar' -> 'Andar'
      - template='CAMINAR', text='andar' -> 'ANDAR'
      - template='caminar', text='andar' -> 'andar'
    """
    if not text:
        return text
    if template.isupper():
        return text.upper()
    if template.istitle() or (template and template[0].isupper()):
        return text[0].upper() + text[1:]
    return text.lower()


class AuraThesaurus:
    """
    Gestor de sinónimos en español offline basado en OpenThesaurus / MyThes.
    Carga perezosa (lazy) con soporte para entornos empaquetados PyInstaller.
    """
    _instance: AuraThesaurus | None = None
    _lock = threading.Lock()

    def __init__(self, dat_path: str | Path | None = None):
        self._dat_path = Path(dat_path) if dat_path else self._resolve_dat_path()
        self._index: dict[str, list[list[str]]] = {}
        self._is_loaded = False
        self._load_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> AuraThesaurus:
        """Obtiene la instancia global compartida (singleton)."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @staticmethod
    def _resolve_dat_path() -> Path:
        """Determina la ruta del archivo de sinónimos en dev o bundle PyInstaller."""
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            base_dir = Path(getattr(sys, "_MEIPASS"))
            path1 = base_dir / "core" / "dicts" / "th_es_ES_v2.dat"
            if path1.exists():
                return path1
            path2 = base_dir / "src" / "core" / "dicts" / "th_es_ES_v2.dat"
            if path2.exists():
                return path2

        return Path(__file__).parent / "dicts" / "th_es_ES_v2.dat"

    def preload_async(self):
        """Inicia la carga de la base de datos en un hilo secundario daemon."""
        if not self._is_loaded:
            thread = threading.Thread(target=self._ensure_loaded, daemon=True, name="AuraThesaurus-Loader")
            thread.start()

    def _ensure_loaded(self):
        """Carga y parsea la base de datos en memoria si aún no está lista."""
        if self._is_loaded:
            return

        with self._load_lock:
            if self._is_loaded:
                return

            if not self._dat_path or not self._dat_path.exists():
                log.warning("Archivo de sinónimos no encontrado en %s", self._dat_path)
                self._is_loaded = True
                return

            try:
                # 1. Detectar codificación desde la primera línea
                encoding = "iso-8859-1"
                with open(self._dat_path, "rb") as f_raw:
                    first_line = f_raw.readline().decode("ascii", errors="ignore").strip().upper()
                    if "UTF-8" in first_line:
                        encoding = "utf-8"

                # 2. Parsear el archivo MyThes
                new_index: dict[str, list[list[str]]] = {}
                with open(self._dat_path, "r", encoding=encoding, errors="replace") as f:
                    lines = f.readlines()

                i = 1
                total = len(lines)
                while i < total:
                    line = lines[i].strip()
                    if not line or "|" not in line:
                        i += 1
                        continue

                    parts = line.split("|")
                    headword = parts[0].strip().lower()
                    try:
                        count = int(parts[1])
                    except (IndexError, ValueError):
                        i += 1
                        continue

                    senses: list[list[str]] = []
                    for _ in range(count):
                        i += 1
                        if i < total:
                            syn_line = lines[i].strip()
                            if syn_line:
                                syn_tokens = syn_line.split("|")
                                # El primer elemento suele ser la categoría léxica (e.g. '(adj)' o '(s)' o '-')
                                group: list[str] = []
                                for token in syn_tokens[1:]:
                                    clean = token.strip()
                                    if clean and clean.lower() != headword:
                                        group.append(clean)
                                if group:
                                    senses.append(group)

                    if senses:
                        if headword in new_index:
                            new_index[headword].extend(senses)
                        else:
                            new_index[headword] = senses
                    i += 1

                self._index = new_index
                log.info("Diccionario de sinónimos cargado: %d términos disponibles.", len(self._index))
            except Exception as exc:
                log.error("Error al cargar la base de datos de sinónimos: %s", exc)
            finally:
                self._is_loaded = True

    def get_synonyms(self, word: str, max_results: int = 8) -> list[str]:
        """
        Retorna una lista plana de sinónimos ordenados y sin duplicados para 'word'.
        Conserva el estilo de mayúsculas/minúsculas de la palabra de entrada.
        """
        if not word or len(word) <= 1:
            return []

        self._ensure_loaded()
        clean_word = word.strip().lower()
        senses = self._index.get(clean_word)
        if not senses:
            return []

        seen: set[str] = set()
        results: list[str] = []

        for group in senses:
            for syn in group:
                syn_lower = syn.lower()
                if syn_lower != clean_word and syn_lower not in seen:
                    seen.add(syn_lower)
                    results.append(match_case(word, syn))
                    if len(results) >= max_results:
                        return results

        return results

    def get_senses(self, word: str) -> list[list[str]]:
        """
        Retorna los sinónimos agrupados por acepción o sentido léxico.
        """
        if not word or len(word) <= 1:
            return []

        self._ensure_loaded()
        clean_word = word.strip().lower()
        raw_senses = self._index.get(clean_word, [])
        formatted: list[list[str]] = []

        for group in raw_senses:
            group_results: list[str] = []
            for syn in group:
                if syn.lower() != clean_word:
                    group_results.append(match_case(word, syn))
            if group_results:
                formatted.append(group_results)

        return formatted

    def has_synonyms(self, word: str) -> bool:
        """Verifica rápidamente si existen sinónimos para el término."""
        if not word or len(word) <= 1:
            return False
        self._ensure_loaded()
        return word.strip().lower() in self._index
