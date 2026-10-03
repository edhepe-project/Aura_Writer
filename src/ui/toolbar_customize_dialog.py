"""
toolbar_customize_dialog.py
───────────────────────────
Diálogo para personalizar los botones visibles en la barra de herramientas
principal de Aura Writer.  Las preferencias se persisten en QSettings.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QCheckBox, QFrame,
)
from core.theme_manager import ThemeManager


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de persistencia
# ─────────────────────────────────────────────────────────────────────────────
_SETTINGS_GROUP = "toolbar_customize"


def save_toolbar_visibility(action_key: str, visible: bool) -> None:
    s = QSettings("AuraWriter", "Aura")
    s.beginGroup(_SETTINGS_GROUP)
    s.setValue(action_key, visible)
    s.endGroup()


def load_toolbar_visibility(action_key: str, default: bool = True) -> bool:
    s = QSettings("AuraWriter", "Aura")
    s.beginGroup(_SETTINGS_GROUP)
    val = s.value(action_key, default, type=bool)
    s.endGroup()
    return val


def apply_saved_visibility(actions_map: dict) -> None:
    """Lee QSettings y aplica la visibilidad guardada a cada accion."""
    for key, action in actions_map.items():
        if action is not None:
            action.setVisible(load_toolbar_visibility(key, True))


# ─────────────────────────────────────────────────────────────────────────────
# Dialogo
# ─────────────────────────────────────────────────────────────────────────────
class ToolbarCustomizeDialog(QDialog):
    """
    Dialogo modal con checkboxes agrupados por seccion para mostrar/ocultar
    cada boton de la barra de herramientas principal.
    Los cambios se aplican en tiempo real y se persisten en QSettings.
    """

    def __init__(self, actions_map: dict, parent=None):
        super().__init__(parent)
        self._actions_map = actions_map
        self._checkboxes: dict[str, QCheckBox] = {}

        self.setWindowTitle("Personalizar barra de herramientas")
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.setMinimumWidth(400)
        self.setMinimumHeight(480)
        self.setModal(True)
        self._build_ui()
        self._apply_style()

    # ── Construccion de la UI ─────────────────────────────────────────────────
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Encabezado
        header = QWidget()
        header.setObjectName("tbcd_header")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 16, 20, 14)
        title_lbl = QLabel("Personalizar barra de herramientas")
        title_lbl.setObjectName("tbcd_title")
        sub_lbl = QLabel("Activa o desactiva cada boton de acceso rapido.")
        sub_lbl.setObjectName("tbcd_subtitle")
        vl = QVBoxLayout()
        vl.setSpacing(3)
        vl.addWidget(title_lbl)
        vl.addWidget(sub_lbl)
        hl.addLayout(vl)
        root.addWidget(header)

        # Separador
        self._add_sep(root)

        # Area scrollable con grupos
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        content.setObjectName("tbcd_content")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 16, 20, 16)
        cl.setSpacing(2)

        for group_title, items in self._build_groups():
            grp_lbl = QLabel(group_title)
            grp_lbl.setObjectName("tbcd_group")
            cl.addWidget(grp_lbl)

            for key, label in items:
                action = self._actions_map.get(key)
                cb = QCheckBox(label)
                cb.setObjectName("tbcd_cb")
                cb.setChecked(load_toolbar_visibility(key, True))
                if action is None:
                    cb.setEnabled(False)
                else:
                    cb.toggled.connect(
                        lambda checked, k=key, a=action: self._on_toggle(k, a, checked)
                    )
                self._checkboxes[key] = cb
                cl.addWidget(cb)

            cl.addSpacing(10)

        cl.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll)

        # Separador inferior
        self._add_sep(root)

        # Barra de botones
        btn_bar = QWidget()
        btn_bar.setObjectName("tbcd_btnbar")
        bl = QHBoxLayout(btn_bar)
        bl.setContentsMargins(16, 10, 16, 10)
        bl.setSpacing(8)

        btn_all = QPushButton("Mostrar todos")
        btn_all.setObjectName("tbcd_btn_secondary")
        btn_all.clicked.connect(self._show_all)

        btn_none = QPushButton("Ocultar todos")
        btn_none.setObjectName("tbcd_btn_secondary")
        btn_none.clicked.connect(self._hide_all)

        btn_close = QPushButton("Cerrar")
        btn_close.setObjectName("tbcd_btn_primary")
        btn_close.setDefault(True)
        btn_close.clicked.connect(self.accept)

        bl.addWidget(btn_all)
        bl.addWidget(btn_none)
        bl.addStretch()
        bl.addWidget(btn_close)
        root.addWidget(btn_bar)

    @staticmethod
    def _add_sep(layout: QVBoxLayout) -> None:
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("tbcd_sep")
        layout.addWidget(sep)

    def _build_groups(self) -> list:
        return [
            ("ARCHIVO", [
                ("act_save", "Guardar"),
            ]),
            ("FORMATO DE TEXTO", [
                ("act_bold",      "Negrita  (Ctrl+B)"),
                ("act_italic",    "Cursiva  (Ctrl+I)"),
                ("act_underline", "Subrayado  (Ctrl+U)"),
                ("act_strike",    "Tachado  (Ctrl+K)"),
                ("act_clean",     "Limpiar formato  (Ctrl+\\)"),
            ]),
            ("ALINEACION", [
                ("act_left",    "Alinear a la izquierda"),
                ("act_center",  "Centrar"),
                ("act_right",   "Alinear a la derecha"),
                ("act_justify", "Justificar"),
            ]),
            ("SIMBOLOS Y ESTRUCTURA", [
                ("act_dot",   "Punto medio  ·"),
                ("act_dash",  "Raya de dialogo  \u2014"),
                ("act_sep",   "Separador de escena  * * *"),
                ("act_pb",    "Salto de pagina"),
                ("act_blank", "Pagina en blanco"),
                ("act_img",   "Insertar imagen"),
            ]),
            ("HERRAMIENTAS", [
                ("act_search", "Buscador global"),
                ("act_lock",   "Bloqueo rapido"),
            ]),
            ("UNIVERSO NARRATIVO", [
                ("act_map",         "Mapa mental del universo"),
                ("act_graph",       "Relaciones de personajes"),
                ("act_place_graph", "Atlas de lugares"),
                ("act_story_graph", "Cronograma narrativo"),
            ]),
            ("EXPORTAR Y PAPELERA", [
                ("act_export", "Exportar"),
                ("act_trash",  "Papelera"),
            ]),
            ("APARIENCIA", [
                ("act_appearance_tb", "Apariencia del editor"),
            ]),
        ]

    # ── Callbacks ─────────────────────────────────────────────────────────────
    def _on_toggle(self, key: str, action, checked: bool) -> None:
        action.setVisible(checked)
        save_toolbar_visibility(key, checked)

    def _show_all(self) -> None:
        for cb in self._checkboxes.values():
            cb.setChecked(True)

    def _hide_all(self) -> None:
        for cb in self._checkboxes.values():
            cb.setChecked(False)

    # ── Estilos ────────────────────────────────────────────────────────────────
    def _apply_style(self) -> None:
        c = ThemeManager.palette()
        bg_dialog = c["bg_surface"]
        bg_header = c["bg_app"]
        fg_title = c["fg_primary"]
        fg_subtitle = c["fg_muted"]
        border_sep = c["border_default"]
        
        grp_fg = c["fg_muted"]
        cb_fg = c["fg_primary"]
        cb_hover_bg = c["bg_hover"]
        cb_disabled = c["fg_disabled"]
        
        chk_indicator_bg = c["bg_input"]
        chk_indicator_border = c["border_default"]
        chk_checked_bg = c["accent"]
        chk_hover_border = c["accent"]
        
        btnbar_bg = c["bg_app"]
        btn_pri_bg = c["accent"]
        btn_pri_fg = c["fg_selected"]
        btn_pri_hover = c["accent_hover"]
        
        btn_sec_bg = c["bg_button"]
        btn_sec_fg = c["fg_primary"]
        btn_sec_border = c["border_default"]
        btn_sec_hover = c["bg_hover"]
        
        scroll_handle = c["scrollbar_handle"]

        self.setStyleSheet(f"""
            QDialog {{ background: {bg_dialog}; }}

            #tbcd_header {{ background: {bg_header}; }}

            #tbcd_title {{
                font-size: 15px;
                font-weight: 700;
                color: {fg_title};
                font-family: 'Segoe UI', sans-serif;
            }}
            #tbcd_subtitle {{
                font-size: 11px;
                color: {fg_subtitle};
                font-family: 'Segoe UI', sans-serif;
            }}

            #tbcd_sep {{
                background: {border_sep};
                min-height: 1px;
                max-height: 1px;
                border: none;
            }}

            #tbcd_content {{ background: {bg_dialog}; }}

            QScrollArea {{ background: {bg_dialog}; border: none; }}
            QScrollBar:vertical {{
                background: {bg_dialog}; width: 6px; border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {scroll_handle}; border-radius: 3px; min-height: 24px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}

            #tbcd_group {{
                font-size: 10px;
                font-weight: 700;
                color: {grp_fg};
                letter-spacing: 0.08em;
                font-family: 'Segoe UI', sans-serif;
                padding-top: 10px;
                padding-bottom: 2px;
            }}

            #tbcd_cb {{
                font-size: 13px;
                color: {cb_fg};
                font-family: 'Segoe UI', sans-serif;
                padding: 5px 10px;
                border-radius: 6px;
                spacing: 8px;
            }}
            #tbcd_cb:hover {{ background: {cb_hover_bg}; }}
            #tbcd_cb:disabled {{ color: {cb_disabled}; }}

            #tbcd_cb::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1.5px solid {chk_indicator_border};
                background: {chk_indicator_bg};
            }}
            #tbcd_cb::indicator:checked {{
                background: {chk_checked_bg};
                border-color: {chk_checked_bg};
                image: none;
            }}
            #tbcd_cb::indicator:unchecked:hover {{ border-color: {chk_hover_border}; }}

            #tbcd_btnbar {{ background: {btnbar_bg}; }}

            #tbcd_btn_primary {{
                background: {btn_pri_bg};
                color: {btn_pri_fg};
                border: none;
                border-radius: 8px;
                padding: 7px 22px;
                font-size: 13px;
                font-weight: 600;
                font-family: 'Segoe UI', sans-serif;
            }}
            #tbcd_btn_primary:hover   {{ background: {btn_pri_hover}; }}
            #tbcd_btn_primary:pressed {{ background: {btn_pri_hover}; }}

            #tbcd_btn_secondary {{
                background: {btn_sec_bg};
                color: {btn_sec_fg};
                border: 1px solid {btn_sec_border};
                border-radius: 8px;
                padding: 7px 14px;
                font-size: 13px;
                font-family: 'Segoe UI', sans-serif;
            }}
            #tbcd_btn_secondary:hover   {{ background: {btn_sec_hover}; }}
            #tbcd_btn_secondary:pressed {{ background: {cb_hover_bg}; }}
        """)
