"""
UI tests for PlaceDock and PlaceEditDialog in Aura Writer using pytest-qt.
"""
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from core.models import Place, UniverseMetadata
from ui.place_dock import PlaceDock, PlaceCard
from ui.place_dialog import PlaceEditDialog
from ui.main_window import AuraMainWindow


def test_place_dock_populate_and_filter(qtbot):
    dock = PlaceDock()
    qtbot.addWidget(dock)

    p1 = Place(name="Castillo de Ébano", category="Fortaleza / Castillo", climate_atmosphere="Frío")
    p2 = Place(name="Cueva de Cristal", category="Mazmorra / Cueva", climate_atmosphere="Húmedo")
    p3 = Place(name="Taverna del Dragón", category="Edificio / Interior", climate_atmosphere="Cálido")

    dock.populate([p1, p2, p3])
    assert len(dock._cards) == 3

    # Filtrar por texto
    dock._search_input.setText("Cueva")
    assert len(dock._cards) == 1
    assert p2.id in dock._cards

    # Limpiar filtro
    dock._search_input.clear()
    assert len(dock._cards) == 3

    # Filtrar por categoría
    dock._cat_filter.setCurrentIndex(dock._cat_filter.findText("Fortaleza / Castillo"))
    assert len(dock._cards) == 1
    assert p1.id in dock._cards


def test_place_dock_selection_and_detail(qtbot):
    dock = PlaceDock()
    qtbot.addWidget(dock)

    p1 = Place(
        name="Bosque Antiguo",
        category="Bosque / Naturaleza",
        climate_atmosphere="Brumoso y templado",
        sensory_details="Aroma a musgo húmedo",
        lore_history="Cuna de los elfos primigenios"
    )
    dock.populate([p1])

    # Seleccionar por ID
    dock.select_place_by_id(p1.id)
    assert dock._selected_place_id == p1.id
    assert "BOSQUE ANTIGUO" in dock._detail_title.text()
    assert "Brumoso y templado" in dock._detail_info.text()
    assert "Aroma a musgo húmedo" in dock._detail_info.text()


def test_place_edit_dialog_validation_and_save(qtbot):
    dialog = PlaceEditDialog()
    qtbot.addWidget(dialog)

    # Inicialmente nombre por defecto o vacío -> setear nuevo nombre
    saved_places = []
    dialog.place_saved.connect(saved_places.append)

    dialog.edit_name.setText("Puerto Esmeralda")
    dialog.edit_climate.setPlainText("Brisa marina suave y soleado.")
    dialog.edit_sensory.setPlainText("Olor a salitre, graznidos de gaviotas.")
    dialog.edit_lore.setPlainText("El puerto comercial más próspero del sur.")

    dialog._save_place()

    assert len(saved_places) == 1
    sp = saved_places[0]
    assert sp.name == "Puerto Esmeralda"
    assert sp.climate_atmosphere == "Brisa marina suave y soleado."
    assert sp.sensory_details == "Olor a salitre, graznidos de gaviotas."
    assert sp.lore_history == "El puerto comercial más próspero del sur."


def test_main_window_inspector_tab_switcher(qtbot):
    window = AuraMainWindow()
    qtbot.addWidget(window)

    # Estado inicial: tab de personajes activo
    assert window._dock_stack.currentWidget() == window.char_dock
    assert window._btn_tab_chars.isChecked()
    assert not window._btn_tab_places.isChecked()

    # Cambiar a Lugares
    window._switch_inspector_tab("places")
    assert window._dock_stack.currentWidget() == window.place_dock
    assert not window._btn_tab_chars.isChecked()
    assert window._btn_tab_places.isChecked()

    # Volver a Personajes
    window._switch_inspector_tab("characters")
    assert window._dock_stack.currentWidget() == window.char_dock
    assert window._btn_tab_chars.isChecked()
    assert not window._btn_tab_places.isChecked()
