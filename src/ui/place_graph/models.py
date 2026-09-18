"""
models.py — Paletas, jerarquías planetarias y estilos visuales para el Grafo de Lugares.
"""
from __future__ import annotations

# Jerarquía Astronómica / Cosmológica
# Nivel 0 (Sol Central): Planeta / Espacio
# Nivel 1 (Planetas Mayores): Reino / Nación
# Nivel 2 (Sistemas Urbanos): Ciudad / Poblado
# Nivel 3 (Lunas / Puntos de Interés): Fortaleza, Taberna, Mazmorra, Naturaleza, Región Mágica, Otro
CATEGORY_TIERS: dict[str, int] = {
    "Planeta / Espacio":    0,  # Sol / Macro-Mundo
    "Reino / Nación":       1,  # Órbita Primaria (Nación)
    "Ciudad / Poblado":     2,  # Órbita Secundaria (Ciudad)
    "Fortaleza / Castillo": 3,  # Satélites / Estancias de la Ciudad
    "Taberna / Interior":   3,
    "Mazmorra / Cueva":     3,
    "Naturaleza / Bosque":  3,
    "Región Mágica":        3,
    "Otro":                 3,
}

# Radios visuales por Tier
TIER_NODE_RADIUS: dict[int, float] = {
    0: 42.0,  # Sol / Planeta Macro (máxima presencia)
    1: 32.0,  # Nación / Reino
    2: 25.0,  # Ciudad / Poblado
    3: 18.0,  # Castillo, Taberna, Mazmorra, Bosque...
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
