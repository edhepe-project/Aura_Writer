import sys
import os
import random

sys.path.insert(0, 'src')

from core.project_manager import ProjectManager
from core.models import UniverseMetadata, Obra, Book, Chapter, Character, CharacterRelation

# Crear el gestor y proyecto
pm = ProjectManager()
output_path = os.path.abspath("Universo_Aura_Demo.aura")
password = "1234"

pm.create_new_project(
    name="Crónicas del Éter Cósmico — 100 Habitantes",
    author="Aura Writer",
    password=password,
    export_path=output_path
)

meta = pm.metadata
obra = meta.obras[0]
libro = obra.libros[0]
libro.capitulos.clear()

# ── DEFINICIÓN GENERADA DE 100 PERSONAJES DIVERSOS ───────────────────────────
FIRST_NAMES = [
    "Ihnara", "Amanae", "Malakor", "Kaelen", "Lyra", "Bram", "Zephyr", "Vespera",
    "Nolan", "Sariel", "Talia", "Corin", "Miraen", "Orion", "Gorok", "Nyx",
    "Torin", "Faelar", "Elowen", "Jax", "Aeloria", "Daelin", "Thalor", "Seraphina",
    "Vaelen", "Morwen", "Draxis", "Elysia", "Caelum", "Sylas", "Kaelitha", "Rathgar",
    "Solara", "Luneth", "Fenris", "Gideon", "Cassian", "Yvaine", "Balthazar", "Kallista",
    "Rowan", "Xander", "Freya", "Aurelius", "Selene", "Theron", "Althea", "Valerius",
    "Morrigan", "Ignis", "Astrid", "Lucian", "Isolde", "Kaelen", "Evander", "Maeve",
    "Cedric", "Ophelia", "Kaeloc", "Rhea", "Alastair", "Eira", "Viggo", "Azura",
    "Boran", "Lyssandra", "Oakhaven", "Tiberius", "Moros", "Cyra", "Hesper", "Zarek",
    "Nyssa", "Garrick", "Syrin", "Vael", "Kharas", "Dorian", "Aveline", "Grimm",
    "Orlaith", "Riven", "Kaelas", "Taron", "Ione", "Corvus", "Elandor", "Vesper",
    "Branoc", "Sylphira", "Zephyrus", "Kaelthorn", "Vulkan", "Aeris", "Erebus", "Thyra",
    "Galen", "Nesta", "Jorah", "Alera"
]

LAST_NAMES = [
    "Valen", "Sylph", "del Vacío", "Drak", "Vael", "Barbaferro", "del Éter", "de las Sombras",
    "Arcano", "la Veloz", "Sombrahoja", "Fierromartillo", "Luzdeestrella", "Ventoforte",
    "Nochedura", "Brumaeterna", "Alapúrpura", "Corazóndorado", "Vientohelado", "Cantofirme",
    "Pedrafuerte", "Hojafiel", "Lumbreviva", "Astroculto", "Grisval", "Fuegoestelar",
    "Raízvieja", "Halconvelo", "Ondamarina", "Silvaclara", "Hierrobruno", "Nievesol",
    "Cruzatormentas", "Cazavientos", "Sangreacero", "Luzplata", "Sombradensa", "Vozarcana"
]

ROLES = ["Protagonista", "Antagonista", "Secundario", "Misterioso", "Otro"]
RACES = ["Humano", "Amanae", "Sombra", "Elfo", "Enano", "Draconiano", "Celeste", "Golem de Éter"]

DESIRES = [
    "Restaurar el equilibrio del cosmos", "Dominio absoluto del Éter", "Proteger a los suyos",
    "Comprender los secretos ancestrales", "Redención por faltas del pasado", "Libertad total",
    "Crear una obra maestra sin igual", "Encontrar a su clan perdido", "Ascender a un plano superior",
    "Desentrañar la magia olvidada", "Defender las fronteras del imperio", "Paz duradera entre reinos",
    "Descubrir la verdad oculta de los dioses", "Dominar la forja estelar", "Reunir las reliquias sagradas"
]

random.seed(42)

char_objs = []
used_names = set()

for i in range(100):
    if i == 0:
        name = "Ihnara Valen"
        role = "Protagonista"
        race = "Humano"
        desc = "Heredera de la Llama Ancestral, faro de esperanza y buscadora de la verdad cósmica."
    elif i == 1:
        name = "Amanae Sylph"
        role = "Protagonista"
        race = "Amanae"
        desc = "Sacerdotisa del Éter Estelar y guardiana suprema de los vientos sagrados."
    elif i == 2:
        name = "Lord Malakor"
        role = "Antagonista"
        race = "Sombra"
        desc = "Señor del Vacío y conquistador implacable de los reinos celestes."
    elif i == 3:
        name = "Kaelen Drak"
        role = "Secundario"
        race = "Humano"
        desc = "Comandante de la Guardia del Norte y estratega militar legendario."
    elif i == 4:
        name = "Lyra Vael"
        role = "Secundario"
        race = "Elfo"
        desc = "Diplomática errante y tejedora de pactos sagrados entre pueblos."
    elif i == 5:
        name = "Bram Barbaferro"
        role = "Secundario"
        race = "Enano"
        desc = "Gran Maestro Forjador de ingenios celestes y armas de mito."
    else:
        fn = FIRST_NAMES[i % len(FIRST_NAMES)]
        ln = LAST_NAMES[(i * 3 + 7) % len(LAST_NAMES)]
        name = f"{fn} {ln}"
        if name in used_names:
            name = f"{fn} {ln} {i}"
        
        # Distribución de roles realista: 3 líderes/protagonistas, 25 secundarios clave, el resto de apoyo
        if i < 28:
            role = random.choice(["Secundario", "Misterioso"])
        else:
            role = random.choice(["Secundario", "Otro", "Misterioso"])
            
        race = random.choice(RACES)
        desc = f"Habitante de los reinos de {race}. Dedicado a sus convicciones y deberes en el cosmos."

    used_names.add(name)
    desire = random.choice(DESIRES)

    c = Character(
        name=name,
        role=role,
        description=desc,
        driving_desire=desire,
        custom_attributes={"Raza / Especie": race}
    )
    char_objs.append(c)

meta.characters.extend(char_objs)
cmap = {c.name: c for c in char_objs}
cids = [c.id for c in char_objs]

# ── CAPÍTULOS CON PRESENCIAS CRONOLÓGICAS ─────────────────────────────────────
for ch_idx in range(1, 21):
    title = f"Capítulo {ch_idx}: Las Crónicas del Éter Astral Parte {ch_idx}"
    
    # Cada capítulo tiene entre 4 y 12 personajes presentes
    # Ihnara, Amanae y Malakor aparecen frecuentemente
    present = []
    if ch_idx in [1, 4, 7, 9, 10, 15, 20]:
        present.append(cids[0]) # Ihnara
    if ch_idx in [2, 4, 6, 9, 10, 14, 20]:
        present.append(cids[1]) # Amanae
    if ch_idx in [3, 8, 10, 17, 20]:
        present.append(cids[2]) # Malakor
    
    # Secundarios recurrentes
    if ch_idx % 2 == 0:
        present.append(cids[3]) # Kaelen
        present.append(cids[4]) # Lyra
    if ch_idx % 3 == 0:
        present.append(cids[5]) # Bram

    # Personajes variados del universo
    sample_size = random.randint(4, 9)
    pool = random.sample(cids[6:], sample_size)
    present.extend(pool)
    present = list(set(present))

    cap = Chapter(
        title=title,
        content_file=f"chap_{ch_idx}.html",
        characters_present=present
    )
    libro.capitulos.append(cap)
    pm._write_content(cap.content_file, f"<h1>{title}</h1><p>En este acontecimiento crucial se reúnen los destinos de {len(present)} personajes...</p>")

# ── RED DE RELACIONES COHESIVA (ÓRBITAS, ALIANZAS Y CLANES) ───────────────────
# Relaciones fijas núcleo
core_rels = [
    (char_objs[0].id, char_objs[1].id, "pareja", "Alianza Sagrada", 5),
    (char_objs[0].id, char_objs[2].id, "rival", "Archienemigos del Vacío", 5),
    (char_objs[1].id, char_objs[2].id, "rival", "Destructores del Éter", 5),
    (char_objs[0].id, char_objs[3].id, "familiar", "Comandante y Protector", 4),
    (char_objs[0].id, char_objs[4].id, "amigo", "Alianza Diplomática", 4),
    (char_objs[1].id, char_objs[4].id, "amigo", "Pacto Élfico-Amanae", 4),
    (char_objs[3].id, char_objs[5].id, "amigo", "Forjador de su Armadura", 3),
    (char_objs[4].id, char_objs[5].id, "amigo", "Tratado Comercial", 3),
]

for a, b, rtype, label, intensity in core_rels:
    meta.relations.append(CharacterRelation(
        char_id_a=a, char_id_b=b, relation_type=rtype, label=label, intensity=intensity
    ))

# Crear relaciones en racimo (clanes por raza y centros gravitatorios)
# Cada personaje secundario/menor tiene al menos 1 o 3 conexiones con líderes o pares
rel_types = ["amigo", "familiar", "descendiente", "mentor", "rival", "otro"]
existing_pairs = {(r.char_id_a, r.char_id_b) for r in meta.relations} | {(r.char_id_b, r.char_id_a) for r in meta.relations}

for idx, ch in enumerate(char_objs[6:], start=6):
    # Conexión con algún núcleo (Ihnara, Amanae, Malakor, Kaelen, Lyra o Bram)
    hub_idx = idx % 6
    hub_id = char_objs[hub_idx].id
    rtype = random.choice(rel_types)
    intensity = random.randint(1, 4)
    labels = {
        "amigo": "Aliado de Batalla", "familiar": "Pariente Lejano",
        "descendiente": "Linaje Continuo", "mentor": "Instructor de Arte",
        "rival": "Contendiente", "otro": "Contacto Comercial"
    }
    
    if (ch.id, hub_id) not in existing_pairs:
        meta.relations.append(CharacterRelation(
            char_id_a=ch.id, char_id_b=hub_id, relation_type=rtype, label=labels.get(rtype, "Vínculo"), intensity=intensity
        ))
        existing_pairs.add((ch.id, hub_id))
        existing_pairs.add((hub_id, ch.id))
    
    # Conexión comunitaria entre personajes de la misma raza o vecinos
    peer_idx = (idx + random.randint(1, 12)) % len(char_objs)
    if peer_idx != idx:
        peer_id = char_objs[peer_idx].id
        if (ch.id, peer_id) not in existing_pairs:
            p_rtype = random.choice(rel_types)
            meta.relations.append(CharacterRelation(
                char_id_a=ch.id, char_id_b=peer_id, relation_type=p_rtype, label=labels.get(p_rtype, "Conexión"), intensity=random.randint(1, 3)
            ))
            existing_pairs.add((ch.id, peer_id))
            existing_pairs.add((peer_id, ch.id))

# Guardar el proyecto cifrado .aura
pm.save_project()
print(f"[OK] Proyecto con {len(char_objs)} personajes y {len(meta.relations)} relaciones generado con exito en:", output_path)
