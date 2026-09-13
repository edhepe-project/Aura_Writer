#!/usr/bin/env python3
"""
Aura Writer — Launcher Cross-Platform
Funciona en Windows y Linux sin modificaciones.
"""

import sys
import os
import traceback

# ── Configurar paths de importación ─────────────────────────────────
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")

# Asegurar que 'src' esté en el path para que los imports funcionen
for p in (src_dir, current_dir):
    if p not in sys.path:
        sys.path.insert(0, p)

# ── Lanzar la aplicación ────────────────────────────────────────────
try:
    from main import main
    main()
except Exception:
    error_msg = traceback.format_exc()
    print(f"ERROR DURANTE EL LANZAMIENTO:\n{error_msg}")

    # Guardar log de crash
    log_path = os.path.join(current_dir, "launcher_crash.log")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(error_msg)

    # Intentar mostrar un mensaje de error visual
    try:
        from PyQt6.QtWidgets import QApplication, QMessageBox
        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(
            None, "Error de Lanzamiento",
            f"La aplicación no pudo iniciarse:\n\n{error_msg[:500]}"
        )
    except Exception:
        pass

    sys.exit(1)
