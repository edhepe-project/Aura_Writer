"""
Aura Writer — Base Exporter Module
Paletas de colores, constantes editoriales y utilidades comunes.
"""

from bs4 import BeautifulSoup

# ======================================================================
# Color Palette — tonos editoriales cálidos y elegantes
# ======================================================================
_COLORS = {
    "text_primary":    "#2c2416",   # casi negro cálido
    "text_secondary":  "#6b5d4f",   # gris-café cálido
    "text_muted":      "#9a8e80",   # canela atenuado
    "accent":          "#8c7b6b",   # taupe cálido
    "accent_light":    "#c0b8a8",   # taupe claro
    "rule":            "#d4ccc0",   # línea sutil
    "note_bg":         "#f8f5f0",   # marfil cálido
    "note_border":     "#b8a88a",   # borde dorado-tan
    "caption":         "#7a6e60",   # pie de foto tenue
    "page_number":     "#6b5d4f",   # gris número de página
    "header":          "#9a8e80",   # cabecera viva
}


def clean_html(html_content: str) -> BeautifulSoup:
    """Limpia atributos inline de estilo y clases para maquetación homogénea."""
    soup = BeautifulSoup(html_content, "lxml")
    for tag in soup.find_all(True):
        tag.attrs.pop("style", None)
        tag.attrs.pop("class", None)
    return soup


def html_to_text(html_content: str) -> str:
    """Convierte HTML a texto plano eliminando todas las etiquetas.
    Utilidad centralizada para búsquedas, análisis y detecciones."""
    if not html_content:
        return ""
    return BeautifulSoup(html_content, "lxml").get_text()
