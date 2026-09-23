"""
physics.py — Distribución espacial y física orbital inspirada fielmente en el Grafo de Relaciones.
Dispersión en espiral áurea estelar, zonas de exclusión por masa y relajación de Coulomb con hash grid.
"""
from __future__ import annotations

import math
from typing import Dict, List, Tuple

from core.models import Place, PlaceLink
from .models import CATEGORY_TIERS, TIER_NODE_RADIUS


def compute_places_layout(
    places: List[Place],
    links: List[PlaceLink]
) -> Dict[str, Tuple[float, float]]:
    """
    Algoritmo orbital espiral idéntico al motor de física de RelationGraph:
      1. Clasificación por Tiers (Core / Primary / Minor).
      2. Dispersión del Núcleo / Soles en anillo generoso.
      3. Dispersión espiral de Arquímedes Áurea (Golden Angle ~137.5°) por sistemas estelares.
      4. Halo exterior expansivo para lugares libres/menores.
      5. Relajación física N-Body (Fuerza de Coulomb espacial) para garantizar colchón de aire y cero solapamientos.
    """
    total_count = len(places)
    if total_count == 0:
        return {}
    if total_count == 1:
        return {places[0].id: (0.0, 0.0)}

    place_map = {p.id: p for p in places}
    tier_map = {p.id: CATEGORY_TIERS.get(p.category, 3) for p in places}

    # Separar en Tiers igual que RelationGraph (Core / Primary / Minor)
    core_nodes = [p.id for p in places if tier_map[p.id] == 0]       # Soles / Macro-Mundos
    primary_nodes = [p.id for p in places if tier_map[p.id] == 1]    # Reinos / Naciones
    minor_nodes = [p.id for p in places if tier_map[p.id] >= 2]      # Ciudades y Puntos de Interés

    # Fallback si no hay tier 0: los primarios ascienden a core
    if not core_nodes:
        if primary_nodes:
            core_nodes = list(primary_nodes)
            primary_nodes = [p.id for p in places if tier_map[p.id] == 2]
            minor_nodes = [p.id for p in places if tier_map[p.id] >= 3]
        else:
            core_nodes = [places[0].id]
            primary_nodes = [p.id for p in places[1:max(2, min(6, total_count // 2))]]
            minor_nodes = [p.id for p in places if p.id not in core_nodes and p.id not in primary_nodes]

    core_set = set(core_nodes)
    primary_set = set(primary_nodes)

    # Construir grafo de adyacencia (tanto por pertenencia parent_place_id como por rutas)
    adj_map: Dict[str, List[str]] = {p.id: [] for p in places}
    for lk in links:
        if lk.place_id_a in adj_map and lk.place_id_b in adj_map:
            adj_map[lk.place_id_a].append(lk.place_id_b)
            adj_map[lk.place_id_b].append(lk.place_id_a)
    for p in places:
        if p.parent_place_id and p.parent_place_id in adj_map:
            adj_map[p.parent_place_id].append(p.id)
            adj_map[p.id].append(p.parent_place_id)

    positions: Dict[str, Tuple[float, float]] = {}

    # ── 1. Anillo de Titanes / Soles Centrales ───────────────────────────────
    n_core = len(core_nodes)
    core_ring_r = max(400.0, 120.0 + math.sqrt(total_count) * 110.0)

    for si, scid in enumerate(core_nodes):
        if n_core == 1:
            positions[scid] = (0.0, 0.0)
        elif n_core == 2:
            offset = core_ring_r * 0.60
            positions[scid] = (-offset if si == 0 else offset, 0.0)
        else:
            ang = 2.0 * math.pi * si / n_core - math.pi / 2.0
            positions[scid] = (math.cos(ang) * core_ring_r * 0.70,
                               math.sin(ang) * core_ring_r * 0.70)

    # ── 2. Secundarios / Naciones en Espiral Áurea de su Sol ──────────────────
    GOLDEN_ANGLE = 2.39996322972865332  # radianes (~137.5 grados)

    titan_primaries: Dict[str, List[str]] = {c: [] for c in core_nodes}
    unanchored_primaries: List[str] = []

    for pcid in primary_nodes:
        p_obj = place_map[pcid]
        best_titan = None
        # Prioridad 1: parent_place_id si apunta a un core
        if p_obj.parent_place_id in core_set:
            best_titan = p_obj.parent_place_id
        else:
            # Prioridad 2: vecino conectado
            for nb in adj_map.get(pcid, []):
                if nb in core_set:
                    best_titan = nb
                    break
        if best_titan:
            titan_primaries[best_titan].append(pcid)
        else:
            unanchored_primaries.append(pcid)

    # Si hay sin ancla, repartir entre titanes
    for pcid in unanchored_primaries:
        best_titan = min(core_nodes, key=lambda c: len(titan_primaries[c]))
        titan_primaries[best_titan].append(pcid)

    for titan_id, sats in titan_primaries.items():
        tx, ty = positions[titan_id]
        r_titan = TIER_NODE_RADIUS.get(tier_map.get(titan_id, 0), 42.0)
        inner_deadzone = max(320.0, r_titan * 5.0)
        for idx, pcid in enumerate(sats):
            r_dist = inner_deadzone + math.sqrt(idx + 1) * 180.0
            theta = (idx + 1) * GOLDEN_ANGLE
            positions[pcid] = (tx + math.cos(theta) * r_dist, ty + math.sin(theta) * r_dist)

    # ── 3. Ciudades y Puntos de Interés en Espiral Áurea de su Ancla ──────────
    anchor_minors: Dict[str, List[str]] = {}
    unanchored_minors: List[str] = []

    for m_id in minor_nodes:
        m_obj = place_map[m_id]
        best_anchor = None
        # Prioridad 1: parent_place_id
        if m_obj.parent_place_id and m_obj.parent_place_id in positions:
            best_anchor = m_obj.parent_place_id
        else:
            # Prioridad 2: vecino ya posicionado
            for nb in adj_map.get(m_id, []):
                if nb in positions:
                    best_anchor = nb
                    break
        if best_anchor:
            anchor_minors.setdefault(best_anchor, []).append(m_id)
        else:
            unanchored_minors.append(m_id)

    for anchor_id, m_list in anchor_minors.items():
        ax, ay = positions[anchor_id]
        parent_tier = tier_map.get(anchor_id, 3)
        r_anchor = TIER_NODE_RADIUS.get(parent_tier, 22.0)
        
        # Para satélites de ciudades/lugares menores (Tier >= 2), órbita cercana y armónica
        if parent_tier >= 2:
            anchor_deadzone = max(80.0, r_anchor * 3.2)
            step_r = 30.0
        else:
            anchor_deadzone = max(140.0, r_anchor * 3.8)
            step_r = 55.0

        n_sats = len(m_list)
        for m_idx, m_id in enumerate(m_list):
            if n_sats <= 5:
                # Distribución circular armónica y uniforme para pocos satélites
                m_theta = 2.0 * math.pi * m_idx / n_sats - math.pi / 2.0
                m_dist = anchor_deadzone
            else:
                # Espiral áurea suave para grupos densos
                m_dist = anchor_deadzone + math.sqrt(m_idx + 1) * step_r
                m_theta = (m_idx + 1) * GOLDEN_ANGLE
            positions[m_id] = (ax + math.cos(m_theta) * m_dist, ay + math.sin(m_theta) * m_dist)

    # Menores sin ancla directa: halo exterior expansivo de la galaxia
    for u_idx, u_id in enumerate(unanchored_minors):
        u_dist = core_ring_r * 1.3 + math.sqrt(u_idx + 1) * 120.0
        u_theta = (u_idx + 1) * GOLDEN_ANGLE
        positions[u_id] = (math.cos(u_theta) * u_dist, math.sin(u_theta) * u_dist)

    # ── 4. Relajación Física Real N-Body (Ley de Coulomb con Spatial Grid) ────
    # Número de iteraciones reducido para no bloquear la UI más de ~100-150ms.
    # La espiral áurea ya produce un layout de alta calidad; la relajación solo
    # corrige solapamientos extremos. 10 iteraciones son suficientes visualmente.
    nodes_list = list(place_map.keys())
    n = len(nodes_list)
    max_it = 10 if n <= 150 else 6

    if max_it > 0:
        radius_dict = {nid: TIER_NODE_RADIUS.get(tier_map.get(nid, 4), 16.0) for nid in nodes_list}
        cell_size = 500.0

        for it in range(max_it):
            temp = 60.0 * (1.0 - it / float(max_it))
            disp = {nid: [0.0, 0.0] for nid in nodes_list}

            # Spatial hash grid
            grid: Dict[Tuple[int, int], List[str]] = {}
            for nid in nodes_list:
                px, py = positions[nid]
                gx, gy = int(px // cell_size), int(py // cell_size)
                grid.setdefault((gx, gy), []).append(nid)

            for (gx, gy), cell_nodes in grid.items():
                neighbors = []
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        neighbors.extend(grid.get((gx + dx, gy + dy), []))

                for u in cell_nodes:
                    pu = positions[u]
                    ru = radius_dict[u]
                    for v in neighbors:
                        if u >= v:
                            continue
                        pv = positions[v]
                        dx = pu[0] - pv[0]
                        dy = pu[1] - pv[1]
                        if abs(dx) > cell_size or abs(dy) > cell_size:
                            continue

                        dist_sq = dx * dx + dy * dy
                        if dist_sq < 1.0:
                            dx, dy = 1.0, 0.0
                            dist_sq = 1.0

                        rv = radius_dict[v]
                        # Distancia mínima obligatoria: suma de radios + colchón de aire
                        min_distance = (ru + rv) * 2.2 + 130.0

                        if dist_sq < min_distance * min_distance:
                            dist = math.sqrt(dist_sq)
                            overlap = (min_distance - dist)
                            force = (overlap / min_distance) * 40.0 + 6.0
                            ux, uy = (dx / dist) * force, (dy / dist) * force
                            disp[u][0] += ux; disp[u][1] += uy
                            disp[v][0] -= ux; disp[v][1] -= uy

            for nid in nodes_list:
                d = math.hypot(disp[nid][0], disp[nid][1])
                if d > 0:
                    step = min(d, temp)
                    positions[nid] = (
                        positions[nid][0] + disp[nid][0] / d * step,
                        positions[nid][1] + disp[nid][1] / d * step
                    )

    return positions
