"""
physics.py — Algoritmo de física y layout orbital/constelación para Lugares.
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
    Layout orbital orgánico en 4 fases para el Atlas de Lugares:
      1. Identificación de macro-lugares (padres/reinos) y satélites (estancias/ciudades).
      2. Asignación de sistemas estelares/regionales (componentes conexas).
      3. Simulación Spring-Embedder con distancia mínima garantizada (min_node_dist >= 170px).
      4. Refuerzo de separación y optimización anti-cruce de rutas.
    """
    n = len(places)
    if n == 0:
        return {}
    if n == 1:
        return {places[0].id: (0.0, 0.0)}

    ids = [p.id for p in places]
    place_map = {p.id: p for p in places}

    # Grafo de adyacencia
    adj: Dict[str, set[str]] = {pid: set() for pid in ids}
    for lk in links:
        if lk.place_id_a in adj and lk.place_id_b in adj:
            adj[lk.place_id_a].add(lk.place_id_b)
            adj[lk.place_id_b].add(lk.place_id_a)
    for p in places:
        if p.parent_place_id and p.parent_place_id in adj and p.id in adj:
            adj[p.parent_place_id].add(p.id)
            adj[p.id].add(p.parent_place_id)

    # ── Fase 1: Detección de Componentes / Constelaciones ────────────────────
    visited: set[str] = set()
    components: List[List[str]] = []
    for pid in ids:
        if pid not in visited:
            comp: List[str] = []
            queue = [pid]
            while queue:
                cur = queue.pop(0)
                if cur in visited:
                    continue
                visited.add(cur)
                comp.append(cur)
                for nb in adj.get(cur, []):
                    if nb not in visited and nb in adj:
                        queue.append(nb)
            components.append(comp)

    num_comp = len(components)
    def _comp_radius(size: int) -> float:
        return max(180.0, size * 110.0)

    comp_centers: List[Tuple[float, float]] = []
    if num_comp == 1:
        comp_centers = [(0.0, 0.0)]
    else:
        for ci in range(num_comp):
            r_comp = _comp_radius(len(components[ci]))
            angle = (2 * math.pi / num_comp) * ci
            gap = r_comp * 2.4
            cx = gap * math.cos(angle)
            cy = gap * math.sin(angle)
            comp_centers.append((cx, cy))

    # Posicionamiento inicial: los padres al centro de la constelación, estancias en órbita
    pos: Dict[str, List[float]] = {}
    for ci, comp in enumerate(components):
        cx, cy = comp_centers[ci]
        comp_places = [place_map[pid] for pid in comp if pid in place_map]
        
        # Identificar raíces de jerarquía dentro de la componente
        roots = [p for p in comp_places if not p.parent_place_id or p.parent_place_id not in place_map]
        if not roots:
            roots = comp_places

        r = _comp_radius(len(comp))
        for j, p in enumerate(comp_places):
            if len(comp_places) == 1:
                pos[p.id] = [cx, cy]
            elif p.parent_place_id and p.parent_place_id in pos:
                # Estancia/Hijo: orbita alrededor de su padre
                parent_pos = pos[p.parent_place_id]
                orb_angle = random.uniform(0, 2 * math.pi)
                orb_dist = random.uniform(160.0, 210.0)
                pos[p.id] = [
                    parent_pos[0] + orb_dist * math.cos(orb_angle),
                    parent_pos[1] + orb_dist * math.sin(orb_angle)
                ]
            else:
                # Raíz o lugar independiente: posición angular espaciosa
                angle = (2 * math.pi / max(1, len(roots))) * j + random.uniform(-0.1, 0.1)
                px = cx + r * math.cos(angle) + random.uniform(-10, 10)
                py = cy + r * math.sin(angle) + random.uniform(-10, 10)
                pos[p.id] = [px, py]

    # ── Fase 2: Simulación de Fuerzas Gravitatorias & Resortes ───────────────
    min_node_dist = 180.0  # Espacio mínimo generoso para que respiren
    k = max(min_node_dist * 1.5, 240.0)
    iterations = 180

    attract_pairs: List[Tuple[str, str]] = []
    seen_a: set[frozenset] = set()
    for lk in links:
        pair = frozenset([lk.place_id_a, lk.place_id_b])
        if pair not in seen_a and lk.place_id_a in pos and lk.place_id_b in pos:
            seen_a.add(pair)
            attract_pairs.append((lk.place_id_a, lk.place_id_b))
    for pl in places:
        if pl.parent_place_id and pl.parent_place_id in pos and pl.id in pos:
            pair = frozenset([pl.parent_place_id, pl.id])
            if pair not in seen_a:
                seen_a.add(pair)
                attract_pairs.append((pl.parent_place_id, pl.id))

    for step in range(iterations):
        disp: Dict[str, List[float]] = {pid: [0.0, 0.0] for pid in ids}
        t_ratio = 1.0 - step / iterations
        temp = k * (t_ratio ** 1.3)

        # Repulsión
        for i in range(n):
            uid = ids[i]
            for j in range(i + 1, n):
                vid = ids[j]
                dx = pos[uid][0] - pos[vid][0]
                dy = pos[uid][1] - pos[vid][1]
                dist = math.hypot(dx, dy) or 0.01

                if dist < min_node_dist:
                    force = (k * k) / dist + (min_node_dist - dist) ** 2 * 0.75
                else:
                    force = (k * k) / dist

                ux, uy = dx / dist, dy / dist
                disp[uid][0] += ux * force
                disp[uid][1] += uy * force
                disp[vid][0] -= ux * force
                disp[vid][1] -= uy * force

        # Atracción
        for a_id, b_id in attract_pairs:
            dx = pos[a_id][0] - pos[b_id][0]
            dy = pos[a_id][1] - pos[b_id][1]
            dist = math.hypot(dx, dy) or 0.01
            force = (dist * dist) / k
            ux, uy = dx / dist, dy / dist
            disp[a_id][0] -= ux * force
            disp[a_id][1] -= uy * force
            disp[b_id][0] += ux * force
            disp[b_id][1] += uy * force

        # Aplicar con temperatura
        for pid in ids:
            dx, dy = disp[pid]
            d = math.hypot(dx, dy) or 0.01
            move = min(d, temp)
            pos[pid][0] += (dx / d) * move
            pos[pid][1] += (dy / d) * move

    # ── Fase 3: Refinamiento de Separación Garantizada ───────────────────────
    for _ in range(35):
        changed = False
        for i in range(n):
            uid = ids[i]
            for j in range(i + 1, n):
                vid = ids[j]
                dx = pos[uid][0] - pos[vid][0]
                dy = pos[uid][1] - pos[vid][1]
                dist = math.hypot(dx, dy) or 0.01
                if dist < min_node_dist:
                    push = (min_node_dist - dist) / 2.0 + 2.0
                    ux, uy = dx / dist, dy / dist
                    pos[uid][0] += ux * push
                    pos[uid][1] += uy * push
                    pos[vid][0] -= ux * push
                    pos[vid][1] -= uy * push
                    changed = True
        if not changed:
            break

    # ── Fase 4: Anti-cruce de Aristas ───────────────────────────────────────
    if n <= 30 and attract_pairs:
        def _cross(p1, p2, p3, p4) -> bool:
            d1x = p2[0] - p1[0]; d1y = p2[1] - p1[1]
            d2x = p4[0] - p3[0]; d2y = p4[1] - p3[1]
            det = d1x * d2y - d1y * d2x
            if abs(det) < 1e-8:
                return False
            t = ((p3[0] - p1[0]) * d2y - (p3[1] - p1[1]) * d2x) / det
            u = ((p3[0] - p1[0]) * d1y - (p3[1] - p1[1]) * d1x) / det
            return 0.03 < t < 0.97 and 0.03 < u < 0.97

        def _total_crossings() -> int:
            cnt = 0
            m = len(attract_pairs)
            for i in range(m):
                a1, a2 = attract_pairs[i]
                for j in range(i + 1, m):
                    b1, b2 = attract_pairs[j]
                    if len({a1, a2, b1, b2}) < 4:
                        continue
                    if _cross(pos[a1], pos[a2], pos[b1], pos[b2]):
                        cnt += 1
            return cnt

        current_crossings = _total_crossings()
        for _ in range(6):
            improved = False
            for i in range(n):
                for j in range(i + 1, n):
                    uid, vid = ids[i], ids[j]
                    pos[uid], pos[vid] = pos[vid], pos[uid]
                    nc = _total_crossings()
                    if nc < current_crossings:
                        current_crossings = nc
                        improved = True
                    else:
                        pos[uid], pos[vid] = pos[vid], pos[uid]
            if not improved or current_crossings == 0:
                break

    return {pid: (pos[pid][0], pos[pid][1]) for pid in ids}
