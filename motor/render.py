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
import anima
import doodle
import fondos
import lab
import voz
from personajes import personaje

W, H, FPS= 1080, 1920, 30
MARGEN= 1.08  # el fondo se dibuja un 8% mas grande para poder hacer zoom
RAIZ= os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTE= os.path.join(RAIZ, 'assets', 'fuentes', 'Anton-Regular.ttf')
FUENTE_LAB= os.path.join(RAIZ, 'assets', 'fuentes', 'Baloo2-ExtraBold.ttf')
AMARILLO= (255, 214, 10)
PAUSA= 0.10
COLA= 0.6  # silencio al final para que el video no corte en seco
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
    max_pal, max_let= {'pop': (3, 14), 'palabra': (1, 1)}.get(ESTILO_SUB, (6, 30))
    """Agrupa palabras en bloques cortos (max 3 palabras / 16 letras) para el subtitulo."""
    dest= {re.sub(r'\W', '', d).lower() for d in destacar}
    gs, act= [], []
    for w in palabras:
        act.append(w)
        txt= ' '.join(x['p'] for x in act)
        if re.search(r'[.,!?;:…]$', w['p']) or len(act) >= max_pal or len(txt) >= max_let:
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
            items.append((re.sub(r'[.,;:…]+$', '', w['p']) if ESTILO_SUB == 'palabra' else w['p'].upper(), clave))
        res.append({'ini': g[0]['ini'], 'fin': g[-1]['fin'], 'items': items})
    for a, b in zip(res, res[1:]):
        a['fin']= b['ini']
    return res


_cache_txt= {}
ESTILO_SUB= 'pop'  # 'pop' (1-3 palabras grandes) o 'caja' (dos lineas en cursiva con palabra clave en recuadro rojo)


def _sprite_caja(items):
    """Dos lineas centradas, cursiva (inclinada), blanco con borde negro; las palabras clave van sobre un recuadro rojo."""
    tam= 84
    font= ImageFont.truetype(FUENTE, tam)
    esp= font.getlength(' ')
    # reparto en una o dos lineas equilibradas
    total= sum(font.getlength(t) for t, _ in items) + esp * (len(items) - 1)
    lineas= [items]
    if total > 620 and len(items) > 1:
        mejor, corte= None, 1
        for c in range(1, len(items)):
            a= sum(font.getlength(t) for t, _ in items[:c]) + esp * (c - 1)
            dif= abs(a - (total - a - esp))
            if mejor is None or dif < mejor:
                mejor, corte= dif, c
        lineas= [items[:corte], items[corte:]]
    alto_l= int(tam * 1.42)
    ancho= int(max(sum(font.getlength(t) for t, _ in l) + esp * (len(l) - 1) for l in lineas)) + 140
    img= Image.new('RGBA', (ancho, alto_l * len(lineas) + 50), (0, 0, 0, 0))
    d= ImageDraw.Draw(img)
    for i, l in enumerate(lineas):
        w= sum(font.getlength(t) for t, _ in l) + esp * (len(l) - 1)
        x= (ancho - w) / 2
        y= 22 + i * alto_l
        for t, k in l:
            a= font.getlength(t)
            if k:
                d.rounded_rectangle([x - 12, y + 12, x + a + 20, y + tam * 1.34 + 8], radius=12, fill=(0, 0, 0, 255))
                d.rounded_rectangle([x - 16, y + 6, x + a + 16, y + tam * 1.34], radius=12, fill=(222, 28, 40, 255))
                d.text((x + 3, y + 4), t, font=font, fill=(90, 0, 8, 255))
                d.text((x, y), t, font=font, fill=(255, 255, 255, 255))
            else:
                d.text((x + 4, y + 5), t, font=font, fill=(0, 0, 0, 255), stroke_width=9, stroke_fill=(0, 0, 0, 255))
                d.text((x, y), t, font=font, fill=(255, 255, 255, 255), stroke_width=8, stroke_fill=(14, 14, 18, 255))
            x+= a + esp
    # cursiva: inclino la imagen
    k= 0.16
    img= img.transform((img.width + int(k * img.height), img.height), Image.AFFINE, (1, k, -k * img.height, 0, 1, 0), Image.BICUBIC)
    return img


def sprite_subtitulo(items):
    """Devuelve una imagen RGBA con el bloque de subtitulo (blanco, claves en amarillo, borde negro)."""
    clave= tuple(items)
    if clave in _cache_txt:
        return _cache_txt[clave]
    if ESTILO_SUB == 'caja':
        _cache_txt[clave]= _sprite_caja(items)
        return _cache_txt[clave]
    if ESTILO_SUB == 'palabra':
        # una sola palabra, redondeada y con borde oscuro (estilo lab)
        t, k= items[0]
        tam= 150
        font= ImageFont.truetype(FUENTE_LAB, tam)
        while font.getlength(t) > W - 160 and tam > 80:
            tam-= 8
            font= ImageFont.truetype(FUENTE_LAB, tam)
        img= Image.new('RGBA', (int(font.getlength(t)) + 100, int(tam * 1.7) + 40), (0, 0, 0, 0))
        d= ImageDraw.Draw(img)
        d.text((50, 26), t, font=font, fill=(6, 12, 34, 150), stroke_width=16, stroke_fill=(6, 12, 34, 150))
        d.text((50, 18), t, font=font, fill=AMARILLO + (255,) if k else (255, 255, 255, 255), stroke_width=12, stroke_fill=(10, 18, 48, 255))
        _cache_txt[clave]= img
        return img
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
    global ESTILO_SUB
    # premisa fija arriba durante todo el video (episodios de Toni con gancho): campo "titulo_fijo"
    titulo_fijo= None
    if ep.get('titulo_fijo'):
        c= {'t': 'cartel', 'texto': ep['titulo_fijo'], 'y': 135, 'tam': 60}
        svg= f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{lab.cartel(c, 0, 0.0, idioma)}</svg>'
        titulo_fijo= Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), output_width=W, output_height=H))).convert('RGBA')
    ESTILO_SUB= ep.get('subtitulos', 'pop')
    _cache_txt.clear()
    os.makedirs(dir_salida, exist_ok=True)
    tmp= os.path.join(dir_salida, f'_tmp_{idioma}')
    os.makedirs(tmp, exist_ok=True)
    base= f'{ep.get("serie", "ep")}{ep["n"]:03d}_{idioma}'

    # 1) voz por escena (una sola voz por episodio: si una falla, repito todo con la siguiente)
    sr= 44100
    for motor, voz_edge in voz.opciones(idioma):
        try:
            escenas, pista= [], []
            if motor in ('edge', 'chatter'):
                # narracion continua: una sola locucion y corto las escenas entre palabra y palabra
                wav= os.path.join(tmp, 'continuo.wav')
                textos= [e['texto'] for e in ep['escenas']]
                dur, por_escena= (voz.sintetizar_continuo(textos, idioma, wav, voz_edge) if motor == 'edge'
                                  else voz.sintetizar_chatter(textos, idioma, wav))
                cortes= [0.0]
                for ant, sig in zip(por_escena, por_escena[1:]):
                    cortes.append((ant[-1]['fin'] + sig[0]['ini']) / 2)
                cortes.append(dur + COLA)
                for i, esc in enumerate(ep['escenas']):
                    ini= cortes[i]
                    palabras= [{'p': w['p'], 'ini': w['ini'] - ini, 'fin': w['fin'] - ini} for w in por_escena[i]]
                    escenas.append({'ini': ini, 'fin': cortes[i + 1], 'esc': esc,
                                    'subs': grupos(palabras, esc.get('destacar', []))})
                pista= [leer_wav(wav), np.zeros(int(sr * COLA), dtype=np.float32)]
                t0= cortes[-1]
            else:
                t0= 0.0
                for i, esc in enumerate(ep['escenas']):
                    wav= os.path.join(tmp, f'{i:02d}.wav')
                    dur, palabras= voz.sintetizar(esc['texto'], idioma, wav, motor=motor, voz_edge=voz_edge)
                    a= leer_wav(wav)
                    a= np.concatenate([a, np.zeros(int(sr * PAUSA), dtype=np.float32)])
                    pista.append(a)
                    d= len(a) / sr
                    escenas.append({'ini': t0, 'fin': t0 + d, 'esc': esc,
                                    'subs': grupos(palabras, esc.get('destacar', []))})
                    t0+= d
            print(f'VOZ {base}: {motor} {voz_edge or ""}', flush=True)
            break
        except voz.VozFallo as e:
            print(f'voz fallo ({e}); pruebo la siguiente', flush=True)
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
    pre= None       # capas de la escena de dibujos que toca
    limpio= None    # ultimo fotograma sin subtitulos ni titulo
    anterior= None  # como acabo la escena anterior, para el empujon de cambio
    for n in range(total):
        t= n / FPS
        while k < len(escenas) - 1 and t >= escenas[k]['fin']:
            k+= 1
            img= None
            pre= None
            anterior= limpio
        e= escenas[k]
        tl= t - e['ini']
        dur= e['fin'] - e['ini']
        es_lab= e['esc'].get('fondo') == 'lab'
        if es_lab:
            # estilo lab: cada fotograma se dibuja entero (todo se mueve)
            data= cairosvg.svg2png(bytestring=lab.fotograma(e['esc'], tl, dur, idioma).encode(), output_width=W, output_height=H)
            img= Image.open(io.BytesIO(data)).convert('RGB')
            limpio= img
            fr= img.copy()
        else:
            # dibujos: cada capa (fondo, personajes, objetos) se mueve por su cuenta
            if pre is None:
                pre= anima.preparar(e['esc'])
            limpio= anima.fotograma(pre, tl, dur, k)
            fr= anima.cambio(anterior, limpio, tl, k)
            if fr is limpio:
                fr= limpio.copy()
        if titulo_fijo is not None and not es_lab:
            fr.paste(titulo_fijo, (0, 0), titulo_fijo)
        # subtitulo activo
        for g in e['subs']:
            if g['ini'] <= tl < g['fin']:
                sp= sprite_subtitulo(g['items'])
                esc_pop= 1.0 + (0.16 if ESTILO_SUB == 'pop' else 0.06) * max(0, 1 - (tl - g['ini']) / 0.09)
                if esc_pop > 1.001:
                    sp= sp.resize((int(sp.width * esc_pop), int(sp.height * esc_pop)), Image.BILINEAR)
                fr.paste(sp, (int(W / 2 - sp.width / 2), int(e['esc'].get('y_sub', 330 if es_lab else 1400) - sp.height / 2)), sp)
                break
        ff.stdin.write(fr.tobytes())
    ff.stdin.close()
    ff.wait()

    # 3) metadatos para la subida
    meta= {'formato': ep.get('formato', ''), 'titulo': ep['titulo'], 'descripcion': ep['descripcion'], 'tags': ep.get('tags', []), 'idioma': idioma, 'voz': f'{motor} {voz_edge or ""}'.strip(),
           'duracion': round(t0, 1), 'archivo': os.path.basename(mp4)}
    json.dump(meta, open(os.path.join(dir_salida, base + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{mp4}  {t0:.1f}s')
    return mp4


if __name__ == '__main__':
    ruta, salida= sys.argv[1], sys.argv[2]
    for idi in (sys.argv[3:] or ['es', 'en']):
        render(ruta, salida, idi)
