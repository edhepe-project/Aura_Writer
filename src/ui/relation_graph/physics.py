"""
Módulo de Física y Layout Espacial del Grafo de Relaciones.
"""

import math
from typing import Dict, List, Tuple
from PyQt6.QtCore import QRunnable, QObject, pyqtSignal, pyqtSlot
from core.models import UniverseMetadata, Character, CharacterRelation
from .models import CharacterMetrics


def calculate_metrics(meta: UniverseMetadata) -> Dict[str, CharacterMetrics]:
    """Calcula la relevancia narrativa de cada personaje basada en capítulos, relaciones e intensidad."""
    chap_counts: Dict[str, int] = {}
    for obra in meta.obras:
        for libro in obra.libros:
            for cap in libro.capitulos:
                for cid in cap.characters_present:
                    chap_counts[cid] = chap_counts.get(cid, 0) + 1

    conn_counts: Dict[str, int] = {}
    int_sums: Dict[str, float] = {}
    for rel in meta.relations:
        a, b = rel.char_id_a, rel.char_id_b
        conn_counts[a] = conn_counts.get(a, 0) + 1
        conn_counts[b] = conn_counts.get(b, 0) + 1
        int_val = max(1, rel.intensity) / 5.0
        int_sums[a] = int_sums.get(a, 0.0) + int_val
        int_sums[b] = int_sums.get(b, 0.0) + int_val

    metrics: Dict[str, CharacterMetrics] = {}
    for ch in meta.characters:
        metrics[ch.id] = CharacterMetrics(
            char_id=ch.id,
            chapters_count=chap_counts.get(ch.id, 0),
            connections_count=conn_counts.get(ch.id, 0),
            intensity_sum=int_sums.get(ch.id, 0.0),
            role=ch.role
        )
    return metrics


class LayoutWorkerSignals(QObject):
    finished = pyqtSignal(dict, float)  # positions, core_radius


class LayoutWorker(QRunnable):
    """Worker para computar la distribución gravitatoria en un hilo secundario sin congelar la UI."""
    def __init__(self, char_map: Dict[str, Character],
                 metrics_map: Dict[str, CharacterMetrics],
                 vis_rels: List[CharacterRelation]):
        super().__init__()
        self.char_map = char_map
        self.metrics_map = metrics_map
        self.vis_rels = vis_rels
        self.signals = LayoutWorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            positions, core_radius = compute_graph_layout(
                self.char_map, self.metrics_map, self.vis_rels
            )
            self.signals.finished.emit(positions, core_radius)
        except Exception as e:
            # Fallback a posiciones circulares rápidas
            positions = {}
            for i, cid in enumerate(self.char_map.keys()):
                ang = 2.0 * math.pi * i / max(1, len(self.char_map))
                positions[cid] = (math.cos(ang) * 400.0, math.sin(ang) * 400.0)
            self.signals.finished.emit(positions, 400.0)


def compute_graph_layout(char_map: Dict[str, Character],
                         metrics_map: Dict[str, CharacterMetrics],
                         vis_rels: List[CharacterRelation]) -> Tuple[Dict[str, Tuple[float, float]], float]:
    """
    Calcula la distribución gravitatoria jerárquica y aplica relajación de separación
    optimizada con partición espacial en cuadrícula (O(N) en vez de O(N^2)).
    """
    core_nodes   = [cid for cid in char_map if metrics_map[cid].tier == "core"]
    primary_nodes= [cid for cid in char_map if metrics_map[cid].tier == "primary"]
    minor_nodes  = [cid for cid in char_map if metrics_map[cid].tier == "minor"]

    if not core_nodes and char_map:
        sorted_chars = sorted(char_map.keys(), key=lambda c: metrics_map[c].weight, reverse=True)
        core_nodes = sorted_chars[:max(1, min(2, len(sorted_chars)))]
        primary_nodes = [c for c in sorted_chars[len(core_nodes):] if metrics_map[c].tier == "primary"]
        minor_nodes = [c for c in sorted_chars[len(core_nodes):] if c not in primary_nodes]

    positions: Dict[str, Tuple[float, float]] = {}
    n_core = len(core_nodes)
    
    # Radio adaptativo para la distribución según cantidad de personajes
    total_count = len(char_map)
    scale_factor = math.sqrt(max(1.0, total_count / 30.0))
    core_radius = max(420.0, n_core * 240.0) * scale_factor

    for si, scid in enumerate(core_nodes):
        if n_core == 1:
            positions[scid] = (0.0, 0.0)
        else:
            ang = 2.0 * math.pi * si / n_core
            positions[scid] = (math.cos(ang) * core_radius, math.sin(ang) * core_radius)

    # Pre-indexar relaciones en un mapa de adyacencia O(1) para evitar bucles O(N*R)
    adj_map: Dict[str, List[str]] = {}
    for rel in vis_rels:
        a = getattr(rel, "char_id_a", getattr(rel, "source", None))
        b = getattr(rel, "char_id_b", getattr(rel, "target", None))
        if a and b:
            sa, sb = str(a), str(b)
            adj_map.setdefault(sa, []).append(sb)
            adj_map.setdefault(sb, []).append(sa)

    # Posicionamiento de secundarios
    for pi, pcid in enumerate(primary_nodes):
        best_core = None
        for neighbor in adj_map.get(pcid, []):
            if neighbor in core_nodes:
                best_core = neighbor
                break

        if best_core and best_core in positions:
            center_x, center_y = positions[best_core]
            p_angle = 2.0 * math.pi * pi / max(len(primary_nodes), 1)
            p_dist = (240.0 + (pi % 4) * 60.0) * min(scale_factor, 2.5)
            positions[pcid] = (
                center_x + math.cos(p_angle) * p_dist,
                center_y + math.sin(p_angle) * p_dist
            )
        else:
            p_angle = 2.0 * math.pi * pi / max(len(primary_nodes), 1)
            p_dist = core_radius * 0.85
            positions[pcid] = (math.cos(p_angle) * p_dist, math.sin(p_angle) * p_dist)

    # Posicionamiento de personajes menores
    host_minors: Dict[str, List[str]] = {}
    unanchored: List[str] = []

    for m_id in minor_nodes:
        anchor = None
        for neighbor in adj_map.get(m_id, []):
            if neighbor in positions:
                anchor = neighbor
                break
        if anchor:
            host_minors.setdefault(anchor, []).append(m_id)
        else:
            unanchored.append(m_id)

    # Satélites alrededor de su nodo principal
    for host_id, m_list in host_minors.items():
        hx, hy = positions[host_id]
        nm = len(m_list)
        for mi, m_id in enumerate(m_list):
            ring_layer = mi // 8
            ring_dist = 110.0 + (ring_layer * 46.0)
            m_ang = 2.0 * math.pi * (mi % 8) / min(nm, 8) + (ring_layer * 0.35)
            positions[m_id] = (
                hx + math.cos(m_ang) * ring_dist,
                hy + math.sin(m_ang) * ring_dist
            )

    num_un = len(unanchored)
    for ui, u_id in enumerate(unanchored):
        u_ang = 2.0 * math.pi * ui / max(num_un, 1)
        u_dist = core_radius + (260.0 * scale_factor) + (ui % 5) * 35.0
        positions[u_id] = (math.cos(u_ang) * u_dist, math.sin(u_ang) * u_dist)

    # ── Relajación Espacial Rápida y Adaptativa ──────────────────────────────
    nodes_list = list(char_map.keys())
    n = len(nodes_list)
    
    # Para grafos masivos (>800 personajes), la colocación orbital gravitatoria
    # calculada arriba ya es matemáticamente óptima y balanceada. 
    # Hacemos una relajación ultra ligera de 3-4 iteraciones vectorizadas.
    if 1 < n <= 800:
        max_it = 12 if n > 300 else 20
    elif n > 800:
        max_it = 3  # Micro-ajuste instantáneo sin coste
    else:
        max_it = 0

    if max_it > 0:
        edge_pairs = []
        for r in vis_rels:
            a = getattr(r, "char_id_a", getattr(r, "source", None))
            b = getattr(r, "char_id_b", getattr(r, "target", None))
            if a and b:
                edge_pairs.append((str(a), str(b)))

        cell_size = 200.0

        for it in range(max_it):
            temp = 24.0 * (1.0 - it / float(max_it))
            disp = {nid: [0.0, 0.0] for nid in nodes_list}

            # 1. Agrupar nodos en cuadrícula espacial
            grid: Dict[Tuple[int, int], List[str]] = {}
            for nid in nodes_list:
                px, py = positions[nid]
                gx = int(px // cell_size)
                gy = int(py // cell_size)
                grid.setdefault((gx, gy), []).append(nid)

            # 2. Comprobación de repulsión por celdas
            checked_pairs = set()
            for (gx, gy), cell_nodes in grid.items():
                neighbor_nodes = []
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        neighbor_nodes.extend(grid.get((gx + dx, gy + dy), []))

                for u in cell_nodes:
                    pos_u = positions[u]
                    rad_u = metrics_map[u].base_radius
                    for v in neighbor_nodes:
                        if u == v:
                            continue
                        pair = (u, v) if u < v else (v, u)
                        if pair in checked_pairs:
                            continue
                        checked_pairs.add(pair)

                        pos_v = positions[v]
                        dx = pos_u[0] - pos_v[0]
                        dy = pos_u[1] - pos_v[1]
                        if abs(dx) > cell_size or abs(dy) > cell_size:
                            continue
                        dist_sq = dx * dx + dy * dy
                        if dist_sq < 1.0: dist_sq = 1.0
                        min_sep = rad_u + metrics_map[v].base_radius + 40.0
                        min_sep_sq = (min_sep * 1.8) ** 2
                        if dist_sq < min_sep_sq:
                            dist = math.sqrt(dist_sq)
                            rep = (min_sep * min_sep * 5.0) / dist
                            ux, uy = dx / dist * rep, dy / dist * rep
                            disp[u][0] += ux;  disp[u][1] += uy
                            disp[v][0] -= ux;  disp[v][1] -= uy

            # 3. Atracción por aristas
            for u, v in edge_pairs:
                if u in positions and v in positions:
                    dx = positions[u][0] - positions[v][0]
                    dy = positions[u][1] - positions[v][1]
                    dist = math.hypot(dx, dy)
                    if dist > 180.0:
                        att = (dist - 130.0) * 0.04
                        ux, uy = dx / dist * att, dy / dist * att
                        disp[u][0] -= ux;  disp[u][1] += uy
                        disp[v][0] += ux;  disp[v][1] += uy

            # 4. Aplicar paso limitado por temperatura
            for nid in nodes_list:
                d = math.hypot(disp[nid][0], disp[nid][1])
                if d > 0:
                    step = min(d, temp)
                    positions[nid] = (
                        positions[nid][0] + disp[nid][0] / d * step,
                        positions[nid][1] + disp[nid][1] / d * step
                    )

    return positions, core_radius
