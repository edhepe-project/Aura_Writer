"""
hierarchy_engine.py — Motor de jerarquía espacial usando AnyTree.
Responsabilidad única: Modelar la relación continente-contenido entre lugares
(ej: Taberna -> Barrio -> Ciudad -> Reino) y resolver la propagación de presencia.
"""
from typing import Dict, List, Optional, Any
import logging

try:
    from anytree import Node, RenderTree, find_by_attr, PreOrderIter
    _ANYTREE_AVAILABLE = True
except ImportError:
    _ANYTREE_AVAILABLE = False

logger = logging.getLogger(__name__)

class HierarchyEngine:
    """
    Construye y consulta el árbol de jerarquía de lugares del proyecto.
    Permite inferir que si un personaje está en 'Taberna del Dragón',
    automáticamente está en 'Ciudadela Alta' y 'Reino de Eldoria'.
    """

    def __init__(self):
        self._nodes: Dict[str, Any] = {} # place_id -> Node
        self._root = None

    def build_from_places(self, places: List[Any]):
        """
        Construye el bosque/árbol a partir de una lista de objetos Place (models.Place)
        o diccionarios con {'id', 'name', 'parent_id'}.
        """
        if not _ANYTREE_AVAILABLE:
            return

        self._nodes.clear()
        
        # 1. Crear nodos sin padres asignados
        for place in places:
            p_id = getattr(place, "id", None) or (place.get("id") if isinstance(place, dict) else str(place))
            p_name = getattr(place, "name", None) or (place.get("name") if isinstance(place, dict) else str(place))
            self._nodes[p_id] = Node(p_id, display_name=p_name, raw_place=place)

        # 2. Asignar relaciones padre-hijo
        for place in places:
            p_id = getattr(place, "id", None) or (place.get("id") if isinstance(place, dict) else str(place))
            parent_id = getattr(place, "parent_place_id", None) or getattr(place, "parent_id", None) or (place.get("parent_place_id") or place.get("parent_id") if isinstance(place, dict) else None)
            
            if parent_id and parent_id in self._nodes and p_id in self._nodes:
                self._nodes[p_id].parent = self._nodes[parent_id]

    def get_ancestors(self, place_id: str) -> List[str]:
        """
        Retorna la lista de IDs de lugares contenedores (padres, abuelos...) desde el más cercano a la raíz.
        """
        if not _ANYTREE_AVAILABLE or place_id not in self._nodes:
            return []
            
        node = self._nodes[place_id]
        return [ancestor.name for ancestor in reversed(node.ancestors)]

    def get_descendants(self, place_id: str) -> List[str]:
        """
        Retorna la lista de IDs de todos los sub-lugares contenidos en place_id.
        """
        if not _ANYTREE_AVAILABLE or place_id not in self._nodes:
            return []

        node = self._nodes[place_id]
        return [descendant.name for descendant in node.descendants]
