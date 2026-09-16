from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QListWidget,
                             QPushButton, QHBoxLayout, QInputDialog,
                             QMessageBox, QListWidgetItem)
from PyQt6.QtCore import Qt, pyqtSignal
import qtawesome as qta

from core.models import Character


class CharacterPanel(QWidget):
    """Panel de personajes del universo con botones para añadir/eliminar."""
    character_added = pyqtSignal(object)     # Character
    character_deleted = pyqtSignal(str)       # character_id
    character_selected = pyqtSignal(str)      # character_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._characters: list[Character] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel("PERSONAJES")
        self.label.setStyleSheet("font-weight: bold; color: #e67e22;")
        layout.addWidget(self.label)

        self.char_list = QListWidget()
        self.char_list.currentRowChanged.connect(self._on_selection_changed)
        layout.addWidget(self.char_list)

        btn_layout = QHBoxLayout()
        try:
            self.add_btn = QPushButton(qta.icon("fa5s.user-plus", color="#27ae60"), "")
            self.del_btn = QPushButton(qta.icon("fa5s.user-minus", color="#e74c3c"), "")
        except Exception:
            self.add_btn = QPushButton("+")
            self.del_btn = QPushButton("-")

        self.add_btn.setToolTip("Añadir personaje")
        self.del_btn.setToolTip("Eliminar personaje")
        self.add_btn.clicked.connect(self._add_character)
        self.del_btn.clicked.connect(self._del_character)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.del_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #e67e22;
                color: white;
            }
        """)

    def populate(self, characters: list[Character]):
        self._characters = list(characters)
        self.char_list.clear()
        for char in self._characters:
            item = QListWidgetItem(char.name)
            item.setData(Qt.ItemDataRole.UserRole, char.id)
            self.char_list.addItem(item)

    def _add_character(self):
        name, ok = QInputDialog.getText(
            self, "Nuevo Personaje", "Nombre del personaje:"
        )
        if ok and name.strip():
            char = Character(name=name.strip())
            self._characters.append(char)
            item = QListWidgetItem(char.name)
            item.setData(Qt.ItemDataRole.UserRole, char.id)
            self.char_list.addItem(item)
            self.character_added.emit(char)

    def _del_character(self):
        row = self.char_list.currentRow()
        if row < 0:
            return
        item = self.char_list.item(row)
        char_id = item.data(Qt.ItemDataRole.UserRole)
        name = item.text()

        reply = QMessageBox.question(
            self, "Eliminar Personaje",
            f"¿Eliminar a '{name}' del universo?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.char_list.takeItem(row)
            self._characters = [c for c in self._characters if c.id != char_id]
            self.character_deleted.emit(char_id)

    def _on_selection_changed(self, row):
        if 0 <= row < len(self._characters):
            self.character_selected.emit(self._characters[row].id)
