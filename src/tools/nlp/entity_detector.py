"""
entity_detector.py — Detección de personajes y lugares en el texto del capítulo.
Responsabilidad única: construir un índice FlashText con todos los nombres
(incluyendo aliases) y encontrar sus apariciones en el texto.

Usa el algoritmo Aho-Corasick (FlashText) para búsqueda O(n) — eficiente
incluso con cientos de personajes y lugares.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from tools.nlp.normalizer import normalize

if TYPE_CHECKING:
    from core.models import Character, Place

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class EntitySpan:
    """Aparición detectada de un personaje o lugar en el texto."""
    start: int          # posición de inicio en el texto normalizado
    end: int            # posición de fin (exclusive)
    text: str           # fragmento original detectado
    entity_type: str    # "character" | "place"
    entity_id: str      # ID en la base de datos del universo
    entity_name: str    # nombre canónico del personaje/lugar


@dataclass
class DetectionResult:
    """Resultado completo de la detección de entidades en una oración."""
    sentence: str                           # oración original
    characters: list[EntitySpan] = field(default_factory=list)
    places: list[EntitySpan] = field(default_factory=list)

    @property
    def has_character(self) -> bool:
        return len(self.characters) > 0

    @property
    def has_place(self) -> bool:
        return len(self.places) > 0

    @property
    def is_candidate(self) -> bool:
        """True si la oración tiene al menos un personaje Y un lugar."""
        return self.has_character and self.has_place


class EntityDetector:
    """
    Detecta menciones de personajes y lugares en texto de capítulos.

    Construye dos índices FlashText separados (uno para personajes,
    uno para lugares) y detecta todas las apariciones en O(n).

    Uso:
        detector = EntityDetector(characters, places)
        results = detector.detect_in_text(plain_text)
        for result in results:
            if result.is_candidate:
                # analizar el verbo que conecta personaje y lugar
    """

    def __init__(
        self,
        characters: list["Character"],
        places: list["Place"],
        case_sensitive: bool = False,
    ):
        """
        Construye los índices FlashText para personajes y lugares.

        Args:
            characters: Lista de Character del universo.
            places: Lista de Place del universo.
            case_sensitive: Si True, el matching distingue mayúsculas.
        """
        try:
            from flashtext import KeywordProcessor
        except ImportError:
            log.error(
                "flashtext no está instalado. "
                "Ejecuta: pip install flashtext"
            )
            raise

        self._char_processor = KeywordProcessor(case_sensitive=case_sensitive)
        self._place_processor = KeywordProcessor(case_sensitive=case_sensitive)

        self._build_character_index(characters)
        self._build_place_index(places)

        log.debug(
            "EntityDetector inicializado: %d personajes, %d lugares",
            len(characters), len(places)
        )

    def _build_character_index(self, characters: list["Character"]) -> None:
        """Añade nombres y aliases de todos los personajes al índice."""
        for char in characters:
            if not char.name.strip():
                continue
            # Nombre principal
            self._char_processor.add_keyword(
                normalize(char.name), char.id
            )
            # Aliases (apodos, nombres en conlang, etc.)
            for alias in getattr(char, "aliases", []):
                if alias.strip():
                    self._char_processor.add_keyword(
                        normalize(alias), char.id
                    )

        # Mapa id → Character para reconstruir EntitySpan
        self._char_map: dict[str, "Character"] = {c.id: c for c in characters}

    def _build_place_index(self, places: list["Place"]) -> None:
        """Añade nombres y aliases de todos los lugares al índice."""
        for place in places:
            if not place.name.strip():
                continue
            # Nombre principal
            self._place_processor.add_keyword(
                normalize(place.name), place.id
            )
            # Aliases ("la ciudad del café", nombre en conlang, etc.)
            for alias in getattr(place, "aliases", []):
                if alias.strip():
                    self._place_processor.add_keyword(
                        normalize(alias), place.id
                    )

        # Mapa id → Place para reconstruir EntitySpan
        self._place_map: dict[str, "Place"] = {p.id: p for p in places}

    def detect_in_sentence(self, sentence: str) -> DetectionResult:
        """
        Detecta personajes y lugares en una única oración.

        Args:
            sentence: Oración de texto plano normalizada.

        Returns:
            DetectionResult con las listas de EntitySpan encontradas.
        """
        norm = normalize(sentence)
        result = DetectionResult(sentence=sentence)

        # FlashText.extract_keywords retorna lista de (keyword, start, end)
        for entity_id, start, end in self._char_processor.extract_keywords(
            norm, span_info=True
        ):
            char = self._char_map.get(entity_id)
            if char:
                result.characters.append(EntitySpan(
                    start=start,
                    end=end,
                    text=norm[start:end],
                    entity_type="character",
                    entity_id=entity_id,
                    entity_name=char.name,
                ))

        for entity_id, start, end in self._place_processor.extract_keywords(
            norm, span_info=True
        ):
            place = self._place_map.get(entity_id)
            if place:
                result.places.append(EntitySpan(
                    start=start,
                    end=end,
                    text=norm[start:end],
                    entity_type="place",
                    entity_id=entity_id,
                    entity_name=place.name,
                ))

        return result

    def detect_in_text(self, text: str) -> list[DetectionResult]:
        """
        Divide el texto en oraciones y detecta entidades en cada una.

        Args:
            text: Texto plano completo del capítulo.

        Returns:
            Lista de DetectionResult, uno por oración.
        """
        sentences = _split_sentences(text)
        return [self.detect_in_sentence(s) for s in sentences if s.strip()]


def _split_sentences(text: str) -> list[str]:
    """
    División simple de texto en oraciones por puntuación.
    En Fase 2, spaCy hace esta división de forma más inteligente.

    Separadores: . ! ? seguidos de espacio y mayúscula, o salto de línea.
    """
    import re
    # Dividir en . ! ? seguido de espacio
    parts = re.split(r"(?<=[.!?])\s+", text)
    # También dividir por saltos de línea (párrafos)
    sentences: list[str] = []
    for part in parts:
        sentences.extend(p.strip() for p in part.split("\n") if p.strip())
    return sentences
