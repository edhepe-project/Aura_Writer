"""
__init__.py — Exports públicos del módulo tools.nlp
"""
from tools.nlp.presence_analyzer import PresenceAnalyzer
from tools.nlp.entity_detector import EntityDetector, EntitySpan, DetectionResult
from tools.nlp.conlang_vocab import ConlangVocab
from tools.nlp.normalizer import normalize, normalize_apostrophes
from tools.nlp.text_cleaner import html_to_text
from tools.nlp._spacy_singleton import is_spacy_available
from tools.nlp.sentence_filter import SentenceFilter
from tools.nlp.fuzzy_matcher import FuzzyMatcher
from tools.nlp.subject_extractor import SubjectExtractor
from tools.nlp.hierarchy_engine import HierarchyEngine
from tools.nlp.presence_merger import PresenceMerger

__all__ = [
    "PresenceAnalyzer",
    "EntityDetector",
    "EntitySpan",
    "DetectionResult",
    "ConlangVocab",
    "normalize",
    "normalize_apostrophes",
    "html_to_text",
    "is_spacy_available",
    "SentenceFilter",
    "FuzzyMatcher",
    "SubjectExtractor",
    "HierarchyEngine",
    "PresenceMerger",
]
