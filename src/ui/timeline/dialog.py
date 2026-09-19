"""
dialog.py — Diálogo modal principal de la Cronología Literaria (Timeline).
Permite visualizar, filtrar por obra/búsqueda, ordenar eventos y exportar a imagen PNG.
"""
from __future__ import annotations
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QFileDialog, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
import qtawesome as qta

from core.models import UniverseMetadata, Chapter, Obra
from core.theme_manager import ThemeManager
from .widget import TimelineWidget


class TimelineDialog(QDialog):
    """
    Ventana interactiva de Cronología / Timeline Literario.
    Ordena eventos según fecha diegética (in_world_date) y orden interno (in_world_order).
    """
    navigate_to_chapter = pyqtSignal(str)  # chapter_id

    def __init__(self, project_manager, parent=None):
        super().__init__(parent)
        self.pm = project_manager
        self.setWindowTitle("⏳ Cronología & Línea de Tiempo del Universo")
        self.resize(1120, 620)
        self.setMinimumSize(850, 480)

        self._all_events_raw = []
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        is_dark = ThemeManager.is_dark()
        bg_main = "#1c1c1e" if is_dark else "#f4f1eb"
        bg_header = "#2c2c2e" if is_dark else "#ffffff"
        fg_title = "#f2f2f7" if is_dark else "#1c1c1e"
        b_border = "#3a3a3c" if is_dark else "#d4cfc8"

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_main};
            }}
            QFrame#header {{
                background-color: {bg_header};
                border-bottom: 1px solid {b_border};
            }}
            QLineEdit, QComboBox {{
                background-color: {'#3a3a3c' if is_dark else '#fbf9f5'};
                color: {fg_title};
                border: 1px solid {b_border};
                border-radius: 6px;
                padding: 5px 10px;
                font-size: 12px;
            }}
            QPushButton {{
                background-color: {'#3a3a3c' if is_dark else '#e8e4dc'};
                color: {fg_title};
                border: 1px solid {b_border};
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {'#48484a' if is_dark else '#ded8ce'};
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header Toolbar
        header = QFrame()
        header.setObjectName("header")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(16, 12, 16, 12)
        hl.setSpacing(12)

        title_label = QLabel("⏳ CRONOLOGÍA NARRATIVA")
        f = QFont()
        f.setBold(True)
        f.setPointSize(12)
        title_label.setFont(f)
        hl.addWidget(title_label)

        hl.addSpacing(15)

        # Filtro de Obra
        hl.addWidget(QLabel("Obra:"))
        self._obra_combo = QComboBox()
        self._obra_combo.setMinimumWidth(160)
        self._obra_combo.currentIndexChanged.connect(self._apply_filters)
        hl.addWidget(self._obra_combo)

        # Barra de búsqueda rápida
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Buscar por capítulo, evento, lugar o personaje...")
        self._search_input.setClearButtonEnabled(True)
        self._search_input.setMinimumWidth(220)
        self._search_input.textChanged.connect(self._apply_filters)
        hl.addWidget(self._search_input)

        # Ordenar por:
        hl.addWidget(QLabel("Orden:"))
        self._order_combo = QComboBox()
        self._order_combo.addItem("Orden Diegético (in_world_order)", "order")
        self._order_combo.addItem("Fecha Diegética (in_world_date)", "date")
        self._order_combo.addItem("Aparición en el libro", "book")
        self._order_combo.currentIndexChanged.connect(self._apply_filters)
        hl.addWidget(self._order_combo)

        hl.addStretch()

        # Botón Exportar PNG
        self._btn_export = QPushButton("📸 Exportar PNG")
        self._btn_export.setIcon(qta.icon("fa5s.camera", color=fg_title))
        self._btn_export.clicked.connect(self._export_png)
        hl.addWidget(self._btn_export)

        root.addWidget(header)

        # Lienzo Timeline interactivo
        self._timeline_widget = TimelineWidget(self)
        self._timeline_widget.chapter_double_clicked.connect(self._on_chapter_double_clicked)
        root.addWidget(self._timeline_widget)

        # Footer informativo
        footer = QFrame()
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(16, 8, 16, 8)
        self._status_label = QLabel("Doble clic en una tarjeta para abrir el capítulo en el editor.")
        self._status_label.setStyleSheet("color: #8e8e93; font-size: 11px;")
        fl.addWidget(self._status_label)
        fl.addStretch()

        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.accept)
        fl.addWidget(btn_close)
        root.addWidget(footer)

    def _load_data(self):
        if not self.pm or not self.pm.metadata:
            return

        meta: UniverseMetadata = self.pm.metadata
        char_map = {c.id: c.name for c in getattr(meta, "characters", [])}
        place_map = {p.id: p.name for p in getattr(meta, "places", [])}

        self._obra_combo.clear()
        self._obra_combo.addItem("Todas las obras", "")

        raw_events = []
        # Mapa de presencias detectadas por capítulo
        detected_presences = getattr(meta, "presences", [])
        presences_by_cap = {}
        for pres in detected_presences:
            presences_by_cap.setdefault(pres.chapter_id, []).append(pres)

        for obra_idx, obra in enumerate(meta.obras):
            self._obra_combo.addItem(obra.title, obra.id)
            color = obra.color or "#0a84ff"
            book_order_idx = 0
            for libro in obra.libros:
                for cap in libro.capitulos:
                    book_order_idx += 1
                    
                    # Combinar asignados manualmente + detectados por NLP
                    char_ids = list(cap.characters_present)
                    place_ids = list(cap.places_present)
                    
                    if cap.id in presences_by_cap:
                        for p in presences_by_cap[cap.id]:
                            if p.character_id and p.character_id not in char_ids:
                                char_ids.append(p.character_id)
                            if p.place_id and p.place_id not in place_ids:
                                place_ids.append(p.place_id)

                    c_names = [char_map.get(cid, cid) for cid in char_ids if cid in char_map]
                    p_names = [place_map.get(pid, pid) for pid in place_ids if pid in place_map]

                    raw_events.append({
                        "chapter": cap,
                        "obra_id": obra.id,
                        "obra_title": obra.title,
                        "obra_color": color,
                        "book_index": book_order_idx,
                        "char_names": c_names,
                        "place_names": p_names
                    })

        self._all_events_raw = raw_events
        self._apply_filters()

    def _apply_filters(self):
        query = self._search_input.text().lower().strip()
        selected_obra = self._obra_combo.currentData()
        sort_mode = self._order_combo.currentData()

        filtered = []
        for ev in self._all_events_raw:
            cap: Chapter = ev["chapter"]
            if selected_obra and ev["obra_id"] != selected_obra:
                continue

            if query:
                in_title = query in cap.title.lower()
                in_date = query in cap.in_world_date.lower()
                in_chars = any(query in c.lower() for c in ev["char_names"])
                in_places = any(query in p.lower() for p in ev["place_names"])
                if not (in_title or in_date or in_chars or in_places):
                    continue

            filtered.append(ev)

        # Ordenar según criterio
        if sort_mode == "order":
            filtered.sort(key=lambda x: (x["chapter"].in_world_order, x["book_index"]))
        elif sort_mode == "date":
            filtered.sort(key=lambda x: (x["chapter"].in_world_date, x["chapter"].in_world_order))
        else:  # book
            filtered.sort(key=lambda x: x["book_index"])

        timeline_tuples = [
            (
                e["chapter"],
                e["obra_title"],
                e["obra_color"],
                e["char_names"],
                e["place_names"]
            )
            for e in filtered
        ]
        self._timeline_widget.set_data(timeline_tuples)
        self._status_label.setText(
            f"Mostrando {len(filtered)} de {len(self._all_events_raw)} evento(s). "
            f"Doble clic en una tarjeta para saltar al capítulo."
        )

    def _on_chapter_double_clicked(self, chapter_id: str):
        self.navigate_to_chapter.emit(chapter_id)
        self.accept()

    def _export_png(self):
        canvas = self._timeline_widget.get_canvas()
        if not canvas:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Cronología como Imagen",
            "cronologia.png",
            "Imágenes PNG (*.png)"
        )
        if not file_path:
            return

        pixmap = canvas.grab()
        if pixmap.save(file_path, "PNG"):
            QMessageBox.information(self, "Exportación Exitosa", f"Cronología guardada con éxito en:\n{file_path}")
        else:
            QMessageBox.warning(self, "Error", "No se pudo guardar la imagen de la cronología.")
