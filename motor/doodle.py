"""Estilo 2: garabato en papel (monigote de palo + objetos a rotulador)."""
import math

N= '#16161a'
ACENTO= '#ff4d2e'
G= 13


def papel(color='#fbf7ee'):
    s= f'<rect width="1080" height="1920" fill="{color}"/>'
    for y in range(60, 1920, 60):
        s+= f'<line x1="0" y1="{y}" x2="1080" y2="{y}" stroke="#cfe0f2" stroke-width="2.5"/>'
    for x in range(60, 1080, 60):
        s+= f'<line x1="{x}" y1="0" x2="{x}" y2="1920" stroke="#cfe0f2" stroke-width="2.5"/>'
    return s


def pizarra():
    return papel('#fff2c9')


def oscuro():
    s= '<rect width="1080" height="1920" fill="#1c1f2b"/>'
    for i in range(60):
        x= (i * 397) % 1080
        y= (i * 613) % 1300
        s+= f'<circle cx="{x}" cy="{y}" r="{2 + i % 3}" fill="#fff" opacity="0.7"/>'
    return s


def palo(expr='normal', pose='normal', x=540, y=1640, escala=1.0, girar=False, ojeras=False, zzz=False, tinta=N):
    sx= -escala if girar else escala
    a= f'fill="none" stroke="{tinta}" stroke-width="{G}" stroke-linecap="round" stroke-linejoin="round"'
    s= f'<g transform="translate({x},{y}) scale({sx},{escala})">'
    # piernas y cuerpo
    s+= f'<path d="M0,-270 L-78,0 M0,-270 L78,0 M0,-505 L0,-270" {a}/>'
    brazos= {
        'normal': 'M0,-450 L-95,-300 M0,-450 L95,-300',
        'arriba': 'M0,-450 L-120,-590 M0,-450 L120,-590',
        'señala': 'M0,-450 L-95,-300 M0,-450 L170,-480',
        'caido': 'M0,-450 L-50,-270 M0,-450 L50,-270',
        'cabeza': 'M0,-450 L-120,-520 L-80,-640 M0,-450 L120,-520 L80,-640',
        'cafe': 'M0,-450 L-95,-300 M0,-450 L110,-400 L120,-470',
    }[pose]
    s+= f'<path d="{brazos}" {a}/>'
    if pose == 'cafe':
        s+= f'<rect x="100" y="-545" width="62" height="74" rx="8" fill="#fff" stroke="{tinta}" stroke-width="9"/><path d="M162,-530 q34,16 0,40" fill="none" stroke="{tinta}" stroke-width="8"/>'
        s+= f'<path d="M118,-570 q-12,-22 0,-40 M142,-570 q-12,-22 0,-40" fill="none" stroke="{tinta}" stroke-width="6" stroke-linecap="round"/>'
    # cabeza
    s+= f'<circle cx="0" cy="-600" r="98" fill="#fff" stroke="{tinta}" stroke-width="{G}"/>'
    # gorro de marca
    s+= f'<path d="M-92,-640 Q-80,-730 0,-732 Q80,-730 92,-640 Z" fill="{ACENTO}" stroke="{tinta}" stroke-width="{G}" stroke-linejoin="round"/>'
    s+= f'<circle cx="0" cy="-745" r="22" fill="{ACENTO}" stroke="{tinta}" stroke-width="10"/>'
    # ojos
    if expr == 'dormido':
        s+= f'<path d="M-52,-600 q16,14 32,0 M20,-600 q16,14 32,0" {a}/>'
    elif expr == 'loco':
        s+= f'<circle cx="-36" cy="-602" r="24" fill="#fff" stroke="{tinta}" stroke-width="8"/><circle cx="36" cy="-602" r="15" fill="#fff" stroke="{tinta}" stroke-width="8"/>'
        s+= f'<circle cx="-36" cy="-602" r="6" fill="{tinta}"/><circle cx="36" cy="-602" r="5" fill="{tinta}"/>'
    elif expr == 'sorpresa':
        s+= f'<circle cx="-36" cy="-606" r="17" fill="{tinta}"/><circle cx="36" cy="-606" r="17" fill="{tinta}"/>'
    else:
        s+= f'<circle cx="-36" cy="-604" r="12" fill="{tinta}"/><circle cx="36" cy="-604" r="12" fill="{tinta}"/>'
    if ojeras:
        s+= f'<path d="M-58,-578 q22,18 44,0 M14,-578 q22,18 44,0" fill="none" stroke="#8a6fb0" stroke-width="8" stroke-linecap="round"/>'
    # boca
    boca= {
        'feliz': 'M-40,-560 Q0,-520 40,-560',
        'triste': 'M-36,-540 Q0,-570 36,-540',
        'sorpresa': 'M-14,-548 a14,18 0 1,0 28,0 a14,18 0 1,0 -28,0',
        'loco': 'M-44,-548 l14,-12 l14,12 l14,-12 l14,12 l14,-12 l14,12',
        'dormido': 'M-12,-548 a12,12 0 1,0 24,0 a12,12 0 1,0 -24,0',
    }.get(expr, 'M-30,-548 L30,-548')
    s+= f'<path d="{boca}" {a}/>'
    if zzz:
        for i, (zx, zy, t) in enumerate([(120, -700, 60), (180, -790, 80), (250, -900, 104)]):
            s+= f'<text x="{zx}" y="{zy}" font-family="Anton" font-size="{t}" fill="{ACENTO}" transform="scale({-1 if girar else 1},1)">Z</text>' if not girar else f'<text x="{zx}" y="{zy}" font-family="Anton" font-size="{t}" fill="{ACENTO}">Z</text>'
    return s + '</g>'


def _esc(t):
    return str(t).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def nota(texto, x=540, y=300, tam=92, color=N, rot=-2, subrayar=True):
    """Texto manuscrito con subrayado de rotulador."""
    tam= int(tam * 1.4)
    tam= min(tam, int(940 / (max(len(texto), 1) * 0.42)))
    w= len(texto) * tam * 0.40
    s= f'<g transform="translate({x},{y}) rotate({rot})">'
    if subrayar:
        s+= f'<path d="M{-w/2},{tam*0.34} q{w/4},-14 {w/2},0 t{w/2},-4" fill="none" stroke="{ACENTO}" stroke-width="14" stroke-linecap="round"/>'
    s+= f'<text x="0" y="0" font-family="Patrick Hand" font-size="{tam}" text-anchor="middle" fill="{color}">{_esc(texto)}</text></g>'
    return s


def numero(valor, etiqueta='', x=540, y=520, tam=300, color=ACENTO):
    s= f'<text x="{x}" y="{y}" font-family="Anton" font-size="{tam}" text-anchor="middle" fill="{color}" stroke="{N}" stroke-width="10" paint-order="stroke">{_esc(valor)}</text>'
    if etiqueta:
        s+= f'<text x="{x}" y="{y+110}" font-family="Patrick Hand" font-size="96" text-anchor="middle" fill="{N}">{_esc(etiqueta)}</text>'
    return s


def reloj(x=540, y=520, r=190, hora=3):
    s= f'<circle cx="{x}" cy="{y}" r="{r}" fill="#fff" stroke="{N}" stroke-width="{G}"/>'
    for i in range(12):
        a= math.pi * i / 6
        s+= f'<line x1="{x+math.sin(a)*(r-30):.0f}" y1="{y-math.cos(a)*(r-30):.0f}" x2="{x+math.sin(a)*(r-12):.0f}" y2="{y-math.cos(a)*(r-12):.0f}" stroke="{N}" stroke-width="8" stroke-linecap="round"/>'
    a= math.pi * hora / 6
    s+= f'<line x1="{x}" y1="{y}" x2="{x+math.sin(a)*r*0.5:.0f}" y2="{y-math.cos(a)*r*0.5:.0f}" stroke="{N}" stroke-width="16" stroke-linecap="round"/>'
    s+= f'<line x1="{x}" y1="{y}" x2="{x}" y2="{y-r*0.75}" stroke="{ACENTO}" stroke-width="10" stroke-linecap="round"/>'
    s+= f'<circle cx="{x}" cy="{y}" r="12" fill="{N}"/>'
    return s


def cama(x=540, y=1640):
    s= f'<g transform="translate({x},{y})">'
    s+= f'<rect x="-330" y="-190" width="660" height="130" rx="20" fill="#bfe3ff" stroke="{N}" stroke-width="{G}"/>'
    s+= f'<rect x="-320" y="-250" width="170" height="80" rx="34" fill="#fff" stroke="{N}" stroke-width="{G}"/>'
    s+= f'<path d="M-330,-60 L-330,0 M330,-60 L330,0 M-360,-300 L-360,0" fill="none" stroke="{N}" stroke-width="{G}" stroke-linecap="round"/>'
    return s + '</g>'


def cerebro(x=540, y=560, escala=1.0, roto=False):
    s= f'<g transform="translate({x},{y}) scale({escala})">'
    s+= f'<path d="M-150,20 Q-210,-40 -150,-100 Q-140,-180 -50,-170 Q0,-220 60,-170 Q150,-180 160,-90 Q220,-30 150,30 Q150,110 50,100 Q0,140 -60,100 Q-150,110 -150,20 Z" fill="#ffb3c7" stroke="{N}" stroke-width="{G}" stroke-linejoin="round"/>'
    s+= f'<path d="M0,-170 Q-30,-60 10,0 Q40,50 0,110 M-110,-60 q40,30 70,0 M60,-90 q40,30 70,0 M-100,40 q40,-30 70,0 M50,30 q40,30 70,0" fill="none" stroke="{N}" stroke-width="9" stroke-linecap="round"/>'
    if roto:
        s+= f'<path d="M-40,-230 l30,70 l-40,30 l50,60" fill="none" stroke="{ACENTO}" stroke-width="14" stroke-linecap="round" stroke-linejoin="round"/>'
        s+= f'<path d="M190,-190 l-40,-40 M230,-120 l-56,-10 M-200,-180 l40,-30" stroke="{ACENTO}" stroke-width="10" stroke-linecap="round"/>'
    return s + '</g>'


def fantasma(x=540, y=600, escala=1.0):
    s= f'<g transform="translate({x},{y}) scale({escala})" opacity="0.92">'
    s+= f'<path d="M-90,120 L-90,-40 Q-90,-140 0,-140 Q90,-140 90,-40 L90,120 L50,84 L18,120 L-18,84 L-50,120 Z" fill="#fff" stroke="{N}" stroke-width="{G}" stroke-linejoin="round"/>'
    s+= f'<circle cx="-30" cy="-50" r="14" fill="{N}"/><circle cx="30" cy="-50" r="14" fill="{N}"/><ellipse cx="0" cy="0" rx="14" ry="20" fill="{N}"/>'
    return s + '</g>'


def trofeo(x=540, y=600, escala=1.0):
    s= f'<g transform="translate({x},{y}) scale({escala})">'
    s+= f'<path d="M-100,-150 L100,-150 L80,0 Q0,70 -80,0 Z" fill="#ffd34d" stroke="{N}" stroke-width="{G}" stroke-linejoin="round"/>'
    s+= f'<path d="M-100,-120 q-70,10 -40,80 q20,30 60,30 M100,-120 q70,10 40,80 q-20,30 -60,30" fill="none" stroke="{N}" stroke-width="{G}"/>'
    s+= f'<rect x="-18" y="40" width="36" height="70" fill="#ffd34d" stroke="{N}" stroke-width="{G}"/><rect x="-80" y="110" width="160" height="40" rx="8" fill="#ffd34d" stroke="{N}" stroke-width="{G}"/>'
    return s + '</g>'


def prohibido(x=540, y=560, r=200):
    return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="#e63946" stroke-width="34"/>'
            f'<line x1="{x-r*0.7}" y1="{y-r*0.7}" x2="{x+r*0.7}" y2="{y+r*0.7}" stroke="#e63946" stroke-width="34"/>')


def coche(x=540, y=1640, choque=False):
    s= f'<g transform="translate({x},{y}) rotate({-8 if choque else 0})">'
    s+= f'<path d="M-230,-70 L-200,-150 Q-190,-200 -130,-200 L80,-200 Q130,-200 160,-150 L230,-130 Q250,-120 250,-70 Z" fill="#8ecae6" stroke="{N}" stroke-width="{G}" stroke-linejoin="round"/>'
    s+= f'<circle cx="-130" cy="-60" r="52" fill="#fff" stroke="{N}" stroke-width="{G}"/><circle cx="140" cy="-60" r="52" fill="#fff" stroke="{N}" stroke-width="{G}"/>'
    s+= '</g>'
    if choque:
        s+= f'<path d="M{x+270},{y-260} l60,-40 M{x+290},{y-180} l80,0 M{x+270},{y-100} l60,40" stroke="{ACENTO}" stroke-width="14" stroke-linecap="round"/>'
    return s


def calendario(n, x=540, y=520, etiqueta='DÍA'):
    s= f'<g transform="translate({x},{y}) rotate(-3)">'
    s+= f'<rect x="-190" y="-200" width="380" height="400" rx="26" fill="#fff" stroke="{N}" stroke-width="{G}"/>'
    s+= f'<path d="M-190,-90 L-190,-174 Q-190,-200 -164,-200 L164,-200 Q190,-200 190,-174 L190,-90 Z" fill="{ACENTO}" stroke="{N}" stroke-width="{G}"/>'
    s+= f'<text x="0" y="-112" font-family="Anton" font-size="70" text-anchor="middle" fill="#fff">{_esc(etiqueta)}</text>'
    s+= f'<text x="0" y="140" font-family="Anton" font-size="230" text-anchor="middle" fill="{N}">{_esc(n)}</text></g>'
    return s


OBJETOS= {'nota': nota, 'numero': numero, 'reloj': reloj, 'cama': cama, 'cerebro': cerebro, 'fantasma': fantasma,
          'trofeo': trofeo, 'prohibido': prohibido, 'coche': coche, 'calendario': calendario}
FONDOS= {'papel': papel, 'papel_amarillo': pizarra, 'oscuro': oscuro}
