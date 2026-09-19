"""
sentence_filter.py — Filtro de oraciones (diálogos, cognición, recuerdos).
Responsabilidad única: Detectar si una oración contiene diálogo directo,
o si expresa pensamientos/recuerdos (cognición), para evitar falsos positivos
donde un personaje habla de un lugar sin estar físicamente en él.
"""
import re
from typing import Tuple

# Patrones típicos de guiones de diálogo en español/narrativa
_DIALOGUE_DASHES = ('—', '–', '-', '―', '"', '“', '”', '«', '»')

# Patrones cognitivos o de mención que indican referencia no presencial
_COGNITIVE_PATTERNS = [
    re.compile(r'\b(pens[óo]|pensaba|record[óo]|recordaba|soñ[óo]|soñaba|imagin[óo]|imaginaba)\b', re.IGNORECASE),
    re.compile(r'\b(habl[óo]|hablaba|mencion[óo]|mencionaba|dijo|dec[íi]a|cont[óo]|contaba)\s+(de|sobre)\b', re.IGNORECASE),
    re.compile(r'\b(extrañ[óo]|extrañaba|aoraba|anhelaba)\b', re.IGNORECASE),
    re.compile(r'\b(nostalgia|recuerdo|memoria|sueño)\b', re.IGNORECASE),
]

class SentenceFilter:
    """
    Evalúa si un fragmento u oración debe ser ignorado o tratado con menor peso (cognitivo/diálogo).
    """

    @staticmethod
    def is_dialogue(sentence: str) -> bool:
        """
        Determina si el fragmento o la oración es primordialmente un diálogo directo.
        """
        clean = sentence.strip()
        if not clean:
            return False
            
        # Comienza con guión largo o comillas
        if clean.startswith(_DIALOGUE_DASHES):
            return True
            
        # Contiene comillas envolventes o guiones largos que encierran el texto
        if clean.count('—') >= 2 or (clean.startswith('"') and clean.endswith('"')):
            return True

        return False

    @staticmethod
    def is_cognitive_reference(sentence: str) -> bool:
        """
        Determina si la oración expresa un pensamiento, recuerdo o referencia indirecta.
        """
        for pattern in _COGNITIVE_PATTERNS:
            if pattern.search(sentence):
                return True
        return False

    @classmethod
    def evaluate_sentence(cls, sentence: str) -> Tuple[bool, str]:
        """
        Retorna (should_process, reason).
        Si should_process es False, la presencia física no debe registrarse como 'present'.
        """
        if cls.is_dialogue(sentence):
            return False, "dialogue"
        if cls.is_cognitive_reference(sentence):
            return False, "cognitive"
        return True, "valid"
