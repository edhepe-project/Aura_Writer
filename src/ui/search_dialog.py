import re
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
                             QListWidget, QListWidgetItem, QLabel, QPushButton,
                             QComboBox, QFrame, QWidget, QSizePolicy,
                             QScrollArea, QApplication)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QColor, QFont, QPalette
from bs4 import BeautifulSoup


class _ResultCard(QWidget):
    """
    Tarjeta de resultado en el buscador.
    Widget propio con layout fijo para que sizeHint() sea correcto.
    """
    clicked = pyqtSignal()

    def __init__(self, icon: str, title: str, location: str,
                 snippet: str, query: str):
        super().__init__()
        from core.theme_manager import ThemeManager
        self.setAutoFillBackground(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        is_dark = ThemeManager.is_dark()
        text_col = "#f2f2f7" if is_dark else "#1a1a2e"
        loc_col  = "#636366" if is_dark else "#7a7a8a"
        sub_col  = "#8e8e93" if is_dark else "#6a6a7a"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        # Línea 1 — ícono + título
        t_lbl = QLabel(f"<b>{icon} {_esc(title)}</b>")
        t_lbl.setTextFormat(Qt.TextFormat.RichText)
        t_lbl.setStyleSheet(f"color:{text_col}; font-size:13px;")
        layout.addWidget(t_lbl)

        # Línea 2 — ruta / breadcrumb
        loc_lbl = QLabel(f"📍 {_esc(location)}")
        loc_lbl.setStyleSheet(f"color:{loc_col}; font-size:11px;")
        layout.addWidget(loc_lbl)

        # Línea 3 — snippet resaltado
        if snippet:
            highlighted = _highlight(snippet, query, is_dark=is_dark)
            snip_lbl = QLabel(highlighted)
            snip_lbl.setTextFormat(Qt.TextFormat.RichText)
            snip_lbl.setWordWrap(True)
            snip_lbl.setStyleSheet(f"color:{sub_col}; font-size:11px;")
            snip_lbl.setSizePolicy(QSizePolicy.Policy.Expanding,
                                   QSizePolicy.Policy.Preferred)
            layout.addWidget(snip_lbl)


# ── Helpers ───────────────────────────────────────────────────────

def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _highlight(text: str, query: str, is_dark: bool = True, is_regex: bool = False) -> str:
    if not query:
        return _esc(text)
    escaped = _esc(text)
    try:
        pattern_str = query if is_regex else re.escape(query)
        pattern = re.compile(pattern_str, re.IGNORECASE)
    except re.error:
        pattern = re.compile(re.escape(query), re.IGNORECASE)

    if is_dark:
        hl_color   = "#ffd60a"
        hl_bg      = "#3a3a3c"
    else:
        hl_color   = "#7c4a00"
        hl_bg      = "#ffe08a"
    return pattern.sub(
        lambda m: (
            f"<b style='color:{hl_color}; background:{hl_bg};"
            f" padding:1px 3px; border-radius:3px;'>{_esc(m.group())}</b>"
        ),
        escaped
    )


# ── Diálogo principal ─────────────────────────────────────────────

class SearchDialog(QDialog):
    """
    Buscador Global Premium — Aura Writer.
    Busca en capítulos, personajes y notas; muestra ubicación y snippet.
    """
    result_selected = pyqtSignal(str, str)   # (item_id, item_type)

    def __init__(self, project_manager, parent=None):
        super().__init__(parent)
        self.pm = project_manager
        self.setWindowTitle("Buscador Global — Aura Writer")
        self.resize(720, 560)
        self.setMinimumSize(560, 420)

        self._setup_ui()
        # Focus al input al abrir
        QTimer.singleShot(0, self.search_input.setFocus)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 12)
        root.setSpacing(10)

        # ── Encabezado ───────────────────────────────────────────────
        header = QLabel("Buscar en el universo")
        header.setStyleSheet("font-size:11px; font-weight:600; letter-spacing:0.5px;")
        root.addWidget(header)

        # ── Barra de búsqueda + filtro ───────────────────────────────
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

        from PyQt6.QtWidgets import QCheckBox
        self.regex_check = QCheckBox("Regex")
        self.regex_check.setToolTip("Habilitar expresiones regulares en la búsqueda")
        self.regex_check.stateChanged.connect(self.perform_search)

        bar.addWidget(self.search_input, 1)
        bar.addWidget(self.filter_combo)
        bar.addWidget(self.regex_check)
        root.addLayout(bar)

        # ── Área de resultados — scroll con tarjetas ──────────────────
        self._results_area = QScrollArea()
        self._results_area.setWidgetResizable(True)
        self._results_area.setFrameShape(QFrame.Shape.NoFrame)

        from core.theme_manager import ThemeManager
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

        # ── Pie de página ─────────────────────────────────────────────
        self.status_lbl = QLabel("Escribe al menos 3 caracteres…")
        self.status_lbl.setStyleSheet("font-size:11px; padding:2px 2px;")
        root.addWidget(self.status_lbl)

    # ------------------------------------------------------------------
    # Búsqueda
    # ------------------------------------------------------------------

    def _on_query_changed(self):
        """Dispara la búsqueda con un pequeño retardo para no buscar en cada tecla."""
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
        count = 0
        seen_ids: set[str] = set()

        is_regex = self.regex_check.isChecked()
        compiled_regex = None
        if is_regex:
            try:
                compiled_regex = re.compile(query, re.IGNORECASE)
            except re.error as e:
                self.status_lbl.setText(f"Error en expresión regular: {e}")
                return

        def matches(target_text: str) -> bool:
            if not target_text:
                return False
            if is_regex and compiled_regex:
                return bool(compiled_regex.search(target_text))
            return query.lower() in target_text.lower()

        # 1. Capítulos
        if scope in ("Todo", "Capítulos"):
            for obra in self.pm.metadata.obras:
                for libro in obra.libros:
                    for cap in libro.capitulos:
                        if cap.id in seen_ids:
                            continue
                        location = f"{obra.title} › {libro.title}"
                        in_title = matches(cap.title)

                        content = self.pm.read_chapter_content(cap.content_file)
                        try:
                            text = BeautifulSoup(content, "lxml").get_text()
                        except Exception:
                            text = content
                        in_content = matches(text)

                        if in_title or in_content:
                            seen_ids.add(cap.id)
                            snippet = (self._get_snippet(text, query, is_regex=is_regex)
                                       if in_content else "Coincidencia en el título")
                            self._add_card("📖", cap.title, location,
                                           snippet, query, cap.id, "chapter", is_regex=is_regex)
                            count += 1

        # 2. Personajes
        if scope in ("Todo", "Personajes"):
            for char in self.pm.metadata.characters:
                if char.id in seen_ids:
                    continue
                in_name = matches(char.name)
                in_desc = matches(char.description)
                if in_name or in_desc:
                    seen_ids.add(char.id)
                    snippet = (self._get_snippet(char.description, query, is_regex=is_regex)
                               if in_desc else "Coincidencia en el nombre")
                    self._add_card("👤", char.name, "Personajes",
                                   snippet, query, char.id, "character", is_regex=is_regex)
                    count += 1

        # 3. Notas de Autor
        if scope in ("Todo", "Notas"):
            for obra in self.pm.metadata.obras:
                for libro in obra.libros:
                    for cap in libro.capitulos:
                        for note in cap.author_notes:
                            if note.id in seen_ids:
                                continue
                            in_title  = matches(note.title)
                            in_body   = matches(note.content)
                            if in_title or in_body:
                                seen_ids.add(note.id)
                                location = f"{obra.title} › {libro.title} › {cap.title}"
                                snippet  = (self._get_snippet(note.content, query, is_regex=is_regex)
                                            if in_body else "Coincidencia en el título")
                                self._add_card("📌", f"Nota: {note.title}", location,
                                               snippet, query, cap.id, "chapter", is_regex=is_regex)
                                count += 1

        if count == 0:
            from core.theme_manager import ThemeManager
            empty_col = "#8e8e93" if ThemeManager.is_dark() else "#78716c"
            empty = QLabel(f"Sin resultados para «{query}»")
            empty.setStyleSheet(f"color:{empty_col}; font-size:13px; padding:24px; background:transparent;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # Insertar antes del stretch
            self._cards_layout.insertWidget(0, empty)
            self.status_lbl.setText("")
        else:
            plural = "s" if count != 1 else ""
            self.status_lbl.setText(f"{count} resultado{plural} encontrado{plural}")

    # ------------------------------------------------------------------
    # Tarjetas de resultados
    # ------------------------------------------------------------------

    def _clear_cards(self):
        """Elimina todas las tarjetas manteniendo el stretch al final."""
        while self._cards_layout.count() > 1:
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _add_card(self, icon, title, location, snippet,
                  query, item_id, item_type, is_regex: bool = False):
        """Crea una tarjeta clickeable y la inserta antes del stretch."""
        card = _ResultCardWidget(icon, title, location, snippet, query,
                                 item_id, item_type, is_regex=is_regex)
        card.activated.connect(self._on_card_activated)
        idx = self._cards_layout.count() - 1   # antes del stretch
        self._cards_layout.insertWidget(idx, card)

    def _on_card_activated(self, item_id: str, item_type: str):
        self.result_selected.emit(item_id, item_type)
        self.accept()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_snippet(text: str, query: str, context: int = 60, is_regex: bool = False) -> str:
        if is_regex:
            try:
                m = re.search(query, text, re.IGNORECASE)
                if m:
                    idx = m.start()
                    q_len = max(1, m.end() - m.start())
                else:
                    idx = -1
                    q_len = len(query)
            except re.error:
                idx = text.lower().find(query.lower())
                q_len = len(query)
        else:
            idx = text.lower().find(query.lower())
            q_len = len(query)

        if idx == -1:
            return text[:120] + ("…" if len(text) > 120 else "")
        start = max(0, idx - context)
        end   = min(len(text), idx + q_len + context)
        pre   = "…" if start > 0 else ""
        suf   = "…" if end < len(text) else ""
        return f"{pre}{text[start:end].replace(chr(10), ' ').strip()}{suf}"


# ── Tarjeta clickeable ────────────────────────────────────────────

class _ResultCardWidget(QFrame):
    """Fila de resultado: fondo alternado, hover highlight, clic → emite señal."""
    activated = pyqtSignal(str, str)   # (item_id, item_type)

    _count = 0   # contador de instancias para alternar colores

    def __init__(self, icon, title, location, snippet,
                 query, item_id, item_type, is_regex: bool = False):
        super().__init__()
        from core.theme_manager import ThemeManager

        _ResultCardWidget._count += 1
        self._item_id   = item_id
        self._item_type = item_type
        self._is_regex  = is_regex
        is_dark = ThemeManager.is_dark()

        if is_dark:
            self._even_bg  = "#1c1c1e"
            self._odd_bg   = "#242426"
            self._hover_bg = "#2c2c2e"
            self._border_col = "#2c2c2e"
            self._hover_border = "#3a3a3c"
            self._hover_bar = "#636366"
            text_col = "#f2f2f7"
            sub_col = "#8e8e93"
            loc_col = "#636366"
        else:
            self._even_bg  = "#f5f0ea"
            self._odd_bg   = "#ede8e1"
            self._hover_bg = "#dedad2"
            self._border_col = "#d4cfc8"
            self._hover_border = "#c4bfb8"
            self._hover_bar = "#9a9490"
            text_col = "#1a1a2e"
            sub_col = "#7a7a8a"
            loc_col = "#7a7a8a"

        self._bg = self._even_bg if _ResultCardWidget._count % 2 == 0 else self._odd_bg

        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame {{
                background: {self._bg};
                border: none;
                border-bottom: 1px solid {self._border_col};
            }}
        """)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(3)

        # Título
        t = QLabel(f"<b>{_esc(icon)} {_esc(title)}</b>")
        t.setTextFormat(Qt.TextFormat.RichText)
        t.setStyleSheet(f"color:{text_col}; font-size:13px; background:transparent;")
        layout.addWidget(t)

        # Ubicación
        loc = QLabel(f"{'  '}{_esc(location)}")
        loc.setStyleSheet(f"color:{loc_col}; font-size:11px; background:transparent;")
        layout.addWidget(loc)

        # Snippet
        if snippet:
            hl = _highlight(snippet, query, is_dark=is_dark, is_regex=self._is_regex)
            snip = QLabel(hl)
            snip.setTextFormat(Qt.TextFormat.RichText)
            snip.setWordWrap(True)
            snip.setStyleSheet(f"color:{sub_col}; font-size:11px; background:transparent;")
            layout.addWidget(snip)

    def enterEvent(self, event):
        self.setStyleSheet(f"""
            QFrame {{
                background: {self._hover_bg};
                border: none;
                border-bottom: 1px solid {self._hover_border};
                border-left: 3px solid {self._hover_bar};
            }}
        """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(f"""
            QFrame {{
                background: {self._bg};
                border: none;
                border-bottom: 1px solid {self._border_col};
            }}
        """)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.activated.emit(self._item_id, self._item_type)
        super().mousePressEvent(event)
