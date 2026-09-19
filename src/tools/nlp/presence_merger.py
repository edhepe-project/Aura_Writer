"""
presence_merger.py — Fusión, deduplicación y resolución de coherencia temporal.
Responsabilidad única: Consolidar múltiples detecciones de presencia a lo largo de un capítulo
o entre capítulos, resolviendo el estado final del personaje (último lugar conocido vs tránsito).
"""
from typing import List, Dict
from core.models import CharacterPresence

class PresenceMerger:
    """
    Fusiona y ordena las presencias detectadas en una escena o capítulo.
    """

    @staticmethod
    def merge_chapter_presences(presences: List[CharacterPresence]) -> List[CharacterPresence]:
        """
        Deduplica y consolida las presencias dentro del mismo capítulo asegurando
        que un personaje solo puede estar en 1 único lugar físico ('present' / 'transit')
        o haber partido ('departed').
        
        Si hay múltiples menciones, se resuelve a favor de:
        1. La última mención cronológica en el texto si ambas son de alta confianza, o
        2. La presencia con mayor confianza (evitando falsos positivos).
        """
        if not presences:
            return []

        # Agrupar por character_id para forzar 1 lugar por personaje
        by_char: Dict[str, CharacterPresence] = {}

        for p in presences:
            char_id = p.character_id
            if not char_id:
                continue

            if char_id not in by_char:
                by_char[char_id] = p
            else:
                existing = by_char[char_id]
                # Priorizar: presencia manual > mayor confianza > estado más reciente
                if p.is_manual and not existing.is_manual:
                    by_char[char_id] = p
                elif not existing.is_manual:
                    # Si la nueva confianza es significativamente mayor o similar (más reciente al final del texto)
                    if p.confidence >= (existing.confidence - 0.05):
                        by_char[char_id] = p

        return list(by_char.values())

    @staticmethod
    def get_latest_character_locations(
        presences: List[CharacterPresence],
        chapter_order_map: Dict[str, int] | None = None
    ) -> List[CharacterPresence]:
        """
        Dado el conjunto de presencias de todo el universo, resuelve la ÚLTIMA
        ubicación física conocida para cada personaje respetando el orden cronológico
        de los capítulos.
        
        Retorna una lista de CharacterPresence con exactamente 1 presencia por personaje.
        """
        if not presences:
            return []

        # Agrupar por personaje
        by_char: Dict[str, List[CharacterPresence]] = {}
        for p in presences:
            if p.presence_type in ("present", "transit") and p.character_id:
                by_char.setdefault(p.character_id, []).append(p)

        latest_list: List[CharacterPresence] = []
        for char_id, char_presences in by_char.items():
            if not char_presences:
                continue

            # Ordenar por:
            # 1. in_world_order del capítulo si está disponible
            # 2. o el orden provisto por chapter_order_map
            # 3. o fecha de creación como fallback
            def _sort_key(item: CharacterPresence):
                order_val = item.in_world_order
                if chapter_order_map and item.chapter_id in chapter_order_map:
                    order_val = chapter_order_map[item.chapter_id]
                return (order_val, item.confidence)

            sorted_p = sorted(char_presences, key=_sort_key)
            latest_list.append(sorted_p[-1])

        return latest_list
