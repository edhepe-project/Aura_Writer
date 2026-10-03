"""
dark.py — Paleta de colores para el tema Oscuro (Apple dark / macOS).

Para crear un tema nuevo: copia este archivo, renómbralo y cambia los valores.
NO modifiques las claves (keys) — solo los valores de color.
La estructura del stylesheet vive en base.py.
"""
from .base import build_stylesheet

DARK_PALETTE = {
    # ── Fondos ──────────────────────────────────────────────────
    "bg_app":        "#131316",   # ventanas, diálogos, toolbar, menubar (fondo base profundo)
    "bg_surface":    "#1c1c20",   # árbol, listas, tablas, paneles
    "bg_input":      "#25252a",   # inputs, combobox, spinbox
    "bg_button":     "#222227",   # botones en reposo
    "bg_hover":      "#2e2e36",   # hover en botones, ítems, toolbar
    "bg_selected":   "#383842",   # ítem seleccionado
    "bg_pressed":    "#32323a",   # botón/tab presionado
    "bg_disabled":   "#18181b",   # fondo deshabilitado
    "bg_muted":      "#131316",   # scrollarea, stackedwidget
    "bg_overlay":    "#25252a",   # tooltips
    "bg_menu":       "#1c1c20",   # menú desplegable
    "bg_tab_active": "#1c1c20",   # pestaña activa / pane
    "bg_tab_idle":   "#25252a",   # pestaña inactiva

    # ── Textos ──────────────────────────────────────────────────
    "fg_primary":    "#f4f4f7",   # texto principal (alto contraste y nitidez)
    "fg_secondary":  "#b0b0b8",   # toolbar, menubar, labels secundarios
    "fg_muted":      "#82828c",   # tabs inactivos, statusbar, headers
    "fg_disabled":   "#4e4e56",   # texto deshabilitado
    "fg_selected":   "#ffffff",   # texto sobre ítem seleccionado
    "fg_accent":     "#ffd60a",   # tab activo, botón chequeado

    # ── Colores semánticos de estado/rol ───────────────────────────────────
    "blue":          "#0a84ff",   # azul informativo / acento
    "red":           "#ff453a",   # rojo alerta / error / eliminado
    "green":         "#30d158",   # verde éxito / confirmación
    "purple":        "#bf5af2",   # morado / badge especial
    "indigo":        "#5e5ce6",   # índigo / notas
    "amber":         "#ff9f0a",   # ámbar / aviso / borrador
    "fg_placeholder":"#63636c",   # texto placeholder

    # ── Bordes ──────────────────────────────────────────────────
    "border_default": "#2e2e36",  # inputs, botones, contenedores (sólido y nítido)
    "border_subtle":  "#24242c",  # menubar, toolbar, divisores sutiles
    "border_strong":  "#383844",  # splitter, groupbox, separadores
    "border_focus":   "#ffd60a",  # anillo de foco activo
    "border_accent":  "#ffd60a",  # borde de botón chequeado/activo

    # ── Acento ──────────────────────────────────────────────────
    "accent":        "#ffd60a",   # checkbox, radio checked, switches
    "accent_hover":  "#ffe84d",   # acento en hover

    # ── Scrollbar ───────────────────────────────────────────────
    "scrollbar_handle":       "#383842",
    "scrollbar_handle_hover": "#545460",

    # ── Componentes específicos ──────────────────────────────────
    "header_bg":     "#25252a",   # encabezados de tabla/árbol
    "header_fg":     "#82828c",
    "menu_hover":    "#2e2e36",   # hover en ítems de menú
    "menu_disabled": "#63636c",
    "menu_sep":      "#24242c",
    "groupbox_fg":   "#b0b0b8",
    "graphics_bg":   "#1c1c20",
    "frame_sep":     "#2e2e36",   # separadores QFrame (líneas H/V)
    "selection_bg":  "#383842",   # selección de texto en editors

    # ── Painter: CharacterNode (relation_graph) ──────────────────
    "node_dimmed_opacity":      0.12,
    "node_aura_focused":        0.55,
    "node_aura_circle":         0.45,
    "node_aura_core":           0.35,
    "node_aura_primary":        0.22,
    "node_aura_minor":          0.14,
    "node_grad_core_hi":        160,   # c.lighter(factor) en nodo core
    "node_grad_core_lo":        140,   # c.darker(factor) en nodo core
    "node_grad_hi":             140,   # c.lighter(factor) nodo normal
    "node_grad_lo":             150,   # c.darker(factor) nodo normal
    "node_border_hi":           160,   # borde brillante (tier core)
    "node_border_mid":          130,   # borde brillante (tier normal)
    "node_border_hi_w":         2.0,   # grosor borde core
    "node_border_mid_w":        1.2,   # grosor borde normal
    "node_ring_factor":         180,   # c.lighter para anillo de foco
    "node_name_dimmed_alpha":   0.35,
    "node_tag_lighter":         True,  # True=lighter, False=darker para tag
    "node_tag_factor":          165,

    # ── Painter: StoryBlock (story_graph) ────────────────────────
    "story_border_subtle":      "#3a3a3c",
    "story_border_selected":    "#ffffff",
    "story_label_lighter":      True,   # True=lighter, False=darker
    "story_label_factor":       140,
    "story_tone_lighter":       False,  # tone footer: darker en dark
    "story_tone_factor":        120,

    # ── Painter: GenealogyNode (genealogy) ───────────────────────
    "genealogy_shadow_alpha":   45,
    "genealogy_avatar_darker":  True,   # True=darker(160), False=lighter(170)
    "genealogy_avatar_factor":  160,
    "genealogy_initials_white": True,   # True=#ffffff, False=role.darker
    # Colores de fondo/borde de tarjetas por tipo de nodo
    "genea_central_bg":         "#1e1b4b",
    "genea_central_bg_hov":     "#2e1065",
    "genea_central_brd":        "#818cf8",
    "genea_central_brd_hov":    "#a5b4fc",
    "genea_central_hdr":        "#4f46e5",
    "genea_central_hdr_hov":    "#6366f1",
    "genea_parent_bg":          "#142d1f",
    "genea_parent_bg_hov":      "#14532d",
    "genea_parent_hdr":         "#166534",
    "genea_parent_hdr_hov":     "#15803d",
    "genea_partner_bg":         "#311327",
    "genea_partner_bg_hov":     "#701a75",
    "genea_partner_hdr":        "#9d174d",
    "genea_partner_hdr_hov":    "#be185d",
    "genea_sibling_bg":         "#172554",
    "genea_sibling_bg_hov":     "#1e3a8a",
    "genea_sibling_hdr":        "#1d4ed8",
    "genea_sibling_hdr_hov":    "#1e40af",
    "genea_descend_bg":         "#142d27",
    "genea_descend_bg_hov":     "#134e4a",
    "genea_descend_hdr":        "#0f766e",
    "genea_descend_hdr_hov":    "#115e59",
}

DARK_STYLESHEET = build_stylesheet(DARK_PALETTE)
