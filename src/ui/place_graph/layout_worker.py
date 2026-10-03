"""
place_graph/layout_worker.py - Hilo secundario para calcular el layout del grafo de lugares.

Separa el calculo de posiciones (CPU-bound) del hilo principal de la UI,
evitando bloqueos al abrir el Atlas Literario con proyectos grandes.

Incluye caching en disco: si los datos del grafo no han cambiado desde la ultima
apertura, reutiliza las posiciones guardadas (0ms de calculo). Util para proyectos
con 200+ lugares donde el N-Body puede tardar varios segundos.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import tempfile
from typing import Dict, Tuple

from PyQt6.QtCore import QThread, pyqtSignal

from core.models import Place, PlaceLink
from .physics import compute_places_layout

log = logging.getLogger(__name__)

# Directorio de cache: junto al modulo actual (persistente entre sesiones)
_CACHE_DIR = os.path.join(os.path.dirname(__file__), "_layout_cache")


def _graph_fingerprint(places: list[Place], links: list[PlaceLink]) -> str:
    """
    Calcula un hash SHA-1 del grafo (ids, categorias y conexiones).
    Si ningun lugar o enlace cambia, el fingerprint es identico y se puede
    reutilizar el layout cacheado sin recalcular.
    """
    parts = []
    for p in sorted(places, key=lambda x: x.id):
        parts.append(f"{p.id}:{p.category}:{p.parent_place_id or ''}")
    for lk in sorted(links, key=lambda x: (x.place_id_a, x.place_id_b)):
        parts.append(f"{lk.place_id_a}-{lk.place_id_b}:{lk.connection_type}")
    raw = "|".join(parts).encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:16]


def _load_cached_layout(fingerprint: str) -> Dict[str, Tuple[float, float]] | None:
    """Carga posiciones desde disco si existe cache valido para este fingerprint."""
    path = os.path.join(_CACHE_DIR, f"{fingerprint}.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {k: (float(v[0]), float(v[1])) for k, v in data.items()}
    except Exception:
        log.debug("Layout cache corrupto, ignorando: %s", path)
        return None


def _save_cached_layout(fingerprint: str, positions: Dict[str, Tuple[float, float]]) -> None:
    """Guarda posiciones en disco para reusar en aperturas futuras."""
    try:
        os.makedirs(_CACHE_DIR, exist_ok=True)
        path = os.path.join(_CACHE_DIR, f"{fingerprint}.json")
        data = {k: [v[0], v[1]] for k, v in positions.items()}
        # Escritura atomica: escribir en tmp y renombrar para evitar corrupcion
        tmp_fd, tmp_path = tempfile.mkstemp(dir=_CACHE_DIR, suffix=".tmp")
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, separators=(",", ":"))
        os.replace(tmp_path, path)
        _evict_old_caches(keep=20)
    except Exception:
        log.debug("No se pudo guardar layout cache", exc_info=True)


def _evict_old_caches(keep: int = 20) -> None:
    """Elimina los caches mas antiguos si hay mas de `keep` archivos."""
    try:
        files = [
            os.path.join(_CACHE_DIR, f)
            for f in os.listdir(_CACHE_DIR)
            if f.endswith(".json")
        ]
        if len(files) <= keep:
            return
        files.sort(key=os.path.getmtime)
        for old in files[:len(files) - keep]:
            os.remove(old)
    except Exception:
        pass


class _LayoutWorker(QThread):
    """
    Ejecuta compute_places_layout() en un hilo secundario para no bloquear la UI.

    Estrategia de rendimiento (para proyectos de 1000+ lugares):
      1. Calcula el fingerprint SHA-1 del grafo (instantaneo).
      2. Si hay cache en disco para ese fingerprint, lo usa directamente (0ms de fisica).
      3. Si no hay cache, ejecuta el algoritmo N-Body y guarda el resultado en disco.

    La segunda apertura del mismo proyecto es practicamente instantanea.

    Senales:
        layout_ready(dict): mapa {place_id: (x, y)} cuando termina el calculo.
    """

    layout_ready = pyqtSignal(dict)

    def __init__(self, places: list[Place], links: list[PlaceLink], parent=None):
        super().__init__(parent)
        self._places = places
        self._links  = links

    def run(self) -> None:
        """Ejecutado en el hilo secundario. No llamar directamente — usar .start()."""
        try:
            fingerprint = _graph_fingerprint(self._places, self._links)

            # 1. Intentar cargar desde cache (primera opcion: 0ms de fisica)
            cached = _load_cached_layout(fingerprint)
            if cached is not None:
                log.debug("Atlas layout: usando cache (%s)", fingerprint)
                self.layout_ready.emit(cached)
                return

            # 2. Calcular layout y guardar en cache para la proxima vez
            log.debug("Atlas layout: calculando N-Body (%d nodos)", len(self._places))
            positions = compute_places_layout(self._places, self._links)
            _save_cached_layout(fingerprint, positions)
            self.layout_ready.emit(positions)

        except Exception:
            log.exception("_LayoutWorker: error calculando layout")
            # Emitir posiciones vacias para que el grafo se muestre aunque sea sin layout
            self.layout_ready.emit({p.id: (0.0, 0.0) for p in self._places})

