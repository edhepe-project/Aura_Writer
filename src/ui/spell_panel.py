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
from PyQt6.QtCore import Qt, pyqtSignal, QSize
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
        ThemeManager.signals.theme_changed.connect(lambda _: self._apply_theme())

    # ------------------------------------------------------------------
    # Construcción de la UI
    # ------------------------------------------------------------------

    def _setup_ui(self):
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumWidth(200)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        # ── Encabezado compacto ───────────────────────────────────────
        header = QHBoxLayout()
        header.setContentsMargins(0, 2, 0, 2)
        header.setSpacing(6)

        self._icon_lbl = QLabel()
        self._title_lbl = QLabel("CORRECTOR")
        font_title = QFont()
        font_title.setBold(True)
        font_title.setPointSize(9)
        self._title_lbl.setFont(font_title)
        
        header.addWidget(self._icon_lbl)
        header.addWidget(self._title_lbl)
        header.addStretch()

        # Switch / Toggle on/off estilo pill cómodo
        self._btn_toggle = QPushButton()
        self._btn_toggle.setObjectName("spellToggleBtn")
        self._btn_toggle.setCheckable(True)
        self._btn_toggle.setChecked(False)
        self._btn_toggle.setFixedSize(42, 26)
        self._btn_toggle.setToolTip("Activar / Desactivar corrector")
        self._btn_toggle.clicked.connect(self._on_toggle)
        header.addWidget(self._btn_toggle)
        root.addLayout(header)

        # ── Barra de control: Idioma y Estado ─────────────────────────
        ctrl_bar = QFrame()
        cbl = QHBoxLayout(ctrl_bar)
        cbl.setContentsMargins(0, 0, 0, 0)
        cbl.setSpacing(6)

        self._combo_lang = QComboBox()
        for code, name in SUPPORTED_LANGUAGES:
            self._combo_lang.addItem(name, code)
        idx = self._combo_lang.findData(self._checker.language)
        if idx >= 0:
            self._combo_lang.setCurrentIndex(idx)
        self._combo_lang.currentIndexChanged.connect(self._on_language_changed)
        cbl.addWidget(self._combo_lang, 1)

        self._count_badge = QLabel("Desactivado")
        self._count_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_badge = QFont()
        font_badge.setPointSize(9)
        font_badge.setBold(True)
        self._count_badge.setFont(font_badge)
        self._count_badge.setFixedHeight(26)
        cbl.addWidget(self._count_badge)

        root.addWidget(ctrl_bar)

        # Separador horizontal sutil
        self._sep = QFrame()
        self._sep.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(self._sep)

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
        btn_layout.setContentsMargins(0, 2, 0, 0)

        # Fila 1: [ Ir al error ] | [ Ignorar ]
        btn_row1 = QHBoxLayout()
        btn_row1.setSpacing(4)
        btn_row1.setContentsMargins(0, 0, 0, 0)

        self._btn_goto = QPushButton(" Ir al error")
        self._btn_goto.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._btn_goto.clicked.connect(self._on_goto)
        btn_row1.addWidget(self._btn_goto, 1)

        self._btn_ignore = QPushButton(" Ignorar")
        self._btn_ignore.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._btn_ignore.clicked.connect(self._on_ignore)
        btn_row1.addWidget(self._btn_ignore, 1)

        btn_layout.addLayout(btn_row1)

        # Fila 2: [ + Añadir al diccionario ]
        self._btn_add = QPushButton(" Añadir al diccionario")
        self._btn_add.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._btn_add.clicked.connect(self._on_add_to_dict)
        btn_layout.addWidget(self._btn_add)

        root.addLayout(btn_layout)

        # ── Pie de ayuda ──────────────────────────────────────────────
        self._footer_lbl = QLabel("Doble clic en un error para localizarlo")
        self._footer_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_xs = QFont()
        font_xs.setPointSize(8)
        self._footer_lbl.setFont(font_xs)
        root.addWidget(self._footer_lbl)

        self._count_lbl = self._count_badge  # Alias para compatibilidad
        self._update_buttons()

    def _apply_theme(self):
        c = ThemeManager.palette()
        bg = c["bg_surface"]
        fg = c["fg_primary"]
        sub_fg = c["fg_secondary"]
        muted_fg = c["fg_muted"]
        border = c["border_default"]
        item_alt = c["bg_app"]
        btn_bg = c["bg_button"]
        btn_hover = c["bg_hover"]
        btn_selected = c["bg_selected"]
        accent = c["accent"]
        accent_hover = c["accent_hover"]

        is_enabled = self._btn_toggle.isChecked()
        toggle_icon = "fa5s.toggle-on" if is_enabled else "fa5s.toggle-off"
        toggle_color = c["green"] if is_enabled else muted_fg
        try:
            self._btn_toggle.setIcon(qta.icon(toggle_icon, color=toggle_color))
            self._btn_toggle.setIconSize(QSize(26, 20))
        except Exception:
            pass

        try:
            self._icon_lbl.setPixmap(qta.icon("fa5s.spell-check", color=c["red"]).pixmap(16, 16))
            self._btn_goto.setIcon(qta.icon("fa5s.search", color=c["blue"]))
            self._btn_ignore.setIcon(qta.icon("fa5s.eye-slash", color=muted_fg))
            self._btn_add.setIcon(qta.icon("fa5s.plus-circle", color=c["green"]))
        except Exception:
            pass

        badge_bg = c["bg_hover"] if not is_enabled else (c["bg_selected"] if self._errors else c["bg_hover"])
        badge_fg = muted_fg if not is_enabled else (c["red"] if self._errors else c["green"])

        self.setStyleSheet(f"""
            SpellPanel {{
                background-color: {bg};
                color: {fg};
            }}
            QLabel {{
                color: {fg};
            }}
            QPushButton#spellToggleBtn {{
                background-color: {c['bg_hover'] if not is_enabled else c['bg_selected']};
                border: 1px solid {c['accent'] if is_enabled else border};
                border-radius: 13px;
                padding: 0px;
            }}
            QPushButton#spellToggleBtn:hover {{
                background-color: {c['bg_selected']};
                border-color: {accent};
            }}
            QListWidget {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 6px;
                alternate-background-color: {item_alt};
            }}
            QListWidget::item {{
                padding: 5px 8px;
                border-radius: 4px;
            }}
            QListWidget::item:selected {{
                background-color: {accent};
                color: {c['fg_selected']};
            }}
            QListWidget::item:hover {{
                background-color: {btn_selected};
            }}
            QListWidget::item:selected:hover {{
                background-color: {accent_hover};
            }}
            QPushButton {{
                background-color: {btn_bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 5px 8px;
                font-size: 11px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {btn_hover};
                border-color: {accent};
            }}
            QPushButton:disabled {{
                color: {c['fg_disabled']};
                background-color: {c['bg_disabled']};
                border-color: {border};
            }}
            QComboBox {{
                background-color: {c['bg_input']};
                color: {fg};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 3px 8px;
                font-size: 11px;
                font-weight: 500;
            }}
            QComboBox:hover {{
                border-color: {accent};
            }}
            QFrame[frameShape="4"] {{
                color: {border};
            }}
        """)
        self._count_badge.setStyleSheet(f"""
            QLabel {{
                background-color: {badge_bg};
                color: {badge_fg};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 2px 8px;
                font-size: 10px;
            }}
        """)
        self._footer_lbl.setStyleSheet(f"color: {muted_fg};")

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
            if not self._checker.show_errors:
                self._count_lbl.setText("En pausa")
            else:
                self._count_lbl.setText("0 errores")
            self._update_buttons()
            self._apply_theme()
            return

        n = len(errors)
        self._count_lbl.setText(f"{n} error{'es' if n != 1 else ''}")

        error_color = QColor(ThemeManager.color("red"))
        item_to_select = None
        for err in errors:
            # Mostrar: "palabra → sugerencia1, sugerencia2…"
            sugs = ", ".join(err.suggestions[:2]) if err.suggestions else "sin sugerencias"
            item = QListWidgetItem(f" {err.word}  →  {sugs}")
            item.setData(Qt.ItemDataRole.UserRole, err)
            item.setForeground(error_color)
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
        self._apply_theme()
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
            self._count_lbl.setText("Revisando capítulo…")
            self.recheck_requested.emit()
        # Actualizar icono del toggle y colores del panel
        self._apply_theme()

    def _on_language_changed(self, index: int):
        code = self._combo_lang.itemData(index)
        if code:
            self._checker.set_language(code)
            if self._checker.show_errors:
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
