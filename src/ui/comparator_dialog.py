"""
Aura Writer — Diálogo de Mesa de Cotejo (Comparador de Capítulos)
Permite visualizar y editar dos capítulos simultáneamente lado a lado con
scroll sincronizado, contadores de palabras y persistencia directa en el proyecto.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter, QFrame,
    QLabel, QComboBox, QPushButton, QTextEdit, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import qtawesome as qta


class ChapterEditorPanel(QFrame):
    """Panel individual para un capítulo (selector, contador y editor editable)."""

    def __init__(self, title_prefix: str, parent=None):
        super().__init__(parent)
        self.title_prefix = title_prefix
        self.chapter_id = None
        self.content_file = None
        self._dirty = False

        from core.theme_manager import ThemeManager
        is_dark = ThemeManager.is_dark()

        panel_bg = "#1c1c1e" if is_dark else "#faf7f3"
        panel_border = "#2c2c2e" if is_dark else "#d4cfc8"
        combo_bg = "#2c2c2e" if is_dark else "#ede8e1"
        combo_fg = "#f2f2f7" if is_dark else "#1a1a2e"
        combo_border = "#3a3a3c" if is_dark else "#c4bfb8"
        editor_bg = "#141416" if is_dark else "#ffffff"
        editor_fg = "#e5e5ea" if is_dark else "#1a1a2e"
        editor_border = "#2c2c2e" if is_dark else "#d4cfc8"
        subtext_color = "#8e8e93" if is_dark else "#7a7a8a"

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"""
            ChapterEditorPanel {{
                background-color: {panel_bg};
                border: 1px solid {panel_border};
                border-radius: 8px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Header: Título + Combo de selección
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        lbl = QLabel(f"<b>{title_prefix}:</b>")
        lbl.setStyleSheet(f"color: {'#9b59b6' if is_dark else '#6b21a8'}; font-size: 13px;")
        header_layout.addWidget(lbl)

        self.combo = QComboBox()
        self.combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {combo_bg};
                color: {combo_fg};
                border: 1px solid {combo_border};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {combo_bg};
                color: {combo_fg};
                selection-background-color: {'#5e5ce6' if is_dark else '#d4a017'};
                selection-color: {'#ffffff' if is_dark else '#000000'};
            }}
        """)
        header_layout.addWidget(self.combo, 1)
        layout.addLayout(header_layout)

        # Editor de texto enriquecido con estilo adaptativo
        self.editor = QTextEdit()
        font = QFont("Georgia", 13)
        font.setStyleHint(QFont.StyleHint.Serif)
        self.editor.setFont(font)
        self.editor.setStyleSheet(f"""
            QTextEdit {{
                background-color: {editor_bg};
                color: {editor_fg};
                border: 1px solid {editor_border};
                border-radius: 6px;
                padding: 12px;
                line-height: 1.6;
                selection-background-color: {'#5e5ce6' if is_dark else '#c8c0b8'};
            }}
        """)
        self.editor.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.editor, 1)

        # Footer: Contador de palabras
        self.stats_lbl = QLabel("Palabras: 0  |  Caracteres: 0")
        self.stats_lbl.setStyleSheet(f"color: {subtext_color}; font-size: 11px;")
        layout.addWidget(self.stats_lbl)

    def _on_text_changed(self):
        self._dirty = True
        text = self.editor.toPlainText()
        words = len(text.split())
        chars = len(text)
        self.stats_lbl.setText(f"Palabras: {words:,}  |  Caracteres: {chars:,}")


class ChapterComparatorDialog(QDialog):
    """Mesa de cotejo lado a lado para comparar y afinar capítulos en vivo."""

    def __init__(self, project_manager, initial_chapter=None, parent=None):
        super().__init__(parent)
        self.pm = project_manager
        self.initial_chapter = initial_chapter
        self._syncing_scroll = False

        self.setWindowTitle("⚖️ Mesa de Cotejo Literaria — Comparar Capítulos")
        self.resize(1180, 780)
        self.setMinimumSize(850, 550)

        self._setup_ui()
        self._load_chapters_into_combos()

    def _setup_ui(self):
        from core.theme_manager import ThemeManager
        is_dark = ThemeManager.is_dark()

        title_color = "#f2f2f7" if is_dark else "#1a1a2e"
        desc_color = "#8e8e93" if is_dark else "#646470"
        chk_color = "#e5e5ea" if is_dark else "#1a1a2e"
        tip_color = "#8e8e93" if is_dark else "#7a7a8a"
        btn_close_bg = "#2c2c2e" if is_dark else "#ede8e1"
        btn_close_fg = "#e5e5ea" if is_dark else "#1a1a2e"
        btn_close_border = "#3a3a3c" if is_dark else "#c4bfb8"

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # Barra superior con opciones de control
        top_bar = QHBoxLayout()
        top_bar.setSpacing(14)

        icon_lbl = QLabel()
        icon_color = "#9b59b6" if is_dark else "#6b21a8"
        icon_lbl.setPixmap(qta.icon("fa5s.columns", color=icon_color).pixmap(20, 20))
        top_bar.addWidget(icon_lbl)

        title_lbl = QLabel("<b>Mesa de Cotejo & Armonización de Tono</b>")
        title_lbl.setStyleSheet(f"font-size: 14px; color: {title_color};")
        top_bar.addWidget(title_lbl)

        desc_lbl = QLabel("Compara dos versiones o capítulos y edítalos lado a lado.")
        desc_lbl.setStyleSheet(f"color: {desc_color}; font-size: 12px;")
        top_bar.addWidget(desc_lbl)

        top_bar.addStretch()

        # Checkbox de scroll sincronizado
        self.sync_scroll_chk = QCheckBox("Scroll Sincronizado")
        self.sync_scroll_chk.setChecked(True)
        self.sync_scroll_chk.setStyleSheet(f"""
            QCheckBox {{
                color: {chk_color};
                font-size: 12px;
                font-weight: 500;
                spacing: 6px;
            }}
        """)
        top_bar.addWidget(self.sync_scroll_chk)

        root.addLayout(top_bar)

        # Splitter central con los dos paneles
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(4)

        self.panel_a = ChapterEditorPanel("Capítulo Izquierdo", self)
        self.panel_b = ChapterEditorPanel("Capítulo Derecho", self)

        self.splitter.addWidget(self.panel_a)
        self.splitter.addWidget(self.panel_b)
        self.splitter.setSizes([590, 590])
        root.addWidget(self.splitter, 1)

        # Conectar scrollbars para sincronización bidireccional
        sb_a = self.panel_a.editor.verticalScrollBar()
        sb_b = self.panel_b.editor.verticalScrollBar()
        sb_a.valueChanged.connect(self._sync_scroll_a_to_b)
        sb_b.valueChanged.connect(self._sync_scroll_b_to_a)

        # Conectar selección de capítulos
        self.panel_a.combo.currentIndexChanged.connect(lambda idx: self._on_chapter_selected(self.panel_a, idx))
        self.panel_b.combo.currentIndexChanged.connect(lambda idx: self._on_chapter_selected(self.panel_b, idx))

        # Barra inferior de acciones
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(10)

        status_tip = QLabel("💡 Tip: Los cambios realizados aquí se guardan directamente en el proyecto.")
        status_tip.setStyleSheet(f"color: {tip_color}; font-size: 11px;")
        bottom_bar.addWidget(status_tip)

        bottom_bar.addStretch()

        btn_save = QPushButton("💾 Guardar Cambios")
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #30d158;
                color: #ffffff;
                font-weight: bold;
                border-radius: 5px;
                padding: 6px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #28b84c;
            }
        """)
        btn_save.clicked.connect(self._save_all)
        bottom_bar.addWidget(btn_save)

        btn_close = QPushButton("Cerrar")
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: {btn_close_bg};
                color: {btn_close_fg};
                border: 1px solid {btn_close_border};
                border-radius: 5px;
                padding: 6px 14px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {'#3a3a3c' if is_dark else '#dedad2'};
            }}
        """)
        btn_close.clicked.connect(self.close)
        bottom_bar.addWidget(btn_close)

        root.addLayout(bottom_bar)

    def _sync_scroll_a_to_b(self, val):
        if not self.sync_scroll_chk.isChecked() or self._syncing_scroll:
            return
        self._syncing_scroll = True
        sb_a = self.panel_a.editor.verticalScrollBar()
        sb_b = self.panel_b.editor.verticalScrollBar()
        max_a = sb_a.maximum() or 1
        max_b = sb_b.maximum() or 1
        ratio = val / max_a
        sb_b.setValue(int(ratio * max_b))
        self._syncing_scroll = False

    def _sync_scroll_b_to_a(self, val):
        if not self.sync_scroll_chk.isChecked() or self._syncing_scroll:
            return
        self._syncing_scroll = True
        sb_a = self.panel_a.editor.verticalScrollBar()
        sb_b = self.panel_b.editor.verticalScrollBar()
        max_a = sb_a.maximum() or 1
        max_b = sb_b.maximum() or 1
        ratio = val / max_b
        sb_a.setValue(int(ratio * max_a))
        self._syncing_scroll = False

    def _collect_all_chapters(self):
        """Retorna una lista de tuplas (id, label_jerarquico, content_file, chapter_obj)."""
        chapters = []
        meta = self.pm.metadata
        if not meta:
            return chapters

        for o in meta.obras:
            for lib in o.libros:
                for cap in lib.capitulos:
                    label = f"{lib.title}  ›  {cap.title}"
                    chapters.append((cap.id, label, cap.content_file, cap))
        return chapters

    def _load_chapters_into_combos(self, select_a: "str | None" = None, select_b: "str | None" = None):
        chapters = self._collect_all_chapters()
        if not chapters:
            self.panel_a.editor.setPlaceholderText("No hay capítulos disponibles en el proyecto.")
            self.panel_b.editor.setPlaceholderText("No hay capítulos disponibles en el proyecto.")
            return

        self.panel_a.combo.blockSignals(True)
        self.panel_b.combo.blockSignals(True)
        self.panel_a.combo.clear()
        self.panel_b.combo.clear()

        idx_initial_a = 0
        idx_initial_b = 1 if len(chapters) > 1 else 0

        for i, (cid, label, cfile, cap) in enumerate(chapters):
            self.panel_a.combo.addItem(label, userData=(cid, cfile, cap))
            self.panel_b.combo.addItem(label, userData=(cid, cfile, cap))

            if select_a and cid == select_a:
                idx_initial_a = i
            elif not select_a and self.initial_chapter and cid == self.initial_chapter.id:
                idx_initial_a = i
                if i + 1 < len(chapters):
                    idx_initial_b = i + 1
                elif i > 0:
                    idx_initial_b = i - 1

            if select_b and cid == select_b:
                idx_initial_b = i

        self.panel_a.combo.setCurrentIndex(idx_initial_a)
        self.panel_b.combo.setCurrentIndex(idx_initial_b)

        self.panel_a.combo.blockSignals(False)
        self.panel_b.combo.blockSignals(False)

        self._on_chapter_selected(self.panel_a, idx_initial_a)
        self._on_chapter_selected(self.panel_b, idx_initial_b)

    def _on_chapter_selected(self, panel: ChapterEditorPanel, idx: int):
        data = panel.combo.itemData(idx)
        if not data:
            return
        cid, cfile, cap = data

        other_panel = self.panel_b if panel is self.panel_a else self.panel_a

        # Detectar si se está seleccionando el mismo capítulo que ya está en el otro panel
        if other_panel.chapter_id == cid:
            # Guardar el contenido que el usuario tuviera en el otro panel por si fue modificado
            if other_panel._dirty and other_panel.content_file:
                self.pm.write_chapter_content(other_panel.content_file, other_panel.editor.toHtml())

            from PyQt6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout
            from core.theme_manager import ThemeManager
            is_dark = ThemeManager.is_dark()

            branch_dlg = QDialog(self)
            branch_dlg.setWindowTitle("📄 ¿Deseas bifurcar este capítulo?")
            branch_dlg.setFixedWidth(560)

            dlg_layout = QVBoxLayout(branch_dlg)
            dlg_layout.setContentsMargins(20, 20, 20, 20)
            dlg_layout.setSpacing(16)

            title_msg = QLabel(f"<b>Has seleccionado «{cap.title}» en ambos lados de la mesa de cotejo.</b>")
            title_msg.setStyleSheet(f"font-size: 13px; color: {'#f2f2f7' if is_dark else '#1a1a2e'};")
            dlg_layout.addWidget(title_msg)

            info_msg = QLabel(
                "Para proteger tu obra de sobreescrituras accidentales, puedes crear una copia "
                "alternativa para experimentar libremente o abrirlo en modo lectura:"
            )
            info_msg.setWordWrap(True)
            info_msg.setStyleSheet(f"font-size: 12px; color: {'#8e8e93' if is_dark else '#646470'}; line-height: 1.4;")
            dlg_layout.addWidget(info_msg)

            btn_box = QHBoxLayout()
            btn_box.setSpacing(10)

            btn_branch = QPushButton("🌿 Crear Borrador Alternativo")
            btn_branch.setStyleSheet("""
                QPushButton {
                    background-color: #30d158;
                    color: white;
                    font-weight: bold;
                    padding: 8px 14px;
                    border-radius: 6px;
                    font-size: 12px;
                }
                QPushButton:hover { background-color: #28b84c; }
            """)

            btn_readonly = QPushButton("👀 Solo Lectura")
            btn_readonly.setStyleSheet(f"""
                QPushButton {{
                    background-color: {'#2c2c2e' if is_dark else '#ede8e1'};
                    color: {'#f2f2f7' if is_dark else '#1a1a2e'};
                    border: 1px solid {'#3a3a3c' if is_dark else '#c4bfb8'};
                    padding: 8px 14px;
                    border-radius: 6px;
                    font-size: 12px;
                }}
                QPushButton:hover {{ background-color: {'#3a3a3c' if is_dark else '#dedad2'}; }}
            """)

            btn_cancel = QPushButton("Cancelar")
            btn_cancel.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {'#8e8e93' if is_dark else '#7a7a8a'};
                    border: 1px solid {'#3a3a3c' if is_dark else '#c4bfb8'};
                    padding: 8px 14px;
                    border-radius: 6px;
                    font-size: 12px;
                }}
                QPushButton:hover {{ background-color: {'#2c2c2e' if is_dark else '#dedad2'}; }}
            """)

            user_action: list[str | None] = [None]
            def _choose_branch():
                user_action[0] = "branch"
                branch_dlg.accept()

            def _choose_readonly():
                user_action[0] = "readonly"
                branch_dlg.accept()

            def _choose_cancel():
                user_action[0] = "cancel"
                branch_dlg.reject()

            btn_branch.clicked.connect(_choose_branch)
            btn_readonly.clicked.connect(_choose_readonly)
            btn_cancel.clicked.connect(_choose_cancel)

            btn_box.addWidget(btn_branch)
            btn_box.addWidget(btn_readonly)
            btn_box.addStretch()
            btn_box.addWidget(btn_cancel)
            dlg_layout.addLayout(btn_box)

            branch_dlg.exec()
            chosen = user_action[0]

            if chosen == "branch":
                # 1. Crear nuevo capítulo duplicado en el mismo libro
                libro = self._find_parent_libro_for_chapter(cid)
                if not libro:
                    QMessageBox.warning(self, "Error", "No se pudo identificar el libro contenedor.")
                    return

                new_title = f"{cap.title} (Versión B)"
                # Tomar el contenido más fresco (del editor de other_panel o del archivo)
                fresh_content = other_panel.editor.toHtml()
                new_chapter = self.pm.create_chapter(new_title)
                self.pm.write_chapter_content(new_chapter.content_file, fresh_content)

                # Insertar en el libro justo después del original
                try:
                    orig_idx = libro.capitulos.index(cap)
                    libro.capitulos.insert(orig_idx + 1, new_chapter)
                except ValueError:
                    libro.capitulos.append(new_chapter)

                if libro.content_order:
                    orig_order_idx = next(
                        (i for i, e in enumerate(libro.content_order) if e.get("id") == cap.id),
                        None
                    )
                    if orig_order_idx is not None:
                        libro.content_order.insert(orig_order_idx + 1, {"type": "chapter", "id": new_chapter.id})
                    else:
                        libro.content_order.append({"type": "chapter", "id": new_chapter.id})

                self.pm.save_project()

                # Notificar a la ventana principal para que actualice su árbol
                parent_w = self.parent()
                if parent_w and hasattr(parent_w, "_refresh_tree"):
                    parent_w._refresh_tree()

                # Recargar combos manteniendo la selección del otro panel y seleccionando el nuevo en este
                other_selected_id = other_panel.chapter_id
                self._load_chapters_into_combos(select_a=other_selected_id if panel is self.panel_b else new_chapter.id,
                                                select_b=new_chapter.id if panel is self.panel_b else other_selected_id)
                return

            elif chosen == "readonly":
                # Cargar el mismo contenido pero poner este panel en solo lectura
                panel.chapter_id = cid
                panel.content_file = cfile
                html = self.pm.read_chapter_content(cfile)
                panel.editor.blockSignals(True)
                panel.editor.setHtml(html)
                panel.editor.setReadOnly(True)
                panel.editor.blockSignals(False)
                panel._dirty = False
                panel._on_text_changed()
                panel.stats_lbl.setText(panel.stats_lbl.text() + "  [🔒 Solo Lectura]")
                return

            else:
                # Cancelar: revertir el combo al capítulo que tenía previamente
                panel.combo.blockSignals(True)
                prev_idx = -1
                for i in range(panel.combo.count()):
                    d = panel.combo.itemData(i)
                    if d and d[0] == panel.chapter_id:
                        prev_idx = i
                        break
                if prev_idx != -1:
                    panel.combo.setCurrentIndex(prev_idx)
                panel.combo.blockSignals(False)
                return

        # Si no hay conflicto o es un capítulo distinto, restaurar modo editable
        panel.editor.setReadOnly(False)
        panel.chapter_id = cid
        panel.content_file = cfile

        html = self.pm.read_chapter_content(cfile)
        panel.editor.blockSignals(True)
        panel.editor.setHtml(html)
        panel.editor.blockSignals(False)
        panel._dirty = False
        panel._on_text_changed()

    def _find_parent_libro_for_chapter(self, chapter_id: str):
        meta = self.pm.metadata
        if not meta:
            return None
        for o in meta.obras:
            for lib in o.libros:
                for c in lib.capitulos:
                    if c.id == chapter_id:
                        return lib
        return None

    def _save_all(self):
        """Guarda los cambios de ambos paneles en el almacenamiento."""
        saved_any = False
        for panel in (self.panel_a, self.panel_b):
            if panel.content_file and panel._dirty:
                self.pm.write_chapter_content(panel.content_file, panel.editor.toHtml())
                panel._dirty = False
                saved_any = True

        if saved_any:
            self.pm.save_project()
            QMessageBox.information(self, "Mesa de Cotejo", "Cambios guardados con éxito en el proyecto.")
        else:
            QMessageBox.information(self, "Mesa de Cotejo", "No hay cambios pendientes por guardar.")

    def closeEvent(self, a0):
        event = a0
        if self.panel_a._dirty or self.panel_b._dirty:
            reply = QMessageBox.question(
                self, "Guardar cambios",
                "Has realizado cambios en la mesa de cotejo.\n¿Deseas guardarlos antes de salir?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )
            if reply == QMessageBox.StandardButton.Save:
                self._save_all()
                event.accept()
            elif reply == QMessageBox.StandardButton.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
