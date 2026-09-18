"""
dock.py — Componente contenedor PlaceDock para la gestión integral de Lugares y Escenarios.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QScrollArea, QFrame, QMessageBox, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import qtawesome as qta

from core.models import Place, PLACE_CATEGORIES
from core.theme_manager import ThemeManager
from ui.place_dialog import PlaceEditDialog
from .card import PlaceCard


class PlaceDock(QWidget):
    """
    Panel de Lugares y Escenarios:
      - Arriba: Barra de búsqueda, filtro por categoría y botón de añadir lugar.
      - Centro: Lista scrolleable de tarjetas de lugares con jerarquía y acciones.
      - Abajo: Resumen de contexto y detalles sensoriales del lugar seleccionado.
    """
    place_added = pyqtSignal(object)    # Place
    place_updated = pyqtSignal(object)  # Place
    place_deleted = pyqtSignal(str)     # place_id
    place_selected = pyqtSignal(str)    # place_id

    def __init__(self, project_manager=None, parent=None):
        super().__init__(parent)
        self.pm = project_manager
        self._places: list[Place] = []
        self._selected_place_id: str | None = None
        self._cards: dict[str, PlaceCard] = {}
        self._chapters_data: list[tuple] = []  # [(chapter, obra_title, libro_title), ...]

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header con título y botón Nuevo
        header = QFrame()
        hl = QHBoxLayout(header)
        hl.setContentsMargins(8, 8, 8, 4)
        hl.setSpacing(6)

        title_lbl = QLabel("LUGARES & ESCENARIOS")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(9)
        title_lbl.setFont(title_font)
        hl.addWidget(title_lbl)
        hl.addStretch()

        self._btn_add = QPushButton()
        self._btn_add.setIcon(qta.icon("fa5s.plus-circle", color="#ffd60a" if ThemeManager.is_dark() else "#d97706"))
        self._btn_add.setText(" Nuevo")
        self._btn_add.setToolTip("Crear un nuevo lugar o escenario")
        self._btn_add.clicked.connect(self._on_add_place)
        hl.addWidget(self._btn_add)
        root.addWidget(header)

        # Barra de Filtro / Búsqueda
        filter_bar = QFrame()
        fbl = QHBoxLayout(filter_bar)
        fbl.setContentsMargins(8, 2, 8, 6)
        fbl.setSpacing(6)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("🔍 Buscar escenario...")
        self._search_input.setClearButtonEnabled(True)
        self._search_input.textChanged.connect(self._filter_places)
        fbl.addWidget(self._search_input, 2)

        self._cat_filter = QComboBox()
        self._cat_filter.addItem("Todas las categorías", "")
        for cat in PLACE_CATEGORIES:
            self._cat_filter.addItem(cat, cat)
        self._cat_filter.currentIndexChanged.connect(self._filter_places)
        fbl.addWidget(self._cat_filter, 1)

        root.addWidget(filter_bar)

        # Contador de resultados
        self._count_label = QLabel("")
        self._count_label.setContentsMargins(8, 0, 8, 2)
        self._count_label.setStyleSheet("font-size: 10px; color: #8e8e93;")
        root.addWidget(self._count_label)

        # Splitter con lista de tarjetas arriba y detalle de contexto abajo
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setHandleWidth(1)

        # Área de Scroll para Tarjetas
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self._cards_container = QWidget()
        self._cards_layout = QVBoxLayout(self._cards_container)
        self._cards_layout.setContentsMargins(8, 4, 8, 8)
        self._cards_layout.setSpacing(6)
        self._cards_layout.addStretch()

        self._scroll_area.setWidget(self._cards_container)
        splitter.addWidget(self._scroll_area)

        # Panel de Detalle Inferior
        self._detail_frame = QFrame()
        dl = QVBoxLayout(self._detail_frame)
        dl.setContentsMargins(8, 6, 8, 8)
        dl.setSpacing(4)

        self._detail_title = QLabel("DETALLES DEL ESCENARIO")
        dt_font = QFont()
        dt_font.setBold(True)
        dt_font.setPointSize(8)
        self._detail_title.setFont(dt_font)
        dl.addWidget(self._detail_title)

        self._detail_info = QLabel("Selecciona un lugar para inspeccionar su atmósfera, clima y lore.")
        self._detail_info.setWordWrap(True)
        dl.addWidget(self._detail_info)
        dl.addStretch()

        splitter.addWidget(self._detail_frame)
        splitter.setSizes([380, 180])
        root.addWidget(splitter)

        self.update_theme()

    def set_project_manager(self, project_manager):
        self.pm = project_manager

    def populate(self, places: list[Place]):
        self._places = list(places)
        self._selected_place_id = None
        self._rebuild_cards()

    def update_chapters_data(self, chapters_data: list[tuple]):
        """Actualiza los datos de capítulos para mostrar apariciones por lugar.
        chapters_data: [(chapter, obra_title, libro_title), ...]
        """
        self._chapters_data = list(chapters_data)
        self._update_detail_panel()

    def _rebuild_cards(self):
        # Limpiar tarjetas existentes
        for card in self._cards.values():
            card.deleteLater()
        self._cards.clear()

        # Limpiar layout
        while self._cards_layout.count() > 0:
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Mapa de id -> nombre para resolver jerarquías
        place_names = {p.id: p.name for p in self._places}

        query = self._search_input.text().lower().strip()
        cat_filter = self._cat_filter.currentData()

        # Ordenar alfabéticamente o por categoría
        filtered = [
            p for p in self._places
            if (not query or query in p.name.lower() or query in p.climate_atmosphere.lower() or query in p.lore_history.lower())
            and (not cat_filter or p.category == cat_filter)
        ]

        if not filtered:
            empty_lbl = QLabel("No se encontraron escenarios.")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_lbl.setStyleSheet("color: #8e8e93; font-style: italic; margin-top: 20px;")
            self._cards_layout.addWidget(empty_lbl)
            self._count_label.setText("")
        else:
            total = len(self._places)
            shown = len(filtered)
            if shown < total:
                self._count_label.setText(f"{shown} de {total} lugares")
            else:
                self._count_label.setText(f"{total} lugar{'es' if total != 1 else ''}")
            for place in filtered:
                # Calcular nivel de jerarquía para sangría
                depth = 0
                parent_id = place.parent_place_id
                visited = set()
                while parent_id and parent_id not in visited:
                    visited.add(parent_id)
                    parent = next((p for p in self._places if p.id == parent_id), None)
                    if parent:
                        depth += 1
                        parent_id = parent.parent_place_id
                    else:
                        break

                parent_name = place_names.get(place.parent_place_id, "")
                card = PlaceCard(place, parent_name=parent_name, depth=depth, parent=self._cards_container)
                card.clicked.connect(self._on_card_clicked)
                card.edit_requested.connect(self._on_card_edit_requested)
                card.delete_requested.connect(self._on_card_delete_requested)
                if place.id == self._selected_place_id:
                    card.set_selected(True)
                self._cards[place.id] = card
                self._cards_layout.addWidget(card)

        self._cards_layout.addStretch()
        self._update_detail_panel()

    def _filter_places(self):
        self._rebuild_cards()

    def _on_card_clicked(self, place_id: str):
        self._selected_place_id = place_id
        for pid, card in self._cards.items():
            card.set_selected(pid == place_id)
        self._update_detail_panel()
        self.place_selected.emit(place_id)

    def _on_card_edit_requested(self, place_id: str):
        place = next((p for p in self._places if p.id == place_id), None)
        if not place:
            return
        dialog = PlaceEditDialog(place=place, all_places=self._places, project_manager=self.pm, parent=self)
        dialog.place_saved.connect(self._on_place_dialog_saved)
        dialog.exec()

    def _on_card_delete_requested(self, place_id: str):
        place = next((p for p in self._places if p.id == place_id), None)
        if not place:
            return

        res = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Estás seguro de que deseas eliminar el escenario '{place.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if res == QMessageBox.StandardButton.Yes:
            self._places = [p for p in self._places if p.id != place_id]
            if self._selected_place_id == place_id:
                self._selected_place_id = None
            self._rebuild_cards()
            self.place_deleted.emit(place_id)

    def _on_add_place(self):
        dialog = PlaceEditDialog(place=None, all_places=self._places, project_manager=self.pm, parent=self)
        dialog.place_saved.connect(self._on_place_dialog_saved)
        dialog.exec()

    def _on_place_dialog_saved(self, saved_place: Place):
        idx = next((i for i, p in enumerate(self._places) if p.id == saved_place.id), None)
        if idx is not None:
            self._places[idx] = saved_place
            self.place_updated.emit(saved_place)
        else:
            self._places.append(saved_place)
            self.place_added.emit(saved_place)

        self._selected_place_id = saved_place.id
        self._rebuild_cards()

    def select_place_by_id(self, place_id: str):
        self._selected_place_id = place_id
        for pid, card in self._cards.items():
            card.set_selected(pid == place_id)
        self._update_detail_panel()
        self.place_selected.emit(place_id)

    def _update_detail_panel(self):
        place = next((p for p in self._places if p.id == self._selected_place_id), None)
        if not place:
            self._detail_title.setText("DETALLES DEL ESCENARIO")
            self._detail_info.setText("Selecciona un lugar para inspeccionar su atmósfera, clima y lore.")
            return

        self._detail_title.setText(f"📍 {place.name.upper()} ({place.category})")
        info_lines = []
        if place.climate_atmosphere:
            info_lines.append(f"<b>Clima/Atmósfera:</b> {place.climate_atmosphere}")
        if place.sensory_details:
            info_lines.append(f"<b>Detalles Sensoriales:</b> {place.sensory_details}")
        if place.lore_history:
            info_lines.append(f"<b>Lore & Historia:</b> {place.lore_history[:120]}{'...' if len(place.lore_history) > 120 else ''}")
        if place.image_asset:
            info_lines.append("<i>🗺️ Contiene mapa/ilustración adjunta</i>")

        # Apariciones en capítulos
        chapters_here = [
            (cap, obra_t, libro_t)
            for (cap, obra_t, libro_t) in self._chapters_data
            if place.id in cap.places_present
        ]
        if chapters_here:
            info_lines.append(f"<b>📖 Aparece en {len(chapters_here)} capítulo(s):</b>")
            for cap, obra_t, libro_t in chapters_here[:5]:
                info_lines.append(f"&nbsp;&nbsp;• {cap.title} <span style='color:#8e8e93'>({obra_t})</span>")
            if len(chapters_here) > 5:
                info_lines.append(f"&nbsp;&nbsp;<i>… y {len(chapters_here) - 5} más</i>")
        else:
            info_lines.append("<i style='color:#8e8e93'>Sin apariciones registradas en capítulos todavía.</i>")

        if len(info_lines) == 1 and "Sin apariciones" in info_lines[0]:
            info_lines.insert(0, "<i>Sin notas adicionales de atmósfera o lore.</i>")

        self._detail_info.setText("<br>".join(info_lines))

    def update_theme(self):
        is_dark = ThemeManager.is_dark()
        bg = "#1c1c1e" if is_dark else "#f5f0ea"
        fg = "#f2f2f7" if is_dark else "#1c1c1e"
        sub_fg = "#8e8e93" if is_dark else "#6e6e73"
        border = "#3a3a3c" if is_dark else "#d4cfc8"
        input_bg = "#2c2c2e" if is_dark else "#ffffff"

        self.setStyleSheet(f"""
            PlaceDock {{
                background-color: {bg};
            }}
            QLineEdit, QComboBox {{
                background-color: {input_bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 11px;
            }}
            QPushButton {{
                background-color: {'#3a3a3c' if is_dark else '#e5e0d8'};
                color: {fg};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {'#48484a' if is_dark else '#d8d3cb'};
            }}
        """)
        self._detail_title.setStyleSheet(f"color: {sub_fg};")
        self._detail_info.setStyleSheet(f"color: {fg}; font-size: 11px;")
        for card in self._cards.values():
            card._apply_style()
