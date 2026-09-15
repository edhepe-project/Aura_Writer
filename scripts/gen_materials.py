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

def fade(samples, ms=8):
    n = min(int(SR * ms / 1000), len(samples) // 4)
    for i in range(n): samples[-(i+1)] *= i / n
    return samples

def normalize(samples, level=0.84):
    peak = max(abs(s) for s in samples) or 1
    return [s / peak * level for s in samples]

# ── MARMOL ──────────────────────────────────────────────────────────────
# Muy duro, impacto instantaneo, decae rapidisimo, partiales agudas e inharmonicas
def marmol(dur_ms=32):
    ratios = [1.000, 1.618, 2.236, 3.141, 4.000]  # Muy inharmonico (fractal-like)
    amps   = [0.65,  0.38,  0.22,  0.12,  0.06]
    fund   = 680  # mas agudo que cuarzo (mas duro)
    decay  = 220  # decae muy rapido
    n = int(SR * dur_ms / 1000)
    out = []
    for i in range(n):
        t = i / SR
        snap    = random.uniform(-1,1) * 0.80 * math.exp(-t * 600)
        mineral = sum(math.sin(2*math.pi*fund*r*t) * math.exp(-t*decay) * a
                      for r,d,a in zip(ratios,[decay]*len(ratios),amps))
        out.append(snap + mineral)
    return fade(normalize(out))

# ── EBANO ───────────────────────────────────────────────────────────────
# Madera densa: mas harmonico que piedra, calido, fundamental grave
def ebano(dur_ms=45):
    # Ratios mas harmonicos (madera vibra mas regularmente que piedra)
    ratios = [1.000, 1.980, 2.950, 3.900]
    amps   = [0.72,  0.32,  0.15,  0.06]
    fund   = 340  # calido y grave
    decays = [95, 140, 190, 250]
    n = int(SR * dur_ms / 1000)
    out = []
    for i in range(n):
        t = i / SR
        snap = random.uniform(-1,1) * 0.38 * math.exp(-t * 280)
        wood = sum(math.sin(2*math.pi*fund*r*t) * math.exp(-t*d) * a
                   for r,d,a in zip(ratios,decays,amps))
        sub  = math.sin(2*math.pi*90*t) * math.exp(-t*200) * 0.20
        out.append(snap + wood + sub)
    return fade(normalize(out))

# ── BAMBU ───────────────────────────────────────────────────────────────
# Hueco resonante: fundamental fuerte, armonico fuerte a la octava, decae medio
def bambu(dur_ms=50):
    fund = 420
    n = int(SR * dur_ms / 1000)
    out = []
    for i in range(n):
        t = i / SR
        snap   = random.uniform(-1,1) * 0.45 * math.exp(-t * 320)
        hollow = math.sin(2*math.pi*fund*t) * math.exp(-t*78) * 0.75
        # La octava es muy fuerte en bambu (cavidad cilindrica)
        hollow+= math.sin(2*math.pi*fund*2*t) * math.exp(-t*110) * 0.45
        hollow+= math.sin(2*math.pi*fund*3*t) * math.exp(-t*160) * 0.18
        sub    = math.sin(2*math.pi*100*t) * math.exp(-t*250) * 0.14
        out.append(snap + hollow + sub)
    return fade(normalize(out))

# ── OBSIDIANA ────────────────────────────────────────────────────────────
# Vidrio volcanico: muy vivo, casi cristalino, tono alto con cola brillante
def obsidiana(dur_ms=38):
    fund   = 820  # alto, casi campanilla
    ratios = [1.000, 1.500, 2.000, 2.750]
    amps   = [0.68,  0.35,  0.20,  0.10]
    decays = [130, 170, 220, 280]
    n = int(SR * dur_ms / 1000)
    out = []
    for i in range(n):
        t = i / SR
        snap  = random.uniform(-1,1) * 0.72 * math.exp(-t * 480)
        glass = sum(math.sin(2*math.pi*fund*r*t) * math.exp(-t*d) * a
                    for r,d,a in zip(ratios,decays,amps))
        out.append(snap + glass)
    return fade(normalize(out))

# ── CERAMICA ─────────────────────────────────────────────────────────────
# Porcelana: limpia, brillo medio, partiales casi harmonicas pero algo inharmonicas
def ceramica(dur_ms=40):
    fund   = 560
    ratios = [1.000, 1.760, 2.560, 3.420]
    amps   = [0.70,  0.40,  0.20,  0.08]
    decays = [105, 145, 190, 240]
    n = int(SR * dur_ms / 1000)
    out = []
    for i in range(n):
        t = i / SR
        snap  = random.uniform(-1,1) * 0.55 * math.exp(-t * 400)
        body  = sum(math.sin(2*math.pi*fund*r*t) * math.exp(-t*d) * a
                    for r,d,a in zip(ratios,decays,amps))
        sub   = math.sin(2*math.pi*80*t) * math.exp(-t*400) * 0.10
        out.append(snap + body + sub)
    return fade(normalize(out))

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

variations = [
    ("Marmol",    "680 Hz - 32ms - Muy duro, impacto seco e instantaneo",  list(marmol())),
    ("Ebano",     "340 Hz - 45ms - Madera densa, calido y preciso",         list(ebano())),
    ("Bambu",     "420 Hz - 50ms - Resonancia hueca, caracteristico",       list(bambu())),
    ("Obsidiana", "820 Hz - 38ms - Vidrio volcanico, vivo y cristalino",    list(obsidiana())),
    ("Ceramica",  "560 Hz - 40ms - Porcelana, limpio sin ser metalico",     list(ceramica())),
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
    <button class="bq" onclick="pl('{name}','{qb}')">&#9000; Secuencia</button>
  </div></div>"""

html = """<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<title>Aura Writer - Materiales</title><style>
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
<p class="sub">Explora materiales - Cada uno tiene una firma acustica distinta</p>
<div class="grid">""" + cards + """</div>
<p class="foot">Un golpe = click individual &nbsp;|&nbsp; Secuencia = 10 teclas seguidas</p>
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
