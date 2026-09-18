"""
Unit tests for Place model extensions in Aura Writer.
"""
import pytest
from core.models import Place, UniverseMetadata, PLACE_CATEGORIES, PLACE_ICONS


def test_place_default_initialization():
    p = Place(name="Castillo del Alba")
    assert p.name == "Castillo del Alba"
    assert p.category == "Reino / Nación"
    assert p.parent_place_id == ""
    assert p.climate_atmosphere == ""
    assert p.sensory_details == ""
    assert p.lore_history == ""
    assert p.notes == ""
    assert p.image_asset == ""
    assert len(p.id) > 0


def test_place_enriched_fields():
    p = Place(
        name="Bosque Sombrío",
        category="Naturaleza / Bosque",
        description="Un bosque envuelto en una niebla milenaria.",
        climate_atmosphere="Frío, húmedo y perpetuamente nublado.",
        sensory_details="Olor a pino mojado y tierra fértil; crujido constante de ramas.",
        lore_history="Se dice que aquí los antiguos reyes druidas sellaron el portal.",
        notes="Importante para el capítulo 4.",
        image_asset="maps/bosque.png"
    )
    assert p.category in PLACE_CATEGORIES
    assert p.category in PLACE_ICONS
    assert p.climate_atmosphere.startswith("Frío")
    assert p.sensory_details.startswith("Olor")
    assert p.lore_history.startswith("Se dice")
    assert p.image_asset == "maps/bosque.png"


def test_universe_metadata_places_serialization():
    p1 = Place(name="Capital Solar", category="Ciudad / Asentamiento")
    p2 = Place(name="Distrito Real", category="Edificio / Interior", parent_place_id=p1.id)

    meta = UniverseMetadata(title="Universo Fantasía", places=[p1, p2])
    data = meta.model_dump()

    assert len(data["places"]) == 2
    assert data["places"][1]["parent_place_id"] == p1.id

    # Deserialización
    meta_restored = UniverseMetadata.model_validate(data)
    assert len(meta_restored.places) == 2
    assert meta_restored.places[0].name == "Capital Solar"
    assert meta_restored.places[1].parent_place_id == p1.id
