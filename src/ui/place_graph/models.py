"""
models.py — Paletas, jerarquías planetarias y estilos visuales para el Grafo de Lugares.
"""
from __future__ import annotations

# Jerarquía Astronómica / Cosmológica Multiescala
# Nivel 0 (Sol Central): Planeta / Espacio (Macro-Cosmos)
# Nivel 1 (Planetas Mayores): Reino / Nación
# Nivel 2 (Grandes Provincias / Territorios): Región Mágica, Naturaleza / Bosque
# Nivel 3 (Sistemas Urbanos): Ciudad / Poblado
# Nivel 4 (Satélites / Puntos de Interés Locales): Fortaleza / Castillo, Mazmorra / Cueva, Taberna / Interior, Otro
CATEGORY_TIERS: dict[str, int] = {
    "Planeta / Espacio":    0,  # Sol / Macro-Mundo (R=42px)
    "Reino / Nación":       1,  # Órbita Primaria Soberana (R=34px)
    "Región Mágica":        2,  # Macro-Territorio / Provincia (R=28px)
    "Naturaleza / Bosque":  2,  # Entornos naturales extensos (R=28px)
    "Ciudad / Poblado":     3,  # Núcleo Urbano (R=22px)
    "Fortaleza / Castillo": 4,  # Estancia / Satélite Local (R=16px)
    "Mazmorra / Cueva":     4,  # Punto de Interés / Mazmorra (R=16px)
    "Taberna / Interior":   4,  # Micro-Interior / Local (R=15px)
    "Otro":                 4,  # PDI Genérico (R=15px)
}

# Radios visuales escalonados por Tier
TIER_NODE_RADIUS: dict[int, float] = {
    0: 42.0,  # Sol / Planeta Macro
    1: 34.0,  # Nación / Reino
    2: 28.0,  # Región / Provincia / Bosque Mayor
    3: 22.0,  # Ciudad / Poblado
    4: 16.0,  # Puntos de interés locales (Castillos, Mazmorras, Tabernas)
}

# Paleta de colores por categoría de Lugar (estilo Apple Dark & Gema)
PLACE_CATEGORY_COLORS: dict[str, str] = {
    "Planeta / Espacio":    "#5e5ce6",   # índigo galáctico
    "Reino / Nación":       "#ffd60a",   # dorado soberano
    "Ciudad / Poblado":     "#0a84ff",   # azul urbano
    "Fortaleza / Castillo": "#ff453a",   # rojo fortaleza
    "Taberna / Interior":   "#ff9f0a",   # ámbar cálido
    "Mazmorra / Cueva":     "#bf5af2",   # violeta oscuro
    "Naturaleza / Bosque":  "#30d158",   # verde esmeralda
    "Región Mágica":        "#64d2ff",   # cian etéreo
    "Otro":                 "#8e8e93",   # gris neutro
}

# Estilos de aristas por tipo de conexión geográfica
CONNECTION_STYLES: dict[str, dict] = {
    "ruta":      {"color": "#30d158", "glow": "#30d158", "dash": None,             "width": 1.8},
    "frontera":  {"color": "#ff453a", "glow": "#ff453a", "dash": [6.0, 4.0],       "width": 1.8},
    "portal":    {"color": "#bf5af2", "glow": "#bf5af2", "dash": [2.0, 3.0],       "width": 2.0},
    "río":       {"color": "#0a84ff", "glow": "#0a84ff", "dash": [8.0, 3.0],       "width": 1.6},
    "camino":    {"color": "#ffd60a", "glow": "#ffd60a", "dash": [4.0, 4.0],       "width": 1.6},
    "comercio":  {"color": "#ff9f0a", "glow": "#ff9f0a", "dash": None,             "width": 1.8},
    "contiene":  {"color": "#bf5af2", "glow": "#bf5af2", "dash": [3.0, 4.0],       "width": 1.3},
    "otro":      {"color": "#8e8e93", "glow": "#8e8e93", "dash": None,             "width": 1.4},
}
