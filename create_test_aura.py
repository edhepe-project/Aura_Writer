"""
create_test_aura.py — Generador de archivo .aura de prueba integral para Aura Writer.
Crea un universo rico en personajes, lugares, relaciones, cronogramas, vocabulario,
obras, libros, capítulos y notas para validar todos los módulos del sistema.
"""

import os
import sys
import tempfile
import logging

# Añadir src/ al sys.path para importar la suite de Aura Writer
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from core.models import (
    UniverseMetadata, Character, Place, CharacterRelation,
    PlaceLink, CustomVocabularyEntry, StoryBlock, StoryArc,
    Obra, Book, Chapter, AuthorNote, MediaNode
)
from core.security import SecurityManager

logging.basicConfig(level=logging.INFO)

def build_test_project():
    aura_file_path = os.path.join(os.path.dirname(__file__), "Proyecto_Prueba_Integral.aura")
    password = "1234"

    # Directorio temporal de empaquetado
    temp_dir = tempfile.mkdtemp(prefix="aura_test_gen_")
    os.makedirs(os.path.join(temp_dir, "content"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "assets"), exist_ok=True)

    # 1. Personajes
    c_valen = Character(
        name="Valen Eldarian",
        role="Protagonista",
        race="Humano / Mestizo",
        age="24",
        birthplace="Valle de Solaria",
        driving_desire="Restaurar el equilibrio de la magia en Eldoria y salvar a su orden.",
        deepest_fear="Convertirse en la sombra que juró destruir.",
        core_values="Lealtad inquebrantable, justicia y protección a los indefensos.",
        transformation_arc="De aprendiz dubitativo a líder sabio y compasivo.",
        distinctive_voice="Calmo, formal pero con un matiz de ironía en momentos de tensión.",
        symbol_metaphor="El faro en la tormenta de fuego.",
        aliases=["El Guardián del Alba", "Valen"],
        custom_attributes={"Arma Emblemática": "Espada de Viento", "Elemento": "Luz"}
    )

    c_morgath = Character(
        name="Morgath el Sombrío",
        role="Antagonista",
        race="Nigromante",
        age="140",
        birthplace="Mazmorras de Abismo",
        driving_desire="Dominar la muerte misma y doblegar las facciones libres.",
        deepest_fear="El olvido absoluto y la nada.",
        core_values="El poder es la única verdad suprema.",
        transformation_arc="Consumido totalmente por el poder oscuro.",
        distinctive_voice="Grave, susurrante, resonante.",
        symbol_metaphor="La luna rota.",
        aliases=["Señor del Abismo", "Morgath"],
        custom_attributes={"Arte": "Nigromancia Ancestral"}
    )

    c_lyra = Character(
        name="Archimaga Lyra",
        role="Mentor",
        race="Elfa",
        age="320",
        birthplace="Bosque de los Susurros",
        driving_desire="Proteger los tomos antiguos de la destrucción.",
        deepest_fear="Que la ignorancia destruya la historia de su pueblo.",
        core_values="El saber debe ser custodiado con responsabilidad.",
        transformation_arc="Acepta que debe guiarse por la esperanza y no solo por el deber.",
        distinctive_voice="Solemne, poética y articulada.",
        symbol_metaphor="El roble inmortal.",
        aliases=["La Custodia de Cristal", "Lyra"]
    )

    c_kael = Character(
        name="Kaelen Riven",
        role="Secundario",
        race="Humano",
        age="27",
        birthplace="Puerto Cristal",
        driving_desire="Obtener riqueza y libertad sin ataduras.",
        deepest_fear="La traición de sus camaradas.",
        core_values="La camaradería vale más que el oro.",
        aliases=["Kael", "El Halcón"]
    )

    c_sombra = Character(
        name="La Presencia Silenciosa",
        role="Misterioso",
        race="Desconocido",
        age="Desconocido",
        driving_desire="Observar el destino sin intervenir directamente.",
        symbol_metaphor="El espejo de obsidiana.",
        aliases=["El Observador"]
    )

    # 2. Lugares (Jerarquía)
    p_reino = Place(
        name="Reino de Eldoria",
        category="Reino / Nación",
        climate_atmosphere="Templado en los valles, nevado en las cumbres celestiales.",
        sensory_details="Olor a pino húmedo y azahar; brisa fresca de montaña.",
        lore_history="Fundado hace 1,000 años tras la Guerra de las Gemas.",
        aliases=["Eldoria", "Tierras del Sol"]
    )

    p_ciudad = Place(
        name="Solaria",
        category="Ciudad / Poblado",
        parent_place_id=p_reino.id,
        climate_atmosphere="Cálido y luminoso durante todo el año.",
        sensory_details="Grito de mercaderes, aroma a especias exóticas y pan recién horneado.",
        lore_history="Capital cultural de Eldoria, protegida por muros de cuarzo.",
        aliases=["La Ciudad del Sol", "Ciudad Celestial"]
    )

    p_castillo = Place(
        name="Ciudadela de Cristal",
        category="Fortaleza / Castillo",
        parent_place_id=p_ciudad.id,
        climate_atmosphere="Fresco, majestuoso con eco continuo.",
        sensory_details="Murmullo de fuentes de agua purificada y fragancia de lavanda.",
        lore_history="Hogar del trono de Eldoria y de la orden de los Archimagos.",
        aliases=["La Fortaleza de Cristal"]
    )

    p_bosque = Place(
        name="Bosque de los Susurros",
        category="Naturaleza / Bosque",
        parent_place_id=p_reino.id,
        climate_atmosphere="Húmedo, envuelto en una niebla plateada constante.",
        sensory_details="Crujido de hojas doradas y susurros plateados en el viento.",
        lore_history="Territorio sagrado protegido por ilusiones de los elfos ancestrales."
    )

    p_mazmorra = Place(
        name="Foso de las Sombras",
        category="Mazmorra / Cueva",
        parent_place_id=p_reino.id,
        climate_atmosphere="Gélido, oscuro, con aire enrarecido.",
        sensory_details="Goteo rítmico sobre roca fría y olor a humedad y azufre.",
        lore_history="Antigua prisión subterránea donde mora Morgath."
    )

    # 3. Relaciones de personajes
    rel1 = CharacterRelation(
        char_id_a=c_valen.id,
        char_id_b=c_morgath.id,
        relation_type="rival",
        intensity=5,
        label="Enemigos mortales. Morgath destruyó el templo de Valen."
    )
    rel2 = CharacterRelation(
        char_id_a=c_valen.id,
        char_id_b=c_lyra.id,
        relation_type="mentor",
        intensity=4,
        label="Mentoría mágica y guía espiritual."
    )
    rel3 = CharacterRelation(
        char_id_a=c_valen.id,
        char_id_b=c_kael.id,
        relation_type="amigo",
        intensity=3,
        label="Camaradas de batalla y compañeros de viaje."
    )

    # 4. Conexiones geográficas (Place Links)
    plink1 = PlaceLink(
        place_id_a=p_ciudad.id,
        place_id_b=p_bosque.id,
        connection_type="camino",
        label="Senderos de Oro (3 días a caballo)"
    )
    plink2 = PlaceLink(
        place_id_a=p_bosque.id,
        place_id_b=p_mazmorra.id,
        connection_type="frontera",
        label="La Grieta Negra (Límite prohibido)"
    )

    # 5. Vocabulario personalizado (Conlang)
    v1 = CustomVocabularyEntry(
        word="Aethora",
        presence_type="present",
        notes="Verbo elfo que significa 'entrar bendecido por la luz'."
    )
    v2 = CustomVocabularyEntry(
        word="Vael",
        presence_type="transit",
        notes="Término para referirse al cruce de portales."
    )

    # 6. Cronograma / Story Blocks
    sb1 = StoryBlock(
        title="El Despertar en Solaria",
        synopsis="Valen descubre una profecía inscrita en el cuarzo de la Ciudadela.",
        status="escrito",
        tone="misterioso",
        x=100.0, y=150.0,
        char_ids=[c_valen.id, c_lyra.id],
        place_ids=[p_ciudad.id, p_castillo.id]
    )

    sb2 = StoryBlock(
        title="La Incursión en el Bosque",
        synopsis="Kael y Valen cruzan el Bosque de los Susurros persiguiendo la sombra.",
        status="listo",
        tone="tenso",
        x=350.0, y=200.0,
        char_ids=[c_valen.id, c_kael.id],
        place_ids=[p_bosque.id]
    )

    sb3 = StoryBlock(
        title="Enfrentamiento en el Foso",
        synopsis="Confrontación climática contra Morgath el Sombrío.",
        status="esbozado",
        tone="epico",
        x=600.0, y=180.0,
        char_ids=[c_valen.id, c_morgath.id],
        place_ids=[p_mazmorra.id]
    )

    arc1 = StoryArc(from_block=sb1.id, to_block=sb2.id, label="Búsqueda del Tomo")
    arc2 = StoryArc(from_block=sb2.id, to_block=sb3.id, label="Ruta Final")

    # 7. Obras, Libros y Capítulos
    cap1_html = """
    <h1>Capítulo 1: La Luz sobre Solaria</h1>
    <p>La mañana amaneció luminosa sobre <b>Solaria</b>. <b>Valen Eldarian</b> ajustó la vaina de su espada y caminó hacia los muros de la <b>Ciudadela de Cristal</b>.</p>
    <p>—El tiempo se agota, Valen —dijo la <b>Archimaga Lyra</b> mientras sostenía un antiguo pergamino elfo. Aethora pronunció con voz grave.</p>
    <p>Mientras tanto, en las sombras lejanas del <b>Foso de las Sombras</b>, <b>Morgath el Sombrío</b> observaba en su esfera de cristal.</p>
    """
    
    cap2_html = """
    <h1>Capítulo 2: Susurros entre las Hojas</h1>
    <p>El aire del <b>Bosque de los Susurros</b> era húmedo y frío. <b>Kaelen Riven</b> avanzaba sigilosamente junto a <b>Valen</b>.</p>
    <p>—Algo ronda estos árboles —susurró Kael desenfundando su daga. Una sombra misteriosa pasó a lo lejos.</p>
    """

    cap1 = Chapter(
        title="Capítulo 1: La Luz sobre Solaria",
        content_file="chap_1.html",
        status="listo",
        places_present=[p_ciudad.id, p_castillo.id, p_mazmorra.id],
        characters_present=[c_valen.id, c_lyra.id, c_morgath.id],
        author_notes=[
            AuthorNote(title="Revisión de Tono", content="Asegurar que la calma inicial contraste con la amenaza de Morgath.")
        ]
    )

    cap2 = Chapter(
        title="Capítulo 2: Susurros entre las Hojas",
        content_file="chap_2.html",
        status="esbozado",
        places_present=[p_bosque.id],
        characters_present=[c_valen.id, c_kael.id, c_sombra.id]
    )

    book1 = Book(title="Libro I: Las Gemas del Sol", capitulos=[cap1, cap2])
    
    cap3_html = "<h1>Capítulo 1: El Reino Caído</h1><p>Las crónicas relatan la caída del segundo templo...</p>"
    cap3 = Chapter(title="Capítulo 1: El Reino Caído", content_file="chap_3.html", status="idea")
    book2 = Book(title="Libro II: La Era Dorada", capitulos=[cap3])

    obra1 = Obra(title="La Sombra del Dragón", libros=[book1])
    obra2 = Obra(title="El Despertar de la Magia", libros=[book2])

    # Escribir HTML de capítulos
    with open(os.path.join(temp_dir, "content", cap1.content_file), "w", encoding="utf-8") as f:
        f.write(cap1_html)
    with open(os.path.join(temp_dir, "content", cap2.content_file), "w", encoding="utf-8") as f:
        f.write(cap2_html)
    with open(os.path.join(temp_dir, "content", cap3.content_file), "w", encoding="utf-8") as f:
        f.write(cap3_html)

    # Metadata completa del universo
    metadata = UniverseMetadata(
        title="El Legado de Eldoria",
        author="Autor Principal",
        genre="Fantasía Épica / Alta Magia",
        description="Universo fantástico completo de prueba para validar el sistema integral de Aura Writer.",
        characters=[c_valen, c_morgath, c_lyra, c_kael, c_sombra],
        places=[p_reino, p_ciudad, p_castillo, p_bosque, p_mazmorra],
        relations=[rel1, rel2, rel3],
        place_links=[plink1, plink2],
        custom_vocabulary=[v1, v2],
        story_blocks=[sb1, sb2, sb3],
        story_arcs=[arc1, arc2],
        author_notes=[
            AuthorNote(title="Planificación General", content="Esta obra explora el equilibrio entre la luz y la nigromancia.")
        ],
        obras=[obra1, obra2]
    )

    # Guardar meta.json en el dir temporal
    meta_path = os.path.join(temp_dir, "meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        import json
        json.dump(metadata.to_dict(), f, indent=2, ensure_ascii=False)

    # Cifrar y empaquetar con SecurityManager V2
    if os.path.exists(aura_file_path):
        os.remove(aura_file_path)

    SecurityManager.package_project(password, temp_dir, aura_file_path)
    print(f"Proyecto .aura creado exitosamente en: {aura_file_path}")
    print(f"Contrasena para abrir: {password}")

if __name__ == "__main__":
    build_test_project()
