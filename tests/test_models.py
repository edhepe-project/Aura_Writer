import pytest
import json
from core.models import (
    UniverseMetadata, Obra, Book, Chapter,
    Character, CharacterRelation, UniverseLink, AuthorNote
)

def test_models_hierarchy_serialization():
    chapter = Chapter(title="El Despertar", content_file="c1.html", pov="Protagonista")
    book = Book(title="Tomo I", capitulos=[chapter])
    obra = Obra(title="Crónicas del Alba", libros=[book])
    universe = UniverseMetadata(title="Universo Principal", author="Autor de Prueba", obras=[obra])

    char = Character(name="Kaelen", role="Protagonista", bio="Guerrero errante")
    universe.characters.append(char)

    json_str = universe.model_dump_json()
    data = json.loads(json_str)

    restored = UniverseMetadata.model_validate(data)
    assert restored.title == "Universo Principal"
    assert len(restored.obras) == 1
    assert restored.obras[0].libros[0].capitulos[0].title == "El Despertar"
    assert len(restored.characters) == 1
    assert restored.characters[0].name == "Kaelen"

def test_author_note_default_flags():
    note = AuthorNote(title="Idea secundaria", content="Revisar ritmo del diálogo")
    assert note.export is False
    assert len(note.id) > 0

def test_character_relation_creation():
    rel = CharacterRelation(char_id_a="id-1", char_id_b="id-2", relation_type="amigo", intensity=3)
    assert rel.relation_type == "amigo"
    assert rel.intensity == 3
