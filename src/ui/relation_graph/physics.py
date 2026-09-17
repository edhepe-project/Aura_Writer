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
    Layout espacioso y navegable — pensado para zoom/pan, NO para caber en pantalla.
    Con N=200 nodos el canvas resultante mide ~4000-6000px de diámetro.
    Los personajes tienen espacio para 'respirar' y crecer con su arco narrativo.
    """
    total_count = len(char_map)
    if total_count == 0:
        return {}, 800.0

    # Ordenar por peso narrativo
    sorted_chars = sorted(char_map.keys(),
                          key=lambda c: metrics_map.get(c, CharacterMetrics()).weight,
                          reverse=True)

    # 1. Clasificar en Core / Primary / Minor
    core_nodes = [c for c in sorted_chars if metrics_map.get(c, CharacterMetrics()).tier == "core"]
    if not core_nodes:
        core_nodes = sorted_chars[:max(1, min(6, total_count // 10))]
    core_set = set(core_nodes)

    primary_nodes = [c for c in sorted_chars
                     if c not in core_set and metrics_map.get(c, CharacterMetrics()).tier == "primary"]
    minor_nodes   = [c for c in sorted_chars
                     if c not in core_set and c not in primary_nodes]

    positions: Dict[str, Tuple[float, float]] = {}

    # ── Peso narrativo por tipo de relación ─────────────────────────────────
    # Cuanto mayor el peso, más fuerte es la "gravedad" entre ambos personajes.
    _TYPE_WEIGHT: Dict[str, float] = {
        "familia":     3.0,   # vínculo de sangre → siempre cerca
        "familiar":    3.0,
        "amor":        2.8,   # máxima proximidad emocional
        "pareja":      2.8,
        "mentor":      2.5,   # el aprendiz gravita al maestro
        "aliado":      2.0,   # causa compartida → espacio compartido
        "rival":       1.8,   # los enemigos también se orbitan
        "enemigo":     1.8,
        "descendiente":2.2,
        "amigo":       1.8,
        "otro":        1.0,
        "pacto":       2.0,
    }
    # Bonus multiplicador según el tier del ancla
    _TIER_BONUS: Dict[str, float] = {"core": 1.4, "primary": 1.0, "minor": 0.6}

    # Construir: adj_map (vecinos) + rel_score_map (score narrativo de cada par)
    adj_map: Dict[str, List[str]] = {}
    rel_score_map: Dict[Tuple[str, str], float] = {}   # (a,b) → score
    for rel in vis_rels:
        a = getattr(rel, "char_id_a", getattr(rel, "source", None))
        b = getattr(rel, "char_id_b", getattr(rel, "target", None))
        if a and b:
            sa, sb = str(a), str(b)
            adj_map.setdefault(sa, []).append(sb)
            adj_map.setdefault(sb, []).append(sa)
            # Score = intensidad × peso del tipo de relación
            rtype = str(getattr(rel, "relation_type", "otro")).lower()
            intensity = max(1, int(getattr(rel, "intensity", 3)))
            score = intensity * _TYPE_WEIGHT.get(rtype, 1.0)
            pair = (min(sa, sb), max(sa, sb))
            # Si hay relaciones múltiples entre el mismo par, sumamos (son más fuertes juntas)
            rel_score_map[pair] = rel_score_map.get(pair, 0.0) + score

    def _narrative_score(a: str, b: str) -> float:
        """Score narrativo entre dos personajes (simétrico)."""
        pair = (min(a, b), max(a, b))
        base = rel_score_map.get(pair, 0.0)
        # Multiplicar por bonus del tier del posible ancla (b)
        tier_b = metrics_map.get(b, CharacterMetrics()).tier
        return base * _TIER_BONUS.get(tier_b, 1.0)

    # ── 2. Colocar nodos Core en un anillo generoso ────────────────────────────
    # Escala: cada nodo necesita ~200px de 'zona personal'
    # Para 200 nodos → canvas de ~2800px radio mínimo
    n_core = len(core_nodes)
    # Radio del anillo de titanes — grande para separar sus galaxias satélites
    core_ring_r = max(700.0, 150.0 + math.sqrt(total_count) * 150.0)

    for si, scid in enumerate(core_nodes):
        if n_core == 1:
            positions[scid] = (0.0, 0.0)
        elif n_core == 2:
            # Dos titanes: polo izquierdo / polo derecho con amplio espacio entre ellos
            offset = core_ring_r * 0.60
            positions[scid] = (-offset if si == 0 else offset, 0.0)
        else:
            ang = 2.0 * math.pi * si / n_core - math.pi / 2
            positions[scid] = (math.cos(ang) * core_ring_r * 0.65,
                               math.sin(ang) * core_ring_r * 0.65)

    # ── 3. Secundarios (Primary): galaxia orbital alrededor de su titán ────────
    # Cada titán tiene su propia 'galaxia' de secundarios orbitando a distancia generosa
    # ── 3. Secundarios (Primary): galaxia orbital expandida con zona de exclusión
    # Agrupar primaries por su titán de mayor gravedad narrativa
    primary_set = set(primary_nodes)
    titan_primaries: Dict[str, List[str]] = {c: [] for c in core_nodes}
    unanchored_primaries: List[str] = []

    for pcid in primary_nodes:
        best_titan = None
        best_score = -1.0
        for nb in adj_map.get(pcid, []):
            if nb in core_set:
                sc = _narrative_score(pcid, nb)
                if sc > best_score:
                    best_score = sc
                    best_titan = nb
        if best_titan:
            titan_primaries[best_titan].append(pcid)
        else:
            unanchored_primaries.append(pcid)

    for pcid in unanchored_primaries:
        best_titan = max(core_nodes, key=lambda c: metrics_map.get(c, CharacterMetrics()).weight)
        titan_primaries[best_titan].append(pcid)

    GOLDEN_ANGLE = 2.39996322972865332  # radianes (~137.5 grados)

    for titan_id, sats in titan_primaries.items():
        tx, ty = positions[titan_id]
        r_titan = metrics_map.get(titan_id, CharacterMetrics()).base_radius
        # Zona de exclusión amplia alrededor del Titán (mínimo 600px de radio libre)
        inner_deadzone = max(550.0, r_titan * 5.0)
        for idx, pcid in enumerate(sats):
            r_dist = inner_deadzone + math.sqrt(idx + 1) * 220.0
            theta = (idx + 1) * GOLDEN_ANGLE
            positions[pcid] = (tx + math.cos(theta) * r_dist, ty + math.sin(theta) * r_dist)

    # ── 4. Menores: órbita con zona de exclusión alrededor de su ancla ────────
    anchor_minors: Dict[str, List[str]] = {}
    unanchored_minors: List[str] = []

    for m_id in minor_nodes:
        best_anchor = None
        best_score = -1.0
        for nb in adj_map.get(m_id, []):
            if nb in positions:
                sc = _narrative_score(m_id, nb)
                if sc > best_score:
                    best_score = sc
                    best_anchor = nb
        if best_anchor:
            anchor_minors.setdefault(best_anchor, []).append(m_id)
        else:
            unanchored_minors.append(m_id)

    # Distribuir menores en espiral áurea con zona de seguridad alrededor del ancla
    for anchor_id, m_list in anchor_minors.items():
        ax, ay = positions[anchor_id]
        r_anchor = metrics_map.get(anchor_id, CharacterMetrics()).base_radius
        anchor_deadzone = max(320.0, r_anchor * 4.0)
        for m_idx, m_id in enumerate(m_list):
            m_dist = anchor_deadzone + math.sqrt(m_idx + 1) * 160.0
            m_theta = (m_idx + 1) * GOLDEN_ANGLE
            positions[m_id] = (ax + math.cos(m_theta) * m_dist, ay + math.sin(m_theta) * m_dist)

    # Menores sin ninguna relación: gran halo exterior de la galaxia
    for u_idx, u_id in enumerate(unanchored_minors):
        u_dist = core_ring_r * 1.8 + math.sqrt(u_idx + 1) * 180.0
        u_theta = (u_idx + 1) * GOLDEN_ANGLE
        positions[u_id] = (math.cos(u_theta) * u_dist, math.sin(u_theta) * u_dist)

    # ── 5. Relajación por repulsión anti-superposición ─────────────────────────
    # ── 5. Física Planetaria Real de Repulsión (Ley de Coulomb / N-Body) ───────
    # Todos los personajes se repelen como planetas con carga del mismo signo
    nodes_list = list(char_map.keys())
    n = len(nodes_list)
    max_it = 28 if n <= 300 else (18 if n <= 700 else 12)

    if max_it > 0:
        # Precomputar radios físicos y zonas de exclusión mínimas de cada planeta
        radius_dict = {nid: metrics_map.get(nid, CharacterMetrics()).base_radius for nid in nodes_list}
        cell_size = 600.0

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
                        if u >= v: continue
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
                        # Distancia mínima obligatoria: suma de sus radios + colchón de aire amplio
                        min_distance = (ru + rv) * 2.4 + 160.0

                        if dist_sq < min_distance * min_distance:
                            dist = math.sqrt(dist_sq)
                            # Fuerza de repulsión gravitatoria inversa / choque elástico
                            overlap = (min_distance - dist)
                            force = (overlap / min_distance) * 45.0 + 8.0
                            ux, uy = (dx / dist) * force, (dy / dist) * force
                            disp[u][0] += ux; disp[u][1] += uy
                            disp[v][0] -= ux; disp[v][1] -= uy

            # Aplicar desplazamientos limitados por la temperatura
            for nid in nodes_list:
                d = math.hypot(disp[nid][0], disp[nid][1])
                if d > 0:
                    step = min(d, temp)
                    positions[nid] = (
                        positions[nid][0] + disp[nid][0] / d * step,
                        positions[nid][1] + disp[nid][1] / d * step
                    )

    return positions, core_ring_r


