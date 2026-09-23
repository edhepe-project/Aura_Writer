"""
Worker background thread para calcular la distribución jerárquica inicial de los bloques del Cronograma.
Organiza los nodos por niveles de precedencia topológica (de izquierda a derecha).
"""

from PyQt6.QtCore import QThread, pyqtSignal as Signal
from core.models import StoryBlock, StoryArc


class StoryLayoutWorker(QThread):
    layout_finished = Signal(dict)  # block_id -> (x, y)

    def __init__(self, blocks: list[StoryBlock], arcs: list[StoryArc]):
        super().__init__()
        self.blocks = blocks
        self.arcs = arcs

    def run(self):
        if not self.blocks:
            self.layout_finished.emit({})
            return

        # Constantes de espaciado
        LEVEL_X_SPACING = 320.0
        NODE_Y_SPACING = 160.0

        # Mapas de in-degree y adyacencia
        in_degree = {b.id: 0 for b in self.blocks}
        adj = {b.id: [] for b in self.blocks}

        for a in self.arcs:
            if a.from_block in adj and a.to_block in in_degree:
                adj[a.from_block].append(a.to_block)
                in_degree[a.to_block] += 1

        # Asignar niveles (Nivel 0 = raices / sin predecesores)
        levels = {}
        queue = [b.id for b in self.blocks if in_degree[b.id] == 0]
        
        # Si todos tienen in-degree > 0 (ciclos), meter el primero como nivel 0
        if not queue:
            queue = [self.blocks[0].id]

        current_level = 0
        visited = set()

        while queue:
            next_queue = []
            for node_id in queue:
                if node_id in visited:
                    continue
                visited.add(node_id)
                levels[node_id] = current_level

                for neighbor in adj[node_id]:
                    if neighbor not in visited:
                        next_queue.append(neighbor)
            queue = next_queue
            current_level += 1

        # Tratar nodos no alcanzados (islas desconectadas)
        for b in self.blocks:
            if b.id not in levels:
                levels[b.id] = 0

        # Agrupar nodos por nivel
        level_groups = {}
        for b_id, lvl in levels.items():
            level_groups.setdefault(lvl, []).append(b_id)

        # Calcular coordenadas (X, Y)
        positions = {}
        for lvl, node_ids in level_groups.items():
            x = lvl * LEVEL_X_SPACING
            total_h = len(node_ids) * NODE_Y_SPACING
            start_y = -total_h / 2.0

            for i, node_id in enumerate(node_ids):
                y = start_y + i * NODE_Y_SPACING
                positions[node_id] = (x, y)

        self.layout_finished.emit(positions)
