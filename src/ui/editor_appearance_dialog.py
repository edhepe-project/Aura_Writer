# ─────────────────────────────────────────────────────────────────────────────
# Aura Writer — Diálogo de Apariencia del Editor & Accesibilidad
# Permite personalizar el papel, fuente de trabajo, zoom visual e interlineado.
# ─────────────────────────────────────────────────────────────────────────────
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QSlider, QGroupBox, QRadioButton, QButtonGroup, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import qtawesome as qta


class EditorAppearanceDialog(QDialog):
    """Diálogo interactivo para configurar la apariencia y accesibilidad del editor."""
    appearance_changed = pyqtSignal()

    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.editor = editor
        self.setWindowTitle("Apariencia")
        self.setFixedSize(520, 480)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        # ── Encabezado ──────────────────────────────────────────────
        header = QHBoxLayout()
        icon_lbl = QLabel()
        try:
            icon_lbl.setPixmap(qta.icon("fa5s.eye", color="#d4a017").pixmap(32, 32))
        except Exception:
            pass
        header.addWidget(icon_lbl)

        title_lbl = QLabel("<b>Ajustes de Visión y Papel de Trabajo</b><br>"
                           "<small style='color:#8e8e93;'>Estos ajustes son visuales y no alteran el formato real del libro.</small>")
        title_lbl.setStyleSheet("font-size: 12px;")
        header.addWidget(title_lbl)
        header.addStretch()
        layout.addLayout(header)

        # ── Grupo 1: Zoom y Accesibilidad Visual ────────────────────
        grp_zoom = QGroupBox("🔍 Zoom de Lectura / Redacción")
        zoom_layout = QVBoxLayout(grp_zoom)

        slider_row = QHBoxLayout()
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(80, 250)
        self.zoom_slider.setValue(self.editor.get_zoom_percentage())
        self.zoom_slider.setSingleStep(10)
        self.zoom_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.zoom_slider.setTickInterval(25)

        self.zoom_label = QLabel(f"{self.editor.get_zoom_percentage()}%")
        self.zoom_label.setFixedWidth(50)
        self.zoom_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #d4a017;")

        self.zoom_slider.valueChanged.connect(self._on_slider_changed)

        slider_row.addWidget(self.zoom_slider)
        slider_row.addWidget(self.zoom_label)
        zoom_layout.addLayout(slider_row)

        # Botones rápidos de zoom
        quick_row = QHBoxLayout()
        for pct in (100, 125, 150, 175, 200):
            btn = QPushButton(f"{pct}%")
            btn.setStyleSheet("padding: 3px 8px; font-size: 11px;")
            btn.clicked.connect(lambda _, p=pct: self.zoom_slider.setValue(p))
            quick_row.addWidget(btn)
        zoom_layout.addLayout(quick_row)
        layout.addWidget(grp_zoom)

        # ── Grupo 2: Tipografía de Trabajo ──────────────────────────
        grp_font = QGroupBox("✍️ Tipografía de Redacción")
        font_layout = QHBoxLayout(grp_font)

        self.combo_font = QComboBox()
        self.combo_font.addItems([
            "Georgia (Serif Editorial Clásica)",
            "Garamond (Serif Literaria)",
            "Segoe UI (Sans-serif Moderna y Nítida)",
            "Inter (Sans-serif de Alta Legibilidad)",
            "Courier Prime (Máquina de escribir / Guion)",
            "Consolas (Monospace)",
            "Atkinson Hyperlegible (Máxima Accesibilidad Visual)",
            "OpenDyslexic (Diseñada para Dislexia)",
        ])

        # Seleccionar la actual
        cur_font = self.editor.get_work_font_family()
        for i in range(self.combo_font.count()):
            item_text = self.combo_font.itemText(i)
            if cur_font.lower() in item_text.lower():
                self.combo_font.setCurrentIndex(i)
                break

        self.combo_font.currentIndexChanged.connect(self._on_font_changed)
        font_layout.addWidget(self.combo_font)
        layout.addWidget(grp_font)

        # ── Grupo 3: Estilo de Papel / Lienzo ────────────────────────
        grp_paper = QGroupBox("📄 Estilo y Tono de Papel")
        paper_layout = QGridLayout(grp_paper)
        paper_layout.setSpacing(10)

        self.paper_btn_group = QButtonGroup(self)
        self.papers = [
            ("blanco", "📄 Blanco Clásico", "#ffffff", "#1a1a1a"),
            ("sepia", "📜 Sepia / Pergamino", "#f4ecd8", "#2d241e"),
            ("verde", "🌿 Té Verde Lofi", "#e8f0e6", "#1c2e1c"),
            ("noche", "🌙 Noche Carbón", "#1e1e20", "#e0e0e0"),
            ("oled", "🖤 OLED Puro", "#000000", "#e6e6e6"),
            ("auto", "🔄 Según Tema de App", "", ""),
        ]

        cur_paper = self.editor.get_paper_style()

        for idx, (p_id, p_name, _, _) in enumerate(self.papers):
            rb = QRadioButton(p_name)
            rb.setProperty("paper_id", p_id)
            if p_id == cur_paper:
                rb.setChecked(True)
            self.paper_btn_group.addButton(rb, idx)
            row = idx // 2
            col = idx % 2
            paper_layout.addWidget(rb, row, col)

        self.paper_btn_group.buttonClicked.connect(self._on_paper_changed)
        layout.addWidget(grp_paper)

        layout.addStretch()

        # ── Botones de cierre ────────────────────────────────────────
        btn_box = QHBoxLayout()
        btn_reset = QPushButton("Restablecer Valores")
        btn_reset.setStyleSheet("padding: 6px 12px; font-size: 11px;")
        btn_reset.clicked.connect(self._reset_defaults)
        btn_box.addWidget(btn_reset)

        btn_box.addStretch()

        btn_close = QPushButton("Cerrar")
        btn_close.setStyleSheet("background-color: #d4a017; color: white; font-weight: bold; padding: 6px 18px;")
        btn_close.clicked.connect(self.accept)
        btn_box.addWidget(btn_close)

        layout.addLayout(btn_box)

    def _on_slider_changed(self, value):
        self.zoom_label.setText(f"{value}%")
        self.editor.set_zoom_percentage(value)
        self.appearance_changed.emit()

    def _on_font_changed(self, index):
        full_text = self.combo_font.currentText()
        family = full_text.split(" (")[0].strip()
        self.editor.set_work_font_family(family)
        self.appearance_changed.emit()

    def _on_paper_changed(self, button):
        paper_id = button.property("paper_id")
        self.editor.set_paper_style(paper_id)
        self.appearance_changed.emit()

    def _reset_defaults(self):
        self.zoom_slider.setValue(100)
        self.combo_font.setCurrentIndex(0)
        # Seleccionar auto
        for btn in self.paper_btn_group.buttons():
            if btn.property("paper_id") == "auto":
                btn.setChecked(True)
                self.editor.set_paper_style("auto")
                break
        self.editor.set_work_font_family("Georgia")
        self.editor.set_zoom_percentage(100)
        self.appearance_changed.emit()
