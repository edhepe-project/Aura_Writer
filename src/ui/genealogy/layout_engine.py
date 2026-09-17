"""
layout_engine.py — Motor Matemático de Árbol Genealógico y Pedigree Jerárquico.
Calcula la disposición espacial por subárboles recursivos (ancestros y descendientes),
garantizando centrado perfecto y evitando colisiones entre ramas familiares.
"""
from __future__ import annotations

from core.models import Character, CharacterRelation


class GenealogyLayoutEngine:
    """Motor que calcula coordenadas (X, Y) y mapas de linaje para el árbol genealógico."""

    CARD_W = 200.0
    CARD_H = 74.0
    V_GAP = 140.0
    PAIR_GAP = 24.0
    BRANCH_GAP = 60.0

    @classmethod
    def compute_layout(
        cls,
        central_char: Character,
        characters: list[Character],
        relations: list[CharacterRelation]
    ) -> tuple[
        dict[str, tuple[float, float]],       # node_coords: cid -> (x, y)
        dict[str, list[str]],                 # child_to_parents: cid -> [p_id, ...]
        dict[str, list[str]],                 # parent_to_children: pid -> [c_id, ...]
        list[str],                            # partners
        list[str]                             # siblings
    ]:
        char_map = {c.id: c for c in characters}
        
        child_to_parents: dict[str, list[str]] = {}
        parent_to_children: dict[str, list[str]] = {}

        for rel in relations:
            if rel.relation_type == "descendiente":
                c_id, p_id = rel.char_id_a, rel.char_id_b
                child_to_parents.setdefault(c_id, []).append(p_id)
                parent_to_children.setdefault(p_id, []).append(c_id)

        # Pareja y Hermanos del personaje principal
        partners: list[str] = []
        siblings: list[str] = []

        for rel in relations:
            if rel.char_id_a != central_char.id and rel.char_id_b != central_char.id:
                continue
            other_id = rel.char_id_b if rel.char_id_a == central_char.id else rel.char_id_a
            if other_id not in char_map:
                continue

            if rel.relation_type == "pareja":
                if other_id not in partners:
                    partners.append(other_id)
            elif rel.relation_type == "familiar":
                if other_id not in siblings:
                    siblings.append(other_id)

        node_coords: dict[str, tuple[float, float]] = {}

        # ── MOTOR RECURSIVO DE SUBÁRBOLES DE ANCESTROS ───────────────────
        def _layout_ancestor_subtree(
            cid: str, current_y: float, visited: set[str] | None = None
        ) -> tuple[float, dict[str, tuple[float, float]]]:
            if visited is None:
                visited = set()
            if cid in visited:
                return cls.CARD_W, {cid: (0.0, current_y)}
            visited.add(cid)

            parents = [p for p in child_to_parents.get(cid, []) if p not in visited]
            if not parents:
                return cls.CARD_W, {cid: (0.0, current_y)}

            if len(parents) == 1:
                p_id = parents[0]
                p_width, p_coords = _layout_ancestor_subtree(p_id, current_y - cls.V_GAP, set(visited))
                coords = {cid: (0.0, current_y)}
                for k, (kx, ky) in p_coords.items():
                    coords[k] = (kx, ky)
                return max(cls.CARD_W, p_width), coords

            # 2+ Padres (Pareja de progenitores)
            p1_id, p2_id = parents[0], parents[1]
            p1_w, p1_coords = _layout_ancestor_subtree(p1_id, current_y - cls.V_GAP, set(visited))
            p2_w, p2_coords = _layout_ancestor_subtree(p2_id, current_y - cls.V_GAP, set(visited))

            gap = max(cls.PAIR_GAP, cls.BRANCH_GAP)
            total_w = p1_w + gap + p2_w

            p1_center_x = -total_w / 2 + p1_w / 2
            p2_center_x = total_w / 2 - p2_w / 2

            coords = {cid: (0.0, current_y)}
            for k, (kx, ky) in p1_coords.items():
                coords[k] = (p1_center_x + kx, ky)
            for k, (kx, ky) in p2_coords.items():
                coords[k] = (p2_center_x + kx, ky)

            return total_w, coords

        _, anc_coords = _layout_ancestor_subtree(central_char.id, 0.0)
        for cid, (cx, cy) in anc_coords.items():
            node_coords[cid] = (cx, cy)

        # ── AGREGAR HERMANOS Y PAREJA EN Y=0 ────────────────────────────
        if siblings:
            leftmost_x = min([x for x, y in node_coords.values() if y == 0.0] + [0.0]) - cls.CARD_W / 2
            for i, s_id in enumerate(siblings):
                sx = leftmost_x - 40.0 - cls.CARD_W / 2 - i * (cls.CARD_W + 40.0)
                node_coords[s_id] = (sx, 0.0)

        if partners:
            rightmost_x = max([x for x, y in node_coords.values() if y == 0.0] + [0.0]) + cls.CARD_W / 2
            p_id = partners[0]
            node_coords[p_id] = (rightmost_x + 80.0 + cls.CARD_W / 2, 0.0)

        # ── MOTOR RECURSIVO DE SUBÁRBOLES DE DESCENDIENTES ───────────────
        main_children = parent_to_children.get(central_char.id, [])

        def _layout_descendant_subtree(
            cid: str, current_y: float, visited: set[str] | None = None
        ) -> tuple[float, dict[str, tuple[float, float]]]:
            if visited is None:
                visited = set()
            if cid in visited:
                return cls.CARD_W, {cid: (0.0, current_y)}
            visited.add(cid)

            children = [ch for ch in parent_to_children.get(cid, []) if ch not in visited]
            if not children:
                return cls.CARD_W, {cid: (0.0, current_y)}

            child_subtrees = []
            total_w = 0.0
            for ch_id in children:
                cw, ccoords = _layout_descendant_subtree(ch_id, current_y + cls.V_GAP, set(visited))
                child_subtrees.append((ch_id, cw, ccoords))
                total_w += cw
            total_w += (len(children) - 1) * cls.BRANCH_GAP

            coords = {cid: (0.0, current_y)}
            start_x = -total_w / 2
            for ch_id, cw, ccoords in child_subtrees:
                ch_center_x = start_x + cw / 2
                for k, (kx, ky) in ccoords.items():
                    coords[k] = (ch_center_x + kx, ky)
                start_x += cw + cls.BRANCH_GAP

            return total_w, coords

        if main_children:
            ch_subtrees = []
            tot_ch_w = 0.0
            for ch_id in main_children:
                cw, ccoords = _layout_descendant_subtree(ch_id, cls.V_GAP)
                ch_subtrees.append((ch_id, cw, ccoords))
                tot_ch_w += cw
            tot_ch_w += (len(main_children) - 1) * cls.BRANCH_GAP

            p_x = node_coords[partners[0]][0] if partners else node_coords[central_char.id][0]
            desc_center_x = (node_coords[central_char.id][0] + p_x) / 2
            start_x = desc_center_x - tot_ch_w / 2
            for ch_id, cw, ccoords in ch_subtrees:
                ch_center_x = start_x + cw / 2
                for k, (kx, ky) in ccoords.items():
                    node_coords[k] = (ch_center_x + kx, ky)
                start_x += cw + cls.BRANCH_GAP

        return node_coords, child_to_parents, parent_to_children, partners, siblings
