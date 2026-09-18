"""
engine.py — Motor de búsqueda y filtrado de texto en proyectos de Aura Writer.
"""

from typing import Callable, Generator
import re
from bs4 import BeautifulSoup


def escape_html(text: str) -> str:
    """Escapa caracteres HTML especiales."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def highlight_text(text: str, query: str, is_dark: bool = True, is_regex: bool = False) -> str:
    """Resalta las coincidencias de búsqueda con etiquetas HTML enriquecidas."""
    if not query:
        return escape_html(text)
    escaped = escape_html(text)
    try:
        pattern_str = query if is_regex else re.escape(query)
        pattern = re.compile(pattern_str, re.IGNORECASE)
    except re.error:
        pattern = re.compile(re.escape(query), re.IGNORECASE)

    if is_dark:
        hl_color = "#ffd60a"
        hl_bg = "#3a3a3c"
    else:
        hl_color = "#7c4a00"
        hl_bg = "#ffe08a"

    return pattern.sub(
        lambda m: (
            f"<b style='color:{hl_color}; background:{hl_bg};"
            f" padding:1px 3px; border-radius:3px;'>{escape_html(m.group())}</b>"
        ),
        escaped
    )


def extract_snippet(text: str, query: str, context: int = 60, is_regex: bool = False) -> str:
    """Extrae un extracto de texto centrado en la primera coincidencia encontrada."""
    if is_regex:
        try:
            m = re.search(query, text, re.IGNORECASE)
            if m:
                idx = m.start()
                q_len = max(1, m.end() - m.start())
            else:
                idx = -1
                q_len = len(query)
        except re.error:
            idx = text.lower().find(query.lower())
            q_len = len(query)
    else:
        idx = text.lower().find(query.lower())
        q_len = len(query)

    if idx == -1:
        return text[:120] + ("…" if len(text) > 120 else "")

    start = max(0, idx - context)
    end = min(len(text), idx + q_len + context)
    pre = "…" if start > 0 else ""
    suf = "…" if end < len(text) else ""
    return f"{pre}{text[start:end].replace(chr(10), ' ').strip()}{suf}"


class SearchEngine:
    """Motor de búsqueda en memoria para el universo actual."""

    def __init__(self, project_manager):
        self.pm = project_manager

    def search(self, query: str, scope: str = "Todo", is_regex: bool = False) -> list[dict]:
        """
        Ejecuta la búsqueda y retorna una lista de resultados con:
        {icon, title, location, snippet, item_id, item_type}
        """
        query = query.strip()
        if len(query) < 1 or not self.pm.metadata:
            return []

        compiled_regex = None
        if is_regex:
            try:
                compiled_regex = re.compile(query, re.IGNORECASE)
            except re.error:
                compiled_regex = None

        def matches(target_text: str) -> bool:
            if not target_text:
                return False
            if is_regex and compiled_regex:
                return bool(compiled_regex.search(target_text))
            return query.lower() in target_text.lower()

        results = []
        seen_ids: set[str] = set()

        # 1. Capítulos
        if scope in ("Todo", "Capítulos"):
            for obra in self.pm.metadata.obras:
                for libro in obra.libros:
                    for cap in libro.capitulos:
                        if cap.id in seen_ids:
                            continue
                        location = f"{obra.title} › {libro.title}"
                        in_title = matches(cap.title)

                        content = self.pm.read_chapter_content(cap.content_file)
                        try:
                            text = BeautifulSoup(content, "lxml").get_text()
                        except Exception:
                            text = content
                        in_content = matches(text)

                        if in_title or in_content:
                            seen_ids.add(cap.id)
                            snippet = (extract_snippet(text, query, is_regex=is_regex)
                                       if in_content else "Coincidencia en el título")
                            results.append({
                                "icon": "📖",
                                "title": cap.title,
                                "location": location,
                                "snippet": snippet,
                                "item_id": cap.id,
                                "item_type": "chapter"
                            })

        # 2. Personajes
        if scope in ("Todo", "Personajes"):
            for char in self.pm.metadata.characters:
                if char.id in seen_ids:
                    continue
                in_name = matches(char.name)
                in_desc = matches(char.description)
                in_role = matches(getattr(char, "role", ""))
                in_voice = matches(getattr(char, "distinctive_voice", ""))
                in_notes = matches(getattr(char, "notes", ""))

                if in_name or in_desc or in_role or in_voice or in_notes:
                    seen_ids.add(char.id)
                    full_desc = char.description or char.notes or f"Rol: {char.role}"
                    snippet = (extract_snippet(full_desc, query, is_regex=is_regex)
                               if not in_name else f"Rol: {char.role}")
                    results.append({
                        "icon": "👤",
                        "title": char.name,
                        "location": "Personajes",
                        "snippet": snippet,
                        "item_id": char.id,
                        "item_type": "character"
                    })

        # 3. Lugares y Escenarios
        if scope in ("Todo", "Lugares"):
            for place in getattr(self.pm.metadata, "places", []):
                if place.id in seen_ids:
                    continue
                in_name = matches(place.name)
                in_desc = matches(place.description)
                in_climate = matches(getattr(place, "climate_atmosphere", ""))
                in_sensory = matches(getattr(place, "sensory_details", ""))
                in_lore = matches(getattr(place, "lore_history", ""))
                in_notes = matches(getattr(place, "notes", ""))

                if in_name or in_desc or in_climate or in_sensory or in_lore or in_notes:
                    seen_ids.add(place.id)
                    all_text = " • ".join(filter(None, [place.description, place.climate_atmosphere, place.sensory_details, place.lore_history, place.notes]))
                    snippet = (extract_snippet(all_text, query, is_regex=is_regex)
                               if not in_name and all_text else f"Categoría: {place.category or 'Lugar'}")
                    results.append({
                        "icon": "🏰",
                        "title": place.name,
                        "location": f"Lugares ({place.category or 'General'})",
                        "snippet": snippet,
                        "item_id": place.id,
                        "item_type": "place"
                    })

        # 4. Notas de Autor (Nivel Capítulo y Nivel Universo/Obra)
        if scope in ("Todo", "Notas"):
            # Notas globales de Universo
            for note in getattr(self.pm.metadata, "author_notes", []):
                if note.id in seen_ids:
                    continue
                if matches(note.title) or matches(note.content):
                    seen_ids.add(note.id)
                    snippet = extract_snippet(note.content, query, is_regex=is_regex) if matches(note.content) else "Coincidencia en título"
                    results.append({
                        "icon": "📌",
                        "title": f"Nota de Universo: {note.title}",
                        "location": "Universo",
                        "snippet": snippet,
                        "item_id": self.pm.metadata.title,
                        "item_type": "universe"
                    })

            # Notas de Capítulos
            for obra in self.pm.metadata.obras:
                for libro in obra.libros:
                    for cap in libro.capitulos:
                        for note in cap.author_notes:
                            if note.id in seen_ids:
                                continue
                            in_title = matches(note.title)
                            in_body = matches(note.content)
                            if in_title or in_body:
                                seen_ids.add(note.id)
                                location = f"{obra.title} › {libro.title} › {cap.title}"
                                snippet = (extract_snippet(note.content, query, is_regex=is_regex)
                                           if in_body else "Coincidencia en el título")
                                results.append({
                                    "icon": "📌",
                                    "title": f"Nota: {note.title}",
                                    "location": location,
                                    "snippet": snippet,
                                    "item_id": cap.id,
                                    "item_type": "chapter"
                                })

        return results
