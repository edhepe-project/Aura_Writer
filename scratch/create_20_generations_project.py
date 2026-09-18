"""
Script para generar un proyecto .aura colosal con 20 GENERACIONES consecutivas de linaje real.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core.project_manager import ProjectManager
from core.models import Character, CharacterRelation, Chapter, Book, Obra, Place

def create_20_generations_project():
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Linaje_Milenario_20_Generaciones.aura"))
    
    pm = ProjectManager()
    password = "123"
    
    print("Creando universo de 20 generaciones...")
    pm.create_new_project(
        name="El Linaje Milenario de los 20 Emperadores",
        author="Aura Studio",
        password=password,
        export_path=output_path
    )
    
    # Nombres de las 20 eras / reyes
    dynasty_names = [
        ("Aethelgard I el Origen", "Reina Mística Ysolda"),
        ("Valerius II el Conquistador", "Reina Lyanna de las Nieves"),
        ("Tiberius III el Constructor", "Reina Rowena de Valdor"),
        ("Caelen IV el Astrónomo", "Reina Morgana del Lago"),
        ("Darius V el Justiciero", "Reina Eleanor del Valle"),
        ("Aurelius VI el Sabio", "Reina Vivienne de Lumina"),
        ("Balthazar VII el Guerrero", "Reina Freya de los Fiordos"),
        ("Cassian VIII el Pacificador", "Reina Sophia de Altagloria"),
        ("Dorian IX el Arcanista", "Reina Isolde de las Sombras"),
        ("Evander X el Ilustrado", "Reina Beatrix de Solaria"),
        ("Fenris XI el Lobo Dorado", "Reina Astrid del Alba"),
        ("Gideon XII el Escudo del Sol", "Reina Maeve de Silvanor"),
        ("Hector XIII el Diplomático", "Reina Cassandra de los Mares"),
        ("Ignatius XIV el Ígneo", "Reina Priscilla de Montecristal"),
        ("Julian XV el Prudente", "Reina Genevieve de la Fuente"),
        ("Kaelen XVI el Renacido", "Reina Diana de las Estrellas"),
        ("Lysander XVII el Valiente", "Reina Valeria de Altos Ricos"),
        ("Morrigan XVIII el Centinela", "Reina Serena de Vientoplata"),
        ("Nathaniel XIX el Visionario", "Reina Aurora del Crepúsculo"),
        ("Adrian XX el Heredero del Milenio (Protagonista)", "Princesa Aurelia de Solaria")
    ]

    characters = []
    relations = []
    
    prev_ruler = None
    prev_consort = None

    for gen_idx, (ruler_name, consort_name) in enumerate(dynasty_names, start=1):
        is_current = (gen_idx == 20)
        
        ruler = Character(
            name=f"Gen {gen_idx}: {ruler_name}",
            role="Protagonista" if (is_current or gen_idx == 1) else "Secundario",
            description=f"Soberano de la Generación {gen_idx} en la línea directa del Trono Milenario.",
            age=f"Era {gen_idx}00",
            birthplace="Capital Imperial de Solaria",
            custom_attributes={
                "Generación": f"Nivel {gen_idx}",
                "Dinastía": "Casa Imperial Milenaria",
                "Raza": "Humano Solar"
            }
        )
        
        consort = Character(
            name=f"Gen {gen_idx}: {consort_name}",
            role="Secundario",
            description=f"Consorte real de la Generación {gen_idx}.",
            age=f"Era {gen_idx}00",
            birthplace="Reinos Aliados",
            custom_attributes={
                "Generación": f"Nivel {gen_idx}",
                "Título": "Reina Consorte"
            }
        )

        characters.append(ruler)
        characters.append(consort)

        # Matrimonio de la generación actual
        relations.append(
            CharacterRelation(
                char_id_a=ruler.id,
                char_id_b=consort.id,
                relation_type="pareja",
                label=f"Matrimonio Real Gen {gen_idx}",
                intensity=5
            )
        )

        # Si hay generación anterior, el soberano actual desciende de la pareja anterior
        if prev_ruler and prev_consort:
            relations.append(
                CharacterRelation(
                    char_id_a=ruler.id,
                    char_id_b=prev_ruler.id,
                    relation_type="descendiente",
                    label="Hijo Heredero",
                    intensity=5
                )
            )
            relations.append(
                CharacterRelation(
                    char_id_a=ruler.id,
                    char_id_b=prev_consort.id,
                    relation_type="descendiente",
                    label="Hijo Heredero",
                    intensity=5
                )
            )

        prev_ruler = ruler
        prev_consort = consort

    # Añadir 2 hijos a la generación 20 para tener además descendencia (Gen 21)
    gen21_a = Character(
        name="Gen 21: Príncipe Solis (Primogénito)",
        role="Protagonista",
        description="Primogénito de Adrian XX y Aurelia, el futuro de la dinastía.",
        age="12 años",
        birthplace="Solaria",
        custom_attributes={"Generación": "Nivel 21", "Título": "Joven Heredero"}
    )
    gen21_b = Character(
        name="Gen 21: Princesa Lunaria",
        role="Secundario",
        description="Segunda hija de Adrian XX y Aurelia.",
        age="9 años",
        birthplace="Solaria",
        custom_attributes={"Generación": "Nivel 21", "Título": "Princesa Menor"}
    )

    characters.append(gen21_a)
    characters.append(gen21_b)

    # Relaciones de los hijos de la Gen 20
    relations.append(CharacterRelation(char_id_a=gen21_a.id, char_id_b=prev_ruler.id, relation_type="descendiente", label="Hijo", intensity=5))
    relations.append(CharacterRelation(char_id_a=gen21_a.id, char_id_b=prev_consort.id, relation_type="descendiente", label="Hijo", intensity=5))
    relations.append(CharacterRelation(char_id_a=gen21_b.id, char_id_b=prev_ruler.id, relation_type="descendiente", label="Hija", intensity=5))
    relations.append(CharacterRelation(char_id_a=gen21_b.id, char_id_b=prev_consort.id, relation_type="descendiente", label="Hija", intensity=5))
    relations.append(CharacterRelation(char_id_a=gen21_a.id, char_id_b=gen21_b.id, relation_type="familiar", label="Hermanos", intensity=4))

    pm.metadata.characters = characters
    pm.metadata.relations = relations

    # Lugares
    solaria = Place(
        name="Templo de los Veinte Tronos",
        description="Mausoleo y basílica sagrada donde descansan las 20 coronas ancestrales.",
        custom_attributes={"Importancia": "Monumento de la Humanidad"}
    )
    pm.metadata.places = [solaria]

    # Capítulo de muestra
    chap1 = Chapter(
        title="Capítulo I: La Memoria de Veinte Eras",
        content_file="chap_1.html",
        word_count=3200
    )
    book1 = Book(title="Tomo Milenario", capitulos=[chap1])
    obra1 = Obra(title="La Gran Dinastía", libros=[book1])
    pm.metadata.obras = [obra1]

    pm._write_content(
        chap1.content_file,
        "<h1>Capítulo I: La Memoria de Veinte Eras</h1>"
        "<p>Veinte generaciones de emperadores contemplaban a Adrian desde los altos vitrales del Templo Sagrado. "
        "Cada piedra, cada tratado de paz y cada estandarte en el reino era el eco vivo de un milenio de linaje ininterrumpido.</p>"
    )

    pm.is_locked = False
    pm.save_project()
    print(f"Proyecto de 20 generaciones creado en: {output_path}")
    print(f"Total de personajes: {len(characters)} | Total relaciones: {len(relations)}")

if __name__ == "__main__":
    create_20_generations_project()
