"""
dialog.py — Diálogo del Buscador Global Premium para Aura Writer.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
    QLabel, QComboBox, QFrame, QWidget, QScrollArea, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

from core.theme_manager import ThemeManager
from ui.search.engine import SearchEngine
from ui.search.card import SearchResultCard


class SearchDialog(QDialog):
    """Buscador Global Premium — Aura Writer."""
    result_selected = pyqtSignal(str, str)   # (item_id, item_type)

    def __init__(self, project_manager, parent=None):
        super().__init__(parent)
        self.pm = project_manager
        self.engine = SearchEngine(project_manager)

        self.setWindowTitle("Buscador Global — Aura Writer")
        self.resize(720, 560)
        self.setMinimumSize(560, 420)

        self._setup_ui()
        QTimer.singleShot(0, self.search_input.setFocus)

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 12)
        root.setSpacing(10)

        # Encabezado
        header = QLabel("Buscar en el universo")
        header.setStyleSheet("font-size:11px; font-weight:600; letter-spacing:0.5px;")
        root.addWidget(header)

        # Barra de búsqueda + filtro
        bar = QHBoxLayout()
        bar.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar en capítulos, personajes y notas…")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._on_query_changed)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Todo", "Capítulos", "Personajes", "Notas"])
        self.filter_combo.setFixedWidth(130)
        self.filter_combo.currentIndexChanged.connect(self.perform_search)

        self.regex_check = QCheckBox("Regex")
        self.regex_check.setToolTip("Habilitar expresiones regulares en la búsqueda")
        self.regex_check.stateChanged.connect(self.perform_search)

        bar.addWidget(self.search_input, 1)
        bar.addWidget(self.filter_combo)
        bar.addWidget(self.regex_check)
        root.addLayout(bar)

        # Área de resultados — scroll con tarjetas
        self._results_area = QScrollArea()
        self._results_area.setWidgetResizable(True)
        self._results_area.setFrameShape(QFrame.Shape.NoFrame)

        _bg = "#1c1c1e" if ThemeManager.is_dark() else "#f5f0ea"
        _area_style = f"background:{_bg}; border:none;"
        self._results_area.setStyleSheet(_area_style)
        self._results_area.viewport().setStyleSheet(_area_style)

        self._cards_container = QWidget()
        self._cards_container.setStyleSheet(f"background:{_bg};")
        self._cards_layout = QVBoxLayout(self._cards_container)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        self._cards_layout.setSpacing(1)
        self._cards_layout.addStretch()

        self._results_area.setWidget(self._cards_container)
        root.addWidget(self._results_area, 1)

        # Pie de página
        self.status_lbl = QLabel("Escribe al menos 3 caracteres…")
        self.status_lbl.setStyleSheet("font-size:11px; padding:2px 2px;")
        root.addWidget(self.status_lbl)

    def _on_query_changed(self):
        if not hasattr(self, "_search_timer"):
            self._search_timer = QTimer(self)
            self._search_timer.setSingleShot(True)
            self._search_timer.timeout.connect(self.perform_search)
        self._search_timer.start(200)

    def perform_search(self):
        query = self.search_input.text().strip()
        self._clear_cards()

        if len(query) < 3:
            self.status_lbl.setText("Escribe al menos 3 caracteres…")
            return

        scope = self.filter_combo.currentText()
        is_regex = self.regex_check.isChecked()

        try:
            results = self.engine.search(query, scope=scope, is_regex=is_regex)
        except Exception as e:
            self.status_lbl.setText(f"Error en búsqueda: {e}")
            return

        count = len(results)
        if count == 0:
            empty_col = "#8e8e93" if ThemeManager.is_dark() else "#78716c"
            empty = QLabel(f"Sin resultados para «{query}»")
            empty.setStyleSheet(f"color:{empty_col}; font-size:13px; padding:24px; background:transparent;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._cards_layout.insertWidget(0, empty)
            self.status_lbl.setText("")
        else:
            for r in results:
                self._add_card(
                    r["icon"], r["title"], r["location"], r["snippet"],
                    query, r["item_id"], r["item_type"], is_regex=is_regex
                )
            plural = "s" if count != 1 else ""
            self.status_lbl.setText(f"{count} resultado{plural} encontrado{plural}")

    def _clear_cards(self):
        while self._cards_layout.count() > 1:
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _add_card(self, icon: str, title: str, location: str, snippet: str,
                  query: str, item_id: str, item_type: str, is_regex: bool = False):
        card = SearchResultCard(icon, title, location, snippet, query,
                                item_id, item_type, is_regex=is_regex)
        card.activated.connect(self._on_card_activated)
        idx = self._cards_layout.count() - 1
        self._cards_layout.insertWidget(idx, card)

    def _on_card_activated(self, item_id: str, item_type: str):
        self.result_selected.emit(item_id, item_type)
        self.accept()
