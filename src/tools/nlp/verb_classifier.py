"""
verb_classifier.py — Clasificador de verbos usando spaCy (Fase 2).
Responsabilidad única: dado un texto, encontrar el verbo principal
de cada oración y clasificarlo como present/transit/departed/referenced.

Reemplaza el sistema de regex de la Fase 1 con lematización real de spaCy:
  - spaCy convierte "llegó", "llegaba", "habría llegado" → lemma "llegar"
  - El lemma se consulta en VERB_TYPE_MAP (diccionario de infinitivos)
  - Los verbos de conlang se verifican ANTES en el vocabulario personalizado

Diseño:
  - Sin estado interno — todas las funciones son puras o reciben el nlp
  - Fallback automático a Fase 1 si spaCy no está disponible
"""
from __future__ import annotations

import logging
from typing import Optional

from tools.nlp.verb_rules import VERB_TYPE_MAP, DESTINATION_PREPS, ORIGIN_PREPS
from tools.nlp.conlang_vocab import ConlangVocab
from tools.nlp.normalizer import normalize

log = logging.getLogger(__name__)

# Confianza por método de detección (Fase 2 con spaCy — más alta que Fase 1)
_CONFIDENCE_SPACY_LEMMA = 0.88      # verbo lematizado por spaCy
_CONFIDENCE_CONLANG = 0.92          # verbo de conlang (definido por el autor)
_CONFIDENCE_NO_VERB = 0.35          # sin verbo claro


class VerbClassifier:
    """
    Clasifica el tipo de presencia de una oración usando spaCy.

    Uso:
        classifier = VerbClassifier(nlp, conlang_vocab)
        ptype, confidence, verb = classifier.classify(sentence_doc)
    """

    def __init__(self, nlp, conlang_vocab: ConlangVocab):
        """
        Args:
            nlp: Instancia de spaCy cargada por _spacy_singleton.get_nlp().
            conlang_vocab: Vocabulario personalizado del universo.
        """
        self._nlp = nlp
        self._conlang = conlang_vocab

    def classify_sentence(
        self,
        sentence: str,
    ) -> tuple[str, float, str]:
        """
        Clasifica el tipo de presencia para una oración completa.

        Pipeline:
          1. Vocabulario conlang (exact match, máxima prioridad)
          2. spaCy lematización de verbos → consulta VERB_TYPE_MAP
          3. Ajuste por preposición para verbos ambiguos
          4. Fallback: "present" con confianza baja

        Args:
            sentence: Oración de texto plano normalizada.

        Returns:
            Tupla (presence_type, confidence, verb_matched).
            Si es "referenced", confidence = 0.0 (ignorar).
        """
        norm = normalize(sentence.lower())

        # ── 1. Conlang: búsqueda por token antes de spaCy ─────────────────────
        # Verificamos palabra por palabra porque spaCy no conoce el conlang
        for token_text in norm.split():
            # Limpiar signos de puntuación adyacentes
            clean = token_text.strip(".,;:!?¿¡\"'«»—")
            if not clean:
                continue
            conlang_type = self._conlang.classify(clean)
            if conlang_type:
                log.debug("Conlang match: '%s' → %s", clean, conlang_type)
                return conlang_type, _CONFIDENCE_CONLANG, clean

        # ── 2. spaCy: lematizar y clasificar verbos ───────────────────────────
        doc = self._nlp(sentence)

        # Prioridad: departed > referenced > present > transit
        # "referenced" se detecta primero para ignorar recuerdos/pensamientos
        priority_order = ["departed", "referenced", "present", "transit"]
        found: dict[str, tuple[str, str]] = {}  # tipo → (lemma, forma_original)

        for token in doc:
            if token.pos_ != "VERB":
                continue

            lemma = token.lemma_.lower()
            verb_type = VERB_TYPE_MAP.get(lemma)

            if verb_type and verb_type not in found:
                found[verb_type] = (lemma, token.text)
                log.debug(
                    "spaCy: '%s' → lemma '%s' → %s",
                    token.text, lemma, verb_type
                )

        for ptype in priority_order:
            if ptype in found:
                lemma, original = found[ptype]
                if ptype == "referenced":
                    return "referenced", 0.0, original
                confidence = _adjust_confidence_by_preposition(
                    doc, original, ptype
                )
                return ptype, confidence, original

        # ── 3. Sin verbo clasificado ──────────────────────────────────────────
        return "present", _CONFIDENCE_NO_VERB, ""


def _adjust_confidence_by_preposition(doc, verb_text: str, ptype: str) -> float:
    """
    Ajusta la confianza según la preposición que sigue al verbo en el doc.
    spaCy nos da acceso a la estructura del doc para buscar dependencias.

    "partir hacia Lumina" → transit en realidad (rebajar confianza de departed)
    "ir de Lumina" → departed en realidad (rebajar confianza de transit)
    """
    for i, token in enumerate(doc):
        if token.text.lower() != verb_text.lower():
            continue
        # Mirar las siguientes 3 palabras buscando preposición
        next_tokens = [t.text.lower() for t in doc[i + 1: i + 4]]
        first_prep = next_tokens[0] if next_tokens else ""

        if ptype == "departed" and first_prep in DESTINATION_PREPS:
            return _CONFIDENCE_SPACY_LEMMA * 0.65  # reducida
        if ptype == "transit" and first_prep in ORIGIN_PREPS:
            return _CONFIDENCE_SPACY_LEMMA * 0.65  # reducida

        return _CONFIDENCE_SPACY_LEMMA

    return _CONFIDENCE_SPACY_LEMMA
