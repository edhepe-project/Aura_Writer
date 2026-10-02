"""
image_viewer.py — Visor de imágenes con soporte para zoom y paneo.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
)
from PyQt6.QtGui import QPixmap, QWheelEvent
from PyQt6.QtGui import QPainter
from PyQt6.QtCore import Qt

class ImageViewerDialog(QDialog):
    def __init__(self, image_path: str, title: str = "Visor de Imagen", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(900, 700)
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowMinimizeButtonHint
        )
        self.setStyleSheet("QDialog { background-color: #000000; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)
        self.view.setStyleSheet("QGraphicsView { border: none; background: transparent; }")
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        layout.addWidget(self.view)

        pixmap = QPixmap(image_path)
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.pixmap_item)

        # Ajustar vista inicial para que la imagen encaje en la ventana si es muy grande
        self.view.setSceneRect(self.pixmap_item.boundingRect())
        
        # Permitir zoom con la rueda del ratón
        self.view.wheelEvent = self._on_wheel_event

    def showEvent(self, event):
        super().showEvent(event)
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def _on_wheel_event(self, event: QWheelEvent):
        if event.angleDelta().y() > 0:
            factor = 1.15
        else:
            factor = 0.85
        self.view.scale(factor, factor)
