# Plan de Implementación: Sistema Semántico de Párrafos y Detección Automática de Diálogos

## Objetivo
Implementar un sistema de análisis y estilos semánticos en el editor de **Aura Writer** que identifique automáticamente fragmentos de **narración**, **diálogo**, **pensamientos** y **acotaciones** sin interrumpir el flujo creativo del escritor, aprovechando esta información tanto en el editor visual como en la exportación y estadísticas.

---

## Fase 1: Motor Semántico del Texto (`core/text_classifier.py` o módulo similar)
**Propósito:** Lógica pura (desacoplada de Qt) para clasificar párrafos y bloques de texto.

1. **Definición de Tipos de Bloque:**
   - `NARRATIVE` (Texto regular en prosa)
   - `DIALOGUE` (Líneas iniciadas con raya `—`, `–`, `--` o comillas de diálogo)
   - `THOUGHT` (Pensamientos directos / monólogo interior, e.g., marcados por cursiva o formato especial)
   - `SCENE_BREAK` (Separadores de escena `* * *`, `---`, `#`)
   - `QUOTE_OR_LETTER` (Cartas, notas o mensajes incrustados)

2. **Reglas de Detección Automática:**
   - Reconocimiento de raya española/em-dash (`—`, Unicode `\u2014`).
   - Reconocimiento de comillas latinas (`«...»`) e inglesas (`"..."`).
   - Detección de acotaciones del narrador dentro de réplicas de diálogo (e.g. `—No puedo hacerlo —respondió con calma.`).
   - Limpieza y normalización de guiones automáticos (convertir `-- ` en `—`).

3. **Pruebas Unitarias:**
   - Tests específicos que cubran capítulos mixtos (alternancia de narración y diálogo).
   - Validar bordes: líneas vacías, párrafos que inician con espacios o tabulaciones.

4. **Soporte para Conlang / Idiomas Ficticios:**
   - Reconocimiento de términos en **cursiva** (`<i>...</i>` o `*...*`) como candidatos a términos de conlang/glosario.
   - Integración con el diccionario local del proyecto (evitar que el corrector ortográfico marque falsos errores en palabras en cursiva que coincidan con el glosario).
   - Capacidad futura de extraer automáticamente todas las palabras en cursiva hacia el Glosario / Apéndice del libro.

---

## Fase 2: Integración con el Editor (`ui/editor/editor_view.py`)
**Propósito:** Que el editor reaccione de forma inteligente y fluida en tiempo real.

1. **Auto-formateo no invasivo (Smart Quotes & Em-Dash):**
   - Atajo o autocorrección al escribir dos guiones (`--` $\rightarrow$ `— `).
   - Tecla rápida configurable para insertar raya larga (e.g. `Alt + -` o `Ctrl + Shift + D`).

2. **Herencia Inteligente en `Enter`:**
   - Al pulsar `Enter` al final de una línea de diálogo:
     - Preparar la siguiente línea con indentación o mantener el contexto conversacional.
     - Si se pulsa `Enter` en una línea vacía, salir del modo de diálogo y volver a narración regular.

3. **Marcado Visual Sutil (Opcional por Configuración):**
   - Guía visual en el margen izquierdo o resaltado tipográfico tenue para distinguir rápidamente réplicas de diálogo sin saturar la vista.
   - Selector manual de estilo en la barra de herramientas como *override* o control manual si el usuario lo desea.

---

## Fase 3: Métricas y Estadísticas de Capítulo
**Propósito:** Brindar valor analítico al escritor sobre el ritmo de su historia.

1. **Balance de Ritmo:**
   - Cálculo automático del ratio: `% Narración vs % Diálogo`.
2. **Alertas de Coherencia Tipográfica:**
   - Identificar rayas abiertas sin cerrar en las réplicas.
   - Detectar inconsistencias en el tipo de comillas o guiones utilizados.

---

## Fase 4: Exportador Enriquecido (`exporters/`)
**Propósito:** Que la exportación respete las convenciones editoriales según el tipo de párrafo.

1. **Exportación a DOCX / PDF / EPUB:**
   - **Narración:** Sangría francesa o sangría de primera línea estándar (1.25 cm), espaciado interlineal estándar.
   - **Diálogo:** Formato específico según convención elegida (estilo español con raya larga o estilo internacional).
   - Separadores de escena con centrado y espaciado decorativo adecuado.

---

## Hoja de Ruta para la Sesión de Mañana:
- [ ] **Paso 1:** Crear `core/text_classifier.py` con las reglas de reconocimiento y sus tests unitarios asociados.
- [ ] **Paso 2:** Conectar la sustitución automática de `--` a `—` en `EditorView`.
- [ ] **Paso 3:** Incorporar la clasificación por bloque en el pipeline de exportación.
- [ ] **Paso 4:** Revisión de tests y pruebas manuales con un fragmento de novela real.
