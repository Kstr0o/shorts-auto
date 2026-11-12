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
           'hielo': ('#9fd3ff', '#eaf6ff'), 'agua': ('#0c4a7a', '#062238'), 'rojo': ('#3a0d12', '#8a1f24')}.get(tipo, (col(tipo), col(tipo)))
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


def interrogacion(c, p, t, idi):
    bamb= 12 * math.sin(t * 3 + c.get('x', 0))
    return _txt(c.get('x', 540), c.get('y', 900) + bamb, '?', c.get('tam', 120), c.get('color', 'amarillo'), borde='#0a1230')


PIEZAS= {'planeta': planeta, 'sol': sol, 'chip': chip, 'texto': texto, 'contador': contador, 'panel': panel, 'barra': barra,
         'regla': regla, 'flecha': flecha, 'viento': viento, 'suelo': suelo, 'persona': persona, 'casa': casa, 'arbol': arbol,
         'coche': coche, 'punto': punto, 'luna': luna, 'circulo': circulo, 'caja': caja, 'encuesta': encuesta, 'nube': nube, 'carretera': carretera}
_NO_ANIMAR= {'items', 'opciones', 'en', 'sale', 't'}

PIEZAS.update({'cuerpo': cuerpo, 'corte': corte, 'mar': mar, 'burbujas': burbujas, 'celda': celda, 'vaso': vaso, 'gota': gota,
               'tortuga': tortuga, 'avion': avion, 'interrogacion': interrogacion})
_NO_ANIMAR.update({'organos', 'alerta', 'cara'})


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
