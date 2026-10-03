"""
sepia.py — Paleta de colores para el tema Sepia / Pergamino Vintage.

Para crear un tema nuevo: copia este archivo, renómbralo y cambia los valores.
NO modifiques las claves (keys) — solo los valores de color.
La estructura del stylesheet vive en base.py.
"""
from .base import build_stylesheet

SEPIA_PALETTE = {
    # ── Fondos ──────────────────────────────────────────────────
    "bg_app":        "#f4ecd8",   # ventanas, diálogos, toolbar, menubar (pergamino cálido)
    "bg_surface":    "#fcf8ee",   # árbol, listas, tablas, paneles
    "bg_input":      "#fcf8ee",   # inputs, combobox, spinbox
    "bg_button":     "#fcf8ee",   # botones en reposo
    "bg_hover":      "#eddcb8",   # hover en botones, ítems, toolbar
    "bg_selected":   "#dccaa7",   # ítem seleccionado
    "bg_pressed":    "#d3c09b",   # botón/tab presionado
    "bg_disabled":   "#eae0ca",   # fondo deshabilitado
    "bg_muted":      "#f4ecd8",   # scrollarea, stackedwidget
    "bg_overlay":    "#fcf8ee",   # tooltips
    "bg_menu":       "#fcf8ee",   # menú desplegable
    "bg_tab_active": "#fcf8ee",   # pestaña activa / pane
    "bg_tab_idle":   "#eae0ca",   # pestaña inactiva (bien diferenciada)

    # ── Textos ──────────────────────────────────────────────────
    "fg_primary":    "#2d241e",   # texto principal (café profundo, alta lectura literaria)
    "fg_secondary":  "#5a4a3e",   # toolbar, menubar, labels
    "fg_muted":      "#7a6858",   # tabs inactivos, statusbar, headers
    "fg_disabled":   "#a69786",   # texto deshabilitado
    "fg_selected":   "#2d241e",   # texto sobre ítem seleccionado
    "fg_accent":     "#a14806",   # tab activo, botón chequeado

    # ── Colores semánticos de estado/rol ───────────────────────────────────
    "blue":          "#2563eb",   # azul informativo / acento
    "red":           "#b91c1c",   # rojo alerta / error / eliminado
    "green":         "#15803d",   # verde éxito / confirmación
    "purple":        "#7e22ce",   # morado / badge especial
    "indigo":        "#4338ca",   # índigo / notas
    "amber":         "#b45309",   # ámbar / aviso / borrador
    "fg_placeholder":"#9e8f7e",   # texto placeholder

    # ── Bordes ──────────────────────────────────────────────────
    "border_default": "#d0c09e",  # inputs, botones, contenedores (cálido y nítido)
    "border_subtle":  "#ded0b5",  # menubar, toolbar (muy sutil)
    "border_strong":  "#beab86",  # splitter, groupbox, separadores
    "border_focus":   "#b45309",  # anillo de foco activo
    "border_accent":  "#b45309",  # borde de botón chequeado/activo

    # ── Acento ──────────────────────────────────────────────────
    "accent":        "#b45309",   # checkbox, radio checked
    "accent_hover":  "#92400e",   # acento en hover

    # ── Scrollbar ───────────────────────────────────────────────
    "scrollbar_handle":       "#d0c09e",
    "scrollbar_handle_hover": "#a6936f",

    # ── Componentes específicos ──────────────────────────────────
    "header_bg":     "#eae0ca",   # encabezados de tabla/árbol
    "header_fg":     "#7a6858",
    "menu_hover":    "#fcf8ee",   # hover en ítems de menú
    "menu_disabled": "#a69786",
    "menu_sep":      "#ded0b5",
    "groupbox_fg":   "#5a4a3e",
    "graphics_bg":   "#fcf8ee",
    "frame_sep":     "#d0c09e",   # separadores QFrame (líneas H/V)
    "selection_bg":  "#e4d4b2",   # selección de texto en editors

    # ── Painter: CharacterNode (relation_graph) ──────────────────
    "node_dimmed_opacity":      0.25,
    "node_aura_focused":        0.42,
    "node_aura_circle":         0.34,
    "node_aura_core":           0.26,
    "node_aura_primary":        0.17,
    "node_aura_minor":          0.11,
    "node_grad_core_hi":        130,
    "node_grad_core_lo":        122,
    "node_grad_hi":             122,
    "node_grad_lo":             130,
    "node_border_hi":           135,
    "node_border_mid":          122,
    "node_border_hi_w":         2.1,
    "node_border_mid_w":        1.5,
    "node_ring_factor":         140,
    "node_name_dimmed_alpha":   0.42,
    "node_tag_lighter":         False,
    "node_tag_factor":          138,

    # ── Painter: StoryBlock (story_graph) ────────────────────────
    "story_border_subtle":      "#c4b89a",
    "story_border_selected":    "#3d2b1f",
    "story_label_lighter":      False,
    "story_label_factor":       115,
    "story_tone_lighter":       True,
    "story_tone_factor":        115,

    # ── Painter: GenealogyNode (genealogy) ───────────────────────
    "genealogy_shadow_alpha":   25,
    "genealogy_avatar_darker":  False,
    "genealogy_avatar_factor":  160,
    "genealogy_initials_white": False,
    "genea_central_bg":         "#f0ebe0",
    "genea_central_bg_hov":     "#e6dfd0",
    "genea_central_brd":        "#7c6f9a",
    "genea_central_brd_hov":    "#6358a0",
    "genea_central_hdr":        "#8b7ab8",
    "genea_central_hdr_hov":    "#7a68a8",
    "genea_parent_bg":          "#eaf3e8",
    "genea_parent_bg_hov":      "#dbeede",
    "genea_parent_hdr":         "#4a8a5a",
    "genea_parent_hdr_hov":     "#3d7a4d",
    "genea_partner_bg":         "#f5e8f0",
    "genea_partner_bg_hov":     "#eed8e8",
    "genea_partner_hdr":        "#b06090",
    "genea_partner_hdr_hov":    "#9a5080",
    "genea_sibling_bg":         "#e8eef8",
    "genea_sibling_bg_hov":     "#d8e4f4",
    "genea_sibling_hdr":        "#4a70c0",
    "genea_sibling_hdr_hov":    "#3a60b0",
    "genea_descend_bg":         "#e8f4f0",
    "genea_descend_bg_hov":     "#d5ece5",
    "genea_descend_hdr":        "#3a9080",
    "genea_descend_hdr_hov":    "#2d8070",
}

SEPIA_STYLESHEET = build_stylesheet(SEPIA_PALETTE)
