"""
conlang_vocab.py — Gestión del vocabulario personalizado del universo (conlang).
Responsabilidad única: construir y consultar el índice de palabras personalizadas
a partir de los CustomVocabularyEntry guardados en el proyecto.

Las palabras de conlang se comparan por texto exacto (case-insensitive)
ANTES de que spaCy procese el texto, porque spaCy no puede lematizar
palabras inventadas que no existen en su modelo de entrenamiento.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from tools.nlp.normalizer import normalize

if TYPE_CHECKING:
    from core.models import CustomVocabularyEntry


class ConlangVocab:
    """
    Índice de búsqueda del vocabulario personalizado del universo.

    Uso:
        vocab = ConlangVocab(universe.custom_vocabulary)
        result = vocab.classify("vel·thar")
        # → "present" si "vel·thar" está registrado como verbo de presencia
        # → None si no está en el vocabulario
    """

    def __init__(self, entries: list["CustomVocabularyEntry"]):
        """
        Construye el índice a partir de los entries del universo.

        Args:
            entries: Lista de CustomVocabularyEntry del UniverseMetadata.
        """
        # Índice: palabra normalizada → tipo de presencia
        # normalize() unifica apóstrofes y espacios para matching robusto
        self._index: dict[str, str] = {}
        for entry in entries:
            if entry.word.strip():
                key = normalize(entry.word.strip().lower())
                self._index[key] = entry.presence_type

    def classify(self, word: str) -> str | None:
        """
        Busca una palabra en el vocabulario personalizado.

        Args:
            word: Palabra a clasificar (se normaliza internamente).

        Returns:
            Tipo de presencia ("present", "transit", "departed", "referenced")
            o None si la palabra no está en el vocabulario.
        """
        key = normalize(word.strip().lower())
        return self._index.get(key)

    def contains(self, word: str) -> bool:
        """Retorna True si la palabra está registrada en el vocabulario."""
        return self.classify(word) is not None

    def __len__(self) -> int:
        return len(self._index)

    def __repr__(self) -> str:
        return f"ConlangVocab({len(self._index)} entries)"
