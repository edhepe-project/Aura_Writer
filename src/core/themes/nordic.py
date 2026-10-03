"""
nordic.py — Paleta de colores para el tema Noche Nórdica (Midnight Blue / Polar Dark).

Inspirado en tonos azul noche ártico, hielo y auroras boreales.
NO modifiques las claves (keys) — solo los valores de color.
La estructura del stylesheet vive en base.py.
"""
from .base import build_stylesheet

NORDIC_PALETTE = {
    # ── Fondos ──────────────────────────────────────────────────
    "bg_app":        "#0d1117",   # ventanas, diálogos, toolbar, menubar (azul noche profundo)
    "bg_surface":    "#161b22",   # árbol, listas, tablas, paneles
    "bg_input":      "#21262d",   # inputs, combobox, spinbox
    "bg_button":     "#1f242c",   # botones en reposo
    "bg_hover":      "#2d333b",   # hover en botones, ítems, toolbar
    "bg_selected":   "#313d4f",   # ítem seleccionado
    "bg_pressed":    "#29313d",   # botón/tab presionado
    "bg_disabled":   "#14181f",   # fondo deshabilitado
    "bg_muted":      "#0d1117",   # scrollarea, stackedwidget
    "bg_overlay":    "#21262d",   # tooltips
    "bg_menu":       "#161b22",   # menú desplegable
    "bg_tab_active": "#161b22",   # pestaña activa / pane
    "bg_tab_idle":   "#21262d",   # pestaña inactiva

    # ── Textos ──────────────────────────────────────────────────
    "fg_primary":    "#f0f6fc",   # texto principal (blanco hielo de alta legibilidad)
    "fg_secondary":  "#8b949e",   # toolbar, menubar, labels
    "fg_muted":      "#6e7681",   # tabs inactivos, statusbar, headers
    "fg_disabled":   "#484f58",   # texto deshabilitado
    "fg_selected":   "#ffffff",   # texto sobre ítem seleccionado
    "fg_accent":     "#38bdf8",   # tab activo, botón chequeado (azul cyan glaciar)

    # ── Colores semánticos de estado/rol ───────────────────────────────────
    "blue":          "#58a6ff",   # azul polar / enlaces
    "red":           "#f85149",   # rojo coral / error / eliminado
    "green":         "#3fb950",   # verde aurora / confirmación
    "purple":        "#bc8cff",   # violeta boreal / badge especial
    "indigo":        "#79c0ff",   # índigo ártico / notas
    "amber":         "#d29922",   # ámbar dorado / aviso / borrador
    "fg_placeholder":"#6e7681",   # texto placeholder

    # ── Bordes ──────────────────────────────────────────────────
    "border_default": "#30363d",  # inputs, botones, contenedores (sólido y nítido)
    "border_subtle":  "#21262d",  # menubar, toolbar (muy sutil)
    "border_strong":  "#38434f",  # splitter, groupbox, separadores
    "border_focus":   "#38bdf8",  # anillo de foco activo (cyan ártico)
    "border_accent":  "#38bdf8",  # borde de botón chequeado/activo

    # ── Acento ──────────────────────────────────────────────────
    "accent":        "#38bdf8",   # checkbox, radio checked, switches
    "accent_hover":  "#7dd3fc",   # acento en hover

    # ── Scrollbar ───────────────────────────────────────────────
    "scrollbar_handle":       "#30363d",
    "scrollbar_handle_hover": "#484f58",

    # ── Componentes específicos ──────────────────────────────────
    "header_bg":     "#21262d",   # encabezados de tabla/árbol
    "header_fg":     "#8b949e",
    "menu_hover":    "#2d333b",   # hover en ítems de menú
    "menu_disabled": "#484f58",
    "menu_sep":      "#21262d",
    "groupbox_fg":   "#8b949e",
    "graphics_bg":   "#161b22",
    "frame_sep":     "#30363d",   # separadores QFrame (líneas H/V)
    "selection_bg":  "#313d4f",   # selección de texto en editors

    # ── Painter: CharacterNode (relation_graph) ──────────────────
    "node_dimmed_opacity":      0.15,
    "node_aura_focused":        0.50,
    "node_aura_circle":         0.40,
    "node_aura_core":           0.30,
    "node_aura_primary":        0.19,
    "node_aura_minor":          0.12,
    "node_grad_core_hi":        150,
    "node_grad_core_lo":        135,
    "node_grad_hi":             135,
    "node_grad_lo":             145,
    "node_border_hi":           155,
    "node_border_mid":          125,
    "node_border_hi_w":         2.0,
    "node_border_mid_w":        1.2,
    "node_ring_factor":         170,
    "node_name_dimmed_alpha":   0.38,
    "node_tag_lighter":         True,
    "node_tag_factor":          155,

    # ── Painter: StoryBlock (story_graph) ────────────────────────
    "story_border_subtle":      "#2e3f50",
    "story_border_selected":    "#cdd9e5",
    "story_label_lighter":      True,
    "story_label_factor":       135,
    "story_tone_lighter":       False,
    "story_tone_factor":        115,

    # ── Painter: GenealogyNode (genealogy) ───────────────────────
    "genealogy_shadow_alpha":   55,
    "genealogy_avatar_darker":  True,
    "genealogy_avatar_factor":  155,
    "genealogy_initials_white": True,
    "genea_central_bg":         "#1a2340",
    "genea_central_bg_hov":     "#22304d",
    "genea_central_brd":        "#7c9fd0",
    "genea_central_brd_hov":    "#9ab8e8",
    "genea_central_hdr":        "#4a72b0",
    "genea_central_hdr_hov":    "#5a85cc",
    "genea_parent_bg":          "#142d20",
    "genea_parent_bg_hov":      "#1a3d2a",
    "genea_parent_hdr":         "#2d8a50",
    "genea_parent_hdr_hov":     "#35a560",
    "genea_partner_bg":         "#2a1530",
    "genea_partner_bg_hov":     "#3a1d42",
    "genea_partner_hdr":        "#8f4db5",
    "genea_partner_hdr_hov":    "#a85fd0",
    "genea_sibling_bg":         "#152035",
    "genea_sibling_bg_hov":     "#1c2f4a",
    "genea_sibling_hdr":        "#3a78c2",
    "genea_sibling_hdr_hov":    "#4a90d8",
    "genea_descend_bg":         "#132b28",
    "genea_descend_bg_hov":     "#1a3d38",
    "genea_descend_hdr":        "#2a8f85",
    "genea_descend_hdr_hov":    "#35a89c",
}

NORDIC_STYLESHEET = build_stylesheet(NORDIC_PALETTE)
