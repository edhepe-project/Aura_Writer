"""
Constantes, colores y utilidades para el Grafo del Cronograma Narrativo.
"""

# Estados del bloque y sus paletas
STATUS_CONFIG = {
    "idea": {
        "label": "Idea",
        "bg_color": "#2c2c2e",
        "light_bg_color": "#ffffff",
        "border_color": "#8e8e93",
        "text_color": "#ebebf5",
        "light_text_color": "#1c1c1e",
        "badge": "•"
    },
    "esbozado": {
        "label": "Esbozado",
        "bg_color": "#1c2b3a",
        "light_bg_color": "#e0f2fe",
        "border_color": "#0a84ff",
        "text_color": "#64d2ff",
        "light_text_color": "#0369a1",
        "badge": "•"
    },
    "listo": {
        "label": "Listo",
        "bg_color": "#1b3322",
        "light_bg_color": "#dcfce7",
        "border_color": "#30d158",
        "text_color": "#30d158",
        "light_text_color": "#15803d",
        "badge": "•"
    },
    "escrito": {
        "label": "Escrito",
        "bg_color": "#3a3018",
        "light_bg_color": "#fef3c7",
        "border_color": "#ffd60a",
        "text_color": "#ffd60a",
        "light_text_color": "#b45309",
        "badge": "•"
    }
}

# Tonos narrativos con colores distintivos
TONE_CONFIG = {
    "misterioso": {"label": "Misterioso", "color": "#bf5af2", "light_color": "#9333ea"},
    "tenso": {"label": "Tenso", "color": "#ff453a", "light_color": "#dc2626"},
    "epico": {"label": "Épico", "color": "#ff9f0a", "light_color": "#ea580c"},
    "lirico": {"label": "Lírico", "color": "#64d2ff", "light_color": "#0284c7"},
    "tragico": {"label": "Trágico", "color": "#ff375f", "light_color": "#e11d48"},
    "revelacion": {"label": "Revelación", "color": "#ffd60a", "light_color": "#d97706"},
    "neutro": {"label": "Neutro", "color": "#98989d", "light_color": "#6b7280"},
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
