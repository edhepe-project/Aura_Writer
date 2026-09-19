"""
test_presence_phase3.py — Tests específicos para robustez y Phase 3:
- Fuzzy Matching
- AnyTree Jerarquía espacial
- Filtro de diálogos directos vs narrativa
- Fusión de presencias
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, "src")

from core.models import Character, Place, Chapter, CustomVocabularyEntry, CharacterPresence
from tools.nlp.presence_analyzer import PresenceAnalyzer
from tools.nlp.fuzzy_matcher import FuzzyMatcher
from tools.nlp.sentence_filter import SentenceFilter
from tools.nlp.hierarchy_engine import HierarchyEngine
from tools.nlp.presence_merger import PresenceMerger

def test_fuzzy_matching():
    print("\n--- Test Fuzzy Matching ---")
    matcher = FuzzyMatcher(threshold=80.0, min_length=4)
    matcher.set_candidates({
        "Kaelen": "char_1",
        "Ciudad de Lumina": "place_1",
        "Taberna del Dragon": "place_2"
    })

    # Typos
    match1 = matcher.match("Kaeln") # typo in Kaelen
    assert match1 is not None, "Fuzzy match Kaeln -> Kaelen falló"
    assert match1[0] == "char_1"
    print("  ✅ PASS  Typo 'Kaeln' -> 'Kaelen' detectado")

    match2 = matcher.match("Taberna del Dragn")
    assert match2 is not None
    assert match2[0] == "place_2"
    print("  ✅ PASS  Typo 'Taberna del Dragn' -> 'place_2' detectado")

def test_hierarchy_engine():
    print("\n--- Test Hierarchy Engine (AnyTree) ---")
    engine = HierarchyEngine()
    places = [
        Place(id="kingdom_1", name="Reino de Eldoria", parent_place_id=""),
        Place(id="city_1", name="Ciudad de Lumina", parent_place_id="kingdom_1"),
        Place(id="tavern_1", name="Taberna del Dragon", parent_place_id="city_1"),
    ]
    engine.build_from_places(places)

    ancestors = engine.get_ancestors("tavern_1")
    assert "city_1" in ancestors, "city_1 debe ser ancestro de tavern_1"
    assert "kingdom_1" in ancestors, "kingdom_1 debe ser ancestro de tavern_1"
    print("  ✅ PASS  Ancestros de 'Taberna del Dragon':", ancestors)

    descendants = engine.get_descendants("kingdom_1")
    assert "city_1" in descendants and "tavern_1" in descendants
    print("  ✅ PASS  Descendientes de 'Reino de Eldoria':", descendants)

def test_sentence_filter():
    print("\n--- Test Sentence Filter ---")
    # Diálogo directo
    dialogue1 = "—Kaelen llegó a la Ciudad de Lumina —dijo el guardia."
    should_proc1, reason1 = SentenceFilter.evaluate_sentence(dialogue1)
    assert not should_proc1 and reason1 == "dialogue"
    print("  ✅ PASS  Diálogo con raya descartado correctamente")

    # Pensamiento/Cognición
    thought = "Kaelen soñaba con volver a la Ciudad de Lumina."
    should_proc2, reason2 = SentenceFilter.evaluate_sentence(thought)
    assert not should_proc2 and reason2 == "cognitive"
    print("  ✅ PASS  Pensamiento/anhelo descartado correctamente")

    # Narración válida
    narrative = "Kaelen entró en la Ciudad de Lumina con paso firme."
    should_proc3, reason3 = SentenceFilter.evaluate_sentence(narrative)
    assert should_proc3 and reason3 == "valid"
    print("  ✅ PASS  Narración física válida procesada")

def test_presence_merger():
    print("\n--- Test Presence Merger (Regla de Unicidad: 1 personaje = 1 lugar) ---")
    p1 = CharacterPresence(chapter_id="c1", character_id="char_1", place_id="place_1", presence_type="present", confidence=0.7)
    p2 = CharacterPresence(chapter_id="c1", character_id="char_1", place_id="place_1", presence_type="present", confidence=0.9)
    p3 = CharacterPresence(chapter_id="c1", character_id="char_1", place_id="place_2", presence_type="present", confidence=0.8)

    merged = PresenceMerger.merge_chapter_presences([p1, p2, p3])
    assert len(merged) == 1, f"Se esperaba 1 única presencia para char_1 en el capítulo, se obtuvieron {len(merged)}"
    
    # Debe conservar la de mayor confianza (place_1 con 0.9)
    assert merged[0].place_id == "place_1"
    assert merged[0].confidence == 0.9
    print("  ✅ PASS  Unicidad por capítulo: char_1 ubicado exclusivamente en place_1 (confianza 0.9)")

    # Test resolución global entre capítulos (última ubicación cronológica)
    p_cap1 = CharacterPresence(chapter_id="c1", character_id="char_1", place_id="place_1", in_world_order=1, presence_type="present")
    p_cap2 = CharacterPresence(chapter_id="c2", character_id="char_1", place_id="place_2", in_world_order=2, presence_type="present")

    latest = PresenceMerger.get_latest_character_locations([p_cap1, p_cap2])
    assert len(latest) == 1
    assert latest[0].place_id == "place_2"
    print("  ✅ PASS  Unicidad global: char_1 ubicado en su última posición cronológica (place_2 del Cap 2)")

if __name__ == "__main__":
    test_fuzzy_matching()
    test_hierarchy_engine()
    test_sentence_filter()
    test_presence_merger()
    print("\n════════════════════════════════════════════════════════════════")
    print("   TODOS LOS TESTS DE LA FASE 3 PASARON EXITOSAMENTE ✅")
    print("════════════════════════════════════════════════════════════════\n")
