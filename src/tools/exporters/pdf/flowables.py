"""
flowables.py — Flowables ornamentales y decorativos para ReportLab (PDF A5).
"""

from reportlab.lib.colors import HexColor
from reportlab.platypus import Flowable


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
