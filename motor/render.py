"""Convierte un episodio (JSON bilingue) en un Short vertical 1080x1920.

Uso: python3 render.py episodios/ep001.json salida/ [es en]
"""
import io
import json
import os
import re
import subprocess
import sys
import wave

import cairosvg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import doodle
import fondos
import voz
from personajes import personaje

W, H, FPS= 1080, 1920, 30
MARGEN= 1.08  # el fondo se dibuja un 8% mas grande para poder hacer zoom
RAIZ= os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTE= os.path.join(RAIZ, 'assets', 'fuentes', 'Anton-Regular.ttf')
AMARILLO= (255, 214, 10)
PAUSA= 0.10
ESCALA_PJ= 1.3  # los personajes llenan mas la pantalla


def loc(v, idioma):
    """Resuelve recursivamente los campos {'es':..., 'en':...}."""
    if isinstance(v, dict):
        if set(v.keys()) <= {'es', 'en'} and v:
            return v[idioma]
        return {k: loc(x, idioma) for k, x in v.items()}
    if isinstance(v, list):
        return [loc(x, idioma) for x in v]
    return v


def _objeto(o):
    if o['tipo'] in doodle.OBJETOS:
        return doodle.OBJETOS[o['tipo']](**{k: v for k, v in o.items() if k != 'tipo'})
    return fondos.objeto(o)


def svg_escena(esc):
    f= esc.get('fondo', 'habitacion')
    s= f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
    if f == 'noticias':
        s+= fondos.noticias(rotulo=esc.get('rotulo', ''))
    elif f in doodle.FONDOS:
        s+= doodle.FONDOS[f]()
    else:
        s+= fondos.FONDOS[f]()
    capas= [o for o in esc.get('objetos', []) if o.get('detras')]
    for o in capas:
        s+= _objeto({k: v for k, v in o.items() if k != 'detras'})
    for p in esc.get('personajes', []):
        a= dict(p)
        if a['n'] == 'palo':
            a.pop('n')
            a['escala']= a.get('escala', 1.0) * 1.1
            s+= doodle.palo(**a)
        else:
            a['escala']= a.get('escala', 1.0) * ESCALA_PJ
            s+= personaje(a.pop('n'), **a)
    if f == 'noticias':
        s+= fondos.mesa_noticias()
    for o in esc.get('objetos', []):
        if not o.get('detras'):
            s+= _objeto(o)
    return s + '</svg>'


def png_escena(esc):
    data= cairosvg.svg2png(bytestring=svg_escena(esc).encode(), output_width=int(W * MARGEN), output_height=int(H * MARGEN))
    return Image.open(io.BytesIO(data)).convert('RGB')


def grupos(palabras, destacar):
    """Agrupa palabras en bloques cortos (max 3 palabras / 16 letras) para el subtitulo."""
    dest= {re.sub(r'\W', '', d).lower() for d in destacar}
    gs, act= [], []
    for w in palabras:
        act.append(w)
        txt= ' '.join(x['p'] for x in act)
        if re.search(r'[.,!?;:…]$', w['p']) or len(act) >= 3 or len(txt) >= 14:
            gs.append(act)
            act= []
    if act:
        gs.append(act)
    res= []
    for g in gs:
        items= []
        for w in g:
            limpio= re.sub(r'[^\w€$%]', '', w['p']).lower()
            clave= limpio in dest or bool(re.search(r'\d', limpio))
            items.append((w['p'].upper(), clave))
        res.append({'ini': g[0]['ini'], 'fin': g[-1]['fin'], 'items': items})
    for a, b in zip(res, res[1:]):
        a['fin']= b['ini']
    return res


_cache_txt= {}


def sprite_subtitulo(items):
    """Devuelve una imagen RGBA con el bloque de subtitulo (blanco, claves en amarillo, borde negro)."""
    clave= tuple(items)
    if clave in _cache_txt:
        return _cache_txt[clave]
    tam= 132
    while True:
        font= ImageFont.truetype(FUENTE, tam)
        esp= font.getlength(' ')
        anchos= [font.getlength(t) for t, _ in items]
        total= sum(anchos) + esp * (len(items) - 1)
        if total <= W - 120 or tam <= 70:
            break
        tam-= 8
    borde= 14
    img= Image.new('RGBA', (int(total) + 80, int(tam * 1.5) + 60), (0, 0, 0, 0))
    d= ImageDraw.Draw(img)
    x= 40
    for (t, k), a in zip(items, anchos):
        # sombra dura + borde
        d.text((x + 6, 26 + 8), t, font=font, fill=(0, 0, 0, 255), stroke_width=borde, stroke_fill=(0, 0, 0, 255))
        d.text((x, 26), t, font=font, fill=AMARILLO + (255,) if k else (255, 255, 255, 255), stroke_width=borde, stroke_fill=(18, 18, 22, 255))
        x+= a + esp
    _cache_txt[clave]= img
    return img


def pop(sr=44100):
    t= np.linspace(0, 0.09, int(sr * 0.09), endpoint=False)
    f= 520 * np.exp(-t * 18) + 180
    return 0.22 * np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-t * 38)


def leer_wav(path):
    with wave.open(path, 'rb') as w:
        a= np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return a


def render(ruta_ep, dir_salida, idioma):
    ep= loc(json.load(open(ruta_ep, encoding='utf-8')), idioma)
    fondos.IDIOMA= idioma
    os.makedirs(dir_salida, exist_ok=True)
    tmp= os.path.join(dir_salida, f'_tmp_{idioma}')
    os.makedirs(tmp, exist_ok=True)
    base= f'{ep.get("serie", "ep")}{ep["n"]:03d}_{idioma}'

    # 1) voz por escena
    sr= 44100
    escenas, pista= [], []
    t0= 0.0
    for i, esc in enumerate(ep['escenas']):
        wav= os.path.join(tmp, f'{i:02d}.wav')
        dur, palabras= voz.sintetizar(esc['texto'], idioma, wav)
        a= leer_wav(wav)
        a= np.concatenate([a, np.zeros(int(sr * PAUSA), dtype=np.float32)])
        p= pop(sr)
        a[:len(p)]+= p[:len(a)].astype(np.float32)
        pista.append(a)
        d= len(a) / sr
        escenas.append({'ini': t0, 'fin': t0 + d, 'esc': esc,
                        'subs': grupos(palabras, esc.get('destacar', []))})
        t0+= d
    audio= np.clip(np.concatenate(pista), -1, 1)
    wav_total= os.path.join(tmp, 'audio.wav')
    with wave.open(wav_total, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((audio * 32767).astype(np.int16).tobytes())

    # 2) fotogramas -> ffmpeg
    mp4= os.path.join(dir_salida, base + '.mp4')
    ff= subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                          '-i', '-', '-i', wav_total, '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p',
                          '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', mp4], stdin=subprocess.PIPE)
    total= int(t0 * FPS)
    k= 0
    img= None
    for n in range(total):
        t= n / FPS
        while k < len(escenas) - 1 and t >= escenas[k]['fin']:
            k+= 1
            img= None
        e= escenas[k]
        if img is None:
            img= png_escena(e['esc'])
        tl= t - e['ini']
        dur= e['fin'] - e['ini']
        # golpe de zoom al entrar y deriva lenta despues
        z= 1.0 + 0.05 * max(0, 1 - tl / 0.14) + 0.035 * (tl / dur)
        cw, ch= W * MARGEN / z, H * MARGEN / z
        cx, cy= img.width / 2, img.height / 2
        caja= (int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))
        fr= img.crop(caja).resize((W, H), Image.BILINEAR)
        # subtitulo activo
        for g in e['subs']:
            if g['ini'] <= tl < g['fin']:
                sp= sprite_subtitulo(g['items'])
                esc_pop= 1.0 + 0.16 * max(0, 1 - (tl - g['ini']) / 0.09)
                if esc_pop > 1.001:
                    sp= sp.resize((int(sp.width * esc_pop), int(sp.height * esc_pop)), Image.BILINEAR)
                fr.paste(sp, (int(W / 2 - sp.width / 2), int(e['esc'].get('y_sub', 1400) - sp.height / 2)), sp)
                break
        ff.stdin.write(fr.tobytes())
    ff.stdin.close()
    ff.wait()

    # 3) metadatos para la subida
    meta= {'titulo': ep['titulo'], 'descripcion': ep['descripcion'], 'tags': ep.get('tags', []), 'idioma': idioma,
           'duracion': round(t0, 1), 'archivo': os.path.basename(mp4)}
    json.dump(meta, open(os.path.join(dir_salida, base + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{mp4}  {t0:.1f}s')
    return mp4


if __name__ == '__main__':
    ruta, salida= sys.argv[1], sys.argv[2]
    for idi in (sys.argv[3:] or ['es', 'en']):
        render(ruta, salida, idi)
