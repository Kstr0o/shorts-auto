"""Animacion por capas de las escenas de dibujos (Toni y compania).

Antes cada escena era una imagen fija con zoom. Ahora el fondo, cada personaje y cada objeto se dibujan
por separado y se mueven solos: los personajes entran, respiran, parpadean y reaccionan segun su expresion,
los carteles y contadores saltan a la pantalla, los rayos giran y entre escena y escena hay un empujon.
"""
import io
import math
import re

import cairosvg
from PIL import Image

import doodle
import fondos
from personajes import personaje

W, H= 1080, 1920
MARGEN= 1.08   # el fondo se dibuja un 8% mas grande para poder hacer zoom
ESCALA_PJ= 1.3
ALA= 320       # margen a los lados al dibujar cada capa, para que nada salga cortado cuando se mueve
SUELO= 1640
T_CAMBIO= 0.2  # lo que dura el empujon entre escenas


def _svg(dentro, x0=0, ancho=W):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho}" height="{H}" viewBox="{x0} 0 {ancho} {H}">{dentro}</svg>'


def _capa(dentro, caja=None):
    """Dibuja un trozo de SVG en transparente y lo recorta. Devuelve (imagen, x, y) o None si no pinta nada."""
    data= cairosvg.svg2png(bytestring=_svg(dentro, -ALA, W + 2 * ALA).encode(), output_width=W + 2 * ALA, output_height=H)
    img= Image.open(io.BytesIO(data)).convert('RGBA')
    caja= caja or img.getbbox()
    if not caja:
        return None
    return img.crop(caja), caja[0] - ALA, caja[1], caja


def _objeto(o):
    if o['tipo'] in doodle.OBJETOS:
        return doodle.OBJETOS[o['tipo']](**{k: v for k, v in o.items() if k != 'tipo'})
    return fondos.objeto(o)


def _svg_pj(p, cerrado=False):
    a= dict(p)
    if a['n'] == 'palo':
        a.pop('n')
        a['escala']= a.get('escala', 1.0) * 1.1
        return doodle.palo(**a)
    a['escala']= a.get('escala', 1.0) * ESCALA_PJ
    return personaje(a.pop('n'), parpadeo=cerrado, **a)


def preparar(esc):
    """Dibuja una vez todas las capas de la escena."""
    f= esc.get('fondo', 'habitacion')
    pre= {'rayos': None, 'capas': []}
    if f == 'noticias':
        dentro= fondos.noticias(rotulo=esc.get('rotulo', ''))
    elif f in doodle.FONDOS:
        dentro= doodle.FONDOS[f]()
    else:
        dentro= fondos.FONDOS[f]()
    if f.startswith('rayos'):
        # los rayos giran: los dibujo en un cuadrado a media resolucion, centrado en su centro, y lo roto en cada fotograma
        cx, cy, r= W / 2, H * 0.42, 1360
        c1= re.search(r'fill="(#[0-9a-fA-F]{6})"', dentro).group(1)
        svg= (f'<svg xmlns="http://www.w3.org/2000/svg" width="{r}" height="{r}" viewBox="{cx - r} {cy - r} {2 * r} {2 * r}">'
              f'<rect x="{cx - r}" y="{cy - r}" width="{2 * r}" height="{2 * r}" fill="{c1}"/>{dentro[dentro.index("<path"):]}</svg>')
        pre['rayos']= Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), output_width=r, output_height=r))).convert('RGB')
    else:
        data= cairosvg.svg2png(bytestring=_svg(dentro).encode(), output_width=int(W * MARGEN), output_height=int(H * MARGEN))
        pre['fondo']= Image.open(io.BytesIO(data)).convert('RGB')
    objs= esc.get('objetos', [])
    for j, o in enumerate(objs):
        if o.get('detras'):
            c= _capa(_objeto({k: v for k, v in o.items() if k != 'detras'}))
            if c:
                pre['capas'].append({'clase': 'obj', 'tipo': o['tipo'], 'j': j, 'img': c[0], 'x': c[1], 'y': c[2]})
    for i, p in enumerate(esc.get('personajes', [])):
        c= _capa(_svg_pj(p))
        if not c:
            continue
        capa= {'clase': 'pj', 'i': i, 'expr': p.get('expr', 'normal'), 'px': p.get('x', 540), 'py': p.get('y', SUELO),
               'img': c[0], 'x': c[1], 'y': c[2], 'cerrado': None}
        if p['n'] != 'palo':
            capa['cerrado']= _capa(_svg_pj(p, True), c[3])[0]
        pre['capas'].append(capa)
    if f == 'noticias':
        c= _capa(fondos.mesa_noticias())
        pre['capas'].append({'clase': 'fijo', 'img': c[0], 'x': c[1], 'y': c[2]})
    for j, o in enumerate(objs):
        if not o.get('detras'):
            c= _capa(_objeto(o))
            if c:
                pre['capas'].append({'clase': 'obj', 'tipo': o['tipo'], 'j': j, 'img': c[0], 'x': c[1], 'y': c[2]})
    return pre


def _rebote(u):
    # sale de 0, se pasa un poco de 1 y vuelve (easeOutBack)
    u= max(0.0, min(1.0, u))
    return 1 + 2.7 * (u - 1) ** 3 + 1.7 * (u - 1) ** 2


def _suave(u):
    u= max(0.0, min(1.0, u))
    return 1 - (1 - u) ** 3


def _mov_pj(c, tl, k):
    """Devuelve (dx, dy, sx, sy, ojos_cerrados) del personaje en el instante tl de la escena numero k."""
    i, expr= c['i'], c['expr']
    dx= dy= 0.0
    sx= sy= 1.0
    seno= lambda periodo, fase=0.0: math.sin(2 * math.pi * (tl / periodo + fase))
    # entrada: en la primera escena ya estan puestos (es el primer fotograma del video) y solo dan un bote;
    # en las demas entran desde su lado, o desde abajo si van en el centro
    te= tl - (0.0 if k == 0 else 0.08 + 0.09 * i)
    if k == 0:
        s= 0.92 + 0.08 * _rebote(te / 0.3)
        sx*= s
        sy*= s
    else:
        b= _rebote(te / 0.34)
        if c['px'] < 480:
            dx-= (1 - b) * 640
        elif c['px'] > 600:
            dx+= (1 - b) * 640
        else:
            dy+= (1 - b) * 520
    # al llegar se aplasta un poco y se recupera
    a= max(0.0, min(1.0, (te - 0.24) / 0.22))
    sy*= 1 - 0.05 * math.sin(math.pi * a)
    sx*= 1 + 0.035 * math.sin(math.pi * a)
    # respira siempre
    sy*= 1 + 0.011 * seno(2.3, 0.37 * i)
    # y reacciona segun la cara que tiene
    if expr == 'feliz':
        dy-= (30 if tl < 1.35 else 9) * abs(seno(0.9 if tl < 1.35 else 1.3))
    elif expr == 'sorpresa':
        s= 1 + 0.09 * max(0.0, 1 - te / 0.3)
        sx*= s
        sy*= s
        dx+= 6 * seno(1 / 11) * max(0.0, 1 - tl / 0.7)
    elif expr == 'enfadado':
        dx+= 7 * seno(1 / 13) * (0.3 + 0.7 * max(0.0, 1 - tl / 0.9))
    elif expr == 'preocupado':
        dx+= 3.5 * seno(1 / 9)
    elif expr == 'triste':
        cae= _suave(tl / 1.2)
        dy+= 10 * cae
        sy*= 1 - 0.025 * cae
        dx+= 4 * seno(3.2)
    elif expr == 'chulo':
        dx+= 6 * seno(2.6, 0.2 * i)
        dy-= 5 * abs(seno(2.6, 0.2 * i))
    cerrado= tl > 0.5 and (tl + 1.3 * i + 0.9) % 2.9 < 0.12
    return dx, dy, sx, sy, cerrado


def _mov_obj(c, tl, k):
    """Devuelve (escala, dy) del objeto, o None si todavia no ha salido."""
    j= c['j']
    t0= (0.0 if k == 0 else 0.22) + 0.15 * j
    u= (tl - t0) / 0.28
    if u <= 0:
        return None
    s= (0.7 + 0.3 * _rebote(u)) if k == 0 else _rebote(u)
    dy= 0.0
    if u > 1:
        t= tl - t0
        if c['tipo'] in ('contador', 'numero'):
            s*= 1 + 0.03 * math.sin(2 * math.pi * t / 1.1)
        elif c['tipo'] in ('pegatina', 'nota'):
            dy= 5 * math.sin(2 * math.pi * (t / 1.9 + 0.3 * j))
            s*= 1 + 0.012 * math.sin(2 * math.pi * t / 1.9)
        else:
            dy= 3 * math.sin(2 * math.pi * (t / 2.4 + 0.3 * j))
    return s, dy


def _pegar(fr, img, x, y, sx=1.0, sy=1.0, ancla=None):
    """Pega img (cuya esquina sin escalar es x,y) escalada respecto al punto ancla."""
    if abs(sx - 1) > 0.002 or abs(sy - 1) > 0.002:
        ax, ay= ancla
        w, h= max(1, round(img.width * sx)), max(1, round(img.height * sy))
        img= img.resize((w, h), Image.BILINEAR)
        x= ax + (x - ax) * sx
        y= ay + (y - ay) * sy
    fr.paste(img, (round(x), round(y)), img)


def fotograma(pre, tl, dur, k):
    """Compone el fotograma de la escena numero k en su instante tl (sin subtitulos ni titulo fijo)."""
    if pre['rayos'] is not None:
        # giro lento de los rayos, con un empujon de zoom al entrar
        r= pre['rayos']
        g= r.rotate(-7.0 * tl * (1 if k % 2 else -1), resample=Image.BILINEAR)
        z= 1.0 + 0.06 * max(0, 1 - tl / 0.16)
        m= r.width / 2
        cw, ch= W / 2 / z, H / 2 / z
        cx= cy= m  # el centro de los rayos queda al 42% de alto del fotograma
        fr= g.crop((round(cx - cw / 2), round(cy - ch * 0.42), round(cx + cw / 2), round(cy + ch * 0.58))).resize((W, H), Image.BILINEAR)
    else:
        # golpe de zoom al entrar y deriva lenta despues, cada escena hacia un lado
        img= pre['fondo']
        z= 1.0 + 0.05 * max(0, 1 - tl / 0.14) + 0.035 * (tl / dur)
        cw, ch= W * MARGEN / z, H * MARGEN / z
        libre= (img.width - cw) / 2
        cx= img.width / 2 + (1 if k % 2 else -1) * libre * 0.8 * (tl / dur - 0.5)
        cy= img.height / 2
        fr= img.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))).resize((W, H), Image.BILINEAR)
    for c in pre['capas']:
        if c['clase'] == 'fijo':
            fr.paste(c['img'], (c['x'], c['y']), c['img'])
        elif c['clase'] == 'pj':
            dx, dy, sx, sy, cerrado= _mov_pj(c, tl, k)
            img= c['cerrado'] if cerrado and c['cerrado'] is not None else c['img']
            _pegar(fr, img, c['x'] + dx, c['y'] + dy, sx, sy, (c['px'] + dx, c['py'] + dy))
        else:
            m= _mov_obj(c, tl, k)
            if m:
                s, dy= m
                img= c['img']
                _pegar(fr, img, c['x'], c['y'] + dy, s, s, (c['x'] + img.width / 2, c['y'] + dy + img.height / 2))
    return fr


def cambio(anterior, nuevo, tl, k):
    """Empujon entre escenas: la anterior sale y la nueva entra, alternando de lado y desde abajo."""
    if anterior is None or tl >= T_CAMBIO:
        return nuevo
    p= _suave(tl / T_CAMBIO)
    fr= Image.new('RGB', (W, H))
    if k % 2:
        x= round(W * (1 - p))
        fr.paste(anterior, (x - W, 0))
        fr.paste(nuevo, (x, 0))
    else:
        y= round(H * (1 - p))
        fr.paste(anterior, (0, y - H))
        fr.paste(nuevo, (0, y))
    return fr
