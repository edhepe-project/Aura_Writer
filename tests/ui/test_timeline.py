"""
Unit tests for the Timeline / Chronology interactive system.
"""
import pytest
from PyQt6.QtCore import Qt
from core.models import Chapter, Obra, Book, Place, Character, UniverseMetadata
from ui.timeline.event_card import TimelineEventCard
from ui.timeline.widget import TimelineCanvas, TimelineWidget
from ui.timeline.dialog import TimelineDialog



def test_timeline_event_card_rendering(qtbot):
    cap = Chapter(
        title="La Batalla del Valle",
        in_world_date="Año 412 Segunda Era",
        in_world_order=5
    )
    card = TimelineEventCard(
        chapter=cap,
        obra_title="Crónicas del Norte",
        obra_color="#ff9f0a",
        characters_names=["Elendil", "Isildur"],
        places_names=["Valle Sombrío"],
    )
    qtbot.addWidget(card)

    assert "La Batalla del Valle" in card._title_label.text()
    assert "Año 412 Segunda Era" in card._date_label.text()
    assert "#5" in card._order_label.text()
    assert "Valle Sombrío" in card._places_label.text()
    assert "Elendil" in card._chars_label.text()

    from PyQt6.QtGui import QMouseEvent
    from PyQt6.QtCore import QPointF
    ev = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPointF(10, 10),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier
    )
    with qtbot.waitSignal(card.clicked, timeout=1000) as blocker:
        card.mousePressEvent(ev)
    assert blocker.args == [cap.id]




def test_timeline_canvas_and_widget(qtbot):
    widget = TimelineWidget()
    qtbot.addWidget(widget)

    cap1 = Chapter(title="Capítulo I", in_world_order=1, in_world_date="Día 1")
    cap2 = Chapter(title="Capítulo II", in_world_order=2, in_world_date="Día 2")

    events = [
        (cap1, "Obra Alpha", "#3498db", ["Protagonista"], ["Ciudad"]),
        (cap2, "Obra Alpha", "#3498db", ["Protagonista", "Rival"], ["Bosque"])
    ]

    widget.set_data(events)
    canvas = widget.get_canvas()
    assert len(canvas._cards) == 2

    with qtbot.waitSignal(widget.chapter_selected, timeout=1000) as blocker:
        canvas._on_card_clicked(cap2.id)
    assert blocker.args == [cap2.id]


def test_timeline_dialog_filters_and_navigation(qtbot, tmp_path):
    from core.project_manager import ProjectManager

    pm = ProjectManager()
    proj_dir = tmp_path / "test_proj"
    proj_dir.mkdir()
    pm.project_dir = proj_dir

    p1 = Place(name="Castillo Oscuro")
    c1 = Character(name="Aragorn")

    cap1 = Chapter(
        title="Comienzo del Viaje",
        in_world_date="Año 3018",
        in_world_order=1,
        places_present=[p1.id],
        characters_present=[c1.id]
    )
    cap2 = Chapter(
        title="Llegada a las Puertas",
        in_world_date="Año 3019",
        in_world_order=2,
        places_present=[],
        characters_present=[]
    )

    libro = Book(title="Libro I", capitulos=[cap1, cap2])
    obra = Obra(title="El Anillo", color="#e74c3c", libros=[libro])

    pm.metadata = UniverseMetadata(
        title="Tierra Media",
        obras=[obra],
        places=[p1],
        characters=[c1]
    )

    dialog = TimelineDialog(project_manager=pm)
    qtbot.addWidget(dialog)

    # Validar que los 2 eventos se cargaron
    canvas = dialog._timeline_widget.get_canvas()
    assert len(canvas._cards) == 2

    # Probar filtro por texto
    dialog._search_input.setText("Puertas")
    assert len(canvas._cards) == 1
    assert canvas._cards[0].chapter.title == "Llegada a las Puertas"

    dialog._search_input.clear()
    assert len(canvas._cards) == 2

    # Probar señal navigate_to_chapter al hacer doble clic
    with qtbot.waitSignal(dialog.navigate_to_chapter, timeout=1000) as blocker:
        dialog._on_chapter_double_clicked(cap1.id)
    assert blocker.args == [cap1.id]
