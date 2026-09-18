import pytest
from core.models import UniverseMetadata, Obra, Book, Chapter, Character, Place, AuthorNote
from core.project_manager import ProjectManager
from ui.search.engine import SearchEngine, highlight_text, extract_snippet

@pytest.fixture
def populated_project(temp_workspace, dummy_password):
    pm = ProjectManager()
    pm.create_new_project("Universo Búsqueda", "Autor", dummy_password, f"{temp_workspace}/search.aura")
    
    # Capítulos
    cap1 = pm.create_chapter("Capítulo 1", "<p>El dragón dorado despertó en la cueva oscura.</p>")
    cap2 = pm.create_chapter("Capítulo 2", "<p>La princesa invocó la espada de fuego.</p>")
    pm.metadata.obras[0].libros[0].capitulos.extend([cap1, cap2])
    
    # Personajes
    char1 = Character(id="c1", name="Aethelgard", role="Protagonista", description="Guerrero del norte", distinctive_voice="Grave")
    pm.metadata.characters.append(char1)
    
    # Lugares
    place1 = Place(id="p1", name="Valle de Cristal", description="Tierras sagradas cubiertas de escarcha.")
    pm.metadata.places.append(place1)
    
    # Notas
    note1 = AuthorNote(id="n1", title="Profecía", content="El elegido nacerá bajo el cometa.")
    pm.metadata.author_notes.append(note1)
    
    return pm

def test_search_engine_chapters(populated_project):
    engine = SearchEngine(populated_project)
    results = engine.search("dragón")
    assert len(results) == 1
    assert results[0]["item_type"] == "chapter"
    assert results[0]["title"] == "Capítulo 1"

def test_search_engine_characters(populated_project):
    engine = SearchEngine(populated_project)
    results = engine.search("Aethelgard")
    assert len(results) == 1
    assert results[0]["item_type"] == "character"
    assert results[0]["title"] == "Aethelgard"

def test_search_engine_places(populated_project):
    engine = SearchEngine(populated_project)
    results = engine.search("Cristal", scope="Lugares")
    assert len(results) == 1
    assert results[0]["item_type"] == "place"
    assert results[0]["title"] == "Valle de Cristal"

def test_search_engine_notes(populated_project):
    engine = SearchEngine(populated_project)
    results = engine.search("cometa", scope="Notas")
    assert len(results) == 1
    assert "Profecía" in results[0]["title"]
