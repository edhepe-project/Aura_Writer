"""
history_diff_dialog.py — Diálogo visual de Historial de Versiones y Diff de Capítulos.
"""

from __future__ import annotations
from datetime import datetime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QPushButton, QListWidget, QListWidgetItem,
    QTextBrowser, QMessageBox, QWidget, QFrame, QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import qtawesome as qta

from core.theme_manager import ThemeManager
from core.diff_engine import DiffEngine
from core.models import Chapter, ChapterRevision


class ChapterHistoryDiffDialog(QDialog):
    """
    Diálogo para inspeccionar, comparar y restaurar versiones históricas de un capítulo.
    """
    revision_restored = pyqtSignal(str)  # Emite el ID del capítulo restaurado

    def __init__(self, project_manager, chapter: Chapter, parent=None):
        super().__init__(parent)
        self.pm = project_manager
        self.chapter = chapter
        self._selected_revision: ChapterRevision | None = None

        self.setWindowTitle(f"📜 Historial de Versiones & Diff — {chapter.title}")
        self.resize(1080, 680)
        self.setMinimumSize(800, 500)

        self._setup_ui()
        self._load_revisions()

    def _setup_ui(self):
        is_dark = ThemeManager.is_dark()

        bg_main = "#1c1c1e" if is_dark else "#f2f2f7"
        bg_card = "#2c2c2e" if is_dark else "#ffffff"
        fg_title = "#f2f2f7" if is_dark else "#1a1a2e"
        fg_muted = "#8e8e93" if is_dark else "#7a7a8a"
        b_border = "#3a3a3c" if is_dark else "#d1d1d6"

        self.setStyleSheet(f"""
            QDialog {{ background-color: {bg_main}; }}
            QFrame#card {{ background-color: {bg_card}; border: 1px solid {b_border}; border-radius: 8px; }}
            QListWidget {{ background-color: {bg_card}; border: 1px solid {b_border}; border-radius: 6px; color: {fg_title}; }}
            QListWidget::item {{ padding: 8px; border-bottom: 1px solid {b_border}; }}
            QListWidget::item:selected {{ background-color: #007aff; color: #ffffff; border-radius: 4px; }}
            QTextBrowser {{ background-color: {bg_card}; border: 1px solid {b_border}; border-radius: 6px; }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # ── Barra superior ───────────────────────────────────────────
        top_bar = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon("fa5s.history", color="#007aff").pixmap(22, 22))
        top_bar.addWidget(icon_lbl)

        title_lbl = QLabel(f"<b>Historial de Revisiones:</b> {self.chapter.title}")
        title_lbl.setStyleSheet(f"font-size: 15px; color: {fg_title};")
        top_bar.addWidget(title_lbl)
        top_bar.addStretch()

        self.btn_snapshot = QPushButton(" 📷 Crear Instantánea Manual")
        self.btn_snapshot.setIcon(qta.icon("fa5s.camera", color="#ffffff"))
        self.btn_snapshot.setStyleSheet("""
            QPushButton {
                background-color: #34c759;
                color: #ffffff;
                font-weight: bold;
                padding: 6px 14px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover { background-color: #30d158; }
        """)
        self.btn_snapshot.clicked.connect(self._create_manual_snapshot)
        top_bar.addWidget(self.btn_snapshot)

        root.addLayout(top_bar)

        # ── Divisor Principal (Lista vs Diff) ────────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Panel Izquierdo: Lista de Revisiones
        left_panel = QFrame()
        left_panel.setObjectName("card")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(8)

        lbl_revs = QLabel("VERSIONES GUARDADAS")
        lbl_revs.setStyleSheet(f"color: {fg_muted}; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;")
        left_layout.addWidget(lbl_revs)

        self.list_revisions = QListWidget()
        self.list_revisions.currentRowChanged.connect(self._on_revision_selected)
        left_layout.addWidget(self.list_revisions, 1)

        splitter.addWidget(left_panel)

        # Panel Derecho: Visualizador de Diff
        right_panel = QFrame()
        right_panel.setObjectName("card")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(8)

        diff_header = QHBoxLayout()
        self.lbl_diff_info = QLabel("Selecciona una revisión para comparar con la versión actual.")
        self.lbl_diff_info.setStyleSheet(f"font-size: 12px; color: {fg_title};")
        diff_header.addWidget(self.lbl_diff_info)
        diff_header.addStretch()

        self.lbl_stats = QLabel("")
        self.lbl_stats.setStyleSheet("font-size: 11px; font-weight: bold;")
        diff_header.addWidget(self.lbl_stats)

        right_layout.addLayout(diff_header)

        self.diff_browser = QTextBrowser()
        self.diff_browser.setOpenExternalLinks(False)
        right_layout.addWidget(self.diff_browser, 1)

        # Barra de acciones inferior en el panel derecho
        bottom_right = QHBoxLayout()
        bottom_right.addStretch()

        self.btn_restore = QPushButton(" ↺ Restaurar esta Versión")
        self.btn_restore.setIcon(qta.icon("fa5s.undo-alt", color="#ffffff"))
        self.btn_restore.setStyleSheet("""
            QPushButton {
                background-color: #007aff;
                color: #ffffff;
                font-weight: bold;
                padding: 8px 18px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover { background-color: #0062cc; }
            QPushButton:disabled { background-color: #555555; color: #888888; }
        """)
        self.btn_restore.setEnabled(False)
        self.btn_restore.clicked.connect(self._restore_selected_revision)
        bottom_right.addWidget(self.btn_restore)

        right_layout.addLayout(bottom_right)

        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        root.addWidget(splitter, 1)

    def _load_revisions(self):
        self.list_revisions.clear()
        revisions = self.chapter.revisions or []

        if not revisions:
            item = QListWidgetItem("Sin revisiones previas.")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_revisions.addItem(item)
            self.diff_browser.setHtml("<p style='color: gray; padding: 16px;'>Aún no hay instantáneas guardadas para este capítulo.<br>Crea una instantánea manual usando el botón superior.</p>")
            self.btn_restore.setEnabled(False)
            return

        # Listar en orden cronológico inverso (la más reciente arriba)
        for rev in reversed(revisions):
            try:
                date_str = rev.created_at.strftime("%d/%m/%Y %H:%M:%S")
            except Exception:
                date_str = str(rev.created_at)

            item = QListWidgetItem(f"🕒 {date_str}\n   {rev.description}")
            item.setData(Qt.ItemDataRole.UserRole, rev)
            self.list_revisions.addItem(item)

        self.list_revisions.setCurrentRow(0)

    def _on_revision_selected(self, row: int):
        item = self.list_revisions.item(row)
        if not item:
            return
        rev = item.data(Qt.ItemDataRole.UserRole)
        if not rev:
            return

        self._selected_revision = rev
        self.btn_restore.setEnabled(True)

        # Leer HTML de la revisión y el HTML actual del capítulo
        rev_html = self.pm.read_chapter_revision_content(rev)
        current_html = self.pm.read_chapter_content(self.chapter.content_file)

        is_dark = ThemeManager.is_dark()
        diff_html, stats = DiffEngine.compute_inline_diff_html(rev_html, current_html, is_dark=is_dark)

        self.diff_browser.setHtml(diff_html)
        self.lbl_diff_info.setText(f"Comparando <b>Revisión ({rev.description})</b> ➔ <b>Versión Actual</b>")

        # Formatear estadísticas
        stat_parts = []
        if stats.words_added > 0:
            stat_parts.append(f"<span style='color:#30d158;'>+{stats.words_added} palabras</span>")
        if stats.words_deleted > 0:
            stat_parts.append(f"<span style='color:#ff453a;'>-{stats.words_deleted} palabras</span>")
        if not stat_parts:
            stat_parts.append("<span style='color:#8e8e93;'>Sin cambios de texto</span>")

        self.lbl_stats.setText(" | ".join(stat_parts))

    def _create_manual_snapshot(self):
        desc, ok = QInputDialog.getText(
            self, "Nueva Instantánea",
            "Descripción de la versión:",
            text="Versión manual"
        )
        if ok and desc.strip():
            rev = self.pm.create_chapter_revision(self.chapter.id, description=desc.strip())
            if rev:
                self._load_revisions()
                QMessageBox.information(self, "Instantánea Guardada", "La versión ha sido guardada en el historial.")

    def _restore_selected_revision(self):
        if not self._selected_revision:
            return

        reply = QMessageBox.question(
            self, "Confirmar Restauración",
            f"¿Estás seguro de que deseas restaurar esta versión?\n\n"
            f"Descripción: {self._selected_revision.description}\n\n"
            f"Se creará una copia de respaldo automática del estado actual antes de sobrescribir.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success = self.pm.restore_chapter_revision(self.chapter.id, self._selected_revision.id)
            if success:
                self.revision_restored.emit(self.chapter.id)
                QMessageBox.information(self, "Versión Restaurada", "El capítulo ha sido restaurado exitosamente.")
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "No se pudo restaurar la versión seleccionada.")
