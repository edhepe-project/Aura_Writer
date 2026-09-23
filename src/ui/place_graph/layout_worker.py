"""
place_graph/layout_worker.py - Hilo secundario para calcular el layout del grafo de lugares.

Separa el calculo de posiciones (CPU-bound) del hilo principal de la UI,
evitando bloqueos al abrir el Atlas Literario con proyectos grandes.
"""
from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from core.models import Place, PlaceLink
from .physics import compute_places_layout


class _LayoutWorker(QThread):
    """
    Ejecuta compute_places_layout() en un hilo secundario para no bloquear la UI.

    El calculo N-Body con espiral aurea puede tomar 100-300 ms con proyectos
    grandes. Al moverlo fuera del hilo principal, el dialogo del Atlas se abre
    instantaneamente y el grafo aparece ~200ms despues.

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
            positions = compute_places_layout(self._places, self._links)
            self.layout_ready.emit(positions)
        except Exception:
            import logging
            logging.getLogger(__name__).exception("_LayoutWorker: error calculando layout")
            # Emitir posiciones vacias para que el grafo se muestre aunque sea sin layout
            self.layout_ready.emit({p.id: (0.0, 0.0) for p in self._places})
