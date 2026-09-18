"""
Script para generar un proyecto .aura de prueba con un árbol genealógico completo y rico.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core.project_manager import ProjectManager
from core.models import Character, CharacterRelation, Chapter, Book, Obra, Place

def create_sample_family_tree_project():
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Cronicas_de_la_Dinastia_Valerius.aura"))
    
    pm = ProjectManager()
    password = "123"  # Contraseña sencilla de prueba
    
    print("Creando universo...")
    pm.create_new_project(
        name="Crónicas de la Dinastía Valerius",
        author="Aura Studio",
        password=password,
        export_path=output_path
    )
    
    # 1. Definir los personajes de 4 generaciones
    # ─────────────────────────────────────────────────────────────
    # Gen 1: Bisabuelos / Fundadores
    aurelius = Character(
        name="Emperador Aurelius Valerius",
        role="Protagonista",
        description="Fundador de la dinastía y arquitecto del Imperio Dorado.",
        age="82 años (Fallecido)",
        birthplace="Ciudad Imperial de Solaria",
        custom_attributes={"Raza": "Humano Solar", "Título": "Emperador Fundador", "Casa": "Valerius"}
    )
    valeria = Character(
        name="Emperatriz Valeria de Lumina",
        role="Secundario",
        description="Erudita y matriarca de la casa Valerius.",
        age="79 años (Fallecida)",
        birthplace="Torres de Lumina",
        custom_attributes={"Raza": "Humano Solar", "Título": "Emperatriz Matriarca", "Casa": "Lumina"}
    )

    # Gen 2: Abuelos y Tíos Abuelos
    tiberius = Character(
        name="Rey Tiberius Valerius II",
        role="Protagonista",
        description="Primogénito de Aurelius, gobernó en tiempos de paz y expansión.",
        age="64 años",
        birthplace="Solaria",
        custom_attributes={"Raza": "Humano Solar", "Título": "Rey Sabio", "Casa": "Valerius"}
    )
    helena = Character(
        name="Reina Helena de Altos Ricos",
        role="Secundario",
        description="Estratega política y cónyuge de Tiberius.",
        age="61 años",
        birthplace="Castillo de Vientoalto",
        custom_attributes={"Raza": "Humano del Norte", "Título": "Reina Consorte", "Casa": "Altos Ricos"}
    )
    lucian = Character(
        name="Gran Duque Lucian Valerius",
        role="Misterioso",
        description="Hermano menor de Tiberius, comandante de la Guardia de la Noche.",
        age="58 años",
        birthplace="Solaria",
        custom_attributes={"Raza": "Humano Solar", "Título": "Gran Duque", "Casa": "Valerius"}
    )

    # Gen 3: Padres, Hermanos y Pareja del Personaje Central
    adrian = Character(
        name="Príncipe Adrian Valerius (Protagonista)",
        role="Protagonista",
        description="Heredero al trono imperial, maestro en táctica y diplomacia.",
        age="34 años",
        birthplace="Solaria",
        driving_desire="Unificar los reinos fracturados sin derramar sangre inocente",
        deepest_fear="Repetir los errores del pasado y perder a su familia",
        core_values="Honor, Justicia, Lealtad",
        custom_attributes={"Raza": "Humano Solar", "Título": "Príncipe Heredero", "Casa": "Valerius"}
    )
    lyanna = Character(
        name="Princesa Lyanna de Silvanor",
        role="Protagonista",
        description="Princesa de los Bosques del Este, diplomática y esposa de Adrian.",
        age="32 años",
        birthplace="Arboleda Sagrada de Silvanor",
        custom_attributes={"Raza": "Elfo Noble", "Título": "Princesa Consorte", "Casa": "Silvanor"}
    )
    cassian = Character(
        name="Comandante Cassian Valerius",
        role="Secundario",
        description="Hermano menor y mano derecha militar de Adrian.",
        age="30 años",
        birthplace="Solaria",
        custom_attributes={"Raza": "Humano Solar", "Título": "Comandante General", "Casa": "Valerius"}
    )
    seraphina = Character(
        name="Lady Seraphina Valerius",
        role="Misterioso",
        description="Hermana de Adrian y suma sacerdotisa del Templo Astral.",
        age="27 años",
        birthplace="Solaria",
        custom_attributes={"Raza": "Humano Solar", "Título": "Oráculo Astral", "Casa": "Valerius"}
    )
    malakor = Character(
        name="Lord Malakor",
        role="Antagonista",
        description="Antiguo rival político y comandante traidor de la frontera occidental.",
        age="45 años",
        birthplace="Fortaleza Sombría",
        custom_attributes={"Raza": "Humano", "Título": "Señor de la Guerra", "Facción": "Sombra"}
    )
    eldrin = Character(
        name="Archimago Eldrin",
        role="Secundario",
        description="Mentor supremo de artes mágicas y consejero de la dinastía.",
        age="120 años",
        birthplace="Torre del Amanecer",
        custom_attributes={"Raza": "Alto Elfo", "Título": "Archimago del Consejo", "Magia": "Luz Solar"}
    )

    # Gen 4: Hijos de Adrian y Lyanna
    rowan = Character(
        name="Príncipe Rowan Valerius",
        role="Protagonista",
        description="Primogénito de Adrian y Lyanna, joven espadachín de talento prodigioso.",
        age="14 años",
        birthplace="Solaria",
        custom_attributes={"Raza": "Semi-Elfo", "Título": "Joven Heredero", "Casa": "Valerius"}
    )
    elena = Character(
        name="Princesa Elena Valerius",
        role="Secundario",
        description="Hija menor de Adrian y Lyanna, prodigio de la magia natural.",
        age="11 años",
        birthplace="Solaria",
        custom_attributes={"Raza": "Semi-Elfo", "Título": "Princesa Menor", "Casa": "Valerius"}
    )

    chars = [
        aurelius, valeria, tiberius, helena, lucian,
        adrian, lyanna, cassian, seraphina, malakor, eldrin,
        rowan, elena
    ]

    pm.metadata.characters = chars

    # 2. Relaciones del Árbol Genealógico y Grafo
    # ─────────────────────────────────────────────────────────────
    # Nota sobre convención:
    # descendiente: char_id_a = HIJO, char_id_b = PADRE/MADRE
    # mentor:       char_id_a = MENTOR, char_id_b = APRENDIZ
    rels = [
        # Matrimonio Gen 1
        CharacterRelation(char_id_a=aurelius.id, char_id_b=valeria.id, relation_type="pareja", label="Esposos Fundadores", intensity=5),
        
        # Hijos de Gen 1 -> Gen 2
        CharacterRelation(char_id_a=tiberius.id, char_id_b=aurelius.id, relation_type="descendiente", label="Hijo Primogénito", intensity=5),
        CharacterRelation(char_id_a=tiberius.id, char_id_b=valeria.id, relation_type="descendiente", label="Hijo Primogénito", intensity=5),
        CharacterRelation(char_id_a=lucian.id, char_id_b=aurelius.id, relation_type="descendiente", label="Segundo Hijo", intensity=4),
        CharacterRelation(char_id_a=lucian.id, char_id_b=valeria.id, relation_type="descendiente", label="Segundo Hijo", intensity=4),
        CharacterRelation(char_id_a=tiberius.id, char_id_b=lucian.id, relation_type="familiar", label="Hermanos", intensity=4),

        # Matrimonio Gen 2
        CharacterRelation(char_id_a=tiberius.id, char_id_b=helena.id, relation_type="pareja", label="Matrimonio Real", intensity=5),

        # Hijos de Gen 2 -> Gen 3 (Adrian, Cassian, Seraphina)
        CharacterRelation(char_id_a=adrian.id, char_id_b=tiberius.id, relation_type="descendiente", label="Hijo Heredero", intensity=5),
        CharacterRelation(char_id_a=adrian.id, char_id_b=helena.id, relation_type="descendiente", label="Hijo Heredero", intensity=5),
        CharacterRelation(char_id_a=cassian.id, char_id_b=tiberius.id, relation_type="descendiente", label="Segundo Hijo", intensity=4),
        CharacterRelation(char_id_a=cassian.id, char_id_b=helena.id, relation_type="descendiente", label="Segundo Hijo", intensity=4),
        CharacterRelation(char_id_a=seraphina.id, char_id_b=tiberius.id, relation_type="descendiente", label="Tercera Hija", intensity=4),
        CharacterRelation(char_id_a=seraphina.id, char_id_b=helena.id, relation_type="descendiente", label="Tercera Hija", intensity=4),

        # Hermanos de Gen 3
        CharacterRelation(char_id_a=adrian.id, char_id_b=cassian.id, relation_type="familiar", label="Hermanos y Compañeros de Armas", intensity=5),
        CharacterRelation(char_id_a=adrian.id, char_id_b=seraphina.id, relation_type="familiar", label="Hermanos", intensity=4),

        # Matrimonio Gen 3 (Adrian + Lyanna)
        CharacterRelation(char_id_a=adrian.id, char_id_b=lyanna.id, relation_type="pareja", label="Alianza Sagrada de Solaria y Silvanor", intensity=5),

        # Hijos de Gen 3 -> Gen 4 (Rowan y Elena)
        CharacterRelation(char_id_a=rowan.id, char_id_b=adrian.id, relation_type="descendiente", label="Primogénito", intensity=5),
        CharacterRelation(char_id_a=rowan.id, char_id_b=lyanna.id, relation_type="descendiente", label="Primogénito", intensity=5),
        CharacterRelation(char_id_a=elena.id, char_id_b=adrian.id, relation_type="descendiente", label="Segunda Hija", intensity=5),
        CharacterRelation(char_id_a=elena.id, char_id_b=lyanna.id, relation_type="descendiente", label="Segunda Hija", intensity=5),
        CharacterRelation(char_id_a=rowan.id, char_id_b=elena.id, relation_type="familiar", label="Hermanos", intensity=4),

        # Relaciones de Mentoría, Rivalidad y Amistad
        CharacterRelation(char_id_a=eldrin.id, char_id_b=adrian.id, relation_type="mentor", label="Tutoría Real y Sabiduría Antigua", intensity=4),
        CharacterRelation(char_id_a=eldrin.id, char_id_b=seraphina.id, relation_type="mentor", label="Enseñanza de Magia Sagrada", intensity=4),
        CharacterRelation(char_id_a=adrian.id, char_id_b=malakor.id, relation_type="rival", label="Enemistad Jurada por la Frontera", intensity=5),
        CharacterRelation(char_id_a=adrian.id, char_id_b=cassian.id, relation_type="amigo", label="Lealtad Incondicional", intensity=5),
    ]

    pm.metadata.relations = rels

    # 3. Lugares del Universo
    solaria = Place(
        name="Solaria (Capital Imperial)",
        description="La ciudad dorada de mil torres, sede del Trono de la Dinastía Valerius.",
        custom_attributes={"Región": "Tierras Centrales", "Clima": "Templado Soleado"}
    )
    silvanor = Place(
        name="Gran Arboleda de Silvanor",
        description="Antiguo bosque élfico protegido por barreras místicas ancestrales.",
        custom_attributes={"Región": "Bosques del Este", "Fuerza Mágica": "Muy Alta"}
    )
    fortaleza = Place(
        name="Fortaleza Sombría de Malakor",
        description="Bastión inexpugnable en las montañas del norte.",
        custom_attributes={"Región": "Cordillera Negra", "Estado": "Bajo control enemigo"}
    )
    pm.metadata.places = [solaria, silvanor, fortaleza]

    # 4. Estructura de Capítulos
    chap1 = Chapter(
        title="Capítulo I: El Legado de los Valerius",
        content_file="chap_1.html",
        word_count=1450
    )
    chap2 = Chapter(
        title="Capítulo II: La Sombra sobre Solaria",
        content_file="chap_2.html",
        word_count=2100
    )
    book1 = Book(title="Libro I: El Amanecer del Heredero", capitulos=[chap1, chap2])
    obra1 = Obra(title="El Trono de Solaria", libros=[book1])
    pm.metadata.obras = [obra1]

    # Contenido de ejemplo
    pm._write_content(
        chap1.content_file,
        "<h1>Capítulo I: El Legado de los Valerius</h1>"
        "<p>El sol brillaba con un resplandor dorado sobre los muros de mármol de Solaria. "
        "El príncipe Adrian contemplaba desde el balcón imperial el horizonte sin fin de su reino.</p>"
        "<p>—Nuestro linaje no se forjó con palabras, sino con la voluntad inquebrantable de cuatro generaciones —le recordó la reina Helena con serenidad.</p>"
    )
    pm._write_content(
        chap2.content_file,
        "<h1>Capítulo II: La Sombra sobre Solaria</h1>"
        "<p>Desde los confines oscuros de la frontera occidental, los mensajeros traían noticias alarmantes sobre los movimientos de Lord Malakor.</p>"
        "<p>Adrian desenvainó la espada de su abuelo Aurelius, sintiendo el calor del sol recorriendo el acero templado.</p>"
    )

    # 5. Guardar proyecto
    pm.is_locked = False
    pm.save_project()
    print(f"Proyecto creado con éxito en: {output_path}")

if __name__ == "__main__":
    create_sample_family_tree_project()
