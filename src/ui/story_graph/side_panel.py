"""
Panel lateral derecho para la edición detallada del StoryBlock seleccionado.
Permite editar título, sinopsis, temas, personajes, tono, estado y notas.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QComboBox, QFrame, QScrollArea, QRadioButton, QButtonGroup
)
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt, pyqtSignal as Signal

from core.models import StoryBlock, Character, Place, Chapter
from ui.story_graph.models import STATUS_CONFIG, TONE_CONFIG


class StorySidePanel(QWidget):
    block_updated = Signal(object)    # StoryBlock actualizado
    block_deleted = Signal(str)       # block_id
    open_chapter_requested = Signal(str) # chapter_id opcional

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(300)
        self._current_block = None
        self._available_characters = []
        self._available_places = []
        self._available_chapters = []  # Lista plana de (label, chapter_id)

        self._setup_ui()
        self.hide()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Dejamos que el tema global (ThemeManager) decida los colores base.
        # Solo definimos un borde separador para el panel.
        from core.theme_manager import ThemeManager
        is_dark = ThemeManager.is_dark()
        border_col = "#3a3a3c" if is_dark else "#d4cfc8"
        bg_col = "#252528" if is_dark else "#faf7f3"
        
        self.setStyleSheet(f"""
            QWidget#StorySidePanel {{
                background-color: {bg_col};
                border-left: 1px solid {border_col};
            }}
            QPushButton#SaveBtn {{
                background-color: {"#30d158" if is_dark else "#16a34a"};
                color: {"#000000" if is_dark else "#ffffff"};
            }}
            QPushButton#DeleteBtn {{
                background-color: {"#ff453a" if is_dark else "#dc2626"};
                color: #ffffff;
            }}
        """)
        self.setObjectName("StorySidePanel")

        # Titulo seccion
        hdr = QLabel("📄 DETALLE DEL BLOQUE")
        hdr.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(hdr)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content_widget = QWidget()
        form = QVBoxLayout(content_widget)
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(12)

        # 1. Título
        form.addWidget(QLabel("TÍTULO DEL EVENTO"))
        self.title_edit = QLineEdit()
        form.addWidget(self.title_edit)

        # 2. Estado (Chips / Radios)
        form.addWidget(QLabel("ESTADO DE DESARROLLO"))
        self.status_combo = QComboBox()
        for k, v in STATUS_CONFIG.items():
            self.status_combo.addItem(f"{v['badge']} {v['label']}", k)
        form.addWidget(self.status_combo)

        # 3. Tono Narrativo
        form.addWidget(QLabel("TONO NARRATIVO"))
        self.tone_combo = QComboBox()
        for k, v in TONE_CONFIG.items():
            self.tone_combo.addItem(f"● {v['label']}", k)
        form.addWidget(self.tone_combo)

        # 3b. Capítulo vinculado (solo visible cuando status == "escrito")
        self.chapter_row_label = QLabel("📖 CAPÍTULO VINCULADO")
        _ch_color = "#ffd60a" if is_dark else "#b45309"
        self.chapter_row_label.setStyleSheet(f"color: {_ch_color}; font-size: 11px; font-weight: bold;")
        self.chapter_combo = QComboBox()
        self.chapter_combo.addItem("— Sin capítulo asignado —", None)
        form.addWidget(self.chapter_row_label)
        form.addWidget(self.chapter_combo)
        self.chapter_row_label.hide()
        self.chapter_combo.hide()

        # 4. Sinopsis
        form.addWidget(QLabel("SINOPSIS / RESUMEN"))
        self.synopsis_edit = QTextEdit()
        self.synopsis_edit.setMaximumHeight(80)
        form.addWidget(self.synopsis_edit)

        # 5. Temas / Tags
        form.addWidget(QLabel("TEMAS / CLAVES (separados por coma)"))
        self.themes_edit = QLineEdit()
        self.themes_edit.setPlaceholderText("Ej: Traicón, Misterio, Huida")
        form.addWidget(self.themes_edit)

        # 6. Notas de trabajo
        form.addWidget(QLabel("NOTAS PRIVADAS DEL ESCRITOR"))
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        form.addWidget(self.notes_edit)

        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        # Conectar el combo de estado al toggle del selector de capítulo
        self.status_combo.currentIndexChanged.connect(self._on_status_changed)

        # Botones de Acción
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Guardar Cambios")
        self.save_btn.setObjectName("SaveBtn")
        self.save_btn.clicked.connect(self._on_save)

        self.del_btn = QPushButton("Eliminar")
        self.del_btn.setObjectName("DeleteBtn")
        self.del_btn.clicked.connect(self._on_delete)

        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.del_btn)
        layout.addLayout(btn_layout)

    def _on_status_changed(self, index: int):
        is_written = self.status_combo.currentData() == "escrito"
        self.chapter_row_label.setVisible(is_written)
        self.chapter_combo.setVisible(is_written)

    def load_block(self, block: StoryBlock, characters: list | None = None, places: list | None = None, chapters: list | None = None):
        """Carga un bloque en el panel. chapters es lista de (label, chapter_id)."""
        self._current_block = block
        self._available_characters = characters or []
        self._available_places = places or []
        self._available_chapters = chapters or []

        self.title_edit.setText(block.title)
        self.synopsis_edit.setPlainText(block.synopsis)
        self.themes_edit.setText(", ".join(block.themes))
        self.notes_edit.setPlainText(block.notes)

        # Seleccionar combo status
        idx_status = self.status_combo.findData(block.status)
        if idx_status >= 0:
            self.status_combo.setCurrentIndex(idx_status)

        # Seleccionar combo tono
        idx_tone = self.tone_combo.findData(block.tone)
        if idx_tone >= 0:
            self.tone_combo.setCurrentIndex(idx_tone)

        # Poblar y seleccionar capítulo vinculado
        self.chapter_combo.blockSignals(True)
        self.chapter_combo.clear()
        self.chapter_combo.addItem("— Sin capítulo asignado —", None)
        for label, chapter_id in self._available_chapters:
            self.chapter_combo.addItem(label, chapter_id)
        
        if block.chapter_id:
            idx_ch = self.chapter_combo.findData(block.chapter_id)
            if idx_ch >= 0:
                self.chapter_combo.setCurrentIndex(idx_ch)
        else:
            self.chapter_combo.setCurrentIndex(0)
        self.chapter_combo.blockSignals(False)

        # Mostrar/ocultar sección de capítulo según el estado actual
        self._on_status_changed(0)

        self.show()

    def _on_save(self):
        if not self._current_block:
            return
        
        self._current_block.title = self.title_edit.text().strip() or "Sin título"
        self._current_block.synopsis = self.synopsis_edit.toPlainText().strip()
        self._current_block.notes = self.notes_edit.toPlainText().strip()
        
        raw_themes = self.themes_edit.text().split(",")
        self._current_block.themes = [t.strip() for t in raw_themes if t.strip()]

        self._current_block.status = self.status_combo.currentData()
        self._current_block.tone = self.tone_combo.currentData()

        # Guardar capítulo vinculado solo si status es 'escrito'
        if self._current_block.status == "escrito":
            self._current_block.chapter_id = self.chapter_combo.currentData()
        else:
            # Si el usuario cambia de estado, desvinculamos el capítulo
            self._current_block.chapter_id = None

        self.block_updated.emit(self._current_block)

    def _on_delete(self):
        if self._current_block:
            self.block_deleted.emit(self._current_block.id)
            self.hide()
