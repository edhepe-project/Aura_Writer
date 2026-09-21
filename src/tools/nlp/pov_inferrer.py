"""
pov_inferrer.py — Inferencia de presencia basada en POV y 1ra persona.
Responsabilidad única: Detectar oraciones en 1ra persona ("llegué", "entramos", "viajamos")
y asociarlas directamente al personaje que tiene el punto de vista (POV) del capítulo.
"""
from __future__ import annotations
import re
from typing import Optional, List
from core.models import Chapter, Character

# Verbos típicos de movimiento/presencia conjugados en 1ra persona (singular y plural)
_FIRST_PERSON_VERB_PATTERN = re.compile(
    r'\b(llegu[ée]|llegamos|entr[ée]|entramos|viaj[ée]|viajamos|camin[ée]|caminamos|'
    r'arrib[ée]|arribamos|part[íi]|partimos|sal[íi]|salimos|alcanc[ée]|alcanzamos|'
    r'me\s+encontraba|nos\s+encontr[áa]bamos|estuve|estuvimos|acamp[ée]|acampamos)\b',
    re.IGNORECASE
)

class POVInferrer:
    """
    Infiere si una oración que menciona un lugar y una acción en 1ra persona
    debe atribuirse al personaje que lleva el POV del capítulo.
    """

    @staticmethod
    def find_pov_character_id(chapter: Chapter, characters: List[Character]) -> Optional[str]:
        """
        Determina el ID del personaje POV del capítulo actual.
        """
        if not chapter or not chapter.pov or not characters:
            return None

        pov_text = chapter.pov.strip().lower()
        # 1. Búsqueda por ID exacto
        for c in characters:
            if c.id.lower() == pov_text:
                return c.id

        # 2. Búsqueda por nombre
        for c in characters:
            if c.name.lower() == pov_text or pov_text in c.name.lower():
                return c.id

        return None

    @classmethod
    def infer_presence_from_pov(
        cls,
        sentence: str,
        chapter: Chapter,
        characters: List[Character]
    ) -> Optional[str]:
        """
        Si la oración está en 1ra persona y el capítulo tiene un POV claro,
        retorna el ID del personaje POV.
        """
        if not _FIRST_PERSON_VERB_PATTERN.search(sentence):
            return None

        return cls.find_pov_character_id(chapter, characters)
