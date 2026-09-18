"""
templates.py — Plantillas de página (Frames, running headers, folios de página) para ReportLab.
"""

from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import Frame, PageTemplate

from tools.exporters.base_exporter import _COLORS


def create_page_templates(book_title: str) -> tuple[list[PageTemplate], float]:
    """Crea y registra las plantillas de página para el documento BaseDocTemplate en A5."""
    text_left = 22 * mm
    text_right = 18 * mm
    text_top = 22 * mm
    text_bottom = 20 * mm
    text_width = A5[0] - text_left - text_right
    text_height = A5[1] - text_top - text_bottom

    frame_text = Frame(text_left, text_bottom, text_width, text_height, id="text")
    frame_text2 = Frame(text_left, text_bottom, text_width, text_height, id="text2")
    frame_blank = Frame(text_left, text_bottom, text_width, text_height, id="blank_frame")

    img_margin = 10 * mm
    img_bottom = 18 * mm
    frame_img = Frame(
        img_margin, img_bottom,
        A5[0] - 2 * img_margin,
        A5[1] - img_margin - img_bottom,
        id="fullpage_img"
    )

    def on_blank_page(canvas, doc):
        pass

    def on_chapter_start(canvas, doc):
        canvas.saveState()
        canvas.setFont("Times-Roman", 8)
        canvas.setFillColor(HexColor(_COLORS["page_number"]))
        canvas.drawCentredString(A5[0] / 2, 10 * mm, str(doc.page))
        canvas.restoreState()

    def on_content_page(canvas, doc):
        canvas.saveState()
        canvas.setFont("Times-Roman", 8)
        canvas.setFillColor(HexColor(_COLORS["page_number"]))
        canvas.drawCentredString(A5[0] / 2, 10 * mm, str(doc.page))

        header_text = getattr(canvas, '_current_chapter_title', '') or book_title
        canvas.setFont("Times-Italic", 7.5)
        canvas.setFillColor(HexColor(_COLORS["header"]))
        canvas.drawCentredString(A5[0] / 2, A5[1] - 14 * mm, f"— {header_text} —")

        canvas.setStrokeColor(HexColor(_COLORS["rule"]))
        canvas.setLineWidth(0.3)
        line_w = text_width * 0.7
        x_start = (A5[0] - line_w) / 2
        canvas.line(x_start, A5[1] - 16 * mm, x_start + line_w, A5[1] - 16 * mm)
        canvas.restoreState()

    def on_image_page(canvas, doc):
        canvas.saveState()
        canvas.setFont("Times-Roman", 8)
        canvas.setFillColor(HexColor(_COLORS["page_number"]))
        canvas.drawCentredString(A5[0] / 2, 10 * mm, str(doc.page))
        canvas.restoreState()

    templates = [
        PageTemplate(id="BlankPage", frames=frame_blank, onPage=on_blank_page),
        PageTemplate(id="ChapterStart", frames=frame_text, onPage=on_chapter_start),
        PageTemplate(id="ContentPage", frames=frame_text2, onPage=on_content_page),
        PageTemplate(id="ImagePage", frames=frame_img, onPage=on_image_page),
    ]

    return templates, text_width
