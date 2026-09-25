"""
diff_engine.py — Motor de cálculo y formateo de diferencias (Diff) para texto literario.

Soporta:
- Comparación palabra por palabra y línea por línea con `difflib`.
- Formateo enriquecido en HTML con estilos visuales modernos (<ins> verde y <del> rojo).
- Modo inline y modo comparativa side-by-side.
- Extracción de estadísticas de edición (palabras añadidas, eliminadas, modificadas).
"""

from __future__ import annotations
import difflib
import html
import re
from dataclasses import dataclass
from bs4 import BeautifulSoup


@dataclass
class DiffStats:
    words_added: int = 0
    words_deleted: int = 0
    words_unchanged: int = 0
    characters_added: int = 0
    characters_deleted: int = 0


class DiffEngine:
    """Motor de cálculo y renderizado de diferencias entre versiones de texto."""

    @staticmethod
    def html_to_plain_text(html_content: str) -> str:
        """Extrae texto legible respetando los saltos de línea y párrafos de un HTML."""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, "html.parser")
        # Reemplazar <p>, <br>, <h1>..<h6> con saltos de línea
        for tag in soup.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6", "div"]):
            tag.append("\n")
        for br in soup.find_all("br"):
            br.replace_with("\n")
        return soup.get_text()

    @classmethod
    def compute_inline_diff_html(
        cls,
        old_text: str,
        new_text: str,
        theme_name: str = "dark"
    ) -> tuple[str, DiffStats]:
        """
        Genera un documento HTML con diferencias semánticas resaltadas:
        - Inserciones en verde (<ins>)
        - Eliminaciones en rojo tachado (<del>)
        """
        # Extraer texto si es HTML
        old_raw = cls.html_to_plain_text(old_text) if "<" in old_text and ">" in old_text else old_text
        new_raw = cls.html_to_plain_text(new_text) if "<" in new_text and ">" in new_text else new_text

        # Tokenizar en palabras y puntuación manteniendo espacios
        old_tokens = re.findall(r'\S+|\s+', old_raw)
        new_tokens = re.findall(r'\S+|\s+', new_raw)

        matcher = difflib.SequenceMatcher(None, old_tokens, new_tokens)
        stats = DiffStats()

        out_fragments: list[str] = []

        # Paleta de colores elegante adaptada al tema
        is_sepia = theme_name == "sepia"
        is_light = theme_name == "light"
        
        if is_sepia:
            ins_bg = "#ebdcb9"
            ins_fg = "#5c4d41"
            del_bg = "#d9b3a8"
            del_fg = "#8c3123"
        elif is_light:
            ins_bg = "#d4edda"
            ins_fg = "#155724"
            del_bg = "#f8d7da"
            del_fg = "#721c24"
        else:
            ins_bg = "#1a3d24"
            ins_fg = "#4cd964"
            del_bg = "#4d1919"
            del_fg = "#ff453a"

        ins_style = f"background-color: {ins_bg}; color: {ins_fg}; text-decoration: none; border-radius: 3px; padding: 1px 3px; font-weight: bold;"
        del_style = f"background-color: {del_bg}; color: {del_fg}; text-decoration: line-through; border-radius: 3px; padding: 1px 3px;"

        for opcode, a0, a1, b0, b1 in matcher.get_opcodes():
            if opcode == "equal":
                text_equal = "".join(old_tokens[a0:a1])
                escaped = html.escape(text_equal).replace("\n", "<br>")
                out_fragments.append(escaped)
                word_count = len([t for t in old_tokens[a0:a1] if t.strip()])
                stats.words_unchanged += word_count
            elif opcode == "insert":
                text_ins = "".join(new_tokens[b0:b1])
                escaped = html.escape(text_ins).replace("\n", "<br>")
                out_fragments.append(f'<ins style="{ins_style}">{escaped}</ins>')
                word_count = len([t for t in new_tokens[b0:b1] if t.strip()])
                stats.words_added += word_count
                stats.characters_added += len(text_ins)
            elif opcode == "delete":
                text_del = "".join(old_tokens[a0:a1])
                escaped = html.escape(text_del).replace("\n", "<br>")
                out_fragments.append(f'<del style="{del_style}">{escaped}</del>')
                word_count = len([t for t in old_tokens[a0:a1] if t.strip()])
                stats.words_deleted += word_count
                stats.characters_deleted += len(text_del)
            elif opcode == "replace":
                text_del = "".join(old_tokens[a0:a1])
                escaped_del = html.escape(text_del).replace("\n", "<br>")
                out_fragments.append(f'<del style="{del_style}">{escaped_del}</del>')
                
                text_ins = "".join(new_tokens[b0:b1])
                escaped_ins = html.escape(text_ins).replace("\n", "<br>")
                out_fragments.append(f'<ins style="{ins_style}">{escaped_ins}</ins>')

                del_words = len([t for t in old_tokens[a0:a1] if t.strip()])
                ins_words = len([t for t in new_tokens[b0:b1] if t.strip()])
                stats.words_deleted += del_words
                stats.words_added += ins_words
                stats.characters_deleted += len(text_del)
                stats.characters_added += len(text_ins)

        if is_sepia:
            font_color = "#2d241e"
            bg_color = "#f4ecd8"
        elif is_light:
            font_color = "#1c1c1e"
            bg_color = "#fafafa"
        else:
            font_color = "#e5e5ea"
            bg_color = "#18181b"

        body_html = "".join(out_fragments)
        full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body {{
    font-family: 'Georgia', serif;
    font-size: 15px;
    line-height: 1.7;
    color: {font_color};
    background-color: {bg_color};
    padding: 16px;
    margin: 0;
}}
</style>
</head>
<body>
{body_html}
</body>
</html>"""
        return full_html, stats
