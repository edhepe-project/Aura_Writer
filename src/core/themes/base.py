"""
base.py — Template único de stylesheet Qt para Aura Writer.

ARQUITECTURA DE TOKENS:
  - Este archivo contiene UN SOLO template con marcadores {token}.
  - Cada tema (dark, light, sepia, ...) provee únicamente un diccionario
    de colores (PALETTE) con los valores para esos tokens.
  - Para crear un tema nuevo: copiar cualquier paleta y cambiar colores.
  - NINGÚN color está hardcodeado aquí; todo es un token semántico.

TOKENS DISPONIBLES:
  Fondos:
    bg_app         — fondo principal (ventanas, diálogos, dock)
    bg_surface     — superficies elevadas (árbol, listas, paneles)
    bg_input       — controles de entrada (linedit, combobox, spinbox)
    bg_button      — botones en reposo
    bg_hover       — fondo al hacer hover
    bg_selected    — fondo de ítem seleccionado
    bg_pressed     — fondo al presionar
    bg_disabled    — fondo deshabilitado
    bg_muted       — fondo sutil (scrollarea, stackedwidget)
    bg_overlay     — tooltips y overlays
    bg_menu        — fondo del menú desplegable
    bg_tab_active  — pestaña activa
    bg_tab_idle    — pestaña inactiva

  Textos:
    fg_primary     — texto principal
    fg_secondary   — texto secundario (toolbar, menubar)
    fg_muted       — texto silenciado (tabs inactivos, headers)
    fg_disabled    — texto deshabilitado
    fg_selected    — texto en ítem seleccionado
    fg_accent      — texto de acento (tab activo, botón chequeado)

  Bordes:
    border_default — bordes estándar (inputs, botones, contenedores)
    border_subtle  — separadores sutiles (menubar, toolbar)
    border_strong  — bordes de separación visible (splitter, groupbox)
    border_focus   — anillo de foco (input enfocado)
    border_accent  — borde de acento (botón/tab activo)

  Acento:
    accent         — color de acento primario
    accent_hover   — acento en hover

  Scrollbar:
    scrollbar_handle       — handle de scrollbar
    scrollbar_handle_hover — handle de scrollbar en hover

  Colores semánticos de estado/rol (para íconos, badges, indicadores):
    blue           — azul informativo / acento secundario
    red            — rojo de error / peligro / destrucción
    green          — verde de éxito / confirmación
    purple         — púrpura / misterio / magia
    indigo         — índigo / violeta
    amber          — ámbar / advertencia
    fg_placeholder — texto de placeholder / hint

  Componentes específicos:
    header_bg      — fondo de encabezados de tabla/árbol
    header_fg      — texto de encabezados
    menu_hover     — hover en items de menú
    menu_disabled  — texto deshabilitado en menú
    menu_sep       — separador de menú
    groupbox_fg    — color de texto del título del groupbox
    graphics_bg    — fondo de QGraphicsView
    frame_sep      — color de separadores QFrame (líneas H/V)
    selection_bg   — fondo de texto seleccionado en editors
"""


BASE_STYLESHEET = """
    /* ─────────────────────────────────────────────────────────────
       BASE — tipografía global (solo familia y tamaño, sin colores)
       ───────────────────────────────────────────────────────────── */
    * {{
        font-family: "Segoe UI", system-ui, sans-serif;
        font-size: 13px;
    }}

    /* ─────────────────────────────────────────────────────────────
       VENTANAS PRINCIPALES
       ───────────────────────────────────────────────────────────── */
    QMainWindow, QDialog, QDockWidget {{
        background-color: {bg_app};
        color: {fg_primary};
    }}
    QWidget {{
        color: {fg_primary};
    }}
    QDockWidget::title {{
        background-color: {bg_hover};
        color: {fg_primary};
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
    }}

    /* ─────────────────────────────────────────────────────────────
       BARRA DE MENÚ
       ───────────────────────────────────────────────────────────── */
    QMenuBar {{
        background-color: {bg_app};
        color: {fg_secondary};
        border-bottom: 1px solid {border_subtle};
        padding: 2px 0;
    }}
    QMenuBar::item:selected {{
        background: {bg_hover};
        border-radius: 4px;
    }}
    QMenu {{
        background: {bg_menu};
        color: {fg_primary};
        border: 1px solid {border_default};
        border-radius: 8px;
        padding: 4px;
    }}
    QMenu::item {{ padding: 6px 20px; border-radius: 5px; }}
    QMenu::item:selected {{ background: {menu_hover}; }}
    QMenu::item:disabled {{ color: {menu_disabled}; }}
    QMenu::separator {{ height: 1px; background: {menu_sep}; margin: 3px 0; }}

    /* ─────────────────────────────────────────────────────────────
       TOOLBAR
       ───────────────────────────────────────────────────────────── */
    QToolBar {{
        background-color: {bg_app};
        border-bottom: 1px solid {border_subtle};
        spacing: 4px;
        padding: 4px 8px;
    }}
    QToolBar QToolButton {{
        background: transparent;
        color: {fg_secondary};
        border: 1px solid transparent;
        border-radius: 6px;
        padding: 5px 9px;
    }}
    QToolBar QToolButton:hover  {{
        background: {bg_hover};
        color: {fg_primary};
    }}
    QToolBar QToolButton:pressed {{ background: {bg_pressed}; }}
    QToolBar QToolButton:checked {{
        background: {bg_hover};
        color: {fg_accent};
        border: 1px solid {border_accent};
    }}
    QToolBar QToolButton:checked:hover {{
        background: {bg_pressed};
        border-color: {accent_hover};
    }}

    /* ─────────────────────────────────────────────────────────────
       BARRA DE ESTADO
       ───────────────────────────────────────────────────────────── */
    QStatusBar {{
        background: {bg_app};
        color: {fg_muted};
        border-top: 1px solid {border_subtle};
        font-size: 11px;
    }}

    /* ─────────────────────────────────────────────────────────────
       BOTONES
       ───────────────────────────────────────────────────────────── */
    QPushButton {{
        background: {bg_button};
        color: {fg_primary};
        border: 1px solid {border_default};
        border-radius: 8px;
        padding: 6px 16px;
        font-size: 13px;
        font-weight: 500;
    }}
    QPushButton:hover   {{ background: {bg_hover};     border-color: {border_strong}; }}
    QPushButton:pressed {{ background: {bg_pressed}; }}
    QPushButton:disabled {{
        color: {fg_disabled};
        background: {bg_disabled};
        border-color: transparent;
    }}
    QDialogButtonBox QPushButton {{ min-width: 80px; }}

    /* ─────────────────────────────────────────────────────────────
       INPUTS DE TEXTO
       ───────────────────────────────────────────────────────────── */
    QLineEdit, QTextEdit, QPlainTextEdit, QTextBrowser {{
        background: {bg_input};
        color: {fg_primary};
        border: 1px solid {border_default};
        border-radius: 8px;
        padding: 6px 10px;
        selection-background-color: {selection_bg};
        selection-color: {fg_primary};
    }}
    QLineEdit:focus,
    QTextEdit:focus,
    QPlainTextEdit:focus,
    QTextBrowser:focus {{
        border: 1px solid {border_focus};
    }}

    /* Lienzo principal de escritura (AuraEditor): mantiene sus márgenes, padding y tamaño de fuente propios */
    AuraEditor {{
        border: none;
        border-radius: 6px;
        padding: 12px;
        font-size: 12pt;
    }}
    AuraEditor:focus {{
        border: none;
    }}

    /* ─────────────────────────────────────────────────────────────
       COMBOBOX
       ───────────────────────────────────────────────────────────── */
    QComboBox {{
        background: {bg_input};
        color: {fg_primary};
        border: 1px solid {border_default};
        border-radius: 8px;
        padding: 5px 10px;
    }}
    QComboBox::drop-down {{ border: none; width: 20px; }}
    QComboBox QAbstractItemView {{
        background: {bg_input};
        color: {fg_primary};
        border: 1px solid {border_default};
        selection-background-color: {bg_selected};
        selection-color: {fg_selected};
    }}

    /* ─────────────────────────────────────────────────────────────
       SPINBOX
       ───────────────────────────────────────────────────────────── */
    QSpinBox {{
        background: {bg_input};
        color: {fg_primary};
        border: 1px solid {border_default};
        border-radius: 8px;
        padding: 4px 8px;
    }}
    QSpinBox::up-button, QSpinBox::down-button {{ width: 0; }}

    /* ─────────────────────────────────────────────────────────────
       SPLITTER
       ───────────────────────────────────────────────────────────── */
    QSplitter::handle {{ background: {border_strong}; }}

    /* ─────────────────────────────────────────────────────────────
       GROUPBOX
       ───────────────────────────────────────────────────────────── */
    QGroupBox {{
        color: {groupbox_fg};
        border: 1px solid {border_strong};
        border-radius: 8px;
        margin-top: 10px;
        padding: 12px 10px 10px 10px;
        font-weight: bold;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
    }}

    /* ─────────────────────────────────────────────────────────────
       PESTAÑAS
       ───────────────────────────────────────────────────────────── */
    QTabWidget::pane {{
        border: 1px solid {border_default};
        background: {bg_tab_active};
        border-radius: 6px;
    }}
    QTabBar::tab {{
        background: {bg_tab_idle};
        color: {fg_muted};
        border: 1px solid {border_default};
        border-bottom: none;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        padding: 6px 14px;
        margin-right: 2px;
        font-weight: 500;
    }}
    QTabBar::tab:selected {{
        background: {bg_tab_active};
        color: {fg_accent};
        font-weight: 600;
        border-color: {border_default};
        border-bottom: 1px solid {bg_tab_active};
    }}
    QTabBar::tab:hover:!selected {{ background: {bg_hover}; }}

    /* ─────────────────────────────────────────────────────────────
       SCROLL AREA
       ───────────────────────────────────────────────────────────── */
    QScrollArea, QStackedWidget {{
        background-color: {bg_muted};
        border: none;
    }}
    QScrollArea > QWidget > QWidget {{ background: transparent; }}
    QScrollArea > .QWidget           {{ background: transparent; }}

    /* ─────────────────────────────────────────────────────────────
       ÁRBOL (QTreeView / QTreeWidget)
       ───────────────────────────────────────────────────────────── */
    QTreeWidget, QTreeView {{
        background: {bg_surface};
        color: {fg_primary};
        border: none;
        outline: none;
    }}
    QTreeWidget::item, QTreeView::item {{ padding: 4px 6px; }}
    QTreeWidget::item:hover, QTreeView::item:hover {{ background: {bg_hover}; }}
    QTreeWidget::item:selected, QTreeView::item:selected {{
        background: {bg_selected};
        color: {fg_selected};
    }}

    /* ─────────────────────────────────────────────────────────────
       LISTAS (QListWidget / QListView)
       ───────────────────────────────────────────────────────────── */
    QListWidget, QListView {{
        background: {bg_surface};
        color: {fg_primary};
        border: none;
        outline: none;
    }}
    QListWidget::item, QListView::item {{ padding: 5px 8px; border-radius: 5px; }}
    QListWidget::item:hover, QListView::item:hover {{ background: {bg_hover}; }}
    QListWidget::item:selected, QListView::item:selected {{
        background: {bg_selected};
        color: {fg_selected};
    }}

    /* ─────────────────────────────────────────────────────────────
       TABLA
       ───────────────────────────────────────────────────────────── */
    QTableWidget {{
        background: {bg_surface};
        color: {fg_primary};
        border: none;
    }}

    /* ─────────────────────────────────────────────────────────────
       ENCABEZADOS (QHeaderView)
       ───────────────────────────────────────────────────────────── */
    QHeaderView::section {{
        background: {header_bg};
        color: {header_fg};
        font-weight: 600;
        font-size: 11px;
        border: none;
        border-bottom: 1px solid {border_default};
        padding: 5px;
    }}

    /* ─────────────────────────────────────────────────────────────
       GRAPHICS VIEW
       ───────────────────────────────────────────────────────────── */
    QGraphicsView {{ background-color: {graphics_bg}; border: none; }}

    /* ─────────────────────────────────────────────────────────────
       LABEL / FRAME SEPARADORES
       ───────────────────────────────────────────────────────────── */
    QLabel {{ color: {fg_primary}; background: transparent; }}
    QFrame[frameShape="4"], QFrame[frameShape="5"] {{ color: {frame_sep}; }}

    /* ─────────────────────────────────────────────────────────────
       TOOLTIP
       ───────────────────────────────────────────────────────────── */
    QToolTip {{
        background: {bg_overlay};
        color: {fg_primary};
        border: 1px solid {border_default};
        border-radius: 6px;
        padding: 4px 8px;
    }}

    /* ─────────────────────────────────────────────────────────────
       SCROLLBARS
       ───────────────────────────────────────────────────────────── */
    QScrollBar:vertical   {{ background: transparent; width: 7px; margin: 2px 1px; }}
    QScrollBar::handle:vertical {{
        background: {scrollbar_handle};
        border-radius: 3px;
        min-height: 28px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {scrollbar_handle_hover}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}

    QScrollBar:horizontal {{ background: transparent; height: 7px; margin: 1px 2px; }}
    QScrollBar::handle:horizontal {{
        background: {scrollbar_handle};
        border-radius: 3px;
        min-width: 28px;
    }}
    QScrollBar::handle:horizontal:hover {{ background: {scrollbar_handle_hover}; }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: none; }}

    /* ─────────────────────────────────────────────────────────────
       CHECKBOX
       ───────────────────────────────────────────────────────────── */
    QCheckBox {{ color: {fg_secondary}; spacing: 6px; }}
    QCheckBox::indicator {{
        width: 15px; height: 15px;
        border: 1px solid {border_default};
        border-radius: 4px;
        background: {bg_input};
    }}
    QCheckBox::indicator:hover {{
        border-color: {border_strong};
        background: {bg_hover};
    }}
    QCheckBox::indicator:checked {{
        background: {accent};
        border-color: {accent};
        image: none;
    }}
    QCheckBox::indicator:checked:hover {{
        background: {accent_hover};
        border-color: {accent_hover};
    }}

    /* ─────────────────────────────────────────────────────────────
       RADIOBUTTON
       ───────────────────────────────────────────────────────────── */
    QRadioButton {{ color: {fg_primary}; spacing: 6px; }}
    QRadioButton::indicator {{
        width: 15px; height: 15px;
        border: 1px solid {border_default};
        border-radius: 8px;
        background: {bg_input};
    }}
    QRadioButton::indicator:hover {{ border-color: {border_strong}; }}
    QRadioButton::indicator:checked {{
        background: {accent};
        border-color: {accent};
    }}
"""


def build_stylesheet(palette: dict) -> str:
    """
    Genera el stylesheet final interpolando la paleta de colores en el template.

    Args:
        palette: Diccionario con todos los tokens de color definidos en TOKENS.
                 Ver las constantes DARK_PALETTE, LIGHT_PALETTE, SEPIA_PALETTE.

    Returns:
        Hoja de estilo Qt lista para usar con app.setStyleSheet().

    Raises:
        KeyError: Si falta algún token requerido en la paleta.
    """
    try:
        return BASE_STYLESHEET.format(**palette)
    except KeyError as e:
        raise KeyError(
            f"Token de color faltante en la paleta del tema: {e}. "
            f"Revisa que la paleta incluya todos los tokens definidos en base.py."
        ) from e
