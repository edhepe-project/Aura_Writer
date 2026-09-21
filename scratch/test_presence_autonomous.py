"""
Test integral del motor autónomo de Presencia NLP:
- Resolución anafórica / pronombres (ContextTracker)
- Coordinación de grupos / viajes conjuntos (GroupCoordinator)
- Inferencia de punto de vista en 1ra persona (POVInferrer)
- Regla de ubicación única y prioridad cronológica
"""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "src")

from core.models import Character, Place, Chapter, CustomVocabularyEntry
from tools.nlp import PresenceAnalyzer

PASS = "\033[92m✅ PASS\033[0m"
FAIL = "\033[91m❌ FAIL\033[0m"

def check(label, condition):
    print(f"  {PASS if condition else FAIL}  {label}")

print("\n═══════════════ TEST: Motor Autónomo de Presencia NLP ═══════════════\n")

# Datos de prueba
kaelen = Character(name="Kaelen", gender="M")
lyra = Character(name="Lyra", gender="F")
coralis = Character(name="Coralis", gender="M")

taberna = Place(name="Taberna del Dragón")
bosque = Place(name="Bosque de las Hadas")
islas = Place(name="Islas Vortex")
ciudad = Place(name="Ciudad de Lumina")

# ── Test 1: Resolución de Pronombres y Sujeto Activo ───────────────────────────
print("Test 1 — Resolución de Pronombre ('Kaelen observó el mapa... él entró en la Taberna'):")
analyzer = PresenceAnalyzer([kaelen, lyra], [taberna, bosque, ciudad], [])
chap1 = Chapter(title="Capítulo 1", id="chap-001")
html1 = "<p>Kaelen observó el mapa detenidamente. Al anochecer, él entró en la Taberna del Dragón.</p>"
results1 = analyzer.analyze_chapter(chap1, html1)

check("Detecta presencia mediante resolución de pronombre", len(results1) >= 1)
if results1:
    check("Personaje asignado es Kaelen", results1[0].character_id == kaelen.id)
    check("Lugar asignado es Taberna del Dragón", results1[0].place_id == taberna.id)
    check("Tipo es present", results1[0].presence_type == "present")

# ── Test 2: Coordinación de Grupos / Viaje Conjunto ────────────────────────────
print("\nTest 2 — Coordinación de Grupos ('Kaelen y Lyra llegaron al Bosque de las Hadas'):")
html2 = "<p>Kaelen y Lyra llegaron al Bosque de las Hadas tras un largo viaje.</p>"
results2 = analyzer.analyze_chapter(chap1, html2)

char_ids_in_results = [r.character_id for r in results2 if r.place_id == bosque.id]
check("Detecta presencias para ambos integrantes del grupo", len(char_ids_in_results) >= 2)
check("Kaelen está presente en el Bosque", kaelen.id in char_ids_in_results)
check("Lyra está presente en el Bosque", lyra.id in char_ids_in_results)

# ── Test 3: Inferencia de POV en 1ra Persona ───────────────────────────────────
print("\nTest 3 — Inferencia de POV 1ra persona ('Llegué a las Islas Vortex'):")
chap_pov = Chapter(title="Diario de Coralis", id="chap-002", pov=coralis.id)
analyzer_pov = PresenceAnalyzer([coralis], [islas, taberna], [])
html3 = "<p>El barco zarpó de madrugada. Finalmente llegué a las Islas Vortex antes del mediodía.</p>"
results3 = analyzer_pov.analyze_chapter(chap_pov, html3)

check("Detecta presencia para el protagonista del POV (1ra persona)", len(results3) >= 1)
if results3:
    check("Personaje inferido es Coralis", results3[0].character_id == coralis.id)
    check("Lugar asignado es Islas Vortex", results3[0].place_id == islas.id)

# ── Test 4: Regla de Ubicación Única en la misma escena ─────────────────────────
print("\nTest 4 — Regla de Ubicación Única (movimiento secuencial en un capítulo):")
html4 = "<p>Kaelen llegó a la Ciudad de Lumina. Más tarde, viajó al Bosque de las Hadas.</p>"
results4 = analyzer.analyze_chapter(chap1, html4)
# En el capítulo, la regla de ubicación única hace que solo quede exactamente 1 presencia para Kaelen: su destino final
kaelen_presences = [r for r in results4 if r.character_id == kaelen.id]
check("Exactamente 1 ubicación final para Kaelen (Regla de Unicidad)", len(kaelen_presences) == 1)
if kaelen_presences:
    check("La ubicación final consolidada es el Bosque de las Hadas", kaelen_presences[0].place_id == bosque.id)

print("\n═══════════════════════════════════════════════════════════════════════\n")
