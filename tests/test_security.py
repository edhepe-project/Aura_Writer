import pytest
import os
from core.security import SecurityManager

def test_encrypt_decrypt_roundtrip(dummy_password):
    data = b"En un lugar de la Mancha, de cuyo nombre no quiero acordarme..."
    encrypted = SecurityManager.encrypt_data(dummy_password, data)

    assert encrypted.startswith(SecurityManager._MAGIC_V2)
    assert SecurityManager.is_v2_format(encrypted)

    decrypted = SecurityManager.decrypt_data(dummy_password, encrypted)
    assert decrypted == data

def test_decrypt_invalid_password(dummy_password):
    data = b"Contenido super secreto"
    encrypted = SecurityManager.encrypt_data(dummy_password, data)

    with pytest.raises(ValueError, match="Contraseña incorrecta o archivo corrupto"):
        SecurityManager.decrypt_data("WrongPassword!123", encrypted)

def test_decrypt_corrupt_data(dummy_password):
    data = b"Texto de prueba"
    encrypted = bytearray(SecurityManager.encrypt_data(dummy_password, data))
    # Corromper bytes del cuerpo cifrado
    encrypted[-5] ^= 0xFF

    with pytest.raises(ValueError):
        SecurityManager.decrypt_data(dummy_password, bytes(encrypted))

def test_package_and_unpackage_project(temp_workspace, dummy_password):
    source_dir = os.path.join(temp_workspace, "source")
    target_dir = os.path.join(temp_workspace, "target")
    output_file = os.path.join(temp_workspace, "obra.aura")

    os.makedirs(os.path.join(source_dir, "content"), exist_ok=True)
    with open(os.path.join(source_dir, "content", "cap1.html"), "w", encoding="utf-8") as f:
        f.write("<p>Capítulo uno</p>")

    SecurityManager.package_project(dummy_password, source_dir, output_file)
    assert os.path.exists(output_file)

    SecurityManager.unpackage_project(dummy_password, output_file, target_dir)
    restored_cap = os.path.join(target_dir, "content", "cap1.html")
    assert os.path.exists(restored_cap)
    with open(restored_cap, "r", encoding="utf-8") as f:
        assert f.read() == "<p>Capítulo uno</p>"
