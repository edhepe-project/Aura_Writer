"""
light.py — Paleta de colores para el tema Claro (papel / diario literario).

Para crear un tema nuevo: copia este archivo, renómbralo y cambia los valores.
NO modifiques las claves (keys) — solo los valores de color.
La estructura del stylesheet vive en base.py.
"""
from .base import build_stylesheet

LIGHT_PALETTE = {
    # ── Fondos ──────────────────────────────────────────────────
    "bg_app":        "#faf8f5",   # ventanas, diálogos, toolbar, menubar
    "bg_surface":    "#f5f0ea",   # árbol, listas, tablas, paneles
    "bg_input":      "#ffffff",   # inputs, combobox, spinbox
    "bg_button":     "#ffffff",   # botones en reposo
    "bg_hover":      "#f3f0ea",   # hover en botones, ítems, toolbar
    "bg_selected":   "#dedad2",   # ítem seleccionado
    "bg_pressed":    "#e5e7eb",   # botón/tab presionado
    "bg_disabled":   "#f3f4f6",   # fondo deshabilitado
    "bg_muted":      "#faf8f5",   # scrollarea, stackedwidget
    "bg_overlay":    "#ffffff",   # tooltips
    "bg_menu":       "#ffffff",   # menú desplegable
    "bg_tab_active": "#f5f0ea",   # pestaña activa / pane
    "bg_tab_idle":   "#ede8e1",   # pestaña inactiva

    # ── Textos ──────────────────────────────────────────────────
    "fg_primary":    "#1f2937",   # texto principal
    "fg_secondary":  "#4b5563",   # toolbar, menubar
    "fg_muted":      "#6b7280",   # tabs inactivos, statusbar, headers
    "fg_disabled":   "#9ca3af",   # texto deshabilitado
    "fg_selected":   "#1f2937",   # texto sobre ítem seleccionado
    "fg_accent":     "#d97706",   # tab activo, botón chequeado

    # ── Colores semánticos de estado/rol ───────────────────────────────────
    "blue":          "#0066cc",   # azul informativo / acento
    "red":           "#dc2626",   # rojo alerta / error / eliminado
    "green":         "#16a34a",   # verde éxito / confirmación
    "purple":        "#9333ea",   # morado / badge especial
    "indigo":        "#4f46e5",   # índigo / notas
    "amber":         "#d97706",   # ámbar / aviso / borrador
    "fg_placeholder":"#9ca3af",   # texto placeholder

    # ── Bordes ──────────────────────────────────────────────────
    "border_default": "#d1d5db",  # inputs, botones, contenedores
    "border_subtle":  "#e5e7eb",  # menubar, toolbar (muy sutil)
    "border_strong":  "#d1d5db",  # splitter, groupbox, separadores
    "border_focus":   "#d97706",  # anillo de foco activo
    "border_accent":  "#d97706",  # borde de botón chequeado/activo

    # ── Acento ──────────────────────────────────────────────────
    "accent":        "#d97706",   # checkbox, radio checked
    "accent_hover":  "#b45309",   # acento en hover

    # ── Scrollbar ───────────────────────────────────────────────
    "scrollbar_handle":       "#d1d5db",
    "scrollbar_handle_hover": "#9ca3af",

    # ── Componentes específicos ──────────────────────────────────
    "header_bg":     "#ede8e1",   # encabezados de tabla/árbol
    "header_fg":     "#6b7280",
    "menu_hover":    "#f3f0ea",   # hover en ítems de menú
    "menu_disabled": "#9ca3af",
    "menu_sep":      "#e5e7eb",
    "groupbox_fg":   "#4b5563",
    "graphics_bg":   "#f5f0ea",
    "frame_sep":     "#e5e7eb",   # separadores QFrame (líneas H/V)
    "selection_bg":  "#e5e7eb",   # selección de texto en editors
}

LIGHT_STYLESHEET = build_stylesheet(LIGHT_PALETTE)
