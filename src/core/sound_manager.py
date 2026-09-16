"""
Aura Writer - Sound Engine basado en PyQt6.QtMultimedia.QSoundEffect.
Garantiza reproducción de audio nativa y multicanal en Qt sin depender de winsound de Windows.
"""

import os
import sys
import random
from typing import Optional
from PyQt6.QtCore import QUrl, QObject
from PyQt6.QtMultimedia import QSoundEffect


class AuraSoundEngine(QObject):
    _instance: Optional["AuraSoundEngine"] = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.enabled: bool = True
        self.bell_enabled: bool = True
        self._chars_in_line: int = 0
        self.bell_column: int = 70

        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            base_dir = getattr(sys, "_MEIPASS")
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        # Buscar preferentemente en 'aura', luego fallback a 'olivetti'
        sounds_dir = os.path.join(base_dir, "assets", "sounds", "aura")
        if not os.path.isdir(sounds_dir):
            sounds_dir = os.path.join(base_dir, "assets", "sounds", "olivetti")

        # ── Pool de martillos: un QSoundEffect por cada hammer_XX.wav ──
        # Así cada tecla usa un archivo diferente → sonido más natural y variado
        self._effect_pool: list[QSoundEffect] = []
        self._pool_idx = 0

        hammer_files: list[str] = []
        if os.path.isdir(sounds_dir):
            hammer_files = sorted(
                f for f in os.listdir(sounds_dir)
                if f.startswith("hammer_") and f.endswith(".wav")
            )
        if not hammer_files:
            hammer_files = ["hammer_00.wav"]

        self._pool_size = len(hammer_files)
        for fname in hammer_files:
            eff = QSoundEffect(self)
            eff.setSource(QUrl.fromLocalFile(os.path.join(sounds_dir, fname)))
            eff.setVolume(1.0)
            self._effect_pool.append(eff)

        # URL del primero (para inspección / diagnóstico)
        self._main_url = QUrl.fromLocalFile(os.path.join(sounds_dir, hammer_files[0]))

        # ── Efectos especiales ──────────────────────────────────────────
        self._space_effect = QSoundEffect(self)
        self._space_effect.setSource(QUrl.fromLocalFile(os.path.join(sounds_dir, "space.wav")))
        self._space_effect.setVolume(1.0)

        self._backspace_effect = QSoundEffect(self)
        self._backspace_effect.setSource(QUrl.fromLocalFile(os.path.join(sounds_dir, "backspace.wav")))
        self._backspace_effect.setVolume(1.0)

        self._enter_effect = QSoundEffect(self)
        self._enter_effect.setSource(QUrl.fromLocalFile(os.path.join(sounds_dir, "enter.wav")))
        self._enter_effect.setVolume(1.0)

        self._bell_effect = QSoundEffect(self)
        self._bell_effect.setSource(QUrl.fromLocalFile(os.path.join(sounds_dir, "bell.wav")))
        self._bell_effect.setVolume(0.9)

    @classmethod
    def instance(cls) -> "AuraSoundEngine":
        if cls._instance is None:
            cls._instance = AuraSoundEngine()
        return cls._instance

    def toggle(self) -> bool:
        self.enabled = not self.enabled
        return self.enabled

    def _play_stroke(self):
        """Reproduce el siguiente martillo del pool de forma cíclica."""
        if not self.enabled:
            return
        eff = self._effect_pool[self._pool_idx]
        eff.play()
        # Avance aleatorio dentro del pool para mayor variedad
        self._pool_idx = random.randint(0, self._pool_size - 1)

    def on_key_pressed(self, text: str, is_enter: bool = False,
                       is_space: bool = False, is_backspace: bool = False):
        if not self.enabled:
            return

        if is_enter:
            self._chars_in_line = 0
            self._enter_effect.play()
        elif is_space:
            self._chars_in_line += 1
            self._space_effect.play()
        elif is_backspace:
            self._chars_in_line = max(0, self._chars_in_line - 1)
            self._backspace_effect.play()
        else:
            self._chars_in_line += 1
            if self.bell_enabled and self._chars_in_line == self.bell_column:
                self._bell_effect.play()
                return
            self._play_stroke()

    def ring_bell(self) -> None:
        """Hace sonar la campanilla manualmente."""
        if self.enabled:
            self._bell_effect.play()


# Alias para retrocompatibilidad total
OlivettiSoundEngine = AuraSoundEngine
