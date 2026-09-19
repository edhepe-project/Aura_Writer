"""
fuzzy_matcher.py — Emparejamiento aproximado de nombres y lugares.
Responsabilidad única: Buscar coincidencias difusas (typos, variaciones ortográficas)
usando RapidFuzz cuando la búsqueda exacta no encuentra resultados o se requiere tolerancia.
"""
from typing import Optional, Tuple, List, Dict
import logging

try:
    from rapidfuzz import process, fuzz
    _RAPIDFUZZ_AVAILABLE = True
except ImportError:
    _RAPIDFUZZ_AVAILABLE = False

logger = logging.getLogger(__name__)

class FuzzyMatcher:
    """
    Realiza matching aproximado contra un catálogo de nombres conocidos (personajes, lugares).
    Protegido contra falsos positivos en palabras cortas (< 4 letras).
    """
    def __init__(self, threshold: float = 85.0, min_length: int = 4):
        self.threshold = threshold
        self.min_length = min_length
        self._target_map: Dict[str, str] = {} # normalized/lower candidate -> entity_id
        self._candidates: List[str] = []

    def set_candidates(self, candidate_map: Dict[str, str]):
        """
        Registra los candidatos disponibles.
        candidate_map: { "nombre_o_alias": "id_o_canonical_name" }
        """
        self._target_map = {k.strip().lower(): v for k, v in candidate_map.items() if len(k.strip()) >= self.min_length}
        self._candidates = list(self._target_map.keys())

    def match(self, query: str) -> Optional[Tuple[str, str, float]]:
        """
        Busca el mejor match para query.
        Retorna (canonical_id_or_name, matched_token, score_0_to_1) o None si no supera el umbral.
        """
        if not _RAPIDFUZZ_AVAILABLE or not self._candidates:
            return None
            
        clean_q = query.strip().lower()
        if len(clean_q) < self.min_length:
            return None

        result = process.extractOne(
            clean_q,
            self._candidates,
            scorer=fuzz.WRatio,
            score_cutoff=self.threshold
        )
        
        if result:
            matched_text, score, _ = result
            target_id = self._target_map.get(matched_text)
            return target_id, matched_text, score / 100.0
            
        return None
