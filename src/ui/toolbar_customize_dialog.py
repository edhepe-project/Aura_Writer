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
        self.setStyleSheet("""
            QDialog { background: #1c1c1e; }

            #tbcd_header { background: #2c2c2e; }

            #tbcd_title {
                font-size: 15px;
                font-weight: 700;
                color: #f2f2f7;
                font-family: 'Segoe UI', sans-serif;
            }
            #tbcd_subtitle {
                font-size: 11px;
                color: #8e8e93;
                font-family: 'Segoe UI', sans-serif;
            }

            #tbcd_sep {
                background: #3a3a3c;
                min-height: 1px;
                max-height: 1px;
                border: none;
            }

            #tbcd_content { background: #1c1c1e; }

            QScrollArea { background: #1c1c1e; border: none; }
            QScrollBar:vertical {
                background: #1c1c1e; width: 6px; border: none;
            }
            QScrollBar::handle:vertical {
                background: #48484a; border-radius: 3px; min-height: 24px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }

            #tbcd_group {
                font-size: 10px;
                font-weight: 700;
                color: #636366;
                letter-spacing: 0.08em;
                font-family: 'Segoe UI', sans-serif;
                padding-top: 10px;
                padding-bottom: 2px;
            }

            #tbcd_cb {
                font-size: 13px;
                color: #e5e5ea;
                font-family: 'Segoe UI', sans-serif;
                padding: 5px 10px;
                border-radius: 6px;
                spacing: 8px;
            }
            #tbcd_cb:hover { background: #2c2c2e; }
            #tbcd_cb:disabled { color: #48484a; }

            #tbcd_cb::indicator {
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1.5px solid #48484a;
                background: #1c1c1e;
            }
            #tbcd_cb::indicator:checked {
                background: #ffd60a;
                border-color: #ffd60a;
                image: none;
            }
            #tbcd_cb::indicator:unchecked:hover { border-color: #636366; }

            #tbcd_btnbar { background: #2c2c2e; }

            #tbcd_btn_primary {
                background: #ffd60a;
                color: #1c1c1e;
                border: none;
                border-radius: 8px;
                padding: 7px 22px;
                font-size: 13px;
                font-weight: 600;
                font-family: 'Segoe UI', sans-serif;
            }
            #tbcd_btn_primary:hover   { background: #ffe84d; }
            #tbcd_btn_primary:pressed { background: #c9a800; }

            #tbcd_btn_secondary {
                background: #3a3a3c;
                color: #e5e5ea;
                border: none;
                border-radius: 8px;
                padding: 7px 14px;
                font-size: 13px;
                font-family: 'Segoe UI', sans-serif;
            }
            #tbcd_btn_secondary:hover   { background: #48484a; }
            #tbcd_btn_secondary:pressed { background: #2c2c2e; }
        """)
