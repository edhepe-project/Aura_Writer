import os
import pytest
from tools.exporters import AuraExporter, PDFExporter, DOCXExporter, EPUBExporter

@pytest.fixture
def sample_export_data():
    """Estructura de datos con jerarquía de capítulos para exportar."""
    return {
        "title": "Las Crónicas de Áurea",
        "author": "Escritor Épico",
        "language": "es",
        "obras": [
            {
                "title": "Tomo I: El Despertar",
                "libros": [
                    {
                        "title": "Libro de la Luz",
                        "capitulos": [
                            {
                                "title": "Capítulo I: La Forja",
                                "content": "<h1>Capítulo I: La Forja</h1><p>En el corazón de la montaña, el martillo resonaba contra el yunque encantado. Las chispas iluminaban la caverna de piedra ancestral.</p><p>El guardián contemplaba la espada recién forjada con reverencia.</p>",
                                "pov": "Guardián de la Forja",
                                "export": True
                            },
                            {
                                "title": "Capítulo II: El Juramento",
                                "content": "<h1>Capítulo II: El Juramento</h1><p>Bajo las estrellas eternas, los siete caballeros alzaron sus copas.</p>",
                                "pov": "Caballero Comandante",
                                "export": True
                            }
                        ]
                    }
                ]
            }
        ]
    }

def test_pdf_exporter(temp_workspace, sample_export_data):
    pdf_out = os.path.join(temp_workspace, "test_output.pdf")
    meta = {"title": sample_export_data["title"], "author": sample_export_data["author"]}
    exporter = PDFExporter(meta=meta, temp_dir=temp_workspace)
    
    success, msg = exporter.export(sample_export_data, pdf_out)
    assert success is True
    assert os.path.exists(pdf_out)
    assert os.path.getsize(pdf_out) > 1000  # Archivo PDF válido generado

def test_docx_exporter(temp_workspace, sample_export_data):
    docx_out = os.path.join(temp_workspace, "test_output.docx")
    meta = {"title": sample_export_data["title"], "author": sample_export_data["author"]}
    exporter = DOCXExporter(meta=meta, temp_dir=temp_workspace)
    
    exporter.export(sample_export_data, docx_out)
    assert os.path.exists(docx_out)
    assert os.path.getsize(docx_out) > 1000  # Archivo Word válido generado

def test_epub_exporter(temp_workspace, sample_export_data):
    epub_out = os.path.join(temp_workspace, "test_output.epub")
    meta = {"title": sample_export_data["title"], "author": sample_export_data["author"], "language": "es"}
    exporter = EPUBExporter(meta=meta, temp_dir=temp_workspace)
    
    exporter.export(sample_export_data, epub_out)
    assert os.path.exists(epub_out)
    assert os.path.getsize(epub_out) > 1000  # Archivo EPUB válido generado

def test_aura_exporter_facade(temp_workspace, sample_export_data):
    meta = {"title": sample_export_data["title"], "author": sample_export_data["author"]}
    facade = AuraExporter(config=meta, temp_dir=temp_workspace)
    
    pdf_path = os.path.join(temp_workspace, "facade.pdf")
    docx_path = os.path.join(temp_workspace, "facade.docx")
    epub_path = os.path.join(temp_workspace, "facade.epub")
    
    success, _ = facade.export_pdf_professional(sample_export_data, pdf_path)
    assert success is True
    assert os.path.exists(pdf_path)
    
    facade.export_draft_docx(sample_export_data, docx_path)
    assert os.path.exists(docx_path)
    
    facade.export_epub(sample_export_data, epub_path)
    assert os.path.exists(epub_path)
