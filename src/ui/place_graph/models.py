"""
models.py — Paletas, constantes y estilos visuales para el Grafo de Lugares.
"""
from __future__ import annotations

# Paleta de colores por categoría de Lugar (estilo Apple Dark & Gema)
PLACE_CATEGORY_COLORS: dict[str, str] = {
    "Reino / Nación":       "#ffd60a",   # dorado soberano
    "Ciudad / Poblado":     "#0a84ff",   # azul urbano
    "Fortaleza / Castillo": "#ff453a",   # rojo fortaleza
    "Taberna / Interior":   "#ff9f0a",   # ámbar cálido
    "Mazmorra / Cueva":     "#bf5af2",   # violeta oscuro
    "Naturaleza / Bosque":  "#30d158",   # verde esmeralda
    "Región Mágica":        "#64d2ff",   # cian etéreo
    "Planeta / Espacio":    "#5e5ce6",   # índigo galáctico
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
