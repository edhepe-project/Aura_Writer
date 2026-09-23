"""
Aura Writer — Main Menu & Toolbar Builder Mixin
Construcción de menús, barras de herramientas con acciones reactivas y actualización de estado.
"""

from PyQt6.QtWidgets import QToolBar
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QKeySequence, QTextCharFormat, QAction, QActionGroup
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

        places_graph_act = QAction("🗺️ Atlas de Lugares y Conexiones", self)
        places_graph_act.setShortcut("Ctrl+Alt+G")
        places_graph_act.triggered.connect(self.open_place_graph_dialog)
        view_menu.addAction(places_graph_act)

        grid_act = QAction("📊 Cuadrícula de Presencias", self)
        grid_act.setShortcut("Ctrl+Alt+P")
        grid_act.setToolTip("Ver y editar qué personajes aparecen en cada capítulo")
        grid_act.triggered.connect(self.open_presence_grid_dialog)
        view_menu.addAction(grid_act)

        places_act = QAction("🏰 Lugares && Escenarios", self)
        places_act.setShortcut("Ctrl+Alt+L")
        places_act.triggered.connect(lambda: self.open_place_edit_dialog(None))
        view_menu.addAction(places_act)

        timeline_act = QAction("⏳ Cronología del Universo", self)
        timeline_act.setShortcut("Ctrl+Alt+T")
        timeline_act.triggered.connect(self.open_timeline_dialog)
        view_menu.addAction(timeline_act)

        story_graph_act = QAction("🕸️ Cronograma Narrativo (Grafo)", self)
        story_graph_act.setShortcut("Ctrl+Alt+C")
        story_graph_act.setToolTip("Grafo causal de la historia con ramificaciones y eventos")
        story_graph_act.triggered.connect(self.open_story_graph_dialog)
        view_menu.addAction(story_graph_act)


        view_menu.addSeparator()
        self._appearance_act = QAction("🎨 Apariencia…", self)
        self._appearance_act.setShortcut("Ctrl+,")
        self._appearance_act.triggered.connect(self.open_editor_appearance_dialog)
        view_menu.addAction(self._appearance_act)

        # Submenú de Zoom
        zoom_menu = view_menu.addMenu("🔍 Zoom de Lectura")
        zoom_in_act = QAction("➕ Aumentar Zoom", self)
        zoom_in_act.setShortcut("Ctrl++")
        zoom_in_act.triggered.connect(self._on_zoom_in)
        zoom_menu.addAction(zoom_in_act)

        zoom_out_act = QAction("➖ Reducir Zoom", self)
        zoom_out_act.setShortcut("Ctrl+-")
        zoom_out_act.triggered.connect(self._on_zoom_out)
        zoom_menu.addAction(zoom_out_act)

        zoom_reset_act = QAction("↺ Restablecer Zoom (100%)", self)
        zoom_reset_act.setShortcut("Ctrl+0")
        zoom_reset_act.triggered.connect(self._on_zoom_reset)
        zoom_menu.addAction(zoom_reset_act)

        view_menu.addSeparator()
        self._zen_act = QAction("🧘 Modo Zen (Sin Distracciones)", self)
        self._zen_act.setShortcut("F11")
        self._zen_act.setCheckable(True)
        self._zen_act.triggered.connect(self.toggle_zen_mode)
        view_menu.addAction(self._zen_act)

        view_menu.addSeparator()
        self._theme_act = QAction("\U0001f319 Cambiar a Tema Claro", self)
        self._theme_act.setShortcut("Ctrl+Shift+T")
        self._theme_act.triggered.connect(self._toggle_theme)
        view_menu.addAction(self._theme_act)
        self._update_theme_action_label()

        # ── Sonido Aura ──────────────────────────────────────────────
        sound_menu = mb.addMenu("&Sonido")
        from core.sound_manager import AuraSoundEngine
        engine = AuraSoundEngine.instance()

        self._sound_toggle_act = QAction("🔊 Activar Sonido de Teclado", self)
        self._sound_toggle_act.setShortcut("Ctrl+M")
        self._sound_toggle_act.setCheckable(True)
        self._sound_toggle_act.setChecked(engine.enabled)
        self._sound_toggle_act.toggled.connect(self._set_sound_enabled)
        sound_menu.addAction(self._sound_toggle_act)

        sound_menu.addSeparator()

        # Selector de perfil acústico
        theme_grp = QActionGroup(self)
        theme_grp.setExclusive(True)

        self._snd_yt_act = QAction("🎵 Sonido 1 (Martilleo Mecánico)", self)
        self._snd_yt_act.setCheckable(True)
        self._snd_yt_act.setChecked(engine.get_theme() == "youtube")
        self._snd_yt_act.triggered.connect(lambda: self._set_sound_theme("youtube"))
        theme_grp.addAction(self._snd_yt_act)
        sound_menu.addAction(self._snd_yt_act)

        self._snd_electric_act = QAction("🎵 Sonido 2 (Electro-Táctil)", self)
        self._snd_electric_act.setCheckable(True)
        self._snd_electric_act.setChecked(engine.get_theme() == "electric")
        self._snd_electric_act.triggered.connect(lambda: self._set_sound_theme("electric"))
        theme_grp.addAction(self._snd_electric_act)
        sound_menu.addAction(self._snd_electric_act)

        self._snd_vintage_act = QAction("🎵 Sonido 3 (Vintage Clásico)", self)
        self._snd_vintage_act.setCheckable(True)
        self._snd_vintage_act.setChecked(engine.get_theme() == "vintage")
        self._snd_vintage_act.triggered.connect(lambda: self._set_sound_theme("vintage"))
        theme_grp.addAction(self._snd_vintage_act)
        sound_menu.addAction(self._snd_vintage_act)

        self._snd_thock_act = QAction("🎵 Sonido 4 (Thock ASMR / Punto Dulce)", self)
        self._snd_thock_act.setCheckable(True)
        self._snd_thock_act.setChecked(engine.get_theme() == "thock")
        self._snd_thock_act.triggered.connect(lambda: self._set_sound_theme("thock"))
        theme_grp.addAction(self._snd_thock_act)
        sound_menu.addAction(self._snd_thock_act)

        sound_menu.addSeparator()

        bell_act = QAction("🔔 Campanilla al pulsar Punto + Enter", self)
        bell_act.setCheckable(True)
        bell_act.setChecked(engine.bell_enabled)
        def _toggle_bell(checked):
            engine.bell_enabled = checked
        bell_act.triggered.connect(_toggle_bell)
        sound_menu.addAction(bell_act)

        # ── Herramientas ─────────────────────────────────────────────
        tools_menu = mb.addMenu("&Herramientas")

        compare_act = QAction("⚖️ Mesa de Cotejo (Comparar Capítulos)…", self)
        compare_act.setShortcut("Ctrl+Shift+C")
        compare_act.triggered.connect(self.open_chapter_comparator)
        tools_menu.addAction(compare_act)

        history_act = QAction("📜 Historial de Versiones y Diff…", self)
        history_act.setShortcut("Ctrl+H")
        history_act.triggered.connect(self.open_chapter_history)
        tools_menu.addAction(history_act)

        tools_menu.addSeparator()

        vocab_act = QAction("📖 Vocabulario y Conlang…", self)
        vocab_act.setShortcut("Ctrl+Shift+V")
        vocab_act.triggered.connect(self.open_vocabulary_dialog)
        tools_menu.addAction(vocab_act)

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

        # ── Ayuda ────────────────────────────────────────────────────
        help_menu = mb.addMenu("A&yuda")

        update_act = QAction("🔄 Buscar Actualizaciones…", self)
        update_act.triggered.connect(self.check_for_updates_manual)
        help_menu.addAction(update_act)

        help_menu.addSeparator()

        web_act = QAction("🌐 Sitio Web del Proyecto…", self)
        web_act.triggered.connect(self.open_project_website)
        help_menu.addAction(web_act)

        about_act = QAction("ℹ️ Acerca de Aura Writer…", self)
        about_act.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_act)

    def setup_toolbar(self):
        """Construye la barra de herramientas principal."""
        self._main_toolbar = QToolBar("Principal")
        self._main_toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(self._main_toolbar)

        try:
            from core.theme_manager import ThemeManager
            is_dark = ThemeManager.is_dark()
            _ic = "#aeaeb2" if is_dark else "#4a4a5a"
            _accent = "#ffd60a" if is_dark else "#d97706"

            self._act_save = self._main_toolbar.addAction(qta.icon("fa5s.save", color="#30d158" if is_dark else "#16a34a"), "Guardar", self.save_project)
            self._main_toolbar.addSeparator()

            self._bold_act.setIcon(qta.icon("fa5s.bold", color=_ic))
            self._bold_act.setText("Negrita (Ctrl+B)")
            self._main_toolbar.addAction(self._bold_act)

            self._italic_act.setIcon(qta.icon("fa5s.italic", color=_ic))
            self._italic_act.setText("Cursiva (Ctrl+I)")
            self._main_toolbar.addAction(self._italic_act)

            self._underline_act.setIcon(qta.icon("fa5s.underline", color=_ic))
            self._underline_act.setText("Subrayado (Ctrl+U)")
            self._main_toolbar.addAction(self._underline_act)

            self._strike_act.setIcon(qta.icon("fa5s.strikethrough", color=_ic))
            self._strike_act.setText("Tachado (Ctrl+K)")
            self._main_toolbar.addAction(self._strike_act)

            self._clean_act.setIcon(qta.icon("fa5s.eraser", color=_ic))
            self._clean_act.setText("Limpiar Formato (Ctrl+\\)")
            self._main_toolbar.addAction(self._clean_act)

            self._main_toolbar.addSeparator()
            self._act_left = self._main_toolbar.addAction(qta.icon("fa5s.align-left", color=_ic), "Izq", self.editor.align_left)
            self._act_center = self._main_toolbar.addAction(qta.icon("fa5s.align-center", color=_ic), "Centrar", self.editor.align_center)
            self._act_right = self._main_toolbar.addAction(qta.icon("fa5s.align-right", color=_ic), "Der", self.editor.align_right)
            self._act_justify = self._main_toolbar.addAction(qta.icon("fa5s.align-justify", color=_ic), "Justificar", self.editor.align_justify)

            self._main_toolbar.addSeparator()
            self._act_dot = self._main_toolbar.addAction(qta.icon("fa5s.circle", color=_accent), "Punto Medio · (Ctrl+.)", self.editor.insert_middle_dot)
            self._act_dash = self._main_toolbar.addAction(qta.icon("fa5s.minus", color=_accent), "Raya — (Ctrl+- o escribir --)", self.editor.insert_em_dash)
            self._act_sep = self._main_toolbar.addAction(qta.icon("fa5s.asterisk", color=_accent), "Separador * * *", self.editor.insert_scene_separator)
            self._act_pb = self._main_toolbar.addAction(qta.icon("fa5s.cut", color="#ff453a" if is_dark else "#dc2626"), "Salto de Pág", self.editor.insert_page_break)
            self._act_blank = self._main_toolbar.addAction(qta.icon("fa5s.file-alt", color=_ic), "Pág en Blanco", self.editor.insert_blank_page)
            self._act_img = self._main_toolbar.addAction(qta.icon("fa5s.image", color="#32ade6" if is_dark else "#0284c7"), "Imagen", self.insert_media)

            self._main_toolbar.addSeparator()
            self._act_search = self._main_toolbar.addAction(qta.icon("fa5s.search", color=_ic), "Buscador Global", self.open_search)
            self._act_lock = self._main_toolbar.addAction(qta.icon("fa5s.lock", color="#ff9f0a" if is_dark else "#ea580c"), "Bloqueo Rápido", self.quick_lock)

            self._main_toolbar.addSeparator()
            self._act_map = self._main_toolbar.addAction(qta.icon("fa5s.globe", color="#bf5af2" if is_dark else "#9333ea"), "Mapa Mental", self.open_universe_map)
            self._act_graph = self._main_toolbar.addAction(qta.icon("fa5s.project-diagram", color="#5e5ce6" if is_dark else "#4f46e5"), "Relaciones", self.open_relation_graph)
            self._act_place_graph = self._main_toolbar.addAction(qta.icon("fa5s.map-marked-alt", color="#ffd60a" if is_dark else "#d97706"), "Atlas de Lugares", self.open_place_graph_dialog)
            self._act_story_graph = self._main_toolbar.addAction(qta.icon("fa5s.stream", color="#ff9f0a" if is_dark else "#ea580c"), "Cronograma Narrativo", self.open_story_graph_dialog)
            self._main_toolbar.addSeparator()
            self._act_export = self._main_toolbar.addAction(qta.icon("fa5s.file-export", color="#30d158" if is_dark else "#16a34a"), "Exportar", self.open_exporter)
            self._act_trash = self._main_toolbar.addAction(qta.icon("fa5s.trash-alt", color="#ff453a" if is_dark else "#dc2626"), "Papelera", self.open_trash_dialog)

            self._main_toolbar.addSeparator()
            self._theme_btn_action = self._main_toolbar.addAction(
                qta.icon("fa5s.sun" if is_dark else "fa5s.moon", color="#ffd60a" if is_dark else "#2563eb"),
                "Cambiar Tema", self._toggle_theme
            )
            self._appearance_act.setIcon(qta.icon("fa5s.paint-brush", color="#bf5af2" if is_dark else "#9333ea"))
            self._main_toolbar.addAction(self._appearance_act)
            self._update_theme_action_label()

            # ── Evitar que los botones de la toolbar roben el foco del editor ──
            # Sin esto, al actualizar setChecked() en las acciones de formato el
            # QToolButton puede tomar el foco visual y "absorber" el siguiente Enter.
            from PyQt6.QtWidgets import QToolButton
            from PyQt6.QtCore import Qt as _Qt
            self._main_toolbar.setFocusPolicy(_Qt.FocusPolicy.NoFocus)
            for _btn in self._main_toolbar.findChildren(QToolButton):
                _btn.setFocusPolicy(_Qt.FocusPolicy.NoFocus)
        except Exception:
            self._main_toolbar.addAction("Guardar", self.save_project)
            self._main_toolbar.addSeparator()
            self._main_toolbar.addAction(self._bold_act)
            self._main_toolbar.addAction(self._italic_act)
            self._main_toolbar.addAction(self._underline_act)
            self._main_toolbar.addAction(self._strike_act)
            self._main_toolbar.addAction(self._clean_act)
            self._main_toolbar.addSeparator()
            self._main_toolbar.addAction("Izq", self.editor.align_left)
            self._main_toolbar.addAction("Cen", self.editor.align_center)
            self._main_toolbar.addAction("Der", self.editor.align_right)
            self._main_toolbar.addAction("Jus", self.editor.align_justify)
            self._main_toolbar.addSeparator()
            self._main_toolbar.addAction("·", self.editor.insert_middle_dot)
            self._main_toolbar.addAction("* * *", self.editor.insert_scene_separator)
            self._main_toolbar.addAction("Salto Pág", self.editor.insert_page_break)
            self._main_toolbar.addAction("Pág Blanco", self.editor.insert_blank_page)
            self._main_toolbar.addSeparator()
            self._main_toolbar.addAction("Img", self.insert_media)
            self._main_toolbar.addSeparator()
            self._main_toolbar.addAction("Mapa", self.open_universe_map)
            self._main_toolbar.addAction("Nodos", self.open_relation_graph)
            self._main_toolbar.addSeparator()
            self._main_toolbar.addAction("Exportar", self.open_exporter)

    def _refresh_toolbar_icons(self):
        """Actualiza los iconos de la barra de herramientas al cambiar de tema."""
        try:
            from core.theme_manager import ThemeManager
            is_dark = ThemeManager.is_dark()
            _ic = "#aeaeb2" if is_dark else "#4a4a5a"
            _accent = "#ffd60a" if is_dark else "#d97706"

            if hasattr(self, "_bold_act"): self._bold_act.setIcon(qta.icon("fa5s.bold", color=_ic))
            if hasattr(self, "_italic_act"): self._italic_act.setIcon(qta.icon("fa5s.italic", color=_ic))
            if hasattr(self, "_underline_act"): self._underline_act.setIcon(qta.icon("fa5s.underline", color=_ic))
            if hasattr(self, "_strike_act"): self._strike_act.setIcon(qta.icon("fa5s.strikethrough", color=_ic))
            if hasattr(self, "_clean_act"): self._clean_act.setIcon(qta.icon("fa5s.eraser", color=_ic))

            if hasattr(self, "_act_left"): self._act_left.setIcon(qta.icon("fa5s.align-left", color=_ic))
            if hasattr(self, "_act_center"): self._act_center.setIcon(qta.icon("fa5s.align-center", color=_ic))
            if hasattr(self, "_act_right"): self._act_right.setIcon(qta.icon("fa5s.align-right", color=_ic))
            if hasattr(self, "_act_justify"): self._act_justify.setIcon(qta.icon("fa5s.align-justify", color=_ic))

            if hasattr(self, "_act_dot"): self._act_dot.setIcon(qta.icon("fa5s.circle", color=_accent))
            if hasattr(self, "_act_dash"): self._act_dash.setIcon(qta.icon("fa5s.minus", color=_accent))
            if hasattr(self, "_act_sep"): self._act_sep.setIcon(qta.icon("fa5s.asterisk", color=_accent))
            if hasattr(self, "_act_pb"): self._act_pb.setIcon(qta.icon("fa5s.cut", color="#ff453a" if is_dark else "#dc2626"))
            if hasattr(self, "_act_blank"): self._act_blank.setIcon(qta.icon("fa5s.file-alt", color=_ic))
            if hasattr(self, "_act_img"): self._act_img.setIcon(qta.icon("fa5s.image", color="#32ade6" if is_dark else "#0284c7"))

            if hasattr(self, "_act_search"): self._act_search.setIcon(qta.icon("fa5s.search", color=_ic))
            if hasattr(self, "_act_lock"): self._act_lock.setIcon(qta.icon("fa5s.lock", color="#ff9f0a" if is_dark else "#ea580c"))
            if hasattr(self, "_act_map"): self._act_map.setIcon(qta.icon("fa5s.globe", color="#bf5af2" if is_dark else "#9333ea"))
            if hasattr(self, "_act_graph"): self._act_graph.setIcon(qta.icon("fa5s.project-diagram", color="#5e5ce6" if is_dark else "#4f46e5"))
            if hasattr(self, "_act_export"): self._act_export.setIcon(qta.icon("fa5s.file-export", color="#30d158" if is_dark else "#16a34a"))
            if hasattr(self, "_act_save"): self._act_save.setIcon(qta.icon("fa5s.save", color="#30d158" if is_dark else "#16a34a"))
        except Exception:
            pass

    def _set_sound_enabled(self, enabled: bool):
        """Activa o desactiva el sonido mecánico con sincronización exacta."""
        try:
            from core.sound_manager import AuraSoundEngine
            engine = AuraSoundEngine.instance()
            engine.enabled = enabled
            status = "Sonido de Teclado: ACTIVADO" if enabled else "Sonido de Teclado: SILENCIADO"
            self.statusBar().showMessage(status, 2500)
        except Exception:
            pass

    def _set_sound_theme(self, theme_name: str):
        """Cambia el perfil acústico del teclado ('youtube', 'electric' o 'vintage')."""
        try:
            from core.sound_manager import AuraSoundEngine
            engine = AuraSoundEngine.instance()
            engine.set_theme(theme_name)
            labels = {
                "youtube": "Sonido 1 (Martilleo Mecánico)",
                "electric": "Sonido 2 (Electro-Táctil)",
                "vintage": "Sonido 3 (Vintage Clásico)",
                "thock": "Sonido 4 (Thock ASMR / Punto Dulce)"
            }
            name_str = labels.get(theme_name, "Personalizado")
            self.statusBar().showMessage(f"Perfil de Sonido: {name_str}", 3000)
        except Exception:
            pass

    def _update_format_actions(self, fmt: QTextCharFormat = None):
        """Sincroniza el estado visual de los botones de formato con el formato bajo el cursor."""
        if fmt is None or not isinstance(fmt, QTextCharFormat):
            fmt = self.editor.currentCharFormat()
        if hasattr(self, '_bold_act'):
            weight = fmt.fontWeight()
            self._bold_act.blockSignals(True)
            self._bold_act.setChecked(weight >= 600 or self.editor.fontWeight() >= 600)
            self._bold_act.blockSignals(False)
        if hasattr(self, '_italic_act'):
            self._italic_act.blockSignals(True)
            self._italic_act.setChecked(fmt.fontItalic() or self.editor.fontItalic())
            self._italic_act.blockSignals(False)
        if hasattr(self, '_underline_act'):
            self._underline_act.blockSignals(True)
            self._underline_act.setChecked(fmt.fontUnderline() or self.editor.fontUnderline())
            self._underline_act.blockSignals(False)
        if hasattr(self, '_strike_act'):
            self._strike_act.blockSignals(True)
            self._strike_act.setChecked(fmt.fontStrikeOut())
            self._strike_act.blockSignals(False)
