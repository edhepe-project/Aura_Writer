"""
Script de descarga de diccionarios hunspell para Aura Writer.
Ejecutar una vez: python src/core/dicts/download_dicts.py
"""
import urllib.request
import os

BASE_URL = "https://raw.githubusercontent.com/LibreOffice/dictionaries/master"
DICTS_DIR = os.path.dirname(os.path.abspath(__file__))

DICTS = {
    "es": ("es", "es_ES"),
    "en": ("en", "en_US"),
    "fr": ("fr_FR", "fr_FR"),
    "pt": ("pt_PT", "pt_PT"),
}

for lang, (folder, name) in DICTS.items():
    for ext in ("aff", "dic"):
        url = f"{BASE_URL}/{folder}/{name}.{ext}"
        dest = os.path.join(DICTS_DIR, f"{lang}.{ext}")
        if os.path.exists(dest):
            print(f"  [ok] {dest} ya existe")
            continue
        try:
            print(f"  Descargando {url} ...")
            urllib.request.urlretrieve(url, dest)
            print(f"  [ok] {dest}")
        except Exception as e:
            print(f"  [ERROR] {url}: {e}")

print("Listo.")
