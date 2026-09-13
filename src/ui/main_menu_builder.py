"""
Aura Writer — Main Menu & Toolbar Builder Mixin
Construcción de menús, barras de herramientas con acciones reactivas y actualización de estado.
"""

from PyQt6.QtWidgets import QToolBar, QMenu
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QKeySequence, QTextCharFormat, QFont, QAction
import qtawesome as qta


class MainMenuBuilderMixin:
    """Mixin para la construcción de barras de menú y herramientas de AuraMainWindow."""

    def setup_menus(self):
        """Construye todos los menús de la barra superior."""
        mb = self.menuBar()

        # ── Archivo ──────────────────────────────────────────────────
        file_menu = mb.addMenu("&Archivo")

        save_act = QAction("Guardar", self)
        save_act.setShortcut(QKeySequence.StandardKey.Save)
        save_act.triggered.connect(self.save_project)
        file_menu.addAction(save_act)

        search_act = QAction("🔍 Buscador Global…", self)
        search_act.setShortcut("Ctrl+F")
        search_act.triggered.connect(self.open_search)
        file_menu.addAction(search_act)
        file_menu.addSeparator()

        export_act = QAction("Exportar Obra…", self)
        export_act.triggered.connect(self.open_exporter)
        file_menu.addAction(export_act)

        file_menu.addSeparator()
        trash_act = QAction("🗑️ Papelera de Reciclaje…", self)
        trash_act.setShortcut("Ctrl+Shift+R")
        trash_act.triggered.connect(self.open_trash_dialog)
        file_menu.addAction(trash_act)

        # ── Edición ──────────────────────────────────────────────────
        edit_menu = mb.addMenu("&Edición")

        self._bold_act = QAction("𝐁 Negrita", self)
        self._bold_act.setShortcut(QKeySequence.StandardKey.Bold)
        self._bold_act.setCheckable(True)
        self._bold_act.triggered.connect(self.editor.set_bold)
        edit_menu.addAction(self._bold_act)

        self._italic_act = QAction("𝐼 Cursiva", self)
        self._italic_act.setShortcut(QKeySequence.StandardKey.Italic)
        self._italic_act.setCheckable(True)
        self._italic_act.triggered.connect(self.editor.set_italic)
        edit_menu.addAction(self._italic_act)

        self._underline_act = QAction("U̲ Subrayado", self)
        self._underline_act.setShortcut(QKeySequence.StandardKey.Underline)
        self._underline_act.setCheckable(True)
        self._underline_act.triggered.connect(self.editor.set_underline)
        edit_menu.addAction(self._underline_act)

        self._strike_act = QAction("S̶ Tachado", self)
        self._strike_act.setShortcut("Ctrl+K")
        self._strike_act.setCheckable(True)
        self._strike_act.triggered.connect(self.editor.set_strikethrough)
        edit_menu.addAction(self._strike_act)

        self._clean_act = QAction("🧹 Limpiar Formato", self)
        self._clean_act.setShortcut("Ctrl+\\")
        self._clean_act.triggered.connect(self.editor.clear_formatting)
        edit_menu.addAction(self._clean_act)

        edit_menu.addSeparator()

        dot_act = QAction("· Punto Medio (Conlang / Morfología)", self)
        dot_act.setShortcut("Ctrl+.")
        dot_act.triggered.connect(self.editor.insert_middle_dot)
        edit_menu.addAction(dot_act)

        dash_act = QAction("— Raya de Diálogo (Guion Largo)", self)
        dash_act.setShortcut("Ctrl+-")
        dash_act.triggered.connect(self.editor.insert_em_dash)
        edit_menu.addAction(dash_act)

        sep_act = QAction("* * * Separador de Escena", self)
        sep_act.triggered.connect(self.editor.insert_scene_separator)
        edit_menu.addAction(sep_act)

        pb_act = QAction("Salto de Página", self)
        pb_act.triggered.connect(self.editor.insert_page_break)
        edit_menu.addAction(pb_act)

        # ── Vista ────────────────────────────────────────────────────
        view_menu = mb.addMenu("&Vista")

        map_act = QAction("🗺️ Mapa Mental del Universo", self)
        map_act.triggered.connect(self.open_universe_map)
        view_menu.addAction(map_act)

        graph_act = QAction("🔗 Relaciones de Personajes", self)
        graph_act.triggered.connect(self.open_relation_graph)
        view_menu.addAction(graph_act)

        view_menu.addSeparator()
        self._theme_act = QAction("\U0001f319 Cambiar a Tema Claro", self)
        self._theme_act.setShortcut("Ctrl+Shift+T")
        self._theme_act.triggered.connect(self._toggle_theme)
        view_menu.addAction(self._theme_act)
        self._update_theme_action_label()

        # ── Seguridad ────────────────────────────────────────────────
        sec_menu = mb.addMenu("&Seguridad")

        lock_act = QAction("🔒 Bloqueo Rápido", self)
        lock_act.setShortcut("Ctrl+L")
        lock_act.triggered.connect(self.quick_lock)
        sec_menu.addAction(lock_act)

        sec_menu.addSeparator()

        totp_act = QAction("🛡️ Configurar / Administrar 2FA…", self)
        totp_act.triggered.connect(self.configure_totp)
        sec_menu.addAction(totp_act)

        pwd_act = QAction("🔑 Cambiar Contraseña del Proyecto…", self)
        pwd_act.triggered.connect(self.change_password_dialog)
        sec_menu.addAction(pwd_act)

        # ── USB & Sincronización ─────────────────────────────────────
        usb_menu = mb.addMenu("&USB")

        usb_config_act = QAction("⚙️ Configurar USB…", self)
        usb_config_act.triggered.connect(self.open_usb_config)
        usb_menu.addAction(usb_config_act)

        usb_sync_act = QAction("🔄 Sincronizar Ahora", self)
        usb_sync_act.setShortcut("Ctrl+Shift+S")
        usb_sync_act.triggered.connect(self.sync_usb_now)
        usb_menu.addAction(usb_sync_act)

        usb_menu.addSeparator()
        usb_status_act = QAction("📊 Estado de USB", self)
        usb_status_act.triggered.connect(self.show_usb_status)
        usb_menu.addAction(usb_status_act)

    def setup_toolbar(self):
        """Construye la barra de herramientas principal."""
        toolbar = QToolBar("Principal")
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(toolbar)

        try:
            _ic = "#aeaeb2"  # gris claro — visible sobre fondos oscuros

            toolbar.addAction(qta.icon("fa5s.save", color="#30d158"), "Guardar", self.save_project)
            toolbar.addSeparator()

            self._bold_act.setIcon(qta.icon("fa5s.bold", color=_ic))
            self._bold_act.setText("Negrita (Ctrl+B)")
            toolbar.addAction(self._bold_act)

            self._italic_act.setIcon(qta.icon("fa5s.italic", color=_ic))
            self._italic_act.setText("Cursiva (Ctrl+I)")
            toolbar.addAction(self._italic_act)

            self._underline_act.setIcon(qta.icon("fa5s.underline", color=_ic))
            self._underline_act.setText("Subrayado (Ctrl+U)")
            toolbar.addAction(self._underline_act)

            self._strike_act.setIcon(qta.icon("fa5s.strikethrough", color=_ic))
            self._strike_act.setText("Tachado (Ctrl+K)")
            toolbar.addAction(self._strike_act)

            self._clean_act.setIcon(qta.icon("fa5s.eraser", color=_ic))
            self._clean_act.setText("Limpiar Formato (Ctrl+\\)")
            toolbar.addAction(self._clean_act)

            toolbar.addSeparator()
            toolbar.addAction(qta.icon("fa5s.align-left", color=_ic), "Izq", self.editor.align_left)
            toolbar.addAction(qta.icon("fa5s.align-center", color=_ic), "Centrar", self.editor.align_center)
            toolbar.addAction(qta.icon("fa5s.align-right", color=_ic), "Der", self.editor.align_right)
            toolbar.addAction(qta.icon("fa5s.align-justify", color=_ic), "Justificar", self.editor.align_justify)

            toolbar.addSeparator()
            toolbar.addAction(qta.icon("fa5s.circle", color="#ffd60a"), "Punto Medio · (Ctrl+.)", self.editor.insert_middle_dot)
            toolbar.addAction(qta.icon("fa5s.minus", color="#ffd60a"), "Raya — (Ctrl+- o escribir --)", self.editor.insert_em_dash)
            toolbar.addAction(qta.icon("fa5s.asterisk", color="#ffd60a"), "Separador * * *", self.editor.insert_scene_separator)
            toolbar.addAction(qta.icon("fa5s.cut", color="#ff453a"), "Salto de Pág", self.editor.insert_page_break)
            toolbar.addAction(qta.icon("fa5s.file-alt", color=_ic), "Pág en Blanco", self.editor.insert_blank_page)
            toolbar.addAction(qta.icon("fa5s.image", color="#32ade6"), "Imagen", self.insert_media)

            toolbar.addSeparator()
            toolbar.addAction(qta.icon("fa5s.search", color=_ic), "Buscador Global", self.open_search)
            toolbar.addAction(qta.icon("fa5s.lock", color="#ff9f0a"), "Bloqueo Rápido", self.quick_lock)

            toolbar.addSeparator()
            toolbar.addAction(qta.icon("fa5s.globe", color="#bf5af2"), "Mapa Mental", self.open_universe_map)
            toolbar.addAction(qta.icon("fa5s.project-diagram", color="#5e5ce6"), "Relaciones", self.open_relation_graph)
            toolbar.addSeparator()
            toolbar.addAction(qta.icon("fa5s.file-export", color="#30d158"), "Exportar", self.open_exporter)
            toolbar.addAction(qta.icon("fa5s.trash-alt", color="#ff453a"), "Papelera", self.open_trash_dialog)

            toolbar.addSeparator()
            self._theme_btn_action = toolbar.addAction(
                qta.icon("fa5s.sun", color="#ffd60a"), "Cambiar Tema", self._toggle_theme
            )
            self._update_theme_action_label()
        except Exception:
            toolbar.addAction("Guardar", self.save_project)
            toolbar.addSeparator()
            toolbar.addAction(self._bold_act)
            toolbar.addAction(self._italic_act)
            toolbar.addAction(self._underline_act)
            toolbar.addAction(self._strike_act)
            toolbar.addAction(self._clean_act)
            toolbar.addSeparator()
            toolbar.addAction("Izq", self.editor.align_left)
            toolbar.addAction("Cen", self.editor.align_center)
            toolbar.addAction("Der", self.editor.align_right)
            toolbar.addAction("Jus", self.editor.align_justify)
            toolbar.addSeparator()
            toolbar.addAction("·", self.editor.insert_middle_dot)
            toolbar.addAction("* * *", self.editor.insert_scene_separator)
            toolbar.addAction("Salto Pág", self.editor.insert_page_break)
            toolbar.addAction("Pág Blanco", self.editor.insert_blank_page)
            toolbar.addSeparator()
            toolbar.addAction("Img", self.insert_media)
            toolbar.addSeparator()
            toolbar.addAction("Mapa", self.open_universe_map)
            toolbar.addAction("Nodos", self.open_relation_graph)
            toolbar.addSeparator()
            toolbar.addAction("Exportar", self.open_exporter)

    def _update_format_actions(self, fmt: QTextCharFormat):
        """Sincroniza el estado visual de los botones de formato con el formato bajo el cursor."""
        if hasattr(self, '_bold_act'):
            weight = fmt.fontWeight()
            self._bold_act.setChecked(weight >= 600 or self.editor.fontWeight() >= 600)
        if hasattr(self, '_italic_act'):
            self._italic_act.setChecked(fmt.fontItalic() or self.editor.fontItalic())
        if hasattr(self, '_underline_act'):
            self._underline_act.setChecked(fmt.fontUnderline() or self.editor.fontUnderline())
        if hasattr(self, '_strike_act'):
            self._strike_act.setChecked(fmt.fontStrikeOut())
