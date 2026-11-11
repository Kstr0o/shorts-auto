"""Escenarios y objetos vectoriales (SVG) de 1080x1920."""

L= '#1b1b1f'
W, H= 1080, 1920
SUELO= 1640  # linea de pies de los personajes
IDIOMA= 'es'  # lo cambia render.py antes de dibujar cada version


def T(es, en):
    return en if IDIOMA == 'en' else es


def MON():
    return '$' if IDIOMA == 'en' else '€'


def _ventana(x, y, w, h, cielo='#9fe0ff', noche=False):
    c= '#1d2650' if noche else cielo
    s= f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{c}" stroke="{L}" stroke-width="8"/>'
    s+= f'<line x1="{x+w/2}" y1="{y}" x2="{x+w/2}" y2="{y+h}" stroke="{L}" stroke-width="8"/>'
    s+= f'<line x1="{x}" y1="{y+h/2}" x2="{x+w}" y2="{y+h/2}" stroke="{L}" stroke-width="8"/>'
    if noche:
        s+= f'<circle cx="{x+w*0.72}" cy="{y+h*0.25}" r="24" fill="#ffe680"/>'
    return s


def habitacion(noche=False):
    s= f'<rect width="{W}" height="{H}" fill="#f3dcb8"/>'
    s+= f'<rect y="{SUELO-80}" width="{W}" height="{H-SUELO+80}" fill="#b98653"/>'
    for i in range(0, W, 120):
        s+= f'<line x1="{i}" y1="{SUELO-80}" x2="{i-60}" y2="{H}" stroke="#a0703f" stroke-width="5"/>'
    s+= f'<rect y="{SUELO-92}" width="{W}" height="16" fill="#8d5f33"/>'
    s+= _ventana(90, 520, 300, 320, noche=noche)
    # poster
    s+= f'<g transform="rotate(-4 800 640)"><rect x="680" y="500" width="240" height="300" fill="#fff6d6" stroke="{L}" stroke-width="7"/>'
    s+= f'<text x="800" y="590" font-family="Anton" font-size="56" text-anchor="middle" fill="#2b9b57">{MON()*3}</text>'
    s+= f'<text x="800" y="680" font-family="Anton" font-size="34" text-anchor="middle" fill="{L}">{T("SE RICO", "GET RICH")}</text>'
    s+= f'<text x="800" y="740" font-family="Anton" font-size="34" text-anchor="middle" fill="{L}">{T("YA", "NOW")}</text></g>'
    # cama
    s+= f'<rect x="620" y="{SUELO-300}" width="420" height="150" rx="20" fill="#5c7cfa" stroke="{L}" stroke-width="8"/>'
    s+= f'<rect x="640" y="{SUELO-340}" width="130" height="60" rx="24" fill="#fff" stroke="{L}" stroke-width="7"/>'
    s+= f'<rect x="620" y="{SUELO-160}" width="30" height="90" fill="#6b4423" stroke="{L}" stroke-width="7"/><rect x="1010" y="{SUELO-160}" width="30" height="90" fill="#6b4423" stroke="{L}" stroke-width="7"/>'
    # hucha vacia
    s+= f'<ellipse cx="200" cy="{SUELO-140}" rx="70" ry="50" fill="#ff9ec4" stroke="{L}" stroke-width="7"/>'
    s+= f'<rect x="185" y="{SUELO-196}" width="30" height="8" fill="{L}"/>'
    s+= f'<rect x="90" y="{SUELO-92}" width="220" height="20" fill="#6b4423" stroke="{L}" stroke-width="6"/>'
    if noche:
        s+= f'<rect width="{W}" height="{H}" fill="#0b1030" opacity="0.35"/>'
    return s


def cocina():
    s= f'<rect width="{W}" height="{H}" fill="#cdeee3"/>'
    for y in range(700, SUELO - 80, 60):
        for x in range(0, W, 60):
            s+= f'<rect x="{x+3}" y="{y+3}" width="54" height="54" fill="#e9fbf5" stroke="#b5ddd0" stroke-width="3"/>'
    s+= f'<rect y="{SUELO-80}" width="{W}" height="{H-SUELO+80}" fill="#f2f2f2"/>'
    for x in range(0, W, 120):
        for y in range(SUELO - 80, H, 120):
            if (x // 120 + y // 120) % 2:
                s+= f'<rect x="{x}" y="{y}" width="120" height="120" fill="#d9d9de"/>'
    # muebles altos
    for x in (60, 330, 600, 870):
        s+= f'<rect x="{x}" y="330" width="230" height="230" rx="10" fill="#f7b267" stroke="{L}" stroke-width="8"/>'
        s+= f'<rect x="{x+100}" y="500" width="30" height="12" rx="6" fill="{L}"/>'
    # encimera
    s+= f'<rect x="0" y="{SUELO-420}" width="{W}" height="40" fill="#8c8c99" stroke="{L}" stroke-width="8"/>'
    s+= f'<rect x="0" y="{SUELO-380}" width="{W}" height="300" fill="#f79d65" stroke="{L}" stroke-width="8"/>'
    # olla
    s+= f'<rect x="760" y="{SUELO-560}" width="200" height="140" rx="14" fill="#b8c0cc" stroke="{L}" stroke-width="8"/>'
    s+= f'<rect x="740" y="{SUELO-578}" width="240" height="26" rx="10" fill="#9aa3b0" stroke="{L}" stroke-width="7"/>'
    return s


def calle(noche=True):
    cielo= '#18204a' if noche else '#8fd3ff'
    s= f'<rect width="{W}" height="{H}" fill="{cielo}"/>'
    if noche:
        s+= '<circle cx="880" cy="260" r="60" fill="#ffe680"/><circle cx="905" cy="245" r="56" fill="#18204a"/>'
    edif= [(0, 520, 260, '#2c3566'), (240, 380, 300, '#343f78'), (520, 600, 240, '#29305c'), (740, 440, 340, '#313b70')]
    if not noche:
        edif= [(x, y, w, c2) for (x, y, w, _), c2 in zip(edif, ('#f4a261', '#e9c46a', '#2a9d8f', '#e76f51'))]
    for x, y, w, c in edif:
        s+= f'<rect x="{x}" y="{y}" width="{w}" height="{SUELO-y}" fill="{c}"/>'
        for wy in range(y + 50, SUELO - 260, 110):
            for wx in range(x + 30, x + w - 50, 80):
                on= ((wx * 7 + wy * 3) // 50) % 3 == 0
                color= '#ffd966' if (on and noche) else ('#1b2142' if noche else '#ffffff')
                s+= f'<rect x="{wx}" y="{wy}" width="44" height="60" rx="4" fill="{color}" opacity="0.95"/>'
    s+= f'<rect y="{SUELO-200}" width="{W}" height="200" fill="#8e8e9e"/>'
    s+= f'<rect y="{SUELO}" width="{W}" height="{H-SUELO}" fill="#3b3b47"/>'
    for x in range(30, W, 200):
        s+= f'<rect x="{x}" y="{SUELO+130}" width="110" height="16" fill="#f4f4f4"/>'
    # farola
    s+= f'<rect x="96" y="{SUELO-760}" width="18" height="760" fill="{L}"/><rect x="70" y="{SUELO-790}" width="70" height="40" rx="10" fill="{L}"/>'
    if noche:
        s+= f'<ellipse cx="105" cy="{SUELO-740}" rx="60" ry="22" fill="#ffe680" opacity="0.6"/>'
    return s


def banco():
    s= f'<rect width="{W}" height="{H}" fill="#efe6d2"/>'
    for x in (40, 960):
        s+= f'<rect x="{x}" y="300" width="80" height="{SUELO-300}" fill="#fbf7ee" stroke="{L}" stroke-width="8"/>'
    s+= f'<rect x="300" y="250" width="480" height="110" rx="12" fill="#22408f" stroke="{L}" stroke-width="8"/>'
    s+= f'<text x="540" y="335" font-family="Anton" font-size="78" text-anchor="middle" fill="#ffd34d">{T("BANCO", "BANK")}</text>'
    s+= f'<rect x="200" y="520" width="300" height="240" fill="#fffbe9" stroke="{L}" stroke-width="7"/>'
    s+= f'<text x="350" y="610" font-family="Anton" font-size="44" text-anchor="middle" fill="#888">{T("PRÉSTAMOS", "LOANS")}</text>'
    s+= f'<text x="350" y="690" font-family="Anton" font-size="60" text-anchor="middle" fill="#d23b3b">{T("AL 21%", "AT 21%")}</text>'
    s+= f'<rect y="{SUELO-80}" width="{W}" height="{H-SUELO+80}" fill="#d7d2c8"/>'
    for x in range(0, W, 100):
        for y in range(SUELO - 80, H, 100):
            if (x // 100 + y // 100) % 2:
                s+= f'<rect x="{x}" y="{y}" width="100" height="100" fill="#ffffff"/>'
    # mostrador
    s+= f'<rect x="560" y="{SUELO-330}" width="480" height="330" fill="#7b4a2a" stroke="{L}" stroke-width="8"/>'
    s+= f'<rect x="540" y="{SUELO-350}" width="520" height="34" fill="#9a603a" stroke="{L}" stroke-width="8"/>'
    return s


def rayos(c1='#ffb703', c2='#fb8500'):
    s= f'<rect width="{W}" height="{H}" fill="{c1}"/>'
    import math
    cx, cy= W / 2, H * 0.42
    n= 18
    for i in range(n):
        a1= 2 * math.pi * i / n
        a2= a1 + math.pi / n
        r= 2400
        s+= (f'<path d="M{cx},{cy} L{cx+r*math.cos(a1):.0f},{cy+r*math.sin(a1):.0f} '
             f'L{cx+r*math.cos(a2):.0f},{cy+r*math.sin(a2):.0f} Z" fill="{c2}"/>')
    return s


def noticias(titular=None, rotulo=''):
    titular= titular or T('ÚLTIMA HORA', 'BREAKING')
    s= f'<rect width="{W}" height="{H}" fill="#14213d"/>'
    for x in range(0, W, 90):
        s+= f'<rect x="{x}" y="0" width="45" height="{H}" fill="#18284a"/>'
    s+= f'<rect x="80" y="380" width="920" height="560" rx="14" fill="#2b4a8b" stroke="#0a0f1f" stroke-width="10"/>'
    s+= f'<rect x="80" y="860" width="920" height="80" fill="#d62828"/>'
    s+= f'<rect x="80" y="860" width="250" height="80" fill="#ffd34d"/>'
    s+= f'<text x="205" y="916" font-family="Anton" font-size="42" text-anchor="middle" fill="{L}">{titular}</text>'
    s+= f'<text x="350" y="918" font-family="Anton" font-size="42" fill="#fff">{rotulo}</text>'
    return s


def mesa_noticias():
    s= ''
    s+= f'<rect x="120" y="{SUELO-260}" width="840" height="260" fill="#1f3c88" stroke="#0a0f1f" stroke-width="8"/>'
    s+= f'<rect x="120" y="{SUELO-275}" width="840" height="30" fill="#d62828"/>'
    s+= f'<text x="540" y="{SUELO-150}" font-family="Anton" font-size="70" text-anchor="middle" fill="#fff">N-100</text>'
    return s


FONDOS= {'habitacion': habitacion, 'habitacion_noche': lambda: habitacion(True), 'cocina': cocina,
         'calle_noche': calle, 'calle_dia': lambda: calle(False), 'banco': banco, 'rayos': rayos,
         'rayos_verde': lambda: rayos('#2a9d8f', '#21867a'), 'rayos_rojo': lambda: rayos('#e63946', '#c92f3b'),
         'noticias': noticias}


# ---------- objetos y pegatinas ----------

def _esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def pegatina(texto, x=540, y=420, color='#ffd34d', tinta=L, rot=-3, tam=58):
    w= max(160, int(len(texto) * tam * 0.52) + 60)
    h= int(tam * 1.5)
    return (f'<g transform="translate({x},{y}) rotate({rot})">'
            f'<rect x="{-w/2+8}" y="{-h/2+10}" width="{w}" height="{h}" rx="12" fill="{L}"/>'
            f'<rect x="{-w/2}" y="{-h/2}" width="{w}" height="{h}" rx="12" fill="{color}" stroke="{L}" stroke-width="6"/>'
            f'<text x="0" y="{tam*0.36}" font-family="Anton" font-size="{tam}" text-anchor="middle" fill="{tinta}">{_esc(texto)}</text></g>')


def cartel(lineas, x=540, y=760, w=600, color='#fffbe9', tachadas=()):
    h= 120 + 90 * len(lineas)
    s= f'<g transform="translate({x},{y}) rotate(2)"><rect x="{-w/2}" y="{-h/2}" width="{w}" height="{h}" fill="{color}" stroke="{L}" stroke-width="8"/>'
    s+= f'<circle cx="{-w/2+30}" cy="{-h/2+30}" r="10" fill="#d62828"/><circle cx="{w/2-30}" cy="{-h/2+30}" r="10" fill="#d62828"/>'
    for i, t in enumerate(lineas):
        ty= -h / 2 + 110 + 90 * i
        s+= f'<text x="0" y="{ty}" font-family="Anton" font-size="60" text-anchor="middle" fill="{L}">{_esc(t)}</text>'
        if i in tachadas:
            s+= f'<line x1="{-w/2+60}" y1="{ty-22}" x2="{w/2-60}" y2="{ty-22}" stroke="#d62828" stroke-width="10"/>'
    return s + '</g>'


def movil_chat(nombre, mensajes, x=540, y=820):
    w, h= 560, 820
    s= f'<g transform="translate({x-w/2},{y-h/2})"><rect width="{w}" height="{h}" rx="50" fill="#1e1f25" stroke="{L}" stroke-width="8"/>'
    s+= f'<rect x="24" y="30" width="{w-48}" height="{h-60}" rx="30" fill="#ece5dd"/>'
    s+= f'<rect x="24" y="30" width="{w-48}" height="110" rx="30" fill="#128c7e"/><rect x="24" y="100" width="{w-48}" height="40" fill="#128c7e"/>'
    s+= f'<circle cx="90" cy="88" r="34" fill="#f2c29b" stroke="#fff" stroke-width="4"/>'
    s+= f'<text x="140" y="104" font-family="Inter" font-weight="bold" font-size="40" fill="#fff">{_esc(nombre)}</text>'
    yy= 190
    for de_mi, t in mensajes:
        tw= min(w - 120, int(len(t) * 19) + 50)
        bx= (w - 50 - tw) if de_mi else 50
        s+= f'<rect x="{bx}" y="{yy}" width="{tw}" height="80" rx="16" fill="{"#dcf8c6" if de_mi else "#fff"}" stroke="#b9b9b9" stroke-width="2"/>'
        s+= f'<text x="{bx+24}" y="{yy+52}" font-family="Inter" font-size="34" fill="{L}">{_esc(t)}</text>'
        yy+= 110
    return s + '</g>'


def billetes(x=540, y=1500, n=6):
    s= ''
    for i in range(n):
        dx= (i % 3) * 110 - 110
        dy= -(i // 3) * 46
        s+= (f'<g transform="translate({x+dx},{y+dy}) rotate({(i*13)%9-4})"><rect x="-90" y="-40" width="180" height="80" rx="8" fill="#7bc96f" stroke="{L}" stroke-width="6"/>'
             f'<circle cx="0" cy="0" r="24" fill="#a8e29a" stroke="{L}" stroke-width="4"/><text x="0" y="12" font-family="Anton" font-size="32" text-anchor="middle" fill="{L}">{MON()}</text></g>')
    return s


def contador(valor, etiqueta, x=540, y=330, color='#2b9b57'):
    return (f'<g transform="translate({x},{y})"><rect x="-260" y="-110" width="520" height="220" rx="24" fill="#16161c" stroke="{L}" stroke-width="8"/>'
            f'<text x="0" y="40" font-family="Anton" font-size="130" text-anchor="middle" fill="{color}">{_esc(valor)}</text>'
            f'<text x="0" y="92" font-family="Anton" font-size="40" text-anchor="middle" fill="#fff">{_esc(etiqueta)}</text></g>')


def grafico(sube=True, x=540, y=600):
    pts= '0,160 80,120 160,140 240,70 320,90 400,10' if sube else '0,10 80,60 160,40 240,120 320,100 400,170'
    col= '#2b9b57' if sube else '#d62828'
    return (f'<g transform="translate({x-230},{y-120})"><rect width="460" height="250" rx="18" fill="#fff" stroke="{L}" stroke-width="8"/>'
            f'<polyline transform="translate(30,40)" points="{pts}" fill="none" stroke="{col}" stroke-width="14" stroke-linejoin="round" stroke-linecap="round"/></g>')


def objeto(spec):
    t= spec.get('tipo')
    a= {k: v for k, v in spec.items() if k != 'tipo'}
    if t == 'pegatina':
        return pegatina(**a)
    if t == 'cartel':
        return cartel(**a)
    if t == 'chat':
        return movil_chat(a['nombre'], [tuple(m) for m in a['mensajes']], a.get('x', 540), a.get('y', 820))
    if t == 'billetes':
        return billetes(**a)
    if t == 'contador':
        return contador(**a)
    if t == 'grafico':
        return grafico(**a)
    if t == 'dia':
        return pegatina(f'{T("DÍA", "DAY")} {a["n"]}/100', x=540, y=150, color='#16161c', tinta='#ffd34d', rot=0, tam=54)
    raise ValueError(f'objeto desconocido: {t}')
