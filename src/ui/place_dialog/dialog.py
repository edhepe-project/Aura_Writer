"""
dialog.py — Diálogo completo de creación y edición de Lugares y Escenarios (PlaceEditDialog).
"""

from __future__ import annotations
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QComboBox, QTabWidget, QFileDialog,
    QFrame, QMessageBox, QWidget, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
import qtawesome as qta

from core.models import Place, PLACE_CATEGORIES, PLACE_ICONS
from core.theme_manager import ThemeManager


class PlaceEditDialog(QDialog):
    """Ventana emergente estética para crear o editar un Lugar/Escenario del universo."""
    place_saved = pyqtSignal(object)  # Place

    def __init__(self, place: Place | None = None, all_places: list[Place] = None, project_manager=None, parent=None):
        super().__init__(parent)
        self.pm = project_manager
        self._is_new = place is None
        self._place = place.model_copy() if place else Place()
        self._all_places = [p for p in (all_places or []) if p.id != self._place.id]

        self.setWindowTitle("Nuevo Lugar" if self._is_new else f"Editar Escenario — {self._place.name}")
        self.resize(740, 680)
        self.setMinimumSize(600, 520)

        self._setup_ui()
        if not self._is_new:
            self._load_from_place()

    def _setup_ui(self):
        is_dark = ThemeManager.is_dark()
        bg_main = "#1c1c1e" if is_dark else "#f5f0ea"
        fg_title = "#f2f2f7" if is_dark else "#1a1a2e"
        b_border = "#3a3a3c" if is_dark else "#d4cfc8"
        bg_tab = "rgba(0,0,0,0.15)" if is_dark else "rgba(255,255,255,0.5)"
        accent = "#ffd60a" if is_dark else "#d97706"

        self.setStyleSheet(f"""
            QDialog {{ background-color: {bg_main}; }}
            QTabWidget::pane {{
                border: 1px solid {b_border};
                border-radius: 8px;
                background: {bg_tab};
            }}
            QTabBar::tab {{
                background: transparent;
                color: {'#8e8e93' if is_dark else '#7a7a8a'};
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 700;
                border-bottom: 2px solid transparent;
            }}
            QTabBar::tab:selected {{
                color: {accent};
                border-bottom: 2px solid {accent};
            }}
            QLineEdit, QTextEdit, QComboBox {{
                background-color: {'#2c2c2e' if is_dark else '#ffffff'};
                color: {fg_title};
                border: 1px solid {b_border};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
                border-color: {accent};
            }}
            QLabel {{ color: {fg_title}; font-size: 12px; font-weight: 600; }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 16)
        root.setSpacing(12)

        # Header
        top_bar = QHBoxLayout()
        header_lbl = QLabel(f"{'NUEVO ESCENARIO' if self._is_new else 'FICHA DE LUGAR'}")
        header_lbl.setStyleSheet(f"font-size: 14px; font-weight: 800; color: {fg_title};")
        top_bar.addWidget(header_lbl)
        top_bar.addStretch()
        root.addLayout(top_bar)

        # Tabs
        self.tabs = QTabWidget()

        # ── PESTAÑA 1: Identidad & Geografía ──────────────────────────
        tab_geo = QWidget()
        l_geo = QVBoxLayout(tab_geo)
        l_geo.setContentsMargins(14, 14, 14, 14)
        l_geo.setSpacing(10)

        # Nombre + Categoría
        r1 = QHBoxLayout()
        c1 = QVBoxLayout()
        c1.addWidget(QLabel("Nombre del Lugar:"))
        self.edit_name = QLineEdit()
        self.edit_name.setPlaceholderText("ej. Ciudadela del Sol, Bosque de los Susurros...")
        c1.addWidget(self.edit_name)
        r1.addLayout(c1, 3)

        c2 = QVBoxLayout()
        c2.addWidget(QLabel("Categoría:"))
        self.combo_cat = QComboBox()
        self.combo_cat.addItems(PLACE_CATEGORIES)
        c2.addWidget(self.combo_cat)
        r1.addLayout(c2, 2)
        l_geo.addLayout(r1)

        # Lugar superior / Contenedor
        l_geo.addWidget(QLabel("Ubicado dentro de (Lugar Superior / Reino):"))
        self.combo_parent = QComboBox()
        self.combo_parent.addItem("— Sin lugar superior (Independiente / Raíz) —", "")
        for p in self._all_places:
            icon = PLACE_ICONS.get(p.category, "●")
            self.combo_parent.addItem(f"{icon} {p.name}", p.id)
        l_geo.addWidget(self.combo_parent)

        # Descripción general
        l_geo.addWidget(QLabel("Descripción General del Paisaje / Estructura:"))
        self.edit_desc = QTextEdit()
        self.edit_desc.setPlaceholderText("Descripción visual, arquitectura, dimensiones, accesos...")
        l_geo.addWidget(self.edit_desc, 1)

        # Imagen / Mapa adjunto
        img_box = QHBoxLayout()
        self.lbl_img_status = QLabel("Sin mapa o imagen adjunta")
        self.lbl_img_status.setStyleSheet(f"color: {'#8e8e93' if is_dark else '#7a7a8a'}; font-size: 11px;")
        img_box.addWidget(self.lbl_img_status, 1)

        self.btn_attach_img = QPushButton("Adjuntar Imagen / Mapa")
        self.btn_attach_img.clicked.connect(self._attach_image)
        img_box.addWidget(self.btn_attach_img)

        self.btn_remove_img = QPushButton("✕ Quitar")
        self.btn_remove_img.clicked.connect(self._remove_image)
        self.btn_remove_img.hide()
        img_box.addWidget(self.btn_remove_img)

        l_geo.addLayout(img_box)
        self.tabs.addTab(tab_geo, "Geografía & Plano")

        # ── PESTAÑA 2: Atmósfera & Inmersión Sensorial ────────────────
        tab_sens = QWidget()
        l_sens = QVBoxLayout(tab_sens)
        l_sens.setContentsMargins(14, 14, 14, 14)
        l_sens.setSpacing(10)

        l_sens.addWidget(QLabel("Clima, Iluminación y Temperatura:"))
        self.edit_climate = QTextEdit()
        self.edit_climate.setPlaceholderText("ej. Niebla densa, iluminación crepuscular, frío punzante de alta montaña...")
        l_sens.addWidget(self.edit_climate, 1)

        l_sens.addWidget(QLabel("Detalles Sensoriales (Olores, Sonidos y Texturas):"))
        self.edit_sensory = QTextEdit()
        self.edit_sensory.setPlaceholderText("ej. Olor a madera húmeda y azufre; eco continuo de gotas de agua al fondo...")
        l_sens.addWidget(self.edit_sensory, 1)

        self.tabs.addTab(tab_sens, "Atmósfera Sensorial")

        # ── PESTAÑA 3: Lore, Historia & Notas ────────────────────────
        tab_lore = QWidget()
        l_lore = QVBoxLayout(tab_lore)
        l_lore.setContentsMargins(14, 14, 14, 14)
        l_lore.setSpacing(10)

        l_lore.addWidget(QLabel("Historia, Mitos, Facciones y Reglas del Lugar:"))
        self.edit_lore = QTextEdit()
        self.edit_lore.setPlaceholderText("ej. Fundada en la Era Antigua por los Reyes del Norte. Prohibido el uso de magia de fuego...")
        l_lore.addWidget(self.edit_lore, 1)

        l_lore.addWidget(QLabel("Notas Privadas del Autor (No se exportan):"))
        self.edit_notes = QTextEdit()
        self.edit_notes.setPlaceholderText("Secretos no revelados a los personajes, ideas futuras para giros de trama...")
        l_lore.addWidget(self.edit_notes, 1)

        self.tabs.addTab(tab_lore, "Lore & Notas")

        root.addWidget(self.tabs, 1)

        # Botones inferiores
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_save = QPushButton(" Guardar Lugar")
        btn_save.setIcon(qta.icon("fa5s.save", color="#ffffff"))
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #34c759;
                color: #ffffff;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover { background-color: #30d158; }
        """)
        btn_save.clicked.connect(self._save_place)
        btn_row.addWidget(btn_save)

        root.addLayout(btn_row)

    def _load_from_place(self):
        self.edit_name.setText(self._place.name)
        idx = self.combo_cat.findText(self._place.category)
        if idx >= 0:
            self.combo_cat.setCurrentIndex(idx)

        # Parent place
        for i in range(self.combo_parent.count()):
            if self.combo_parent.itemData(i) == self._place.parent_place_id:
                self.combo_parent.setCurrentIndex(i)
                break

        self.edit_desc.setPlainText(self._place.description)
        self.edit_climate.setPlainText(self._place.climate_atmosphere)
        self.edit_sensory.setPlainText(self._place.sensory_details)
        self.edit_lore.setPlainText(self._place.lore_history)
        self.edit_notes.setPlainText(self._place.notes)

        if self._place.image_asset:
            self.lbl_img_status.setText(f"Imagen adjunta: {self._place.image_asset}")
            self.btn_remove_img.show()

    def _attach_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Mapa o Ilustración", "",
            "Imágenes (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if path and self.pm:
            try:
                with open(path, "rb") as f:
                    data = f.read()
                ext = os.path.splitext(path)[1]
                asset_name = self.pm.save_media_asset(data, ext)
                self._place.image_asset = asset_name
                self.lbl_img_status.setText(f"Imagen adjunta: {asset_name}")
                self.btn_remove_img.show()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo guardar la imagen: {e}")

    def _remove_image(self):
        self._place.image_asset = ""
        self.lbl_img_status.setText("Sin mapa o imagen adjunta")
        self.btn_remove_img.hide()

    def _save_place(self):
        name = self.edit_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Campo requerido", "Por favor ingresa un nombre para el lugar.")
            self.edit_name.setFocus()
            return

        self._place.name = name
        self._place.category = self.combo_cat.currentText()
        self._place.parent_place_id = self.combo_parent.currentData() or ""
        self._place.description = self.edit_desc.toPlainText()
        self._place.climate_atmosphere = self.edit_climate.toPlainText()
        self._place.sensory_details = self.edit_sensory.toPlainText()
        self._place.lore_history = self.edit_lore.toPlainText()
        self._place.notes = self.edit_notes.toPlainText()

        self.place_saved.emit(self._place)
        self.accept()

    def get_place(self) -> Place:
        return self._place
