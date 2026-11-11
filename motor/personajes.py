"""Personajes vectoriales parametricos (SVG).

Cada personaje se dibuja con el origen en los pies (centro) y mide ~760 px a escala 1.
"""

LINEA = '#1b1b1f'
G = 7  # grosor de contorno

PERSONAJES = {
    # protagonista: Toni, 0 euros y 100 dias para hacerse millonario
    'toni': dict(piel='#f2c29b', pelo='#c4521f', peinado='flequillo', ropa='#7b4fd6', pantalon='#2f3a56',
                 zapatos='#f4f4f4', gafas=True, barba=False, extra='sudadera'),
    'madre': dict(piel='#e8b48c', pelo='#3a2a22', peinado='mono', ropa='#2fa58b', pantalon='#3c3c48',
                  zapatos='#7a3b2e', gafas=False, barba=False, extra='collar'),
    'colega': dict(piel='#a86b43', pelo='#151515', peinado='rapado', ropa='#f2b632', pantalon='#26303f',
                   zapatos='#e04646', gafas=False, barba=True, extra='gorra'),
    'banquero': dict(piel='#f0c8a8', pelo='#9a9aa2', peinado='calvo', ropa='#2b2f3a', pantalon='#2b2f3a',
                     zapatos='#121212', gafas=True, barba=False, extra='corbata'),
}


def _ojos(expr):
    # ojos grandes con brillo; la expresion cambia cejas y pupilas
    dy= {'sorpresa': -4, 'triste': 4}.get(expr, 0)
    r= 21 if expr == 'sorpresa' else 18
    s= ''
    for x in (-38, 38):
        s+= f'<ellipse cx="{x}" cy="-555" rx="{r+4}" ry="{r+8}" fill="#fff" stroke="{LINEA}" stroke-width="5"/>'
        s+= f'<circle cx="{x+3}" cy="{-553+dy}" r="{r-7}" fill="{LINEA}"/>'
        s+= f'<circle cx="{x+8}" cy="{-560+dy}" r="4" fill="#fff"/>'
    cejas= {
        'feliz': [(-60, -592, -18, -598), (18, -598, 60, -592)],
        'sorpresa': [(-60, -605, -18, -612), (18, -612, 60, -605)],
        'enfadado': [(-62, -600, -16, -585), (16, -585, 62, -600)],
        'preocupado': [(-62, -586, -18, -600), (18, -600, 62, -586)],
        'triste': [(-62, -585, -18, -598), (18, -598, 62, -585)],
        'chulo': [(-60, -590, -18, -590), (18, -596, 60, -604)],
    }.get(expr, [(-58, -594, -18, -596), (18, -596, 58, -594)])
    for x1, y1, x2, y2 in cejas:
        s+= f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{LINEA}" stroke-width="9" stroke-linecap="round"/>'
    return s


def _boca(expr):
    if expr == 'sorpresa':
        return f'<ellipse cx="0" cy="-475" rx="20" ry="26" fill="#5a1d24" stroke="{LINEA}" stroke-width="5"/>'
    if expr in ('triste', 'preocupado'):
        return f'<path d="M-30,-470 Q0,-494 30,-470" fill="none" stroke="{LINEA}" stroke-width="7" stroke-linecap="round"/>'
    if expr == 'enfadado':
        return f'<rect x="-34" y="-490" width="68" height="24" rx="6" fill="#fff" stroke="{LINEA}" stroke-width="5"/><line x1="-34" y1="-478" x2="34" y2="-478" stroke="{LINEA}" stroke-width="3"/>'
    if expr == 'chulo':
        return f'<path d="M-24,-482 Q8,-466 34,-490" fill="none" stroke="{LINEA}" stroke-width="7" stroke-linecap="round"/>'
    if expr == 'habla':
        return f'<path d="M-30,-488 Q0,-450 30,-488 Z" fill="#5a1d24" stroke="{LINEA}" stroke-width="5" stroke-linejoin="round"/>'
    # feliz / normal
    return f'<path d="M-36,-490 Q0,-446 36,-490 Z" fill="#fff" stroke="{LINEA}" stroke-width="5" stroke-linejoin="round"/>'


def _pelo(p):
    c= p['pelo']
    t= p['peinado']
    if t == 'flequillo':
        return (f'<path d="M-92,-560 Q-100,-690 0,-700 Q100,-692 92,-566 Q70,-640 20,-620 Q-10,-660 -40,-616 Q-70,-640 -92,-560 Z" '
                f'fill="{c}" stroke="{LINEA}" stroke-width="{G}" stroke-linejoin="round"/>')
    if t == 'mono':
        return (f'<circle cx="0" cy="-712" r="38" fill="{c}" stroke="{LINEA}" stroke-width="{G}"/>'
                f'<path d="M-94,-540 Q-104,-686 0,-690 Q104,-686 94,-540 Q80,-630 0,-640 Q-80,-630 -94,-540 Z" '
                f'fill="{c}" stroke="{LINEA}" stroke-width="{G}" stroke-linejoin="round"/>')
    if t == 'rapado':
        return (f'<path d="M-88,-590 Q-90,-684 0,-688 Q90,-684 88,-590 Q60,-640 0,-640 Q-60,-640 -88,-590 Z" '
                f'fill="{c}" stroke="{LINEA}" stroke-width="{G}" stroke-linejoin="round"/>')
    if t == 'calvo':
        return (f'<path d="M-94,-560 Q-104,-620 -80,-640 L-70,-600 Z" fill="{c}" stroke="{LINEA}" stroke-width="5"/>'
                f'<path d="M94,-560 Q104,-620 80,-640 L70,-600 Z" fill="{c}" stroke="{LINEA}" stroke-width="5"/>')
    return ''


def _extra_cabeza(p):
    s= ''
    if p['gafas']:
        s+= (f'<g fill="none" stroke="{LINEA}" stroke-width="6"><circle cx="-38" cy="-556" r="32"/>'
             f'<circle cx="38" cy="-556" r="32"/><line x1="-6" y1="-558" x2="6" y2="-558"/></g>')
    if p['barba']:
        s+= (f'<path d="M-88,-520 Q-80,-430 0,-424 Q80,-430 88,-520 Q60,-470 0,-466 Q-60,-470 -88,-520 Z" '
             f'fill="{p["pelo"]}" stroke="{LINEA}" stroke-width="5"/>')
    if p['extra'] == 'gorra':
        s+= (f'<path d="M-96,-610 Q-96,-712 0,-714 Q96,-712 96,-610 Z" fill="#e04646" stroke="{LINEA}" stroke-width="{G}"/>'
             f'<path d="M-10,-612 L150,-604 Q150,-588 -10,-592 Z" fill="#c13434" stroke="{LINEA}" stroke-width="{G}" stroke-linejoin="round"/>')
    return s


def _brazo(lado, pose, ropa, piel):
    # lado -1 izquierda, 1 derecha; hombro en (lado*92, -385)
    hx= lado * 92
    if pose == 'arriba' and lado == 1:
        d= f'M{hx},-385 L{hx+70},-520'
        mano= (hx + 76, -540)
    elif pose == 'movil' and lado == 1:
        d= f'M{hx},-385 L{hx+30},-300 L{hx-10},-470'
        mano= (hx - 14, -490)
    elif pose == 'señala' and lado == 1:
        d= f'M{hx},-385 L{hx+150},-360'
        mano= (hx + 170, -360)
    elif pose == 'cruzado':
        d= f'M{hx},-385 L{hx+lado*16},-290 L{-lado*40},-300'
        mano= (-lado * 50, -300)
    else:
        d= f'M{hx},-385 L{hx+lado*26},-220'
        mano= (hx + lado * 28, -205)
    s= (f'<path d="{d}" fill="none" stroke="{LINEA}" stroke-width="58" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<path d="{d}" fill="none" stroke="{ropa}" stroke-width="44" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="{mano[0]}" cy="{mano[1]}" r="25" fill="{piel}" stroke="{LINEA}" stroke-width="{G}"/>')
    if pose == 'movil' and lado == 1:
        s+= (f'<rect x="{mano[0]-30}" y="{mano[1]-70}" width="44" height="82" rx="9" fill="#25262b" stroke="{LINEA}" stroke-width="5"/>'
             f'<rect x="{mano[0]-25}" y="{mano[1]-63}" width="34" height="62" rx="5" fill="#6fd3ff"/>')
    return s


def personaje(nombre, expr='normal', pose='normal', x=540, y=1640, escala=1.0, girar=False, sudor=False, olor=False):
    p= PERSONAJES[nombre]
    sx= -escala if girar else escala
    L= LINEA
    s= f'<g transform="translate({x},{y}) scale({sx},{escala})">'
    # sombra
    s+= '<ellipse cx="0" cy="6" rx="150" ry="22" fill="#000" opacity="0.18"/>'
    # piernas y zapatos
    for lx in (-44, 44):
        s+= f'<rect x="{lx-30}" y="-250" width="60" height="230" rx="14" fill="{p["pantalon"]}" stroke="{L}" stroke-width="{G}"/>'
        s+= f'<path d="M{lx-40},0 Q{lx-40},-40 {lx},-38 Q{lx+52},-36 {lx+52},0 Z" fill="{p["zapatos"]}" stroke="{L}" stroke-width="{G}" stroke-linejoin="round"/>'
    # brazo trasero (izquierdo)
    s+= _brazo(-1, pose if pose == 'cruzado' else 'normal', p['ropa'], p['piel'])
    # torso
    s+= f'<path d="M-100,-400 Q-100,-430 -60,-430 L60,-430 Q100,-430 100,-400 L108,-230 Q108,-210 88,-210 L-88,-210 Q-108,-210 -108,-230 Z" fill="{p["ropa"]}" stroke="{L}" stroke-width="{G}" stroke-linejoin="round"/>'
    if p['extra'] == 'sudadera':
        s+= f'<path d="M-50,-300 L50,-300 L44,-246 L-44,-246 Z" fill="none" stroke="{L}" stroke-width="5" opacity="0.6"/>'
        s+= f'<line x1="-18" y1="-430" x2="-24" y2="-360" stroke="#fff" stroke-width="6" stroke-linecap="round"/><line x1="18" y1="-430" x2="24" y2="-360" stroke="#fff" stroke-width="6" stroke-linecap="round"/>'
    elif p['extra'] == 'corbata':
        s+= f'<path d="M-40,-430 L0,-370 L40,-430 Z" fill="#fff" stroke="{L}" stroke-width="5"/><path d="M-12,-410 L12,-410 L20,-300 L0,-276 L-20,-300 Z" fill="#c8302f" stroke="{L}" stroke-width="5" stroke-linejoin="round"/>'
    elif p['extra'] == 'collar':
        s+= '<path d="M-44,-424 Q0,-370 44,-424" fill="none" stroke="#f4e9c7" stroke-width="10" stroke-dasharray="2 14" stroke-linecap="round"/>'
    # cuello y cabeza
    s+= f'<rect x="-26" y="-450" width="52" height="40" fill="{p["piel"]}" stroke="{L}" stroke-width="{G}"/>'
    s+= f'<ellipse cx="-96" cy="-540" rx="20" ry="28" fill="{p["piel"]}" stroke="{L}" stroke-width="{G}"/>'
    s+= f'<ellipse cx="96" cy="-540" rx="20" ry="28" fill="{p["piel"]}" stroke="{L}" stroke-width="{G}"/>'
    s+= f'<rect x="-96" y="-668" width="192" height="236" rx="86" fill="{p["piel"]}" stroke="{L}" stroke-width="{G}"/>'
    s+= f'<ellipse cx="-62" cy="-500" rx="18" ry="10" fill="#ff7a7a" opacity="0.35"/><ellipse cx="62" cy="-500" rx="18" ry="10" fill="#ff7a7a" opacity="0.35"/>'
    s+= _pelo(p)
    s+= _ojos(expr)
    s+= f'<path d="M-4,-540 Q10,-516 -6,-510" fill="none" stroke="{L}" stroke-width="5" stroke-linecap="round"/>'
    s+= _boca(expr)
    s+= _extra_cabeza(p)
    # brazo delantero (derecho)
    s+= _brazo(1, pose, p['ropa'], p['piel'])
    if sudor:
        s+= '<path d="M110,-640 Q122,-614 110,-604 Q98,-614 110,-640 Z" fill="#7fd3ff" stroke="#1b1b1f" stroke-width="4"/>'
        s+= '<path d="M-118,-600 Q-108,-580 -118,-572 Q-128,-580 -118,-600 Z" fill="#7fd3ff" stroke="#1b1b1f" stroke-width="4"/>'
    if olor:
        for ox in (-150, -110, 120):
            s+= f'<path d="M{ox},-420 q-18,-30 0,-60 q18,-30 0,-60" fill="none" stroke="#6bbf3a" stroke-width="8" stroke-linecap="round" opacity="0.8"/>'
    s+= '</g>'
    return s
