"""Corta y edita los momentos elegidos: vertical 9:16 siguiendo la cara, zooms al final de frase con whoosh,
subtitulos de una palabra (estilo canales grandes) con las palabras clave en color y titulo opcional arriba. Todo local, 0 tokens.

Uso: python clipper/editar.py trabajo/<id> [--solo 1,3]
Lee video.mp4, palabras.json y momentos.json de la carpeta y deja clips/NN_nombre.mp4 + .json (titulo, descripcion...).

momentos.json (lo escribe Claude con la skill clipper):
{"idioma": "en", "color": "#FFD400",
 "clips": [{"inicio": 812.4, "fin": 851.0, "titulo": "...", "descripcion": "...", "tags": ["..."],
            "texto_arriba": "opcional", "claves": ["million", "billionaire"], "nota": 9, "gancho": "..."}]}
"""
import argparse, json, os, re, subprocess, unicodedata
import cv2
import numpy as np

AQUI= os.path.dirname(os.path.abspath(__file__))
FUENTES= os.path.join(AQUI, '..', 'assets', 'fuentes')
SALIDA_W, SALIDA_H= 1080, 1920
ALTO_CAM= 700  # alto de la franja de la camara en el encuadre split
ZOOM= 1.18          # cuanto se acerca en cada zoom
HUECO_ZOOM= 3.5     # segundos minimos entre zooms


def slug(t):
    t= unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '_', t).strip('_')[:40] or 'clip'


# ---------- 1. analisis: cambios de plano y caras ----------
def analizar(ruta, ini, fin):
    cap= cv2.VideoCapture(ruta); fps= cap.get(cv2.CAP_PROP_FPS) or 30
    W, H= int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.set(cv2.CAP_PROP_POS_MSEC, ini * 1000)
    n= int((fin - ini) * fps)
    det= cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    esc= 480 / W
    caras, cortes, prev_hist= [None] * n, [0], None
    elegido= None
    for i in range(n):
        ok, fr= cap.read()
        if not ok:
            n= i; caras= caras[:n]; break
        peq= cv2.cvtColor(cv2.resize(fr, (int(W * esc), int(H * esc))), cv2.COLOR_BGR2GRAY)
        hist= cv2.calcHist([peq], [0], None, [32], [0, 256]); cv2.normalize(hist, hist)
        if prev_hist is not None and cv2.compareHist(prev_hist, hist, cv2.HISTCMP_BHATTACHARYYA) > 0.35 and i - cortes[-1] > fps * 0.5:
            cortes.append(i); elegido= None
        prev_hist= hist
        if i % 3 == 0:
            fs= det.detectMultiScale(peq, 1.1, 5, minSize=(int(H * esc / 12),) * 2)
            if len(fs):
                cand= [((x + w / 2) / esc, (y + h / 2) / esc, w / esc) for x, y, w, h in fs]
                grande= max(cand, key=lambda c: c[2])
                if elegido is not None:   # no saltar entre dos personas salvo que la otra sea mucho mas grande
                    cerca= min(cand, key=lambda c: abs(c[0] - elegido[0]))
                    grande= grande if grande[2] > 1.5 * cerca[2] else cerca
                elegido= caras[i]= grande
    cap.release()
    return fps, W, H, n, caras, cortes


def trayectoria(n, caras, cortes, W, H, fps):
    """Centro (x, y) suavizado por plano; en cada corte salta de golpe al nuevo encuadre."""
    cx, cy= np.full(n, W / 2), np.full(n, H / 2)
    lims= cortes + [n]
    for a, b in zip(lims[:-1], lims[1:]):
        idx= [i for i in range(a, b) if caras[i] is not None]
        if not idx:
            continue
        xs= np.interp(range(a, b), idx, [caras[i][0] for i in idx])
        ys= np.interp(range(a, b), idx, [caras[i][1] for i in idx])
        k= max(1, int(fps * 0.8))
        ker= np.ones(k) / k
        cx[a:b]= np.convolve(np.pad(xs, (k // 2, k - 1 - k // 2), mode='edge'), ker, mode='valid')
        cy[a:b]= np.convolve(np.pad(ys, (k // 2, k - 1 - k // 2), mode='edge'), ker, mode='valid')
    return cx, cy


# ---------- 2. zooms y whoosh ----------
def momentos_zoom(pal, dur):
    t_ult, ev= -9, []
    for i, p in enumerate(pal):
        pausa= i + 1 < len(pal) and pal[i + 1]['s'] - p['e'] > 0.35   # transcripciones sin puntuacion: zoom en las pausas
        if (re.search(r'[.?!,]$', p['w']) or pausa) and p['e'] - t_ult >= HUECO_ZOOM and 1.5 < p['e'] < dur - 1.0:
            ev.append(p['e']); t_ult= p['e']
    return ev


def zoom_en(t, ev):
    z= 1.0
    for k, te in enumerate(ev):
        if t >= te:
            obj= ZOOM if k % 2 == 0 else 1.0; ant= 1.0 if k % 2 == 0 else ZOOM
            f= min(1.0, (t - te) / 0.18); f= 1 - (1 - f) ** 3
            z= ant + (obj - ant) * f
    return z


def whoosh(ruta, ev, dur, sr=48000):
    """Pista de efectos: un whoosh de ruido filtrado (generado aqui, sin derechos de nadie) en cada zoom."""
    pista= np.zeros(int(dur * sr) + sr, dtype=np.float32)
    L= int(0.35 * sr); t= np.linspace(0, 1, L)
    rng= np.random.default_rng(7)
    for te in ev:
        ruido= rng.standard_normal(L).astype(np.float32)
        # filtro paso bajo que sube de tono: barrido
        out= np.zeros(L, dtype=np.float32); y= 0.0
        for i in range(L):
            a= 0.02 + 0.25 * t[i]
            y+= a * (ruido[i] - y); out[i]= y
        env= np.sin(np.pi * t) ** 2
        s= int(max(0, te - 0.25) * sr)
        pista[s:s + L]+= (out * env * 0.9)[:len(pista) - s]
    import soundfile as sf
    sf.write(ruta, np.clip(pista, -1, 1), sr)


# ---------- 3. subtitulos ASS ----------
def color_ass(hexrgb):
    h= hexrgb.lstrip('#'); return f'&H00{h[4:6]}{h[2:4]}{h[0:2]}&'.upper()


def bloques(pal, maximo=1):
    """Una palabra cada vez, como los canales de clips grandes (DaPlug, Kai Cenat Live...); dos si la primera es muy corta."""
    g, act= [], []
    for i, p in enumerate(pal):
        cabe= len(act) < maximo or (len(act) == 1 and len(act[0]['w']) <= 3 and len(act[0]['w']) + len(p['w']) <= 9)
        if act and (not cabe or p['s'] - act[-1]['e'] > 0.5):
            g.append(act); act= []
        act.append(p)
        if re.search(r'[.?!]$', p['w']):
            g.append(act); act= []
    if act:
        g.append(act)
    return g


def ts(t):
    t= max(0, t); return f'{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}'



def tarjeta_gancho(texto, ruta, claves=(), ancho_max=960):
    """Gancho como lo ponen los canales grandes: tarjeta blanca de esquinas redondeadas con sombra suave,
    letra Anton negra en 1-2 lineas equilibradas y la palabra clave en rojo. PNG transparente para superponer.
    Devuelve (ancho, alto) de la tarjeta o None si no hay texto."""
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    texto= limpio(texto or '').upper().strip()
    if not texto:
        return None
    fuente= os.path.join(FUENTES, 'Anton-Regular.ttf')
    pal= texto.split()
    clave= {re.sub(r'\W', '', c.upper()) for c in claves or []}
    pad_x, pad_y, inter= 44, 26, 6
    for tam in range(78, 40, -2):
        f= ImageFont.truetype(fuente, tam)
        anchos= [f.getlength(w) for w in pal]; esp= f.getlength(' ')
        total= sum(anchos) + esp * (len(pal) - 1)
        if total + 2 * pad_x <= ancho_max:
            lineas= [pal]
        else:  # partir en 2 lineas lo mas parecidas posible
            mejor= None
            for i in range(1, len(pal)):
                a= sum(anchos[:i]) + esp * (i - 1); b= sum(anchos[i:]) + esp * (len(pal) - i - 1)
                if mejor is None or max(a, b) < mejor[0]:
                    mejor= (max(a, b), i)
            lineas= [pal[:mejor[1]], pal[mejor[1]:]]
        ancho_l= [f.getlength(' '.join(l)) for l in lineas]
        if max(ancho_l) + 2 * pad_x <= ancho_max:
            break
    asc, desc= f.getmetrics(); alto_l= asc + desc
    w= int(max(ancho_l) + 2 * pad_x); h= int(alto_l * len(lineas) + inter * (len(lineas) - 1) + 2 * pad_y)
    m= 28  # margen para la sombra
    img= Image.new('RGBA', (w + 2 * m, h + 2 * m), (0, 0, 0, 0))
    sombra= Image.new('RGBA', img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sombra).rounded_rectangle((m, m + 8, m + w, m + h + 8), radius=30, fill=(0, 0, 0, 120))
    img= Image.alpha_composite(img, sombra.filter(ImageFilter.GaussianBlur(12)))
    d= ImageDraw.Draw(img)
    d.rounded_rectangle((m, m, m + w, m + h), radius=30, fill=(255, 255, 255, 255))
    y= m + pad_y
    for l, al in zip(lineas, ancho_l):
        x= m + (w - al) / 2
        for p in l:
            rojo= re.sub(r'\W', '', p) in clave
            d.text((x, y), p, font=f, fill=(232, 32, 42, 255) if rojo else (12, 12, 12, 255))
            x+= f.getlength(p + ' ')
        y+= alto_l + inter
    img.save(ruta)
    return img.size

def ass(ruta, pal, dur, claves, color, arriba, franja=None, acciones=()):
    """franja: altura (px) de la union camara/juego en el encuadre split; el texto va ahi, sin tapar cara ni accion.
    Subtitulos al estilo de los canales grandes: una palabra en el centro, mayusculas, caja oscura translucida.
    acciones: [{t, texto}] rotulos tipo *STREAMER AWARD* / *LAUGHS* (segundos desde el inicio del clip)."""
    claves= {re.sub(r'\W', '', c.lower()) for c in claves}
    cab= f"""[Script Info]
ScriptType: v4.00+
PlayResX: {SALIDA_W}
PlayResY: {SALIDA_H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Anton,100,&H00FFFFFF,&H00FFFFFF,&H50000000,&H50000000,0,0,0,0,100,100,1,0,3,14,0,5,60,60,0,1
Style: Accion,Anton,70,&H00FFFFFF,&H00FFFFFF,&H50000000,&H50000000,0,0,0,0,100,100,1,0,3,12,0,5,60,60,0,1
Style: Arriba,Anton,92,&H00000000,&H00000000,&H00FFFFFF,&H00FFFFFF,0,0,0,0,100,100,0,0,3,22,0,8,70,70,190,1
Style: Franja,Anton,64,&H00000000,&H00000000,&H00FFFFFF,&H00FFFFFF,0,0,0,0,100,100,0,0,3,16,0,5,90,90,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lin= []
    if arriba and franja:
        lin.append(f'Dialogue: 1,{ts(0)},{ts(dur)},Franja,,0,0,0,,{{\\an5\\pos({SALIDA_W // 2},{franja})\\fad(200,0)}}{limpio(arriba).upper()}')
    elif arriba:
        lin.append(f'Dialogue: 1,{ts(0)},{ts(dur)},Arriba,,0,0,0,,{limpio(arriba).upper()}')
    # centro del cuerpo/pecho en encuadre completo; parte alta del juego en split (debajo de la franja)
    y_sub= franja + 330 if franja else 1010
    for a in acciones or []:
        try:
            t0= max(0.0, float(a['t']))
        except (KeyError, TypeError, ValueError):
            continue
        if t0 < dur and a.get('texto'):
            lin.append(f'Dialogue: 2,{ts(t0)},{ts(min(dur, t0 + 1.4))},Accion,,0,0,0,,{{\\an5\\pos({SALIDA_W // 2},{y_sub - 150})}}*{limpio(a["texto"]).upper()[:28]}*')
    gs= bloques(pal)
    for k, g in enumerate(gs):
        fin= min(gs[k + 1][0]['s'], g[-1]['e'] + 0.6) if k + 1 < len(gs) else g[-1]['e'] + 0.6
        txt= []
        for p in g:
            w= limpio(p['w']).upper()
            base= re.sub(r'\W', '', p['w'].lower())
            if base in claves or re.search(r'\d', base):
                w= f'{{\\c{color}}}{w}{{\\c&H00FFFFFF&}}'
            txt.append(w)
        pop= f'{{\\an5\\pos({SALIDA_W // 2},{y_sub})\\fscx85\\fscy85\\t(0,90,\\fscx100\\fscy100)}}'
        lin.append(f'Dialogue: 0,{ts(g[0]["s"])},{ts(min(fin, dur))},Sub,,0,0,0,,{pop}{" ".join(txt)}')
    open(ruta, 'w', encoding='utf-8').write(cab + '\n'.join(lin) + '\n')


def limpio(t):
    return t.replace('{', '(').replace('}', ')').replace('\\', '/')


# ---------- 4. render ----------
def split(fr, W, H, cam, juego=None):
    """Directo de Twitch con camara: arriba la camara del streamer, abajo el juego recortado al centro."""
    x, y, w, h= int(cam[0] * W), int(cam[1] * H), int(cam[2] * W), int(cam[3] * H)
    alto_cam= ALTO_CAM
    arriba= fr[y:y + h, x:x + w]
    # relleno la franja de arriba recortando la camara a su proporcion
    ratio= SALIDA_W / alto_cam
    if w / h > ratio:
        nw= int(h * ratio); arriba= arriba[:, (w - nw) // 2:(w - nw) // 2 + nw]
    else:
        nh= int(w / ratio); arriba= arriba[(h - nh) // 2:(h - nh) // 2 + nh]
    arriba= cv2.resize(arriba, (SALIDA_W, alto_cam))
    alto_juego= SALIDA_H - alto_cam
    if juego:  # zona del juego sin overlays (fracciones x, y, ancho, alto)
        jx, jy, jw, jh= int(juego[0] * W), int(juego[1] * H), int(juego[2] * W), int(juego[3] * H)
        fr= fr[jy:jy + jh, jx:jx + jw]; H, W= fr.shape[:2]
    gw= min(W, int(H * SALIDA_W / alto_juego)); gx= (W - gw) // 2
    gh= min(H, int(gw * alto_juego / SALIDA_W)); gy= (H - gh) // 2
    abajo= cv2.resize(fr[gy:gy + gh, gx:gx + gw], (SALIDA_W, alto_juego), interpolation=cv2.INTER_LANCZOS4)
    return np.vstack([arriba, abajo])


def completo(fr, W, H):
    """Directo entero (16:9) en el centro sobre el mismo fotograma ampliado y desenfocado: no se pierde la webcam
    cuando no se ha podido localizar. El directo queda un poco por encima del centro para dejar sitio a los subtitulos."""
    fh= int(SALIDA_W * H / W)
    fondo= cv2.resize(fr, (int(SALIDA_H * W / H), SALIDA_H))
    x0= (fondo.shape[1] - SALIDA_W) // 2
    fondo= cv2.GaussianBlur(cv2.resize(fondo[:, x0:x0 + SALIDA_W], (SALIDA_W // 8, SALIDA_H // 8)), (0, 0), 3)
    fondo= (cv2.resize(fondo, (SALIDA_W, SALIDA_H)) * 0.55).astype(np.uint8)
    y= (SALIDA_H - fh) // 2 - 120
    fondo[y:y + fh]= cv2.resize(fr, (SALIDA_W, fh), interpolation=cv2.INTER_AREA)
    return fondo


def render_clip(carpeta, k, m, palabras, color, idioma, info):
    video= os.path.join(carpeta, 'video.mp4')
    ini, fin= float(m['inicio']), float(m['fin']); dur= fin - ini
    if dur <= 1:
        print(f'  clip {k} saltado: fin antes que inicio'); return
    pal= [dict(p, s=p['s'] - ini, e=p['e'] - ini) for p in palabras if p['s'] >= ini - 0.05 and p['e'] <= fin + 0.3]
    # saco el trozo a 30 fps constantes: OpenCV salta mal en videos largos o de fps variable (Twitch, moviles)
    trozo= os.path.join(carpeta, f'_trozo{k}.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{ini}', '-t', f'{dur}', '-i', video, '-r', os.environ.get('FPS_CLIP', '30'), '-vf', 'scale=-2:min(ih\\,1080)',
                    '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '16', '-c:a', 'aac', '-b:a', '192k', trozo], check=True)
    fps, W, H, n, caras, cortes= analizar(trozo, 0, dur)
    cx, cy= trayectoria(n, caras, cortes, W, H, fps)
    ev= momentos_zoom(pal, dur)
    base_w, base_h= (H * 9 / 16, H) if W / H > 9 / 16 else (W, W * 16 / 9)
    os.makedirs(os.path.join(carpeta, 'clips'), exist_ok=True)
    nombre= f'{k:02d}_{slug(m["titulo"])}'
    sal= os.path.join(carpeta, 'clips', nombre)
    franja= ALTO_CAM if m.get('encuadre') == 'split' else None
    tarjeta= None
    try:
        tarjeta= tarjeta_gancho(m.get('texto_arriba'), sal + '_gancho.png', m.get('claves', []))
    except Exception as e:  # sin Pillow o sin fuente: el texto sale como antes, con el estilo del .ass
        print('  tarjeta del gancho no disponible:', e)
    ass(sal + '.ass', pal, dur, m.get('claves', []), color_ass(m.get('color', color)), None if tarjeta else m.get('texto_arriba'),
        franja, m.get('acciones') or [])
    # centro de la tarjeta: en la union camara/juego (split) o arriba del todo (encuadre completo)
    y_tarjeta= franja if franja else 190 + (tarjeta[1] // 2 if tarjeta else 0)
    whoosh(sal + '_sfx.wav', ev, dur)
    fdir= os.path.abspath(FUENTES).replace('\\', '/').replace(':', '\\:')
    assp= os.path.abspath(sal + '.ass').replace('\\', '/').replace(':', '\\:')
    ff= subprocess.Popen(['ffmpeg', '-v', 'error', '-y',
                          '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{SALIDA_W}x{SALIDA_H}', '-r', f'{fps}', '-i', '-',
                          '-i', trozo, '-i', sal + '_sfx.wav',
                          *(['-loop', '1', '-framerate', f'{fps}', '-t', f'{dur}', '-i', sal + '_gancho.png'] if tarjeta else []),
                          '-filter_complex', (f"[0:v]ass='{assp}':fontsdir='{fdir}'[s];[3:v]format=rgba,fade=in:st=0:d=0.25:alpha=1[g];"
                                              f"[s][g]overlay=(W-w)/2:{y_tarjeta}-h/2:shortest=1[v];" if tarjeta else
                                              f"[0:v]ass='{assp}':fontsdir='{fdir}'[v];")
                          + "[1:a]loudnorm=I=-14:TP=-1.5,aresample=48000[voz];[voz][2:a]amix=inputs=2:duration=first:normalize=0[a]",
                          '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-preset', os.environ.get('PRESET_CLIP', 'medium'), '-crf', os.environ.get('CRF_CLIP', '20'), '-pix_fmt', 'yuv420p',
                          '-c:a', 'aac', '-b:a', os.environ.get('AUDIO_CLIP', '160k'), '-t', f'{dur}', '-movflags', '+faststart', sal + '.mp4'], stdin=subprocess.PIPE)
    cap= cv2.VideoCapture(trozo)
    for i in range(n):
        ok, fr= cap.read()
        if not ok:
            break
        if m.get('encuadre') == 'split':
            ff.stdin.write(split(fr, W, H, m.get('camara', [0.0, 0.0, 0.3, 0.3]), m.get('juego')).tobytes()); continue
        if m.get('encuadre') == 'completo':
            ff.stdin.write(completo(fr, W, H).tobytes()); continue
        if m.get('encuadre') == 'centro':
            cx[i], cy[i]= W / 2, H / 2
        z= zoom_en(i / fps, ev)
        cw, ch= base_w / z, base_h / z
        x0= min(max(cx[i] - cw / 2, 0), W - cw)
        y0= min(max(cy[i] - ch * 0.42, 0), H - ch)   # cara un poco por encima del centro
        rec= fr[int(y0):int(y0 + ch), int(x0):int(x0 + cw)]
        ff.stdin.write(cv2.resize(rec, (SALIDA_W, SALIDA_H), interpolation=cv2.INTER_LANCZOS4 if z > 1 else cv2.INTER_LINEAR).tobytes())
    cap.release(); ff.stdin.close(); ff.wait()
    for extra in (sal + '.ass', sal + '_sfx.wav', sal + '_gancho.png', trozo):
        if os.path.exists(extra):
            os.remove(extra)
    credito= ''
    if info.get('url'):
        credito= f"\n\nOriginal: {info.get('titulo', '')} ({info.get('canal', '')}) {info['url']}"
    meta= {'titulo': m['titulo'], 'descripcion': (m.get('descripcion', '') + credito).strip(), 'tags': m.get('tags', []),
           'idioma': idioma, 'formato': 'clip', 'sintetico': False, 'nota': m.get('nota'), 'gancho': m.get('gancho'),
           'inicio': ini, 'fin': fin, 'fuente': info.get('url') or info.get('fuente'), 'campana': m.get('campana')}
    json.dump(meta, open(sal + '.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'  {nombre}.mp4  {dur:.0f}s  zooms={len(ev)} cortes={len(cortes) - 1}')


def main():
    ap= argparse.ArgumentParser()
    ap.add_argument('carpeta'); ap.add_argument('--solo')
    a= ap.parse_args()
    mom= json.load(open(os.path.join(a.carpeta, 'momentos.json'), encoding='utf-8'))
    palabras= json.load(open(os.path.join(a.carpeta, 'palabras.json'), encoding='utf-8'))
    infop= os.path.join(a.carpeta, 'info.json')
    info= json.load(open(infop, encoding='utf-8')) if os.path.exists(infop) else {}
    clips= sorted(mom['clips'], key=lambda c: -float(c.get('nota', 0)))
    solo= {int(x) for x in a.solo.split(',')} if a.solo else None
    for k, m in enumerate(clips, 1):
        if solo is None or k in solo:
            render_clip(a.carpeta, k, m, palabras, mom.get('color', '#FFD400'), mom.get('idioma', 'en'), info)


if __name__ == '__main__':
    main()
