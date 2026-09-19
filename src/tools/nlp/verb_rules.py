"""
verb_rules.py — Diccionario de verbos clasificados por tipo de presencia.
Responsabilidad única: contener SOLO los datos de verbos, sin lógica.

IMPORTANTE: Todos los verbos están en INFINITIVO.
- En Fase 1 se comparan con texto normalizado en minúsculas.
- En Fase 2 (spaCy), el lematizador convierte cualquier conjugación al infinitivo
  automáticamente antes de consultar este diccionario.

Categorías:
  present    → el personaje está físicamente en el lugar
  transit    → el personaje se desplaza hacia el lugar (aún no ha llegado)
  departed   → el personaje acaba de salir/abandonar el lugar
  referenced → el lugar solo se menciona cognitiva o referencialmente
"""
from __future__ import annotations

# ── Verbos de PRESENCIA física ────────────────────────────────────────────────
# El sujeto está o se encuentra activamente en el lugar.
PRESENT_VERBS: frozenset[str] = frozenset({
    "llegar", "arribar", "entrar", "ingresar",
    "estar", "encontrarse", "hallarse", "situarse", "ubicarse",
    "permanecer", "quedarse", "instalarse", "asentarse", "establecerse",
    "vivir", "habitar", "residir", "morar",
    "acampar", "refugiarse", "hospedarse", "alojarse", "pernoctar",
    "detenerse", "descansar", "parar",
    "caminar", "andar", "vagar", "recorrer", "atravesar", "cruzar",
    "explorar", "inspeccionar", "visitar",
    "aparecer", "presentarse", "asomarse",
    "trabajar", "operar", "actuar",          # implican presencia sostenida
})

# ── Verbos de TRÁNSITO ────────────────────────────────────────────────────────
# El sujeto se mueve HACIA el lugar pero no ha llegado todavía.
TRANSIT_VERBS: frozenset[str] = frozenset({
    "dirigirse", "encaminarse", "desplazarse",
    "viajar", "marchar", "avanzar", "acercarse", "aproximarse",
    "cabalgar", "navegar", "volar", "correr",   # verbos de movimiento + "hacia/rumbo a"
    "ir", "moverse", "trasladarse",
    "partir", "salir",                           # ambiguos: con "hacia" = transit, con "de" = departed
    "huir", "escapar", "alejarse",               # ambiguos: con "hacia" = transit
})

# ── Verbos de SALIDA ─────────────────────────────────────────────────────────
# El sujeto deja o abandona el lugar.
DEPARTED_VERBS: frozenset[str] = frozenset({
    "salir", "partir", "abandonar", "marcharse", "irse",
    "alejarse", "retirarse", "huir", "escapar", "desertar",
    "dejar", "evacuar", "exiliarse",
})

# ── Verbos de REFERENCIA cognitiva/emocional ─────────────────────────────────
# El lugar se menciona pero el sujeto NO está físicamente allí.
REFERENCED_VERBS: frozenset[str] = frozenset({
    "recordar", "rememorar", "evocar",
    "pensar", "imaginar", "soñar", "fantasear",
    "hablar", "mencionar", "comentar", "describir", "narrar", "contar",
    "conocer", "saber",
    "añorar", "extrañar", "desear", "anhelar",
    "escuchar", "oír", "leer",
    "temer", "odiar", "amar",                    # sentimientos hacia un lugar
    "planear", "querer", "pretender", "intentar", # intención futura
})

# ── Preposiciones de DESTINO (refuerzan transit/present) ─────────────────────
# Si un verbo ambiguo va seguido de estas preposiciones → probablemente transit/present
DESTINATION_PREPS: frozenset[str] = frozenset({
    "a", "hacia", "hasta", "en", "dentro", "rumbo",
})

# ── Preposiciones de ORIGEN (refuerzan departed) ─────────────────────────────
# Si un verbo ambiguo va seguido de estas preposiciones → probablemente departed
ORIGIN_PREPS: frozenset[str] = frozenset({
    "de", "desde", "fuera",
})

# ── Mapa consolidado para consulta rápida ────────────────────────────────────
VERB_TYPE_MAP: dict[str, str] = {
    **{v: "present"    for v in PRESENT_VERBS},
    **{v: "transit"    for v in TRANSIT_VERBS},
    **{v: "departed"   for v in DEPARTED_VERBS},
    **{v: "referenced" for v in REFERENCED_VERBS},
}
# Nota: verbos en múltiples sets (salir, huir...) quedan con el tipo del set procesado
# último (departed > transit > referenced > present). Se resuelve por contexto en Fase 3.
