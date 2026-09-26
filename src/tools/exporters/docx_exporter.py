"""
Aura Writer — DOCX Exporter Module
Generación de borradores en formato Microsoft Word (.docx) con diseño editorial inteligente y pulido.
"""

import os
from bs4 import BeautifulSoup
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_LINE_SPACING, WD_ALIGN_PARAGRAPH

from tools.exporters.base_exporter import clean_html
from tools.protection.aura_protect import strip_zero_width_chars


class DOCXExporter:
    """Motor de exportación de borradores manuscritos en formato DOCX con acabado editorial inteligente."""

    def __init__(self, meta: dict, temp_dir: str):
        self.meta = meta
        self.temp_dir = temp_dir

    def export(self, project_data: dict, output_path: str):
        """Genera un documento Word (.docx) limpio, elegante y profesional."""
        doc = Document()

        # Inyectar firma en metadatos del archivo DOCX sin alterar el texto visible
        sig = project_data.get("protection_signature", "")
        if sig:
            try:
                doc.core_properties.keywords = sig
                doc.core_properties.comments = f"Protegido con Aura Protect — {sig}"
            except Exception:
                pass

        # Configuración de página Carta Estándar (US Letter 8.5 x 11 in, Márgenes limpios de 1 pulgada)
        section = doc.sections[0]
        section.page_width = Inches(8.5)
        section.page_height = Inches(11.0)
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

        # Tipografía editorial elegante (Georgia 11.5 pt, Interlineado 1.35)
        style = doc.styles["Normal"]
        style.font.name = "Georgia"
        style.font.size = Pt(11.5)
        style.font.color.rgb = RGBColor(30, 30, 30)
        style.paragraph_format.line_spacing = 1.35
        style.paragraph_format.space_after = Pt(4)
        style.paragraph_format.space_before = Pt(0)

        title = self.meta.get("title", "Borrador").strip()
        author = self.meta.get("author", "").strip()

        # Separador florón clásico (Hiedra)
        FLORAL_MOTIF = "— ❧ —"

        # --- Portada Elegante ---
        for _ in range(7):
            p_sp = doc.add_paragraph("")
            p_sp.paragraph_format.line_spacing = 1.0

        p_title = doc.add_paragraph()
        p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_title.paragraph_format.space_after = Pt(12)
        run_title = p_title.add_run(title)
        run_title.font.name = "Georgia"
        run_title.font.size = Pt(26)
        run_title.font.bold = True
        run_title.font.color.rgb = RGBColor(20, 20, 20)

        p_ornament = doc.add_paragraph()
        p_ornament.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_ornament.paragraph_format.space_after = Pt(18)
        run_orn = p_ornament.add_run(FLORAL_MOTIF)
        run_orn.font.size = Pt(12)
        run_orn.font.color.rgb = RGBColor(160, 150, 135)

        if author:
            p_author = doc.add_paragraph()
            p_author.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run_a = p_author.add_run(author)
            run_a.font.name = "Georgia"
            run_a.font.size = Pt(13)
            run_a.font.italic = True
            run_a.font.color.rgb = RGBColor(80, 80, 80)

        # --- Secciones / Capítulos ---
        numbered_chapter_count = 0
        for item in project_data.get("chapters", []):
            doc.add_page_break()

            content_soup_d = BeautifulSoup(item.get("content", ""), "lxml")
            html_heading_d = content_soup_d.find(["h1", "h2", "h3"])
            chapter_title_d = html_heading_d.get_text(strip=True) if html_heading_d else item.get("title", "")
            chapter_title_d = chapter_title_d.strip()
            libro_label_d = item.get("libro_title", "").strip()

            title_lower = chapter_title_d.lower()

            special_sections = [
                "prólogo", "prologo", "epílogo", "epilogo", "introducción", "introduccion",
                "prefacio", "nota del autor", "agradecimientos", "dedicatoria", "apéndice", "apendice"
            ]
            is_special = any(spec in title_lower for spec in special_sections)

            if not is_special and not title_lower.startswith("capítulo") and not title_lower.startswith("capitulo"):
                numbered_chapter_count += 1

            # Espaciado superior previo al título
            for _ in range(2):
                p_sp = doc.add_paragraph("")
                p_sp.paragraph_format.line_spacing = 1.0

            if libro_label_d:
                p_label = doc.add_paragraph()
                p_label.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_label.paragraph_format.space_after = Pt(4)
                run_label = p_label.add_run(libro_label_d.upper())
                run_label.font.name = "Georgia"
                run_label.font.size = Pt(9)
                run_label.font.color.rgb = RGBColor(130, 120, 110)

            # Renderizado de títulos
            if is_special:
                p_ch_title = doc.add_paragraph()
                p_ch_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_ch_title.paragraph_format.space_after = Pt(14)
                run_ch = p_ch_title.add_run(chapter_title_d if chapter_title_d else "Prólogo")
                run_ch.font.name = "Georgia"
                run_ch.font.size = Pt(18)
                run_ch.font.bold = True
                run_ch.font.color.rgb = RGBColor(20, 20, 20)
            elif title_lower.startswith("capítulo") or title_lower.startswith("capitulo"):
                p_ch_title = doc.add_paragraph()
                p_ch_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_ch_title.paragraph_format.space_after = Pt(14)
                run_ch = p_ch_title.add_run(chapter_title_d)
                run_ch.font.name = "Georgia"
                run_ch.font.size = Pt(18)
                run_ch.font.bold = True
                run_ch.font.color.rgb = RGBColor(20, 20, 20)
            else:
                p_ch_num = doc.add_paragraph()
                p_ch_num.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_ch_num.paragraph_format.space_after = Pt(2)
                run_num = p_ch_num.add_run(f"Capítulo {numbered_chapter_count}")
                run_num.font.name = "Georgia"
                run_num.font.size = Pt(12)
                run_num.font.bold = True
                run_num.font.color.rgb = RGBColor(120, 100, 80)

                if chapter_title_d:
                    p_ch_title = doc.add_paragraph()
                    p_ch_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p_ch_title.paragraph_format.space_after = Pt(14)
                    run_ch = p_ch_title.add_run(chapter_title_d)
                    run_ch.font.name = "Georgia"
                    run_ch.font.size = Pt(16)
                    run_ch.font.bold = True
                    run_ch.font.color.rgb = RGBColor(20, 20, 20)

            # Separador florón clásico (Hiedra)
            p_sep = doc.add_paragraph()
            p_sep.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_sep.paragraph_format.space_after = Pt(24)
            run_s = p_sep.add_run(FLORAL_MOTIF)
            run_s.font.size = Pt(10)
            run_s.font.color.rgb = RGBColor(180, 170, 155)

            for m in item.get("medias", []):
                if m.get("position") == "before":
                    self._add_media(doc, m)

            soup = clean_html(item.get("content", ""))
            first_heading_skipped_d = False
            is_first_para = True

            for p in soup.find_all(["p", "h1", "h2", "h3"]):
                if p.name in ("h1", "h2", "h3") and not first_heading_skipped_d:
                    first_heading_skipped_d = True
                    continue

                text = strip_zero_width_chars(p.get_text(strip=True))
                if not text:
                    continue

                if "[ Página en Blanco ]" in text or "[ Página en blanco ]" in text or "página en blanco" in text.lower():
                    doc.add_page_break()
                    doc.add_page_break()
                    is_first_para = True
                    continue

                if "Salto de Página" in text or "salto de página" in text.lower() or "page-break-after" in str(p.get("style", "")):
                    doc.add_page_break()
                    is_first_para = True
                    continue

                if text:
                    para = doc.add_paragraph(text)
                    para.paragraph_format.line_spacing = 1.35
                    para.paragraph_format.space_after = Pt(4)
                    para.paragraph_format.space_before = Pt(0)
                    
                    if is_first_para:
                        para.paragraph_format.first_line_indent = Inches(0)
                        is_first_para = False
                    else:
                        para.paragraph_format.first_line_indent = Inches(0.4)

            for m in item.get("medias", []):
                if m.get("position") in ("after", "inline"):
                    self._add_media(doc, m)

            for note_text in item.get("author_notes", []):
                if note_text:
                    p = doc.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    p.paragraph_format.first_line_indent = Inches(0)
                    run = p.add_run(f"📌 Nota del autor: {note_text}")
                    run.font.color.rgb = RGBColor(120, 110, 100)
                    run.italic = True
                    run.font.size = Pt(9.5)

        doc.save(output_path)
        return True, f"Borrador DOCX profesional generado en: {output_path}"

    def _add_media(self, doc, m):
        path = m.get("path", "")
        if not os.path.exists(path):
            return
        try:
            para = doc.add_paragraph()
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            para.paragraph_format.first_line_indent = Inches(0)
            run = para.add_run()
            run.add_picture(path, width=Inches(4.5))
            if m.get("caption"):
                cap_para = doc.add_paragraph(m["caption"])
                cap_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                cap_para.paragraph_format.first_line_indent = Inches(0)
                cap_para.runs[0].italic = True
                cap_para.runs[0].font.size = Pt(9.5)
                cap_para.runs[0].font.color.rgb = RGBColor(110, 110, 110)
        except Exception:
            pass
