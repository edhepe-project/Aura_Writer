"""
_spacy_singleton.py — Cargador singleton de spaCy (thread-safe).
Responsabilidad única: cargar el modelo spaCy UNA sola vez y reutilizarlo.

Resuelve la ruta del modelo tanto en desarrollo normal como dentro
de un bundle PyInstaller (.exe), donde los archivos van en sys._MEIPASS.

Uso:
    from tools.nlp._spacy_singleton import get_nlp, is_spacy_available
    if is_spacy_available():
        nlp = get_nlp()
"""
from __future__ import annotations

import os
import sys
import logging
import threading
from typing import Optional

log = logging.getLogger(__name__)

# ── Thread lock para carga segura en contextos concurrentes ──────────────────
_lock = threading.Lock()
_nlp_instance = None          # instancia única del modelo
_load_attempted = False       # evitar reintentar si ya falló
_load_error: str = ""         # mensaje del error (si hubo)


def is_spacy_available() -> bool:
    """Retorna True si spaCy está instalado y el modelo está disponible."""
    try:
        import spacy  # noqa: F401
        return True
    except ImportError:
        return False


def get_nlp():
    """
    Retorna la instancia única del modelo spaCy (es_core_news_sm).

    - Carga el modelo solo la primera vez (~1-2 segundos).
    - Llamadas posteriores retornan la instancia en caché (instantáneo).
    - Thread-safe: usa un lock para evitar cargas paralelas.
    - Compatible con PyInstaller: detecta sys._MEIPASS automáticamente.

    Returns:
        spacy.Language: El modelo NLP listo para usar.

    Raises:
        RuntimeError: Si spaCy no está instalado o el modelo no se encontró.
    """
    global _nlp_instance, _load_attempted, _load_error

    # Fast-path: ya está cargado
    if _nlp_instance is not None:
        return _nlp_instance

    with _lock:
        # Double-check locking
        if _nlp_instance is not None:
            return _nlp_instance

        if _load_attempted and _load_error:
            raise RuntimeError(_load_error)

        _load_attempted = True
        try:
            _nlp_instance = _load_model()
            return _nlp_instance
        except Exception as err:
            _load_error = str(err)
            raise


def _load_model():
    """Carga el modelo es_core_news_sm con el tokenizador configurado para conlang."""
    try:
        import spacy
    except ImportError as e:
        msg = (
            "spaCy no está instalado. "
            "Instala con: pip install spacy"
        )
        log.error(msg)
        raise RuntimeError(msg) from e

    model_path = _resolve_model_path()

    try:
        if model_path and os.path.isdir(model_path):
            # Cargar desde ruta local (bundle PyInstaller o carpeta model/)
            log.info("Cargando spaCy desde: %s", model_path)
            nlp = spacy.load(model_path)
        else:
            # Cargar modelo instalado como paquete pip
            log.info("Cargando spaCy es_core_news_sm (instalado)")
            nlp = spacy.load("es_core_news_sm")
    except OSError as e:
        msg = (
            "Modelo spaCy 'es_core_news_sm' no encontrado. "
            "Instala con: python -m spacy download es_core_news_sm"
        )
        log.error(msg)
        raise RuntimeError(msg) from e

    # Configurar tokenizador para respetar · y ' dentro de palabras de conlang
    _configure_conlang_tokenizer(nlp)
    log.info("spaCy cargado correctamente (pipeline: %s)", nlp.pipe_names)
    return nlp


def _resolve_model_path() -> Optional[str]:
    """
    Resuelve la ruta del modelo según el entorno de ejecución.

    - Dentro de PyInstaller (.exe): usa sys._MEIPASS/es_core_news_sm
    - En desarrollo: busca src/tools/nlp/model/es_core_news_sm
    - Si no existe ninguna, retorna None (se usa el paquete pip)
    """
    # Entorno PyInstaller
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        bundled = os.path.join(sys._MEIPASS, "es_core_news_sm")
        if os.path.isdir(bundled):
            return bundled

    # Carpeta model/ junto a este archivo (desarrollo o build manual)
    here = os.path.dirname(os.path.abspath(__file__))
    local = os.path.join(here, "model", "es_core_news_sm")
    if os.path.isdir(local):
        return local

    return None


def _configure_conlang_tokenizer(nlp) -> None:
    """
    Configura el tokenizador de spaCy para NO partir en · y ' cuando
    están dentro de palabras de conlang (entre letras).

    Sin esta configuración, "vel·thar'an" se tokenizaría como
    ["vel", "·", "thar", "'", "an"] en lugar de ["vel·thar'an"].
    """
    try:
        from spacy.util import compile_infix_regex

        # Obtener las reglas de infijos actuales
        infixes = list(nlp.Defaults.infixes or [])

        # Eliminar reglas que parten en · (punto medio U+00B7)
        infixes = [r for r in infixes if "\u00b7" not in r and "·" not in r]

        # Añadir nueva regla: · solo es separador si NO está entre letras unicode
        # Esto preserva "vel·thar" como un token único
        infixes.append(r"(?<![^\W\d_])\xb7(?![^\W\d_])")

        nlp.tokenizer.infix_finditer = compile_infix_regex(infixes).finditer
        log.debug("Tokenizador conlang configurado correctamente")
    except Exception as e:
        # No fatal — spaCy puede tokenizar menos bien pero el pipeline sigue funcionando
        log.warning("No se pudo configurar el tokenizador conlang: %s", e)
