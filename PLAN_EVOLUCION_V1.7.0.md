# Plan de Evolución v1.7.0 — Aura Writer

Cuatro pilares de mejora profunda que convierten Aura Writer en una herramienta de worldbuilding completa.

---

## 📋 Resumen de las 4 Áreas

| # | Módulo | Descripción | Estado |
|---|--------|-------------|--------|
| 1 | **Lugares en Capítulos** | Vincular escenarios a capítulos + detección automática de menciones | 🟡 En progreso (Modelos & detección listos) |
| 2 | **Cronología / Timeline Literario** | Visualizador de eventos en línea temporal interactiva (`Ctrl+Alt+T`) | ⚪ Pendiente |
| 3 | **Grafo de Lugares** | Red visual de conexiones geográficas entre escenarios (`Ctrl+Alt+G`) | ⚪ Pendiente |
| 4 | **UI Polish** | Refinamientos de experiencia, microanimaciones y accesibilidad | ⚪ Pendiente |

---

## 1 🏰 Lugares en Capítulos

### Objetivo
Al igual que los personajes, un capítulo puede **ocurrir en uno o más lugares**. El `PlaceDock` mostrará qué capítulos se ambientan en cada lugar, y el editor detectará automáticamente menciones de nombres de escenarios.

### Estado Actual:
- [x] **Modelos actualizados (`models.py`)**:
  - `Chapter.places_present: List[str] = []`
  - `Chapter.in_world_date: str = ""`
  - `Chapter.in_world_order: int = 0`
  - `PlaceLink` y `UniverseMetadata.place_links: List[PlaceLink] = []`
- [x] **Detección automática (`character_controller.py`)**:
  - Implementado `_detect_place_mentions(chapter)`
  - Conectado a `notes_controller.py` y `app_lifecycle_controller.py`
- [x] **PlaceDock (`dock.py` & `card.py`)**:
  - Conteo de resultados filtrados
  - Sangría visual por jerarquía (`depth`)
  - Panel inferior adaptado para listar apariciones de capítulos
- [ ] **Siguiente paso pendiente**:
  - Conectar el refresco en vivo de `update_chapters_data()` desde el ciclo principal / señales.
  - Tests unitarios en `tests/test_place_models.py`.

---

## 2 ⏳ Cronología / Timeline Literario

### Objetivo
Ventana modal con una **línea temporal horizontal e interactiva** ordenada por `in_world_date` / `in_world_order`, donde cada evento/capítulo aparece como nodo en el eje de tiempo.

### Características
- Eje de tiempo horizontal con eras/años del universo.
- Nodos de capítulos coloreados por obra.
- Filtro por obra + vista de personajes y lugares presentes por nodo.
- Atajo: `Ctrl+Alt+T`.
- Exportable como PNG.

### Archivos a Crear
- **`src/ui/timeline/__init__.py`**
- **`src/ui/timeline/dialog.py`**
- **`src/ui/timeline/widget.py`**
- **`src/ui/timeline/event_card.py`**
- **`src/ui/main_menu_builder.py`**: Entrada `Vista → ⏳ Cronología (Ctrl+Alt+T)`.

---

## 3 🗺️ Grafo de Lugares / Atlas de Conexiones

### Objetivo
Grafo topológico de los lugares del universo con aristas representando conexiones geográficas (rutas, fronteras, portales, ríos...).

### Archivos a Crear
- **`src/ui/place_graph/__init__.py`**
- **`src/ui/place_graph/widget.py`**
- **`src/ui/place_graph/dialog.py`**
- **`src/ui/main_menu_builder.py`**: Entrada `Vista → 🗺️ Atlas (Ctrl+Alt+G)`.

---

## 4 ✨ UI Polish

| Área | Mejora |
|------|--------|
| **PlaceDock** | Contador de resultados filtrados ("3 de 12 lugares") (Completado) |
| **PlaceDock** | Sangría visual en tarjetas hijas para jerarquías (Completado) |
| **Inspector** | Animación suave al cambiar entre tabs `👤` / `🏰` |
| **Status Bar** | Muestra lugar activo del capítulo actual |
| **Grafo de Lugares** | Botón `Reorganizar` con spring layout automático |

---

## 🚀 Cómo Continuar en Casa

1. Hacer `git pull` en la máquina de casa.
2. Ejecutar tests para validar estado base:
   ```bash
   pytest -q
   ```
3. Decirle al asistente: **"Continuar con el Plan de Evolución v1.7.0 (Módulo 1 tests & Módulo 2 Timeline)"**.
