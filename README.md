# 🪶 Aura Writer — Premium Editorial Edition

**Tu obra. Tu legado. Tu privacidad.**

Aura Writer es el procesador de textos definitivo para novelistas que exigen lo mejor en **seguridad, diseño editorial y control creativo**. Diseñado como una herramienta offline-first y privada, permite llevar un manuscrito desde la primera idea hasta una versión impresa de calidad profesional sin depender de la nube.

---

## ✨ Características Premium

### 📕 Exportación con Calidad de Imprenta
*   **PDF (A5):** Maquetación automática con portadas, páginas legales, numeración antigua y running headers.
*   **Diseño Editorial:** Primeros párrafos sin sangría, letras capitales (Drop Caps) en EPUB y ornamentos tipográficos (`❧`).
*   **Formatos para Distribución:** DOCX profesional para borradores y EPUB3 fluido para e-readers.

### 🔒 Arquitectura de Seguridad "Zero-Knowledge"
*   **Cifrado Militar:** Todo se guarda en archivos `.aura` cifrados con **AES-256-GCM**.
*   **Doble Factor (2FA):** Soporte nativo para TOTP (Google Authenticator, Authy, etc.) 100% offline.
*   **Sin Telemetría:** Tus historias son solo tuyas. Sin conexión a internet, sin rastreo.

### 🗺️ Ingeniería Narrativa
*   **Jerarquía Literaria:** Estructura completa de Universos, Obras, Libros y Capítulos.
*   **Gestión de Elenco:** Base de datos de personajes con grafos de relaciones interactivos.
*   **Mapa Mental:** Visualización dinámica de los nodos de tu universo.
*   **Multigénero:** Soporta capítulos de texto e imágenes a página completa (ilustraciones).

---

## 🚀 Instalación Rápida

Consulta la lista completa en [INSTRUCCIONES_INSTALACION.txt](INSTRUCCIONES_INSTALACION.txt).

### Windows
1. Instala Python 3.10+ (marcando "Add to PATH").
2. Crea e instala el entorno:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Lanza: `python launcher.py`

### Ubuntu / Linux
1. Instala dependencias gráficas esenciales:
   ```bash
   sudo apt update
   sudo apt install -y python3-venv libxcb-cursor0 libxcb-xinerama0 libxcb-icccm4 libxcb-image0 libxkbcommon-x11-0 libegl1 libgl1-mesa-glx
   ```
2. Configura y lanza:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python3 launcher.py
   ```

---

## 📁 Portabilidad Total

Tu archivo `.aura` es un búnker digital portátil. Puedes llevarlo en una memoria USB entre Windows y Linux sin perder un solo bit. Aura Writer detectará automáticamente el entorno y ajustará el tema para una experiencia fluida.

---

## 📄 Licencia y Uso
Aura Writer es una herramienta privada. Todos los derechos reservados. Diseñado para creadores que valoran la libertad de escribir en su propio santuario digital.

---
*Escrito con Aura Writer.*
