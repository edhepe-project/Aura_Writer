"""
Unit tests for PlaceGraphWidget and PlaceGraphDialog (Atlas Literario).
"""
from PyQt6.QtWidgets import QMessageBox
from core.models import Place, PlaceLink, UniverseMetadata
from ui.place_graph.widget import PlaceGraphWidget, PlaceNodeItem, PlaceLinkItem
from ui.place_graph.dialog import PlaceGraphDialog


def test_place_graph_widget_population_and_spring_layout(qtbot):
    widget = PlaceGraphWidget()
    qtbot.addWidget(widget)

    p1 = Place(name="Valle Escondido", category="Naturaleza / Bosque")
    p2 = Place(name="Castillo del Sol", category="Reino / Nación")
    link = PlaceLink(place_id_a=p1.id, place_id_b=p2.id, label="Camino Real", connection_type="ruta")

    widget.set_data([p1, p2], [link])

    qtbot.waitUntil(lambda: len(widget._node_map) == 2, timeout=2000)

    assert len(widget._node_map) == 2
    assert len(widget._link_items) == 1
    assert p1.id in widget._node_map
    assert p2.id in widget._node_map

    # Test Spring layout execution
    widget.reorganize_layout()
    qtbot.waitUntil(lambda: widget._stack.currentIndex() == 1, timeout=2000)

    # Búsqueda interactiva
    widget._search_input.setText("Castillo")
    node_castillo = widget._node_map[p2.id]
    node_valle = widget._node_map[p1.id]
    assert node_castillo._is_focused is True
    assert node_valle._is_focused is False


def test_place_graph_dialog_connections_management(qtbot, tmp_path):
    from core.project_manager import ProjectManager

    pm = ProjectManager()
    proj_dir = tmp_path / "test_proj_atlas"
    proj_dir.mkdir()
    pm.project_dir = proj_dir

    p1 = Place(name="Ciudad Puerto")
    p2 = Place(name="Isla Remota")

    pm.metadata = UniverseMetadata(
        title="Mundo Insular",
        places=[p1, p2],
        place_links=[]
    )

    dialog = PlaceGraphDialog(project_manager=pm)
    qtbot.addWidget(dialog)

    # Forzar carga de datos y esperar a que el layout termine de procesar
    dialog._load_data()
    qtbot.waitUntil(lambda: dialog._graph_widget._stack.currentIndex() == 1, timeout=3000)

    # Seleccionar p1
    dialog._on_place_selected(p1.id)
    assert "Ciudad Puerto" in dialog._info_name.text()

    # Crear conexión con p2
    dialog._combo_target_place.setCurrentIndex(dialog._combo_target_place.findText("Isla Remota"))
    dialog._combo_conn_type.setCurrentIndex(dialog._combo_conn_type.findText("Ruta"))
    dialog._input_conn_label.setText("Ruta Marítima")
    dialog._add_connection()

    assert len(pm.metadata.place_links) == 1
    link = pm.metadata.place_links[0]
    assert link.place_id_a == p1.id
    assert link.place_id_b == p2.id
    assert link.label == "Ruta Marítima"

    # Seleccionar la ruta en la lista y eliminarla (simulando clic en QMessageBox.Yes)
    assert dialog._connections_list.count() == 1
    dialog._connections_list.setCurrentRow(0)
    assert dialog._btn_delete_link.isEnabled()

    from unittest.mock import patch
    with patch("PyQt6.QtWidgets.QMessageBox.question", return_value=QMessageBox.StandardButton.Yes):
        dialog._delete_selected_connection()

    assert len(pm.metadata.place_links) == 0

    # Doble clic para enfocar
    with qtbot.waitSignal(dialog.place_selected_for_focus, timeout=1000) as blocker:
        dialog._on_place_double_clicked(p2.id)
    assert blocker.args == [p2.id]


def test_place_graph_hierarchy_orbital_mode(qtbot):
    widget = PlaceGraphWidget()
    qtbot.addWidget(widget)

    # Castillo (padre) -> Salón del Trono (estancia hija) -> Mazmorra (sub-estancia)
    castillo = Place(name="Castillo de la Roca", category="Fortaleza / Castillo")
    salon = Place(name="Salón del Trono", category="Taberna / Interior", parent_place_id=castillo.id)
    mazmorra = Place(name="Mazmorras Bajas", category="Mazmorra / Cueva", parent_place_id=salon.id)

    widget.set_data([castillo, salon, mazmorra], [])

    qtbot.waitUntil(lambda: len(widget._node_map) == 3, timeout=2000)

    assert len(widget._node_map) == 3
    node_castillo = widget._node_map[castillo.id]
    node_salon = widget._node_map[salon.id]
    node_mazmorra = widget._node_map[mazmorra.id]

    assert node_castillo.child_count == 1
    assert node_castillo.depth == 0
    assert node_salon.child_count == 1
    assert node_salon.depth == 1
    assert node_mazmorra.depth == 2

    # Se deben haber generado las aristas orbitales automáticas de contención
    contain_links = [item for item in widget._link_items if item.link.connection_type == "contiene"]
    assert len(contain_links) == 2

