"""
Aura Writer — PDF Exporter Module
Maquetación profesional en tamaño A5 con ReportLab: cabeceras vivas, drop caps, reglas ornamentales y paginación.
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    Paragraph, Spacer, PageBreak, BaseDocTemplate, Frame,
    PageTemplate, Image as RLImage, Flowable, NextPageTemplate
)
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT

from tools.exporters.base_exporter import _COLORS, clean_html


# ======================================================================
# Flowables Decorativos
# ======================================================================

class OrnamentalRule(Flowable):
    """Regla horizontal decorativa con ornamento central."""
    def __init__(self, width, ornament="✦", color="#8c7b6b", thickness=0.5,
                 rule_width_ratio=0.35, space_before=12, space_after=12):
        super().__init__()
        self.width = width
        self.ornament = ornament
        self.color = HexColor(color)
        self.thickness = thickness
        self.rule_width_ratio = rule_width_ratio
        self.spaceBefore = space_before
        self.spaceAfter = space_after
        self.height = 20

    def draw(self):
        canvas = self.canv
        canvas.saveState()
        y_mid = self.height / 2

        rule_len = self.width * self.rule_width_ratio
        gap = 8

        canvas.setStrokeColor(self.color)
        canvas.setLineWidth(self.thickness)

        # Línea izquierda
        x_left_start = (self.width - 2 * rule_len - 2 * gap) / 2
        canvas.line(x_left_start, y_mid, x_left_start + rule_len, y_mid)

        # Línea derecha
        x_right_start = self.width / 2 + gap
        canvas.line(x_right_start, y_mid, x_right_start + rule_len, y_mid)

        # Ornamento central
        canvas.setFillColor(self.color)
        canvas.setFont("Times-Roman", 10)
        canvas.drawCentredString(self.width / 2, y_mid - 3, self.ornament)

        canvas.restoreState()


class DecorativeLine(Flowable):
    """Línea horizontal delgada decorativa."""
    def __init__(self, width, color="#c0b8a8", thickness=0.4, width_ratio=0.6):
        super().__init__()
        self.width = width
        self.color = HexColor(color)
        self.thickness = thickness
        self.width_ratio = width_ratio
        self.height = 8

    def draw(self):
        canvas = self.canv
        canvas.saveState()
        canvas.setStrokeColor(self.color)
        canvas.setLineWidth(self.thickness)
        line_w = self.width * self.width_ratio
        x_start = (self.width - line_w) / 2
        canvas.line(x_start, self.height / 2, x_start + line_w, self.height / 2)
        canvas.restoreState()


class ChapterMarker(Flowable):
    """Flowable invisible que actualiza el título del capítulo para running headers."""
    width = 0
    height = 0

    def __init__(self, title):
        super().__init__()
        self._title = title

    def draw(self):
        self.canv._current_chapter_title = self._title


class PDFExporter:
    """Motor de exportación PDF editorial en formato A5."""

    def __init__(self, meta: dict, temp_dir: str):
        self.meta = meta
        self.temp_dir = temp_dir
        self.styles = getSampleStyleSheet()

    def build_styles(self, avail_width):
        """Genera los estilos tipográficos para la novela en PDF."""
        s = {}
        s["body"] = ParagraphStyle(
            "AuraBody",
            fontName="Times-Roman",
            fontSize=10.5,
            leading=15,
            alignment=TA_JUSTIFY,
            firstLineIndent=4*mm,
            textColor=HexColor(_COLORS["text_primary"]),
            spaceBefore=0,
            spaceAfter=1,
        )
        s["body_first"] = ParagraphStyle(
            "AuraBodyFirst",
            parent=s["body"],
            firstLineIndent=0,
        )
        s["cover_title"] = ParagraphStyle(
            "CoverTitle",
            fontName="Times-Bold",
            fontSize=26,
            leading=32,
            alignment=TA_CENTER,
            textColor=HexColor(_COLORS["text_primary"]),
            spaceAfter=6,
        )
        s["cover_subtitle"] = ParagraphStyle(
            "CoverSubtitle",
            fontName="Times-Italic",
            fontSize=13,
            leading=18,
            alignment=TA_CENTER,
            textColor=HexColor(_COLORS["text_secondary"]),
            spaceAfter=4,
        )
        s["cover_author"] = ParagraphStyle(
            "CoverAuthor",
            fontName="Times-Roman",
            fontSize=14,
            leading=20,
            alignment=TA_CENTER,
            textColor=HexColor(_COLORS["text_secondary"]),
            spaceBefore=8,
            spaceAfter=0,
        )
        s["chapter_label"] = ParagraphStyle(
            "ChapterLabel",
            fontName="Times-Roman",
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            textColor=HexColor(_COLORS["text_muted"]),
            spaceBefore=0,
            spaceAfter=4,
        )
        s["chapter_title"] = ParagraphStyle(
            "ChapterTitle",
            fontName="Times-Bold",
            fontSize=18,
            leading=24,
            alignment=TA_CENTER,
            textColor=HexColor(_COLORS["text_primary"]),
            spaceBefore=4,
            spaceAfter=8,
        )
        s["caption"] = ParagraphStyle(
            "AuraCaption",
            fontName="Times-Italic",
            fontSize=8.5,
            leading=12,
            alignment=TA_CENTER,
            textColor=HexColor(_COLORS["caption"]),
            spaceBefore=4,
            spaceAfter=10,
        )
        s["fullpage_caption"] = ParagraphStyle(
            "FullPageCaption",
            fontName="Times-Italic",
            fontSize=9,
            leading=13,
            alignment=TA_CENTER,
            textColor=HexColor(_COLORS["caption"]),
            spaceBefore=6,
            spaceAfter=0,
        )
        s["note"] = ParagraphStyle(
            "AuthorNote",
            fontName="Times-Italic",
            fontSize=9.5,
            leading=13.5,
            alignment=TA_JUSTIFY,
            firstLineIndent=3*mm,
            textColor=HexColor(_COLORS["text_secondary"]),
            backColor=HexColor(_COLORS["note_bg"]),
            borderLeftWidth=2,
            borderLeftColor=HexColor(_COLORS["note_border"]),
            borderPadding=10,
            spaceBefore=14,
            spaceAfter=14,
        )
        s["legal"] = ParagraphStyle(
            "Legal",
            fontName="Times-Roman",
            fontSize=8,
            leading=11,
            alignment=TA_CENTER,
            textColor=HexColor(_COLORS["text_muted"]),
            spaceBefore=2,
            spaceAfter=2,
        )
        s["half_title"] = ParagraphStyle(
            "HalfTitle",
            fontName="Times-Italic",
            fontSize=16,
            leading=22,
            alignment=TA_CENTER,
            textColor=HexColor(_COLORS["text_secondary"]),
        )
        return s

    def export(self, project_data: dict, output_path: str):
        """Genera el documento PDF A5 profesional con ReportLab."""
        doc = BaseDocTemplate(
            output_path,
            pagesize=A5,
            rightMargin=18*mm,
            leftMargin=22*mm,
            topMargin=22*mm,
            bottomMargin=20*mm,
        )

        book_title = self.meta.get("title", "Obra")
        book_author = self.meta.get("author", "")

        # Frames
        text_left = 22*mm
        text_right = 18*mm
        text_top = 22*mm
        text_bottom = 20*mm
        text_width = A5[0] - text_left - text_right
        text_height = A5[1] - text_top - text_bottom

        frame_text = Frame(text_left, text_bottom, text_width, text_height, id="text")
        frame_text2 = Frame(text_left, text_bottom, text_width, text_height, id="text2")
        frame_blank = Frame(text_left, text_bottom, text_width, text_height, id="blank_frame")

        img_margin = 10*mm
        img_bottom = 18*mm
        frame_img = Frame(img_margin, img_bottom,
                          A5[0] - 2*img_margin,
                          A5[1] - img_margin - img_bottom,
                          id="fullpage_img")

        def on_blank_page(canvas, doc):
            pass

        def on_chapter_start(canvas, doc):
            canvas.saveState()
            canvas.setFont("Times-Roman", 8)
            canvas.setFillColor(HexColor(_COLORS["page_number"]))
            canvas.drawCentredString(A5[0]/2, 10*mm, str(doc.page))
            canvas.restoreState()

        def on_content_page(canvas, doc):
            canvas.saveState()
            canvas.setFont("Times-Roman", 8)
            canvas.setFillColor(HexColor(_COLORS["page_number"]))
            canvas.drawCentredString(A5[0]/2, 10*mm, str(doc.page))

            header_text = getattr(canvas, '_current_chapter_title', '') or book_title
            canvas.setFont("Times-Italic", 7.5)
            canvas.setFillColor(HexColor(_COLORS["header"]))
            canvas.drawCentredString(A5[0]/2, A5[1] - 14*mm, f"— {header_text} —")

            canvas.setStrokeColor(HexColor(_COLORS["rule"]))
            canvas.setLineWidth(0.3)
            line_w = text_width * 0.7
            x_start = (A5[0] - line_w) / 2
            canvas.line(x_start, A5[1] - 16*mm, x_start + line_w, A5[1] - 16*mm)
            canvas.restoreState()

        def on_image_page(canvas, doc):
            canvas.saveState()
            canvas.setFont("Times-Roman", 8)
            canvas.setFillColor(HexColor(_COLORS["page_number"]))
            canvas.drawCentredString(A5[0]/2, 10*mm, str(doc.page))
            canvas.restoreState()

        doc.addPageTemplates([
            PageTemplate(id="BlankPage", frames=frame_blank, onPage=on_blank_page),
            PageTemplate(id="ChapterStart", frames=frame_text, onPage=on_chapter_start),
            PageTemplate(id="ContentPage", frames=frame_text2, onPage=on_content_page),
            PageTemplate(id="ImagePage", frames=frame_img, onPage=on_image_page),
        ])

        st = self.build_styles(text_width)
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
        avail_img_width = A5[0] - 2*img_margin
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
