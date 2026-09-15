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

# ── AURA SINGULARITY 528 (La Obra Maestra: Phi Ratio + Clic Cerámico-Mineral) ──
def aura_singularity_528(dur_ms=28):
    n = int(SR * dur_ms / 1000)
    fund = 528.0
    phi = (1.0 + math.sqrt(5.0)) / 2.0  # 1.6180339887...
    ratios = [1.0, phi, phi**2 / 2.0, phi**2, phi**3 / 2.0]
    amps   = [0.65, 0.28, 0.15, 0.07, 0.03]
    decays = [170, 240, 320, 420, 560]
    
    out = []
    for i in range(n):
        t = i / SR
        snap = random.uniform(-1, 1) * 0.78 * math.exp(-t * 680)
        body = sum(math.sin(2 * math.pi * (fund * r) * t) * math.exp(-t * d) * a 
                   for r, d, a in zip(ratios, decays, amps))
        sub = math.sin(2 * math.pi * 132 * t) * math.exp(-t * 220) * 0.08
        out.append(snap + body + sub)
    return fade(normalize(out, level=0.85))

def aura_singularity_space(dur_ms=26):
    # Espacio: Un suspiro seco y nítido (cuerpo de madera-mineral seco, sin 'blop' sub-grave)
    n = int(SR * dur_ms / 1000)
    fund = 480.0
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    ratios = [1.0, phi, phi**2 / 2.0]
    amps   = [0.65, 0.25, 0.10]
    decays = [200, 300, 420]
    out = []
    for i in range(n):
        t = i / SR
        # Transiente seco y aireado
        snap = random.uniform(-1, 1) * 0.65 * math.exp(-t * 620)
        body = sum(math.sin(2 * math.pi * (fund * r) * t) * math.exp(-t * d) * a 
                   for r, d, a in zip(ratios, decays, amps))
        out.append(snap + body)
    return fade(normalize(out, level=0.75))

def aura_singularity_backspace(dur_ms=25):
    # Backspace: Más seco y ligero (660 Hz)
    n = int(SR * dur_ms / 1000)
    fund = 660.0
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    ratios = [1.0, phi]
    amps   = [0.75, 0.25]
    decays = [220, 380]
    out = []
    for i in range(n):
        t = i / SR
        snap = random.uniform(-1, 1) * 0.72 * math.exp(-t * 720)
        body = sum(math.sin(2 * math.pi * (fund * r) * t) * math.exp(-t * d) * a 
                   for r, d, a in zip(ratios, decays, amps))
        out.append(snap + body)
    return fade(normalize(out, level=0.82))

def aura_singularity_enter(dur_ms=38):
    # Enter: Tono áureo profundo y resolutivo (264 Hz)
    n = int(SR * dur_ms / 1000)
    fund = 264.0
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    ratios = [1.0, phi, 2.0, phi**2]
    amps   = [0.65, 0.30, 0.20, 0.10]
    decays = [120, 170, 230, 310]
    out = []
    for i in range(n):
        t = i / SR
        snap = random.uniform(-1, 1) * 0.60 * math.exp(-t * 480)
        body = sum(math.sin(2 * math.pi * (fund * r) * t) * math.exp(-t * d) * a 
                   for r, d, a in zip(ratios, decays, amps))
        out.append(snap + body)
    return fade(normalize(out, level=0.88))

def aura_singularity_bell(dur_ms=200):
    # Campana Áurea Zen en 1056 Hz (octava superior de 528 Hz)
    n = int(SR * dur_ms / 1000)
    fund = 1056.0
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    ratios = [1.0, phi/1.2, phi, phi**2/2.0, phi**2]
    amps   = [0.65, 0.22, 0.16, 0.10, 0.05]
    decays = [18, 30, 42, 58, 85]
    out = []
    for i in range(n):
        t = i / SR
        snap = random.uniform(-1, 1) * 0.25 * math.exp(-t * 400)
        body = sum(math.sin(2 * math.pi * (fund * r) * t) * math.exp(-t * d) * a 
                   for r, d, a in zip(ratios, decays, amps))
        out.append(snap + body)
    return fade(normalize(out, level=0.75), ms=30)

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sounds_dir = os.path.join(base_dir, "assets", "sounds", "olivetti")
special_dir = os.path.join(sounds_dir, "special")

# Generar sonido principal para todas las teclas
stroke_sound = aura_singularity_528()
space_sound = aura_singularity_space()
backspace_sound = aura_singularity_backspace()
enter_sound = aura_singularity_enter()
bell_sound = aura_singularity_bell()

# 1. Martillos (27 teclas)
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

print("Aura Singularity-528 instalado con exito en assets/sounds/olivetti/")
