"""
Diálogo independiente para abrir el Cronograma Narrativo (Grafo de Historia).
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal as Signal

from core.models import UniverseMetadata
from ui.story_graph.widget import StoryGraphWidget


class StoryGraphDialog(QDialog):
    navigate_to_chapter = Signal(str)  # chapter_id

    def __init__(self, metadata: UniverseMetadata, parent=None):
        super().__init__(parent)
        self.metadata = metadata
        self.setWindowTitle("🕸️ Cronograma Narrativo — Grafo Causal de la Historia")
        self.resize(1150, 750)
        self.setMinimumSize(800, 500)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.graph_widget = StoryGraphWidget(self.metadata, self)
        self.graph_widget.navigate_to_chapter.connect(self._on_navigate_to_chapter)
        layout.addWidget(self.graph_widget)

    def _on_navigate_to_chapter(self, chapter_id: str):
        """Cierra el diálogo y emite la señal de navegación al capítulo."""
        self.accept()  # Cierra el diálogo primero
        self.navigate_to_chapter.emit(chapter_id)
