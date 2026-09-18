"""
physics.py — Algoritmo de física y layout orbital/planetario para Lugares.
"""
from __future__ import annotations

import math
import random
from typing import Dict, List, Tuple

from core.models import Place, PlaceLink


def compute_places_layout(
    places: List[Place],
    links: List[PlaceLink]
) -> Dict[str, Tuple[float, float]]:
    """
    Layout planetario / sistema solar para el Atlas de Lugares:
      - Los Lugares Principales (reinos, ciudades, regiones) actúan como Soles/Planetas primarios.
      - Las Estancias/Interiores orbitan en círculos limpios alrededor de su Planeta Padre como lunas/satélites.
      - Los Planetas primarios se distribuyen con fuerzas de repulsión generosas para respirar libremente.
    """
    n = len(places)
    if n == 0:
        return {}
    if n == 1:
        return {places[0].id: (0.0, 0.0)}

    place_map = {p.id: p for p in places}

    # 1. Separar planetas primarios (raíces) y lunas/satélites (hijos con parent_place_id válido)
    primaries: List[Place] = []
    satellites_by_parent: Dict[str, List[Place]] = {}

    for p in places:
        if p.parent_place_id and p.parent_place_id in place_map:
            satellites_by_parent.setdefault(p.parent_place_id, []).append(p)
        else:
            primaries.append(p)

    if not primaries:
        primaries = list(places)

    num_prim = len(primaries)
    primary_ids = [p.id for p in primaries]
    pos: Dict[str, List[float]] = {}

    # 2. Posicionamiento de los Planetas Primarios
    # Si hay pocos planetas, darles una órbita amplia
    if num_prim == 1:
        pos[primaries[0].id] = [0.0, 0.0]
    else:
        radius_ring = max(240.0, num_prim * 120.0)
        for i, p in enumerate(primaries):
            angle = (2.0 * math.pi / num_prim) * i - math.pi / 2.0
            pos[p.id] = [
                radius_ring * math.cos(angle),
                radius_ring * math.sin(angle)
            ]

        # Simulación de repulsión entre planetas primarios para equilibrar distancias
        min_prim_dist = 280.0
        k = 320.0
        for _ in range(80):
            disp = {pid: [0.0, 0.0] for pid in primary_ids}
            for i in range(num_prim):
                u = primary_ids[i]
                for j in range(i + 1, num_prim):
                    v = primary_ids[j]
                    dx = pos[u][0] - pos[v][0]
                    dy = pos[u][1] - pos[v][1]
                    dist = math.hypot(dx, dy) or 0.01
                    if dist < min_prim_dist:
                        force = (k * k) / dist + (min_prim_dist - dist) ** 2 * 0.6
                    else:
                        force = (k * k) / dist
                    ux, uy = dx / dist, dy / dist
                    disp[u][0] += ux * force
                    disp[u][1] += uy * force
                    disp[v][0] -= ux * force
                    disp[v][1] -= uy * force

            # Aplicar desplazamiento acotado
            for pid in primary_ids:
                dx, dy = disp[pid]
                d = math.hypot(dx, dy) or 0.01
                move = min(d, 25.0)
                pos[pid][0] += (dx / d) * move
                pos[pid][1] += (dy / d) * move

    # 3. Ubicar Satélites/Lunas orbitando armónicamente alrededor de su Planeta Padre
    for parent_id, sats in satellites_by_parent.items():
        parent_pos = pos.get(parent_id, [0.0, 0.0])
        num_sats = len(sats)
        orbit_radius = 135.0 if num_sats <= 3 else (150.0 + num_sats * 12.0)

        for j, sat in enumerate(sats):
            # Distribución equitativa en ángulo orbital
            sat_angle = (2.0 * math.pi / num_sats) * j - math.pi / 4.0
            pos[sat.id] = [
                parent_pos[0] + orbit_radius * math.cos(sat_angle),
                parent_pos[1] + orbit_radius * math.sin(sat_angle)
            ]

    # Cualquier lugar remanente que pudiera faltar
    for p in places:
        if p.id not in pos:
            pos[p.id] = [random.uniform(-150, 150), random.uniform(-150, 150)]

    return {pid: (pos[pid][0], pos[pid][1]) for pid in pos}
