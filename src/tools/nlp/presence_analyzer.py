"""
presence_analyzer.py — Orquestador principal del pipeline de detección.
Responsabilidad: coordinar text_cleaner → normalizer → entity_detector → verb_classifier
y producir lista de CharacterPresence.

Fase 1: FlashText + patrones regex de conjugación (sin spaCy).
Fase 2: FlashText + spaCy lematización real (si está disponible).
Fallback automático: si spaCy no está instalado, usa Fase 1 silenciosamente.
"""
from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from core.models import CharacterPresence
from tools.nlp.text_cleaner import html_to_text
from tools.nlp.normalizer import normalize
from tools.nlp.verb_rules import VERB_TYPE_MAP, DESTINATION_PREPS, ORIGIN_PREPS
from tools.nlp.conlang_vocab import ConlangVocab
from tools.nlp.entity_detector import EntityDetector, DetectionResult

if TYPE_CHECKING:
    from core.models import Character, Place, CustomVocabularyEntry, Chapter

log = logging.getLogger(__name__)

# Confianza base por método de detección
_CONFIDENCE_RULE_MATCH  = 0.70   # verbo por regex (Fase 1)
_CONFIDENCE_CONLANG_MATCH = 0.80 # verbo de conlang
_CONFIDENCE_NO_VERB     = 0.40   # sin verbo claro (sugerencia)

# ── Detectar disponibilidad de spaCy en tiempo de importación ────────────────
try:
    from tools.nlp._spacy_singleton import is_spacy_available
    from tools.nlp.verb_classifier import VerbClassifier
    _SPACY_READY = is_spacy_available()
except ImportError:
    _SPACY_READY = False
    VerbClassifier = None

from tools.nlp.sentence_filter import SentenceFilter
from tools.nlp.fuzzy_matcher import FuzzyMatcher
from tools.nlp.subject_extractor import SubjectExtractor
from tools.nlp.presence_merger import PresenceMerger

if _SPACY_READY:
    log.debug("PresenceAnalyzer: usando Fase 2/3 (spaCy + Robustez)")
else:
    log.debug("PresenceAnalyzer: usando Fase 1 (regex, spaCy no disponible)")


class PresenceAnalyzer:
    """
    Analiza el HTML de un capítulo y produce una lista de CharacterPresence.

    Pipeline (Fase 3 con robustez total):
      1. html_to_text       → texto plano
      2. normalize          → estandarizar caracteres especiales
      3. SentenceFilter     → descartar diálogos puros / referencias cognitivas iniciales
      4. EntityDetector     → encontrar personajes y lugares (FlashText + Fuzzy fallback)
      5. VerbClassifier     → determinar tipo de presencia con spaCy
      6. SubjectExtractor   → verificar relación sujeto-verbo
      7. PresenceMerger     → deduplicar y consolidar presencias del capítulo
    """

    def __init__(
        self,
        characters: list["Character"],
        places: list["Place"],
        custom_vocabulary: list["CustomVocabularyEntry"],
    ):
        self._detector = EntityDetector(characters, places)
        self._conlang = ConlangVocab(custom_vocabulary)
        self._char_map = {c.id: c for c in characters}
        self._place_map = {p.id: p for p in places}

        # Fuzzy Matcher para nombres con posibles erratas
        self._fuzzy_matcher = FuzzyMatcher()
        candidate_dict = {}
        for c in characters:
            candidate_dict[c.name] = c.id
        for p in places:
            candidate_dict[p.name] = p.id
            if hasattr(p, "aliases") and p.aliases:
                for alias in p.aliases:
                    candidate_dict[alias] = p.id
        self._fuzzy_matcher.set_candidates(candidate_dict)

        # Inicializar VerbClassifier de Fase 2 si spaCy está disponible
        self._verb_classifier = None
        if _SPACY_READY and VerbClassifier is not None:
            try:
                from tools.nlp._spacy_singleton import get_nlp
                nlp = get_nlp()
                self._verb_classifier = VerbClassifier(nlp, self._conlang)
                log.info("VerbClassifier (spaCy) inicializado correctamente")
            except Exception as e:
                log.warning(
                    "No se pudo inicializar spaCy VerbClassifier: %s "
                    "(usando Fase 1 como fallback)", e
                )

    def analyze_chapter(
        self,
        chapter: "Chapter",
        html_content: str,
    ) -> list[CharacterPresence]:
        """
        Analiza el HTML de un capítulo y retorna las presencias detectadas.
        """
        if not html_content or not html_content.strip():
            return []

        # ── Paso 1-2: Limpiar y normalizar ────────────────────────────────────
        plain_text = html_to_text(html_content)
        plain_text = normalize(plain_text)

        if not plain_text.strip():
            return []

        # ── Paso 3: Detectar entidades por oración ────────────────────────────
        detection_results = self._detector.detect_in_text(plain_text)

        # ── Paso 4-5: Clasificar y construir presencias ───────────────────────
        raw_presences: list[CharacterPresence] = []

        for detection in detection_results:
            if not detection.is_candidate:
                continue

            # Filtro de oración (diálogos directos / menciones cognitivas)
            should_proc, _ = SentenceFilter.evaluate_sentence(detection.sentence)
            if not should_proc:
                continue

            new_presences = self._process_detection(detection, chapter)
            raw_presences.extend(new_presences)

        # ── Paso 6: Deduplicación y consolidación ──────────────────────────
        presences = PresenceMerger.merge_chapter_presences(raw_presences)

        log.debug(
            "Capítulo '%s': %d oraciones candidatas, %d presencias detectadas",
            chapter.title,
            sum(1 for d in detection_results if d.is_candidate),
            len(presences),
        )
        return presences

    def _process_detection(
        self,
        detection: DetectionResult,
        chapter: "Chapter",
    ) -> list[CharacterPresence]:
        """
        Procesa una oración candidata (con personaje + lugar) y genera presencias.
        """
        presences = []

        for char_span in detection.characters:
            for place_span in detection.places:
                context = detection.sentence

                # ── Fase 2: usar spaCy VerbClassifier si está disponible ──────
                if self._verb_classifier is not None:
                    presence_type, confidence, verb_matched = \
                        self._verb_classifier.classify_sentence(context)
                else:
                    # ── Fase 1 fallback: regex de conjugación ─────────────────
                    presence_type, confidence, verb_matched = self._classify_verb(
                        context, char_span, place_span
                    )

                # Ignorar referencias cognitivas — el personaje no está allí
                if presence_type == "referenced":
                    continue

                presences.append(CharacterPresence(
                    character_id=char_span.entity_id,
                    place_id=place_span.entity_id,
                    chapter_id=chapter.id,
                    in_world_order=getattr(chapter, "in_world_order", 0),
                    presence_type=presence_type,
                    confidence=confidence,
                    matched_text=context[:200],   # max 200 chars para el log
                    verb_matched=verb_matched,
                    is_manual=False,
                ))

        return presences

    def _classify_verb(
        self,
        sentence: str,
        char_span,
        place_span,
    ) -> tuple[str, float, str]:
        """
        Clasifica el tipo de presencia buscando verbos en la oración.

        Estrategia Fase 1 (sin spaCy):
          1. Buscar verbo de conlang exacto → alta confianza
          2. Buscar formas conjugadas del diccionario → confianza media
          3. Sin verbo detectado → "present" con confianza baja (conservador)

        Returns:
            Tupla (presence_type, confidence, verb_matched)
        """
        norm_sentence = normalize(sentence.lower())

        # ── 1. Vocabulario conlang (máxima prioridad) ─────────────────────────
        words = re.findall(r"[\w·']+", norm_sentence)
        for word in words:
            conlang_type = self._conlang.classify(word)
            if conlang_type:
                return conlang_type, _CONFIDENCE_CONLANG_MATCH, word

        # ── 2. Buscar verbos con variantes conjugadas ─────────────────────────
        # En Fase 1 sin spaCy, generamos patrones regex que capturan las
        # conjugaciones más comunes de cada infinitivo (-ar/-er/-ir).
        priority = ["departed", "referenced", "present", "transit"]
        found: dict[str, str] = {}   # tipo → verbo/forma encontrada

        for verb, verb_type in VERB_TYPE_MAP.items():
            pattern = _build_conjugation_pattern(verb)
            m = re.search(pattern, norm_sentence)
            if m:
                found[verb_type] = m.group(0)

        for ptype in priority:
            if ptype in found:
                matched_form = found[ptype]
                # Referencias cognitivas → ignorar (personaje no está físicamente)
                if ptype == "referenced":
                    return "referenced", 0.0, matched_form
                confidence = _CONFIDENCE_RULE_MATCH
                if ptype in ("departed", "transit"):
                    confidence = self._adjust_by_preposition(
                        norm_sentence, matched_form, ptype
                    )
                return ptype, confidence, matched_form

        # ── 3. Sin verbo detectado — sugerencia con baja confianza ───────────
        return "present", _CONFIDENCE_NO_VERB, ""

    def _adjust_by_preposition(
        self,
        sentence: str,
        verb: str,
        current_type: str,
    ) -> float:
        """
        Ajusta la confianza de verbos ambiguos (salir, partir, ir...)
        según la preposición que sigue al verbo.
        """
        match = re.search(r"\b" + re.escape(verb) + r"\b", sentence)
        if not match:
            return _CONFIDENCE_RULE_MATCH

        post = sentence[match.end():match.end() + 30].strip()
        first_word = post.split()[0] if post.split() else ""

        if current_type == "departed" and first_word in DESTINATION_PREPS:
            return _CONFIDENCE_RULE_MATCH * 0.6
        if current_type == "transit" and first_word in ORIGIN_PREPS:
            return _CONFIDENCE_RULE_MATCH * 0.6

        return _CONFIDENCE_RULE_MATCH


# ─────────────────────────────────────────────────────────────────────────────
# Generador de patrones de conjugación para Fase 1 (sin spaCy)
# ─────────────────────────────────────────────────────────────────────────────

def _build_conjugation_pattern(infinitive: str) -> str:
    """
    Genera un patrón regex que detecta las formas conjugadas más comunes
    de un infinitivo español. Estrategia conservadora: solo sufijos de alta
    frecuencia para minimizar falsos positivos.

    Soporta verbos -ar, -er, -ir.
    En Fase 2, spaCy reemplaza esto con lematización real.
    """
    if infinitive.endswith("ar"):
        stem = infinitive[:-2]
        # Presente, pretérito, imperfecto, subjuntivo, gerundio, imperativo
        suffixes = (
            "o", "as", "a", "amos", "an",           # presente
            "e", "es", "emos", "en",                 # subjuntivo
            r"[eé]", r"aste", r"[oó]", "amos", "aron",  # pretérito
            "aba", "abas", "aban",                   # imperfecto
            "ando",                                  # gerundio
            "ado", "ada",                            # participio
        )
    elif infinitive.endswith("er"):
        stem = infinitive[:-2]
        suffixes = (
            "o", "es", "e", "emos", "en",
            r"[íi]", "iste", r"[ióo]", "imos", "ieron",
            "ía", "ías", "ían",
            "iendo",
            "ido", "ida",
        )
    elif infinitive.endswith("ir"):
        stem = infinitive[:-2]
        suffixes = (
            "o", "es", "e", "imos", "en",
            r"[íi]", "iste", r"[ióo]", "imos", "ieron",
            "ía", "ías", "ían",
            "iendo",
            "ido", "ida",
        )
    else:
        # Verbo irregular o forma no reconocida → buscar tal cual
        return r"\b" + re.escape(infinitive) + r"\b"

    # Escapar el stem (puede contener caracteres especiales en conlang)
    escaped_stem = re.escape(stem)
    # Construir alternativas: stem + cada sufijo
    alts = "|".join(f"{escaped_stem}{s}" for s in suffixes)
    # También incluir el infinitivo completo
    alts += f"|{re.escape(infinitive)}"
    return r"\b(?:" + alts + r")\b"

