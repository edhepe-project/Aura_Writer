"""
spell_panel.py — Panel lateral de errores ortográficos de Aura Writer.

Muestra una lista de palabras con error, permite navegar a cada una,
corregirla, ignorarla o añadirla al diccionario personal del proyecto.
"""
from __future__ import annotations

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QSizePolicy, QFrame, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
import qtawesome as qta

from core.spell_checker import AuraSpellChecker, SpellError
from core.theme_manager import ThemeManager

log = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = [
    ("es", "Español"),
    ("en", "English"),
    ("fr", "Français"),
    ("pt", "Português"),
]


class SpellPanel(QWidget):
    """
    Panel lateral del corrector ortográfico.

    Señales:
        navigate_to_error(start, end)  — pide al editor que posicione el cursor
        replace_word(start, end, new_word) — pide al editor que reemplace la palabra
        word_added_to_dict(word) — una palabra fue añadida al diccionario personal
        word_ignored(word) — una palabra fue ignorada en esta sesión
    """

    navigate_to_error  = pyqtSignal(int, int)
    replace_word       = pyqtSignal(int, int, str)
    word_added_to_dict = pyqtSignal(str)
    word_ignored       = pyqtSignal(str)
    recheck_requested  = pyqtSignal()

    def __init__(self, checker: AuraSpellChecker, parent=None):
        super().__init__(parent)
        self._checker = checker
        self._errors: list[SpellError] = []
        self._setup_ui()
        self._apply_theme()

    # ------------------------------------------------------------------
    # Construcción de la UI
    # ------------------------------------------------------------------

    def _setup_ui(self):
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.setMinimumWidth(220)
        self.setMaximumWidth(320)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # ── Encabezado ────────────────────────────────────────────────
        header = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon("fa5s.spell-check", color="#ff453a").pixmap(18, 18))
        self._title_lbl = QLabel("Corrector Ortográfico")
        self._title_lbl.setFont(QFont("", 11, QFont.Weight.Bold))
        header.addWidget(icon_lbl)
        header.addWidget(self._title_lbl)
        header.addStretch()

        # Toggle on/off
        self._btn_toggle = QPushButton()
        self._btn_toggle.setCheckable(True)
        self._btn_toggle.setChecked(True)
        self._btn_toggle.setFixedSize(28, 28)
        self._btn_toggle.setToolTip("Activar / Desactivar corrector")
        self._btn_toggle.clicked.connect(self._on_toggle)
        header.addWidget(self._btn_toggle)
        root.addLayout(header)

        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(sep)

        # ── Selector de idioma ────────────────────────────────────────
        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel("Idioma:"))
        self._combo_lang = QComboBox()
        for code, name in SUPPORTED_LANGUAGES:
            self._combo_lang.addItem(name, code)
        # Seleccionar español por defecto
        idx = self._combo_lang.findData(self._checker.language)
        if idx >= 0:
            self._combo_lang.setCurrentIndex(idx)
        self._combo_lang.currentIndexChanged.connect(self._on_language_changed)
        lang_row.addWidget(self._combo_lang, 1)
        root.addLayout(lang_row)

        # ── Contador de errores ───────────────────────────────────────
        self._count_lbl = QLabel("Sin errores encontrados")
        self._count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_sm = QFont()
        font_sm.setPointSize(9)
        self._count_lbl.setFont(font_sm)
        root.addWidget(self._count_lbl)

        # ── Lista de errores ──────────────────────────────────────────
        self._list = QListWidget()
        self._list.setAlternatingRowColors(True)
        self._list.setSpacing(2)
        self._list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._list.itemSelectionChanged.connect(self._update_buttons)
        root.addWidget(self._list, 1)

        # ── Botones de acción ─────────────────────────────────────────
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(4)

        self._btn_goto = QPushButton(
            qta.icon("fa5s.search", color="#32ade6"), "  Ir al error")
        self._btn_goto.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._btn_goto.clicked.connect(self._on_goto)
        btn_layout.addWidget(self._btn_goto)

        self._btn_ignore = QPushButton(
            qta.icon("fa5s.eye-slash", color="#8e8e93"), "  Ignorar esta vez")
        self._btn_ignore.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._btn_ignore.clicked.connect(self._on_ignore)
        btn_layout.addWidget(self._btn_ignore)

        self._btn_add = QPushButton(
            qta.icon("fa5s.plus-circle", color="#30d158"), "  Añadir al diccionario")
        self._btn_add.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._btn_add.clicked.connect(self._on_add_to_dict)
        btn_layout.addWidget(self._btn_add)

        root.addLayout(btn_layout)

        # ── Pie ───────────────────────────────────────────────────────
        self._footer_lbl = QLabel("Doble clic para ir al error")
        self._footer_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_xs = QFont()
        font_xs.setPointSize(8)
        self._footer_lbl.setFont(font_xs)
        root.addWidget(self._footer_lbl)

        self._update_buttons()

    def _apply_theme(self):
        is_dark = ThemeManager.is_dark()
        bg = "#1c1c1e" if is_dark else "#f5f5f7"
        fg = "#f2f2f7" if is_dark else "#1c1c1e"
        border = "#3a3a3c" if is_dark else "#d1d1d6"
        item_alt = "#2c2c2e" if is_dark else "#ebebeb"
        btn_bg = "#2c2c2e" if is_dark else "#e5e5ea"
        btn_hover = "#3a3a3c" if is_dark else "#d1d1d6"

        toggle_icon = "fa5s.toggle-on" if self._btn_toggle.isChecked() else "fa5s.toggle-off"
        toggle_color = "#30d158" if self._btn_toggle.isChecked() else "#8e8e93"
        self._btn_toggle.setIcon(qta.icon(toggle_icon, color=toggle_color))

        self.setStyleSheet(f"""
            SpellPanel {{
                background-color: {bg};
                color: {fg};
                border-left: 1px solid {border};
            }}
            QLabel {{
                color: {fg};
            }}
            QListWidget {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 6px;
                alternate-background-color: {item_alt};
            }}
            QListWidget::item:selected {{
                background-color: #0a84ff;
                color: #ffffff;
                border-radius: 4px;
            }}
            QListWidget::item:hover {{
                background-color: {'#3a3a3c' if is_dark else '#e0e0e8'};
            }}
            QListWidget::item:selected:hover {{
                background-color: #0a84ff;
            }}
            QPushButton {{
                background-color: {btn_bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 5px 10px;
                text-align: left;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {btn_hover};
            }}
            QPushButton:disabled {{
                color: {'#48484a' if is_dark else '#aeaeb2'};
            }}
            QComboBox {{
                background-color: {btn_bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 5px;
                padding: 3px 6px;
                font-size: 11px;
            }}
            QFrame[frameShape="4"] {{
                color: {border};
            }}
        """)

    # ------------------------------------------------------------------
    # API pública — llamada desde el controlador del editor
    # ------------------------------------------------------------------

    def update_errors(self, errors: list[SpellError]):
        """Actualiza la lista de errores mostrada en el panel.

        Solo reconstruye la lista si los errores cambiaron realmente,
        evitando el parpadeo causado por clear()+reinsert en cada revisión.
        """
        # ── Dirty check: comparar huella antes de reconstruir ─────────────
        new_fp = frozenset((e.start, e.end, e.word) for e in errors)
        old_fp = frozenset((e.start, e.end, e.word) for e in self._errors)
        if new_fp == old_fp:
            return  # Sin cambios reales: no reconstruir ni parpadear

        self._errors = errors
        selected_err = self._selected_error()
        prev_key = (selected_err.start, selected_err.end, selected_err.word) if selected_err else None

        self._list.clear()

        if not errors:
            self._count_lbl.setText("✅ Sin errores encontrados")
            self._update_buttons()
            return

        n = len(errors)
        self._count_lbl.setText(f"⚠ {n} error{'es' if n != 1 else ''} encontrado{'s' if n != 1 else ''}")

        item_to_select = None
        for err in errors:
            # Mostrar: "palabra → sugerencia1, sugerencia2…"
            sugs = ", ".join(err.suggestions[:3]) if err.suggestions else "—"
            item = QListWidgetItem(f"  {err.word}  →  {sugs}")
            item.setData(Qt.ItemDataRole.UserRole, err)
            item.setForeground(QColor("#ff453a"))
            self._list.addItem(item)
            if prev_key and (err.start, err.end, err.word) == prev_key:
                item_to_select = item

        if item_to_select:
            # Preservar posición del scroll: setCurrentItem() hace scrollToItem()
            # internamente, lo que causaría que la vista salte de vuelta al ítem
            # cada vez que el corrector emite resultados (~800 ms de debounce).
            _vbar = self._list.verticalScrollBar()
            _scroll_pos = _vbar.value()
            self._list.setCurrentItem(item_to_select)
            _vbar.setValue(_scroll_pos)

        self._update_buttons()
        # No llamar _apply_theme() aquí: resetear el stylesheet en cada revisión
        # causa parpadeo en los estados hover/active de los widgets.

    def refresh_theme(self):
        """Actualiza colores al cambiar el tema de la app."""
        self._apply_theme()

    # ------------------------------------------------------------------
    # Slots internos
    # ------------------------------------------------------------------

    def _on_toggle(self):
        enabled = self._btn_toggle.isChecked()
        self._checker.enabled = enabled
        if not enabled:
            self._list.clear()
            self._count_lbl.setText("Corrector desactivado")
            self._update_buttons()
        else:
            self._count_lbl.setText("Revisando ortografía…")
            self.recheck_requested.emit()
        # Actualizar icono del toggle y colores del panel
        self._apply_theme()

    def _on_language_changed(self, index: int):
        code = self._combo_lang.itemData(index)
        if code:
            self._checker.set_language(code)
            if self._checker.enabled:
                self._count_lbl.setText("Revisando ortografía…")
                self.recheck_requested.emit()

    def _selected_error(self) -> SpellError | None:
        items = self._list.selectedItems()
        if not items:
            return None
        return items[0].data(Qt.ItemDataRole.UserRole)

    def _on_item_double_clicked(self, item: QListWidgetItem):
        err = item.data(Qt.ItemDataRole.UserRole)
        if err:
            self.navigate_to_error.emit(err.start, err.end)

    def _on_goto(self):
        err = self._selected_error()
        if err:
            self.navigate_to_error.emit(err.start, err.end)

    def _on_ignore(self):
        err = self._selected_error()
        if err:
            self._checker.ignore_word(err.word)
            self.word_ignored.emit(err.word)

    def _on_add_to_dict(self):
        err = self._selected_error()
        if err:
            self._checker.add_to_personal_dictionary(err.word)
            self.word_added_to_dict.emit(err.word)

    def _update_buttons(self):
        has_sel = bool(self._list.selectedItems())
        self._btn_goto.setEnabled(has_sel)
        self._btn_ignore.setEnabled(has_sel)
        self._btn_add.setEnabled(has_sel)
