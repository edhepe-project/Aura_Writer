"""
Aura Writer — EPUB Exporter Module
Generación de libros electrónicos estándar EPUB3 con CSS editorial optimizado para e-readers.
"""

import os
import uuid
from bs4 import BeautifulSoup
from ebooklib import epub


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

        css_content = """
            @import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&display=swap');

            body {
                font-family: 'Libre Baskerville', 'Georgia', serif;
                line-height: 1.7;
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
                font-size: 1.1em;
                margin-bottom: 2em;
                letter-spacing: 0.5em;
            }

            p {
                text-indent: 1.5em;
                margin: 0;
                padding: 0;
                text-align: justify;
                hyphens: auto;
                -webkit-hyphens: auto;
            }

            p.first-paragraph {
                text-indent: 0;
            }

            p.first-paragraph::first-letter {
                font-size: 3.2em;
                float: left;
                line-height: 0.85;
                padding-right: 0.08em;
                padding-top: 0.05em;
                font-weight: 700;
                color: #6b5d4f;
            }

            .scene-break {
                text-align: center;
                color: #c0b8a8;
                font-size: 0.9em;
                margin: 1.8em 0;
                letter-spacing: 0.4em;
            }

            figure {
                text-align: center;
                margin: 2em auto;
                page-break-inside: avoid;
            }

            figure img {
                max-width: 90%;
                border-radius: 2px;
            }

            figcaption {
                font-style: italic;
                color: #7a6e60;
                font-size: 0.85em;
                margin-top: 0.6em;
                letter-spacing: 0.02em;
            }

            aside.author-note {
                background: #f8f5f0;
                border-left: 3px solid #b8a88a;
                padding: 1em 1.2em;
                margin: 2em 0;
                font-style: italic;
                font-size: 0.88em;
                color: #6b5d4f;
                border-radius: 0 4px 4px 0;
            }

            aside.author-note p {
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
        chapter_num = 0

        for i, item in enumerate(project_data.get("chapters", [])):
            chapter_num += 1

            content_soup_e = BeautifulSoup(item.get("content", ""), "lxml")
            html_heading_e = content_soup_e.find(["h1", "h2", "h3"])
            chapter_title_e = html_heading_e.get_text(strip=True) if html_heading_e else item.get("title", f"Capítulo {chapter_num}")
            libro_label_e = item.get("libro_title", "").strip()

            chapter = epub.EpubHtml(title=chapter_title_e, file_name=f"chap_{i}.xhtml", lang="es")
            chapter.add_item(nav_css)

            html_parts = []
            html_parts.append(f'<p class="running-header">&mdash; {chapter_title_e} &mdash;</p>\n')

            if libro_label_e:
                html_parts.append(f'<p class="chapter-label">{libro_label_e}</p>\n')
            html_parts.append(f'<h1>{chapter_title_e}</h1>\n')
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
                text = p.get_text(strip=True)
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
                    html_parts.append('<p class="scene-break">✦ &nbsp; ✦ &nbsp; ✦</p>\n')
                    is_first = True
                    continue

                if p.name in ("h2", "h3"):
                    html_parts.append(f'<h2>{text}</h2>\n')
                    is_first = True
                    continue

                if is_first:
                    html_parts.append(f'<p class="first-paragraph">{text}</p>\n')
                    is_first = False
                else:
                    html_parts.append(f'<p>{text}</p>\n')

            for m in item.get("medias", []):
                if m.get("position") in ("after", "inline"):
                    html_parts.append(self._media_html(book, m, media_counter))
                    media_counter += 1

            for note_text in item.get("author_notes", []):
                if note_text:
                    html_parts.append(
                        f'<aside class="author-note"><p>Nota del autor — {note_text}</p></aside>'
                    )

            chapter.content = "\n".join(html_parts)
            chapter.add_item(nav_css)
            book.add_item(chapter)
            chapters.append(chapter)

        book.toc = tuple(chapters)
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = ["nav"] + chapters

        epub.write_epub(output_path, book, {})
        return True, f"EPUB generado en: {output_path}"

    def _media_html(self, book, m, counter):
        path = m.get("path", "")
        if not os.path.exists(path):
            return ""
        try:
            ext = os.path.splitext(path)[1].lower()
            media_types = {
                ".png": "image/png", ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg", ".gif": "image/gif",
                ".webp": "image/webp"
            }
            mt = media_types.get(ext, "image/png")
            fname = f"images/media_{counter}{ext}"

            with open(path, "rb") as f:
                img_data = f.read()

            img_item = epub.EpubItem(
                uid=f"media_{counter}",
                file_name=fname,
                media_type=mt,
                content=img_data
            )
            book.add_item(img_item)

            caption_html = f"<figcaption>{m['caption']}</figcaption>" if m.get("caption") else ""
            return f'<figure><img src="{fname}" alt="{m.get("caption", "")}" />{caption_html}</figure>'
        except Exception:
            return ""
