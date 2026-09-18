# Plan de Evolución v1.7.0 — Aura Writer

Cuatro pilares de mejora profunda que convierten Aura Writer en una herramienta de worldbuilding completa.

---

## 📋 Resumen de las 4 Áreas

| # | Módulo | Descripción | Estado |
|---|--------|-------------|--------|
| 1 | **Lugares en Capítulos** | Vincular escenarios a capítulos + detección automática de menciones | 🟢 Completado |
| 2 | **Cronología / Timeline Literario** | Visualizador de eventos en línea temporal interactiva (`Ctrl+Alt+T`) | 🟢 Completado |
| 3 | **Grafo de Lugares** | Red visual de conexiones geográficas entre escenarios (`Ctrl+Alt+G`) | 🟢 Completado |
| 4 | **UI Polish** | Refinamientos de experiencia, microanimaciones y accesibilidad | 🟢 Completado |

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
  - Panel inferior adaptado para listar apariciones de capítulos con navegación interactiva
- [x] **Siguiente paso completado**:
  - Conectar el refresco en vivo de `update_chapters_data()` desde el ciclo principal / señales.
  - Tests unitarios en `tests/test_place_models.py` y `tests/ui/test_place_dock.py`.

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

### Archivos Creados
- [x] **`src/ui/timeline/__init__.py`**
- [x] **`src/ui/timeline/dialog.py`**
- [x] **`src/ui/timeline/widget.py`**
- [x] **`src/ui/timeline/event_card.py`**
- [x] **`src/ui/main_menu_builder.py`**: Entrada `Vista → ⏳ Cronología (Ctrl+Alt+T)`.
- [x] **`tests/ui/test_timeline.py`**: Suite de tests interactivos.

---

## 3 🗺️ Grafo de Lugares / Atlas de Conexiones

### Objetivo
Grafo topológico de los lugares del universo con aristas representando conexiones geográficas (rutas, fronteras, portales, ríos...).

### Archivos Creados
- [x] **`src/ui/place_graph/__init__.py`**
- [x] **`src/ui/place_graph/widget.py`**
- [x] **`src/ui/place_graph/dialog.py`**
- [x] **`src/ui/main_menu_builder.py`**: Entrada `Vista → 🗺️ Atlas (Ctrl+Alt+G)`.
- [x] **`tests/ui/test_place_graph.py`**: Suite de tests automatizados.

---

## 4 ✨ UI Polish

| Área | Mejora | Estado |
|------|--------|--------|
| **PlaceDock** | Contador de resultados filtrados ("3 de 12 lugares") | Completado |
| **PlaceDock** | Sangría visual en tarjetas hijas para jerarquías | Completado |
| **Inspector** | Conmutación segmentada instantánea entre `👤` y `🏰` | Completado |
| **Status Bar** | Muestra lugar activo del capítulo actual | Completado |
| **Grafo de Lugares** | Botón `Reorganizar` con spring layout automático | Completado |


---

## 🚀 Cómo Continuar en Casa

1. Hacer `git pull` en la máquina de casa.
2. Ejecutar tests para validar estado base:
   ```bash
   pytest -q
   ```
3. Decirle al asistente: **"Continuar con el Plan de Evolución v1.7.0 (Módulo 1 tests & Módulo 2 Timeline)"**.
