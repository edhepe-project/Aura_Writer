"""
Modelo de datos de Aura Writer.

Jerarquía del universo literario:

    UNIVERSO
    ├── characters[]        ← Personajes globales
    ├── places[]            ← Lugares globales
    ├── relations[]         ← Grafo de relaciones entre personajes
    ├── universe_links[]    ← Conexiones del mapa mental
    ├── medias[]            ← Mapas/imágenes a nivel universo
    └── obras[]
        └── OBRA
            ├── medias[]    ← Mapas/imágenes a nivel obra
            └── libros[]
                └── LIBRO
                    └── capitulos[]
                        └── CAPÍTULO
                            ├── medias[]        ← Imágenes dentro del capítulo
                            ├── author_notes[]  ← Notas de autor (no exportables por defecto)
                            └── revisions[]     ← Historial de versiones guardadas
"""

from __future__ import annotations

from typing import List, Dict, Optional, Any
import uuid
from datetime import datetime, timezone
from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


# ======================================================================
# Nodos hoja
# ======================================================================

class MediaNode(BaseModel):
    """Imagen o mapa insertado en el árbol narrativo."""
    id: str = Field(default_factory=_new_id)
    title: str = "Nueva imagen"
    image_asset: str = ""       # ruta relativa dentro de assets/
    caption: str = ""           # pie de foto opcional
    position: str = "after"     # "before" | "after" | "inline"
    # Campos nuevos de metadatos
    alt_text: str = ""
    width: Optional[int] = None
    height: Optional[int] = None
    created_at: datetime = Field(default_factory=_now)


class AuthorNote(BaseModel):
    """Nota de autor — no se exporta por defecto."""
    id: str = Field(default_factory=_new_id)
    title: str = "Nota"
    content: str = ""
    export: bool = False        # el usuario puede activar la exportación
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class ChapterRevision(BaseModel):
    """Instantánea de un capítulo en un punto del tiempo."""
    id: str = Field(default_factory=_new_id)
    content_file: str = ""
    created_at: datetime = Field(default_factory=_now)
    description: str = "Revisión manual"


# ======================================================================
# Jerarquía narrativa
# ======================================================================

class Chapter(BaseModel):
    id: str = Field(default_factory=_new_id)
    title: str = "Nuevo Capítulo"
    content_file: str = ""          # archivo .html en content/
    status: str = "Borrador"        # Borrador | Revisado | Finalizado
    pov: str = ""
    tags: List[str] = Field(default_factory=list)
    characters_present: List[str] = Field(default_factory=list)  # IDs de personaje
    medias: List[MediaNode] = Field(default_factory=list)
    author_notes: List[AuthorNote] = Field(default_factory=list)
    # Nuevo historial de revisiones
    revisions: List[ChapterRevision] = Field(default_factory=list)
    # Timestamps
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class Book(BaseModel):
    id: str = Field(default_factory=_new_id)
    title: str = "Nuevo Libro"
    capitulos: List[Chapter] = Field(default_factory=list)
    medias: List[MediaNode] = Field(default_factory=list)       # imágenes a nivel libro (hermanas de capítulos)
    author_notes: List[AuthorNote] = Field(default_factory=list)
    content_order: List[Dict[str, str]] = Field(default_factory=list)     # [{"type":"chapter"|"media", "id":"..."}]
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class Obra(BaseModel):
    id: str = Field(default_factory=_new_id)
    title: str = "Nueva Obra"
    color: str = "#e67e22"          # color para el grafo de relaciones
    medias: List[MediaNode] = Field(default_factory=list)  # mapas a nivel obra
    libros: List[Book] = Field(default_factory=list)
    author_notes: List[AuthorNote] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


# ======================================================================
# Personajes y Lugares (globales del universo)
# ======================================================================

class DescriptionEntry(BaseModel):
    """Versión de la descripción de un personaje en una obra/época específica."""
    obra_id: str = ""           # vacío = descripción base/global
    description: str = ""
    notes: str = ""


class Character(BaseModel):
    id: str = Field(default_factory=_new_id)
    name: str = "Nuevo Personaje"
    description: str = ""       # descripción general del personaje
    notes: str = ""             # notas privadas del autor
    image_asset: str = ""
    obra_ids: List[str] = Field(default_factory=list)   # obras en las que aparece
    role: str = "Secundario"    # Protagonista | Secundario | Antagonista | Misterioso | Otro
    aliases: List[str] = Field(default_factory=list)    # nombres alternativos para detección
    description_history: List[DescriptionEntry] = Field(default_factory=list)
    # ── Datos biográficos ────────────────────────────────────────
    age: str = ""               # edad (texto libre: "32 años", "Inmortal", etc.)
    birth_date: str = ""        # fecha de nacimiento (texto libre)
    birthplace: str = ""        # lugar de nacimiento
    # ── Los 7 campos esenciales del personaje ────────────────────
    driving_desire: str = ""    # deseo motivador / propósito vital
    deepest_fear: str = ""      # miedo más profundo
    core_values: str = ""       # valores y creencias fundamentales
    transformation_arc: str = ""  # arco de transformación (inicio → medio → final)
    distinctive_voice: str = ""   # tono o voz distintiva
    symbol_metaphor: str = ""   # símbolo o metáfora que representa
    # ── Atributos dinámicos ──────────────────────────────────────
    custom_attributes: Dict[str, str] = Field(default_factory=dict)
    # Timestamps
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    def get_description_for_obra(self, obra_id: str) -> DescriptionEntry:
        """Retorna la entrada de descripción para una obra dada, o la base si no existe."""
        for entry in self.description_history:
            if entry.obra_id == obra_id:
                return entry
        return DescriptionEntry(obra_id=obra_id, description=self.description, notes=self.notes)

    def set_description_for_obra(self, obra_id: str, description: str, notes: str):
        """Crea o actualiza la descripción de este personaje para una obra específica."""
        for entry in self.description_history:
            if entry.obra_id == obra_id:
                entry.description = description
                entry.notes = notes
                return
        self.description_history.append(
            DescriptionEntry(obra_id=obra_id, description=description, notes=notes)
        )


PLACE_CATEGORIES = [
    "Reino / Nación",
    "Ciudad / Poblado",
    "Fortaleza / Castillo",
    "Taberna / Interior",
    "Mazmorra / Cueva",
    "Naturaleza / Bosque",
    "Región Mágica",
    "Planeta / Espacio",
    "Otro"
]

PLACE_ICONS = {
    "Reino / Nación": "👑",
    "Ciudad / Poblado": "🏛️",
    "Fortaleza / Castillo": "🏰",
    "Taberna / Interior": "🍻",
    "Mazmorra / Cueva": "🗝️",
    "Naturaleza / Bosque": "🌲",
    "Región Mágica": "✨",
    "Planeta / Espacio": "🪐",
    "Otro": "📍"
}


class Place(BaseModel):
    id: str = Field(default_factory=_new_id)
    name: str = "Nuevo Lugar"
    category: str = "Reino / Nación"
    parent_place_id: str = ""       # Jerarquía: ID del lugar contenedor
    description: str = ""           # Descripción general del lugar
    climate_atmosphere: str = ""    # Clima, temperatura, iluminación y ambiente
    sensory_details: str = ""       # Olores, sonidos y texturas características
    lore_history: str = ""          # Historia, leyendas, mitos y secretos
    notes: str = ""                 # Notas privadas del autor (no exportables)
    image_asset: str = ""           # Plano o ilustración conceptual en assets/
    custom_attributes: Dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


# ======================================================================
# Grafo de relaciones y mapa mental
# ======================================================================

RELATION_TYPES = ["pareja", "familiar", "descendiente", "rival", "mentor", "amigo", "otro"]

RELATION_COLORS = {
    "pareja": "#e84393",
    "familiar": "#27ae60",
    "descendiente": "#2ecc71",
    "rival": "#e67e22",
    "mentor": "#3498db",
    "amigo": "#9b59b6",
    "otro": "#95a5a6",
}

RELATION_ICONS = {
    "pareja": "",
    "familiar": "",
    "descendiente": "",
    "rival": "",
    "mentor": "",
    "amigo": "",
    "otro": "",
}


class CharacterRelation(BaseModel):
    """Arista del grafo de relaciones entre personajes."""
    id: str = Field(default_factory=_new_id)
    char_id_a: str = ""
    char_id_b: str = ""
    label: str = ""              # descripción libre de la relación
    intensity: int = 1           # 1-5, afecta grosor de la arista
    relation_type: str = "otro"  # pareja | familiar | descendiente | rival | mentor | amigo | otro
    obra_id: str = ""            # vacío = relación universal
    created_at: datetime = Field(default_factory=_now)


class UniverseLink(BaseModel):
    """Conexión visual en el mapa mental del universo."""
    id: str = Field(default_factory=_new_id)
    source_id: str = ""
    target_id: str = ""
    label: str = ""


class TrashedItem(BaseModel):
    """Elemento enviado a la papelera de reciclaje."""
    id: str = Field(default_factory=_new_id)
    original_id: str = ""
    item_type: str = ""   # "obra" | "libro" | "chapter" | "media" | "author_note" | "character"
    title: str = "Elemento eliminado"
    deleted_at: datetime = Field(default_factory=_now)
    original_parent_id: str = ""
    original_parent_type: str = ""
    data: Dict[str, Any] = Field(default_factory=dict)


# ======================================================================
# Raíz del universo
# ======================================================================

class UniverseMetadata(BaseModel):
    """Datos raíz del archivo .aura — representa un universo literario completo."""
    title: str = "Nuevo Universo"
    author: str = ""
    version: str = "2.0"
    characters: List[Character] = Field(default_factory=list)
    places: List[Place] = Field(default_factory=list)
    relations: List[CharacterRelation] = Field(default_factory=list)
    universe_links: List[UniverseLink] = Field(default_factory=list)
    medias: List[MediaNode] = Field(default_factory=list)   # mapas a nivel universo
    obras: List[Obra] = Field(default_factory=list)
    author_notes: List[AuthorNote] = Field(default_factory=list)
    trash: List[TrashedItem] = Field(default_factory=list)  # Papelera de reciclaje
    # ── 2FA (TOTP) ──────────────────────────────────────────
    totp_enabled: bool = False
    totp_secret: str = ""               # secreto base32 para TOTP
    totp_recovery_codes: List[str] = Field(default_factory=list)
    # ── Estado de sesión (para reabrir exactamente donde te quedaste) ────
    last_selected_node_id: str = ""
    # Timestamps
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> UniverseMetadata:
        if "obras" not in data:
            return _migrate_v1_to_v2(data)
        return cls.model_validate(data)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(mode="json")


# ======================================================================
# Migración v1 → v2 (Mantenida para compatibilidad si la UI la llama)
# ======================================================================

def _migrate_v1_to_v2(data: Dict[str, Any]) -> UniverseMetadata:
    """
    Convierte un diccionario meta.json con la estructura antigua:
        ProjectMetadata { parts: [Part { chapters: [Chapter { scenes }] }] }
    al formato UniverseMetadata Pydantic v2.
    """
    raw_parts = data.get("parts") or data.get("hierarchy") or []

    capitulos: List[Chapter] = []
    for part in raw_parts:
        for old_chap in part.get("chapters", []):
            for old_scene in old_chap.get("scenes", []):
                capitulos.append(Chapter(
                    id=old_scene.get("id", str(uuid.uuid4())),
                    title=old_scene.get("title", "Sin título"),
                    content_file=old_scene.get("content_file", ""),
                    status=old_scene.get("status", "Borrador"),
                    pov=old_scene.get("pov", ""),
                    tags=old_scene.get("tags", []),
                    characters_present=old_scene.get("characters_present", []),
                ))
            # Si no había escenas, el capítulo viejo es el capítulo nuevo
            if not old_chap.get("scenes"):
                capitulos.append(Chapter(
                    id=old_chap.get("id", str(uuid.uuid4())),
                    title=old_chap.get("title", "Sin título"),
                ))

    book = Book(title=data.get("title", "Libro 1"), capitulos=capitulos)
    obra = Obra(title=data.get("title", "Obra migrada"), libros=[book])

    # Convertir personajes y lugares desde los dicts crudos usando Pydantic
    chars = [Character.model_validate(c) for c in data.get("characters", [])]
    places = [Place.model_validate(p) for p in data.get("places", [])]

    return UniverseMetadata(
        title=data.get("title", "Universo migrado"),
        author=data.get("author", ""),
        version="2.0",
        characters=chars,
        places=places,
        obras=[obra],
    )
