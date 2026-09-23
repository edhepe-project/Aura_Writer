from core.models import StoryBlock, StoryArc, UniverseMetadata


def test_story_block_creation():
    block = StoryBlock(
        title="El Despertar",
        synopsis="Amanae despierta en Solaria",
        status="esbozado",
        tone="misterioso",
        themes=["Misterio", "Identidad"]
    )
    assert block.title == "El Despertar"
    assert block.status == "esbozado"
    assert len(block.themes) == 2
    assert block.id is not None


def test_story_arc_creation():
    arc = StoryArc(
        from_block="block-1",
        to_block="block-2",
        arc_type="branch",
        label="Consecuencia"
    )
    assert arc.from_block == "block-1"
    assert arc.to_block == "block-2"
    assert arc.arc_type == "branch"


def test_universe_metadata_story_serialization():
    meta = UniverseMetadata(title="Universo de Prueba")
    block1 = StoryBlock(title="Evento 1")
    block2 = StoryBlock(title="Evento 2")
    arc = StoryArc(from_block=block1.id, to_block=block2.id)

    meta.story_blocks.append(block1)
    meta.story_blocks.append(block2)
    meta.story_arcs.append(arc)

    data = meta.to_dict()
    assert len(data["story_blocks"]) == 2
    assert len(data["story_arcs"]) == 1

    restored = UniverseMetadata.from_dict(data)
    assert len(restored.story_blocks) == 2
    assert restored.story_blocks[0].title == "Evento 1"
    assert restored.story_arcs[0].from_block == block1.id
