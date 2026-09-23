# 🪶 Aura Writer — Premium Editorial Edition

**Tu obra. Tu legado. Tu privacidad.**

Aura Writer es el procesador de textos definitivo para novelistas que exigen lo mejor en **seguridad, diseño editorial y control creativo**. Diseñado como una herramienta offline-first y privada, lleva tu manuscrito desde la primera idea hasta una versión impresa de calidad profesional — sin depender nunca de la nube.

> _Versión actual: **1.7.2**_

---

## ✨ Características Premium

### 📕 Exportación con Calidad de Imprenta
- **PDF (A5):** Maquetación automática con portadas, páginas legales, numeración romana y running headers.
- **Diseño Editorial:** Primeros párrafos sin sangría, letras capitales (Drop Caps) en EPUB y ornamentos tipográficos (`❧`).
- **EPUB3 fluido** para e-readers y **DOCX profesional** para borradores editoriales.

### 🔒 Arquitectura de Seguridad "Zero-Knowledge"
- **Cifrado Militar:** Archivos `.aura` cifrados con **AES-256-GCM**.
- **Doble Factor (2FA):** Soporte nativo para TOTP (Google Authenticator, Authy) 100% offline.
- **Bloqueo Rápido:** Cierra la sesión con un solo clic (`Ctrl+L`) sin cerrar el programa.
- **Sin Telemetría:** Tus historias son solo tuyas. Sin internet, sin rastreo, sin servidores.

### 🗺️ Ingeniería Narrativa Avanzada
- **Jerarquía Literaria Completa:** Universos → Obras → Libros → Capítulos, todo en un solo proyecto.
- **Grafo de Relaciones de Personajes:** Visualización interactiva con física orbital y filtros dinámicos.
- **Atlas Literario (Grafo de Lugares):** Mapa espacial de escenarios con rutas, fronteras, portales y jerarquía planetaria. Maximizable a pantalla completa.
- **Cuadrícula de Presencias:** Tabla interactiva personaje × capítulo para rastrear quién aparece dónde y cuándo.
- **Cronología del Universo:** Línea de tiempo con eventos, épocas y orden cronológico del mundo narrativo.
- **Cronograma Narrativo (Grafo Causal):** Red de eventos causales con ramificaciones, consecuencias y temas.
- **Genealogía:** Árbol familiar interactivo de personajes con líneas de herencia visual.

### 🌐 Worldbuilding Profundo
- **Gestión de Elenco:** Fichas completas de personajes (nombre, rol, arco, imagen).
- **Lugares & Escenarios:** Base de datos geográfica con categorías, clima, lore, historia y jerarquía (continentes → ciudades → interiores).
- **Vocabulario y Conlang:** Glosario de términos inventados, lenguas construidas y morfología del universo.
- **Marcadores Semánticos:** Sistema de etiquetado por categoría para búsqueda rápida en el texto.

### 🛠️ Herramientas de Autor
- **Motor de Búsqueda Global:** Búsqueda con resaltado en tiempo real en todo el manuscrito.
- **Mesa de Cotejo:** Comparación visual de dos capítulos lado a lado (diff semántico).
- **Historial de Versiones:** Control de cambios con diff de texto por capítulo.
- **Backup Automático:** Copias de seguridad programadas con retención configurable.

---

## 🚀 Instalación Rápida (Windows)

### Instalador Visual (Recomendado)
Descarga `AuraWriter_Setup_v1.7.2.exe` desde la sección [Releases](../../releases) y sigue el asistente.

### Desde el Código Fuente
```powershell
git clone https://github.com/edhepe-project/Aura_Writer.git
cd Aura_Writer
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
python launcher.py
```
> Requisitos: Python 3.10+ con "Add to PATH" marcado durante la instalación.

### Ubuntu / Linux
```bash
sudo apt update && sudo apt install -y python3-venv libxcb-cursor0 libxcb-xinerama0 \
    libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxkbcommon-x11-0 libegl1 libgl1-mesa-glx
git clone https://github.com/edhepe-project/Aura_Writer.git && cd Aura_Writer
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt && python3 launcher.py
```

---

## 📁 Portabilidad Total

Tu archivo `.aura` es un búnker digital portátil. Llévalo en una memoria USB entre Windows y Linux sin perder un solo bit. Aura Writer detecta automáticamente el entorno y se adapta.

---

## 🧪 Calidad del Código

- **67 tests automatizados** con pytest — cobertura de módulos críticos de seguridad, exportación, modelos y UI.
- Arquitectura modular por componentes con separación limpia de capas (core / ui / tools).

---

## 📄 Licencia y Uso

Aura Writer es una herramienta privada. Todos los derechos reservados.
Diseñado para creadores que valoran la libertad de escribir en su propio santuario digital.

---
*Escrito con Aura Writer.*
