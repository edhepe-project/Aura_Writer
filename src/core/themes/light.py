"""
light.py — Paleta de colores para el tema Claro (papel / diario literario).

Para crear un tema nuevo: copia este archivo, renómbralo y cambia los valores.
NO modifiques las claves (keys) — solo los valores de color.
La estructura del stylesheet vive en base.py.
"""
from .base import build_stylesheet

LIGHT_PALETTE = {
    # ── Fondos ──────────────────────────────────────────────────
    "bg_app":        "#faf8f5",   # ventanas, diálogos, toolbar, menubar (tono papel cálido)
    "bg_surface":    "#f4efe9",   # árbol, listas, tablas, paneles
    "bg_input":      "#ffffff",   # inputs, combobox, spinbox
    "bg_button":     "#ffffff",   # botones en reposo
    "bg_hover":      "#eee8df",   # hover en botones, ítems, toolbar
    "bg_selected":   "#ded6ca",   # ítem seleccionado
    "bg_pressed":    "#e4ddd2",   # botón/tab presionado
    "bg_disabled":   "#f3efe9",   # fondo deshabilitado
    "bg_muted":      "#faf8f5",   # scrollarea, stackedwidget
    "bg_overlay":    "#ffffff",   # tooltips
    "bg_menu":       "#ffffff",   # menú desplegable
    "bg_tab_active": "#f4efe9",   # pestaña activa / pane
    "bg_tab_idle":   "#eae3d8",   # pestaña inactiva

    # ── Textos ──────────────────────────────────────────────────
    "fg_primary":    "#1f242e",   # texto principal (carbón nítido de alta legibilidad)
    "fg_secondary":  "#4a5260",   # toolbar, menubar, labels
    "fg_muted":      "#737b88",   # tabs inactivos, statusbar, headers
    "fg_disabled":   "#a2a8b2",   # texto deshabilitado
    "fg_selected":   "#1f242e",   # texto sobre ítem seleccionado
    "fg_accent":     "#c26a05",   # tab activo, botón chequeado

    # ── Colores semánticos de estado/rol ───────────────────────────────────
    "blue":          "#0066cc",   # azul informativo / acento
    "red":           "#dc2626",   # rojo alerta / error / eliminado
    "green":         "#16a34a",   # verde éxito / confirmación
    "purple":        "#9333ea",   # morado / badge especial
    "indigo":        "#4f46e5",   # índigo / notas
    "amber":         "#d97706",   # ámbar / aviso / borrador
    "fg_placeholder":"#9ca3af",   # texto placeholder

    # ── Bordes ──────────────────────────────────────────────────
    "border_default": "#ded8ce",  # inputs, botones, contenedores (cálido y armónico)
    "border_subtle":  "#ebe6dc",  # menubar, toolbar (muy sutil)
    "border_strong":  "#cfc7bc",  # splitter, groupbox, separadores
    "border_focus":   "#d97706",  # anillo de foco activo
    "border_accent":  "#d97706",  # borde de botón chequeado/activo

    # ── Acento ──────────────────────────────────────────────────
    "accent":        "#d97706",   # checkbox, radio checked
    "accent_hover":  "#b45309",   # acento en hover

    # ── Scrollbar ───────────────────────────────────────────────
    "scrollbar_handle":       "#ded8ce",
    "scrollbar_handle_hover": "#b8afa3",

    # ── Componentes específicos ──────────────────────────────────
    "header_bg":     "#eae3d8",   # encabezados de tabla/árbol
    "header_fg":     "#737b88",
    "menu_hover":    "#f4efe9",   # hover en ítems de menú
    "menu_disabled": "#a2a8b2",
    "menu_sep":      "#ebe6dc",
    "groupbox_fg":   "#4a5260",
    "graphics_bg":   "#f4efe9",
    "frame_sep":     "#ded8ce",   # separadores QFrame (líneas H/V)
    "selection_bg":  "#e6dfd3",   # selección de texto en editors

    # ── Painter: CharacterNode (relation_graph) ──────────────────
    "node_dimmed_opacity":      0.28,
    "node_aura_focused":        0.40,
    "node_aura_circle":         0.32,
    "node_aura_core":           0.25,
    "node_aura_primary":        0.16,
    "node_aura_minor":          0.10,
    "node_grad_core_hi":        125,
    "node_grad_core_lo":        120,
    "node_grad_hi":             120,
    "node_grad_lo":             125,
    "node_border_hi":           130,
    "node_border_mid":          120,
    "node_border_hi_w":         2.2,
    "node_border_mid_w":        1.6,
    "node_ring_factor":         135,
    "node_name_dimmed_alpha":   0.45,
    "node_tag_lighter":         False,
    "node_tag_factor":          140,

    # ── Painter: StoryBlock (story_graph) ────────────────────────
    "story_border_subtle":      "#d1d5db",
    "story_border_selected":    "#000000",
    "story_label_lighter":      False,
    "story_label_factor":       110,
    "story_tone_lighter":       True,
    "story_tone_factor":        120,

    # ── Painter: GenealogyNode (genealogy) ───────────────────────
    "genealogy_shadow_alpha":   20,
    "genealogy_avatar_darker":  False,
    "genealogy_avatar_factor":  170,
    "genealogy_initials_white": False,
    "genea_central_bg":         "#f5f3ff",
    "genea_central_bg_hov":     "#ede9fe",
    "genea_central_brd":        "#4f46e5",
    "genea_central_brd_hov":    "#4338ca",
    "genea_central_hdr":        "#6366f1",
    "genea_central_hdr_hov":    "#4f46e5",
    "genea_parent_bg":          "#f0fdf4",
    "genea_parent_bg_hov":      "#dcfce7",
    "genea_parent_hdr":         "#22c55e",
    "genea_parent_hdr_hov":     "#16a34a",
    "genea_partner_bg":         "#fdf2f8",
    "genea_partner_bg_hov":     "#fce7f3",
    "genea_partner_hdr":        "#ec4899",
    "genea_partner_hdr_hov":    "#db2777",
    "genea_sibling_bg":         "#eff6ff",
    "genea_sibling_bg_hov":     "#dbeafe",
    "genea_sibling_hdr":        "#3b82f6",
    "genea_sibling_hdr_hov":    "#2563eb",
    "genea_descend_bg":         "#f0fdfa",
    "genea_descend_bg_hov":     "#ccfbf1",
    "genea_descend_hdr":        "#14b8a6",
    "genea_descend_hdr_hov":    "#0d9488",
}

LIGHT_STYLESHEET = build_stylesheet(LIGHT_PALETTE)
