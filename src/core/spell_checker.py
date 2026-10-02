"""
spell_checker.py — Motor de corrección ortográfica offline para Aura Writer.

Usa pyspellchecker (rápido, liviano) con una capa de excepciones morfológicas
para reconocer conjugaciones verbales y formas del español que el corpus de
frecuencias no incluye.

Estrategia de verificación:
1. Palabra en diccionario personal o ignoradas → OK
2. Palabra en excepciones morfológicas (verbos conjugados) → OK
3. pyspellchecker la conoce → OK
4. Si ninguno → ERROR
"""
from __future__ import annotations

import re
import logging
from pathlib import Path
from typing import NamedTuple

from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal

log = logging.getLogger(__name__)


# ── Tipos de datos ─────────────────────────────────────────────────────────────

class SpellError(NamedTuple):
    """Un error ortográfico detectado en el texto plano del editor."""
    word: str
    start: int
    end: int
    suggestions: list[str]


# ── Generador morfológico de excepciones ───────────────────────────────────────

def _generate_morphological_exceptions() -> set[str]:
    """
    Genera el conjunto de formas morfológicas válidas del español que
    pyspellchecker no conoce por ser poco frecuentes en su corpus.
    Incluye conjugaciones regulares de -AR, -ER, -IR en todos los tiempos.
    """
    exceptions: set[str] = set()

    # ── Pretérito perfecto simple (pasado) ────────────────────────────────────
    # Terminaciones -AR: -é -aste -ó -amos -asteis -aron
    ar_pret = ['é', 'aste', 'ó', 'amos', 'asteis', 'aron']
    # Terminaciones -ER/-IR: -í -iste -ió -imos -isteis -ieron
    er_pret = ['í', 'iste', 'ió', 'imos', 'isteis', 'ieron']

    # ── Imperfecto de indicativo ──────────────────────────────────────────────
    # -AR: -aba -abas -aba -ábamos -abais -aban
    ar_imp = ['aba', 'abas', 'ábamos', 'abais', 'aban']
    # -ER/-IR: -ía -ías -ía -íamos -íais -ían
    er_imp = ['ía', 'ías', 'íamos', 'íais', 'ían']

    # ── Futuro de indicativo ──────────────────────────────────────────────────
    fut = ['é', 'ás', 'á', 'emos', 'éis', 'án']  # se añade a infinitivo

    # ── Condicional ───────────────────────────────────────────────────────────
    cond = ['ía', 'ías', 'íamos', 'íais', 'ían']  # se añade a infinitivo

    # ── Subjuntivo presente ───────────────────────────────────────────────────
    ar_subj = ['e', 'es', 'emos', 'éis', 'en']
    er_subj = ['a', 'as', 'amos', 'áis', 'an']

    # ── Subjuntivo imperfecto (-ra / -se) ─────────────────────────────────────
    ar_subj_imp = ['ara', 'aras', 'áramos', 'arais', 'aran',
                   'ase', 'ases', 'ásemos', 'aseis', 'asen']
    er_subj_imp = ['iera', 'ieras', 'iéramos', 'ierais', 'ieran',
                   'iese', 'ieses', 'iésemos', 'ieseis', 'iesen']

    # Verbos -AR comunes (raíces)
    # Nota: sin duplicados (‘am’, ‘salt’, ‘entr’, ‘esper’ aparecían más de una vez)
    ar_roots = [
        'labor', 'am', 'cant', 'trabaj', 'habl', 'escuch', 'mir', 'pens',
        'cambi', 'us', 'llam', 'llev', 'dej', 'tom', 'pas', 'bus', 'encontr',
        'empez', 'acab', 'necesit', 'esper', 'intent', 'demostr', 'prepar',
        'guard', 'termin', 'comenz', 'mov', 'continu', 'luch', 'aprend',
        'camb', 'entr', 'salt', 'pregunt', 'respet', 'logr', 'alcanc',
        'escrib', 'dibuj', 'cre', 'jug', 'camin', 'corr',
        'toc', 'grit', 'susurr', 'soñ', 'viv', 'od', 'busc',
        'llegue', 'volv', 'regres', 'sal', 'empe',
    ]

    # Verbos -ER comunes (raíces)
    er_roots = [
        'com', 'beb', 'le', 'corr', 'vend', 'vol', 'pod', 'pon', 'ten',
        'sab', 'querer', 'deb', 'prometi', 'aprend', 'comprendí', 'respond',
        'comprend', 'sorprend', 'entend', 'descend', 'ascend', 'depend',
    ]

    # Verbos -IR comunes (raíces)
    ir_roots = [
        'viv', 'escrib', 'part', 'sub', 'abr', 'recib', 'sali', 'decid',
        'permit', 'insist', 'consist', 'exist', 'ocurri', 'conclui',
        'concluy', 'constru', 'destruy', 'inclu',
    ]

    # Generar formas -AR pretérito e imperfecto
    for root in ar_roots:
        for suf in ar_pret:
            exceptions.add(root + suf)
        for suf in ar_imp:
            exceptions.add(root + suf)
        for suf in ar_subj:
            exceptions.add(root + suf)
        for suf in ar_subj_imp:
            exceptions.add(root + suf)

    # Generar formas -ER/-IR pretérito e imperfecto
    for root in er_roots + ir_roots:
        for suf in er_pret:
            exceptions.add(root + suf)
        for suf in er_imp:
            exceptions.add(root + suf)
        for suf in er_subj:
            exceptions.add(root + suf)
        for suf in er_subj_imp:
            exceptions.add(root + suf)

    # Formas irregulares muy comunes que pyspell no reconoce
    manual = {
        # Haber (auxiliar)
        'hube','hubiste','hubo','hubimos','hubisteis','hubieron',
        'había','habías','habíamos','habíais','habían',
        # Ser/Estar
        'fui','fuiste','fue','fuimos','fuisteis','fueron',
        'era','eras','éramos','erais','eran',
        'estuve','estuviste','estuvo','estuvimos','estuvisteis','estuvieron',
        'estaba','estabas','estábamos','estabais','estaban',
        # Tener
        'tuve','tuviste','tuvo','tuvimos','tuvisteis','tuvieron',
        'tenía','tenías','teníamos','teníais','tenían',
        # Hacer
        'hice','hiciste','hizo','hicimos','hicisteis','hicieron',
        'hacía','hacías','hacíamos','hacíais','hacían',
        # Ir
        'iba','ibas','íbamos','ibais','iban',
        # Poder
        'pude','pudiste','pudo','pudimos','pudisteis','pudieron',
        'podía','podías','podíamos','podíais','podían',
        # Querer
        'quise','quisiste','quiso','quisimos','quisisteis','quisieron',
        'quería','querías','queríamos','queríais','querían',
        # Decir
        'dije','dijiste','dijo','dijimos','dijisteis','dijeron',
        'decía','decías','decíamos','decíais','decían',
        # Venir
        'vine','viniste','vino','vinimos','vinisteis','vinieron',
        'venía','venías','veníamos','veníais','venían',
        # Ver
        'vi','viste','vio','vimos','visteis','vieron',
        'veía','veías','veíamos','veíais','veían',
        # Saber
        'supe','supiste','supo','supimos','supisteis','supieron',
        'sabía','sabías','sabíamos','sabíais','sabían',
        # Dar
        'di','diste','dio','dimos','disteis','dieron',
        'daba','dabas','dábamos','dabais','daban',
        # Poner
        'puse','pusiste','puso','pusimos','pusisteis','pusieron',
        'ponía','ponías','poníamos','poníais','ponían',
        # Salir
        'salí','saliste','salió','salimos','salisteis','salieron',
        'salía','salías','salíamos','salíais','salían',
        # Volver
        'volví','volviste','volvió','volvimos','volvisteis','volvieron',
        'volvía','volvías','volvíamos','volvíais','volvían',
        # Escribir
        'escribí','escribiste','escribió','escribimos','escribisteis','escribieron',
        'escribía','escribías','escribíamos','escribíais','escribían',
        # Abrir
        'abrí','abriste','abrió','abrimos','abristeis','abrieron',
        'abría','abrías','abríamos','abríais','abrían',
        # Vivir
        'viví','viviste','vivió','vivimos','vivisteis','vivieron',
        'vivía','vivías','vivíamos','vivíais','vivían',
        # Correr
        'corrí','corriste','corrió','corrimos','corristeis','corrieron',
        'corría','corrías','corríamos','corríais','corrían',
        # Palabras comunes mal clasificadas
        'había','habrá','habría','hubiera','hubiese',
        'seré','serás','será','seremos','seréis','serán',
        'sería','serías','seríamos','seríais','serían',
    }
    exceptions.update(manual)
    return exceptions


# Caché global — se genera una vez al importar el módulo
_MORPHOLOGICAL_EXCEPTIONS: set[str] = _generate_morphological_exceptions()


# ── Worker asíncrono ───────────────────────────────────────────────────────────

class _SpellWorkerSignals(QObject):
    finished = pyqtSignal(list)
    error    = pyqtSignal(str)


class _SpellWorker(QRunnable):
    """Ejecuta la revisión en un hilo del pool global, sin bloquear la UI."""

    def __init__(self, checker: "AuraSpellChecker", plain_text: str):
        super().__init__()
        self._checker = checker
        self._text = plain_text
        self.signals = _SpellWorkerSignals()
        self.setAutoDelete(True)

    def run(self):
        try:
            if getattr(self._checker, "_is_closing", False) or not getattr(self._checker, "_enabled", True):
                return
            errors = self._checker._check_text(self._text)
            if getattr(self._checker, "_is_closing", False) or not getattr(self._checker, "_enabled", True):
                return
            if getattr(self._checker, "_show_errors", True):
                self.signals.finished.emit(errors)
            else:
                self.signals.finished.emit([])
        except RuntimeError:
            # Objeto Qt subyacente ya fue destruido (la ventana se está cerrando)
            pass
        except Exception as exc:
            if not getattr(self._checker, "_is_closing", False):
                log.exception("Error en SpellWorker: %s", exc)
                try:
                    self.signals.error.emit(str(exc))
                except Exception:
                    pass


# ── Motor principal ────────────────────────────────────────────────────────────

class AuraSpellChecker(QObject):
    """
    Corrector ortográfico offline integrado en Aura Writer.

    Uso:
        checker = AuraSpellChecker(language='es')
        checker.errors_ready.connect(my_slot)
        checker.check_async(plain_text)
    """

    checking_started = pyqtSignal()
    errors_ready     = pyqtSignal(list)
    check_error      = pyqtSignal(str)

    _WORD_RE = re.compile(
        r"\b[a-záéíóúüñàèìòùâêîôûäëïöüç\u2019\u2018A-ZÁÉÍÓÚÜÑ]+"
        r"(?:['\u2019-][a-záéíóúüñA-ZÁÉÍÓÚÜÑ]+)*\b"
    )

    def __init__(self, language: str = "es", parent: QObject | None = None):
        super().__init__(parent)
        self._language = language
        self._hunspell = None
        self._checker = None
        self._word_cache: dict[str, bool] = {}
        self._suggestion_cache: dict[str, list[str]] = {}
        self._personal_words: set[str] = set()
        self._ignored_words: set[str] = set()
        self._pool = QThreadPool.globalInstance()
        self._enabled = False  # Completamente desactivado por defecto
        self._show_errors = False
        self._is_closing = False
        self._load_checker()

    def stop(self):
        """Detiene el corrector ortográfico de forma limpia."""
        self._is_closing = True
        self._enabled = False
        try:
            self.checking_started.disconnect()
        except Exception:
            pass
        try:
            self.errors_ready.disconnect()
        except Exception:
            pass
        try:
            self.check_error.disconnect()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Inicialización
    # ------------------------------------------------------------------

    def _load_checker(self):
        """Carga Hunspell (spylls) como motor principal y pyspellchecker como fallback."""
        self._word_cache.clear()
        self._suggestion_cache.clear()

        # 1. Intentar Hunspell mediante spylls
        try:
            import sys as _sys
            from spylls.hunspell import Dictionary
            if getattr(_sys, "frozen", False) and hasattr(_sys, "_MEIPASS"):
                base_dir = Path(getattr(_sys, "_MEIPASS"))
                dict_base = base_dir / "core" / "dicts" / self._language
                if not dict_base.with_suffix(".aff").exists():
                    dict_base = base_dir / "src" / "core" / "dicts" / self._language
            else:
                dict_base = Path(__file__).parent / "dicts" / self._language

            aff_path = dict_base.with_suffix(".aff")
            dic_path = dict_base.with_suffix(".dic")
            if aff_path.exists() and dic_path.exists():
                self._hunspell = Dictionary.from_files(str(dict_base))
                log.info("Hunspell '%s' cargado con éxito.", self._language)
            else:
                self._hunspell = None
                log.warning("Archivos de diccionario no encontrados en %s", dict_base)
        except Exception as exc:
            log.warning("No se pudo cargar Hunspell para '%s': %s", self._language, exc)
            self._hunspell = None

        # 2. Cargar pyspellchecker como fallback
        try:
            from spellchecker import SpellChecker
            self._checker = SpellChecker(language=self._language, distance=1)
            log.info("pyspellchecker '%s' cargado como fallback.", self._language)
        except Exception as exc:
            log.error("No se pudo cargar pyspellchecker para '%s': %s", self._language, exc)
            self._checker = None

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value
        self._show_errors = value
        if not value:
            self.errors_ready.emit([])

    @property
    def show_errors(self) -> bool:
        return self._show_errors

    @show_errors.setter
    def show_errors(self, value: bool):
        # Activar show_errors también activa el motor; desactivar apaga todo
        self.enabled = value

    @property
    def language(self) -> str:
        return self._language

    def set_language(self, lang: str):
        """Cambia el idioma y recarga el diccionario."""
        if lang == self._language and (self._hunspell is not None or self._checker is not None):
            return
        self._language = lang
        self._load_checker()

    def add_to_personal_dictionary(self, word: str):
        """Añade una palabra al diccionario personal (persistente en el proyecto)."""
        self._personal_words.add(word.lower().strip())
        self._word_cache.clear()
        self._suggestion_cache.clear()

    def ignore_word(self, word: str):
        """Ignora una palabra sólo en esta sesión."""
        self._ignored_words.add(word.lower().strip())
        self._word_cache.clear()
        self._suggestion_cache.clear()

    def load_personal_dictionary(self, words: list[str]):
        """Carga el diccionario personal desde los datos del proyecto."""
        self._personal_words = {w.lower().strip() for w in words if w.strip()}
        self._word_cache.clear()
        self._suggestion_cache.clear()
        if self._checker and self._personal_words:
            self._checker.word_frequency.load_words(list(self._personal_words))

    def get_personal_dictionary(self) -> list[str]:
        """Devuelve la lista de palabras del diccionario personal."""
        return sorted(self._personal_words)

    def check_async(self, plain_text: str):
        """Lanza la revisión ortográfica en segundo plano."""
        if not self._enabled or (self._hunspell is None and self._checker is None):
            self.errors_ready.emit([])
            return
        self.checking_started.emit()
        worker = _SpellWorker(self, plain_text)
        worker.signals.finished.connect(self.errors_ready)
        worker.signals.error.connect(self.check_error)
        self._pool.start(worker)

    def check_word(self, word: str) -> bool:
        """Retorna True si la palabra está bien escrita."""
        if not self._enabled:
            return True
        w_clean = word.strip(".,;:!?¡¿\"'()[]{}/\\-—–«»“”")
        if not w_clean or len(w_clean) <= 1 or w_clean.isdigit():
            return True

        w_lower = w_clean.lower()
        if w_lower in self._ignored_words or w_lower in self._personal_words:
            return True
        if w_lower in _MORPHOLOGICAL_EXCEPTIONS:
            return True

        # Caché en memoria (instantáneo: 0.0001 ms)
        cached = self._word_cache.get(w_clean)
        if cached is not None:
            return cached

        # 1. Consulta Hunspell (valida reglas de afijos, tiempos verbales y plurales)
        if self._hunspell is not None:
            try:
                valid = self._hunspell.lookup(w_clean) or self._hunspell.lookup(w_lower)
                if valid:
                    self._word_cache[w_clean] = True
                    return True
            except Exception:
                pass

        # 2. Consulta pyspellchecker (fallback)
        if self._checker is not None:
            try:
                if not self._checker.unknown([w_lower]):
                    self._word_cache[w_clean] = True
                    return True
            except Exception:
                pass

        self._word_cache[w_clean] = False
        return False

    def suggestions(self, word: str) -> list[str]:
        """Devuelve hasta 5 sugerencias para una palabra con error (con caché)."""
        w_clean = word.strip(".,;:!?¡¿\"'()[]{}/\\-—–«»“”")
        if not w_clean:
            return []

        w_lower = w_clean.lower()
        cached = self._suggestion_cache.get(w_lower)
        if cached is not None:
            if w_clean and w_clean[0].isupper():
                return [s.capitalize() for s in cached]
            return list(cached)

        res: list[str] = []

        # 1. Hunspell suggestions
        if self._hunspell is not None:
            try:
                sugs = list(self._hunspell.suggest(w_clean))
                if not sugs and w_clean != w_lower:
                    sugs = list(self._hunspell.suggest(w_lower))
                res = sugs[:5]
            except Exception as exc:
                log.debug("Error obteniendo sugerencias de hunspell para %s: %s", word, exc)

        # 2. pyspellchecker fallback
        if not res and self._checker is not None:
            try:
                res = sorted(self._checker.candidates(w_lower) or set())[:5]
            except Exception:
                pass

        # Guardar en caché
        self._suggestion_cache[w_lower] = list(res)

        if w_clean and w_clean[0].isupper():
            return [s.capitalize() for s in res]
        return res

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _check_text(self, text: str) -> list[SpellError]:
        """
        Analiza el texto plano y devuelve la lista completa de errores.
        Se ejecuta en el QThreadPool, NO en el hilo principal.
        """
        if not self._enabled or not text:
            return []
        if self._hunspell is None and self._checker is None:
            return []

        matches: list[tuple[str, int, int]] = []
        unique_unknowns: list[str] = []
        seen_unknowns: set[str] = set()

        for match in self._WORD_RE.finditer(text):
            word = match.group()
            if len(word) <= 1 or word.isdigit():
                continue

            if not self.check_word(word):
                matches.append((word, match.start(), match.end()))
                w_lower = word.lower()
                if w_lower not in seen_unknowns:
                    seen_unknowns.add(w_lower)
                    unique_unknowns.append(word)

        if not matches:
            return []

        # Precomputar sugerencias solo para las palabras únicas no cacheadas.
        # Límite alto (50) para que el menú contextual nunca tenga que calcularlas
        # síncronamente en el hilo principal (bug #6).
        _MAX_PRECOMPUTED = 50
        for w in unique_unknowns[:_MAX_PRECOMPUTED]:
            if w.lower() not in self._suggestion_cache:
                self.suggestions(w)

        errors: list[SpellError] = []
        for word, start, end in matches:
            errors.append(SpellError(
                word=word,
                start=start,
                end=end,
                suggestions=self.suggestions(word)
            ))

        return errors
