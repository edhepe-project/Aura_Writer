"""
Script para generar un proyecto .aura con 3 GRANDES LINAJES / CASAS NOBLES
que convergen y se mezclan a lo largo de varias generaciones.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core.project_manager import ProjectManager
from core.models import Character, CharacterRelation, Chapter, Book, Obra, Place

def create_three_lineages_project():
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Convergencia_de_los_Tres_Linajes.aura"))
    
    pm = ProjectManager()
    password = "123"
    
    print("Creando universo de 3 linajes convergentes...")
    pm.create_new_project(
        name="La Convergencia de los Tres Linajes",
        author="Aura Studio",
        password=password,
        export_path=output_path
    )
    
    characters = []
    relations = []

    # ═════════════════════════════════════════════════════════════════════
    # 🏰 CASA 1: DINASTÍA SOLAR (CASA VALERIUS - Fuego y Luz)
    # ═════════════════════════════════════════════════════════════════════
    # Gen 1 (Bisabuelos)
    sol_g1_m = Character(name="Rey Aurelius I (Solar)", role="Secundario", description="Fundador del Reino Solar.", custom_attributes={"Casa": "Valerius (Solar)", "Raza": "Humano Solar", "Elemento": "Fuego / Luz"})
    sol_g1_f = Character(name="Reina Solaria de Fuego", role="Secundario", description="Matriarca del Templo Solar.", custom_attributes={"Casa": "Valerius (Solar)", "Raza": "Humano Solar"})
    # Gen 2 (Abuelos)
    sol_g2_m = Character(name="Príncipe Tiberius Solar", role="Secundario", description="Guerrero solar.", custom_attributes={"Casa": "Valerius (Solar)", "Raza": "Humano Solar"})
    sol_g2_f = Character(name="Lady Helena de la Llama", role="Secundario", description="Noble de las Tierras Altas.", custom_attributes={"Casa": "Valerius (Solar)", "Raza": "Humano Solar"})
    # Gen 3 (Padre del Protagonista)
    sol_g3_m = Character(name="Lord Adrian Valerius (Padre Solar)", role="Secundario", description="Señor de Solaria, portador de la Llama Imperial.", custom_attributes={"Casa": "Valerius (Solar)", "Raza": "Humano Solar"})

    # ═════════════════════════════════════════════════════════════════════
    # 🌲 CASA 2: LINAJE ÉLFICO SILVANO (CASA SILVANOR - Naturaleza)
    # ═════════════════════════════════════════════════════════════════════
    # Gen 1 (Bisabuelos)
    elf_g1_m = Character(name="Archidruida Elrond de las Arboledas", role="Secundario", description="Señor ancestral de los Bosques del Este.", custom_attributes={"Casa": "Silvanor (Élfica)", "Raza": "Alto Elfo", "Elemento": "Vida / Tierra"})
    elf_g1_f = Character(name="Lady Ysolde del Bosque Profundo", role="Secundario", description="Vidente del Árbol Sagrado.", custom_attributes={"Casa": "Silvanor (Élfica)", "Raza": "Alto Elfo"})
    # Gen 2 (Abuela del Protagonista por parte materna)
    elf_g2_f = Character(name="Princesa Elfa Lyanna Silvanor", role="Secundario", description="Princesa diplomática de los Elfos.", custom_attributes={"Casa": "Silvanor (Élfica)", "Raza": "Alto Elfo"})

    # ═════════════════════════════════════════════════════════════════════
    # 🌊 CASA 3: SEÑORES DEL MAR Y LAS MAREAS (CASA VORTEX - Agua y Mareas)
    # ═════════════════════════════════════════════════════════════════════
    # Gen 1 (Bisabuelos)
    sea_g1_m = Character(name="Gran Almirante Nereus", role="Secundario", description="Conquistador de las Islas Tormentosas.", custom_attributes={"Casa": "Vortex (Mar)", "Raza": "Tritón / Humano Marino", "Elemento": "Agua / Tormenta"})
    sea_g1_f = Character(name="Sirena Thalassa de Coral", role="Secundario", description="Cantora de las Mareas.", custom_attributes={"Casa": "Vortex (Mar)", "Raza": "Tritón / Humano Marino"})
    # Gen 2 (Abuelo del Protagonista por parte materna)
    sea_g2_m = Character(name="Capitán Coralis Vortex", role="Secundario", description="Señor de los Mares del Sur.", custom_attributes={"Casa": "Vortex (Mar)", "Raza": "Tritón / Humano Marino"})

    # ═════════════════════════════════════════════════════════════════════
    # 🌪️ PRIMERA FUSIÓN (Gen 2 -> Gen 3): CASA 2 + CASA 3 (Elfos + Mar)
    # ═════════════════════════════════════════════════════════════════════
    # De Coralis (Casa Mar) + Lyanna (Casa Elfa) nace la Madre del Protagonista:
    hybrid_mother = Character(
        name="Dama Marina Silvanor-Vortex (Madre)",
        role="Protagonista",
        description="Heredera híbrida: combina la magia arbórea de los Elfos con el dominio de las mareas.",
        custom_attributes={
            "Casa": "Alianza Silvanor-Vortex",
            "Raza": "Semi-Elfa Marina",
            "Linajes": "50% Élfico + 50% Marino"
        }
    )

    # ═════════════════════════════════════════════════════════════════════
    # 👑 GRAN FUSIÓN FINAL (Gen 3 -> Gen 4): CASA 1 + (CASA 2 + CASA 3)
    # ═════════════════════════════════════════════════════════════════════
    # Del Padre Solar (Adrian) + Madre Híbrida (Marina) nacen los Protagonistas Trilinaje:
    protagonist = Character(
        name="Kaelen el Portador de la Trinidad (Protagonista)",
        role="Protagonista",
        description="El primer ser en unificar los Tres Linajes Sagrados: Fuego Solar, Naturaleza Élfica y Tormenta Marina.",
        age="22 años",
        birthplace="Templo de la Convergencia",
        driving_desire="Restaurar el equilibrio entre los Reinos de Fuego, Bosque y Mar",
        core_values="Unidad, Equilibrio Elemental, Sabiduría",
        custom_attributes={
            "Casa": "Dinastía Trilateral",
            "Raza": "Elegido Trilinaje",
            "Composición de Sangre": "50% Solar + 25% Élfico + 25% Marino",
            "Poderes": "Luz Solar, Magia Arbórea, Dominio de Mareas"
        }
    )

    sister = Character(
        name="Princesa Lunaris (Hermana Trilinaje)",
        role="Protagonista",
        description="Segunda hija de la unión trilateral, oráculo de la armonía.",
        age="18 años",
        custom_attributes={
            "Casa": "Dinastía Trilateral",
            "Raza": "Elegida Trilinaje",
            "Composición de Sangre": "50% Solar + 25% Élfico + 25% Marino"
        }
    )

    characters.extend([
        # Linaje Solar
        sol_g1_m, sol_g1_f, sol_g2_m, sol_g2_f, sol_g3_m,
        # Linaje Elfo
        elf_g1_m, elf_g1_f, elf_g2_f,
        # Linaje Mar
        sea_g1_m, sea_g1_f, sea_g2_m,
        # Fusión 1
        hybrid_mother,
        # Fusión Final
        protagonist, sister
    ])

    # ═════════════════════════════════════════════════════════════════════
    # RELACIONES GENEALÓGICAS
    # ═════════════════════════════════════════════════════════════════════
    # 1. Rama Solar
    relations.append(CharacterRelation(char_id_a=sol_g1_m.id, char_id_b=sol_g1_f.id, relation_type="pareja", label="Fundadores Solares", intensity=5))
    relations.append(CharacterRelation(char_id_a=sol_g2_m.id, char_id_b=sol_g1_m.id, relation_type="descendiente", label="Hijo Solar", intensity=5))
    relations.append(CharacterRelation(char_id_a=sol_g2_m.id, char_id_b=sol_g1_f.id, relation_type="descendiente", label="Hijo Solar", intensity=5))
    relations.append(CharacterRelation(char_id_a=sol_g2_m.id, char_id_b=sol_g2_f.id, relation_type="pareja", label="Matrimonio Solar", intensity=5))
    relations.append(CharacterRelation(char_id_a=sol_g3_m.id, char_id_b=sol_g2_m.id, relation_type="descendiente", label="Hijo", intensity=5))
    relations.append(CharacterRelation(char_id_a=sol_g3_m.id, char_id_b=sol_g2_f.id, relation_type="descendiente", label="Hijo", intensity=5))

    # 2. Rama Élfica
    relations.append(CharacterRelation(char_id_a=elf_g1_m.id, char_id_b=elf_g1_f.id, relation_type="pareja", label="Señores Druidas", intensity=5))
    relations.append(CharacterRelation(char_id_a=elf_g2_f.id, char_id_b=elf_g1_m.id, relation_type="descendiente", label="Hija Élfica", intensity=5))
    relations.append(CharacterRelation(char_id_a=elf_g2_f.id, char_id_b=elf_g1_f.id, relation_type="descendiente", label="Hija Élfica", intensity=5))

    # 3. Rama Marina
    relations.append(CharacterRelation(char_id_a=sea_g1_m.id, char_id_b=sea_g1_f.id, relation_type="pareja", label="Reyes de los Océanos", intensity=5))
    relations.append(CharacterRelation(char_id_a=sea_g2_m.id, char_id_b=sea_g1_m.id, relation_type="descendiente", label="Hijo de las Mareas", intensity=5))
    relations.append(CharacterRelation(char_id_a=sea_g2_m.id, char_id_b=sea_g1_f.id, relation_type="descendiente", label="Hijo de las Mareas", intensity=5))

    # 4. Fusión Élfico-Marina (Coralis + Lyanna -> Marina)
    relations.append(CharacterRelation(char_id_a=sea_g2_m.id, char_id_b=elf_g2_f.id, relation_type="pareja", label="Pacto del Bosque y el Mar", intensity=5))
    relations.append(CharacterRelation(char_id_a=hybrid_mother.id, char_id_b=sea_g2_m.id, relation_type="descendiente", label="Hija Elfa-Marina", intensity=5))
    relations.append(CharacterRelation(char_id_a=hybrid_mother.id, char_id_b=elf_g2_f.id, relation_type="descendiente", label="Hija Elfa-Marina", intensity=5))

    # 5. Gran Fusión Final (Adrian + Marina -> Kaelen y Lunaris)
    relations.append(CharacterRelation(char_id_a=sol_g3_m.id, char_id_b=hybrid_mother.id, relation_type="pareja", label="Alianza Suprema de los Tres Reinos", intensity=5))
    relations.append(CharacterRelation(char_id_a=protagonist.id, char_id_b=sol_g3_m.id, relation_type="descendiente", label="Primogénito Trilateral", intensity=5))
    relations.append(CharacterRelation(char_id_a=protagonist.id, char_id_b=hybrid_mother.id, relation_type="descendiente", label="Primogénito Trilateral", intensity=5))
    relations.append(CharacterRelation(char_id_a=sister.id, char_id_b=sol_g3_m.id, relation_type="descendiente", label="Segunda Hija Trilateral", intensity=5))
    relations.append(CharacterRelation(char_id_a=sister.id, char_id_b=hybrid_mother.id, relation_type="descendiente", label="Segunda Hija Trilateral", intensity=5))
    relations.append(CharacterRelation(char_id_a=protagonist.id, char_id_b=sister.id, relation_type="familiar", label="Hermanos de la Trinidad", intensity=4))

    pm.metadata.characters = characters
    pm.metadata.relations = relations

    # Lugares
    pm.metadata.places = [
        Place(name="Santuario de los Tres Ríos", description="Donde convergen el fuego de la tierra, la arboleda sagrada y el mar abierto."),
        Place(name="Solaria Imperial", description="Templo del Sol."),
        Place(name="Bosques de Silvanor", description="Reino de los Elfos."),
        Place(name="Islas Vortex", description="Dominio de las Mareas.")
    ]

    # Capítulo
    chap = Chapter(
        title="Capítulo I: La Sangre de la Trinidad",
        content_file="chap_1.html",
        word_count=2800
    )
    pm.metadata.obras = [Obra(title="La Leyenda de la Trinidad", libros=[Book(title="Tomo de la Alianza", capitulos=[chap])])]
    pm._write_content(
        chap.content_file,
        "<h1>Capítulo I: La Sangre de la Trinidad</h1>"
        "<p>Kaelen cerró los ojos y sintió las tres herencias ardiendo en su interior: "
        "el calor dorado del sol de su padre Adrian, el murmullo de los robles antiguos de su abuela Lyanna, "
        "y la fuerza incontenible de las olas de su abuelo Coralis.</p>"
    )

    pm.is_locked = False
    pm.save_project()
    print(f"Proyecto de 3 linajes convergentes creado en: {output_path}")

if __name__ == "__main__":
    create_three_lineages_project()
