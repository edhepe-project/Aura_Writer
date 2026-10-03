"""
dracula.py — Paleta de colores premium para el tema Drácula / Amatista.

Un tema oscuro profundo, elegante y moderno, diseñado para largas sesiones 
de escritura sin fatiga visual. Basado en la paleta Drácula original pero 
adaptada para Aura Writer.
"""
from .base import build_stylesheet

DRACULA_PALETTE = {
    # ── Fondos (Capas de profundidad) ───────────────────────────
    "bg_app":        "#1e1e24",   # ventanas, diálogos (fondo base ultra profundo, casi negro pero con matiz índigo)
    "bg_surface":    "#24252e",   # paneles laterales, inspector (ligeramente más elevado)
    "bg_input":      "#2a2b36",   # cajas de texto y combobox (bien sutil)
    "bg_button":     "#2e303e",   # botones en reposo (ligeramente más claros que los inputs)
    "bg_hover":      "#3b3e51",   # hover (índigo suave)
    "bg_selected":   "#44475a",   # selección activa
    "bg_pressed":    "#2a2b36",   # clic presionado
    "bg_disabled":   "#18191f",   # deshabilitado oscuro
    "bg_muted":      "#1e1e24",   # scrollarea
    "bg_overlay":    "#2a2b36",   # tooltips y menús popups
    "bg_menu":       "#24252e",   # fondo del menú superior
    "bg_tab_active": "#24252e",   # pestaña activa (se funde con el panel)
    "bg_tab_idle":   "#1e1e24",   # pestaña inactiva

    # ── Textos ──────────────────────────────────────────────────
    "fg_primary":    "#f8f8f2",   # blanco humo suave, máxima legibilidad
    "fg_secondary":  "#a3aabf",   # gris azulado para textos secundarios
    "fg_muted":      "#6272a4",   # índigo apagado para desactivados/placeholders
    "fg_disabled":   "#4f556b",   # texto inactivo profundo
    "fg_selected":   "#ffffff",   # blanco brillante al seleccionar
    "fg_accent":     "#bd93f9",   # Púrpura Amatista

    # ── Colores semánticos (Ajustados para no quemar la vista) ────
    "blue":          "#8be9fd",   # Cian
    "red":           "#ff5555",   # Coral
    "green":         "#50fa7b",   # Verde Esmeralda claro
    "purple":        "#bd93f9",   # Púrpura
    "indigo":        "#ff79c6",   # Fucsia
    "amber":         "#f1fa8c",   # Dorado suave
    "fg_placeholder":"#6272a4",

    # ── Bordes (Elegancia sin ruido) ─────────────────────────────
    "border_default": "#36384a",  # muy sutil para inputs
    "border_subtle":  "#2a2b36",  # casi invisible (separadores)
    "border_strong":  "#44475a",  # cajas de grupos o divisiones principales
    "border_focus":   "#bd93f9",  # anillo de foco púrpura neón
    "border_accent":  "#bd93f9",

    # ── Acento ──────────────────────────────────────────────────
    "accent":        "#bd93f9",
    "accent_hover":  "#d5b8ff",   # Un lavanda brillante al pasar el ratón

    # ── Scrollbar ───────────────────────────────────────────────
    "scrollbar_handle":       "#3b3e51",
    "scrollbar_handle_hover": "#50546d",

    # ── Componentes específicos ──────────────────────────────────
    "header_bg":     "#2a2b36",
    "header_fg":     "#a3aabf",
    "menu_hover":    "#3b3e51",
    "menu_disabled": "#4f556b",
    "menu_sep":      "#2a2b36",
    "groupbox_fg":   "#bd93f9",
    "graphics_bg":   "#1e1e24",
    "frame_sep":     "#2a2b36",
    "selection_bg":  "#44475a",

    # ── Painter: CharacterNode (relation_graph) ──────────────────
    "node_dimmed_opacity":      0.15,
    "node_aura_focused":        0.45,
    "node_aura_circle":         0.35,
    "node_aura_core":           0.25,
    "node_aura_primary":        0.15,
    "node_aura_minor":          0.08,
    "node_grad_core_hi":        140,
    "node_grad_core_lo":        120,
    "node_grad_hi":             120,
    "node_grad_lo":             130,
    "node_border_hi":           150,
    "node_border_mid":          125,
    "node_border_hi_w":         2.0,
    "node_border_mid_w":        1.2,
    "node_ring_factor":         160,
    "node_name_dimmed_alpha":   0.4,
    "node_tag_lighter":         True,
    "node_tag_factor":          150,

    # ── Painter: StoryBlock (story_graph) ────────────────────────
    "story_border_subtle":      "#36384a",
    "story_border_selected":    "#bd93f9",
    "story_label_lighter":      True,
    "story_label_factor":       120,
    "story_tone_lighter":       False,
    "story_tone_factor":        110,

    # ── Painter: GenealogyNode (genealogy) ───────────────────────
    "genealogy_shadow_alpha":   60,
    "genealogy_avatar_darker":  True,
    "genealogy_avatar_factor":  150,
    "genealogy_initials_white": True,
    # Tarjetas más oscuras y elegantes, con bordes que brillan al hover
    "genea_central_bg":         "#211f30",
    "genea_central_bg_hov":     "#2a2740",
    "genea_central_brd":        "#6272a4",
    "genea_central_brd_hov":    "#bd93f9",
    "genea_central_hdr":        "#383a59",
    "genea_central_hdr_hov":    "#44475a",
    
    "genea_parent_bg":          "#1f2b26",
    "genea_parent_bg_hov":      "#25362e",
    "genea_parent_hdr":         "#274234",
    "genea_parent_hdr_hov":     "#325442",
    
    "genea_partner_bg":         "#301e28",
    "genea_partner_bg_hov":     "#3b2432",
    "genea_partner_hdr":        "#4a2c3d",
    "genea_partner_hdr_hov":    "#5e374d",
    
    "genea_sibling_bg":         "#1c2436",
    "genea_sibling_bg_hov":     "#222b42",
    "genea_sibling_hdr":        "#273552",
    "genea_sibling_hdr_hov":    "#324469",
    
    "genea_descend_bg":         "#2a241f",
    "genea_descend_bg_hov":     "#362e26",
    "genea_descend_hdr":        "#453729",
    "genea_descend_hdr_hov":    "#574534",
}

DRACULA_STYLESHEET = build_stylesheet(DRACULA_PALETTE)
