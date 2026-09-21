"""
context_tracker.py — Rastreador de contexto pronominal y último sujeto activo.
Responsabilidad única: Permitir que oraciones con pronombres ("él", "ella", "el joven")
o sujetos tácitos hereden el personaje activo del párrafo o la oración anterior.
"""
from __future__ import annotations
import re
from typing import Optional, Dict, List

# Pronombres y sintagmas anafóricos comunes en narrativa en español
_PRONOUNS_SINGULAR = {
    "él": "masculine",
    "ella": "feminine",
    "aquel": "masculine",
    "aquella": "feminine",
    "el joven": "masculine",
    "la joven": "feminine",
    "el guerrero": "masculine",
    "la guerrera": "feminine",
    "el mago": "masculine",
    "la maga": "feminine",
}

_PRONOUN_PATTERN = re.compile(
    r'\b(él|ella|aquel|aquella|el joven|la joven|el guerrero|la guerrera|el mago|la maga)\b',
    re.IGNORECASE
)

class ContextTracker:
    """
    Mantiene el estado del último personaje activo en la escena
    para resolver anáforas y referencias pronominales a lugares.
    """

    def __init__(self):
        self._last_active_character_id: Optional[str] = None
        self._sentence_counter: int = 0

    def reset(self):
        """Reinicia el contexto al cambiar de capítulo."""
        self._last_active_character_id = None
        self._sentence_counter = 0

    def register_subject(self, character_id: str):
        """Registra un personaje explícito como el sujeto activo actual."""
        if character_id:
            self._last_active_character_id = character_id

    def resolve_pronoun_subject(self, sentence: str) -> Optional[str]:
        """
        Si la oración contiene un pronombre o referencia anafórica (o un sujeto tácito/elíptico)
        pero no nombra al personaje explícitamente, retorna el ID del último sujeto activo si existe.
        """
        if not self._last_active_character_id:
            return None

        # 1. Verificar si la oración contiene algún pronombre o sintagma anafórico explícito
        if _PRONOUN_PATTERN.search(sentence):
            return self._last_active_character_id

        # 2. Si no hay pronombre explícito pero hay un sujeto activo registrado recientemente,
        # resolver como sujeto tácito/elíptico de continuidad narrativa
        return self._last_active_character_id
