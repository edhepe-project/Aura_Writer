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

def fade(samples, ms=4):
    n = min(int(SR * ms / 1000), len(samples) // 4)
    for i in range(n): samples[-(i+1)] *= (i / n)
    return samples

def normalize(samples, level=0.85):
    peak = max(abs(s) for s in samples) or 1
    return [s / peak * level for s in samples]

# ── 1. AURA SINGULARITY (La Obra Maestra: Golden Ratio + Clic Cerámico-Mineral) ──
def aura_singularity(dur_ms=28):
    """
    Fundamento: 528 Hz (Frecuencia de reparación / tono central áureo).
    Ataque: Transiente de 1.8ms en banda 3.2kHz (clic táctil instantáneo).
    Cuerpo: 5 armónicos en proporción Phi (1.6180339...) que decaen exponencialmente.
    Cola: Cero ruido residual a los 28ms exactos para no empastar ráfagas rápidas.
    """
    n = int(SR * dur_ms / 1000)
    fund = 528.0
    phi = (1.0 + math.sqrt(5.0)) / 2.0  # 1.6180339887...
    ratios = [1.0, phi, phi**2 / 2.0, phi**2, phi**3 / 2.0]  # Armónicos áureos
    amps   = [0.65, 0.28, 0.15, 0.07, 0.03]
    decays = [170, 240, 320, 420, 560]  # Los armónicos agudos se extinguen primero
    
    out = []
    for i in range(n):
        t = i / SR
        # Transiente de clic háptico ultra-rápido (sensación táctil precisa)
        snap = random.uniform(-1, 1) * 0.78 * math.exp(-t * 680)
        # Cuerpo áureo hipnótico
        body = sum(math.sin(2 * math.pi * (fund * r) * t) * math.exp(-t * d) * a 
                   for r, d, a in zip(ratios, decays, amps))
        # Micro-subtonal 132Hz (sensación de peso físico aterciopelado)
        sub = math.sin(2 * math.pi * 132 * t) * math.exp(-t * 220) * 0.08
        out.append(snap + body + sub)
    return fade(normalize(out))

# ── 2. AURA NEURO-DRIVE 432 (Afinación Pitagórica de Calma Profunda) ───────────
def aura_neuro_432(dur_ms=26):
    """
    Fundamento: 432 Hz + armónicos matemáticos enteros.
    Perfil ultra-seco de 26ms: diseñado para escritura a alta velocidad (>80 WPM).
    Efecto: Estado de trance por pulsación rítmica continua sin fatiga.
    """
    n = int(SR * dur_ms / 1000)
    fund = 432.0
    ratios = [1.0, 1.5, 2.0, 3.0]
    amps   = [0.70, 0.30, 0.15, 0.05]
    decays = [180, 260, 350, 480]
    out = []
    for i in range(n):
        t = i / SR
        snap = random.uniform(-1, 1) * 0.82 * math.exp(-t * 700)
        body = sum(math.sin(2 * math.pi * (fund * r) * t) * math.exp(-t * d) * a 
                   for r, d, a in zip(ratios, decays, amps))
        out.append(snap + body)
    return fade(normalize(out))

# ── 3. AURA HYPER-CRISP (Cristal Cuántico / Máxima Nitidez Quirúrgica) ─────────
def aura_hyper_crisp(dur_ms=24):
    """
    Fundamento: 640 Hz.
    Duración ultra-corta de 24ms.
    Para quien busca la máxima definición acústica posible: un clic que corta el aire.
    """
    n = int(SR * dur_ms / 1000)
    fund = 640.0
    ratios = [1.0, 1.732, 2.828, 4.0]
    amps   = [0.68, 0.32, 0.14, 0.04]
    decays = [210, 300, 420, 580]
    out = []
    for i in range(n):
        t = i / SR
        snap = random.uniform(-1, 1) * 0.88 * math.exp(-t * 750)
        body = sum(math.sin(2 * math.pi * (fund * r) * t) * math.exp(-t * d) * a 
                   for r, d, a in zip(ratios, decays, amps))
        out.append(snap + body)
    return fade(normalize(out))

def sequence(samples, count=14, gap_ms=95):
    gap = int(SR * gap_ms / 1000)
    total = len(samples) + gap * (count - 1)
    out = [0.0] * total
    for i in range(count):
        for j, s in enumerate(samples):
            if i * gap + j < total:
                # Variación micro-dinámica (1%) que emula la respuesta háptica real
                out[i * gap + j] += s * (0.97 + (i % 3) * 0.02)
    peak = max(abs(x) for x in out) or 1
    return [x / peak * 0.82 for x in out]

variations = [
    ("Aura-Singularity-528", 
     "528 Hz (Proporción Áurea Phi) - 28ms - Mi diseño maestro definitivo: clic táctil ultra-nítido con cuerpo mineral armónico.", 
     list(aura_singularity())),

    ("Aura-Neuro-432", 
     "432 Hz (Afinación Pitagórica) - 26ms - Frecuencia de calma y foco profundo; ultra seco, cero fatiga auditiva tras horas.", 
     list(aura_neuro_432())),

    ("Aura-HyperCrisp-640", 
     "640 Hz (Cristal Cuántico) - 24ms - El sonido más rápido y quirúrgico posible; corte instantáneo sin ningún tipo de cola.", 
     list(aura_hyper_crisp())),
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
    <button class="bq" onclick="pl('{name}','{qb}')">&#9000; Escuchar Ritmo (Trance Flow)</button>
  </div></div>"""

html = """<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<title>Aura Writer - Master Neuroacoustic Design</title><style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#09090e;color:#e0e0ec;padding:48px 24px}
h1{text-align:center;font-size:28px;font-weight:300;letter-spacing:.16em;color:#e2b714;margin-bottom:6px}
.sub{text-align:center;color:#808098;font-size:13px;margin-bottom:44px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;max-width:980px;margin:0 auto}
.card{background:#11111a;border:1px solid #242436;border-radius:16px;padding:26px;transition:border-color .2s,transform .15s}
.card:hover{border-color:#e2b71466;transform:translateY(-2px)}
.card.active{border-color:#e2b714;background:#181710;box-shadow:0 0 30px rgba(226,183,20,0.14)}
.cn{font-size:17px;font-weight:600;color:#f5f5ff;margin-bottom:5px}
.cd{font-size:12px;color:#8888a0;margin-bottom:18px;line-height:1.5}
.pb{height:3px;background:#242436;border-radius:2px;margin-bottom:16px;overflow:hidden}
.pf{height:100%;width:0%;background:#e2b714;border-radius:2px;transition:width .04s}
.bt{display:flex;gap:8px}
button{flex:1;padding:10px 0;border:none;border-radius:8px;font-size:13px;font-weight:500;cursor:pointer;transition:all .12s}
button:active{transform:scale(.96)}
.bs{background:#222234;color:#a8a8c8}.bs:hover{background:#2c2c44;color:#fff}
.bq{background:#e2b71418;color:#e2b714;border:1px solid #e2b71444}.bq:hover{background:#e2b71428;color:#fff}
.foot{text-align:center;margin-top:44px;color:#505068;font-size:12px;line-height:1.6}
</style></head><body>
<h1>Aura Writer &mdash; El Dise&ntilde;o Maestro de la IA</h1>
<p class="sub">S&iacute;ntesis Neuroac&uacute;stica de Precisi&oacute;n: M&aacute;ximo Estado de Flujo, Cero Fatiga Cognitiva</p>
<div class="grid">""" + cards + """</div>
<p class="foot">Recomendaci&oacute;n: Pulsa <strong>Escuchar Ritmo (Trance Flow)</strong> en <em>Aura-Singularity-528</em> con los ojos cerrados para percibir la cadencia cerebral.</p>
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
