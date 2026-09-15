import struct, math, random, wave, io, base64, os

random.seed(42)
SR = 44100

def to_b64(samples):
    data = struct.pack('<' + 'h' * len(samples),
                      *[max(-32767, min(32767, int(s * 32767))) for s in samples])
    buf = io.BytesIO()
    with wave.open(buf, 'w') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(data)
    return base64.b64encode(buf.getvalue()).decode()

def fade(samples, ms=10):
    n = int(SR * ms / 1000)
    n = min(n, len(samples) // 4)  # nunca mas del 25% del sonido
    for i in range(n):
        samples[-(i+1)] *= i / n
    return samples

def quartz(fund_hz, dur_ms, snap_vol=0.55, snap_decay=380, decay_base=110, sub_vol=0.10, uniform_decay=False):
    """
    Choque de dos piedras de cuarzo.
    uniform_decay=True: todos los parciales decaen igual (evita doble sonido en duraciones cortas)
    """
    n = int(SR * dur_ms / 1000)
    ratios = [1.000, 1.414, 1.732, 2.121, 2.646]
    amps   = [0.70,  0.42,  0.28,  0.16,  0.09]
    if uniform_decay:
        # Todos los parciales mueren al mismo ritmo -> sonido unitario, sin capas
        decays = [decay_base * 1.2] * len(ratios)
    else:
        decays = [decay_base * (1.0 + r * 0.40) for r in ratios]
    out = []
    for i in range(n):
        t = i / SR
        snap = random.uniform(-1, 1) * snap_vol * math.exp(-t * snap_decay)
        mineral = sum(
            math.sin(2 * math.pi * fund_hz * r * t) * math.exp(-t * d) * a
            for r, d, a in zip(ratios, decays, amps)
        )
        sub = math.sin(2 * math.pi * 65 * t) * math.exp(-t * 650) * sub_vol
        out.append(snap + mineral + sub)
    peak = max(abs(s) for s in out) or 1
    return fade([s / peak * 0.84 for s in out])

def sequence(samples, count=10, gap_ms=110):
    gap = int(SR * gap_ms / 1000)
    total = len(samples) + gap * (count - 1)
    out = [0.0] * total
    for i in range(count):
        for j, s in enumerate(samples):
            if i * gap + j < total:
                out[i * gap + j] += s
    peak = max(abs(x) for x in out) or 1
    return [x / peak * 0.82 for x in out]

def lerp(a, b, t): return a + (b - a) * t

# Extremo A: Resonante
A = dict(dur=44, snap_vol=0.68, snap_decay=420, decay_base=100, sub_vol=0.07, uniform_decay=False)
# Extremo B: UltraSeco
B = dict(dur=28, snap_vol=0.80, snap_decay=520, decay_base=200, sub_vol=0.04, uniform_decay=True)

steps = [0.0, 0.25, 0.50, 0.75, 1.0]
labels = ["A-Resonante", "A25-MasLargo", "AB-Medio", "B75-MasCorto", "B-UltraSeco"]
descs  = [
    "44ms - Resonante (extremo A)",
    "40ms - Mas largo, algo de resonancia",
    "36ms - Punto medio exacto",
    "32ms - Mas corto, casi seco",
    "28ms - UltraSeco (extremo B)",
]

variations = []
for label, desc, t in zip(labels, descs, steps):
    ud = B["uniform_decay"] if t >= 0.5 else A["uniform_decay"]
    variations.append((
        label, f"520 Hz - {desc}",
        quartz(
            520,
            int(round(lerp(A["dur"], B["dur"], t))),
            snap_vol    = lerp(A["snap_vol"],    B["snap_vol"],    t),
            snap_decay  = lerp(A["snap_decay"],  B["snap_decay"],  t),
            decay_base  = lerp(A["decay_base"],  B["decay_base"],  t),
            sub_vol     = lerp(A["sub_vol"],     B["sub_vol"],     t),
            uniform_decay = ud,
        )
    ))

cards = ""
for name, desc, s in variations:
    sb = to_b64(list(s))
    qb = to_b64(sequence(list(s)))
    cards += f"""<div class="card" id="c{name}">
  <div class="cn">{name}</div><div class="cd">{desc}</div>
  <div class="pb"><div class="pf" id="f{name}"></div></div>
  <div class="bt">
    <button class="bs" onclick="pl('{name}','{sb}')">&#9654; Un golpe</button>
    <button class="bq" onclick="pl('{name}','{qb}')">&#9000; Secuencia</button>
  </div></div>"""

html = """<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<title>Aura Writer - Cuarzo</title><style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0d0d12;color:#e0e0ec;padding:48px 24px}
h1{text-align:center;font-size:28px;font-weight:300;letter-spacing:.16em;color:#c8a96e;margin-bottom:6px}
.sub{text-align:center;color:#555;font-size:13px;margin-bottom:44px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px;max-width:900px;margin:0 auto}
.card{background:#15151f;border:1px solid #252535;border-radius:16px;padding:26px;transition:border-color .2s,transform .15s}
.card:hover{border-color:#c8a96e33;transform:translateY(-2px)}
.card.active{border-color:#c8a96e;background:#1a192a}
.cn{font-size:17px;font-weight:600;color:#e8e8f4;margin-bottom:5px}
.cd{font-size:12px;color:#555;margin-bottom:18px;line-height:1.5}
.pb{height:3px;background:#252535;border-radius:2px;margin-bottom:16px;overflow:hidden}
.pf{height:100%;width:0%;background:#c8a96e;border-radius:2px;transition:width .04s}
.bt{display:flex;gap:8px}
button{flex:1;padding:9px 0;border:none;border-radius:8px;font-size:13px;font-weight:500;cursor:pointer;transition:transform .1s}
button:active{transform:scale(.96)}
.bs{background:#252535;color:#a0a0c0}.bs:hover{background:#2e2e42}
.bq{background:#c8a96e18;color:#c8a96e;border:1px solid #c8a96e33}.bq:hover{background:#c8a96e28}
.foot{text-align:center;margin-top:44px;color:#383848;font-size:12px}
</style></head><body>
<h1>Aura Writer</h1>
<p class="sub">Piedras de cuarzo - Variaciones de frecuencia fundamental</p>
<div class="grid">""" + cards + """</div>
<p class="foot">Haz clic en "Un golpe" o "Secuencia". Di cual numero/nombre prefieres.</p>
<script>
let cur=null,cn=null;
function pl(name,b64){
  if(cur){cur.pause();cur=null;}
  if(cn){document.getElementById('c'+cn).classList.remove('active');document.getElementById('f'+cn).style.width='0%';}
  const a=new Audio('data:audio/wav;base64,'+b64);
  cur=a;cn=name;
  document.getElementById('c'+name).classList.add('active');
  const f=document.getElementById('f'+name);
  a.addEventListener('timeupdate',()=>{f.style.width=(a.currentTime/a.duration*100)+'%';});
  a.addEventListener('ended',()=>{f.style.width='0%';document.getElementById('c'+name).classList.remove('active');cn=null;});
  a.play();
}
</script></body></html>"""

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sound_preview.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)
print('OK: ' + out)
