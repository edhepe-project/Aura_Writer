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

def fade(samples, ms=5):
    n = min(int(SR * ms / 1000), len(samples) // 4)
    for i in range(n): samples[-(i+1)] *= (i / n)
    return samples

def normalize(samples, level=0.85):
    peak = max(abs(s) for s in samples) or 1
    return [s / peak * level for s in samples]

# 1. JADE NEGRO (Piedra preciosa ultra densa, impacto seco y aterciopelado)
def jade_negro(dur_ms=28):
    fund = 720
    ratios = [1.000, 1.587, 2.210, 3.120]
    amps   = [0.70,  0.30,  0.15,  0.06]
    decays = [170,   220,   290,   380]
    n = int(SR * dur_ms / 1000)
    out = []
    for i in range(n):
        t = i / SR
        snap = random.uniform(-1,1) * 0.78 * math.exp(-t * 580)
        body = sum(math.sin(2*math.pi*fund*r*t) * math.exp(-t*d) * a for r,d,a in zip(ratios,decays,amps))
        aura = math.sin(2*math.pi*480*t) * math.exp(-t*190) * 0.08
        out.append(snap + body + aura)
    return fade(normalize(out))

# 2. CUARZO AHUMADO (Clásico, nitidez mineral cortada, pureza 520Hz zen)
def cuarzo_ahumado(dur_ms=30):
    fund = 520
    ratios = [1.000, 1.732, 2.645, 3.873]
    amps   = [0.72,  0.36,  0.18,  0.07]
    decays = [160,   210,   270,   360]
    n = int(SR * dur_ms / 1000)
    out = []
    for i in range(n):
        t = i / SR
        snap = random.uniform(-1,1) * 0.76 * math.exp(-t * 540)
        body = sum(math.sin(2*math.pi*fund*r*t) * math.exp(-t*d) * a for r,d,a in zip(ratios,decays,amps))
        out.append(snap + body)
    return fade(normalize(out))

# 3. GOTA DE ROCA / AGUA ZEN (Impacto inicial preciso de micro-gota sobre piedra)
def gota_roca(dur_ms=31):
    n = int(SR * dur_ms / 1000)
    out = []
    for i in range(n):
        t = i / SR
        # Pitch drop sutil de gota que cae sobre superficie mineral seca
        f = 880 * math.exp(-t * 22)
        snap = random.uniform(-1,1) * 0.70 * math.exp(-t * 560)
        drop = math.sin(2*math.pi*f*t) * math.exp(-t * 155) * 0.75
        drop_oct = math.sin(2*math.pi*(f*1.85)*t) * math.exp(-t * 240) * 0.25
        out.append(snap + drop + drop_oct)
    return fade(normalize(out))

# 4. CRISTAL DE ZAFIRO (Ultra nítido, 860Hz, cristal óptico de reloj de lujo)
def cristal_zafiro(dur_ms=26):
    fund = 860
    ratios = [1.000, 1.414, 2.150, 3.200]
    amps   = [0.65,  0.28,  0.14,  0.05]
    decays = [190,   250,   330,   440]
    n = int(SR * dur_ms / 1000)
    out = []
    for i in range(n):
        t = i / SR
        snap = random.uniform(-1,1) * 0.85 * math.exp(-t * 620)
        glass = sum(math.sin(2*math.pi*fund*r*t) * math.exp(-t*d) * a for r,d,a in zip(ratios,decays,amps))
        out.append(snap + glass)
    return fade(normalize(out))

# 5. CERÁMICA NEGRA MATE (Impacto mate, sordo pero definido, cero fatiga auditiva)
def ceramica_mate(dur_ms=29):
    fund = 640
    ratios = [1.000, 1.680, 2.450]
    amps   = [0.75,  0.28,  0.12]
    decays = [180,   240,   320]
    n = int(SR * dur_ms / 1000)
    out = []
    for i in range(n):
        t = i / SR
        snap = random.uniform(-1,1) * 0.72 * math.exp(-t * 510)
        body = sum(math.sin(2*math.pi*fund*r*t) * math.exp(-t*d) * a for r,d,a in zip(ratios,decays,amps))
        out.append(snap + body)
    return fade(normalize(out))

def sequence(samples, count=12, gap_ms=105):
    gap = int(SR * gap_ms / 1000)
    total = len(samples) + gap * (count - 1)
    out = [0.0] * total
    for i in range(count):
        for j, s in enumerate(samples):
            if i * gap + j < total:
                out[i * gap + j] += s * (0.96 + (i % 3) * 0.03)
    peak = max(abs(x) for x in out) or 1
    return [x / peak * 0.82 for x in out]

variations = [
    ("Jade-Negro", 
     "720 Hz - 28ms - Piedra densa, impacto seco, noble y con fondo hipnótico", 
     list(jade_negro())),

    ("Cuarzo-Ahumado", 
     "520 Hz - 30ms - Mineral puro, timbre cálido, cortado y muy reconocible", 
     list(cuarzo_ahumado())),

    ("Gota-Roca-Zen", 
     "Micro-gota ~880Hz - 31ms - Seco pero onírico, sensación de fluidez y trance", 
     list(gota_roca())),

    ("Cristal-Zafiro", 
     "860 Hz - 26ms - Ultra nítido, seco y cristalino (estilo reloj de lujo)", 
     list(cristal_zafiro())),

    ("Ceramica-Mate", 
     "640 Hz - 29ms - Golpe mate pulido, cero resonancias molestas, foco total", 
     list(ceramica_mate())),
]

cards = ""
for name, desc, s in variations:
    sb = to_b64(list(s))
    qb = to_b64(sequence(list(s)))
    cards += f"""<div class="card" id="c{name}">
  <div class="cn">{name}</div><div class="cd">{desc}</div>
  <div class="pb"><div class="pf" id="f{name}"></div></div>
  <div class="bt">
    <button class="bs" onclick="pl('{name}','{sb}')">&#9654; Un golpe</button>
    <button class="bq" onclick="pl('{name}','{qb}')">&#9000; Modo Trance (Ritmo)</button>
  </div></div>"""

html = """<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<title>Aura Writer - Nuevos Candidatos</title><style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0b0b10;color:#e0e0ec;padding:48px 24px}
h1{text-align:center;font-size:28px;font-weight:300;letter-spacing:.16em;color:#4ade80;margin-bottom:6px}
.sub{text-align:center;color:#7a7a9a;font-size:13px;margin-bottom:44px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px;max-width:960px;margin:0 auto}
.card{background:#13131d;border:1px solid #232338;border-radius:16px;padding:26px;transition:border-color .2s,transform .15s}
.card:hover{border-color:#4ade8055;transform:translateY(-2px)}
.card.active{border-color:#4ade80;background:#141f1a;box-shadow:0 0 25px rgba(74,222,128,0.12)}
.cn{font-size:17px;font-weight:600;color:#f0f0ff;margin-bottom:5px}
.cd{font-size:12px;color:#787890;margin-bottom:18px;line-height:1.5}
.pb{height:3px;background:#232338;border-radius:2px;margin-bottom:16px;overflow:hidden}
.pf{height:100%;width:0%;background:#4ade80;border-radius:2px;transition:width .04s}
.bt{display:flex;gap:8px}
button{flex:1;padding:10px 0;border:none;border-radius:8px;font-size:13px;font-weight:500;cursor:pointer;transition:all .12s}
button:active{transform:scale(.96)}
.bs{background:#232338;color:#a0a0c8}.bs:hover{background:#2e2e4a;color:#fff}
.bq{background:#4ade8018;color:#4ade80;border:1px solid #4ade8044}.bq:hover{background:#4ade8028;color:#fff}
.foot{text-align:center;margin-top:44px;color:#48485e;font-size:12px}
</style></head><body>
<h1>Aura Writer &mdash; Tercera Opci&oacute;n</h1>
<p class="sub">Nuevos materiales afinados para nitidez, impacto seco y trance on&iacute;rico</p>
<div class="grid">""" + cards + """</div>
<p class="foot">Pulsa <strong>Modo Trance (Ritmo)</strong> para comparar la sensaci&oacute;n de flujo continuo.</p>
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
