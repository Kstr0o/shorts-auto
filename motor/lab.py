"""Estilo 'lab' para los ¿Y si...?: infografia plana y animada sobre fondo oscuro.

Cada escena lleva una lista de capas; cualquier numero puede ir como [desde, hasta] y se anima a lo largo de la escena.
Tambien vale {'de': a, 'a': b, 'ini': 0.2, 'fin': 0.8} para animar solo en un trozo (fracciones de la escena).
'en' (fraccion) hace que la capa aparezca con un saltito en ese momento; 'sale' la quita.
"""
import math
import random

W, H= 1080, 1920
FUENTE= 'Baloo 2'
C= {'fondo1': '#0a1230', 'fondo2': '#152a63', 'mar': '#2f7fe0', 'mar2': '#1f5fc0', 'tierra': '#4cc06f', 'tierra2': '#35a058',
    'hielo': '#f1f6ff', 'sol': '#ffcf4a', 'amarillo': '#ffd60a', 'rojo': '#ff5a5f', 'turquesa': '#35e0c2', 'blanco': '#ffffff',
    'chip': '#0c1838', 'borde': '#3d5bb0', 'gris': '#9fb0d8', 'arena': '#e2b06a', 'arena2': '#c98f4a', 'luna': '#cfd6e6',
    'luna2': '#aab3c9', 'piel': '#ffe0bd', 'naranja': '#ff9f43', 'morado': '#9b6bff', 'noche': '#050a1c'}


def col(c):
    return C.get(c, c)


def suave(p):
    p= max(0.0, min(1.0, p))
    return p * p * (3 - 2 * p)


def valor(v, p):
    """Resuelve un parametro animado en el instante p (0..1 de la escena)."""
    if isinstance(v, list) and len(v) == 2 and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in v):
        return v[0] + (v[1] - v[0]) * suave(p)
    if isinstance(v, dict) and 'onda' in v:
        # vaiven: base + onda * cos(2*pi*(ciclos*p + fase))
        return v.get('base', 0) + v['onda'] * math.cos(2 * math.pi * (v.get('ciclos', 1) * p + v.get('fase', 0)))
    if isinstance(v, dict) and 'de' in v and 'a' in v:
        i, f= v.get('ini', 0.0), v.get('fin', 1.0)
        q= (p - i) / max(f - i, 1e-6)
        q= max(0.0, min(1.0, q))
        q= q if v.get('curva') == 'lineal' else (q * q if v.get('curva') == 'acelera' else suave(q))
        return v['de'] + (v['a'] - v['de']) * q
    return v


def num(v, dec=0, idi='es'):
    s= f'{v:,.{dec}f}'
    if idi == 'es':
        s= s.replace(',', '_').replace('.', ',').replace('_', '.')
    return s


def _txt(x, y, s, tam=60, color='blanco', ancla='middle', peso=800, op=1.0, borde=None):
    s= str(s).replace('&', '&amp;').replace('<', '&lt;')
    base= (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FUENTE}" font-weight="{peso}" font-size="{tam:.1f}" '
           f'text-anchor="{ancla}" opacity="{op:.2f}" ')
    r= ''
    if borde:
        # primero el borde y encima el relleno (cairosvg no entiende paint-order)
        r= base + f'fill="{col(borde)}" stroke="{col(borde)}" stroke-width="{tam * 0.2:.1f}" stroke-linejoin="round">{s}</text>'
    return r + base + f'fill="{col(color)}">{s}</text>'


def _ancho(s, tam):
    return len(str(s)) * tam * 0.56


# ---------- fondos ----------

_estrellas= {}


def cielo(tipo, t):
    if tipo == 'espacio':
        if 'e' not in _estrellas:
            r= random.Random(7)
            _estrellas['e']= [(r.uniform(0, W), r.uniform(0, H), r.choice([1.5, 2, 2, 3, 4]), r.uniform(0, 6.28)) for _ in range(150)]
        s= ('<defs><linearGradient id="gf" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0a1230"/>'
            '<stop offset="1" stop-color="#152a63"/></linearGradient></defs>'
            f'<rect width="{W}" height="{H}" fill="url(#gf)"/>')
        for x, y, r, f in _estrellas['e']:
            s+= f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="#fff" opacity="{0.45 + 0.4 * math.sin(t * 2 + f):.2f}"/>'
        return s
    a, b= {'dia': ('#5ec3ff', '#c9f0ff'), 'noche': ('#070d24', '#1a2b63'), 'atardecer': ('#ff9a5a', '#ffe0a3'),
           'hielo': ('#9fd3ff', '#eaf6ff'), 'agua': ('#0c4a7a', '#062238'), 'rojo': ('#3a0d12', '#8a1f24'), 'negro': ('#050507', '#0d0d14')}.get(tipo, (col(tipo), col(tipo)))
    return (f'<defs><linearGradient id="gf" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{a}"/>'
            f'<stop offset="1" stop-color="{b}"/></linearGradient></defs><rect width="{W}" height="{H}" fill="url(#gf)"/>')


# ---------- piezas ----------

# manchas de tierra: (longitud, latitud, ancho, alto) en grados y fraccion del radio
_CONT= [(0, 25, .34, .26), (18, 5, .22, .3), (-12, 45, .26, .16), (30, -25, .2, .24), (75, 30, .3, .2), (95, 10, .2, .22),
        (110, 40, .26, .16), (150, -20, .24, .18), (170, 15, .16, .14), (215, 35, .32, .22), (235, 10, .2, .24), (250, -25, .22, .3),
        (205, 55, .24, .12), (300, 20, .18, .16), (320, -35, .2, .14), (285, -10, .12, .12)]
_CRAT= [(10, 20, .16), (60, -30, .12), (100, 35, .2), (150, 5, .1), (200, -25, .18), (250, 30, .14), (300, -5, .12), (330, 45, .1)]
_uid= [0]


def planeta(c, p, t, idi):
    """Planeta que gira de verdad: las manchas se estrechan al acercarse al borde. tipo: tierra | luna | marte | hielo."""
    x, y, r= c.get('x', 540), c.get('y', 900), c.get('r', 330)
    giro= c.get('giro', 0.0) * 2 * math.pi
    tipo= c.get('tipo', 'tierra')
    banda= c.get('banda', 0.0)  # 0..1: los oceanos se van a los polos y queda un continente en el ecuador
    _uid[0]+= 1
    cid= f'cp{_uid[0]}'
    base, mancha= {'tierra': ('mar', 'tierra'), 'luna': ('luna', 'luna2'), 'marte': ('#d9713c', '#b5542a'),
                   'hielo': ('#cfe6ff', 'hielo'), 'seco': ('arena', 'arena2')}[tipo]
    s= f'<defs><clipPath id="{cid}"><circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}"/></clipPath></defs>'
    if c.get('atm', tipo == 'tierra'):
        s+= f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r * 1.09:.1f}" fill="#7fc4ff" opacity="0.18"/>'
        s+= f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r * 1.04:.1f}" fill="#9fd6ff" opacity="0.22"/>'
    s+= f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{col(base)}"/><g clip-path="url(#{cid})">'
    if tipo in ('luna', 'marte'):
        for lon, lat, w in _CRAT:
            la= math.radians(lon) + giro
            if math.cos(la) > 0.05:
                px= x + r * math.cos(math.radians(lat)) * math.sin(la)
                py= y - r * math.sin(math.radians(lat))
                s+= f'<ellipse cx="{px:.1f}" cy="{py:.1f}" rx="{w * r * math.cos(la):.1f}" ry="{w * r:.1f}" fill="{col(mancha)}"/>'
    else:
        op= 1.0 - 0.75 * banda
        for lon, lat, w, h in _CONT:
            la= math.radians(lon) + giro
            if math.cos(la) > 0.05:
                px= x + r * math.cos(math.radians(lat)) * math.sin(la)
                py= y - r * math.sin(math.radians(lat))
                s+= (f'<ellipse cx="{px:.1f}" cy="{py:.1f}" rx="{w * r * math.cos(la):.1f}" ry="{h * r:.1f}" '
                     f'fill="{col(mancha)}" opacity="{op:.2f}"/>')
        if banda > 0.01:
            alto= r * 0.62 * banda
            s+= f'<rect x="{x - r:.1f}" y="{y - alto:.1f}" width="{2 * r:.1f}" height="{2 * alto:.1f}" fill="{col("arena")}"/>'
            s+= f'<rect x="{x - r:.1f}" y="{y - alto * 0.35:.1f}" width="{2 * r:.1f}" height="{alto * 0.7:.1f}" fill="{col("arena2")}" opacity="0.6"/>'
            # el agua se acumula en los polos
            s+= f'<ellipse cx="{x:.1f}" cy="{y - r:.1f}" rx="{r:.1f}" ry="{r * 0.5 * banda:.1f}" fill="{col("mar2")}"/>'
            s+= f'<ellipse cx="{x:.1f}" cy="{y + r:.1f}" rx="{r:.1f}" ry="{r * 0.5 * banda:.1f}" fill="{col("mar2")}"/>'
        if c.get('polos', True) and banda < 0.5:
            s+= f'<ellipse cx="{x:.1f}" cy="{y - r:.1f}" rx="{r * 0.5:.1f}" ry="{r * 0.16:.1f}" fill="{col("hielo")}"/>'
            s+= f'<ellipse cx="{x:.1f}" cy="{y + r:.1f}" rx="{r * 0.42:.1f}" ry="{r * 0.13:.1f}" fill="{col("hielo")}"/>'
    noche= c.get('noche', 0.0)  # 0..1: media cara a oscuras (el sol queda a la izquierda)
    if noche > 0.01:
        s+= f'<rect x="{x:.1f}" y="{y - r:.1f}" width="{r:.1f}" height="{2 * r:.1f}" fill="{col("noche")}" opacity="{0.72 * noche:.2f}"/>'
    if c.get('sombra', True) and noche < 0.5:
        s+= f'<circle cx="{x + r * 0.55:.1f}" cy="{y + r * 0.25:.1f}" r="{r * 1.05:.1f}" fill="none" stroke="#04102e" stroke-width="{r * 0.5:.1f}" opacity="0.16"/>'
    s+= '</g>'
    if c.get('ecuador'):
        s+= (f'<line x1="{x - r:.1f}" y1="{y:.1f}" x2="{x + r:.1f}" y2="{y:.1f}" stroke="{col("amarillo")}" stroke-width="7" '
             f'stroke-dasharray="26 18" stroke-dashoffset="{-t * 120:.1f}" stroke-linecap="round"/>')
    if c.get('eje'):
        s+= (f'<line x1="{x:.1f}" y1="{y - r * 1.25:.1f}" x2="{x:.1f}" y2="{y + r * 1.25:.1f}" stroke="#fff" stroke-width="5" '
             f'stroke-dasharray="14 14" opacity="0.55"/>')
    if c.get('incl'):
        s= f'<g transform="rotate({c["incl"]:.2f} {x:.1f} {y:.1f})">{s}</g>'
    return s


def sol(c, p, t, idi):
    x, y, r= c.get('x', 160), c.get('y', 420), c.get('r', 110)
    lat= 1 + 0.05 * math.sin(t * 3)
    return (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r * 1.9 * lat:.1f}" fill="{col("sol")}" opacity="0.10"/>'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r * 1.4 * lat:.1f}" fill="{col("sol")}" opacity="0.22"/>'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{col("sol")}"/>'
            f'<circle cx="{x - r * 0.15:.1f}" cy="{y - r * 0.15:.1f}" r="{r * 0.7:.1f}" fill="#ffe08a" opacity="0.7"/>')


def chip(c, p, t, idi):
    """Etiqueta redondeada con texto."""
    x, y, tam= c.get('x', 540), c.get('y', 600), c.get('tam', 52)
    s= str(c['texto'])
    a= _ancho(s, tam) + tam * 1.1
    h= tam * 1.55
    f, tx= (col(c['color']), '#0a1230') if c.get('color') else (col('chip'), '#fff')
    bd= '' if c.get('color') else f' stroke="{col("borde")}" stroke-width="4"'
    return (f'<rect x="{x - a / 2:.1f}" y="{y - h / 2:.1f}" width="{a:.1f}" height="{h:.1f}" rx="{h / 2:.1f}" fill="{f}"{bd}/>'
            + _txt(x, y + tam * 0.36, s, tam, tx))


def texto(c, p, t, idi):
    return _txt(c.get('x', 540), c.get('y', 600), c['texto'], c.get('tam', 90), c.get('color', 'blanco'), borde=c.get('borde', '#0a1230'))


def contador(c, p, t, idi):
    """Cifra grande que va subiendo."""
    x, y, tam= c.get('x', 540), c.get('y', 1300), c.get('tam', 150)
    v= c.get('v', 0)
    if c.get('reloj'):
        s= f'{int(v) // 60}:{int(v) % 60:02d}'
    else:
        s= f'{c.get("pre", "")}{num(v, c.get("dec", 0), idi)}{c.get("suf", "")}'
    r= _txt(x, y, s, tam, c.get('color', 'amarillo'), borde='#0a1230')
    if c.get('pie'):
        r+= _txt(x, y + tam * 0.55, c['pie'], tam * 0.36, 'blanco', borde='#0a1230')
    return r


def panel(c, p, t, idi):
    """Marcador con casillas (rotulo arriba, valor abajo)."""
    items= c['items']
    y= c.get('y', 1560)
    n= len(items)
    a= min(300, (W - 80 - 16 * (n - 1)) / n)
    x0= (W - (a * n + 16 * (n - 1))) / 2
    s= ''
    for i, it in enumerate(items):
        x= x0 + i * (a + 16)
        v= valor(it['v'], p)
        if isinstance(v, (int, float)):
            v= f'{it.get("pre", "")}{num(v, it.get("dec", 0), idi)}{it.get("suf", "")}'
        s+= f'<rect x="{x:.1f}" y="{y:.1f}" width="{a:.1f}" height="150" rx="22" fill="{col("chip")}" stroke="{col("borde")}" stroke-width="4"/>'
        s+= _txt(x + a / 2, y + 48, it['k'], 30, 'gris')
        s+= _txt(x + a / 2, y + 118, v, 56 if len(str(v)) < 9 else 42, it.get('color', 'blanco'))
    return s


def barra(c, p, t, idi):
    """Barra horizontal de comparacion con rotulo y valor."""
    x, y, a= c.get('x', 110), c.get('y', 1300), c.get('ancho', 860)
    v= max(0.0, min(1.0, c.get('v', 1.0)))
    s= _txt(x, y - 20, c.get('texto', ''), 46, 'blanco', 'start')
    if c.get('valor'):
        s+= _txt(x + a, y - 20, c['valor'], 46, c.get('color', 'amarillo'), 'end')
    s+= f'<rect x="{x}" y="{y}" width="{a}" height="44" rx="22" fill="{col("chip")}" stroke="{col("borde")}" stroke-width="3"/>'
    if v > 0.03:
        s+= f'<rect x="{x}" y="{y}" width="{a * v:.1f}" height="44" rx="22" fill="{col(c.get("color", "amarillo"))}"/>'
    return s


def regla(c, p, t, idi):
    """Linea de medida con topes y texto."""
    x1, y1, x2, y2= c['x1'], c['y1'], c['x2'], c['y2']
    k= col(c.get('color', 'amarillo'))
    s= f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{k}" stroke-width="7" stroke-linecap="round"/>'
    for a, b in ((x1, y1), (x2, y2)):
        s+= f'<circle cx="{a}" cy="{b}" r="13" fill="{k}"/>'
    if c.get('texto'):
        s+= chip({'x': (x1 + x2) / 2, 'y': (y1 + y2) / 2 - 50, 'texto': c['texto'], 'tam': c.get('tam', 44)}, p, t, idi)
    return s


def flecha(c, p, t, idi):
    x1, y1, x2, y2= c['x1'], c['y1'], c['x2'], c['y2']
    k= col(c.get('color', 'amarillo'))
    g= c.get('grosor', 16)
    a= math.atan2(y2 - y1, x2 - x1)
    L= g * 2.6
    bx, by= x2 - L * math.cos(a), y2 - L * math.sin(a)
    pts= ' '.join(f'{px:.1f},{py:.1f}' for px, py in [(x2, y2), (bx + L * 0.6 * math.sin(a), by - L * 0.6 * math.cos(a)),
                                                    (bx - L * 0.6 * math.sin(a), by + L * 0.6 * math.cos(a))])
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="{k}" stroke-width="{g}" stroke-linecap="round"/>'
            f'<polygon points="{pts}" fill="{k}"/>')


def viento(c, p, t, idi):
    """Rafagas que cruzan una franja de la pantalla."""
    y0, y1= c.get('y0', 500), c.get('y1', 1300)
    n, vel= int(c.get('n', 14)), c.get('vel', 1600)
    fuerza= c.get('fuerza', 1.0)
    r= random.Random(c.get('semilla', 3))
    s= ''
    for _ in range(n):
        y= r.uniform(y0, y1)
        L= r.uniform(120, 340)
        x= (r.uniform(0, W + 400) + t * vel * r.uniform(0.7, 1.3)) % (W + 500) - 400
        s+= (f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x + L:.1f}" y2="{y:.1f}" stroke="{col(c.get("color", "blanco"))}" '
             f'stroke-width="{r.choice([6, 8, 10])}" stroke-linecap="round" opacity="{0.55 * fuerza:.2f}"/>')
    return s


def suelo(c, p, t, idi):
    y= c.get('y', 1250)
    k, k2= col(c.get('color', 'tierra')), col(c.get('color2', 'tierra2'))
    return (f'<rect x="-200" y="{y}" width="{W + 400}" height="{H - y + 200}" fill="{k}"/>'
            f'<rect x="-200" y="{y}" width="{W + 400}" height="26" fill="{k2}"/>')


def nube(c, p, t, idi):
    x, y, e= c.get('x', 300) + t * c.get('vel', 0), c.get('y', 700), c.get('escala', 1.0)
    return (f'<g transform="translate({x:.1f} {y:.1f}) scale({e})" fill="#fff" opacity="{c.get("op", 0.9)}"><ellipse cx="0" cy="0" rx="120" ry="46"/>'
            '<circle cx="-50" cy="-30" r="50"/><circle cx="30" cy="-48" r="64"/><circle cx="90" cy="-14" r="40"/></g>')


def carretera(c, p, t, idi):
    y= c.get('y', 1300)
    s= f'<rect x="-200" y="{y}" width="{W + 400}" height="120" fill="#3b4256"/>'
    for i in range(-1, 8):
        s+= f'<rect x="{i * 190 - (t * c.get("vel", 0)) % 190:.1f}" y="{y + 54}" width="100" height="12" rx="6" fill="#ffd60a"/>'
    return s


def _girado(x, y, rot, e, cuerpo):
    return f'<g transform="translate({x:.1f} {y:.1f}) rotate({rot:.1f}) scale({e:.3f})">{cuerpo}</g>'


def persona(c, p, t, idi):
    """Figura plana; (x, y) son los pies."""
    k= col(c.get('color', 'turquesa'))
    cuerpo= (f'<rect x="-34" y="-150" width="68" height="110" rx="30" fill="{k}"/>'
             f'<rect x="-30" y="-52" width="24" height="52" rx="12" fill="#22335e"/><rect x="6" y="-52" width="24" height="52" rx="12" fill="#22335e"/>'
             f'<circle cx="0" cy="-190" r="40" fill="{col("piel")}"/>')
    if c.get('brazos') == 'arriba':
        cuerpo+= (f'<line x1="-30" y1="-130" x2="-70" y2="-200" stroke="{k}" stroke-width="20" stroke-linecap="round"/>'
                  f'<line x1="30" y1="-130" x2="70" y2="-200" stroke="{k}" stroke-width="20" stroke-linecap="round"/>')
    return _girado(c.get('x', 540), c.get('y', 1250), c.get('rot', 0), c.get('escala', 1.0), cuerpo)


def casa(c, p, t, idi):
    cuerpo= ('<rect x="-110" y="-170" width="220" height="170" fill="#f4e3c1"/><polygon points="-135,-170 0,-280 135,-170" fill="#ff5a5f"/>'
             '<rect x="-30" y="-90" width="60" height="90" rx="6" fill="#8a5a3c"/><rect x="50" y="-130" width="44" height="44" rx="6" fill="#7fd3ff"/>')
    return _girado(c.get('x', 300), c.get('y', 1250), c.get('rot', 0), c.get('escala', 1.0), cuerpo)


def arbol(c, p, t, idi):
    cuerpo= ('<rect x="-16" y="-120" width="32" height="120" rx="8" fill="#8a5a3c"/><circle cx="0" cy="-190" r="85" fill="#2f9e58"/>'
             '<circle cx="-40" cy="-150" r="50" fill="#2f9e58"/><circle cx="42" cy="-150" r="54" fill="#38b266"/>')
    return _girado(c.get('x', 800), c.get('y', 1250), c.get('rot', 0), c.get('escala', 1.0), cuerpo)


def coche(c, p, t, idi):
    cuerpo= ('<rect x="-120" y="-80" width="240" height="60" rx="22" fill="#ffd60a"/><path d="M-70,-80 L-40,-130 L50,-130 L80,-80 Z" fill="#ffd60a"/>'
             '<path d="M-52,-84 L-32,-120 L0,-120 L0,-84 Z" fill="#7fd3ff"/><path d="M10,-84 L10,-120 L44,-120 L62,-84 Z" fill="#7fd3ff"/>'
             '<circle cx="-65" cy="-20" r="28" fill="#1b2340"/><circle cx="68" cy="-20" r="28" fill="#1b2340"/>')
    return _girado(c.get('x', 540), c.get('y', 1250), c.get('rot', 0), c.get('escala', 1.0), cuerpo)


def punto(c, p, t, idi):
    """Marcador que late sobre un sitio."""
    x, y, r= c.get('x', 540), c.get('y', 900), c.get('r', 20)
    k= col(c.get('color', 'rojo'))
    f= (t * 1.4) % 1
    return (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r * (1 + 2.2 * f):.1f}" fill="none" stroke="{k}" stroke-width="6" opacity="{1 - f:.2f}"/>'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{k}" stroke="#fff" stroke-width="5"/>')


def luna(c, p, t, idi):
    return planeta({**c, 'tipo': 'luna', 'atm': False}, p, t, idi)


def circulo(c, p, t, idi):
    borde= f' stroke="{col(c["borde"])}" stroke-width="{c.get("grosor", 6)}"' if c.get('borde') else ''
    return (f'<circle cx="{c.get("x", 540):.1f}" cy="{c.get("y", 900):.1f}" r="{c.get("r", 100):.1f}" '
            f'fill="{col(c.get("color", "none"))}" opacity="{c.get("op", 1.0):.2f}"{borde}/>')


def caja(c, p, t, idi):
    return (f'<rect x="{c.get("x", 0):.1f}" y="{c.get("y", 0):.1f}" width="{c.get("ancho", 100):.1f}" height="{c.get("alto", 100):.1f}" '
            f'rx="{c.get("radio", 0)}" fill="{col(c.get("color", "blanco"))}" opacity="{c.get("op", 1.0):.2f}"/>')


def encuesta(c, p, t, idi):
    """Tarjeta para que el publico elija el siguiente episodio en comentarios."""
    y= c.get('y', 1180)
    s= f'<rect x="90" y="{y}" width="900" height="{150 + 130 * len(c["opciones"])}" rx="40" fill="{col("chip")}" stroke="{col("borde")}" stroke-width="5"/>'
    s+= _txt(540, y + 90, c['titulo'], 58, 'amarillo')
    for i, o in enumerate(c['opciones']):
        yy= y + 130 + i * 130
        k= ['turquesa', 'naranja', 'morado'][i % 3]
        s+= f'<rect x="130" y="{yy}" width="820" height="104" rx="52" fill="#16285c"/>'
        s+= f'<circle cx="182" cy="{yy + 52}" r="40" fill="{col(k)}"/>' + _txt(182, yy + 72, 'ABC'[i], 54, '#0a1230')
        s+= _txt(245, yy + 70, o, 46 if len(o) < 26 else 38, 'blanco', 'start')
    return s




# ---------- piezas para cuerpo humano, mar y corte de la Tierra ----------

def cuerpo(c, p, t, idi):
    """Silueta grande de frente. agua (0..1) la llena por dentro; organos: cerebro, corazon, pulmones, rinones.
    alerta: organo que late en rojo; aire (0..1) hincha los pulmones; latido: pulsaciones por segundo."""
    x, y, e= c.get('x', 540), c.get('y', 1000), c.get('escala', 1.0)
    _uid[0]+= 1
    cid= f'cu{_uid[0]}'
    def rr(x0, y0, w, h, r):
        return (f'M{x0 + r},{y0} h{w - 2 * r} a{r},{r} 0 0 1 {r},{r} v{h - 2 * r} a{r},{r} 0 0 1 {-r},{r} h{-(w - 2 * r)} '
                f'a{r},{r} 0 0 1 {-r},{-r} v{-(h - 2 * r)} a{r},{r} 0 0 1 {r},{-r} Z ')
    # un solo trazo para que sirva tambien de recorte del agua
    forma= ('<path d="M-88,-300 a88,88 0 1 1 176,0 a88,88 0 1 1 -176,0 Z ' + rr(-36, -230, 72, 60, 20) + rr(-125, -200, 250, 390, 64)
            + rr(-200, -192, 66, 330, 33) + rr(134, -192, 66, 330, 33) + rr(-112, 140, 100, 310, 44) + rr(12, 140, 100, 310, 44) + '"/>')
    g= f'<defs><clipPath id="{cid}">{forma}</clipPath></defs><g fill="{col(c.get("color", "#2b4a94"))}">{forma}</g>'
    agua= c.get('agua')
    if agua is not None:
        niv= 450 - 838 * max(0.0, min(1.0, agua))
        ola= ' '.join(f'L{xx},{niv + 9 * math.sin(xx / 38 + t * 4):.1f}' for xx in range(-210, 211, 30))
        g+= f'<g clip-path="url(#{cid})"><path d="M-210,460 {ola} L210,460 Z" fill="{col(c.get("liquido", "#3aa0ff"))}"/></g>'
    org= c.get('organos', [])
    alerta= c.get('alerta')
    lat= 1 + 0.12 * max(0.0, math.sin(t * 2 * math.pi * c.get('latido', 1.2))) ** 4

    def aviso(cx, cy, r):
        f= (t * 1.6) % 1
        return f'<circle cx="{cx}" cy="{cy}" r="{r * (1 + 0.9 * f):.1f}" fill="none" stroke="{col("rojo")}" stroke-width="8" opacity="{1 - f:.2f}"/>'
    if 'cerebro' in org:
        k= col('rojo') if alerta == 'cerebro' else '#ff9ec4'
        g+= f'<ellipse cx="0" cy="-318" rx="56" ry="42" fill="{k}"/><path d="M0,-358 L0,-280 M-28,-340 q14,22 0,44 M28,-340 q-14,22 0,44" stroke="#c2577f" stroke-width="5" fill="none"/>'
        if alerta == 'cerebro':
            g+= aviso(0, -318, 70)
    if 'pulmones' in org:
        a= 0.75 + 0.35 * c.get('aire', 0.6)
        k= col('rojo') if alerta == 'pulmones' else col(c.get('color_pulmon', '#ff8fa3'))
        g+= (f'<ellipse cx="-56" cy="-95" rx="{44 * a:.1f}" ry="{78 * a:.1f}" fill="{k}"/><ellipse cx="56" cy="-95" rx="{44 * a:.1f}" ry="{78 * a:.1f}" fill="{k}"/>'
             '<rect x="-6" y="-185" width="12" height="70" rx="6" fill="#ffd0d8"/>')
        if alerta == 'pulmones':
            g+= aviso(0, -95, 110)
    if 'corazon' in org:
        g+= (f'<g transform="translate(-22 -90) scale({lat:.3f})"><path d="M0,26 C-46,-8 -30,-44 0,-22 C30,-44 46,-8 0,26 Z" fill="{col("rojo")}" stroke="#fff" stroke-width="4"/></g>')
        if alerta == 'corazon':
            g+= aviso(-22, -92, 52)
    if 'rinones' in org:
        k= col('rojo') if alerta == 'rinones' else '#c97b5a'
        g+= f'<ellipse cx="-52" cy="60" rx="26" ry="42" fill="{k}" transform="rotate(14 -52 60)"/><ellipse cx="52" cy="60" rx="26" ry="42" fill="{k}" transform="rotate(-14 52 60)"/>'
        if alerta == 'rinones':
            g+= aviso(0, 60, 95)
    cara= c.get('cara')
    if cara and 'cerebro' not in org:
        g+= '<circle cx="-30" cy="-312" r="10" fill="#fff"/><circle cx="30" cy="-312" r="10" fill="#fff"/>'
        g+= {'bien': '<path d="M-26,-272 q26,24 52,0" stroke="#fff" stroke-width="8" fill="none" stroke-linecap="round"/>',
             'mal': '<path d="M-26,-262 q26,-22 52,0" stroke="#fff" stroke-width="8" fill="none" stroke-linecap="round"/>',
             'seca': '<rect x="-24" y="-276" width="48" height="12" rx="6" fill="#fff"/>'}.get(cara, '')
    return _girado(x, y, c.get('rot', 0), e, g)


def corte(c, p, t, idi):
    """La Tierra cortada por la mitad, con sus capas, un tunel de lado a lado y un viajero (-1 arriba, 1 abajo)."""
    x, y, r= c.get('x', 540), c.get('y', 1000), c.get('r', 420)
    s= f'<circle cx="{x}" cy="{y}" r="{r * 1.05:.1f}" fill="#7fc4ff" opacity="0.2"/>'
    for f, k in ((1.0, '#3a8f5a'), (0.965, '#8a5a3c'), (0.90, '#d9562b'), (0.56, '#f08a2e'), (0.22, '#ffd75e')):
        s+= f'<circle cx="{x}" cy="{y}" r="{r * f:.1f}" fill="{k}"/>'
    br= c.get('brillo', 0.0)
    if br > 0.01:
        s+= f'<circle cx="{x}" cy="{y}" r="{r * (0.3 + 0.08 * math.sin(t * 6)):.1f}" fill="#fff3b0" opacity="{0.55 * br:.2f}"/>'
    if c.get('tunel', True):
        a= r * 0.075
        s+= f'<rect x="{x - a:.1f}" y="{y - r:.1f}" width="{2 * a:.1f}" height="{2 * r:.1f}" fill="#0a1230"/>'
    v= c.get('viajero')
    if v is not None:
        vy= y + v * r
        s+= (f'<circle cx="{x}" cy="{vy:.1f}" r="{r * 0.06:.1f}" fill="{col("turquesa")}" stroke="#fff" stroke-width="5"/>'
             f'<circle cx="{x}" cy="{vy - r * 0.075:.1f}" r="{r * 0.038:.1f}" fill="{col("piel")}"/>')
        est= c.get('estela', 0.0)
        if abs(est) > 0.01:
            s+= (f'<line x1="{x}" y1="{vy - est * r * 0.12:.1f}" x2="{x}" y2="{vy - est * r * 0.4:.1f}" stroke="#fff" stroke-width="10" '
                 f'stroke-linecap="round" opacity="0.5"/>')
    return s


def mar(c, p, t, idi):
    """Agua con olas; y es la altura de la superficie."""
    y= c.get('y', 1300)
    k= col(c.get('color', 'mar'))
    amp= c.get('olas', 16)
    ola= ' '.join(f'L{xx},{y + amp * math.sin(xx / 70 + t * 2.4):.1f}' for xx in range(-40, W + 80, 40))
    ola2= ' '.join(f'L{xx},{y + 26 + amp * math.sin(xx / 90 - t * 1.8):.1f}' for xx in range(-40, W + 80, 40))
    return (f'<path d="M-40,{H + 40} {ola} L{W + 40},{H + 40} Z" fill="{k}" opacity="0.75"/>'
            f'<path d="M-40,{H + 40} {ola2} L{W + 40},{H + 40} Z" fill="{col(c.get("color2", "mar2"))}"/>')


def burbujas(c, p, t, idi):
    r= random.Random(c.get('semilla', 5))
    x0, an= c.get('x', 540), c.get('ancho', 300)
    y0, y1= c.get('y0', 1500), c.get('y1', 500)
    s= ''
    for _ in range(int(c.get('n', 12))):
        f= (r.random() + t * r.uniform(0.15, 0.35)) % 1
        bx= x0 + r.uniform(-an / 2, an / 2) + 14 * math.sin(t * 3 + r.uniform(0, 6))
        s+= (f'<circle cx="{bx:.1f}" cy="{y0 + (y1 - y0) * f:.1f}" r="{r.choice([8, 12, 16, 22])}" fill="none" stroke="#dff3ff" '
             f'stroke-width="5" opacity="{0.8 * (1 - f):.2f}"/>')
    return s


def barrotes(c, p, t, idi):
    x, y, an, al= c.get('x', 190), c.get('y', 560), c.get('ancho', 700), c.get('alto', 900)
    s= f'<rect x="{x}" y="{y}" width="{an}" height="{al}" rx="20" fill="#18203c" stroke="#5a6a94" stroke-width="10"/>'
    return s, ''.join(f'<rect x="{x + 50 + i * (an - 100) / 6 - 11:.1f}" y="{y}" width="22" height="{al}" rx="11" fill="#7d8bb3"/>' for i in range(7))


def celda(c, p, t, idi):
    """Calabozo: pared, persona dentro y barrotes delante."""
    fondo, rejas= barrotes(c, p, t, idi)
    x, y, an, al= c.get('x', 190), c.get('y', 560), c.get('ancho', 700), c.get('alto', 900)
    gotas= ''
    r= random.Random(2)
    for _ in range(6):
        gx= x + r.uniform(60, an - 60)
        f= (r.random() + t * 0.25) % 1
        gotas+= f'<circle cx="{gx:.1f}" cy="{y + 40 + f * (al - 120):.1f}" r="9" fill="#6fc3ff" opacity="{0.9 * (1 - f * 0.6):.2f}"/>'
    return fondo + gotas + persona({'x': x + an / 2, 'y': y + al - 40, 'escala': 1.7, 'color': 'naranja'}, p, t, idi) + rejas


def vaso(c, p, t, idi):
    x, y, e= c.get('x', 540), c.get('y', 1200), c.get('escala', 1.0)
    n= max(0.0, min(1.0, c.get('nivel', 0.8)))
    alto= 300 * n
    g= (f'<path d="M-112,{-alto:.1f} L112,{-alto:.1f} L92,0 L-92,0 Z" fill="#3aa0ff"/>'
        '<path d="M-125,-330 L125,-330 L95,10 L-95,10 Z" fill="#dff3ff" opacity="0.28" stroke="#fff" stroke-width="10" stroke-linejoin="round"/>')
    return _girado(x, y, c.get('rot', 0), e, g)


def gota(c, p, t, idi):
    g= '<path d="M0,-70 C40,-10 52,14 52,34 A52,52 0 0 1 -52,34 C-52,14 -40,-10 0,-70 Z" fill="#3aa0ff" stroke="#fff" stroke-width="6"/>'
    return _girado(c.get('x', 540), c.get('y', 900), 0, c.get('escala', 1.0), g)


def tortuga(c, p, t, idi):
    g= ('<ellipse cx="-70" cy="20" rx="34" ry="16" fill="#6cc48a"/><ellipse cx="60" cy="24" rx="30" ry="14" fill="#6cc48a"/>'
        '<circle cx="104" cy="-14" r="28" fill="#6cc48a"/><circle cx="114" cy="-20" r="6" fill="#0a1230"/>'
        '<ellipse cx="0" cy="-10" rx="88" ry="56" fill="#2f9e58"/><ellipse cx="0" cy="-16" rx="54" ry="30" fill="#38b266"/>')
    return _girado(c.get('x', 540), c.get('y', 1300), c.get('rot', 0), c.get('escala', 1.0), g)


def avion(c, p, t, idi):
    g= ('<rect x="-150" y="-26" width="300" height="52" rx="26" fill="#f1f6ff"/><polygon points="-20,-10 40,-10 -50,-130 -90,-130" fill="#cfd6e6"/>'
        '<polygon points="-20,10 40,10 -50,130 -90,130" fill="#cfd6e6"/><polygon points="-150,-10 -110,-10 -160,-80 -185,-80" fill="#ff5a5f"/>'
        '<rect x="60" y="-12" width="60" height="14" rx="7" fill="#7fd3ff"/>')
    return _girado(c.get('x', 540), c.get('y', 700), c.get('rot', 0), c.get('escala', 1.0), g)


def cartel(c, p, t, idi):
    """Cartel grande con la pregunta del video: va desde el primer fotograma, en una o dos lineas."""
    x, y, tam= c.get('x', 540), c.get('y', 1540), c.get('tam', 88)
    pal= str(c['texto']).split()
    lineas= [' '.join(pal)]
    if _ancho(lineas[0], tam) > 900 and len(pal) > 1:
        mejor= min(range(1, len(pal)), key=lambda i: abs(len(' '.join(pal[:i])) - len(' '.join(pal[i:]))))
        lineas= [' '.join(pal[:mejor]), ' '.join(pal[mejor:])]
    while max(_ancho(l, tam) for l in lineas) > 900:
        tam-= 4
    an= max(_ancho(l, tam) for l in lineas) + tam * 1.2
    al= tam * 1.25 * len(lineas) + tam * 0.7
    lat= 1 + 0.02 * math.sin(t * 5)
    s= (f'<rect x="{x - an / 2 + 10:.1f}" y="{y - al / 2 + 14:.1f}" width="{an:.1f}" height="{al:.1f}" rx="36" fill="#04102e" opacity="0.6"/>'
        f'<rect x="{x - an / 2:.1f}" y="{y - al / 2:.1f}" width="{an:.1f}" height="{al:.1f}" rx="36" fill="{col(c.get("color", "amarillo"))}"/>')
    for i, l in enumerate(lineas):
        s+= _txt(x, y - al / 2 + tam * 0.35 + tam * 1.25 * (i + 0.72), l, tam, '#0a1230')
    return f'<g transform="translate({x} {y}) scale({lat:.3f}) translate({-x} {-y})">{s}</g>'


def interrogacion(c, p, t, idi):
    bamb= 12 * math.sin(t * 3 + c.get('x', 0))
    return _txt(c.get('x', 540), c.get('y', 900) + bamb, '?', c.get('tam', 120), c.get('color', 'amarillo'), borde='#0a1230')


PIEZAS= {'planeta': planeta, 'sol': sol, 'chip': chip, 'texto': texto, 'contador': contador, 'panel': panel, 'barra': barra,
         'regla': regla, 'flecha': flecha, 'viento': viento, 'suelo': suelo, 'persona': persona, 'casa': casa, 'arbol': arbol,
         'coche': coche, 'punto': punto, 'luna': luna, 'circulo': circulo, 'caja': caja, 'encuesta': encuesta, 'nube': nube, 'carretera': carretera}
_NO_ANIMAR= {'items', 'opciones', 'en', 'sale', 't'}

PIEZAS.update({'cuerpo': cuerpo, 'corte': corte, 'mar': mar, 'burbujas': burbujas, 'celda': celda, 'vaso': vaso, 'gota': gota,
               'tortuga': tortuga, 'avion': avion, 'interrogacion': interrogacion, 'cartel': cartel})
_NO_ANIMAR.update({'organos', 'alerta', 'cara'})


# ---------- piezas del formato "historia" (plano negro con puntitos) ----------

def gente(c, p, t, idi):
    """Multitud de puntitos: salen repartidos por una zona y se van agrupando en los destinos segun 'mov' (0..1)."""
    n, mov= int(c.get('n', 120)), max(0.0, min(1.0, c.get('mov', 0.0)))
    x0, y0, an, al= c.get('x', 140), c.get('y', 520), c.get('ancho', 800), c.get('alto', 420)
    dest= c.get('destinos') or [[540, 1100]]
    r= random.Random(c.get('semilla', 3))
    k= col(c.get('color', 'blanco'))
    s= ''
    for i in range(n):
        ax, ay= x0 + r.uniform(0, an), y0 + r.uniform(0, al)
        d= dest[i % len(dest)]
        ang, rad= r.uniform(0, 6.28), c.get('radio', 70) * math.sqrt(r.uniform(0, 1))
        bx, by= d[0] + rad * math.cos(ang), d[1] + rad * math.sin(ang) * 0.7
        q= suave(max(0.0, min(1.0, mov * 1.35 - r.uniform(0, 0.35))))
        f= r.uniform(0, 6.28)
        x= ax + (bx - ax) * q + 4 * math.sin(t * 3 + f)
        y= ay + (by - ay) * q + 4 * math.cos(t * 2.6 + f)
        s+= f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{c.get("r", 7)}" fill="{k}"/>'
    return s



def tienda(c, p, t, idi):
    """Local con rotulo y persiana que baja segun 'baja' (0..1)."""
    x, y, an, al= c.get('x', 540), c.get('y', 900), c.get('ancho', 300), c.get('alto', 300)
    b= max(0.0, min(1.0, c.get('baja', 0.0)))
    s= (f'<rect x="{x - an / 2:.1f}" y="{y - al:.1f}" width="{an}" height="{al}" rx="10" fill="{col(c.get("color", "#ffb347"))}" opacity="{0.9 - 0.75 * b:.2f}"/>'
        f'<rect x="{x - an / 2:.1f}" y="{y - al - 64:.1f}" width="{an}" height="58" rx="10" fill="#1b1b26" stroke="#3a3a48" stroke-width="4"/>'
        + _txt(x, y - al - 22, c.get('texto', ''), 36, 'blanco'))
    hb= al * b
    if hb > 4:
        s+= f'<rect x="{x - an / 2:.1f}" y="{y - al:.1f}" width="{an}" height="{hb:.1f}" fill="#4a4a58"/>'
        for j in range(int(hb // 22)):
            yy= y - al + 22 * (j + 1)
            s+= f'<line x1="{x - an / 2:.1f}" y1="{yy:.1f}" x2="{x + an / 2:.1f}" y2="{yy:.1f}" stroke="#2c2c38" stroke-width="4"/>'
    return s





def puerta(c, p, t, idi):
    """Puerta de servicio vista de frente; 'abre' (0..1) la entorna y deja ver el hueco."""
    x, y, an, al= c.get('x', 540), c.get('y', 1200), c.get('ancho', 300), c.get('alto', 560)
    a= max(0.0, min(1.0, c.get('abre', 0.0)))
    s= (f'<rect x="{x - an / 2 - 16:.1f}" y="{y - al - 16:.1f}" width="{an + 32}" height="{al + 16}" fill="#3a3a48"/>'
        f'<rect x="{x - an / 2:.1f}" y="{y - al:.1f}" width="{an}" height="{al}" fill="{col(c.get("hueco", "#000000"))}"/>')
    ah= an * (1 - 0.72 * a)
    s+= (f'<polygon points="{x - an / 2:.1f},{y - al:.1f} {x - an / 2 + ah:.1f},{y - al + 34 * a:.1f} {x - an / 2 + ah:.1f},{y - 34 * a:.1f} {x - an / 2:.1f},{y:.1f}" fill="#6b6b7c"/>'
         f'<circle cx="{x - an / 2 + ah - 34:.1f}" cy="{y - al / 2:.1f}" r="13" fill="#d8d8e4"/>')
    return s


def escalera(c, p, t, idi):
    """Escalera que baja hacia la oscuridad: cada peldano mas apagado que el anterior."""
    x, y, n= c.get('x', 300), c.get('y', 560), int(c.get('n', 8))
    v= max(0.0, min(1.0, c.get('ver', 1.0)))
    s= ''
    for i in range(n):
        if i / n > v:
            break
        op= max(0.06, 1 - i / (n - 1) * 0.95)
        s+= f'<rect x="{x + 62 * i:.1f}" y="{y + 82 * i:.1f}" width="150" height="26" rx="6" fill="#9fb0d8" opacity="{op:.2f}"/>'
    return s


PIEZAS.update({'gente': gente, 'tienda': tienda, 'puerta': puerta, 'escalera': escalera})
_NO_ANIMAR.update({'destinos'})


def sala(c, p, t, idi):
    """Recinto del plano: rectangulo con borde y rotulo pequeno."""
    x, y, an, al= c.get('x', 100), c.get('y', 500), c.get('ancho', 300), c.get('alto', 200)
    k= col(c.get('color', '#4a4a58'))
    r= (f'<rect x="{x:.1f}" y="{y:.1f}" width="{an:.1f}" height="{al:.1f}" rx="10" fill="{col(c.get("relleno", "#0e0e16"))}" '
        f'stroke="{k}" stroke-width="{c.get("grosor", 6)}"/>')
    if c.get('texto'):
        r+= _txt(x + an / 2, y + al / 2 + 13, c['texto'], c.get('tam', 36), c.get('tinta', 'gris'), peso=700)
    return r


def ruta(c, p, t, idi):
    """Camino a trazos sobre el plano que se va dibujando segun 'v' (0..1), con un punto que avanza por el."""
    pts= c['puntos']
    v= max(0.0, min(1.0, c.get('v', 1.0)))
    tr= [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])]
    falta= sum(tr) * v
    d= f'M{pts[0][0]},{pts[0][1]}'
    cx, cy= pts[0]
    for (a, b), l in zip(zip(pts, pts[1:]), tr):
        if falta <= 0:
            break
        q= min(1.0, falta / max(l, 1e-6))
        cx, cy= a[0] + (b[0] - a[0]) * q, a[1] + (b[1] - a[1]) * q
        d+= f' L{cx:.1f},{cy:.1f}'
        falta-= l
    k= col(c.get('color', 'amarillo'))
    lat= 1 + 0.25 * math.sin(t * 6)
    return (f'<path d="{d}" fill="none" stroke="{k}" stroke-width="8" stroke-dasharray="18 14" stroke-linecap="round"/>'
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{30 * lat:.1f}" fill="{col("naranja")}" opacity="0.25"/>'
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="18" fill="{col("naranja")}" stroke="#fff" stroke-width="4"/>')


def linterna(c, p, t, idi):
    """Cono de luz que sale de (x, y) con angulo 'rot' en grados (0 = hacia la derecha)."""
    x, y, l, ab= c.get('x', 200), c.get('y', 900), c.get('largo', 600), c.get('abre', 16)
    rot= c.get('rot', 0) + 2 * math.sin(t * 2.3)
    op= max(0.0, min(1.0, c.get('luz', 1.0)))
    h= l * math.tan(math.radians(ab))
    return (f'<g transform="translate({x:.1f} {y:.1f}) rotate({rot:.1f})">'
            f'<polygon points="0,-8 {l},{-h:.1f} {l},{h:.1f} 0,8" fill="#fff6c9" opacity="{0.34 * op:.2f}"/>'
            f'<polygon points="0,-6 {l * 0.6:.1f},{-h * 0.42:.1f} {l * 0.6:.1f},{h * 0.42:.1f} 0,6" fill="#fff6c9" opacity="{0.3 * op:.2f}"/>'
            f'<rect x="-46" y="-16" width="50" height="32" rx="8" fill="#9fb0d8"/></g>')


def movil(c, p, t, idi):
    """Telefono con la bateria en grande; 'v' es la carga (0..1)."""
    x, y, e= c.get('x', 540), c.get('y', 900), c.get('escala', 1.0)
    v= max(0.0, min(1.0, c.get('v', 0.3)))
    k= col('rojo') if v < 0.2 else (col('amarillo') if v < 0.5 else col('turquesa'))
    g= (f'<rect x="-150" y="-280" width="300" height="560" rx="44" fill="#16161f" stroke="#4a4a58" stroke-width="8"/>'
        f'<rect x="-120" y="-240" width="240" height="480" rx="18" fill="#0b0b12"/>'
        f'<rect x="-80" y="-60" width="160" height="80" rx="12" fill="none" stroke="#fff" stroke-width="7"/><rect x="84" y="-36" width="14" height="32" rx="5" fill="#fff"/>'
        f'<rect x="-70" y="-50" width="{140 * v:.1f}" height="60" rx="6" fill="{k}"/>'
        + _txt(0, 110, f'{round(v * 100)}%', 76, k)
        + _txt(0, -150, c.get('texto', ''), 38, 'gris', peso=700))
    return _girado(x, y, 0, e, g)


PIEZAS.update({'sala': sala, 'ruta': ruta, 'linterna': linterna, 'movil': movil})
_NO_ANIMAR.update({'puntos'})


# ---------- piezas vivas para los "Y si" del cuerpo (bichos, peste, moscas, reloj, ojo, luces) ----------

def bichos(c, p, t, idi):
    """Bacterias con ojos que se multiplican: 'n' puede animarse y cada una nueva aparece con un saltito."""
    n= max(0.0, c.get('n', 10))
    x0, y0, an, al= c.get('x', 240), c.get('y', 700), c.get('ancho', 600), c.get('alto', 700)
    r= random.Random(c.get('semilla', 11))
    colores= c.get('colores') or ['#7bd651', '#b7e04a', '#4fc98a', '#e0c341']
    g= ''
    for i in range(int(c.get('max', 80))):
        bx, by= r.uniform(x0, x0 + an), r.uniform(y0, y0 + al)
        rad, k, fase, vel= r.uniform(16, 34) * c.get('escala', 1.0), r.choice(colores), r.uniform(0, 6.28), r.uniform(1.5, 3.5)
        nace= n - i  # cuanto hace que nacio, en unidades de bicho
        if nace <= 0:
            continue
        e= min(1.0, nace * 1.5)
        e= e * (1 + 0.5 * math.sin(e * math.pi) * (1 - e))
        bx+= 9 * math.sin(t * vel + fase)
        by+= 7 * math.cos(t * vel * 0.8 + fase)
        ap= 1 + 0.12 * math.sin(t * vel * 2 + fase)  # se estira y se encoge
        g+= (f'<g transform="translate({bx:.1f} {by:.1f}) scale({e * ap:.3f} {e / ap:.3f})">'
             f'<ellipse rx="{rad * 1.25:.1f}" ry="{rad:.1f}" fill="{k}" stroke="#0a1230" stroke-width="4"/>'
             f'<circle cx="{-rad * 0.4:.1f}" cy="{-rad * 0.15:.1f}" r="{rad * 0.26:.1f}" fill="#fff"/><circle cx="{rad * 0.4:.1f}" cy="{-rad * 0.15:.1f}" r="{rad * 0.26:.1f}" fill="#fff"/>'
             f'<circle cx="{-rad * 0.36:.1f}" cy="{-rad * 0.12:.1f}" r="{rad * 0.12:.1f}" fill="#0a1230"/><circle cx="{rad * 0.44:.1f}" cy="{-rad * 0.12:.1f}" r="{rad * 0.12:.1f}" fill="#0a1230"/>'
             f'</g>')
    return g


def peste(c, p, t, idi):
    """Ondas de mal olor que suben desde (x, y). fuerza 0..1 = cuantas y como de marcadas."""
    x, y, f= c.get('x', 540), c.get('y', 700), max(0.0, min(1.0, c.get('fuerza', 1.0)))
    k= col(c.get('color', '#9bd64a'))
    n= int(round(2 + 7 * f))
    an= c.get('ancho', 520)
    g= ''
    for i in range(n):
        ox= x - an / 2 + an * (i + 0.5) / n
        sube= ((t * 0.55 + i * 0.37) % 1.0)
        yy= y - sube * c.get('alto', 420)
        d= f'M{ox:.1f},{yy:.1f}'
        for j in range(3):
            d+= f' q{26 * (1 if j % 2 == 0 else -1):.0f},-32 0,-64'
        g+= f'<path d="{d}" fill="none" stroke="{k}" stroke-width="{10 + 6 * f:.1f}" stroke-linecap="round" opacity="{(0.25 + 0.65 * f) * math.sin(sube * math.pi):.2f}"/>'
    return g


def moscas(c, p, t, idi):
    """Moscas que dan vueltas alrededor de (x, y)."""
    x, y, n= c.get('x', 540), c.get('y', 700), max(0.0, c.get('n', 4))
    r= random.Random(c.get('semilla', 5))
    g= ''
    for i in range(12):
        rx, ry, vel, fase= r.uniform(120, 300), r.uniform(60, 220), r.uniform(2.2, 4.5) * r.choice([-1, 1]), r.uniform(0, 6.28)
        if i >= n:
            continue
        mx= x + rx * math.cos(t * vel + fase) + 20 * math.sin(t * 9 + fase)
        my= y + ry * math.sin(t * vel * 1.3 + fase)
        ala= 10 + 6 * math.sin(t * 60 + fase)
        g+= (f'<g transform="translate({mx:.1f} {my:.1f})"><ellipse cx="-9" cy="-10" rx="{ala:.1f}" ry="7" fill="#dfe9ff" opacity="0.8"/>'
             f'<ellipse cx="9" cy="-10" rx="{ala:.1f}" ry="7" fill="#dfe9ff" opacity="0.8"/><ellipse rx="13" ry="10" fill="#15151c" stroke="#fff" stroke-width="2"/></g>')
    return g


def reloj(c, p, t, idi):
    """Reloj de agujas. hora (0..24, animable) mueve las agujas; loco 0..1 las hace temblar y adelantarse."""
    x, y, r= c.get('x', 540), c.get('y', 800), c.get('r', 200)
    h, loco= c.get('hora', 3.0), c.get('loco', 0.0)
    h+= loco * 1.5 * math.sin(t * 3.1) + loco * 0.6 * math.sin(t * 11)
    am, ah= (h % 1) * 2 * math.pi, (h % 12) / 12 * 2 * math.pi
    k= col(c.get('color', 'blanco'))
    g= f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="#101a3d" stroke="{k}" stroke-width="{r * 0.07:.1f}"/>'
    for i in range(12):
        a= i / 12 * 2 * math.pi
        g+= (f'<line x1="{x + r * 0.8 * math.sin(a):.1f}" y1="{y - r * 0.8 * math.cos(a):.1f}" x2="{x + r * 0.9 * math.sin(a):.1f}" y2="{y - r * 0.9 * math.cos(a):.1f}" '
             f'stroke="{k}" stroke-width="{r * 0.04:.1f}" stroke-linecap="round"/>')
    g+= (f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x + r * 0.5 * math.sin(ah):.1f}" y2="{y - r * 0.5 * math.cos(ah):.1f}" stroke="{k}" stroke-width="{r * 0.08:.1f}" stroke-linecap="round"/>'
         f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x + r * 0.74 * math.sin(am):.1f}" y2="{y - r * 0.74 * math.cos(am):.1f}" stroke="{col(c.get("aguja", "amarillo"))}" stroke-width="{r * 0.05:.1f}" stroke-linecap="round"/>'
         f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r * 0.07:.1f}" fill="{k}"/>')
    return g


def ojo(c, p, t, idi):
    """Ojo grande. pupila 0..1 (dilatacion), mira (-1..1) lo mueve a los lados, cierre 0..1 baja el parpado; parpadea solo."""
    x, y, e= c.get('x', 540), c.get('y', 800), c.get('escala', 1.0)
    pup, mira= max(0.0, min(1.0, c.get('pupila', 0.4))), c.get('mira', 0.0)
    cierre= max(c.get('cierre', 0.0), 1.0 if (t + 0.4) % 2.7 < 0.11 else 0.0)
    _uid[0]+= 1
    cid= f'oj{_uid[0]}'
    forma= '<path d="M-300,0 Q0,-230 300,0 Q0,230 -300,0 Z"/>'
    ix= 70 * mira + 6 * math.sin(t * 1.3)
    g= (f'<defs><clipPath id="{cid}">{forma}</clipPath></defs><g fill="#fff">{forma}</g><g clip-path="url(#{cid})">'
        f'<circle cx="{ix:.1f}" cy="0" r="135" fill="{col(c.get("iris", "#3aa0ff"))}"/><circle cx="{ix:.1f}" cy="0" r="135" fill="none" stroke="#0a1230" stroke-width="8" opacity="0.5"/>'
        f'<circle cx="{ix:.1f}" cy="0" r="{40 + 80 * pup:.1f}" fill="#05070f"/><circle cx="{ix + 38:.1f}" cy="-44" r="20" fill="#fff" opacity="0.9"/>'
        f'<rect x="-320" y="{-240:.0f}" width="640" height="{480 * cierre:.1f}" fill="{col(c.get("parpado", "#f2c29b"))}"/></g>'
        f'<g fill="none" stroke="#0a1230" stroke-width="12">{forma}</g>')
    return f'<g transform="translate({x:.1f} {y:.1f}) scale({e:.3f})">{g}</g>'


def luces(c, p, t, idi):
    """Luces fantasma que flotan y laten (lo que inventa el cerebro a oscuras). fuerza 0..1."""
    f= max(0.0, min(1.0, c.get('fuerza', 1.0)))
    x0, y0, an, al= c.get('x', 140), c.get('y', 500), c.get('ancho', 800), c.get('alto', 800)
    r= random.Random(c.get('semilla', 9))
    g= ''
    for i in range(int(c.get('n', 9))):
        lx, ly, rad, k= r.uniform(x0, x0 + an), r.uniform(y0, y0 + al), r.uniform(40, 110), r.choice(['#ff5a8a', '#5ad1ff', '#ffe45a', '#9b7bff', '#5affb0'])
        fase, vel= r.uniform(0, 6.28), r.uniform(0.6, 1.6)
        lx+= 60 * math.sin(t * vel + fase)
        ly+= 45 * math.cos(t * vel * 0.7 + fase)
        op= f * (0.25 + 0.3 * (1 + math.sin(t * vel * 2.2 + fase)) / 2)
        for m, o in ((1.0, 0.35), (0.65, 0.6), (0.3, 1.0)):
            g+= f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="{rad * m:.1f}" fill="{k}" opacity="{op * o:.2f}"/>'
    return g


PIEZAS.update({'bichos': bichos, 'peste': peste, 'moscas': moscas, 'reloj': reloj, 'ojo': ojo, 'luces': luces})
_NO_ANIMAR.update({'colores'})


def fotograma(esc, tl, dur, idi='es'):
    """SVG completo de la escena en el segundo tl."""
    p= tl / max(dur, 1e-6)
    _uid[0]= 0
    s= f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">' + cielo(esc.get('cielo', 'espacio'), tl)
    cam= esc.get('cam')
    if cam:
        z, cx, cy= valor(cam.get('z', 1.0), p), valor(cam.get('x', W / 2), p), valor(cam.get('y', H / 2), p)
        s+= f'<g transform="translate({W / 2:.1f} {H / 2:.1f}) scale({z:.4f}) translate({-cx:.1f} {-cy:.1f})">'
    fijas= ''
    for capa in esc.get('capas', []):
        en= capa.get('en', 0.0)
        if p < en or p >= capa.get('sale', 9):
            continue
        c= {k: (v if k in _NO_ANIMAR else valor(v, p)) for k, v in capa.items()}
        g= PIEZAS[capa['t']](c, p, tl, idi)
        if en > 0:
            # aparece con un saltito
            q= min(1.0, (tl - en * dur) / 0.28)
            e= 1 + 0.18 * math.sin(q * math.pi) * (1 - q) - 0.35 * (1 - q) ** 2
            ax, ay= c.get('x', c.get('x1', W / 2)), c.get('y', c.get('y1', H / 2))
            g= f'<g opacity="{min(1.0, q * 2.5):.2f}" transform="translate({ax:.1f} {ay:.1f}) scale({e:.3f}) translate({-ax:.1f} {-ay:.1f})">{g}</g>'
        if c.get('alfa') is not None:
            g= f'<g opacity="{max(0.0, min(1.0, c["alfa"])):.2f}">{g}</g>'
        if capa.get('fija'):
            fijas+= g  # no le afecta la camara (rotulos, marcadores)
        else:
            s+= g
    if cam:
        s+= '</g>'
    return s + fijas + '</svg>'


# ---------- piezas del formato "cuento" (un Y si contado como historia, con protagonista) ----------

def prota(c, p, t, idi):
    """Personaje plano con cara; (x, y) son los pies. 'sin_cara' (0..1) le borra la cara y deja un interrogante."""
    ropa, pelo, piel= col(c.get('ropa', 'turquesa')), col(c.get('pelo', '#3a2a4a')), col(c.get('piel', 'piel'))
    cara, mira= c.get('cara', 'normal'), c.get('mira', 0)
    sc= max(0.0, min(1.0, c.get('sin_cara', 0)))
    f= c.get('x', 0) * 0.013
    quieto= c.get('quieto')
    dy= 0.0 if quieto else -5 * math.sin(t * 2.4 + f)
    g= ('<rect x="-62" y="-170" width="52" height="170" rx="22" fill="#22335e"/><rect x="10" y="-170" width="52" height="170" rx="22" fill="#22335e"/>'
        '<rect x="-74" y="-26" width="68" height="26" rx="13" fill="#f1f6ff"/><rect x="6" y="-26" width="68" height="26" rx="13" fill="#f1f6ff"/>')
    brazo= c.get('brazo', 'abajo')
    bi= f'<line x1="-98" y1="{-345 + dy:.1f}" x2="-122" y2="{-205 + dy:.1f}" stroke="{ropa}" stroke-width="46" stroke-linecap="round"/><circle cx="-123" cy="{-190 + dy:.1f}" r="24" fill="{piel}"/>'
    if brazo == 'saluda':
        ay= -500 + 14 * math.sin(t * 9)
        bd= f'<line x1="98" y1="{-345 + dy:.1f}" x2="172" y2="{ay + 40:.1f}" stroke="{ropa}" stroke-width="46" stroke-linecap="round"/><circle cx="178" cy="{ay:.1f}" r="26" fill="{piel}"/>'
    elif brazo == 'taza':
        bd= f'<path d="M98,-345 L150,-250 L70,-395" fill="none" stroke="{ropa}" stroke-width="46" stroke-linecap="round" stroke-linejoin="round"/><circle cx="66" cy="-400" r="26" fill="{piel}"/>'
    elif brazo == 'apunta':
        bd= f'<line x1="98" y1="{-345 + dy:.1f}" x2="205" y2="{-420 + dy:.1f}" stroke="{ropa}" stroke-width="46" stroke-linecap="round"/><circle cx="220" cy="{-430 + dy:.1f}" r="26" fill="{piel}"/>'
    elif brazo == 'frente':
        bd= f'<line x1="98" y1="{-345 + dy:.1f}" x2="215" y2="{-330 + dy:.1f}" stroke="{ropa}" stroke-width="46" stroke-linecap="round"/><circle cx="232" cy="{-330 + dy:.1f}" r="26" fill="{piel}"/>'
    else:
        bd= f'<line x1="98" y1="{-345 + dy:.1f}" x2="122" y2="{-205 + dy:.1f}" stroke="{ropa}" stroke-width="46" stroke-linecap="round"/><circle cx="123" cy="{-190 + dy:.1f}" r="24" fill="{piel}"/>'
    g+= bi + bd + f'<rect x="-105" y="{-400 + dy:.1f}" width="210" height="{270 - dy:.1f}" rx="70" fill="{ropa}"/>'
    hy= -485 + dy * 1.4
    if c.get('largo'):
        g+= f'<rect x="-122" y="{hy - 40:.1f}" width="244" height="190" rx="60" fill="{pelo}"/>'
    g+= f'<circle cx="0" cy="{hy:.1f}" r="105" fill="{piel}"/>'
    g+= f'<path d="M-108,{hy - 8:.1f} A108,108 0 0 1 108,{hy - 8:.1f} Q60,{hy - 62:.1f} 0,{hy - 50:.1f} Q-60,{hy - 40:.1f} -108,{hy - 8:.1f} Z" fill="{pelo}"/>'
    cs= ''
    grande= 1.25 if cara in ('sorpresa', 'miedo') else 1.0
    cerr= (t + f * 7) % 3.3 < 0.12 and cara not in ('sorpresa',) and not quieto
    for lado in (-1, 1):
        ex, ey= lado * 40 + 7 * mira, hy + 12
        if cerr:
            cs+= f'<line x1="{ex - 18:.1f}" y1="{ey:.1f}" x2="{ex + 18:.1f}" y2="{ey:.1f}" stroke="#1b2340" stroke-width="7" stroke-linecap="round"/>'
        else:
            cs+= (f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="{21 * grande:.1f}" fill="#fff"/>'
                  f'<circle cx="{ex + 7 * mira:.1f}" cy="{ey + 2:.1f}" r="{10 * grande:.1f}" fill="#1b2340"/>')
        if cara in ('triste', 'miedo'):
            cs+= f'<line x1="{ex - 20 * lado:.1f}" y1="{ey - 44:.1f}" x2="{ex + 16 * lado:.1f}" y2="{ey - 34:.1f}" stroke="{pelo}" stroke-width="8" stroke-linecap="round"/>'
        elif cara == 'seria':
            cs+= f'<line x1="{ex - 20:.1f}" y1="{ey - 36:.1f}" x2="{ex + 20:.1f}" y2="{ey - 36:.1f}" stroke="{pelo}" stroke-width="8" stroke-linecap="round"/>'
    by= hy + 62
    if cara == 'sonrie':
        cs+= f'<path d="M-26,{by - 6:.1f} Q0,{by + 22:.1f} 26,{by - 6:.1f}" fill="none" stroke="#1b2340" stroke-width="8" stroke-linecap="round"/>'
    elif cara == 'triste':
        cs+= f'<path d="M-24,{by + 8:.1f} Q0,{by - 14:.1f} 24,{by + 8:.1f}" fill="none" stroke="#1b2340" stroke-width="8" stroke-linecap="round"/>'
    elif cara in ('sorpresa', 'miedo'):
        cs+= f'<ellipse cx="0" cy="{by + 4:.1f}" rx="15" ry="{20 if cara == "sorpresa" else 13}" fill="#1b2340"/>'
    else:
        cs+= f'<line x1="-18" y1="{by:.1f}" x2="18" y2="{by:.1f}" stroke="#1b2340" stroke-width="8" stroke-linecap="round"/>'
    g+= f'<g opacity="{1 - sc:.2f}">{cs}</g>'
    if sc > 0.02:
        g+= f'<g opacity="{sc:.2f}">{_txt(0, hy + 58, "?", 150, "gris")}</g>'
    return _girado(c.get('x', 540), c.get('y', 1380), c.get('rot', 0), c.get('escala', 1.0), g)


def hud(c, p, t, idi):
    """Rotulo fino de arriba que dice en que momento de la historia estamos."""
    x, y, s= c.get('x', 540), c.get('y', 440), str(c['texto'])
    k= col(c.get('color', 'amarillo'))
    a= len(s) * 24 + 110
    lat= 0.35 + 0.65 * (math.sin(t * 5) > 0)
    return (f'<rect x="{x - a / 2:.1f}" y="{y - 30}" width="{a:.1f}" height="60" rx="8" fill="#05081a" stroke="{k}" stroke-width="3" opacity="0.92"/>'
            f'<circle cx="{x - a / 2 + 32:.1f}" cy="{y}" r="8" fill="{col("rojo")}" opacity="{lat:.2f}"/>'
            f'<text x="{x + 16:.1f}" y="{y + 11}" text-anchor="middle" font-family="DejaVu Sans Mono, monospace" font-weight="700" font-size="30" '
            f'letter-spacing="5" fill="{k}">{s}</text>')


def bocadillo(c, p, t, idi):
    x, y, tam, s= c.get('x', 540), c.get('y', 700), c.get('tam', 56), str(c['texto'])
    a, h= _ancho(s, tam) + tam * 1.3, tam * 1.9
    cx= x + c.get('cola', 0) * a * 0.28
    k= col(c.get('color', 'blanco'))
    return (f'<polygon points="{cx - 26:.1f},{y + h / 2 - 4:.1f} {cx + 26:.1f},{y + h / 2 - 4:.1f} {cx + c.get("cola", 0) * 30:.1f},{y + h / 2 + 46:.1f}" fill="{k}"/>'
            f'<rect x="{x - a / 2:.1f}" y="{y - h / 2:.1f}" width="{a:.1f}" height="{h:.1f}" rx="{h * 0.36:.1f}" fill="{k}"/>'
            + _txt(x, y + tam * 0.34, s, tam, '#0a1230'))


def cruz(c, p, t, idi):
    x, y, r= c.get('x', 540), c.get('y', 900), c.get('r', 80)
    k= col(c.get('color', 'rojo'))
    return (f'<line x1="{x - r:.1f}" y1="{y - r:.1f}" x2="{x + r:.1f}" y2="{y + r:.1f}" stroke="{k}" stroke-width="{c.get("grosor", 24)}" stroke-linecap="round"/>'
            f'<line x1="{x + r:.1f}" y1="{y - r:.1f}" x2="{x - r:.1f}" y2="{y + r:.1f}" stroke="{k}" stroke-width="{c.get("grosor", 24)}" stroke-linecap="round"/>')


def sirena(c, p, t, idi):
    """Luces roja y azul que se alternan, como un coche de policia fuera de plano."""
    y= c.get('y', 900)
    a= (math.sin(t * 11) + 1) / 2
    return (f'<circle cx="-60" cy="{y}" r="520" fill="#ff2d3d" opacity="{0.34 * a:.2f}"/>'
            f'<circle cx="{W + 60}" cy="{y}" r="520" fill="#2d6bff" opacity="{0.34 * (1 - a):.2f}"/>')


def llave(c, p, t, idi):
    k= col(c.get('color', 'amarillo'))
    g= (f'<circle cx="-90" cy="0" r="52" fill="none" stroke="{k}" stroke-width="24"/><rect x="-42" y="-12" width="190" height="24" rx="10" fill="{k}"/>'
        f'<rect x="96" y="6" width="22" height="42" rx="6" fill="{k}"/><rect x="130" y="6" width="18" height="30" rx="6" fill="{k}"/>')
    return _girado(c.get('x', 540), c.get('y', 900) + 6 * math.sin(t * 3), c.get('rot', 0), c.get('escala', 1.0), g)


def camara(c, p, t, idi):
    """Camara de vigilancia en (x, y) que enfoca con un cono hacia abajo a la derecha o izquierda ('lado')."""
    x, y, lado= c.get('x', 200), c.get('y', 620), c.get('lado', 1)
    led= 0.3 + 0.7 * (math.sin(t * 7) > 0)
    g= (f'<polygon points="60,10 {c.get("largo", 760)},{c.get("abre", 330)} {c.get("largo", 760) - 420},{c.get("abre", 330) + 240}" fill="#ff5a5f" opacity="0.13"/>'
        '<rect x="-20" y="-70" width="16" height="70" fill="#4a4a58"/><rect x="-70" y="-34" width="150" height="68" rx="14" fill="#cfd6e6" transform="rotate(18)"/>'
        '<circle cx="70" cy="22" r="20" fill="#1b2340"/>' f'<circle cx="-30" cy="-8" r="9" fill="#ff2d3d" opacity="{led:.2f}"/>')
    return f'<g transform="translate({x:.1f} {y:.1f}) scale({lado} 1)">{g}</g>'


def movilcara(c, p, t, idi):
    """Telefono intentando reconocer una cara: ovalo a trazos, linea de escaneo y aviso."""
    x, y, e= c.get('x', 540), c.get('y', 950), c.get('escala', 1.0)
    k= col(c.get('color', 'rojo'))
    sy= -120 + 200 * ((t * 0.9) % 1)
    g= ('<rect x="-190" y="-340" width="380" height="680" rx="54" fill="#16161f" stroke="#4a4a58" stroke-width="8"/>'
        '<rect x="-160" y="-300" width="320" height="600" rx="24" fill="#0b0b12"/>'
        f'<ellipse cx="0" cy="-40" rx="96" ry="124" fill="none" stroke="{k}" stroke-width="8" stroke-dasharray="20 14"/>'
        f'<line x1="-120" y1="{sy:.1f}" x2="120" y2="{sy:.1f}" stroke="{k}" stroke-width="6" opacity="0.8"/>'
        + _txt(0, -10, '?', 130, k) + _txt(0, 190, c.get('texto', ''), 34, k, peso=700))
    return _girado(x, y, 0, e, g)


_FOTO= [(-175, '#8a8fa8', '#9b6bff', 1), (0, '#3a2a4a', '#35e0c2', 1), (175, '#5a3a1e', '#ff9f43', 0)]


def foto(c, p, t, idi):
    """Foto de familia con tres personas. 'marca' (0 madre, 1 ella, 2 el chico) rodea a una; 'duda' (0..1) pone un interrogante sobre el chico."""
    x, y, e= c.get('x', 540), c.get('y', 950), c.get('escala', 1.0)
    g= ('<rect x="-330" y="-260" width="660" height="560" rx="10" fill="#04102e" opacity="0.5" transform="translate(14 18)"/>'
        '<rect x="-330" y="-260" width="660" height="560" rx="10" fill="#f4eede"/><rect x="-296" y="-226" width="592" height="420" fill="#7fb7e6"/>'
        '<rect x="-296" y="80" width="592" height="114" fill="#5fae6e"/>')
    for i, (fx, pelo, ropa, largo) in enumerate(_FOTO):
        if largo:
            g+= f'<rect x="{fx - 66}" y="-150" width="132" height="130" rx="40" fill="{pelo}"/>'
        g+= (f'<rect x="{fx - 78}" y="10" width="156" height="184" rx="50" fill="{ropa}"/><circle cx="{fx}" cy="-66" r="62" fill="{col("piel")}"/>'
             f'<path d="M{fx - 64},-72 A64,64 0 0 1 {fx + 64},-72 Q{fx + 30},-104 {fx},-96 Q{fx - 34},-90 {fx - 64},-72 Z" fill="{pelo}"/>'
             f'<circle cx="{fx - 22}" cy="-58" r="8" fill="#1b2340"/><circle cx="{fx + 22}" cy="-58" r="8" fill="#1b2340"/>'
             f'<path d="M{fx - 16},-34 Q{fx},-20 {fx + 16},-34" fill="none" stroke="#1b2340" stroke-width="6" stroke-linecap="round"/>')
    m= c.get('marca')
    if m is not None:
        fx= _FOTO[int(m)][0]
        lat= 1 + 0.05 * math.sin(t * 6)
        g+= f'<circle cx="{fx}" cy="-60" r="{96 * lat:.1f}" fill="none" stroke="{col("rojo" if int(m) == 2 else "amarillo")}" stroke-width="10"/>'
    d= max(0.0, min(1.0, c.get('duda', 0)))
    if d > 0.02:
        g+= f'<g opacity="{d:.2f}">{_txt(175, -150, "?", 130, "rojo", borde="#0a1230")}</g>'
    return _girado(x, y, c.get('rot', -3), e, g)


def dorso(c, p, t, idi):
    """Reverso de la foto con una frase escrita a mano que se va revelando segun 'v' (0..1)."""
    x, y, e= c.get('x', 540), c.get('y', 950), c.get('escala', 1.0)
    v= max(0.0, min(1.0, c.get('v', 1.0)))
    _uid[0]+= 1
    cid= f'dz{_uid[0]}'
    lineas= str(c['texto']).split('|')
    g= ('<rect x="-330" y="-260" width="660" height="560" rx="10" fill="#04102e" opacity="0.5" transform="translate(14 18)"/>'
        '<rect x="-330" y="-260" width="660" height="560" rx="10" fill="#f4eede"/>'
        f'<defs><clipPath id="{cid}"><rect x="-330" y="-260" width="{660 * v:.1f}" height="560"/></clipPath></defs><g clip-path="url(#{cid})">')
    for i, l in enumerate(lineas):
        yy= 40 - (len(lineas) - 1) * 60 + i * 120
        g+= (f'<line x1="-250" y1="{yy + 26}" x2="250" y2="{yy + 26}" stroke="#d9a0a0" stroke-width="3"/>'
             f'<text x="0" y="{yy}" text-anchor="middle" font-family="DejaVu Serif, serif" font-style="italic" font-weight="700" font-size="{c.get("tam", 86)}" fill="#8a1f2b">{l}</text>')
    return _girado(x, y, c.get('rot', 2), e, g + '</g>')


PIEZAS.update({'prota': prota, 'hud': hud, 'bocadillo': bocadillo, 'cruz': cruz, 'sirena': sirena, 'llave': llave, 'camara': camara,
               'movilcara': movilcara, 'foto': foto, 'dorso': dorso})


# ---------- piezas de las historias por partes ----------

def ciudad(c, p, t, idi):
    """Linea de edificios con ventanas; 'luz' (0..1) es la parte de ventanas encendidas."""
    y, k, kv= c.get('y', 1380), col(c.get('color', '#14263a')), col(c.get('ventana', '#ffd98a'))
    r= random.Random(c.get('semilla', 5))
    luz= c.get('luz', 0.3)
    g, x= '', -40
    while x < W + 40:
        an, al= r.choice([150, 190, 230]), r.uniform(320, 760) * c.get('alto', 1.0)
        g+= f'<rect x="{x}" y="{y - al:.1f}" width="{an}" height="{al:.1f}" fill="{k}"/>'
        for fy in range(int(al // 78) - 1):
            for fx in range(an // 60):
                on= r.random() < luz
                g+= f'<rect x="{x + 18 + fx * 58}" y="{y - al + 30 + fy * 78:.1f}" width="30" height="42" rx="4" fill="{kv if on else "#0a1622"}" opacity="{0.95 if on else 0.8}"/>'
        x+= an + 14
    return g


def lluvia(c, p, t, idi):
    """Gotas de lluvia. 'vel' en px/s: con 0 se quedan clavadas en el aire."""
    r= random.Random(c.get('semilla', 4))
    vel, y0, y1= c.get('vel', 0), c.get('y0', 480), c.get('y1', 1380)
    g= ''
    for _ in range(int(c.get('n', 70))):
        x, y, l= r.uniform(0, W), r.uniform(y0, y1), r.uniform(26, 54)
        y= y0 + (y - y0 + t * vel) % (y1 - y0)
        g+= f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x - 5:.1f}" y2="{y + l:.1f}" stroke="{col(c.get("color", "#8fd3ff"))}" stroke-width="6" stroke-linecap="round" opacity="{c.get("op", 0.75)}"/>'
    return g


def taza(c, p, t, idi):
    """Taza con el cafe saliendose y parado en el aire; 'vacia' quita el cafe."""
    k= col(c.get('color', '#f1f6ff'))
    g= (f'<path d="M-90,-70 L90,-70 L72,80 Q0,104 -72,80 Z" fill="{k}"/><path d="M88,-40 Q160,-30 150,20 Q140,60 78,50" fill="none" stroke="{k}" stroke-width="22"/>'
        '<ellipse cx="0" cy="-70" rx="90" ry="20" fill="#0a1622"/>')
    if not c.get('vacia'):
        g+= ('<ellipse cx="0" cy="-70" rx="80" ry="15" fill="#6b3f1d"/><path d="M-30,-74 Q-70,-190 -130,-210 Q-90,-150 -64,-72 Z" fill="#6b3f1d"/>'
             '<circle cx="-150" cy="-232" r="20" fill="#6b3f1d"/><circle cx="-196" cy="-216" r="12" fill="#6b3f1d"/><circle cx="-176" cy="-272" r="9" fill="#6b3f1d"/>')
    return _girado(c.get('x', 540), c.get('y', 950), c.get('rot', -14), c.get('escala', 1.0), g)


def banco(c, p, t, idi):
    x, y, e= c.get('x', 540), c.get('y', 1380), c.get('escala', 1.0)
    g= ('<rect x="-260" y="-190" width="520" height="44" rx="12" fill="#7a4b2a"/><rect x="-260" y="-290" width="520" height="34" rx="12" fill="#7a4b2a"/>'
        '<rect x="-260" y="-360" width="520" height="34" rx="12" fill="#7a4b2a"/><rect x="-230" y="-370" width="26" height="370" fill="#3a3a48"/>'
        '<rect x="204" y="-370" width="26" height="370" fill="#3a3a48"/>')
    return _girado(x, y, 0, e, g)


def muro(c, p, t, idi):
    """Pared de ladrillo con un mensaje en tiza que se va escribiendo segun 'v' (0..1). Lineas separadas por |."""
    x, y, an, al= c.get('x', 60), c.get('y', 560), c.get('ancho', 960), c.get('alto', 820)
    v= max(0.0, min(1.0, c.get('v', 1.0)))
    _uid[0]+= 1
    cid= f'mu{_uid[0]}'
    g= f'<rect x="{x}" y="{y}" width="{an}" height="{al}" fill="#5a2f2a"/>'
    for i in range(int(al // 62) + 1):
        yy= y + i * 62
        g+= f'<line x1="{x}" y1="{yy}" x2="{x + an}" y2="{yy}" stroke="#3d1f1c" stroke-width="6"/>'
        for j in range(int(an // 150) + 2):
            xx= x + j * 150 - (75 if i % 2 else 0)
            if x < xx < x + an:
                g+= f'<line x1="{xx}" y1="{yy}" x2="{xx}" y2="{min(yy + 62, y + al)}" stroke="#3d1f1c" stroke-width="6"/>'
    lineas= str(c.get('texto', '')).split('|')
    tam= c.get('tam', 84)
    g+= f'<defs><clipPath id="{cid}"><rect x="{x}" y="{y}" width="{an * v:.1f}" height="{al}"/></clipPath></defs><g clip-path="url(#{cid})">'
    for i, l in enumerate(lineas):
        yy= y + al / 2 - (len(lineas) - 1) * tam * 0.62 + i * tam * 1.25 + tam * 0.3
        g+= (f'<text x="{x + an / 2}" y="{yy:.1f}" text-anchor="middle" font-family="DejaVu Sans, sans-serif" font-weight="700" font-size="{tam}" fill="#f4f1e6" '
             f'opacity="0.93" transform="rotate(-2 {x + an / 2} {yy:.1f})">{l}</text>')
    g+= '</g>'
    if c.get('flecha'):
        fy= y + al - 110
        g+= f'<g opacity="{min(1.0, max(0.0, v * 3 - 2)):.2f}"><line x1="{x + an / 2 - 190}" y1="{fy}" x2="{x + an / 2 + 150}" y2="{fy}" stroke="#f4f1e6" stroke-width="16" stroke-linecap="round"/><polygon points="{x + an / 2 + 210},{fy} {x + an / 2 + 140},{fy - 40} {x + an / 2 + 140},{fy + 40}" fill="#f4f1e6"/></g>'
    return g


def polvo(c, p, t, idi):
    """Motas de tiza cayendo muy despacio."""
    r= random.Random(c.get('semilla', 8))
    g= ''
    for _ in range(int(c.get('n', 40))):
        x, y= c.get('x', 540) + r.uniform(-300, 300), c.get('y', 900) + r.uniform(0, 380)
        g+= f'<circle cx="{x + 6 * math.sin(t * 1.5 + y):.1f}" cy="{y + (t * 16) % 60:.1f}" r="{r.choice([3, 4, 5])}" fill="#f4f1e6" opacity="{r.uniform(0.3, 0.8):.2f}"/>'
    return g


def grieta(c, p, t, idi):
    """Grieta en zigzag que crece desde (x, y) segun 'v' (0..1)."""
    x, y, v= c.get('x', 540), c.get('y', 900), max(0.0, min(1.0, c.get('v', 1.0)))
    r= random.Random(c.get('semilla', 2))
    g= ''
    for ang in (-2.4, -0.7, 0.9, 2.3, -1.5):
        px, py, d= x, y, f'M{x},{y}'
        for i in range(int(1 + 5 * v)):
            px+= 48 * math.cos(ang) + r.uniform(-22, 22)
            py+= 48 * math.sin(ang) + r.uniform(-22, 22)
            d+= f' L{px:.1f},{py:.1f}'
        g+= f'<path d="{d}" fill="none" stroke="{col(c.get("color", "#dff3ff"))}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>'
    return g


def mesa(c, p, t, idi):
    x, y, an= c.get('x', 540), c.get('y', 1180), c.get('ancho', 700)
    return (f'<rect x="{x - an / 2}" y="{y}" width="{an}" height="40" rx="12" fill="#8a5a3c"/><rect x="{x - an / 2 + 40}" y="{y + 40}" width="34" height="{1380 - y - 40}" fill="#6b4226"/>'
            f'<rect x="{x + an / 2 - 74}" y="{y + 40}" width="34" height="{1380 - y - 40}" fill="#6b4226"/>')


PIEZAS.update({'ciudad': ciudad, 'lluvia': lluvia, 'taza': taza, 'banco': banco, 'muro': muro, 'polvo': polvo, 'grieta': grieta, 'mesa': mesa})


# ---------- piezas del formato "como funciona" (plano tecnico azul) ----------

def cuadricula(c, p, t, idi):
    """Fondo de plano tecnico: cuadricula fina."""
    paso, g= c.get('paso', 90), ''
    for x in range(0, W + 1, paso):
        g+= f'<line x1="{x}" y1="0" x2="{x}" y2="{H}" stroke="#ffffff" stroke-width="{4 if x % (paso * 4) == 0 else 2}" opacity="0.07"/>'
    for y in range(0, H + 1, paso):
        g+= f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="#ffffff" stroke-width="{4 if y % (paso * 4) == 0 else 2}" opacity="0.07"/>'
    return g


def vagon(c, p, t, idi):
    """Tren de perfil; (x, y) es el centro sobre la via. 'giro' son las vueltas por segundo de las ruedas."""
    x, y, e= c.get('x', 540), c.get('y', 1200), c.get('escala', 1.0)
    k= col(c.get('color', 'rojo'))
    a= t * 360 * c.get('giro', 1.0)
    g= (f'<rect x="-330" y="-250" width="660" height="200" rx="34" fill="{k}" stroke="#fff" stroke-width="8"/>'
        '<rect x="-330" y="-110" width="660" height="26" fill="#ffffff" opacity="0.85"/>'
        '<path d="M330,-250 Q420,-240 430,-150 L430,-50 L330,-50 Z" fill="#ffd60a" stroke="#fff" stroke-width="8"/>')
    for wx in (-250, -110, 30, 170):
        g+= f'<rect x="{wx}" y="-215" width="100" height="74" rx="10" fill="#bfe6ff" stroke="#fff" stroke-width="5"/>'
    for rx in (-220, -90, 90, 220):
        g+= (f'<g transform="translate({rx} -10) rotate({a:.1f})"><circle r="48" fill="#1b2340" stroke="#fff" stroke-width="7"/>'
             '<line x1="-40" y1="0" x2="40" y2="0" stroke="#fff" stroke-width="6"/><line x1="0" y1="-40" x2="0" y2="40" stroke="#fff" stroke-width="6"/></g>')
    g+= f'<rect x="-700" y="40" width="1400" height="14" fill="#cfd6e6"/>'
    return _girado(x, y, c.get('rot', 0), e, g)


def volante(c, p, t, idi):
    x, y, r= c.get('x', 540), c.get('y', 900), c.get('r', 130)
    a= 25 * math.sin(t * 2.2)
    g= f'<circle r="{r}" fill="none" stroke="#fff" stroke-width="{r * 0.2:.0f}"/><circle r="{r * 0.24:.0f}" fill="#fff"/>'
    for ang in (90, 210, 330):
        g+= f'<line x1="0" y1="0" x2="{r * math.cos(math.radians(ang)):.1f}" y2="{r * math.sin(math.radians(ang)):.1f}" stroke="#fff" stroke-width="{r * 0.16:.0f}"/>'
    return f'<g transform="translate({x} {y}) rotate({a:.1f})">{g}</g>'


def ejeruedas(c, p, t, idi):
    """Eje de tren visto de frente con sus dos ruedas conicas sobre los railes.
    des (-1..1) lo desplaza hacia un lado; plano=True dibuja ruedas rectas; marca resalta el radio de apoyo de cada rueda."""
    x, y, e= c.get('x', 540), c.get('y', 1000), c.get('escala', 1.0)
    des= max(-1.0, min(1.0, c.get('des', 0.0))) * 38
    plano= c.get('plano')
    R1, R2, an, sep= 150, (150 if plano else 100), 96, 250   # radio por dentro, por fuera, ancho de rueda, media via
    def radio(u):  # u: 0 en el borde interior de la rueda, 1 en el exterior
        return R1 + (R2 - R1) * max(0.0, min(1.0, u))
    # el rail queda a mitad de rueda cuando des=0
    ui, ud= 0.5 + des / an, 0.5 - des / an    # donde apoya cada rueda: al irse a la derecha, la derecha apoya mas cerca de la pestana (parte ancha)
    ri, rd= radio(ui), radio(ud)
    incl= -math.degrees(math.atan2(rd - ri, 2 * sep))
    ky= col(c.get('color', '#cfd6e6'))
    g= f'<rect x="{-sep - 70}" y="-16" width="{2 * sep + 140}" height="32" rx="12" fill="#8fa3c8"/>'
    for lado in (-1, 1):
        xi, xo= lado * (sep - an / 2), lado * (sep + an / 2)
        g+= (f'<polygon points="{xi},{-R1} {xo},{-R2} {xo},{R2} {xi},{R1}" fill="{ky}" stroke="#fff" stroke-width="7" stroke-linejoin="round"/>'
             f'<rect x="{min(xi, xi - lado * 18)}" y="{-R1 - 26}" width="18" height="{2 * R1 + 52}" rx="7" fill="#ffd60a"/>')
    cuerpo= f'<g transform="translate({des:.1f} {-(ri + rd) / 2:.1f}) rotate({incl:.2f})">{g}</g>'
    # railes fijos
    for lado in (-1, 1):
        cuerpo+= (f'<rect x="{lado * sep - 26}" y="0" width="52" height="34" rx="12" fill="#ff9f43"/><rect x="{lado * sep - 12}" y="30" width="24" height="90" fill="#ff9f43"/>'
                  f'<rect x="{lado * sep - 50}" y="116" width="100" height="22" rx="6" fill="#ff9f43"/>')
    if c.get('marca'):
        for lado, r, u in ((-1, ri, ui), (1, rd, ud)):
            k= col('rojo') if r >= (ri + rd) / 2 + 1 else (col('turquesa') if r <= (ri + rd) / 2 - 1 else '#fff')
            cuerpo+= (f'<line x1="{lado * sep}" y1="-6" x2="{lado * sep}" y2="{-2 * r:.1f}" stroke="{k}" stroke-width="9" stroke-dasharray="16 10"/>'
                      + _txt(lado * sep, -2 * r - 40, ('BIG' if r > (ri + rd) / 2 + 1 else 'SMALL') if abs(ri - rd) > 2 else 'SAME', 46, k))
    return _girado(x, y, 0, e, cuerpo)


def curvavia(c, p, t, idi):
    """Curva de via vista desde arriba: rail exterior e interior, y un punto que avanza por cada uno segun v (0..1)."""
    x, y= c.get('x', 240), c.get('y', 1340)      # centro de la curva
    v= max(0.0, min(1.0, c.get('v', 1.0)))
    g= ''
    for r, k, nombre in ((720, 'rojo', c.get('fuera', 'OUTER')), (560, 'turquesa', c.get('dentro', 'INNER'))):
        a1= math.radians(-88)
        a2= math.radians(-88 + 86 * v)
        x1, y1= x + r * math.cos(a1), y + r * math.sin(a1)
        x2, y2= x + r * math.cos(a2), y + r * math.sin(a2)
        xf, yf= x + r * math.cos(math.radians(-2)), y + r * math.sin(math.radians(-2))
        g+= (f'<path d="M{x1:.1f},{y1:.1f} A{r},{r} 0 0 1 {xf:.1f},{yf:.1f}" fill="none" stroke="#ffffff" stroke-width="10" opacity="0.25"/>'
             f'<path d="M{x1:.1f},{y1:.1f} A{r},{r} 0 0 1 {x2:.1f},{y2:.1f}" fill="none" stroke="{col(k)}" stroke-width="16" stroke-linecap="round"/>'
             f'<circle cx="{x2:.1f}" cy="{y2:.1f}" r="22" fill="{col(k)}" stroke="#fff" stroke-width="6"/>')
        if c.get('rotulos', True):
            g+= _txt(x + (r + (70 if r > 600 else -80)) * math.cos(math.radians(-45)), y + (r + (70 if r > 600 else -80)) * math.sin(math.radians(-45)), nombre, 44, k, borde='#0a1230')
    return g


def ruedadist(c, p, t, idi):
    """Rueda de radio r que rueda una vuelta y deja marcada la distancia recorrida (para comparar grande y pequena)."""
    x, y, r= c.get('x', 160), c.get('y', 900), c.get('r', 100)
    v= max(0.0, min(1.0, c.get('v', 1.0)))
    k= col(c.get('color', 'rojo'))
    d= 2 * math.pi * r * v * c.get('k', 0.55)
    return (f'<line x1="{x}" y1="{y + r + 10}" x2="{x + d:.1f}" y2="{y + r + 10}" stroke="{k}" stroke-width="16" stroke-linecap="round"/>'
            f'<g transform="translate({x + d:.1f} {y}) rotate({360 * v:.1f})"><circle r="{r}" fill="#0e3f73" stroke="{k}" stroke-width="12"/>'
            f'<line x1="0" y1="0" x2="0" y2="{-r}" stroke="{k}" stroke-width="10"/></g>')


PIEZAS.update({'cuadricula': cuadricula, 'vagon': vagon, 'volante': volante, 'ejeruedas': ejeruedas, 'curvavia': curvavia, 'ruedadist': ruedadist})


# ---------- piezas del formato "como funciona", estilo mundo (atardecer, contorno grueso, capas con profundidad) ----------

TINTA= '#1d2440'
CREMA= '#fdf6ec'


def _lomas(base, amp, off, color, k1=0.006, k2=0.017):
    pts= [f'{x},{base - amp * (math.sin(k1 * (x + off)) + 0.5 * math.sin(k2 * (x + off) + 1.3)):.1f}' for x in range(-600, W + 601, 40)]
    return f'<polygon points="-600,{H + 600} ' + ' '.join(pts) + f' {W + 600},{H + 600}" fill="{color}"/>'


def _nubecita(x, y, e, color, op):
    return (f'<g transform="translate({x:.1f} {y:.1f}) scale({e:.2f})" fill="{color}" opacity="{op}"><rect x="-150" y="-30" width="300" height="60" rx="30"/>'
            '<circle cx="-60" cy="-36" r="52"/><circle cx="30" cy="-58" r="70"/><circle cx="100" cy="-26" r="44"/></g>')


def paisaje(c, p, t, idi):
    """Fondo completo: cielo en degradado, sol, nubes y lomas con paralaje. 'hor' es la altura del horizonte
    (mayor que 1920 = volando alto, sin suelo); 'vel' son px/s de avance hacia la izquierda."""
    tipo, hor, vel= c.get('tipo', 'tarde'), c.get('hor', 1500), c.get('vel', 0)
    a, m, b= {'tarde': ('#34459f', '#f08a7e', '#ffd9a0'), 'alto': ('#16226a', '#4f7fe0', '#bfe0ff'),
              'noche': ('#0b1033', '#2a2f7a', '#7a5fa8')}.get(tipo, ('#34459f', '#f08a7e', '#ffd9a0'))
    _uid[0]+= 1
    i= f'gp{_uid[0]}'
    s= (f'<defs><linearGradient id="{i}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{a}"/><stop offset="0.6" stop-color="{m}"/>'
        f'<stop offset="1" stop-color="{b}"/></linearGradient></defs><rect x="-400" y="-400" width="{W + 800}" height="{H + 800}" fill="url(#{i})"/>')
    sx, sy= c.get('solx', 800), c.get('soly', 1180)
    if c.get('sol', True):
        for r, o in ((260, 0.10), (190, 0.16), (130, 1.0)):
            s+= f'<circle cx="{sx}" cy="{sy}" r="{r + (6 * math.sin(t * 1.5) if o < 1 else 0):.1f}" fill="#fff1c4" opacity="{o}"/>'
    kn= '#ffd3c4' if tipo == 'tarde' else '#ffffff'
    for j, (nx, ny, ne, nv) in enumerate(((150, 720, 1.1, 0.10), (760, 560, 0.8, 0.07), (480, 980, 1.4, 0.14), (980, 860, 0.9, 0.09))):
        x= (nx - t * (vel * nv + 6 + j)) % (W + 500) - 250
        s+= _nubecita(x, ny + c.get('nubesy', 0), ne, kn, 0.55 if j % 2 else 0.8)
    if hor < H + 100:
        tonos= ('#8a68b0', '#5a4f99', '#2f3a72') if tipo != 'alto' else ('#7fa6ea', '#5b84d6', '#3a5fb4')
        s+= _lomas(hor - 150, 70, t * vel * 0.12, tonos[0], 0.004, 0.011)
        s+= _lomas(hor - 60, 55, 300 + t * vel * 0.3, tonos[1], 0.007, 0.019)
        s+= _lomas(hor + 40, 40, 700 + t * vel * 0.65, tonos[2], 0.009, 0.023)
    return s


def jet(c, p, t, idi):
    """Avion de pasajeros de perfil, mirando a la derecha. 'winglet' 0..1 levanta la punta del ala; 'luz' la resalta."""
    x, y, e= c.get('x', 540), c.get('y', 900), c.get('escala', 1.0)
    k, wl= col(c.get('color', '#ff5a5f')), c.get('winglet', 1.0)
    y+= 10 * math.sin(t * 1.6)
    g= (f'<polygon points="-300,-40 -372,-200 -296,-200 -196,-44" fill="{k}" stroke="{TINTA}" stroke-width="8" stroke-linejoin="round"/>'
        f'<polygon points="-345,-18 -250,-22 -300,-64 -372,-62" fill="#d9cdbf" stroke="{TINTA}" stroke-width="7" stroke-linejoin="round"/>'
        f'<path d="M-345,-18 Q-345,-60 -262,-62 L220,-62 Q332,-56 364,0 Q330,46 220,50 L-224,50 Q-322,40 -345,-18 Z" fill="{CREMA}" stroke="{TINTA}" stroke-width="8" stroke-linejoin="round"/>'
        '<path d="M-318,22 L338,22 Q300,46 220,46 L-224,46 Q-290,42 -318,22 Z" fill="#e6d8c6"/>'
        f'<rect x="-322" y="2" width="640" height="12" rx="6" fill="{k}"/>'
        f'<path d="M262,-44 L312,-30 L330,-10 L256,-10 Z" fill="{TINTA}"/>')
    for wx in range(-230, 221, 50):
        g+= f'<rect x="{wx}" y="-42" width="26" height="30" rx="10" fill="{TINTA}"/>'
    g+= (f'<rect x="-10" y="52" width="130" height="52" rx="24" fill="#b9c0d9" stroke="{TINTA}" stroke-width="7"/>'
         f'<ellipse cx="116" cy="78" rx="12" ry="22" fill="{TINTA}"/>'
         f'<polygon points="-50,14 116,14 -70,140 -170,140" fill="#efe4d4" stroke="{TINTA}" stroke-width="8" stroke-linejoin="round"/>')
    if wl > 0.02:
        h= 110 * wl
        luz= c.get('luz', 0)
        if luz:
            g+= f'<circle cx="-140" cy="{140 - h * 0.5:.1f}" r="{100 + 14 * math.sin(t * 6):.1f}" fill="#ffd60a" opacity="{0.35 * luz:.2f}"/>'
        g+= f'<polygon points="-170,140 -84,140 {-150 - 14 * wl:.1f},{140 - h:.1f} {-196 - 14 * wl:.1f},{140 - h:.1f}" fill="{k}" stroke="{TINTA}" stroke-width="8" stroke-linejoin="round"/>'
    return _girado(x, y, c.get('rot', -3) + 1.2 * math.sin(t * 1.1), e, g)


def _espiral(r, giro, color, op, ancho=9):
    s= ''
    for brazo in (0, 180):
        pts= []
        for i in range(0, 40):
            a= math.radians(giro + brazo + i * 17)
            rr= r * (i / 39) ** 0.8
            pts.append(f'{rr * math.cos(a):.1f},{rr * math.sin(a):.1f}')
        s+= f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="{ancho}" stroke-linecap="round" opacity="{op:.2f}"/>'
    return s


def jetatras(c, p, t, idi):
    """Avion visto desde atras. 'presion' muestra alta presion debajo y baja encima; 'flujo' el aire que rodea la punta;
    'vortice' el torbellino de cada punta (0..1 de tamano); 'winglet' levanta la punta (0..1)."""
    x, y, e= c.get('x', 540), c.get('y', 1050), c.get('escala', 1.0)
    k, L= col(c.get('color', '#ff5a5f')), 400
    pr, fl, vo, wl= c.get('presion', 0), c.get('flujo', 0), c.get('vortice', 0), c.get('winglet', 0)
    y+= 8 * math.sin(t * 1.4)
    g= f'<polygon points="-190,-34 190,-34 176,-18 -176,-18" fill="#d9cdbf" stroke="{TINTA}" stroke-width="7" stroke-linejoin="round"/>'
    g+= f'<polygon points="-12,-60 12,-60 7,-230 -7,-230" fill="{k}" stroke="{TINTA}" stroke-width="8" stroke-linejoin="round"/>'
    lado= ''
    lado+= f'<polygon points="50,-10 {L},-40 {L},-24 50,26" fill="{CREMA}" stroke="{TINTA}" stroke-width="8" stroke-linejoin="round"/>'
    lado+= (f'<rect x="196" y="6" width="12" height="26" fill="{TINTA}"/><circle cx="202" cy="58" r="46" fill="#b9c0d9" stroke="{TINTA}" stroke-width="8"/>'
            f'<circle cx="202" cy="58" r="28" fill="{TINTA}"/>')
    for a in (0, 60, 120):
        ang= math.radians(a + t * 500)
        lado+= f'<line x1="{202 - 26 * math.cos(ang):.1f}" y1="{58 - 26 * math.sin(ang):.1f}" x2="{202 + 26 * math.cos(ang):.1f}" y2="{58 + 26 * math.sin(ang):.1f}" stroke="#7f88ad" stroke-width="5"/>'
    if pr > 0.02:
        for i in range(6):
            px= 90 + i * 56
            sube= (t * 60 + i * 23) % 60
            lado+= (f'<g opacity="{pr * (1 - sube / 60):.2f}"><line x1="{px}" y1="{120 - sube:.1f}" x2="{px}" y2="{80 - sube:.1f}" stroke="#ff5a5f" stroke-width="9" stroke-linecap="round"/>'
                    f'<polygon points="{px - 13},{84 - sube:.1f} {px + 13},{84 - sube:.1f} {px},{62 - sube:.1f}" fill="#ff5a5f"/></g>')
        for i in range(4):
            px= 110 + i * 80
            lado+= f'<circle cx="{px}" cy="{-90 - 10 * math.sin(t * 2 + i):.1f}" r="9" fill="#9fe3ff" opacity="{0.8 * pr:.2f}"/>'
    if wl > 0.02:
        lado+= f'<polygon points="{L - 16},-40 {L + 2},-24 {L + 26 * wl:.1f},{-32 - 150 * wl:.1f} {L + 8 * wl:.1f},{-36 - 150 * wl:.1f}" fill="{k}" stroke="{TINTA}" stroke-width="8" stroke-linejoin="round"/>'
    if fl > 0.02:
        # el aire de abajo rodea la punta por fuera y sube
        n= max(2, int(26 * fl))
        pts= []
        for i in range(n + 1):
            a= math.radians(100 - 200 * (i / 26))
            pts.append((L + 4 + 78 * math.cos(a), -32 + 78 * math.sin(a)))
        lado+= f'<polyline points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in pts)}" fill="none" stroke="#ffd60a" stroke-width="13" stroke-linecap="round" stroke-linejoin="round"/>'
        (x1, y1), (x2, y2)= pts[-2], pts[-1]
        d= math.atan2(y2 - y1, x2 - x1)
        lado+= (f'<polygon points="{x2 + 30 * math.cos(d):.1f},{y2 + 30 * math.sin(d):.1f} {x2 + 22 * math.cos(d + 2.2):.1f},{y2 + 22 * math.sin(d + 2.2):.1f} '
                f'{x2 + 22 * math.cos(d - 2.2):.1f},{y2 + 22 * math.sin(d - 2.2):.1f}" fill="#ffd60a"/>')
    if vo > 0.02:
        lado+= f'<g transform="translate({L + 20 + 20 * wl:.1f} {-36 - 60 * wl:.1f})">' + _espiral(130 * vo, -t * 420, '#ffffff', 0.9, 10) + _espiral(90 * vo, -t * 420 + 90, '#9fe3ff', 0.7, 7) + '</g>'
    g+= lado + f'<g transform="scale(-1 1)">{lado}</g>'
    g+= f'<circle r="74" fill="{CREMA}" stroke="{TINTA}" stroke-width="8"/><path d="M-66,30 Q0,84 66,30 Q40,70 0,72 Q-40,70 -66,30 Z" fill="#e6d8c6"/>'
    return _girado(x, y, 1.5 * math.sin(t * 1.2), e, g)


def jetarriba(c, p, t, idi):
    """Avion visto desde arriba, morro hacia arriba, con las estelas en espiral de las puntas.
    'estela' 0..1 es el largo, 'fuerza' 0..1 el grosor del torbellino, 'winglet' 0..1 pinta las puntas."""
    x, y, e= c.get('x', 540), c.get('y', 800), c.get('escala', 1.0)
    k, es, fu, wl= col(c.get('color', '#ff5a5f')), c.get('estela', 0), c.get('fuerza', 1.0), c.get('winglet', 0)
    x+= 10 * math.sin(t * 1.3)
    g= ''
    if es > 0.02:
        largo= 900 * es
        for sx in (-330, 330):
            for fase, kk, an in ((0, '#ffffff', 11), (math.pi, '#9fe3ff', 8)):
                pts= []
                for i in range(0, int(largo), 14):
                    amp= (16 + 70 * fu) * min(1.0, i / 160 + 0.25)
                    pts.append(f'{sx + amp * math.sin(i * 0.035 - t * 9 + fase):.1f},{70 + i}')
                if len(pts) > 1:
                    g+= f'<polyline points="{" ".join(pts)}" fill="none" stroke="{kk}" stroke-width="{an * (0.5 + 0.5 * fu):.1f}" stroke-linecap="round" stroke-linejoin="round" opacity="{0.35 + 0.5 * fu:.2f}"/>'
    g+= (f'<polygon points="-40,-20 -330,90 -330,130 -40,90" fill="#efe4d4" stroke="{TINTA}" stroke-width="8" stroke-linejoin="round"/>'
         f'<polygon points="40,-20 330,90 330,130 40,90" fill="#efe4d4" stroke="{TINTA}" stroke-width="8" stroke-linejoin="round"/>'
         f'<polygon points="-30,250 -130,310 -130,336 -30,316" fill="#d9cdbf" stroke="{TINTA}" stroke-width="7" stroke-linejoin="round"/>'
         f'<polygon points="30,250 130,310 130,336 30,316" fill="#d9cdbf" stroke="{TINTA}" stroke-width="7" stroke-linejoin="round"/>')
    for sx in (-170, 170):
        g+= f'<rect x="{sx - 24}" y="-10" width="48" height="96" rx="22" fill="#b9c0d9" stroke="{TINTA}" stroke-width="7"/>'
    g+= (f'<path d="M0,-330 Q52,-270 52,-170 L52,260 Q40,340 0,352 Q-40,340 -52,260 L-52,-170 Q-52,-270 0,-330 Z" fill="{CREMA}" stroke="{TINTA}" stroke-width="8" stroke-linejoin="round"/>'
         f'<path d="M-30,-262 Q0,-296 30,-262 L24,-238 L-24,-238 Z" fill="{TINTA}"/><rect x="-7" y="-200" width="14" height="500" rx="7" fill="{k}"/>')
    if wl > 0.02:
        for s_ in (-1, 1):
            g+= f'<rect x="{s_ * 330 - 11:.0f}" y="{84 - 10 * wl:.0f}" width="22" height="{52 + 10 * wl:.0f}" rx="8" fill="{k}" stroke="{TINTA}" stroke-width="6" opacity="{wl:.2f}"/>'
    return _girado(x, y, 1.2 * math.sin(t * 1.0), e, g)


def nubesabajo(c, p, t, idi):
    """Nubes que pasan hacia abajo (vista desde arriba): dan sensacion de vuelo."""
    vel, s= c.get('vel', 500), ''
    for j, (nx, ne, o) in enumerate(((120, 1.3, 0.5), (860, 1.0, 0.4), (420, 1.7, 0.35), (700, 0.8, 0.5), (60, 0.9, 0.4))):
        y= (j * 470 + t * vel * (0.7 + 0.12 * j)) % (H + 500) - 250
        s+= _nubecita(nx, y, ne, '#ffffff', o)
    return s


def aguila(c, p, t, idi):
    """Aguila planeando vista de frente: las plumas de la punta del ala se abren y suben. 'luz' resalta las puntas."""
    x, y, e= c.get('x', 540), c.get('y', 1000), c.get('escala', 1.0)
    al= 14 * math.sin(t * 2.2)
    k, k2= '#5a3b2e', '#3d2820'
    lado= f'<path d="M30,0 Q180,{-70 - al:.1f} 330,{-40 - al * 1.6:.1f} Q200,{20 - al:.1f} 30,40 Z" fill="{k}" stroke="{TINTA}" stroke-width="8" stroke-linejoin="round"/>'
    if c.get('luz', 0):
        lado+= f'<circle cx="380" cy="{-110 - al * 2:.1f}" r="{110 + 12 * math.sin(t * 6):.1f}" fill="#ffd60a" opacity="{0.35 * c["luz"]:.2f}"/>'
    for i in range(5):
        a= math.radians(-8 - i * 17)
        x0, y0= 300 + i * 6, -38 - al * 1.6 + i * 6
        lado+= (f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x0 + 118 * math.cos(a):.1f}" y2="{y0 + 118 * math.sin(a) - al:.1f}" stroke="{TINTA}" stroke-width="30" stroke-linecap="round"/>'
                f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x0 + 118 * math.cos(a):.1f}" y2="{y0 + 118 * math.sin(a) - al:.1f}" stroke="{k2}" stroke-width="17" stroke-linecap="round"/>')
    g= lado + f'<g transform="scale(-1 1)">{lado}</g>'
    g+= (f'<ellipse cx="0" cy="24" rx="52" ry="70" fill="{k}" stroke="{TINTA}" stroke-width="8"/><circle cx="0" cy="-34" r="42" fill="#fff" stroke="{TINTA}" stroke-width="8"/>'
         f'<circle cx="-15" cy="-40" r="6" fill="{TINTA}"/><circle cx="15" cy="-40" r="6" fill="{TINTA}"/><polygon points="-11,-26 11,-26 0,-4" fill="#ffb020" stroke="{TINTA}" stroke-width="5" stroke-linejoin="round"/>')
    return _girado(x, y + 14 * math.sin(t * 1.1), 0, e, g)


def medidor(c, p, t, idi):
    """Deposito de combustible: barra con nivel 'v' (0..1) y rotulo."""
    x, y, an, v= c.get('x', 540), c.get('y', 1380), c.get('ancho', 620), max(0.0, min(1.0, c.get('v', 1.0)))
    k= '#35e0c2' if v > 0.5 else ('#ffd60a' if v > 0.25 else '#ff5a5f')
    s= (f'<rect x="{x - an / 2 - 16}" y="{y - 52}" width="{an + 32}" height="104" rx="34" fill="{TINTA}"/>'
        f'<rect x="{x - an / 2}" y="{y - 36}" width="{an}" height="72" rx="24" fill="#0c1228"/>'
        f'<rect x="{x - an / 2}" y="{y - 36}" width="{max(48, an * v):.1f}" height="72" rx="24" fill="{k}"/>')
    return s + _txt(x, y + 17, c.get('texto', 'FUEL'), 46, 'blanco', borde=TINTA)


PIEZAS.update({'paisaje': paisaje, 'jet': jet, 'jetatras': jetatras, 'jetarriba': jetarriba, 'nubesabajo': nubesabajo, 'aguila': aguila, 'medidor': medidor})


def _rueda(x, y, r, a):
    g= f'<g transform="translate({x:.1f} {y:.1f}) rotate({a:.1f})"><circle r="{r}" fill="#2a2f45" stroke="{TINTA}" stroke-width="8"/><circle r="{r * 0.52:.1f}" fill="{CREMA}" stroke="{TINTA}" stroke-width="6"/>'
    for i in range(5):
        an= math.radians(i * 72)
        g+= f'<circle cx="{r * 0.3 * math.cos(an):.1f}" cy="{r * 0.3 * math.sin(an):.1f}" r="{r * 0.08:.1f}" fill="{TINTA}"/>'
    return g + '</g>'


def camion(c, p, t, idi):
    """Camion plataforma de perfil, mirando a la derecha; (x, y) es el suelo bajo el centro.
    'carga' 0..1 apila cajas; 'eje' 1 = eje extra apoyado, 0 = levantado; 'giro' vueltas/s; 'luz' resalta el eje elevable."""
    x, y, e= c.get('x', 540), c.get('y', 1300), c.get('escala', 1.0)
    k, ca, ej, luz= col(c.get('color', '#2bb8a4')), max(0.0, min(1.0, c.get('carga', 0))), max(0.0, min(1.0, c.get('eje', 1))), c.get('luz', 0)
    a, R= t * 360 * c.get('giro', 0), 74
    hund= 10 * ca + 3 * math.sin(t * 9) * (1 if c.get('giro', 0) else 0)
    g= ''
    sub= 54 * (1 - ej)
    if luz:
        g+= f'<circle cx="-285" cy="{-R - sub:.1f}" r="{118 + 12 * math.sin(t * 6):.1f}" fill="#ffd60a" opacity="{0.4 * luz:.2f}"/>'
    g+= _rueda(-285, -R - sub, R, a if ej > 0.95 else 0) + _rueda(-135, -R, R, a) + _rueda(300, -R, R, a)
    cu= f'<rect x="-400" y="-150" width="620" height="30" rx="8" fill="#4a5173" stroke="{TINTA}" stroke-width="7"/>'
    cu+= f'<rect x="-410" y="-190" width="610" height="44" rx="8" fill="#c98f4a" stroke="{TINTA}" stroke-width="8"/>'
    cajas= [(-395, 0), (-275, 0), (-155, 0), (-35, 0), (-335, 1), (-215, 1), (-95, 1), (-275, 2)]
    n= ca * len(cajas)
    for i, (bx, fila) in enumerate(cajas):
        q= max(0.0, min(1.0, n - i))
        if q <= 0:
            continue
        by= -190 - 112 * (fila + 1) - 500 * (1 - suave(q)) ** 2
        kc= ('#ffb347', '#ff8f5a', '#ffd27a')[i % 3]
        cu+= (f'<rect x="{bx}" y="{by:.1f}" width="112" height="108" rx="10" fill="{kc}" stroke="{TINTA}" stroke-width="7"/>'
              f'<line x1="{bx + 12}" y1="{by + 54:.1f}" x2="{bx + 100}" y2="{by + 54:.1f}" stroke="{TINTA}" stroke-width="5" opacity="0.5"/>')
    cu+= (f'<path d="M214,-146 L214,-380 Q214,-400 236,-400 L330,-400 Q360,-398 374,-366 L412,-270 Q420,-250 420,-230 L420,-146 Z" fill="{k}" stroke="{TINTA}" stroke-width="8" stroke-linejoin="round"/>'
          f'<path d="M286,-368 L336,-368 Q350,-366 356,-352 L386,-272 L286,-272 Z" fill="#bfe6ff" stroke="{TINTA}" stroke-width="7" stroke-linejoin="round"/>'
          f'<rect x="232" y="-250" width="34" height="12" rx="6" fill="{TINTA}"/><rect x="398" y="-190" width="30" height="24" rx="8" fill="#ffd60a" stroke="{TINTA}" stroke-width="5"/>'
          f'<rect x="196" y="-420" width="20" height="150" rx="8" fill="#9aa3c4" stroke="{TINTA}" stroke-width="6"/>')
    g+= f'<g transform="translate(0 {hund:.1f})">{cu}</g>'
    return _girado(x, y, 0, e, g)


def calzada(c, p, t, idi):
    """Carretera con arcen y tierra debajo. 'vel' mueve las rayas; 'grieta' 0..1 agrieta el asfalto bajo 'gx'."""
    y, vel, gr, gx= c.get('y', 1300), c.get('vel', 0), c.get('grieta', 0), c.get('gx', 400)
    s= (f'<rect x="-600" y="{y}" width="{W + 1200}" height="900" fill="#3b2f4f"/><rect x="-600" y="{y - 6}" width="{W + 1200}" height="110" fill="#4a4f6a" stroke="{TINTA}" stroke-width="8"/>'
        f'<rect x="-600" y="{y + 150}" width="{W + 1200}" height="46" fill="#4a3b63"/><rect x="-600" y="{y + 290}" width="{W + 1200}" height="70" fill="#2f2540"/>')
    for i in range(-4, 12):
        s+= f'<rect x="{i * 220 - (t * vel) % 220:.1f}" y="{y + 44}" width="110" height="14" rx="7" fill="#ffe9a8"/>'
    if c.get('bache') is not None:
        bx, br= c['bache'], c.get('bancho', 120)
        s+= f'<path d="M{bx - br:.1f},{y - 4} Q{bx:.1f},{y - 4 - br * 0.75:.1f} {bx + br:.1f},{y - 4} Z" fill="#ffd60a" stroke="{TINTA}" stroke-width="8" stroke-linejoin="round"/>'
    if gr > 0.02:
        rr= random.Random(5)
        for j in range(7):
            x0, y0= gx + rr.uniform(-190, 190), y + 2
            pts= [(x0, y0)]
            for _ in range(5):
                x0+= rr.uniform(-34, 34)
                y0+= rr.uniform(14, 24)
                pts.append((x0, y0))
            n= max(2, int(len(pts) * min(1.0, gr * 1.4 - j * 0.05) + 0.99)) if gr * 1.4 - j * 0.05 > 0 else 0
            if n:
                s+= f'<polyline points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in pts[:n])}" fill="none" stroke="{TINTA}" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>'
    return s


def empuje(c, p, t, idi):
    """Flecha gorda que aprieta hacia abajo (peso sobre un eje). 'fuerza' 0..1 cambia tamano y color."""
    x, y, f= c.get('x', 540), c.get('y', 1100), max(0.05, c.get('fuerza', 1.0))
    k= '#ff5a5f' if f > 0.75 else ('#ffd60a' if f > 0.5 else '#35e0c2')
    al, an= 60 + 120 * f, 22 + 30 * f
    d= 10 * math.sin(t * 7) * f
    return (f'<g transform="translate({x:.1f} {y + d:.1f})"><polygon points="{-an / 2:.1f},{-al:.1f} {an / 2:.1f},{-al:.1f} {an / 2:.1f},{-an:.1f} {an:.1f},{-an:.1f} 0,0 {-an:.1f},{-an:.1f} {-an / 2:.1f},{-an:.1f}" '
            f'fill="{k}" stroke="{TINTA}" stroke-width="7" stroke-linejoin="round"/></g>')


PIEZAS.update({'camion': camion, 'calzada': calzada, 'empuje': empuje})



def _salto(d, ancho, alto):
    """Cuanto sube una rueda que esta a distancia d del centro del bache."""
    return -alto * max(0.0, 1 - (d / ancho) ** 2)


def _rebote(d, modo, amp, paso):
    """Movimiento de la carroceria una vez pasado el bache (d > 0), segun el tipo de suspension."""
    if d <= 0 or modo == 'rigido':
        return 0.0
    if modo == 'muelle':
        return -amp * math.sin(d / paso)
    return -amp * 0.8 * math.exp(-d / (paso * 1.6)) * math.sin(d / paso)


def turismo(c, p, t, idi):
    """Coche de perfil mirando a la derecha; (x, y) es el suelo. 'bache' es la x del bache en la carretera y
    'modo' la suspension: 'rigido' (el golpe llega entero), 'muelle' (rebota sin parar) o 'bien' (un movimiento y listo)."""
    x, y, e= c.get('x', 540), c.get('y', 1300), c.get('escala', 1.0)
    k, modo, bx= col(c.get('color', '#ffc93c')), c.get('modo', 'bien'), c.get('bache')
    R, a= 70, t * 360 * c.get('giro', 0)
    l1= l2= sube= cab= 0.0
    if bx is not None:
        d1, d2= (x + 190 * e - bx) / e, (x - 190 * e - bx) / e
        l1, l2= _salto(d1, 150, 44), _salto(d2, 150, 44)
        if modo == 'rigido':
            sube= (l1 + l2) / 2 * 1.6
            cab= sube * 1.4
        else:
            sube= (l1 + l2) * 0.12 + _rebote(d1, modo, 62, 70)
            cab= sube * 0.5
    cabeceo= (l2 - l1) * (0.12 if modo == 'rigido' else 0.03)
    g= _rueda(-190, -R + l2, R, a) + _rueda(190, -R + l1, R, a)
    cu= (f'<path d="M-330,-90 L-330,-170 Q-320,-200 -270,-205 L-190,-215 L-110,-310 Q-95,-330 -60,-330 L110,-330 Q150,-328 175,-300 L250,-215 L310,-200 '
         f'Q340,-190 340,-150 L340,-90 Q340,-70 320,-70 L-310,-70 Q-330,-70 -330,-90 Z" fill="{k}" stroke="{TINTA}" stroke-width="8" stroke-linejoin="round"/>'
         f'<path d="M-95,-305 L-165,-222 L20,-222 L20,-305 Z" fill="#bfe6ff" stroke="{TINTA}" stroke-width="7" stroke-linejoin="round"/>'
         f'<path d="M48,-305 L48,-222 L212,-222 L152,-296 Q142,-305 122,-305 Z" fill="#bfe6ff" stroke="{TINTA}" stroke-width="7" stroke-linejoin="round"/>'
         f'<circle cx="112" cy="{-262 + cab:.1f}" r="30" fill="#ffe0bd" stroke="{TINTA}" stroke-width="6"/><circle cx="124" cy="{-266 + cab:.1f}" r="5" fill="{TINTA}"/>'
         f'<rect x="-320" y="-150" width="640" height="14" rx="7" fill="{TINTA}" opacity="0.18"/><rect x="316" y="-180" width="26" height="30" rx="10" fill="#fff1c4" stroke="{TINTA}" stroke-width="5"/>'
         f'<rect x="-336" y="-176" width="20" height="30" rx="8" fill="#ff5a5f" stroke="{TINTA}" stroke-width="5"/><rect x="30" y="-196" width="40" height="10" rx="5" fill="{TINTA}"/>')
    for wx in (-190, 190):
        cu+= f'<path d="M{wx - 96},-70 A96,96 0 0 1 {wx + 96},-70 Z" fill="{TINTA}"/>'
    g= f'<g transform="translate(0 {sube:.1f}) rotate({cabeceo:.2f})">{cu}</g>' + g
    return _girado(x, y, 0, e, g)


def suspension(c, p, t, idi):
    """Detalle de una rueda con su suspension; (x, y) es el suelo bajo la rueda. 'muelle' 0/1 (sin el, barra rigida),
    'amort' 0/1 dibuja el amortiguador, 'calor' 0..1 lo pone al rojo. Reacciona al 'bache' igual que el coche ('modo')."""
    x, y= c.get('x', 540), c.get('y', 1330)
    k, modo, bx= col(c.get('color', '#ffc93c')), c.get('modo', 'bien'), c.get('bache')
    mu, am, cal= c.get('muelle', 1), c.get('amort', 0), c.get('calor', 0)
    R= 150
    lift= chas= 0.0
    if bx is not None:
        d= x - bx
        lift= _salto(d, 260, 80)
        chas= lift if modo == 'rigido' else lift * 0.12 + _rebote(d, modo, 80, 95)
    wy, cy= y - R + lift, y - 520 + chas
    g= ''
    if mu < 0.5:
        g+= f'<rect x="{x - 26}" y="{cy:.1f}" width="52" height="{wy - cy:.1f}" fill="#9aa3c4" stroke="{TINTA}" stroke-width="8"/>'
    else:
        n, an_= 8, 78
        pts= [(x, cy)]
        largo= (wy - 60) - cy
        for i in range(n * 2):
            pts.append((x + (an_ if i % 2 == 0 else -an_), cy + largo * (i + 0.5) / (n * 2)))
        pts.append((x, wy - 60))
        ps= ' '.join(f'{a:.1f},{b:.1f}' for a, b in pts)
        g+= (f'<polyline points="{ps}" fill="none" stroke="{TINTA}" stroke-width="34" stroke-linejoin="round" stroke-linecap="round"/>'
             f'<polyline points="{ps}" fill="none" stroke="#c9d2f0" stroke-width="18" stroke-linejoin="round" stroke-linecap="round"/>')
    if am > 0.02:
        ax= x - 190
        if cal > 0.02:
            g+= f'<circle cx="{ax}" cy="{cy + 150:.1f}" r="{150 + 14 * math.sin(t * 7):.1f}" fill="#ff5a5f" opacity="{0.4 * cal:.2f}"/>'
        g+= (f'<rect x="{ax - 11}" y="{cy + 100:.1f}" width="22" height="{wy - cy - 130:.1f}" fill="#e6e9f5" stroke="{TINTA}" stroke-width="6"/>'
             f'<rect x="{ax - 40}" y="{cy:.1f}" width="80" height="190" rx="16" fill="{"#ff7a59" if cal > 0.5 else "#35b8d6"}" stroke="{TINTA}" stroke-width="8"/>'
             f'<line x1="{ax}" y1="{wy - 30:.1f}" x2="{x}" y2="{wy:.1f}" stroke="{TINTA}" stroke-width="22" stroke-linecap="round"/>')
    g+= _rueda(x, wy, R, t * 360 * c.get('giro', 0))
    g+= (f'<path d="M{x - 420},{cy + 10:.1f} L{x - 420},{cy - 150:.1f} Q{x - 420},{cy - 190:.1f} {x - 380},{cy - 190:.1f} L{x + 380},{cy - 190:.1f} Q{x + 420},{cy - 190:.1f} {x + 420},{cy - 150:.1f} L{x + 420},{cy + 10:.1f} '
         f'L{x + 250},{cy + 10:.1f} A250,250 0 0 0 {x - 250},{cy + 10:.1f} Z" fill="{k}" stroke="{TINTA}" stroke-width="8" stroke-linejoin="round"/>')
    return g


def amortiguador(c, p, t, idi):
    """Amortiguador abierto por dentro: tubo con aceite y piston con agujeritos. 'v' -1..1 es la posicion del piston,
    'calor' 0..1 lo pone al rojo, 'chorros' 0..1 muestra el aceite pasando por los agujeros."""
    x, y, v= c.get('x', 540), c.get('y', 1050), max(-1.0, min(1.0, c.get('v', 0)))
    cal, ch= c.get('calor', 0), c.get('chorros', 1)
    an_, al= 300, 640
    py= y + v * 190
    g= (f'<rect x="{x - 24}" y="{y - al / 2 - 200:.1f}" width="48" height="{py - (y - al / 2 - 200):.1f}" fill="#e6e9f5" stroke="{TINTA}" stroke-width="8"/>'
        f'<rect x="{x - an_ / 2}" y="{y - al / 2}" width="{an_}" height="{al}" rx="40" fill="#ffb347" stroke="{TINTA}" stroke-width="10"/>'
        f'<rect x="{x - an_ / 2 + 18}" y="{y - al / 2 + 18}" width="40" height="{al - 36}" rx="20" fill="#ffd27a" opacity="0.7"/>')
    if cal > 0.02:
        g+= f'<rect x="{x - an_ / 2}" y="{y - al / 2}" width="{an_}" height="{al}" rx="40" fill="#ff3b30" opacity="{0.55 * cal:.2f}"/>'
    g+= f'<rect x="{x - 24}" y="{y - al / 2 + 5:.1f}" width="48" height="{max(0.0, py - (y - al / 2) - 5):.1f}" fill="#e6e9f5" stroke="{TINTA}" stroke-width="8"/>'
    g+= f'<rect x="{x - an_ / 2 + 8}" y="{py - 30:.1f}" width="{an_ - 16}" height="60" rx="10" fill="#4a5173" stroke="{TINTA}" stroke-width="8"/>'
    vel= math.cos(t * 4)
    for hx in (-90, 90):
        g+= f'<rect x="{x + hx - 11}" y="{py - 30:.1f}" width="22" height="60" fill="#ffb347"/>'
        if ch > 0.02:
            for i in range(4):
                q= ((t * 2.2 + i * 0.25) % 1.0)
                dy= (-34 - 120 * q) * (1 if c.get('dir', 1) > 0 else -1)
                g+= f'<circle cx="{x + hx + 10 * math.sin(q * 9 + i):.1f}" cy="{py + dy:.1f}" r="{9 - 5 * q:.1f}" fill="#fff1c4" opacity="{ch * (1 - q):.2f}"/>'
    if cal > 0.3:
        for i in range(3):
            q= (t * 0.9 + i / 3) % 1.0
            hx= x + an_ / 2 + 50 + 40 * i
            g+= (f'<path d="M{hx},{y + 120 - 300 * q:.1f} q22,-30 0,-60 q-22,-30 0,-60" fill="none" stroke="#ff5a5f" stroke-width="10" stroke-linecap="round" opacity="{cal * (1 - q):.2f}"/>')
    return g


PIEZAS.update({'turismo': turismo, 'suspension': suspension, 'amortiguador': amortiguador})
