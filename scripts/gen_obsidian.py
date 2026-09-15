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

def fade(samples, ms=6):
    n = min(int(SR * ms / 1000), len(samples) // 4)
    for i in range(n): samples[-(i+1)] *= (i / n)
    return samples

def normalize(samples, level=0.85):
    peak = max(abs(s) for s in samples) or 1
    return [s / peak * level for s in samples]

# ── Generador Paramétrico de Obsidiana / Vidrio Volcánico Onírico ───────────
def synth_obsidian(dur_ms=34, fund=780, snap_vol=0.65, snap_decay=520, 
                   decay_mult=1.0, shimmer=0.08, aura_freq=432, aura_vol=0.04):
    """
    Sonido de obsidiana: impacto nítido, seco y cristalino, con un halo 
    armónico sutil (onírico/hipnótico) que induce concentración profunda.
    """
    n = int(SR * dur_ms / 1000)
    out = []
    
    # Ratios inarmónicos característicos del vidrio volcánico
    ratios = [1.000, 1.498, 2.012, 2.760, 3.820]
    amps   = [0.65,  0.32,  0.18,  0.08,  0.03]
    base_decays = [140, 180, 240, 310, 400]
    
    for i in range(n):
        t = i / SR
        
        # 1. Snap nítido / seco (transiente inmediato reconocible)
        snap = random.uniform(-1, 1) * snap_vol * math.exp(-t * snap_decay)
        
        # 2. Cristal de Obsidiana (cuerpo resonante rápido)
        glass = 0.0
        for r, d, a in zip(ratios, base_decays, amps):
            glass += math.sin(2 * math.pi * fund * r * t) * math.exp(-t * (d * decay_mult)) * a
            
        # 3. Halo Onírico / Hipnótico (micro-shimmer cristalino & tono zen)
        # Sutil modulación armónica que da sensación de trance sin alargar la duración
        hypno = math.sin(2 * math.pi * (fund * 1.5) * t + math.sin(2 * math.pi * 12 * t) * 0.5) * math.exp(-t * (160 * decay_mult)) * shimmer
        aura  = math.sin(2 * math.pi * aura_freq * t) * math.exp(-t * (120 * decay_mult)) * aura_vol
        
        out.append(snap + glass + hypno + aura)
        
    return fade(normalize(out))

def sequence(samples, count=12, gap_ms=105):
    gap = int(SR * gap_ms / 1000)
    total = len(samples) + gap * (count - 1)
    out = [0.0] * total
    for i in range(count):
        for j, s in enumerate(samples):
            if i * gap + j < total:
                # Muy leve variación humana en amplitud (1-2%) para trance hipnótico fluido
                out[i * gap + j] += s * (0.96 + (i % 3) * 0.03)
    peak = max(abs(x) for x in out) or 1
    return [x / peak * 0.82 for x in out]

variations = [
    ("Obsidiana-Original", 
     "820 Hz - 38ms - El que te agradó (referencia base)", 
     synth_obsidian(dur_ms=38, fund=820, snap_vol=0.72, snap_decay=480, decay_mult=1.0, shimmer=0.0, aura_vol=0.0)),
     
    ("Obsidiana-Trance-Seco", 
     "740 Hz - 30ms - Más seco y cortado, impacto nítido con toque hipnótico sutil", 
     synth_obsidian(dur_ms=30, fund=740, snap_vol=0.75, snap_decay=550, decay_mult=1.35, shimmer=0.08, aura_vol=0.03)),

    ("Obsidiana-Onírica", 
     "680 Hz - 34ms - Tono más profundo/zen, transiente limpio + micro-shimmer hipnótico", 
     synth_obsidian(dur_ms=34, fund=680, snap_vol=0.68, snap_decay=500, decay_mult=1.15, shimmer=0.12, aura_vol=0.05)),

    ("Obsidiana-GotaZen", 
     "600 Hz - 32ms - Frecuencia armónica 432Hz aura, sensación de fluidez y foco puro", 
     synth_obsidian(dur_ms=32, fund=600, snap_vol=0.70, snap_decay=520, decay_mult=1.20, shimmer=0.09, aura_vol=0.07, aura_freq=432)),

    ("Obsidiana-UltraNitida", 
     "780 Hz - 27ms - Golpe ultra preciso y seco como teclado mecánico premium de cristal", 
     synth_obsidian(dur_ms=27, fund=780, snap_vol=0.82, snap_decay=600, decay_mult=1.5, shimmer=0.05, aura_vol=0.02)),
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
<title>Aura Writer - Obsidiana Trance & Onírico</title><style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0b0b10;color:#e0e0ec;padding:48px 24px}
h1{text-align:center;font-size:28px;font-weight:300;letter-spacing:.16em;color:#bca1f5;margin-bottom:6px}
.sub{text-align:center;color:#7a7a9a;font-size:13px;margin-bottom:44px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px;max-width:960px;margin:0 auto}
.card{background:#13131d;border:1px solid #232338;border-radius:16px;padding:26px;transition:border-color .2s,transform .15s}
.card:hover{border-color:#bca1f555;transform:translateY(-2px)}
.card.active{border-color:#bca1f5;background:#1b192e;box-shadow:0 0 25px rgba(188,161,245,0.12)}
.cn{font-size:17px;font-weight:600;color:#f0f0ff;margin-bottom:5px}
.cd{font-size:12px;color:#787890;margin-bottom:18px;line-height:1.5}
.pb{height:3px;background:#232338;border-radius:2px;margin-bottom:16px;overflow:hidden}
.pf{height:100%;width:0%;background:#bca1f5;border-radius:2px;transition:width .04s}
.bt{display:flex;gap:8px}
button{flex:1;padding:10px 0;border:none;border-radius:8px;font-size:13px;font-weight:500;cursor:pointer;transition:all .12s}
button:active{transform:scale(.96)}
.bs{background:#232338;color:#a0a0c8}.bs:hover{background:#2e2e4a;color:#fff}
.bq{background:#bca1f518;color:#bca1f5;border:1px solid #bca1f544}.bq:hover{background:#bca1f528;color:#fff}
.foot{text-align:center;margin-top:44px;color:#48485e;font-size:12px}
</style></head><body>
<h1>Aura Writer &mdash; Obsidiana</h1>
<p class="sub">Claro &bull; N&iacute;tido &bull; Seco &bull; Estado de Trance Hipn&oacute;tico y On&iacute;rico</p>
<div class="grid">""" + cards + """</div>
<p class="foot">Tip: Prueba el bot&oacute;n <strong>Modo Trance (Ritmo)</strong> para sentir c&oacute;mo suena al escribir oraciones completas de forma continua.</p>
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
