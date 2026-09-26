"""
Aura Writer — EPUB Exporter Module
Generación de libros electrónicos estándar EPUB3 con CSS editorial optimizado para e-readers.
"""

import os
import uuid
from bs4 import BeautifulSoup
from ebooklib import epub

from tools.exporters.base_exporter import clean_html
from tools.protection.aura_protect import strip_zero_width_chars


class EPUBExporter:
    """Motor de exportación de libros digitales EPUB3."""

    def __init__(self, meta: dict, temp_dir: str):
        self.meta = meta
        self.temp_dir = temp_dir

    def export(self, project_data: dict, output_path: str):
        """Genera el libro electrónico en formato EPUB3."""
        book = epub.EpubBook()
        book.set_identifier(str(uuid.uuid4()))
        book.set_title(self.meta.get("title", "Obra"))
        book.set_language(self.meta.get("language", "es"))
        book.add_author(self.meta.get("author", "Autor"))

        sig = project_data.get("protection_signature", "")
        if sig:
            book.add_metadata("DC", "rights", f"Aura Protect: {sig}")

        css_content = """
            body {
                font-family: 'Georgia', 'Times New Roman', 'Palatino Linotype', serif;
                line-height: 1.5;
                color: #2c2416;
                margin: 1.5em 1em;
                background: #fefcf8;
            }

            .chapter-label {
                text-align: center;
                font-size: 0.75em;
                color: #9a8e80;
                letter-spacing: 0.2em;
                text-transform: uppercase;
                margin-top: 4em;
                margin-bottom: 0.3em;
            }

            h1 {
                text-align: center;
                font-size: 1.4em;
                font-weight: 700;
                color: #2c2416;
                margin-top: 0.3em;
                margin-bottom: 0.5em;
                letter-spacing: 0.02em;
            }

            .chapter-ornament {
                text-align: center;
                color: #c0b8a8;
                font-size: 0.9em;
                margin-bottom: 2em;
            }

            p {
                text-indent: 1.5em;
                margin-top: 0;
                margin-bottom: 0;
                text-align: justify;
            }

            p.first-p {
                text-indent: 0;
            }

            p.blank-line {
                text-indent: 0;
                text-align: center;
                margin: 1.2em 0;
                color: #c0b8a8;
            }

            .author-note {
                font-style: italic;
                color: #8c7b6b;
                font-size: 0.9em;
                margin-top: 1.5em;
                border-top: 1px solid #e8e2d8;
                padding-top: 0.5em;
                text-indent: 0;
                text-align: left;
            }

            .running-header {
                text-align: center;
                color: #c0b8a8;
                font-size: 0.7em;
                font-style: italic;
                margin-bottom: 2em;
                letter-spacing: 0.1em;
                border-bottom: 1px solid #e8e2d8;
                padding-bottom: 0.8em;
            }
        """
        nav_css = epub.EpubItem(
            uid="style_default",
            file_name="style/default.css",
            media_type="text/css",
            content=css_content
        )
        book.add_item(nav_css)

        chapters = []
        media_counter = 0
        numbered_chapter_count = 0

        special_sections = [
            "prólogo", "prologo", "epílogo", "epilogo", "introducción", "introduccion",
            "prefacio", "nota del autor", "agradecimientos", "dedicatoria", "apéndice", "apendice"
        ]

        for i, item in enumerate(project_data.get("chapters", [])):
            content_soup_e = BeautifulSoup(item.get("content", ""), "lxml")
            html_heading_e = content_soup_e.find(["h1", "h2", "h3"])
            chapter_title_e = html_heading_e.get_text(strip=True) if html_heading_e else item.get("title", "")
            chapter_title_e = chapter_title_e.strip()
            libro_label_e = item.get("libro_title", "").strip()

            title_lower = chapter_title_e.lower()
            is_special = any(spec in title_lower for spec in special_sections)

            if not is_special and not title_lower.startswith("capítulo") and not title_lower.startswith("capitulo"):
                numbered_chapter_count += 1

            display_title = chapter_title_e if chapter_title_e else f"Capítulo {numbered_chapter_count}"

            chapter = epub.EpubHtml(title=display_title, file_name=f"chap_{i}.xhtml", lang="es")
            chapter.add_item(nav_css)

            html_parts = []
            html_parts.append(f'<p class="running-header">&mdash; {display_title} &mdash;</p>\n')

            if libro_label_e:
                html_parts.append(f'<p class="chapter-label">{libro_label_e}</p>\n')
            html_parts.append(f'<h1>{display_title}</h1>\n')
            html_parts.append('<p class="chapter-ornament">— ❧ —</p>\n')

            for m in item.get("medias", []):
                if m.get("position") == "before":
                    html_parts.append(self._media_html(book, m, media_counter))
                    media_counter += 1

            content_html = item.get("content", "")
            content_soup = BeautifulSoup(content_html, "lxml")
            content_paragraphs = content_soup.find_all(["p", "h1", "h2", "h3"])

            is_first = True
            first_heading_skipped_e = False
            for p in content_paragraphs:
                text = strip_zero_width_chars(p.get_text(strip=True))
                if not text:
                    continue

                if p.name in ("h1", "h2", "h3") and not first_heading_skipped_e:
                    first_heading_skipped_e = True
                    continue

                if "[ Página en Blanco ]" in text or "[ Página en blanco ]" in text or "página en blanco" in text.lower():
                    html_parts.append('<div style="page-break-after:always; height:1px;"></div>\n')
                    is_first = True
                    continue

                if "Salto de Página" in text or "salto de página" in text.lower() or "page-break-after" in str(p.get("style", "")):
                    html_parts.append('<div style="page-break-after:always; height:1px;"></div>\n')
                    is_first = True
                    continue

                if text.strip() in ("***", "* * *", "---", "———", "• • •", "⁂"):
                    html_parts.append('<p class="chapter-ornament">— ❧ —</p>\n')
                    is_first = True
                    continue

                cls = ' class="first-p"' if is_first else ''
                html_parts.append(f'<p{cls}>{text}</p>\n')
                is_first = False

            for m in item.get("medias", []):
                if m.get("position") in ("after", "inline"):
                    html_parts.append(self._media_html(book, m, media_counter))
                    media_counter += 1

            for note_text in item.get("author_notes", []):
                if note_text:
                    html_parts.append(f'<p class="author-note">📌 Nota del autor: {note_text}</p>\n')

            chapter.content = "".join(html_parts)
            book.add_item(chapter)
            chapters.append(chapter)

        book.toc = tuple(chapters)
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = ["nav"] + chapters

        epub.write_epub(output_path, book, {})
        return True, f"Libro electrónico EPUB3 generado en: {output_path}"

    def _media_html(self, book, m, index: int) -> str:
        path = m.get("path", "")
        if not os.path.exists(path):
            return ""
        try:
            ext = os.path.splitext(path)[1].lower()
            media_type = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
            with open(path, "rb") as fp:
                img_data = fp.read()
            filename = f"images/img_{index}{ext}"
            image_item = epub.EpubItem(
                uid=f"img_{index}",
                file_name=filename,
                media_type=media_type,
                content=img_data
            )
            book.add_item(image_item)
            caption_html = f'<p class="chapter-label" style="margin-top:0.5em;">{m["caption"]}</p>' if m.get("caption") else ""
            return f'<div style="text-align:center; margin:1em 0;"><img src="{filename}" style="max-width:100%; height:auto;" />{caption_html}</div>\n'
        except Exception:
            return ""
