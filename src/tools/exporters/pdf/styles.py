"""
styles.py — Estilos tipográficos editoriales para exportación PDF en Aura Writer.
"""

from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER

from tools.exporters.base_exporter import _COLORS


def get_pdf_styles(avail_width: float) -> dict[str, ParagraphStyle]:
    """Genera los estilos tipográficos para la novela en PDF A5."""
    s = {}
    s["body"] = ParagraphStyle(
        "AuraBody",
        fontName="Times-Roman",
        fontSize=10.5,
        leading=15,
        alignment=TA_JUSTIFY,
        firstLineIndent=4 * mm,
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
        firstLineIndent=3 * mm,
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
