"""
test_load_and_validate_project.py — Pruebas de integración de todos los módulos y subsistemas de Aura Writer.
"""

import os
import sys
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from core.project_manager import ProjectManager
from ui.search.engine import SearchEngine

def validate_all_subsystems():
    aura_path = os.path.join(os.path.dirname(__file__), "Proyecto_Prueba_Integral.aura")
    password = "1234"

    print("=== INICIANDO VALIDACIÓN INTEGRAL DE AURA WRITER ===")
    pm = ProjectManager()
    
    # 1. Abrir y Descifrar Proyecto
    print("1. Probando apertura y descifrado V2/V3 SecurityManager...")
    pm.open_project(aura_path, password)
    assert pm.metadata is not None, "Metadata es None tras abrir el proyecto"
    assert pm.metadata.title == "El Legado de Eldoria", f"Título incorrecto: {pm.metadata.title}"
    print("   [OK] Proyecto descifrado y cargado correctamente.")

    # 2. Validar Estructura de Obras, Libros y Capítulos
    print("2. Validar estructura de árbol narrativo (Obras/Libros/Capítulos)...")
    assert len(pm.metadata.obras) == 2, f"Se esperaban 2 obras, hay {len(pm.metadata.obras)}"
    obra1 = pm.metadata.obras[0]
    assert len(obra1.libros[0].capitulos) == 2, "Capítulos incorrectos en Libro I"
    print("   [OK] Jerarquía narrativa validada.")

    # 3. Validar Fichas de Personajes y Atributos
    print("3. Validar módulo de Personajes y atributos de esencia...")
    assert len(pm.metadata.characters) == 5, f"Esperados 5 personajes, hay {len(pm.metadata.characters)}"
    valen = next(c for c in pm.metadata.characters if c.name == "Valen Eldarian")
    assert valen.driving_desire != "", "El deseo motivador no se cargó correctamente"
    assert valen.custom_attributes.get("Elemento") == "Luz", "Atributos personalizados no cargados"
    print("   [OK] Personajes y esencia validados.")

    # 4. Validar Atlas de Lugares y Jerarquía
    print("4. Validar Atlas Geográfico y Jerarquía de Escenarios...")
    assert len(pm.metadata.places) == 5, f"Esperados 5 lugares, hay {len(pm.metadata.places)}"
    ciudad = next(p for p in pm.metadata.places if p.name == "Solaria")
    assert ciudad.parent_place_id != "", "Jerarquía de lugar vacía"
    print("   [OK] Atlas y escenarios validados.")

    # 5. Validar Grafo de Relaciones entre Personajes
    print("5. Validar Grafo de Relaciones...")
    assert len(pm.metadata.relations) == 3, "Relaciones faltantes en metadata"
    print("   [OK] Aristas y tipos de relaciones validadas.")

    # 6. Validar Conexiones Geográficas (Place Links)
    print("6. Validar Conexiones Geográficas (Place Links)...")
    assert len(pm.metadata.place_links) == 2, "Place links faltantes"
    print("   [OK] Conexiones geográficas validadas.")

    # 7. Validar Vocabulario Conlang
    print("7. Validar Glosario Conlang...")
    assert len(pm.metadata.custom_vocabulary) == 2, "Vocabulario conlang faltante"
    print("   [OK] Vocabulario conlang validado.")

    # 8. Validar Cronograma Narrativo (Story Blocks & Arcs)
    print("8. Validar Cronograma / Grafo Narrativo...")
    assert len(pm.metadata.story_blocks) == 3, "Story blocks faltantes"
    assert len(pm.metadata.story_arcs) == 2, "Story arcs faltantes"
    print("   [OK] Bloques narrativos y arcos causales validados.")

    # 9. Validar Motor de Búsqueda Global (Search Engine)
    print("9. Probando Motor de Búsqueda Global...")
    searcher = SearchEngine(pm)
    res_valen = searcher.search("Valen", scope="Todo")
    assert len(res_valen) > 0, "Búsqueda por 'Valen' no devolvió resultados"
    res_solaria = searcher.search("Solaria", scope="Lugares")
    assert len(res_solaria) > 0, "Búsqueda de lugar 'Solaria' falló"
    print(f"   [OK] Motor de búsqueda funcional (Resultados para 'Valen': {len(res_valen)}).")

    # 10. Validar Re-Guardado y Cifrado
    print("10. Validar guardado y empaquetado V2...")
    pm.save_project()
    print("   [OK] Re-guardado completado sin errores.")

    # Limpieza de temporal
    if pm.temp_dir and os.path.exists(pm.temp_dir):
        shutil.rmtree(pm.temp_dir, ignore_errors=True)

    print("\n=======================================================")
    print("--- TODOS LOS MODULOS Y SISTEMAS PASARON CON EXITO ---")
    print("=======================================================")

if __name__ == "__main__":
    validate_all_subsystems()
