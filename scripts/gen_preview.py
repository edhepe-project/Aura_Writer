import struct, math, random, wave, io, base64, os, sys

random.seed(7)
SR = 44100

def to_b64(samples):
    data = struct.pack('<' + 'h' * len(samples),
                      *[max(-32767, min(32767, int(s * 32767))) for s in samples])
    buf = io.BytesIO()
    with wave.open(buf, 'w') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data)
    return base64.b64encode(buf.getvalue()).decode()

def fade(samples, ms=8):
    n = int(SR * ms / 1000)
    for i in range(min(n, len(samples))):
        samples[-(i+1)] *= i / n
    return samples

def cherry(snap_hz, body_hz, dur_ms, snap_vol=0.88, body_vol=0.65, snap_dec=520, body_dec=95, delay_ms=5):
    """
    Arquitectura Cherry MX de dos etapas:
    Etapa 1 (snap): alta frecuencia, muy corta -> NITIDEZ / crispness
    Etapa 2 (body): frecuencia media-grave, retrasada -> CALOR y cuerpo
    """
    n = int(SR * dur_ms / 1000)
    delay_s = delay_ms / 1000
    out = []
    for i in range(n):
        t = i / SR
        # Snap: el mecanismo de clic (agudo, cortisimo)
        snap = math.sin(2 * math.pi * snap_hz * t) * math.exp(-t * snap_dec) * snap_vol
        snap += random.uniform(-1, 1) * 0.65 * math.exp(-t * snap_dec * 0.75)
        # Body: la camara de resonancia (mas grave, llega 5ms despues)
        td = max(0.0, t - delay_s)
        body = math.sin(2 * math.pi * body_hz * td) * math.exp(-td * body_dec) * body_vol
        body += math.sin(2 * math.pi * body_hz * 1.5 * td) * math.exp(-td * body_dec * 1.6) * body_vol * 0.15
        # Sub-golpe fisico (da peso, no pitch)
        sub = math.sin(2 * math.pi * 95 * t) * math.exp(-t * 440) * 0.22
        out.append(snap + body + sub)
    peak = max(abs(s) for s in out) or 1
    return fade([s / peak * 0.84 for s in out])

def water_drop(dur_ms=65, f_start=1300, f_end=480, impact_vol=0.80,
               bubble_vol=0.75, bubble_decay=28, glide_speed=18):
    n = int(SR * dur_ms / 1000)
    out = []
    phase = 0.0
    dt = 1.0 / SR
    for i in range(n):
        t = i / SR
        impact = random.uniform(-1, 1) * impact_vol * math.exp(-t * 700)
        freq = f_end + (f_start - f_end) * math.exp(-glide_speed * t)
        phase += 2 * math.pi * freq * dt
        bubble = math.sin(phase) * math.exp(-bubble_decay * t) * bubble_vol
        sub = math.sin(2 * math.pi * 80 * t) * math.exp(-t * 500) * 0.18
        out.append(impact + bubble + sub)
    peak = max(abs(s) for s in out) or 1
    return fade([s / peak * 0.84 for s in out], ms=12)


def hybrid(dur_ms=55, snap_hz=3400, f_start=1100, f_end=420,
           snap_vol=0.88, bubble_vol=0.70, snap_dec=560,
           bubble_decay=32, glide_speed=20):
    n = int(SR * dur_ms / 1000)
    out = []
    phase = 0.0
    dt = 1.0 / SR
    for i in range(n):
        t = i / SR
        snap = math.sin(2 * math.pi * snap_hz * t) * math.exp(-t * snap_dec) * snap_vol
        snap += random.uniform(-1, 1) * 0.60 * math.exp(-t * snap_dec * 0.75)
        freq = f_end + (f_start - f_end) * math.exp(-glide_speed * t)
        phase += 2 * math.pi * freq * dt
        bubble = math.sin(phase) * math.exp(-bubble_decay * t) * bubble_vol
        sub = math.sin(2 * math.pi * 88 * t) * math.exp(-t * 460) * 0.20
        out.append(snap + bubble + sub)
    peak = max(abs(s) for s in out) or 1
    return fade([s / peak * 0.84 for s in out], ms=10)


def sequence(samples, count=10, gap_ms=115):
    gap = int(SR * gap_ms / 1000)
    total = len(samples) + gap * (count - 1)
    out = [0.0] * total
    for i in range(count):
        for j, s in enumerate(samples):
            if i * gap + j < total:
                out[i * gap + j] += s
    peak = max(abs(x) for x in out) or 1
    return [x / peak * 0.82 for x in out]

variations = [
    ("CrispMX",
     "3400 Hz snap - 32ms - El que te gusto",
     cherry(3400, 520, 32, snap_vol=0.96, body_vol=0.55, snap_dec=590, body_dec=105, delay_ms=4)),
    ("GotaPura",
     "1300->480 Hz - 65ms - Gota de agua pura",
     water_drop(65, f_start=1300, f_end=480, impact_vol=0.75, bubble_vol=0.82, bubble_decay=26, glide_speed=16)),
    ("GotaBrillante",
     "1600->560 Hz - 50ms - Gota mas corta y brillante",
     water_drop(50, f_start=1600, f_end=560, impact_vol=0.88, bubble_vol=0.74, bubble_decay=34, glide_speed=24)),
    ("Fusion",
     "Snap CrispMX + burbuja de agua - 55ms",
     hybrid(55, snap_hz=3400, f_start=1100, f_end=420, snap_vol=0.90, bubble_vol=0.72, snap_dec=560, bubble_decay=30, glide_speed=20)),
    ("FusionSuave",
     "Snap suave + burbuja calida - 60ms",
     hybrid(60, snap_hz=2800, f_start=1000, f_end=380, snap_vol=0.72, bubble_vol=0.82, snap_dec=470, bubble_decay=24, glide_speed=15)),
]

cards_html = ""
for name, desc, samples in variations:
    s_b64 = to_b64(list(samples))
    q_b64 = to_b64(sequence(list(samples)))
    cards_html += f"""
    <div class="card" id="card-{name}">
      <div class="card-name">{name}</div>
      <div class="card-desc">{desc}</div>
      <div class="progress-bar"><div class="progress-fill" id="fill-{name}"></div></div>
      <div class="btns">
        <button class="btn-single" onclick="play('{name}','{s_b64}')">&#9654; Un golpe</button>
        <button class="btn-seq"    onclick="play('{name}','{q_b64}')">&#9000; Secuencia</button>
      </div>
    </div>"""

html = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Aura Writer - Preview de Sonidos</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0d0d12;color:#e0e0ec;min-height:100vh;padding:48px 24px}
h1{text-align:center;font-size:30px;font-weight:300;letter-spacing:.18em;color:#c8a96e;margin-bottom:8px}
.sub{text-align:center;color:#555;font-size:13px;margin-bottom:48px;letter-spacing:.06em}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px;max-width:920px;margin:0 auto}
.card{background:#15151f;border:1px solid #252535;border-radius:18px;padding:28px;transition:border-color .2s,transform .15s,background .2s}
.card:hover{border-color:#c8a96e33;transform:translateY(-3px)}
.card.active{border-color:#c8a96e;background:#1a192a}
.card-name{font-size:18px;font-weight:600;color:#e8e8f4;margin-bottom:6px}
.card-desc{font-size:12px;color:#555;margin-bottom:20px;line-height:1.6}
.progress-bar{height:3px;background:#252535;border-radius:2px;margin-bottom:18px;overflow:hidden}
.progress-fill{height:100%;width:0%;background:#c8a96e;border-radius:2px;transition:width .04s linear}
.btns{display:flex;gap:10px}
button{flex:1;padding:10px 0;border:none;border-radius:9px;font-size:13px;font-weight:500;cursor:pointer;transition:opacity .15s,transform .1s;letter-spacing:.02em}
button:active{transform:scale(.96)}
.btn-single{background:#252535;color:#a0a0c0}
.btn-single:hover{background:#2e2e42}
.btn-seq{background:#c8a96e18;color:#c8a96e;border:1px solid #c8a96e33}
.btn-seq:hover{background:#c8a96e28}
.footer{text-align:center;margin-top:52px;color:#383848;font-size:12px;line-height:1.8}
</style>
</head>
<body>
<h1>Aura Writer</h1>
<p class="sub">Escucha cada variacion y di cual prefieres</p>
<div class="grid">""" + cards_html + """</div>
<p class="footer">Haz clic en "Un golpe" o en "Secuencia" para escuchar como suena al escribir rapido</p>
<script>
let cur = null, curName = null;
function play(name, b64) {
  if (cur) { cur.pause(); cur = null; }
  if (curName) {
    document.getElementById('card-' + curName).classList.remove('active');
    document.getElementById('fill-' + curName).style.width = '0%';
  }
  const audio = new Audio('data:audio/wav;base64,' + b64);
  cur = audio; curName = name;
  document.getElementById('card-' + name).classList.add('active');
  const fill = document.getElementById('fill-' + name);
  audio.addEventListener('timeupdate', () => {
    fill.style.width = (audio.currentTime / audio.duration * 100) + '%';
  });
  audio.addEventListener('ended', () => {
    fill.style.width = '0%';
    document.getElementById('card-' + name).classList.remove('active');
    curName = null;
  });
  audio.play();
}
</script>
</body>
</html>"""

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sound_preview.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)
print('OK:' + out)
