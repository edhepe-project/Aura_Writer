"""
Aura Writer — Exporters Package
Fachada unificada AuraExporter con delegación a PDFExporter, DOCXExporter y EPUBExporter.
"""

from tools.exporters.pdf_exporter import PDFExporter, OrnamentalRule, DecorativeLine, ChapterMarker
from tools.exporters.docx_exporter import DOCXExporter
from tools.exporters.epub_exporter import EPUBExporter


class AuraExporter:
    """Fachada unificada para exportación de proyectos Aura Writer a PDF, DOCX y EPUB."""

    def __init__(self, config: dict, temp_dir: str):
        self.config = config
        self.temp_dir = temp_dir
        self.pdf_engine = PDFExporter(config, temp_dir)
        self.docx_engine = DOCXExporter(config, temp_dir)
        self.epub_engine = EPUBExporter(config, temp_dir)

    def export_pdf_professional(self, project_data: dict, output_path: str):
        """Exporta la obra en PDF A5 de calidad editorial."""
        return self.pdf_engine.export(project_data, output_path)

    def export_draft_docx(self, project_data: dict, output_path: str):
        """Exporta la obra a borrador DOCX para Microsoft Word."""
        return self.docx_engine.export(project_data, output_path)

    def export_epub(self, project_data: dict, output_path: str):
        """Exporta la obra a libro electrónico EPUB3."""
        return self.epub_engine.export(project_data, output_path)


__all__ = [
    "AuraExporter",
    "PDFExporter",
    "DOCXExporter",
    "EPUBExporter",
    "OrnamentalRule",
    "DecorativeLine",
    "ChapterMarker",
]
