"""Simulacion relajante sin voz: "¿Y si cada luciernaga encendiera dos mas?".

Una regla en pantalla, un contador y sonido de noche generado aqui mismo (grillos, viento, campanitas): sin voz ni musica de terceros.
Uso: python3 motor/sim_luciernagas.py salida.mp4 [segundos]
"""
import heapq, io, math, os, random, subprocess, sys, wave
import cairosvg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS= 1080, 1920, 30
RAIZ= os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTE= os.path.join(RAIZ, 'assets', 'fuentes', 'Baloo2-ExtraBold.ttf')
T= float(sys.argv[2]) if len(sys.argv) > 2 else 60.0
PERIODO, TOPE= 3.4, 900
RAFAGAS= [14.0, 15.3, 16.4, 17.7, 18.8, 20.1, 21.2, 22.5, 23.6, 24.9, 26.0, 27.3, 28.4, 29.6, 30.7, 31.9]
REGLA= ['Cada luciérnaga enciende 2 más.', 'Cada ráfaga de viento apaga la mitad.']
ROTULO= 'LUCIÉRNAGAS'
TINTA= '#0b1030'


def simular():
    r= random.Random(11)
    moscas= [{'n': 0.0, 'm': 1e9, 'x': 540.0, 'y': 1180.0, 'px': 540.0, 'py': 1180.0, 'f': r.uniform(0, 6.28)}]
    cola= [(1.5, 0)]
    eventos= [(g, -1) for g in RAFAGAS]
    for e in eventos:
        heapq.heappush(cola, e)
    brotes, t_tope= [], None
    while cola:
        t, i= heapq.heappop(cola)
        if t > T:
            break
        vivas= [k for k, m in enumerate(moscas) if m['n'] <= t < m['m']]
        if i == -1:
            r.shuffle(vivas)
            for k in vivas[:len(vivas) // 2]:
                moscas[k]['m']= t + r.uniform(0.15, 0.9)
            continue
        m= moscas[i]
        if not (m['n'] <= t < m['m']):
            continue
        if len(vivas) >= TOPE:
            t_tope= t
            break
        for _ in range(2):
            a, d= r.uniform(0, 6.28), r.uniform(120, 480)
            x= m['x'] + d * math.cos(a)
            y= m['y'] + d * 0.8 * math.sin(a)
            x, y= x + (r.uniform(120, 960) - x) * 0.35, y + (r.uniform(760, 1540) - y) * 0.35
            x, y= min(W - 60, max(60, x)), min(1580, max(720, y))
            moscas.append({'n': t, 'm': 1e9, 'x': x, 'y': y, 'px': m['x'], 'py': m['y'], 'f': r.uniform(0, 6.28)})
            heapq.heappush(cola, (t + PERIODO * r.uniform(0.85, 1.15), len(moscas) - 1))
        brotes.append(t)
        heapq.heappush(cola, (t + PERIODO * r.uniform(0.85, 1.15), i))
    return moscas, brotes, (t_tope or T)


def fondo():
    r= random.Random(3)
    s= (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"><defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#050818"/><stop offset="0.55" stop-color="#121a44"/><stop offset="1" stop-color="#232a63"/></linearGradient></defs>'
        f'<rect width="{W}" height="{H}" fill="url(#g)"/>')
    for _ in range(170):
        s+= f'<circle cx="{r.uniform(0, W):.0f}" cy="{r.uniform(0, 1150):.0f}" r="{r.choice([1.5, 2, 2, 3])}" fill="#fff" opacity="{r.uniform(0.25, 0.8):.2f}"/>'
    s+= '<circle cx="850" cy="820" r="74" fill="#f4f1d8"/><circle cx="822" cy="800" r="66" fill="#0e1538"/>'
    for base, amp, k, color in ((1230, 60, 0.005, '#161d4a'), (1300, 45, 0.009, '#111740')):
        pts= ' '.join(f'{x},{base - amp * (math.sin(k * x) + 0.5 * math.sin(k * 2.7 * x + 1)):.0f}' for x in range(-20, W + 21, 20))
        s+= f'<polygon points="-20,{H} {pts} {W + 20},{H}" fill="{color}"/>'
    for x, al in ((60, 520), (190, 400), (-30, 380), (1010, 540), (890, 410), (1100, 390)):
        y0= 1400
        s+= f'<rect x="{x - 10}" y="{y0 - 60}" width="20" height="90" fill="#070b22"/>'
        for j in range(4):
            an, yb= 150 - j * 28, y0 - 40 - j * al / 4.6
            s+= f'<polygon points="{x - an},{yb:.0f} {x + an},{yb:.0f} {x},{yb - al / 2.6:.0f}" fill="#070b22"/>'
    s+= f'<rect x="0" y="1390" width="{W}" height="{H - 1390}" fill="#0a0f2c"/>'
    for _ in range(260):
        x, y, h= r.uniform(0, W), r.uniform(1392, 1900), r.uniform(18, 46)
        s+= f'<path d="M{x:.0f},{y:.0f} q{r.uniform(-8, 8):.0f},{-h * 0.6:.0f} {r.uniform(-14, 14):.0f},{-h:.0f}" stroke="#141c4d" stroke-width="5" fill="none" stroke-linecap="round"/>'
    return np.asarray(Image.open(io.BytesIO(cairosvg.svg2png(bytestring=(s + '</svg>').encode()))).convert('RGB'), dtype=np.float32)


def brillo(radio, color, fuerza, dureza):
    y, x= np.mgrid[-radio:radio + 1, -radio:radio + 1]
    d= np.sqrt(x * x + y * y) / radio
    a= np.clip(1 - d, 0, 1) ** dureza * fuerza
    return a[:, :, None] * np.array(color, dtype=np.float32)[None, None, :]


def estampa(lienzo, sp, x, y, k):
    r= sp.shape[0] // 2
    x0, y0= int(x) - r, int(y) - r
    a0, b0, a1, b1= max(0, x0), max(0, y0), min(W, x0 + sp.shape[1]), min(H, y0 + sp.shape[0])
    if a1 > a0 and b1 > b0:
        lienzo[b0:b1, a0:a1]+= sp[b0 - y0:b1 - y0, a0 - x0:a1 - x0] * k


def cuenta(moscas, t, t_tope, n_tope):
    if t <= t_tope:
        return sum(1 for m in moscas if m['n'] <= t < m['m'])
    return int(n_tope * 3 ** ((t - t_tope) / PERIODO))


def texto_capa():
    im= Image.new('RGBA', (W, 260), (0, 0, 0, 0))
    d= ImageDraw.Draw(im)
    f= ImageFont.truetype(FUENTE, 50)
    for i, l in enumerate(REGLA):
        d.text((W / 2, 40 + i * 64), l, font=f, fill='#ffffff', anchor='mm', stroke_width=7, stroke_fill=TINTA)
    return np.asarray(im, dtype=np.float32)


def pegar(lienzo, capa, y):
    a= capa[:, :, 3:4] / 255.0
    lienzo[y:y + capa.shape[0]]= lienzo[y:y + capa.shape[0]] * (1 - a) + capa[:, :, :3] * a


def audio(ruta, brotes, t_tope):
    fs= 44100
    n= int(T * fs)
    t= np.arange(n) / fs
    rng= np.random.default_rng(5)
    L, R= np.zeros(n), np.zeros(n)
    # grillos: trenes de chirridos
    for f0, ritmo, fase, pan in ((4300, 0.83, 0.0, 0.3), (4750, 0.61, 1.7, 0.75), (3900, 0.47, 3.1, 0.55)):
        env= np.clip(np.sin(2 * np.pi * 16 * t) * 3, 0, 1) * np.clip(np.sin(2 * np.pi * ritmo * t + fase) * 4 - 1.2, 0, 1)
        c= np.sin(2 * np.pi * f0 * t) * env * 0.02
        L+= c * (1 - pan)
        R+= c * pan
    # colchon suave
    for f0, a in ((110, 0.05), (164.8, 0.035), (220, 0.03), (277.2, 0.018)):
        p= np.sin(2 * np.pi * f0 * t) * a * (0.75 + 0.25 * np.sin(2 * np.pi * 0.11 * t + f0))
        L+= p
        R+= p
    # viento: ruido marron con rachas
    ruido= np.cumsum(rng.standard_normal(n))
    ruido-= np.convolve(ruido, np.ones(4000) / 4000, mode='same')
    ruido= np.convolve(ruido, np.ones(60) / 60, mode='same')
    ruido/= np.abs(ruido).max()
    env= 0.05 + sum(np.exp(-((t - g - 0.5) / 0.7) ** 2) for g in RAFAGAS) * 0.55
    L+= ruido * env * 0.5
    R+= np.roll(ruido, 900) * env * 0.5
    # campanitas: una por brote, pentatonica
    notas= [440, 495, 554.4, 659.3, 740, 880, 990, 1108.7, 1318.5]
    ev= list(brotes)
    tt= t_tope
    while tt < T - 2.5:
        tt+= max(0.035, 0.12 * math.exp(-(tt - t_tope) / 5))
        ev.append(tt)
    ult= -1.0
    dur= int(0.9 * fs)
    td= np.arange(dur) / fs
    for e in sorted(ev):
        if e - ult < 0.03 or e >= T - 1:
            continue
        ult= e
        f0= notas[int(rng.integers(len(notas)))]
        g= np.sin(2 * np.pi * f0 * td) * np.exp(-td * 6) * 0.07 + np.sin(2 * np.pi * f0 * 2 * td) * np.exp(-td * 9) * 0.02
        i0= int(e * fs)
        m= min(dur, n - i0)
        pan= rng.uniform(0.2, 0.8)
        L[i0:i0 + m]+= g[:m] * (1 - pan) * 1.6
        R[i0:i0 + m]+= g[:m] * pan * 1.6
    s= np.stack([L, R], axis=1)
    s*= np.clip(t / 1.0, 0, 1)[:, None] * np.clip((T - t) / 2.0, 0, 1)[:, None]
    s= np.tanh(s * 1.4) / np.abs(np.tanh(s * 1.4)).max() * 0.7
    with wave.open(ruta, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(fs)
        w.writeframes((s * 32767).astype(np.int16).tobytes())


def main(salida):
    moscas, brotes, t_tope= simular()
    n_tope= sum(1 for m in moscas if m['n'] <= t_tope < m['m'])
    bg= fondo()
    halo= brillo(70, (150, 215, 60), 0.75, 2.2)
    nucleo= brillo(12, (255, 255, 200), 1.0, 1.2)
    regla= texto_capa()
    fnum, frot= ImageFont.truetype(FUENTE, 150), ImageFont.truetype(FUENTE, 40)
    wav= salida + '.wav'
    audio(wav, brotes, t_tope)
    ff= subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', wav,
                          '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', salida], stdin=subprocess.PIPE)
    calido= np.array([255, 232, 160], dtype=np.float32)
    yy= np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    rr= random.Random(9)
    rayas= [(rr.uniform(0, 1), rr.uniform(650, 1600), rr.uniform(140, 320)) for _ in range(26)]
    for nf in range(int(T * FPS)):
        t= nf / FPS
        c= bg.copy()
        viento= max((1 - abs(t - g - 0.5) / 0.9 for g in RAFAGAS), default=0)
        viento= max(0.0, viento)
        vivas= 0
        for m in moscas:
            if m['n'] > t or t > m['m'] + 0.7:
                continue
            ed= t - m['n']
            q= min(1.0, ed / 0.8)
            q= q * q * (3 - 2 * q)
            x= m['px'] + (m['x'] - m['px']) * q + 22 * math.sin(t * 0.7 + m['f']) + 10 * math.sin(t * 1.9 + m['f'] * 2)
            y= m['py'] + (m['y'] - m['py']) * q + 16 * math.cos(t * 0.6 + m['f'] * 1.3)
            k= min(1.0, ed / 0.4) * (0.7 + 0.3 * math.sin(t * 3.1 + m['f'] * 3))
            if t > m['m']:
                z= (t - m['m']) / 0.7
                k*= 1 - z
                x+= 420 * z * z
                y-= 60 * z
            else:
                vivas+= 1
                x+= 30 * viento * math.sin(m['f'])
            estampa(c, halo, x, y, k)
            estampa(c, nucleo, x, y, k)
        n= cuenta(moscas, t, t_tope, n_tope)
        amb= min(1.0, math.log10(max(1, n)) / 3.2)
        c+= (yy ** 1.5) * amb * np.array([40, 60, 14], dtype=np.float32)
        if t > t_tope:
            z= min(1.0, (t - t_tope) / max(1.0, T - t_tope - 2.5))
            z= z * z * (3 - 2 * z)
            c= c * (1 - 0.92 * z) + calido * (0.92 * z) * (0.75 + 0.25 * yy)
        if viento > 0.02:
            g= max(RAFAGAS, key=lambda g_: 1 - abs(t - g_ - 0.5))
            av= (t - g) / 1.4
            for fx, fy, lg in rayas:
                x0= int((fx + av * 1.6) * (W + 600) - 500)
                a0, a1= max(0, x0), min(W, x0 + int(lg))
                if a1 > a0:
                    c[int(fy):int(fy) + 4, a0:a1]+= 70 * viento
        pegar(c, regla, 300)
        im= Image.fromarray(np.clip(c, 0, 255).astype(np.uint8))
        d= ImageDraw.Draw(im)
        d.text((W / 2, 590), f'{n:,}'.replace(',', '.'), font=fnum, fill='#ffe27a', anchor='mm', stroke_width=10, stroke_fill=TINTA)
        d.text((W / 2, 690), ROTULO, font=frot, fill='#ffffff', anchor='mm', stroke_width=5, stroke_fill=TINTA)
        ff.stdin.write(im.tobytes())
    ff.stdin.close()
    ff.wait()
    os.remove(wav)
    print('fin', salida, 'tope', round(t_tope, 1), n_tope)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--cuenta':
        ms, br, tt= simular()
        nt= sum(1 for m in ms if m['n'] <= tt < m['m'])
        print('tope', tt, nt, [cuenta(ms, s, tt, nt) for s in range(0, int(T) + 1, 2)])
    else:
        main(sys.argv[1])
