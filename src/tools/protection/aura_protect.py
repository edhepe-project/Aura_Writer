"""
Aura Writer — Aura Protect Module
Sistema de protección forense y firma criptográfica SHA-256 en metadatos de archivos.
"""

import hashlib
import os
import re
import zipfile
from datetime import datetime


def compute_manuscript_sha256(project_data: dict, author: str, title: str) -> str:
    """Calcula la firma criptográfica SHA-256 única del manuscrito y metadatos."""
    hasher = hashlib.sha256()
    hasher.update(title.encode("utf-8"))
    hasher.update(author.encode("utf-8"))

    items = project_data.get("items", project_data.get("chapters", []))
    for item in items:
        hasher.update(item.get("title", "").encode("utf-8"))
        hasher.update(item.get("content", "").encode("utf-8"))

    return hasher.hexdigest()


def create_protection_signature(author: str, title: str, sha256_hash: str) -> str:
    """Construye la firma compacta de protección para los metadatos."""
    timestamp = datetime.now().strftime("%Y-%m-%d")
    short_hash = sha256_hash[:12]
    return f"AURA-PROTECT|{author}|{title}|{short_hash}|{timestamp}"


def extract_watermark_from_text(text: str) -> str | None:
    """Busca la firma explícita AURA-PROTECT en un texto plano o HTML."""
    if not text:
        return None
    match = re.search(r"AURA-PROTECT\|[^\r\n\t]+", text)
    if match:
        return match.group(0).strip()
    return None


def extract_watermark_from_file(file_path: str) -> str | None:
    """
    Extrae la huella Aura Protect de los metadatos de un archivo exportado (PDF, DOCX, EPUB).
    """
    if not file_path or not os.path.exists(file_path):
        return None

    ext = os.path.splitext(file_path)[1].lower()

    # ── PDF ──────────────────────────────────────────────────────────────────
    if ext == ".pdf":
        try:
            with open(file_path, "rb") as fp:
                raw = fp.read()

            # Patrón 1: texto UTF-8 directo en Subject/Keywords/Info
            m = re.search(rb"AURA-PROTECT\|[^\r\n\x00\(\)<>\\\/\)]{5,}", raw)
            if m:
                return m.group(0).decode("utf-8", errors="ignore").strip()

            # Patrón 2: Latin-1
            raw_latin = raw.decode("latin-1", errors="ignore")
            m = re.search(r"AURA-PROTECT\|[^\r\n\x00\(\)<>\\\/]{5,}", raw_latin)
            if m:
                return m.group(0).strip()
        except Exception:
            pass

    # ── DOCX (archivo ZIP) ────────────────────────────────────────────────────
    elif ext == ".docx":
        try:
            with zipfile.ZipFile(file_path, "r") as z:
                for candidate in ("docProps/core.xml", "docProps/app.xml"):
                    if candidate in z.namelist():
                        content = z.read(candidate).decode("utf-8", errors="ignore")
                        m = re.search(r"AURA-PROTECT\|[^\r\n<]{5,}", content)
                        if m:
                            return m.group(0).strip()
        except Exception:
            pass

    # ── EPUB (archivo ZIP) ────────────────────────────────────────────────────
    elif ext == ".epub":
        try:
            with zipfile.ZipFile(file_path, "r") as z:
                for name in z.namelist():
                    if name.endswith(".opf") or name.endswith("content.opf"):
                        content = z.read(name).decode("utf-8", errors="ignore")
                        m = re.search(r"AURA-PROTECT\|[^\r\n<]{5,}", content)
                        if m:
                            return m.group(0).strip()
        except Exception:
            pass

    # ── Fallback: búsqueda binaria general ───────────────────────────────────
    try:
        with open(file_path, "rb") as fp:
            raw = fp.read()
        m = re.search(rb"AURA-PROTECT\|[^\r\n\x00]{5,}", raw)
        if m:
            return m.group(0).decode("utf-8", errors="ignore").strip()
    except Exception:
        pass

    return None


def strip_zero_width_chars(text: str) -> str:
    """Limpia cualquier carácter de ancho cero remanente."""
    if not text:
        return ""
    return re.sub(r"[\u200b\u200c\ufeff]", "", text)
