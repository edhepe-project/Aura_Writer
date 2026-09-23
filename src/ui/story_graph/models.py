"""
Constantes, colores y utilidades para el Grafo del Cronograma Narrativo.
"""

# Estados del bloque y sus paletas
STATUS_CONFIG = {
    "idea": {
        "label": "Idea",
        "bg_color": "#2c2c2e",
        "border_color": "#8e8e93",
        "text_color": "#ebebf5",
        "badge": "💡"
    },
    "esbozado": {
        "label": "Esbozado",
        "bg_color": "#1c2b3a",
        "border_color": "#0a84ff",
        "text_color": "#64d2ff",
        "badge": "📝"
    },
    "listo": {
        "label": "Listo",
        "bg_color": "#1b3322",
        "border_color": "#30d158",
        "text_color": "#30d158",
        "badge": "✅"
    },
    "escrito": {
        "label": "Escrito",
        "bg_color": "#3a3018",
        "border_color": "#ffd60a",
        "text_color": "#ffd60a",
        "badge": "📖"
    }
}

# Tonos narrativos con colores distintivos
TONE_CONFIG = {
    "misterioso": {"label": "Misterioso", "color": "#bf5af2"},
    "tenso": {"label": "Tenso", "color": "#ff453a"},
    "epico": {"label": "Épico", "color": "#ff9f0a"},
    "lirico": {"label": "Lírico", "color": "#64d2ff"},
    "tragico": {"label": "Trágico", "color": "#ff375f"},
    "revelacion": {"label": "Revelación", "color": "#ffd60a"},
    "neutro": {"label": "Neutro", "color": "#98989d"},
}

# Tipos de arco / conexiones causales
ARC_TYPE_CONFIG = {
    "main": {
        "label": "Secuencia Principal",
        "color": "#e5e5ea",
        "style": "solid",
        "width": 2.5
    },
    "branch": {
        "label": "Ramificación / Decisión",
        "color": "#0a84ff",
        "style": "dash",
        "width": 2.0
    },
    "parallel": {
        "label": "Trama Paralela",
        "color": "#bf5af2",
        "style": "dot",
        "width": 2.0
    },
    "flashback": {
        "label": "Flashback / Antecedente",
        "color": "#ff9f0a",
        "style": "dashdot",
        "width": 2.0
    }
}
