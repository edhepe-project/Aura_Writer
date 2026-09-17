"""
Módulo de Datos, Paletas y Modelos del Grafo de Relaciones.
"""

import math
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QPainterPath
from core.models import Character

# ── Paletas ──────────────────────────────────────────────────────────────────

# Paleta luminosa, rica y distinguible de personajes
CHARACTER_PALETTE = [
    "#f59e0b", "#06b6d4", "#ec4899", "#10b981", "#3b82f6",
    "#8b5cf6", "#f97316", "#14b8a6", "#e11d48", "#84cc16",
    "#0ea5e9", "#d97706", "#6366f1", "#a855f7", "#22c55e",
    "#ef4444", "#eab308", "#0284c7", "#f43f5e", "#10b981",
]

# Aristas finas, limpias y con colores semánticos vivos
RELATION_STYLES: dict[str, dict] = {
    "pareja":       {"color": "#f43f5e", "width": 1.8, "dash": None,           "glow": "#f43f5e"},
    "familiar":     {"color": "#06b6d4", "width": 1.5, "dash": [6, 4],         "glow": "#06b6d4"},
    "descendiente": {"color": "#38bdf8", "width": 1.4, "dash": [3, 4],         "glow": "#38bdf8"},
    "rival":        {"color": "#ef4444", "width": 1.8, "dash": [8, 3, 2, 3], "glow": "#ef4444"},
    "mentor":       {"color": "#a855f7", "width": 1.5, "dash": [10, 3, 2, 3], "glow": "#a855f7"},
    "amigo":        {"color": "#eab308", "width": 1.4, "dash": [5, 4],         "glow": "#eab308"},
    "otro":         {"color": "#8e8e93", "width": 1.2, "dash": [3, 5],         "glow": "#8e8e93"},
}

FOCUS_ALPHA = 1.0
DIM_ALPHA   = 0.12

# ── Helpers ──────────────────────────────────────────────────────────────────

_RACE_KEYS = {"raza", "raza / especie", "raza/especie", "especie", "race", "species"}


def get_race(char: "Character") -> str:
    """Extrae la raza o especie de los atributos personalizados del personaje."""
    for key, val in char.custom_attributes.items():
        if key.strip().lower() in _RACE_KEYS and val.strip():
            return val.strip()
    return ""


def bezier_path(p1: QPointF, p2: QPointF, curv: float = 0.16, r1: float = 0.0, r2: float = 0.0) -> QPainterPath:
    """Genera una curva bezier suave que nace y termina exactamente en el perímetro/borde de cada esfera."""
    dx, dy = p2.x() - p1.x(), p2.y() - p1.y()
    dist = math.hypot(dx, dy)
    if dist < 1.0:
        return QPainterPath()

    # Vector normal para la curvatura
    nx = -dy / dist * dist * curv
    ny =  dx / dist * dist * curv
    ctrl = QPointF((p1.x() + p2.x()) / 2 + nx, (p1.y() + p2.y()) / 2 + ny)

    # Recortar el punto inicial al borde de la esfera 1 (hacia el punto de control)
    if r1 > 0:
        v1x, v1y = ctrl.x() - p1.x(), ctrl.y() - p1.y()
        d1 = max(math.hypot(v1x, v1y), 1.0)
        start_pt = QPointF(p1.x() + (v1x / d1) * r1, p1.y() + (v1y / d1) * r1)
    else:
        start_pt = p1

    # Recortar el punto final al borde de la esfera 2 (desde el punto de control)
    if r2 > 0:
        v2x, v2y = ctrl.x() - p2.x(), ctrl.y() - p2.y()
        d2 = max(math.hypot(v2x, v2y), 1.0)
        end_pt = QPointF(p2.x() + (v2x / d2) * r2, p2.y() + (v2y / d2) * r2)
    else:
        end_pt = p2

    path = QPainterPath(start_pt)
    path.quadTo(ctrl, end_pt)
    return path


# ── Jerarquía y Métricas del Personaje ──────────────────────────────────────

ROLE_BONUS = {
    "protagonista": 20.0,
    "antagonista":  18.0,
    "secundario":    4.0,
    "misterioso":    5.0,
    "otro":          1.0,
}


class CharacterMetrics:
    def __init__(self, char_id: str = "", chapters_count: int = 0, connections_count: int = 0,
                 intensity_sum: float = 0.0, role: str = ""):
        self.char_id = char_id
        self.chapters_count = chapters_count
        self.connections_count = connections_count
        self.intensity_sum = intensity_sum
        self.role = role

        role_key = (role or "").strip().lower()
        self.role_bonus = ROLE_BONUS.get(role_key, 1.0)

        # Peso de ordenación (solo para ordenar nodos, NO determina el tamaño)
        self.weight = (
            (chapters_count * 3.5) +
            (connections_count * 1.8) +
            (intensity_sum * 0.8) +
            self.role_bonus * 0.5   # rol: influencia mínima en ordenación
        )

        # ── Tamaño y Tier basado SOLO en actividad narrativa real ─────────────
        # Fórmula: activity_score = sqrt(conexiones * 3 + apariciones * 2)
        # Esto garantiza crecimiento sublineal: doblar conexiones NO dobla el tamaño.
        # Rangos esperados con 200 personajes (distribución de ley de potencias):
        #   Titán     (35+ conex, 10 caps): score ≈ sqrt(105+20) = 11.2  → ~46 px
        #   Protagonista normal (15 conex, 5 caps): score ≈ 8.4          → ~42 px
        #   Secundario (6-8 conex, 2-3 caps): score ≈ 5.3-5.7            → ~22-24 px
        #   Menor (1-2 conex, 0 caps): score ≈ 1.7-2.4                   → ~11-12 px
        activity_score = math.sqrt(
            max(0.0, connections_count * 3.0 + chapters_count * 2.0)
        )

        # Tier: refleja la densidad de conexiones, no el rol declarado
        if connections_count >= 20 or (connections_count >= 10 and chapters_count >= 4):
            # Mega-hub o pilar narrativo real
            self.tier = "core"
        elif connections_count >= 3 or chapters_count >= 2 or role_key in ("secundario", "misterioso"):
            # Personaje con presencia narrativa real
            self.tier = "primary"
        else:
            # Satélite / personaje de fondo
            self.tier = "minor"

        # Radio: 100% basado en activity_score con techo duro por tier
        # Techo minor=14, primary=26, core=46 → diferencia visual clara pero no monstruosa
        if self.tier == "core":
            self.base_radius = min(46.0, 28.0 + activity_score * 1.6)
        elif self.tier == "primary":
            self.base_radius = min(26.0, 14.0 + activity_score * 2.2)
        else:
            self.base_radius = min(14.0, 8.0 + activity_score * 1.8)

        # ── Forma Geométrica Progresiva (Polígonos regulares -> Círculo como Hito Legendario 100+) ──
        # ▲ Triángulo (3 lados)   : 1-2 conex.   (Terciario / Incidental)
        # ⯁ Rombo (4 lados)       : 3-5 conex.   (Secundario Menor)
        # ⬟ Pentágono (5 lados)   : 6-9 conex.   (Secundario Recurrente)
        # ⬢ Hexágono (6 lados)    : 10-14 conex. (Notable)
        # ⬡ Heptágono (7 lados)   : 15-22 conex. (Importante)
        # 🛑 Octágono (8 lados)    : 23-35 conex. (Pilar de Facción)
        # 💎 Decágono (10 lados)   : 36-55 conex. (Co-protagonista / Rival Mayor)
        # 🔷 Dodecágono (12 lados) : 56-79 conex. (Protagonista de Arco)
        # 🔮 Icoságono (20 lados)  : 80-99 conex. (Casi esférico)
        # ● Círculo Radiante       : 100+ conex.  (Hito Mítico / Núcleo Absoluto)
        if connections_count >= 100:
            self.shape = "circle"
        elif connections_count >= 80:
            self.shape = "icosagon"
        elif connections_count >= 56:
            self.shape = "dodecagon"
        elif connections_count >= 36:
            self.shape = "decagon"
        elif connections_count >= 23:
            self.shape = "octagon"
        elif connections_count >= 15:
            self.shape = "heptagon"
        elif connections_count >= 10:
            self.shape = "hexagon"
        elif connections_count >= 6:
            self.shape = "pentagon"
        elif connections_count >= 3:
            self.shape = "diamond"
        else:
            self.shape = "triangle"





