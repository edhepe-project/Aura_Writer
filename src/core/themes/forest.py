"""
forest.py — Paleta de colores premium para el tema Bosque Profundo / Everglade.

Un tema oscuro ultra-sofisticado basado en tonos pino oscuro, musgo profundo, 
verde salvia y acentos en oro suave (madera). Diseñado para dar una sensación 
orgánica, relajante y de muy alta gama, como un escritorio de roble en una 
cabaña de noche.
"""
from .base import build_stylesheet

FOREST_PALETTE = {
    # ── Fondos (Grafito ultra-profundo, sin tinte verde) ─────────────
    "bg_app":        "#131415",   # Gris casi negro, neutro.
    "bg_surface":    "#1a1b1d",   # Paneles, inspector (ligera elevación, neutro).
    "bg_input":      "#202124",   # Cajas de texto, muy limpio.
    "bg_button":     "#232427",   # Botones en reposo.
    "bg_hover":      "#2a2c30",   # Hover neutro.
    "bg_selected":   "#22332a",   # Aquí sí: un sutil tinte esmeralda oscuro para la selección.
    "bg_pressed":    "#1d1e20",   # Clic presionado.
    "bg_disabled":   "#101112",   # Deshabilitado.
    "bg_muted":      "#131415",   # Scrollarea.
    "bg_overlay":    "#202124",   # Tooltips y menús.
    "bg_menu":       "#1a1b1d",   
    "bg_tab_active": "#1a1b1d",   
    "bg_tab_idle":   "#131415",   

    # ── Textos (Blancos y grises puros, 0% verde) ───────────────────
    "fg_primary":    "#f0f1f3",   # Blanco nítido neutro.
    "fg_secondary":  "#a0a2a8",   # Gris plomo neutro (iconos limpios).
    "fg_muted":      "#656870",   # Gris oscuro para desactivados.
    "fg_disabled":   "#45474d",   # Texto inactivo profundo.
    "fg_selected":   "#ffffff",   # Blanco puro al seleccionar.
    "fg_accent":     "#68b382",   # Acento: Verde salvia vibrante.

    # ── Colores semánticos (Clásicos y legibles) ───────────────────
    "blue":          "#5c98d6",   # Azul puro
    "red":           "#e05c5c",   # Rojo coral limpio
    "green":         "#68b382",   # Verde acento principal
    "purple":        "#a57bcf",   # Púrpura sutil
    "indigo":        "#d19d69",   # Ocre
    "amber":         "#d9b359",   # Oro clásico
    "fg_placeholder":"#656870",

    # ── Bordes (Grafito, separadores limpios) ─────────────────────
    "border_default": "#303236",  
    "border_subtle":  "#1f2022",  
    "border_strong":  "#3c3f45",  
    "border_focus":   "#68b382",  # Foco esmeralda.
    "border_accent":  "#68b382",

    # ── Acento (El toque premium) ───────────────────────────────
    "accent":        "#68b382",   # Salvia elegante.
    "accent_hover":  "#86c49d",   # Salvia brillante.

    # ── Scrollbar ───────────────────────────────────────────────
    "scrollbar_handle":       "#303236",
    "scrollbar_handle_hover": "#42454a",

    # ── Componentes específicos ──────────────────────────────────
    "header_bg":     "#1a1b1d",
    "header_fg":     "#a0a2a8",
    "menu_hover":    "#22332a",   # Hover en menú con ligero toque bosque.
    "menu_disabled": "#45474d",
    "menu_sep":      "#202124",
    "groupbox_fg":   "#a0a2a8",
    "graphics_bg":   "#131415",
    "frame_sep":     "#1f2022",
    "selection_bg":  "#22332a",

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
    "story_border_subtle":      "#303236",
    "story_border_selected":    "#68b382",
    "story_label_lighter":      True,
    "story_label_factor":       120,
    "story_tone_lighter":       False,
    "story_tone_factor":        110,

    # ── Painter: GenealogyNode (genealogy) ───────────────────────
    "genealogy_shadow_alpha":   70,
    "genealogy_avatar_darker":  True,
    "genealogy_avatar_factor":  150,
    "genealogy_initials_white": True,
    
    # Tarjetas en grises neutros muy oscuros, hover con matiz verde
    "genea_central_bg":         "#18191b",
    "genea_central_bg_hov":     "#1b241e",
    "genea_central_brd":        "#3c3f45",
    "genea_central_brd_hov":    "#68b382",
    "genea_central_hdr":        "#202124",
    "genea_central_hdr_hov":    "#243028",
    
    "genea_parent_bg":          "#18191b",
    "genea_parent_bg_hov":      "#1b241e",
    "genea_parent_hdr":         "#202124",
    "genea_parent_hdr_hov":     "#243028",
    
    "genea_partner_bg":         "#18191b",
    "genea_partner_bg_hov":     "#1b241e",
    "genea_partner_hdr":        "#202124",
    "genea_partner_hdr_hov":    "#243028",
    
    "genea_sibling_bg":         "#18191b",
    "genea_sibling_bg_hov":     "#1b241e",
    "genea_sibling_hdr":        "#202124",
    "genea_sibling_hdr_hov":    "#243028",
    
    "genea_descend_bg":         "#18191b",
    "genea_descend_bg_hov":     "#1b241e",
    "genea_descend_hdr":        "#202124",
    "genea_descend_hdr_hov":    "#243028",
}

FOREST_STYLESHEET = build_stylesheet(FOREST_PALETTE)
