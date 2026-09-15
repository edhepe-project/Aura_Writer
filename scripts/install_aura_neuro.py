import struct, math, random, wave, os

random.seed(42)
SR = 44100

def write_wav(path, samples):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    data = struct.pack('<' + 'h' * len(samples),
                      *[max(-32767, min(32767, int(s * 32767))) for s in samples])
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data)

def fade(samples, ms=4):
    n = min(int(SR * ms / 1000), len(samples) // 4)
    for i in range(n): samples[-(i+1)] *= (i / n)
    return samples

def normalize(samples, level=0.85):
    peak = max(abs(s) for s in samples) or 1
    return [s / peak * level for s in samples]

def aura_neuro_432(dur_ms=26, fund=432.0, snap_vol=0.82, snap_decay=700):
    """
    Aura Neuro-432: Clic táctil de 432 Hz en afinación pitagórica.
    """
    n = int(SR * dur_ms / 1000)
    ratios = [1.0, 1.5, 2.0, 3.0]
    amps   = [0.70, 0.30, 0.15, 0.05]
    decays = [180, 260, 350, 480]
    out = []
    for i in range(n):
        t = i / SR
        snap = random.uniform(-1, 1) * snap_vol * math.exp(-t * snap_decay)
        body = sum(math.sin(2 * math.pi * (fund * r) * t) * math.exp(-t * d) * a 
                   for r, d, a in zip(ratios, decays, amps))
        out.append(snap + body)
    return fade(normalize(out, level=0.85))

def aura_neuro_space(dur_ms=30):
    # Espacio: Tono un poco más bajo (324 Hz) con toque mullido
    n = int(SR * dur_ms / 1000)
    fund = 324.0
    ratios = [1.0, 1.5, 2.0]
    amps   = [0.75, 0.25, 0.10]
    decays = [140, 220, 310]
    out = []
    for i in range(n):
        t = i / SR
        snap = random.uniform(-1, 1) * 0.55 * math.exp(-t * 500)
        body = sum(math.sin(2 * math.pi * (fund * r) * t) * math.exp(-t * d) * a 
                   for r, d, a in zip(ratios, decays, amps))
        sub = math.sin(2 * math.pi * 108 * t) * math.exp(-t * 180) * 0.12
        out.append(snap + body + sub)
    return fade(normalize(out, level=0.78))

def aura_neuro_backspace(dur_ms=24):
    # Backspace: Más seco y ligero (486 Hz)
    n = int(SR * dur_ms / 1000)
    fund = 486.0
    ratios = [1.0, 2.0]
    amps   = [0.75, 0.25]
    decays = [220, 380]
    out = []
    for i in range(n):
        t = i / SR
        snap = random.uniform(-1, 1) * 0.70 * math.exp(-t * 750)
        body = sum(math.sin(2 * math.pi * (fund * r) * t) * math.exp(-t * d) * a 
                   for r, d, a in zip(ratios, decays, amps))
        out.append(snap + body)
    return fade(normalize(out, level=0.80))

def aura_neuro_enter(dur_ms=36):
    # Enter: Tono de confirmación armónica profunda (216 Hz -> 432 Hz)
    n = int(SR * dur_ms / 1000)
    fund = 216.0
    ratios = [1.0, 2.0, 3.0, 4.0]
    amps   = [0.65, 0.35, 0.20, 0.10]
    decays = [120, 180, 240, 320]
    out = []
    for i in range(n):
        t = i / SR
        snap = random.uniform(-1, 1) * 0.65 * math.exp(-t * 450)
        body = sum(math.sin(2 * math.pi * (fund * r) * t) * math.exp(-t * d) * a 
                   for r, d, a in zip(ratios, decays, amps))
        out.append(snap + body)
    return fade(normalize(out, level=0.88))

def aura_neuro_bell(dur_ms=180):
    # Campana Zen: Campana armónica pura en 864 Hz (octava de 432Hz)
    n = int(SR * dur_ms / 1000)
    fund = 864.0
    ratios = [1.0, 1.5, 2.0, 2.76, 4.0]
    amps   = [0.65, 0.25, 0.15, 0.10, 0.05]
    decays = [22, 35, 45, 60, 90]
    out = []
    for i in range(n):
        t = i / SR
        snap = random.uniform(-1, 1) * 0.30 * math.exp(-t * 400)
        body = sum(math.sin(2 * math.pi * (fund * r) * t) * math.exp(-t * d) * a 
                   for r, d, a in zip(ratios, decays, amps))
        out.append(snap + body)
    return fade(normalize(out, level=0.75), ms=25)

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sounds_dir = os.path.join(base_dir, "assets", "sounds", "olivetti")
special_dir = os.path.join(sounds_dir, "special")

# Generar sonido principal para todas las teclas
stroke_sound = aura_neuro_432()
space_sound = aura_neuro_space()
backspace_sound = aura_neuro_backspace()
enter_sound = aura_neuro_enter()
bell_sound = aura_neuro_bell()

# 1. Martillos (27 teclas - todas con la consistencia zen de Aura Neuro-432)
for i in range(27):
    path = os.path.join(sounds_dir, f"hammer_{i:02d}.wav")
    write_wav(path, stroke_sound)

# 2. Especiales principales
write_wav(os.path.join(sounds_dir, "space.wav"), space_sound)
write_wav(os.path.join(sounds_dir, "backspace.wav"), backspace_sound)
write_wav(os.path.join(sounds_dir, "enter.wav"), enter_sound)
write_wav(os.path.join(sounds_dir, "bell.wav"), bell_sound)

# 3. Números y puntuación
for n in range(10):
    write_wav(os.path.join(special_dir, f"num_{n}.wav"), stroke_sound)

punct_files = [
    "punct_dot.wav", "punct_comma.wav", "punct_colon.wav", "punct_semicolon.wav",
    "punct_quest.wav", "punct_exclam.wav", "punct_quote.wav", "punct_dash.wav",
    "punct_paren.wav", "punct_symbol.wav"
]
for pf in punct_files:
    write_wav(os.path.join(special_dir, pf), stroke_sound)

print("Aura Neuro-432 instalado con exito en assets/sounds/olivetti/")
