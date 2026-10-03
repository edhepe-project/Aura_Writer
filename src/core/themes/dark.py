"""
dark.py — Paleta de colores para el tema Oscuro (Apple dark / macOS).

Para crear un tema nuevo: copia este archivo, renómbralo y cambia los valores.
NO modifiques las claves (keys) — solo los valores de color.
La estructura del stylesheet vive en base.py.
"""
from .base import build_stylesheet

DARK_PALETTE = {
    # ── Fondos ──────────────────────────────────────────────────
    "bg_app":        "#121214",   # ventanas, diálogos, toolbar, menubar
    "bg_surface":    "#1c1c1e",   # árbol, listas, tablas, paneles
    "bg_input":      "#2c2c2e",   # inputs, combobox, spinbox
    "bg_button":     "#1c1c1e",   # botones en reposo
    "bg_hover":      "#2c2c2e",   # hover en botones, ítems, toolbar
    "bg_selected":   "#3a3a3c",   # ítem seleccionado
    "bg_pressed":    "#3a3a3c",   # botón/tab presionado
    "bg_disabled":   "#18181a",   # fondo deshabilitado
    "bg_muted":      "#121214",   # scrollarea, stackedwidget
    "bg_overlay":    "#2c2c2e",   # tooltips
    "bg_menu":       "#1c1c1e",   # menú desplegable
    "bg_tab_active": "#1c1c1e",   # pestaña activa / pane
    "bg_tab_idle":   "#2c2c2e",   # pestaña inactiva

    # ── Textos ──────────────────────────────────────────────────
    "fg_primary":    "#f2f2f7",   # texto principal
    "fg_secondary":  "#aeaeb2",   # toolbar, menubar
    "fg_muted":      "#8e8e93",   # tabs inactivos, statusbar, headers
    "fg_disabled":   "#48484a",   # texto deshabilitado
    "fg_selected":   "#ffffff",   # texto sobre ítem seleccionado
    "fg_accent":     "#ffd60a",   # tab activo, botón chequeado

    # ── Colores semánticos de estado/rol ───────────────────────────────────
    "blue":          "#0a84ff",   # azul informativo / acento
    "red":           "#ff453a",   # rojo alerta / error / eliminado
    "green":         "#30d158",   # verde éxito / confirmación
    "purple":        "#bf5af2",   # morado / badge especial
    "indigo":        "#5e5ce6",   # índigo / notas
    "amber":         "#ff9f0a",   # ámbar / aviso / borrador
    "fg_placeholder":"#636366",   # texto placeholder

    # ── Bordes ──────────────────────────────────────────────────
    "border_default": "rgba(255,255,255,0.10)",  # inputs, botones, contenedores
    "border_subtle":  "rgba(255,255,255,0.08)",  # menubar, toolbar (muy sutil)
    "border_strong":  "#3a3a3c",                 # splitter, groupbox, separadores
    "border_focus":   "#ffd60a",                 # anillo de foco activo
    "border_accent":  "#ffd60a",                 # borde de botón chequeado/activo

    # ── Acento ──────────────────────────────────────────────────
    "accent":        "#ffd60a",   # checkbox, radio checked
    "accent_hover":  "#ffe84d",   # acento en hover

    # ── Scrollbar ───────────────────────────────────────────────
    "scrollbar_handle":       "#3a3a3c",
    "scrollbar_handle_hover": "#636366",

    # ── Componentes específicos ──────────────────────────────────
    "header_bg":     "#2c2c2e",   # encabezados de tabla/árbol
    "header_fg":     "#8e8e93",
    "menu_hover":    "#2c2c2e",   # hover en ítems de menú
    "menu_disabled": "#636366",
    "menu_sep":      "rgba(255,255,255,0.08)",
    "groupbox_fg":   "#aeaeb2",
    "graphics_bg":   "#1c1c1e",
    "frame_sep":     "#3a3a3c",   # separadores QFrame (líneas H/V)
    "selection_bg":  "#3a3a3c",   # selección de texto en editors
}

DARK_STYLESHEET = build_stylesheet(DARK_PALETTE)
