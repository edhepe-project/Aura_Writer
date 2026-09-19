"""
subject_extractor.py — Extracción y validación del sujeto sintáctico usando spaCy.
Responsabilidad única: Identificar la relación de dependencia entre un personaje (sujeto)
y el verbo de desplazamiento o presencia, para asegurar que la acción recae sobre él.
"""
from __future__ import annotations
from typing import Optional, List, Tuple, Any
import logging

try:
    from spacy.tokens import Doc, Token
    _SPACY_AVAILABLE = True
except ImportError:
    _SPACY_AVAILABLE = False
    Doc = Any
    Token = Any

logger = logging.getLogger(__name__)

class SubjectExtractor:
    """
    Verifica mediante análisis de dependencias de spaCy si el personaje es el sujeto
    o participante activo del verbo en la oración.
    """

    @staticmethod
    def find_verb_for_subject(doc: Doc, char_start: int, char_end: int) -> Optional[Tuple[Token, str]]:
        """
        Dado un span de caracteres en el Doc, busca el token de personaje
        y su verbo rector o subordinado.
        Retorna (verb_token, dependency_label) o None.
        """
        if not _SPACY_AVAILABLE or not doc:
            return None

        # Localizar el token correspondiente al span
        char_tokens = [t for t in doc if t.idx >= char_start and (t.idx + len(t.text)) <= char_end]
        if not char_tokens:
            # Buscar el token más cercano si los índices son inexactos
            char_tokens = [t for t in doc if (t.idx <= char_start < t.idx + len(t.text)) or (t.idx < char_end <= t.idx + len(t.text))]
            
        if not char_tokens:
            return None

        head_token = char_tokens[0]

        # Si el token es sujeto (nsubj, nsubj:pass, etc.)
        if "subj" in head_token.dep_:
            if head_token.head.pos_ in ("VERB", "AUX"):
                return head_token.head, head_token.dep_

        # Si el token depende directamente de un verbo
        if head_token.head.pos_ in ("VERB", "AUX"):
            return head_token.head, head_token.dep_

        # Si el token tiene hijos que son verbos o participios
        for child in head_token.children:
            if child.pos_ in ("VERB", "AUX"):
                return child, child.dep_

        return None
