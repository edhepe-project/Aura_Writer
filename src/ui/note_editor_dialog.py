"""
Aura Writer — Note Editor Dialog
Modal para ver, editar y eliminar notas de autor desde el inspector.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTextEdit, QPushButton, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut


class NoteEditorDialog(QDialog):
    """
    Modal premium para editar una nota de autor.
    Se abre con doble-click en la lista de notas del inspector.
    Emite la nota modificada al aceptar.
    """

    def __init__(self, note, parent=None):
        super().__init__(parent)
        from core.theme_manager import ThemeManager
        self._note     = note
        self._is_dark  = ThemeManager.is_dark()
        self._deleted  = False

        self.setWindowTitle(f"Nota — {note.title}")
        self.setModal(True)
        self.resize(580, 460)
        self.setMinimumSize(440, 340)

        self._setup_ui()
        self._apply_style()

        # Ctrl+Enter guarda
        QShortcut(QKeySequence("Ctrl+Return"), self, activated=self._save)
        # Esc cierra sin guardar
        QShortcut(QKeySequence("Escape"), self, activated=self.reject)

        QTimer.singleShot(0, self.content_edit.setFocus)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        # ── Encabezado ─────────────────────────────────────────────
        hdr = QHBoxLayout()

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title_hint = QLabel("NOTA DE AUTOR")
        title_hint.setObjectName("noteHint")
        title_col.addWidget(title_hint)

        self.title_edit = QLineEdit(self._note.title)
        self.title_edit.setObjectName("noteTitle")
        self.title_edit.setPlaceholderText("Título de la nota…")
        title_col.addWidget(self.title_edit)

        hdr.addLayout(title_col, 1)
        root.addLayout(hdr)

        # ── Separador ──────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("noteSep")
        root.addWidget(sep)

        # ── Contenido ──────────────────────────────────────────────
        content_hint = QLabel("Contenido")
        content_hint.setObjectName("contentHint")
        root.addWidget(content_hint)

        self.content_edit = QTextEdit()
        self.content_edit.setObjectName("noteContent")
        self.content_edit.setPlaceholderText("Escribe el contenido de la nota aquí…")
        self.content_edit.setPlainText(self._note.content or "")
        self.content_edit.setSizePolicy(QSizePolicy.Policy.Expanding,
                                        QSizePolicy.Policy.Expanding)
        root.addWidget(self.content_edit, 1)

        # ── Botonera ───────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.btn_delete = QPushButton("Eliminar")
        self.btn_delete.setObjectName("btnDelete")
        self.btn_delete.clicked.connect(self._delete)

        btn_row.addWidget(self.btn_delete)
        btn_row.addStretch()

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setObjectName("btnCancel")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton("Guardar")
        self.btn_save.setObjectName("btnSave")
        self.btn_save.setDefault(True)
        self.btn_save.clicked.connect(self._save)

        btn_row.addWidget(self.btn_cancel)
        btn_row.addWidget(self.btn_save)
        root.addLayout(btn_row)

        # Shortcut hint
        hint = QLabel("Ctrl+Enter para guardar  ·  Esc para cancelar")
        hint.setObjectName("shortcutHint")
        hint.setAlignment(Qt.AlignmentFlag.AlignRight)
        root.addWidget(hint)

    def _apply_style(self):
        if self._is_dark:
            bg          = "#1c1c1e"
            surface     = "#2c2c2e"
            surface2    = "#3a3a3c"
            border      = "#3a3a3c"
            accent      = "#9b59b6"
            text        = "#f2f2f7"
            sub         = "#8e8e93"
            danger      = "#ff453a"
            danger_hover= "#ff6961"
            ok_bg       = "#30d158"
            ok_hover    = "#32e05e"
            ok_text     = "#000000"
            sep_col     = "#3a3a3c"
        else:
            bg          = "#f5f0ea"
            surface     = "#faf7f3"
            surface2    = "#ede8e1"
            border      = "#d4cfc8"
            accent      = "#9b59b6"
            text        = "#1a1a2e"
            sub         = "#7a7a8a"
            danger      = "#c0392b"
            danger_hover= "#e74c3c"
            ok_bg       = "#27ae60"
            ok_hover    = "#2ecc71"
            ok_text     = "#ffffff"
            sep_col     = "#d4cfc8"

        self.setStyleSheet(f"""
            QDialog {{
                background: {bg};
            }}
            QLabel#noteHint {{
                color: {accent};
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 1px;
            }}
            QLabel#noteIcon {{
                font-size: 28px;
                padding-right: 8px;
            }}
            QLabel#contentHint {{
                color: {sub};
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }}
            QLabel#shortcutHint {{
                color: {sub};
                font-size: 10px;
                padding-top: 2px;
            }}
            QFrame#noteSep {{
                color: {sep_col};
                margin: 2px 0;
            }}
            QLineEdit#noteTitle {{
                background: {surface};
                color: {text};
                border: 1px solid {border};
                border-radius: 8px;
                padding: 7px 12px;
                font-size: 15px;
                font-weight: 600;
            }}
            QLineEdit#noteTitle:focus {{
                border-color: {accent};
            }}
            QTextEdit#noteContent {{
                background: {surface};
                color: {text};
                border: 1px solid {border};
                border-radius: 10px;
                padding: 10px 14px;
                font-size: 13px;
                line-height: 1.5;
                selection-background-color: {surface2};
            }}
            QTextEdit#noteContent:focus {{
                border-color: {accent};
            }}
            QPushButton#btnSave {{
                background: {ok_bg};
                color: {ok_text};
                border: none;
                border-radius: 8px;
                padding: 7px 20px;
                font-size: 13px;
                font-weight: 600;
                min-width: 110px;
            }}
            QPushButton#btnSave:hover {{
                background: {ok_hover};
            }}
            QPushButton#btnSave:pressed {{
                opacity: 0.85;
            }}
            QPushButton#btnCancel {{
                background: {surface2};
                color: {sub};
                border: 1px solid {border};
                border-radius: 8px;
                padding: 7px 16px;
                font-size: 13px;
                min-width: 90px;
            }}
            QPushButton#btnCancel:hover {{
                color: {text};
                background: {surface};
            }}
            QPushButton#btnDelete {{
                background: transparent;
                color: {danger};
                border: 1px solid {danger};
                border-radius: 8px;
                padding: 7px 14px;
                font-size: 13px;
                min-width: 100px;
            }}
            QPushButton#btnDelete:hover {{
                background: {danger_hover};
                color: #ffffff;
            }}
        """)

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------

    def _save(self):
        title = self.title_edit.text().strip()
        if not title:
            self.title_edit.setFocus()
            return
        self._note.title   = title
        self._note.content = self.content_edit.toPlainText()
        self._deleted = False
        self.accept()

    def _delete(self):
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "Eliminar Nota",
            f"¿Eliminar la nota «{self._note.title}» permanentemente?\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._deleted = True
            self.accept()

    # ------------------------------------------------------------------
    # Propiedades de resultado
    # ------------------------------------------------------------------

    @property
    def was_deleted(self) -> bool:
        return self._deleted

    @property
    def note(self):
        return self._note
