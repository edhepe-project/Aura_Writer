"""
Aura Writer - Sound Engine.
Utiliza simpleaudio / pygame para reproducción de audio de latencia ultra-baja y polifonía real,
independiente del event loop de Qt y de las sesiones WASAPI de Windows.
"""

import os
import sys
import random
from typing import Optional, List
from PyQt6.QtCore import QObject


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

        self._base_dir = base_dir
        self._current_theme = "youtube"  # "youtube" (Máquina del Video), "electric" (Eléctrica), "vintage" (Clásica)
        
        self._backend = "none"

        # Objetos de audio precargados en memoria RAM
        self._hammer_waves: List[object] = []
        self._space_wave: Optional[object] = None
        self._backspace_wave: Optional[object] = None
        self._enter_wave: Optional[object] = None
        self._bell_wave: Optional[object] = None

        self._pool_idx = 0
        self._pool_size = 1
        self._last_key_was_dot: bool = False
        self._init_audio()

    def set_theme(self, theme_name: str):
        """Cambia entre 'youtube' (Sonido 1), 'thock' (Sonido 4), 'electric' (Sonido 2) y 'vintage' (Sonido 3)."""
        if theme_name not in ("youtube", "thock", "electric", "vintage"):
            theme_name = "youtube"
        self._current_theme = theme_name
        self._load_current_theme_sounds()

    def get_theme(self) -> str:
        return self._current_theme

    def _get_theme_dir(self) -> str:
        if self._current_theme == "youtube":
            p = os.path.join(self._base_dir, "assets", "sounds", "youtube_typewriter")
            if os.path.isdir(p):
                return p
        elif self._current_theme == "thock":
            p = os.path.join(self._base_dir, "assets", "sounds", "thock_asmr")
            if os.path.isdir(p):
                return p
        elif self._current_theme == "electric":
            p = os.path.join(self._base_dir, "assets", "sounds", "electric")
            if os.path.isdir(p):
                return p
        # Fallback a vintage / aura
        p = os.path.join(self._base_dir, "assets", "sounds", "aura")
        if not os.path.isdir(p):
            p = os.path.join(self._base_dir, "assets", "sounds", "olivetti")
        return p

    def _init_audio(self):
        """Precarga todos los archivos de sonido en memoria usando el mejor backend disponible."""
        # 1. Intentar pygame.mixer (robusto, polifónico, 32 canales, no crashea con hilos rápidos)
        try:
            import pygame
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(32)
            self._backend = "pygame"
            self._load_pygame(pygame)
            return
        except Exception as e:
            print(f"[SND] pygame no disponible: {e}")

        # 2. Intentar simpleaudio como fallback
        try:
            import simpleaudio as sa
            self._backend = "simpleaudio"
            self._load_simpleaudio(sa)
            return
        except Exception as e:
            print(f"[SND] simpleaudio no disponible: {e}")

        # 3. Fallback winsound en Windows si fallan los anteriores
        if sys.platform == "win32":
            self._backend = "winsound"
            self._load_file_paths()

    def _load_current_theme_sounds(self):
        """Recarga los archivos de sonido en memoria según el tema seleccionado."""
        self._hammer_waves.clear()
        if self._backend == "pygame":
            import pygame
            self._load_pygame(pygame)
        elif self._backend == "simpleaudio":
            import simpleaudio as sa
            self._load_simpleaudio(sa)
        elif self._backend == "winsound":
            self._load_file_paths()

    def _load_simpleaudio(self, sa):
        sounds_dir = self._get_theme_dir()
        hammer_files = sorted(
            f for f in os.listdir(sounds_dir)
            if f.startswith("hammer_") and f.endswith(".wav")
        ) if os.path.isdir(sounds_dir) else []

        if not hammer_files and os.path.isfile(os.path.join(sounds_dir, "hammer_00.wav")):
            hammer_files = ["hammer_00.wav"]

        for f in hammer_files:
            try:
                wave = sa.WaveObject.from_wave_file(os.path.join(sounds_dir, f))
                self._hammer_waves.append(wave)
            except Exception:
                pass

        self._pool_size = max(1, len(self._hammer_waves))

        def _safe_load(fname):
            p = os.path.join(sounds_dir, fname)
            if os.path.isfile(p):
                try:
                    return sa.WaveObject.from_wave_file(p)
                except Exception:
                    return None
            return None

        self._space_wave = _safe_load("space.wav")
        self._backspace_wave = _safe_load("backspace.wav")
        self._enter_wave = _safe_load("enter.wav")
        self._bell_wave = _safe_load("bell.wav")

    def _load_pygame(self, pygame):
        sounds_dir = self._get_theme_dir()
        hammer_files = sorted(
            f for f in os.listdir(sounds_dir)
            if f.startswith("hammer_") and f.endswith(".wav")
        ) if os.path.isdir(sounds_dir) else []

        if not hammer_files and os.path.isfile(os.path.join(sounds_dir, "hammer_00.wav")):
            hammer_files = ["hammer_00.wav"]

        for f in hammer_files:
            try:
                snd = pygame.mixer.Sound(os.path.join(sounds_dir, f))
                self._hammer_waves.append(snd)
            except Exception:
                pass

        self._pool_size = max(1, len(self._hammer_waves))

        def _safe_load(fname):
            p = os.path.join(sounds_dir, fname)
            if os.path.isfile(p):
                try:
                    return pygame.mixer.Sound(p)
                except Exception:
                    return None
            return None

        self._space_wave = _safe_load("space.wav")
        self._backspace_wave = _safe_load("backspace.wav")
        self._enter_wave = _safe_load("enter.wav")
        self._bell_wave = _safe_load("bell.wav")

    def _load_file_paths(self):
        sounds_dir = self._get_theme_dir()
        self._hammer_paths = sorted(
            os.path.join(sounds_dir, f)
            for f in os.listdir(sounds_dir)
            if f.startswith("hammer_") and f.endswith(".wav")
        ) if os.path.isdir(sounds_dir) else []
        self._space_path = os.path.join(sounds_dir, "space.wav")
        self._backspace_path = os.path.join(sounds_dir, "backspace.wav")
        self._enter_path = os.path.join(sounds_dir, "enter.wav")
        self._bell_path = os.path.join(sounds_dir, "bell.wav")
        self._pool_size = max(1, len(self._hammer_paths))

    def _play_object(self, obj):
        if obj is None:
            return
        try:
            if self._backend == "simpleaudio":
                obj.play()
            elif self._backend == "pygame":
                obj.play()
        except Exception:
            pass

    @classmethod
    def instance(cls) -> "AuraSoundEngine":
        if cls._instance is None:
            cls._instance = AuraSoundEngine()
        return cls._instance

    def toggle(self) -> bool:
        self.enabled = not self.enabled
        return self.enabled

    def _play_stroke(self):
        if not self.enabled:
            return
        if self._hammer_waves:
            wave = self._hammer_waves[self._pool_idx]
            self._play_object(wave)
            self._pool_idx = random.randint(0, self._pool_size - 1)

    def on_key_pressed(self, text: str, is_enter: bool = False,
                       is_space: bool = False, is_backspace: bool = False):
        if not self.enabled:
            return

        if is_enter:
            self._chars_in_line = 0
            self._play_object(self._enter_wave)
            # Si la tecla previa fue un punto (.), hacer sonar la campanilla
            if self.bell_enabled and self._last_key_was_dot:
                self._play_object(self._bell_wave)
            self._last_key_was_dot = False
        elif is_space:
            self._chars_in_line += 1
            self._play_object(self._space_wave)
            self._last_key_was_dot = False
        elif is_backspace:
            self._chars_in_line = max(0, self._chars_in_line - 1)
            self._play_object(self._backspace_wave)
            self._last_key_was_dot = False
        else:
            self._chars_in_line += 1
            # Tocar el martilleo normal para todas las teclas (incluyendo el punto '.')
            self._play_stroke()
            # Registrar si fue punto (.)
            self._last_key_was_dot = (text == ".")

    def ring_bell(self) -> None:
        if not self.enabled:
            return
        self._play_object(self._bell_wave)


# Alias para retrocompatibilidad total
OlivettiSoundEngine = AuraSoundEngine
