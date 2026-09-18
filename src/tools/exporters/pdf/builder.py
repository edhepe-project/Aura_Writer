"""
builder.py — Generador principal del documento PDF A5 para novelas de Aura Writer.
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    Paragraph, Spacer, PageBreak, BaseDocTemplate,
    Image as RLImage, NextPageTemplate
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT

from tools.exporters.base_exporter import _COLORS, clean_html
from tools.exporters.pdf.flowables import (
    OrnamentalRule, DecorativeLine, ChapterMarker
)
from tools.exporters.pdf.styles import get_pdf_styles
from tools.exporters.pdf.templates import create_page_templates


class PDFExporter:
    """Motor de exportación PDF editorial en formato A5."""

    def __init__(self, meta: dict, temp_dir: str):
        self.meta = meta
        self.temp_dir = temp_dir

    def export(self, project_data: dict, output_path: str) -> tuple[bool, str]:
        """Genera el documento PDF A5 profesional con ReportLab."""
        doc = BaseDocTemplate(
            output_path,
            pagesize=A5,
            rightMargin=18 * mm,
            leftMargin=22 * mm,
            topMargin=22 * mm,
            bottomMargin=20 * mm,
        )

        book_title = self.meta.get("title", "Obra")
        book_author = self.meta.get("author", "")

        templates, text_width = create_page_templates(book_title)
        doc.addPageTemplates(templates)

        st = get_pdf_styles(text_width)
        story = []

        # Front Matter
        story.append(NextPageTemplate("BlankPage"))
        story.append(Spacer(1, A5[1] * 0.28))
        story.append(DecorativeLine(text_width, color=_COLORS["accent_light"], thickness=0.6, width_ratio=0.4))
        story.append(Spacer(1, 8))
        story.append(Paragraph(book_title.upper(), st["cover_title"]))
        story.append(Spacer(1, 6))
        story.append(DecorativeLine(text_width, color=_COLORS["accent_light"], thickness=0.6, width_ratio=0.4))

        if book_author:
            story.append(Spacer(1, 24))
            story.append(Paragraph(book_author, st["cover_author"]))

        # Copyright / Legal
        story.append(PageBreak())
        story.append(Spacer(1, A5[1] * 0.65))
        year = datetime.now().year
        legal_lines = [
            f"© {year} {book_author}" if book_author else f"© {year}",
            "Todos los derechos reservados.",
            "",
            "Generado con Aura Writer",
            f"{datetime.now().strftime('%d de %B de %Y')}",
        ]
        for line in legal_lines:
            if line:
                story.append(Paragraph(line, st["legal"]))
            else:
                story.append(Spacer(1, 6))

        # Half-Title
        story.append(PageBreak())
        story.append(Spacer(1, A5[1] * 0.35))
        story.append(Paragraph(book_title, st["half_title"]))
        story.append(Spacer(1, 10))
        story.append(DecorativeLine(text_width, color=_COLORS["accent_light"], thickness=0.4, width_ratio=0.25))

        # Body items
        img_margin = 10 * mm
        img_bottom = 18 * mm
        avail_img_width = A5[0] - 2 * img_margin
        avail_img_height = A5[1] - img_margin - img_bottom - 20
        avail_width = text_width

        items = project_data.get("items", project_data.get("chapters", []))
        chapter_number = 0

        for item in items:
            item_type = item.get("type", "chapter")

            if item_type == "full_page_media":
                img_path = item.get("path", "")
                if not img_path or not os.path.exists(img_path):
                    continue

                story.append(NextPageTemplate("ImagePage"))
                story.append(PageBreak())
                try:
                    img = RLImage(img_path)
                    iw, ih = img.drawWidth, img.drawHeight
                    scale_w = avail_img_width / iw
                    scale_h = avail_img_height / ih
                    scale = min(scale_w, scale_h)
                    img.drawWidth = iw * scale
                    img.drawHeight = ih * scale
                    img.hAlign = "CENTER"
                    story.append(img)
                    caption = item.get("caption", "")
                    if caption:
                        story.append(Paragraph(f"<i>{caption}</i>", st["fullpage_caption"]))
                except Exception:
                    pass
                story.append(NextPageTemplate("ChapterStart"))

            else:
                chapter_number += 1
                content_soup_title = clean_html(item.get("content", ""))
                html_heading = content_soup_title.find(["h1", "h2", "h3"])
                chapter_title = html_heading.get_text(strip=True) if html_heading else item.get("title", f"Capítulo {chapter_number}")
                libro_label = item.get("libro_title", "").strip()

                story.append(ChapterMarker(chapter_title))
                story.append(NextPageTemplate("ChapterStart"))
                story.append(PageBreak())
                story.append(NextPageTemplate("ContentPage"))
                story.append(Spacer(1, 28))

                if libro_label:
                    story.append(Paragraph(libro_label.upper(), st["chapter_label"]))

                story.append(Paragraph(chapter_title, st["chapter_title"]))
                story.append(OrnamentalRule(
                    avail_width,
                    ornament="❧",
                    color=_COLORS["accent"],
                    thickness=0.4,
                    rule_width_ratio=0.25,
                    space_before=4,
                    space_after=18,
                ))

                for m in item.get("medias", []):
                    if m.get("position") == "before" and os.path.exists(m.get("path", "")):
                        story.extend(self._media_block(m, avail_width, st["caption"]))

                soup = clean_html(item.get("content", ""))
                paragraphs = soup.find_all(["p", "h1", "h2", "h3"])

                is_first_para = True
                first_heading_skipped = False
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if not text:
                        continue

                    if p.name in ("h1", "h2", "h3") and not first_heading_skipped:
                        first_heading_skipped = True
                        continue

                    # Detección de Página en Blanco y Salto de Página
                    if "[ Página en Blanco ]" in text or "[ Página en blanco ]" in text or "página en blanco" in text.lower():
                        story.append(NextPageTemplate("BlankPage"))
                        story.append(PageBreak())
                        story.append(Spacer(1, 40))
                        story.append(NextPageTemplate("ContentPage"))
                        story.append(PageBreak())
                        is_first_para = True
                        continue

                    if "Salto de Página" in text or "salto de página" in text.lower() or "page-break-after" in str(p.get("style", "")):
                        story.append(PageBreak())
                        is_first_para = True
                        continue

                    if text.strip() in ("***", "* * *", "---", "———", "• • •", "⁂"):
                        story.append(Spacer(1, 8))
                        story.append(OrnamentalRule(
                            avail_width,
                            ornament="✦",
                            color=_COLORS["accent_light"],
                            thickness=0.3,
                            rule_width_ratio=0.2,
                            space_before=6,
                            space_after=6,
                        ))
                        story.append(Spacer(1, 8))
                        is_first_para = True
                        continue

                    if p.name in ("h2", "h3"):
                        sub_style = ParagraphStyle(
                            "SubHeading",
                            fontName="Times-Bold",
                            fontSize=12 if p.name == "h2" else 11,
                            leading=16,
                            alignment=TA_LEFT,
                            textColor=HexColor(_COLORS["text_primary"]),
                            spaceBefore=16,
                            spaceAfter=8,
                        )
                        story.append(Paragraph(text, sub_style))
                        is_first_para = True
                        continue

                    style = st["body_first"] if is_first_para else st["body"]
                    story.append(Paragraph(text, style))
                    is_first_para = False

                for m in item.get("medias", []):
                    if m.get("position") in ("after", "inline") and os.path.exists(m.get("path", "")):
                        story.extend(self._media_block(m, avail_width, st["caption"]))

                for note_text in item.get("author_notes", []):
                    if note_text:
                        story.append(Paragraph(f"<i>Nota del autor — {note_text}</i>", st["note"]))

        try:
            doc.build(story)
            return True, f"PDF Profesional generado en: {output_path}"
        except Exception as e:
            return False, f"Error en PDF: {e}"

    def _media_block(self, m, avail_width, st_caption):
        elements = []
        try:
            img = RLImage(m["path"])
            iw, ih = img.drawWidth, img.drawHeight
            max_w = avail_width * 0.85
            if iw > max_w:
                ratio = max_w / iw
                img.drawWidth = max_w
                img.drawHeight = ih * ratio
            img.hAlign = "CENTER"
            elements.append(Spacer(1, 10))
            elements.append(img)
            if m.get("caption"):
                elements.append(Paragraph(f"<i>{m['caption']}</i>", st_caption))
            elements.append(Spacer(1, 10))
        except Exception:
            pass
        return elements
