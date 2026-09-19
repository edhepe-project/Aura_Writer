"""
Test funcional del pipeline de Presencia (Fase 1).
Ejecutar con: python scratch/test_presence_phase1.py
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "src")

from core.models import Character, Place, Chapter, CustomVocabularyEntry
from tools.nlp import PresenceAnalyzer

# ── Datos de prueba ───────────────────────────────────────────────────────────
char  = Character(name="Kaelen")
char2 = Character(name="Syl")
place  = Place(name="Ciudad de Lumina", aliases=["la ciudad del cafe", "Lumina"])
place2 = Place(name="Taberna del Dragon")
vocab  = CustomVocabularyEntry(word="vel'thar", presence_type="present",
                               notes="conlang: llegar/entrar")
chapter = Chapter(title="Capitulo 1", id="chap-001")

PASS = "\033[92m✅ PASS\033[0m"
FAIL = "\033[91m❌ FAIL\033[0m"

def check(label, condition):
    print(f"  {PASS if condition else FAIL}  {label}")

print("\n═══════════════ TEST: Sistema de Presencia Fase 1 ═══════════════\n")

# ── Test 1: Verbo español normal ──────────────────────────────────────────────
analyzer = PresenceAnalyzer([char], [place, place2], [vocab])
html = "<p>Kaelen llegó a la Ciudad de Lumina al anochecer.</p>"
results = analyzer.analyze_chapter(chapter, html)
print("Test 1 — Verbo español ('llego'):")
check("Detecta 1 presencia", len(results) == 1)
check("Tipo: present", results[0].presence_type == "present" if results else False)
check("Confidence >= 0.70", results[0].confidence >= 0.70 if results else False)
check("character_id correcto", results[0].character_id == char.id if results else False)
check("place_id correcto", results[0].place_id == place.id if results else False)

# ── Test 2: Alias de lugar ────────────────────────────────────────────────────
html = "<p>Kaelen entró a la ciudad del cafe sin mirar atrás.</p>"
results = analyzer.analyze_chapter(chapter, html)
print("\nTest 2 — Alias de lugar ('la ciudad del cafe' → Ciudad de Lumina):")
check("Detecta 1 presencia por alias", len(results) == 1)
check("place_id mapeado correctamente al ID de Lumina",
      results[0].place_id == place.id if results else False)

# ── Test 3: Verbo de conlang ─────────────────────────────────────────────────
analyzer2 = PresenceAnalyzer([char2], [place], [vocab])
html = "<p>Syl vel'thar a la Ciudad de Lumina con sigilo.</p>"
results = analyzer2.analyze_chapter(chapter, html)
print("\nTest 3 — Verbo de conlang ('vel'thar'):")
check("Detecta 1 presencia", len(results) == 1)
check("Verbo matched = vel'thar",
      results[0].verb_matched == "vel'thar" if results else False)
check("Tipo: present", results[0].presence_type == "present" if results else False)
check("Confidence >= 0.80 (conlang = mayor confianza)",
      results[0].confidence >= 0.80 if results else False)

# ── Test 4: Narrador omnisciente sin personaje (debe ignorarse) ───────────────
html = "<p>Las torres de la Ciudad de Lumina se alzaban en el horizonte brumoso.</p>"
results = analyzer.analyze_chapter(chapter, html)
print("\nTest 4 — Narrador omnisciente (sin personaje como sujeto):")
check("0 presencias detectadas (narración pura)", len(results) == 0)

# ── Test 5: Referencia cognitiva (debe ignorarse) ─────────────────────────────
html = "<p>Kaelen recordaba la Ciudad de Lumina con nostalgia infinita.</p>"
results = analyzer.analyze_chapter(chapter, html)
print("\nTest 5 — Referencia cognitiva ('recordaba'):")
check("0 presencias físicas (solo referencia)", len(results) == 0)

# ── Test 6: Verbo de salida ───────────────────────────────────────────────────
html = "<p>Kaelen abandonó la Ciudad de Lumina sin mirar atrás.</p>"
results = analyzer.analyze_chapter(chapter, html)
print("\nTest 6 — Verbo de salida ('abandono'):")
check("Detecta 1 presencia", len(results) == 1)
check("Tipo: departed", results[0].presence_type == "departed" if results else False)

# ── Test 7: HTML con múltiples párrafos ──────────────────────────────────────
html = """
<h1>Capitulo 1</h1>
<p>La ciudad estaba en calma.</p>
<p>Kaelen llegó a la Taberna del Dragon después de días de camino.</p>
<p>Las estrellas brillaban sobre Ciudad de Lumina, lejos.</p>
"""
results = analyzer.analyze_chapter(chapter, html)
print("\nTest 7 — HTML con múltiples párrafos:")
check("Detecta presencia en la Taberna",
      any(r.place_id == place2.id for r in results))
check("NO detecta presencia en Lumina (solo narración sin Kaelen como sujeto)",
      not any(r.place_id == place.id for r in results))

# ── Test 8: Normalización de apóstrofes ──────────────────────────────────────
vocab_curly = CustomVocabularyEntry(word="vel\u2019thar", presence_type="transit")
analyzer3 = PresenceAnalyzer([char], [place], [vocab_curly])
html = "<p>Kaelen vel\u2019thar hacia Ciudad de Lumina.</p>"  # apóstrofe curvo
results = analyzer3.analyze_chapter(chapter, html)
print("\nTest 8 — Normalización de apóstrofe curvo → recto:")
check("Detecta verbo con apóstrofe curvo normalizado", len(results) == 1)

print("\n════════════════════════════════════════════════════════════════\n")
