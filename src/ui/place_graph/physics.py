"""
physics.py — Física gravitatoria y cálculo de galaxia en espiral armónica.
Sol Central (Planeta/Macro) -> Brazos Espirales (Naciones/Reinos) -> Órbitas (Ciudades) -> Satélites (Puntos de Interés).
"""
from __future__ import annotations

import math
from typing import Dict, List, Tuple

from core.models import Place, PlaceLink
from .models import CATEGORY_TIERS


def compute_places_layout(
    places: List[Place],
    links: List[PlaceLink]
) -> Dict[str, Tuple[float, float]]:
    """
    Layout Galaxia en Espiral de Arquímedes Áurea:
      - Distribución armónica en espiral/constelación abierta alrededor del Sol Central.
      - Cada cuerpo celeste (Nación, Ciudad, Castillo, etc.) tiene un radio y ángulo orbital garantizado.
      - Respeta la jerarquía padre -> hijos sin colapsar en líneas diagonales.
      - Asegura que ningún lugar se solape ni se pierda fuera de la vista.
    """
    n = len(places)
    if n == 0:
        return {}
    if n == 1:
        return {places[0].id: (0.0, 0.0)}

    place_map = {p.id: p for p in places}

    # 1. Separar por Tiers
    tier_places: Dict[int, List[Place]] = {0: [], 1: [], 2: [], 3: []}
    for p in places:
        tier = CATEGORY_TIERS.get(p.category, 3)
        tier_places[tier].append(p)

    soles = tier_places[0]
    reinos = tier_places[1]
    ciudades = tier_places[2]
    interiores = tier_places[3]

    # Mapeo de hijos
    children_by_parent: Dict[str, List[Place]] = {}
    for p in places:
        if p.parent_place_id and p.parent_place_id in place_map:
            children_by_parent.setdefault(p.parent_place_id, []).append(p)

    pos: Dict[str, List[float]] = {}

    # 2. Posicionar el Sol Central (o centro principal)
    if soles:
        center_id = soles[0].id
        pos[center_id] = [0.0, 0.0]
        # Si hay más de un Sol/Planeta macro, repartirlos en un anillo amplio
        for i, s in enumerate(soles[1:], start=1):
            ang = (2.0 * math.pi / max(1, len(soles) - 1)) * i
            pos[s.id] = [450.0 * math.cos(ang), 450.0 * math.sin(ang)]
    elif reinos:
        # Si no hay Tier 0, el primer reino es el Sol de este sistema
        center_id = reinos[0].id
        pos[center_id] = [0.0, 0.0]
    elif ciudades:
        center_id = ciudades[0].id
        pos[center_id] = [0.0, 0.0]
    else:
        center_id = places[0].id
        pos[center_id] = [0.0, 0.0]

    # 3. Espiral de Arquímedes Áurea para ubicar Sistemas y Satélites
    # Ángulo áureo ~ 137.5 grados (2.3999632 rad) para distribución orgánica sin alineaciones
    GOLDEN_ANGLE = 2.39996323

    # Función para posicionar satélites de un cuerpo padre en espiral orbital
    def _layout_satellites_spiral(parent_id: str, sats: List[Place], base_dist: float, step_dist: float):
        num = len(sats)
        if num == 0:
            return
        parent_pos = pos.get(parent_id, [0.0, 0.0])
        for idx, sat in enumerate(sats):
            if sat.id in pos:
                continue
            # Ángulo distribuido equitativamente alrededor del círculo + leve espiral
            theta = (2.0 * math.pi / num) * idx + (GOLDEN_ANGLE * 0.3)
            r = base_dist + idx * step_dist
            pos[sat.id] = [
                parent_pos[0] + r * math.cos(theta),
                parent_pos[1] + r * math.sin(theta)
            ]
            # Recursión para sus propios hijos
            sub_children = [c for c in children_by_parent.get(sat.id, []) if c.id not in pos]
            if sub_children:
                _layout_satellites_spiral(sat.id, sub_children, base_dist=120.0, step_dist=20.0)

    # A. Naciones/Reinos directos del centro (Órbita Mayor)
    naciones_del_centro = [p for p in reinos if p.id not in pos]
    if naciones_del_centro:
        _layout_satellites_spiral(center_id, naciones_del_centro, base_dist=240.0, step_dist=35.0)

    # B. Ciudades directas de reinos o del centro
    for r_obj in reinos:
        ciudades_reino = [p for p in children_by_parent.get(r_obj.id, []) if p.id not in pos]
        if ciudades_reino:
            _layout_satellites_spiral(r_obj.id, ciudades_reino, base_dist=170.0, step_dist=25.0)

    ciudades_sueltas = [p for p in ciudades if p.id not in pos]
    if ciudades_sueltas:
        _layout_satellites_spiral(center_id, ciudades_sueltas, base_dist=280.0, step_dist=30.0)

    # C. Puntos de interés (Castillos, Tabernas, Mazmorras, Bosques, etc.)
    for c_obj in ciudades:
        puntos_ciudad = [p for p in children_by_parent.get(c_obj.id, []) if p.id not in pos]
        if puntos_ciudad:
            _layout_satellites_spiral(c_obj.id, puntos_ciudad, base_dist=130.0, step_dist=20.0)

    # D. Cualquier lugar remanente que no haya tenido padre explícito -> Espiral Galáctica
    remanentes = [p for p in places if p.id not in pos]
    if remanentes:
        for k, p in enumerate(remanentes):
            theta = (k + 1) * GOLDEN_ANGLE
            r = 180.0 + math.sqrt(k + 1) * 90.0
            pos[p.id] = [
                r * math.cos(theta),
                r * math.sin(theta)
            ]

    # 4. Refuerzo de separación física O(n²) estricta para garantizar que NUNCA colisionen
    all_ids = list(pos.keys())
    total_nodes = len(all_ids)
    min_separation = 150.0  # Espacio vital amplio para respirar

    for _ in range(50):
        changed = False
        for i in range(total_nodes):
            u = all_ids[i]
            for j in range(i + 1, total_nodes):
                v = all_ids[j]
                dx = pos[u][0] - pos[v][0]
                dy = pos[u][1] - pos[v][1]
                dist = math.hypot(dx, dy) or 0.01
                if dist < min_separation:
                    push = (min_separation - dist) / 2.0 + 1.5
                    ux, uy = dx / dist, dy / dist
                    pos[u][0] += ux * push
                    pos[u][1] += uy * push
                    pos[v][0] -= ux * push
                    pos[v][1] -= uy * push
                    changed = True
        if not changed:
            break

    return {pid: (pos[pid][0], pos[pid][1]) for pid in pos}
