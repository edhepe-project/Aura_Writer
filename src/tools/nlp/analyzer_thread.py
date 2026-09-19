"""
analyzer_thread.py — QThread wrapper para análisis NLP asíncrono.
Responsabilidad única: ejecutar PresenceAnalyzer en un hilo secundario
para que el guardado y la UI nunca se bloqueen.

Flujo:
  1. El controlador crea AnalyzerThread con los datos del capítulo
  2. Llama a .start() → el análisis corre en background
  3. Cuando termina, emite analysis_done(presences) o analysis_error(msg)
  4. El slot del hilo principal recibe el resultado y actualiza el modelo

IMPORTANTE: Este thread NO modifica ningún dato compartido directamente.
Solo emite señales. La actualización del modelo ocurre en el hilo principal
a través de los slots conectados a analysis_done.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import QThread, pyqtSignal

if TYPE_CHECKING:
    from core.models import Character, Place, CustomVocabularyEntry, Chapter

log = logging.getLogger(__name__)


class AnalyzerThread(QThread):
    """
    Ejecuta el análisis de presencia de un capítulo en un hilo secundario.

    Señales:
        analysis_done(list): Lista de CharacterPresence detectadas.
        analysis_error(str): Mensaje de error si el análisis falla.
        analysis_progress(str): Mensaje de progreso (nombre del capítulo).

    Uso:
        thread = AnalyzerThread(chapter, html, characters, places, vocab)
        thread.analysis_done.connect(self._on_presences_ready)
        thread.analysis_error.connect(self._on_analysis_error)
        thread.start()
        # El hilo principal sigue libre — sin bloqueos
    """

    analysis_done     = pyqtSignal(list)    # List[CharacterPresence]
    analysis_error    = pyqtSignal(str)     # mensaje de error
    analysis_progress = pyqtSignal(str)     # nombre del capítulo en proceso

    def __init__(
        self,
        chapters_and_html: list[tuple],     # [(Chapter, html_str), ...]
        characters: list["Character"],
        places: list["Place"],
        custom_vocabulary: list["CustomVocabularyEntry"],
        parent=None,
    ):
        """
        Args:
            chapters_and_html: Lista de tuplas (Chapter, html) a analizar.
            characters: Personajes del universo.
            places: Lugares del universo.
            custom_vocabulary: Vocabulario personalizado (conlang).
            parent: QObject padre opcional.
        """
        super().__init__(parent)
        self._chapters_and_html = chapters_and_html
        self._characters = characters
        self._places = places
        self._custom_vocabulary = custom_vocabulary

    def run(self) -> None:
        """
        Ejecutado en el hilo secundario. NO llamar directamente — usar .start().
        """
        try:
            from tools.nlp.presence_analyzer import PresenceAnalyzer

            analyzer = PresenceAnalyzer(
                characters=self._characters,
                places=self._places,
                custom_vocabulary=self._custom_vocabulary,
            )

            all_presences = []
            for chapter, html in self._chapters_and_html:
                self.analysis_progress.emit(chapter.title)
                log.debug("AnalyzerThread: analizando '%s'", chapter.title)

                detected = analyzer.analyze_chapter(chapter, html)
                all_presences.extend(detected)

            log.info(
                "AnalyzerThread: %d presencias detectadas en %d capítulos",
                len(all_presences),
                len(self._chapters_and_html),
            )
            self.analysis_done.emit(all_presences)

        except Exception as e:
            log.exception("AnalyzerThread: error durante el análisis")
            self.analysis_error.emit(str(e))


class SingleChapterAnalyzerThread(AnalyzerThread):
    """
    Versión simplificada para analizar un solo capítulo (auto-análisis al guardar).

    Uso:
        thread = SingleChapterAnalyzerThread(chapter, html, chars, places, vocab)
        thread.analysis_done.connect(self._on_chapter_presences_ready)
        thread.start()
    """

    def __init__(
        self,
        chapter: "Chapter",
        html: str,
        characters: list["Character"],
        places: list["Place"],
        custom_vocabulary: list["CustomVocabularyEntry"],
        parent=None,
    ):
        super().__init__(
            chapters_and_html=[(chapter, html)],
            characters=characters,
            places=places,
            custom_vocabulary=custom_vocabulary,
            parent=parent,
        )
        self._chapter = chapter

    @property
    def chapter_id(self) -> str:
        """ID del capítulo que se está analizando."""
        return self._chapter.id
