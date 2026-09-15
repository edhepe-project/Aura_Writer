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

@pytest.fixture
def temp_workspace():
    """Provee un directorio temporal limpio que se destruye tras el test."""
    temp_dir = tempfile.mkdtemp(prefix="test_aura_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def dummy_password():
    return "MasterSecretKey!2026#Novel"
