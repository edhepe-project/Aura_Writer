import pytest
import os
import sys
import tempfile
import shutil

# Agregar src al sys.path para imports en tests
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, "..", "src"))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from core.models import (
    UniverseMetadata, Obra, Book, Chapter,
    Character, CharacterRelation, UniverseLink, AuthorNote
)

@pytest.fixture
def temp_workspace():
    """Provee un directorio temporal limpio que se destruye tras el test."""
    temp_dir = tempfile.mkdtemp(prefix="test_aura_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def dummy_password():
    return "MasterSecretKey!2026#Novel"

@pytest.fixture
def sample_universe():
    """Crea un UniverseMetadata de prueba con personajes, relaciones y capítulos."""
    char1 = Character(
        id="char_1",
        name="Arthur Pendragon",
        role="Protagonista",
        description="Rey legendario de Britania. El Héroe."
    )
    char2 = Character(
        id="char_2",
        name="Guinevere",
        role="Secundario",
        description="Reina consorte. El Cuidador."
    )
    char3 = Character(
        id="char_3",
        name="Lancelot du Lac",
        role="Antagonista",
        description="Caballero de la mesa redonda. El Guerrero."
    )
    char4 = Character(
        id="char_4",
        name="Galahad",
        role="Secundario",
        description="Hijo de Lancelot. El Inocente."
    )

    rel1 = CharacterRelation(id="rel_1", char_id_a="char_1", char_id_b="char_2", relation_type="pareja", label="Esposos", intensity=4)
    rel2 = CharacterRelation(id="rel_2", char_id_a="char_3", char_id_b="char_2", relation_type="pareja", label="Amor secreto", intensity=5)
    rel3 = CharacterRelation(id="rel_3", char_id_a="char_1", char_id_b="char_3", relation_type="amigo", label="Compañeros", intensity=3)
    rel4 = CharacterRelation(id="rel_4", char_id_a="char_3", char_id_b="char_4", relation_type="descendiente", label="Padre e hijo", intensity=4)

    chap1 = Chapter(id="chap_1", title="Capítulo 1: El Inicio", characters_present=["char_1", "char_2"])
    chap2 = Chapter(id="chap_2", title="Capítulo 2: El Duelo", characters_present=["char_1", "char_3"])
    book1 = Book(id="book_1", title="Libro I", capitulos=[chap1, chap2])
    obra1 = Obra(id="obra_1", title="La Leyenda de Camelot", libros=[book1])

    universe = UniverseMetadata(
        title="Reino de Camelot",
        author="T. H. White",
        characters=[char1, char2, char3, char4],
        relations=[rel1, rel2, rel3, rel4],
        obras=[obra1]
    )
    return universe
