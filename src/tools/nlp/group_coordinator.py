"""
group_coordinator.py — Detección y coordinación de grupos y acompañantes.
Responsabilidad única: Detectar sintagmas comitativos ("junto con", "acompañado de", "y")
para propagar el movimiento de un grupo completo de personajes hacia un destino.
"""
from __future__ import annotations
import re
from typing import List, Set
from tools.nlp.entity_detector import EntitySpan

# Patrones de conexión comitativa y coordinación de personajes
_GROUP_CONNECTORS = re.compile(
    r'\b(junto\s+a|junto\s+con|acompañad[oa]s?\s+de?|con|y|e)\b',
    re.IGNORECASE
)

class GroupCoordinator:
    """
    Coordina la presencia de múltiples personajes que viajan o se desplazan juntos.
    """

    @staticmethod
    def extract_coordinated_characters(
        characters_spans: List[EntitySpan],
        sentence: str
    ) -> List[str]:
        """
        Retorna la lista de IDs de todos los personajes presentes en la oración
        que están vinculados como un grupo o acompañantes.
        """
        if not characters_spans:
            return []

        # Si solo hay 1 personaje, es el único
        if len(characters_spans) == 1:
            return [characters_spans[0].entity_id]

        char_ids: Set[str] = {span.entity_id for span in characters_spans}

        # Si hay múltiples personajes en la misma oración con verbos de movimiento/presencia,
        # verificar si están enlazados por conectores de grupo o coordinación
        if _GROUP_CONNECTORS.search(sentence) or len(char_ids) > 1:
            return list(char_ids)

        return [characters_spans[0].entity_id]
