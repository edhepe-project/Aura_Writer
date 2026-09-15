"""
Aura Writer - Sound Engine basado en PyQt6.QtMultimedia.QSoundEffect.
Garantiza reproducción de audio nativa y multicanal en Qt sin depender de winsound de Windows.
"""

import os
import sys
from typing import Optional, Dict
from PyQt6.QtCore import QUrl, QObject
from PyQt6.QtMultimedia import QSoundEffect


class OlivettiSoundEngine(QObject):
    _instance: Optional["OlivettiSoundEngine"] = None

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
            
        sounds_dir = os.path.join(base_dir, "assets", "sounds", "olivetti")
        special_dir = os.path.join(sounds_dir, "special")

        # Pool de reproductores QSoundEffect para polifonía y cero latencia
        self._effect_pool = []
        self._pool_idx = 0
        self._pool_size = 12

        # Cargar archivo principal de tecla
        main_hammer_path = os.path.join(sounds_dir, "hammer_00.wav")
        self._main_url = QUrl.fromLocalFile(main_hammer_path)

        for _ in range(self._pool_size):
            eff = QSoundEffect(self)
            eff.setSource(self._main_url)
            eff.setVolume(1.0)
            self._effect_pool.append(eff)

        # Efectos especiales
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
    def instance(cls) -> "OlivettiSoundEngine":
        if cls._instance is None:
            cls._instance = OlivettiSoundEngine()
        return cls._instance

    def toggle(self) -> bool:
        self.enabled = not self.enabled
        return self.enabled

    def _play_stroke(self):
        if not self.enabled:
            return
        eff = self._effect_pool[self._pool_idx]
        eff.play()
        self._pool_idx = (self._pool_idx + 1) % self._pool_size

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
        if self.enabled:
            self._bell_effect.play()
