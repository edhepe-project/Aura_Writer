"""
Módulo de Datos, Paletas y Modelos del Grafo de Relaciones.
"""

from typing import Optional, Dict, List
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


def bezier_path(p1: QPointF, p2: QPointF, curv: float = 0.16) -> QPainterPath:
    """Genera una curva bezier suave entre dos puntos para las aristas."""
    dx, dy = p2.x() - p1.x(), p2.y() - p1.y()
    dist = max(math.hypot(dx, dy), 1.0)
    nx = -dy / dist * dist * curv
    ny =  dx / dist * dist * curv
    ctrl = QPointF((p1.x() + p2.x()) / 2 + nx, (p1.y() + p2.y()) / 2 + ny)
    path = QPainterPath(p1)
    path.quadTo(ctrl, p2)
    return path


# ── Jerarquía y Métricas del Personaje ──────────────────────────────────────

ROLE_BONUS = {
    "protagonista": 12.0,
    "antagonista":  10.0,
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

        # Peso o relevancia continua
        self.weight = (
            (chapters_count * 2.2) +
            (connections_count * 1.6) +
            (intensity_sum * 1.0) +
            self.role_bonus
        )

        # Nivel jerárquico y dimensionamiento de nodo
        if self.weight >= 22.0 or role_key == "protagonista":
            self.tier = "core"      # Protagonista / Eje central
            self.base_radius = min(38.0, 28.0 + (self.weight - 22.0) * 0.3)
        elif self.weight >= 9.0 or connections_count >= 4 or chapters_count >= 3:
            self.tier = "primary"   # Secundario principal / conector
            self.base_radius = 20.0 + min(6.0, (self.weight - 9.0) * 0.4)
        else:
            self.tier = "minor"     # Satélite / menor
            self.base_radius = max(11.0, 11.0 + self.weight * 0.35)
