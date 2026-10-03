"""
sepia.py — Paleta de colores para el tema Sepia / Pergamino Vintage.

Para crear un tema nuevo: copia este archivo, renómbralo y cambia los valores.
NO modifiques las claves (keys) — solo los valores de color.
La estructura del stylesheet vive en base.py.
"""
from .base import build_stylesheet

SEPIA_PALETTE = {
    # ── Fondos ──────────────────────────────────────────────────
    "bg_app":        "#f4ecd8",   # ventanas, diálogos, toolbar, menubar
    "bg_surface":    "#fcf8ee",   # árbol, listas, tablas, paneles
    "bg_input":      "#fcf8ee",   # inputs, combobox, spinbox
    "bg_button":     "#fcf8ee",   # botones en reposo
    "bg_hover":      "#ebdcb9",   # hover en botones, ítems, toolbar
    "bg_selected":   "#d8c8a8",   # ítem seleccionado
    "bg_pressed":    "#d8c8a8",   # botón/tab presionado
    "bg_disabled":   "#ebdcb9",   # fondo deshabilitado
    "bg_muted":      "#f4ecd8",   # scrollarea, stackedwidget
    "bg_overlay":    "#fcf8ee",   # tooltips
    "bg_menu":       "#fcf8ee",   # menú desplegable
    "bg_tab_active": "#fcf8ee",   # pestaña activa / pane
    "bg_tab_idle":   "#f4ecd8",   # pestaña inactiva

    # ── Textos ──────────────────────────────────────────────────
    "fg_primary":    "#2d241e",   # texto principal
    "fg_secondary":  "#5c4d41",   # toolbar, menubar
    "fg_muted":      "#6b5b4e",   # tabs inactivos, statusbar, headers
    "fg_disabled":   "#a39585",   # texto deshabilitado
    "fg_selected":   "#2d241e",   # texto sobre ítem seleccionado
    "fg_accent":     "#b45309",   # tab activo, botón chequeado

    # ── Colores semánticos de estado/rol ───────────────────────────────────
    "blue":          "#2563eb",   # azul informativo / acento
    "red":           "#b91c1c",   # rojo alerta / error / eliminado
    "green":         "#15803d",   # verde éxito / confirmación
    "purple":        "#7e22ce",   # morado / badge especial
    "indigo":        "#4338ca",   # índigo / notas
    "amber":         "#b45309",   # ámbar / aviso / borrador
    "fg_placeholder":"#a39585",   # texto placeholder

    # ── Bordes ──────────────────────────────────────────────────
    "border_default": "#cbb894",  # inputs, botones, contenedores
    "border_subtle":  "#d8c8a8",  # menubar, toolbar (muy sutil)
    "border_strong":  "#cbb894",  # splitter, groupbox, separadores
    "border_focus":   "#b45309",  # anillo de foco activo
    "border_accent":  "#b45309",  # borde de botón chequeado/activo

    # ── Acento ──────────────────────────────────────────────────
    "accent":        "#b45309",   # checkbox, radio checked
    "accent_hover":  "#92400e",   # acento en hover

    # ── Scrollbar ───────────────────────────────────────────────
    "scrollbar_handle":       "#cbb894",
    "scrollbar_handle_hover": "#b45309",

    # ── Componentes específicos ──────────────────────────────────
    "header_bg":     "#ebdcb9",   # encabezados de tabla/árbol
    "header_fg":     "#5c4d41",
    "menu_hover":    "#ebdcb9",   # hover en ítems de menú
    "menu_disabled": "#a39585",
    "menu_sep":      "#d8c8a8",
    "groupbox_fg":   "#5c4d41",
    "graphics_bg":   "#fcf8ee",
    "frame_sep":     "#d8c8a8",   # separadores QFrame (líneas H/V)
    "selection_bg":  "#ebdcb9",   # selección de texto en editors
}

SEPIA_STYLESHEET = build_stylesheet(SEPIA_PALETTE)
