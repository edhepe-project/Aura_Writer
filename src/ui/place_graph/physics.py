"""
physics.py — Física gravitatoria y cálculo de órbitas celestes por jerarquía categórica.
Sol (Planeta/Mundo) -> Órbitas (Naciones) -> Órbitas (Ciudades) -> Órbitas (Castillos/Tabernas/Mazmorras/Bosques).
"""
from __future__ import annotations

import math
import random
from typing import Dict, List, Tuple

from core.models import Place, PlaceLink
from .models import CATEGORY_TIERS


def compute_places_layout(
    places: List[Place],
    links: List[PlaceLink]
) -> Dict[str, Tuple[float, float]]:
    """
    Layout cosmológico en cascada gravitacional por categorías:
      - Tier 0: Sol / Planeta Macro (Centro del universo o centros estelares)
      - Tier 1: Reinos / Naciones (Orbitan alrededor de su Planeta o como soles regionales)
      - Tier 2: Ciudades / Poblados (Orbitan alrededor de su Nación / Reino)
      - Tier 3: Castillos, Tabernas, Mazmorras, Bosques, Regiones Mágicas (Orbitan alrededor de su Ciudad)
    """
    n = len(places)
    if n == 0:
        return {}
    if n == 1:
        return {places[0].id: (0.0, 0.0)}

    place_map = {p.id: p for p in places}

    # 1. Clasificar lugares por Tier categórico
    tier_places: Dict[int, List[Place]] = {0: [], 1: [], 2: [], 3: []}
    for p in places:
        tier = CATEGORY_TIERS.get(p.category, 3)
        tier_places[tier].append(p)

    # 2. Mapear jerarquía de pertenencia
    # Si el usuario definió parent_place_id lo respetamos; si no, anclamos automáticamente
    # al centro gravitacional correspondiente más cercano (Tier 3 a Ciudad, Tier 2 a Reino, Tier 1 a Sol)
    children_by_parent: Dict[str, List[Place]] = {}
    
    # Listas de candidatos ancla
    soles = tier_places[0]
    reinos = tier_places[1]
    ciudades = tier_places[2]
    interiores = tier_places[3]

    # Asignar anclas para Tier 1 (Naciones -> Soles)
    for p in reinos:
        parent_id = p.parent_place_id if (p.parent_place_id and p.parent_place_id in place_map) else None
        if not parent_id and soles:
            parent_id = soles[0].id
        if parent_id:
            children_by_parent.setdefault(parent_id, []).append(p)

    # Asignar anclas para Tier 2 (Ciudades -> Naciones/Soles)
    for p in ciudades:
        parent_id = p.parent_place_id if (p.parent_place_id and p.parent_place_id in place_map) else None
        if not parent_id and reinos:
            parent_id = reinos[0].id
        elif not parent_id and soles:
            parent_id = soles[0].id
        if parent_id:
            children_by_parent.setdefault(parent_id, []).append(p)

    # Asignar anclas para Tier 3 (Castillos/Tabernas/Mazmorras -> Ciudades/Naciones/Soles)
    for p in interiores:
        parent_id = p.parent_place_id if (p.parent_place_id and p.parent_place_id in place_map) else None
        if not parent_id and ciudades:
            parent_id = ciudades[0].id
        elif not parent_id and reinos:
            parent_id = reinos[0].id
        elif not parent_id and soles:
            parent_id = soles[0].id
        if parent_id:
            children_by_parent.setdefault(parent_id, []).append(p)

    # 3. Identificar centros macro (Tier 0 si hay, si no Tier 1, si no Tier 2, etc.)
    macro_roots: List[Place] = []
    if soles:
        macro_roots = soles
    elif reinos:
        macro_roots = reinos
    elif ciudades:
        macro_roots = ciudades
    else:
        macro_roots = list(places)

    pos: Dict[str, List[float]] = {}
    num_roots = len(macro_roots)

    # Ubicar Centros Macro con gran separación entre sí
    if num_roots == 1:
        pos[macro_roots[0].id] = [0.0, 0.0]
    else:
        root_dist = max(380.0, num_roots * 160.0)
        for i, root_p in enumerate(macro_roots):
            angle = (2.0 * math.pi / num_roots) * i - math.pi / 2.0
            pos[root_p.id] = [
                root_dist * math.cos(angle),
                root_dist * math.sin(angle)
            ]

    # 4. Función para distribuir satélites en anillos limpios sin superposición
    def _layout_orbit(parent_id: str, satellites: List[Place], base_radius: float):
        num_sats = len(satellites)
        if num_sats == 0:
            return
        parent_pos = pos.get(parent_id, [0.0, 0.0])
        # Aumentar radio si hay muchos satélites para que las etiquetas de texto no choquen
        orb_radius = max(base_radius, num_sats * 38.0 + 90.0)
        
        # Desfase angular orgánico
        phase = random.uniform(0.0, math.pi / 4.0)
        for j, sat in enumerate(satellites):
            sat_angle = (2.0 * math.pi / num_sats) * j + phase
            pos[sat.id] = [
                parent_pos[0] + orb_radius * math.cos(sat_angle),
                parent_pos[1] + orb_radius * math.sin(sat_angle)
            ]

            # Si este satélite a su vez tiene sub-satélites (ej. una Ciudad con Tabernas/Castillos)
            sub_sats = [p for p in children_by_parent.get(sat.id, []) if p.id not in pos]
            if sub_sats:
                _layout_orbit(sat.id, sub_sats, base_radius=120.0)

    # Desplegar niveles en orden jerárquico
    # Nivel Soles -> Naciones (Órbita de 300px)
    for root_p in macro_roots:
        direct_sats = [p for p in children_by_parent.get(root_p.id, []) if p.id not in pos]
        if direct_sats:
            _layout_orbit(root_p.id, direct_sats, base_radius=220.0)

    # Cualquier lugar que no haya quedado anclado
    for p in places:
        if p.id not in pos:
            pos[p.id] = [random.uniform(-160, 160), random.uniform(-160, 160)]

    # 5. Pasada de repulsión física estricta para garantizar distancia mínima absoluta entre TODOS los nodos
    all_ids = list(pos.keys())
    total_nodes = len(all_ids)
    min_dist_strict = 140.0  # Espacio vital mínimo para cada nodo y su etiqueta de texto

    for _ in range(40):
        changed = False
        for i in range(total_nodes):
            u = all_ids[i]
            for j in range(i + 1, total_nodes):
                v = all_ids[j]
                dx = pos[u][0] - pos[v][0]
                dy = pos[u][1] - pos[v][1]
                dist = math.hypot(dx, dy) or 0.01
                if dist < min_dist_strict:
                    push = (min_dist_strict - dist) / 2.0 + 1.5
                    ux, uy = dx / dist, dy / dist
                    pos[u][0] += ux * push
                    pos[u][1] += uy * push
                    pos[v][0] -= ux * push
                    pos[v][1] -= uy * push
                    changed = True
        if not changed:
            break

    return {pid: (pos[pid][0], pos[pid][1]) for pid in pos}
