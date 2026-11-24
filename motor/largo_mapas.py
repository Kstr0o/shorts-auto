"""Videos de mapas a escala (largos 16:9 y Shorts 9:16) para El Laboratorio del Y Si.

Uso: python3 motor/largo_mapas.py largos/imperios.json salida [--sin-voz] [--hasta SEG] [--fotos t1,t2,...]
- El guion es una lista de frases ("beats"); cada frase con "v" abre una escena nueva (globo, mapa, comparativa...).
- Mapas en proyeccion Equal Earth (de igual area: los tamanos se comparan a escala de verdad).
- Voz: Supertonic (la del canal, en Actions). --sin-voz estima los tiempos para probar la imagen en local.
No toca render.py ni voz.py: solo usa voz._hablado y el mismo modelo.
"""
import json
import math
import os
import re
import subprocess
import sys
import tempfile

import cairocffi as cairo
import numpy as np
from shapely.geometry import box, shape, Polygon, MultiPolygon
from shapely.ops import unary_union
from shapely import affinity

AQUI= os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
FPS= 30

# ---------------------------------------------------------------- colores
FONDO= (0.035, 0.055, 0.12)
MAR= (0.06, 0.11, 0.24)
TIERRA= (0.20, 0.25, 0.38)
FRONTERA= (0.30, 0.37, 0.55)
BLANCO= (1, 1, 1)
AMARILLO= (1, 0.84, 0.04)


def hexrgb(h):
    h= h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


# ---------------------------------------------------------------- geografia
PAISES= {}
for f in json.load(open(os.path.join(AQUI, '..', 'assets', 'mapas', 'paises_110m.geojson'), encoding='utf-8'))['features']:
    p= f['properties']
    PAISES[p['a3']]= {'g': shape(f['geometry']).buffer(0), 'nombre': p['nombre'], 'cont': p['cont']}

UE27= 'AUT BEL BGR HRV CYP CZE DNK EST FIN FRA DEU GRC HUN IRL ITA LVA LTU LUX NLD POL PRT ROU SVK SVN ESP SWE'.split()  # Malta no sale a esta escala


def _parte(p):
    if isinstance(p, str):
        if p.startswith('cont:'):
            return unary_union([v['g'] for v in PAISES.values() if v['cont'] == p[5:]])
        return PAISES[p]['g']
    g= PAISES[p['a3']]['g']
    return g.intersection(unary_union([box(*c) for c in p['cajas']]))


def zona(partes):
    return unary_union([_parte(p) for p in partes]).buffer(0)


# Fronteras aproximadas en su maxima extension, montadas con paises actuales y recortes por coordenadas.
IMPERIOS= {
    'ESP': {'nombre': 'Imperio Español', 'color': '#ffd23f', 'km2': 13.7, 'origen': (-3.7, 40.4), 'lon0': -40,
            'partes': ['ESP', 'MEX', 'GTM', 'HND', 'SLV', 'NIC', 'CRI', 'PAN', 'CUB', 'DOM', 'PRI', 'COL', 'VEN', 'ECU', 'PER',
                       'BOL', 'CHL', 'ARG', 'PRY', 'URY', 'PHL', 'GNQ', 'TTO',
                       {'a3': 'USA', 'cajas': [(-125, 24, -90, 42), (-112, 42, -90, 49), (-88, 24, -80, 31)]}]},
    'QING': {'nombre': 'Imperio Qing', 'color': '#ff6b35', 'km2': 14.7, 'origen': (116.4, 39.9), 'lon0': 100,
             'partes': ['CHN', 'TWN', 'MNG', {'a3': 'RUS', 'cajas': [(127, 42, 142, 54), (89, 49.5, 99, 53.5)]},
                        {'a3': 'KAZ', 'cajas': [(74, 42, 88, 49)]}, {'a3': 'KGZ', 'cajas': [(76, 39, 81, 43)]}]},
    'RUS': {'nombre': 'Imperio Ruso', 'color': '#3ddc97', 'km2': 22.8, 'origen': (37.6, 55.75), 'lon0': 100,
            'partes': ['RUS', 'FIN', 'EST', 'LVA', 'LTU', 'BLR', 'UKR', 'MDA', 'GEO', 'ARM', 'AZE', 'KAZ', 'UZB', 'TKM',
                       'KGZ', 'TJK', {'a3': 'POL', 'cajas': [(19, 49, 25, 55)]}]},
    'MONG': {'nombre': 'Imperio Mongol', 'color': '#b57bff', 'km2': 24.0, 'origen': (102.8, 47.2), 'lon0': 80,
             'partes': ['MNG', 'CHN', 'KOR', 'PRK', 'KAZ', 'UZB', 'TKM', 'KGZ', 'TJK', 'AFG', 'IRN', 'IRQ', 'AZE', 'ARM',
                        'GEO', 'UKR', 'MDA', {'a3': 'TUR', 'cajas': [(35, 35, 45, 42.5)]},
                        {'a3': 'RUS', 'cajas': [(27, 40, 60, 58), (60, 40, 135, 56)]}]},
    'BRIT': {'nombre': 'Imperio Británico', 'color': '#ff4fa3', 'km2': 35.5, 'origen': (-0.1, 51.5), 'lon0': 10,
             'partes': ['GBR', 'IRL', 'CAN', 'AUS', 'NZL', 'IND', 'PAK', 'BGD', 'MMR', 'LKA', 'MYS', 'BRN', 'ZAF', 'NAM',
                        'BWA', 'LSO', 'SWZ', 'ZWE', 'ZMB', 'MWI', 'KEN', 'UGA', 'TZA', 'SDN', 'SDS', 'EGY', 'NGA', 'GHA',
                        'SLE', 'GMB', 'IRQ', 'JOR', 'ISR', 'PSX', 'CYP', 'GUY', 'BLZ', 'JAM', 'BHS', 'TTO', 'SOL', 'KWT',
                        'QAT', 'ARE', 'PNG', 'FJI', 'SLB']},
}
# formas sueltas para comparar
FORMAS= {
    'UE': {'nombre': 'Unión Europea', 'partes': UE27, 'color': '#5aa9ff', 'km2': 4.2},
    'ESP_HOY': {'nombre': 'España hoy', 'partes': ['ESP'], 'color': '#ffffff', 'km2': 0.5},
    'CHN_HOY': {'nombre': 'China hoy', 'partes': ['CHN', 'TWN'], 'color': '#ffffff', 'km2': 9.6},
    'RUS_HOY': {'nombre': 'Rusia hoy', 'partes': ['RUS'], 'color': '#ffffff', 'km2': 17.1},
    'AUS': {'nombre': 'Australia', 'partes': ['AUS'], 'color': '#5aa9ff', 'km2': 7.7},
    'AMN': {'nombre': 'América del Norte', 'partes': ['cont:North America'], 'color': '#5aa9ff', 'km2': 24.7},
    'AFR': {'nombre': 'África entera', 'partes': ['cont:Africa'], 'color': '#5aa9ff', 'km2': 30.4},
    'GBR_HOY': {'nombre': 'Reino Unido', 'partes': ['GBR'], 'color': '#ffffff', 'km2': 0.24},
    'ALASKA': {'nombre': 'Alaska', 'partes': [{'a3': 'USA', 'cajas': [(-180, 51, -129, 72)]}], 'color': '#ffffff', 'km2': 1.7},
}
for k, d in IMPERIOS.items():
    FORMAS[k]= d
_GEOM= {}


def cargar_zonas(g):
    """Zonas propias del guion ("zonas": {CLAVE: {nombre, color, km2, partes, [origen], [lon0], [cifra]}}).
    partes: codigos ISO a3 de paises, 'cont:Africa' o {a3, cajas: [[lon0, lat0, lon1, lat1], ...]} para recortar."""
    for k, d in (g.get('zonas') or {}).items():
        d= dict(d)
        d['partes']= [p if isinstance(p, str) else {'a3': p['a3'], 'cajas': [tuple(c) for c in p['cajas']]} for p in d['partes']]
        d.setdefault('color', '#5aa9ff')
        FORMAS[k]= d
        _GEOM.pop(k, None)
        if 'origen' not in d or 'lon0' not in d:
            c= geom(k).representative_point()
            d.setdefault('origen', (round(c.x, 2), round(c.y, 2)))
            d.setdefault('lon0', max(-180, min(180, round(c.x))))
        if 'km2' not in d:
            d['km2']= 0.0


def _claves(v):
    ks= list(v.get('imps', [])) + list(v.get('otros', [])) + list(v.get('encima', [])) + list(v.get('formas', []))
    return ks + ([v['imp']] if v.get('imp') else [])


def validar(ruta):
    """Errores de un guion antes de gastar tiempo de render (lista vacia = bien)."""
    try:
        g= json.load(open(ruta, encoding='utf-8'))
    except Exception as e:
        return [f'json roto: {e}']
    mal= []
    for k in ('id', 'titulo', 'descripcion', 'tags', 'beats'):
        if not g.get(k):
            mal.append(f'falta {k}')
    if mal:
        return mal
    try:
        cargar_zonas(g)
    except Exception as e:
        return [f'zonas: {type(e).__name__} {e}']
    if 'v' not in g['beats'][0]:
        mal.append('la primera frase debe abrir escena (campo v)')
    for i, b in enumerate(g['beats']):
        if not b.get('texto'):
            mal.append(f'frase {i}: sin texto')
        v= b.get('v')
        if v is None:
            continue
        if v.get('tipo') not in ESCENAS:
            mal.append(f'frase {i}: escena desconocida {v.get("tipo")}')
            continue
        for k in _claves(v):
            if k not in FORMAS:
                mal.append(f'frase {i}: zona desconocida {k}')
        if v['tipo'] in ('ficha',) and not v.get('imp'):
            mal.append(f'frase {i}: ficha sin imp')
        if v['tipo'] in ('compara', 'cuadros') and not v.get('formas'):
            mal.append(f'frase {i}: {v["tipo"]} sin formas')
        if v['tipo'] == 'barras' and not all(isinstance(x, list) and len(x) == 3 for x in v.get('items', [])):
            mal.append(f'frase {i}: barras necesita items [nombre, valor, color]')
        if v['tipo'] in ('dato', 'titulo') and not v.get('lineas'):
            mal.append(f'frase {i}: {v["tipo"]} sin lineas')
    palabras= sum(len(b.get('di', b['texto']).split()) for b in g['beats'])
    if g.get('formato_yt', 'largo') == 'largo' and not 1300 <= palabras <= 1800:
        mal.append(f'largo de {palabras} palabras (hacen falta 1300-1800; con Jorge 1.450 son unos 11 min)')
    return mal


def geom(k):
    if k not in _GEOM:
        _GEOM[k]= zona(FORMAS[k]['partes'])
    return _GEOM[k]


# ---------------------------------------------------------------- proyecciones
A1, A2, A3, A4= 1.340264, -0.081106, 0.000893, 0.003796
M= math.sqrt(3) / 2


def equal_earth(lon, lat):
    l= np.radians(lon)
    th= np.arcsin(M * np.sin(np.radians(lat)))
    t2= th * th
    t6= t2 * t2 * t2
    x= 2 * math.sqrt(3) * l * np.cos(th) / (3 * (9 * A4 * t6 * t2 + 7 * A3 * t6 + 3 * A2 * t2 + A1))
    y= th * (A1 + A2 * t2 + t6 * (A3 + A4 * t2))
    return x, y


def _girar(g, lon0):
    """Pasa la geometria a longitudes relativas a lon0, cortando por el nuevo antimeridiano."""
    g= affinity.translate(g, -lon0, 0)
    trozos= [g.intersection(box(-180, -90, 180, 90))]
    for d, c in ((-360, box(180, -90, 540, 90)), (360, box(-540, -90, -180, 90))):
        r= g.intersection(c)
        if not r.is_empty:
            trozos.append(affinity.translate(r, d, 0))
    return unary_union(trozos)


def _anillos(g):
    polis= list(g.geoms) if hasattr(g, 'geoms') else [g]
    out= []
    for p in polis:
        if isinstance(p, Polygon):
            out.append([np.array(p.exterior.coords)] + [np.array(i.coords) for i in p.interiors])
        elif hasattr(p, 'geoms'):
            out+= _anillos(p)
    return out


_PROY= {}


def proyectada(clave, g, lon0):
    """Anillos ya proyectados (Equal Earth) de una geometria, en coordenadas de mapa."""
    k= (clave, round(lon0))
    if k not in _PROY:
        res= []
        for poli in _anillos(_girar(g.segmentize(1.0), lon0)):
            res.append([np.column_stack(equal_earth(a[:, 0], a[:, 1])) for a in poli])
        _PROY[k]= res
    return _PROY[k]


_DENS= {}


def densa(clave, g):
    if clave not in _DENS:
        _DENS[clave]= [[np.radians(a) for a in poli] for poli in _anillos(g.segmentize(2.0))]
    return _DENS[clave]


def mundo():
    return {a: v['g'] for a, v in PAISES.items() if a != 'ATA'}


# ---------------------------------------------------------------- dibujo basico
def ease(x):
    x= min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def rr(ctx, x, y, w, h, r):
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()


def texto(ctx, s, x, y, tam, fuente='Anton', color=BLANCO, alinear='c', borde=0, alfa=1.0, color_borde=(0, 0, 0)):
    ctx.select_font_face(fuente, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(tam)
    e= ctx.text_extents(s)
    if alinear == 'c':
        x-= e[4] / 2
    elif alinear == 'd':
        x-= e[4]
    ctx.move_to(x, y)
    ctx.text_path(s)
    if borde:
        ctx.set_source_rgba(*color_borde, alfa)
        ctx.set_line_width(borde)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke_preserve()
    ctx.set_source_rgba(*color, alfa)
    ctx.fill()
    return e[4]


def ancho(ctx, s, tam, fuente='Anton'):
    ctx.select_font_face(fuente, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(tam)
    return ctx.text_extents(s)[4]


def km(v, unidad=None):
    if unidad is not None:  # barras de otra magnitud (personas, anos, toneladas...)
        return (f'{v:,.10g}'.replace(',', '.') + (' ' + unidad if unidad else '')) if not isinstance(v, str) else v
    return f'{v:.1f}'.replace('.', ',') + ' M km²'


def cifra(k):
    """Texto bajo cada forma: su 'cifra' si el guion la da (poblacion, PIB...), si no la superficie."""
    return FORMAS[k].get('cifra') or km(FORMAS[k]['km2'])


def fondo(ctx, W, H):
    g= cairo.RadialGradient(W / 2, H * 0.45, 0, W / 2, H * 0.45, max(W, H) * 0.8)
    g.add_color_stop_rgb(0, 0.07, 0.10, 0.22)
    g.add_color_stop_rgb(1, *FONDO)
    ctx.set_source(g)
    ctx.paint()


# ---------------------------------------------------------------- mapa plano
class Vista:
    """Encuadre del mapa: centro (x, y) en coordenadas Equal Earth y escala en px por unidad."""
    def __init__(self, cx, cy, esc):
        self.cx, self.cy, self.esc= cx, cy, esc

    def mezcla(self, o, f):
        # interpolo la escala en logaritmo para que el zoom vaya suave
        return Vista(self.cx + (o.cx - self.cx) * f, self.cy + (o.cy - self.cy) * f,
                     math.exp(math.log(self.esc) + (math.log(o.esc) - math.log(self.esc)) * f))


def vista_de(caja, lon0, W, H, margen=1.12, arriba=0.0):
    lon_a, lat_a, lon_b, lat_b= caja
    # paso las longitudes al marco girado y muestreo el borde para encuadrar bien
    lons= np.linspace(lon_a, lon_b if lon_b > lon_a else lon_b + 360, 40)
    lons= (lons - lon0 + 180) % 360 - 180
    lats= np.linspace(lat_a, lat_b, 40)
    LO, LA= np.meshgrid(lons, lats)
    x, y= equal_earth(LO.ravel(), LA.ravel())
    ancho_u, alto_u= (x.max() - x.min()) * margen, (y.max() - y.min()) * margen
    util= H * (1 - arriba)
    esc= min(W / ancho_u, util / alto_u)
    return Vista((x.max() + x.min()) / 2, (y.max() + y.min()) / 2 + arriba * H / esc / 2, esc)


def _camino(ctx, anillos, v, W, H, dx=0.0, dy=0.0):
    for poli in anillos:
        for a in poli:
            px= W / 2 + (a[:, 0] - v.cx) * v.esc + dx
            py= H / 2 - (a[:, 1] - v.cy) * v.esc + dy
            ctx.move_to(px[0], py[0])
            for i in range(1, len(px)):
                ctx.line_to(px[i], py[i])
            ctx.close_path()


def pinta_mapa(ctx, W, H, v, lon0, capas, alfa_base=1.0):
    """capas: lista de (clave, color, alfa, revelar) con revelar = None o (x, y, radio) en px."""
    # oceano con la silueta del mundo (contorno de la proyeccion)
    lat= np.linspace(-90, 90, 90)
    xd, yd= equal_earth(np.full_like(lat, 180.0), lat)
    xi, yi= equal_earth(np.full_like(lat, -180.0), lat[::-1])
    borde= np.concatenate([np.column_stack([xd, yd]), np.column_stack([xi, yi])])
    _camino(ctx, [[borde]], v, W, H)
    ctx.set_source_rgba(*MAR, alfa_base)
    ctx.fill()
    # reticula
    ctx.set_line_width(1)
    ctx.set_source_rgba(1, 1, 1, 0.05 * alfa_base)
    for lo in range(-180, 181, 30):
        la= np.linspace(-90, 90, 60)
        x, y= equal_earth(np.full_like(la, float(lo)), la)
        _linea(ctx, x, y, v, W, H)
    for la in range(-60, 61, 30):
        lo= np.linspace(-180, 180, 90)
        x, y= equal_earth(lo, np.full_like(lo, float(la)))
        _linea(ctx, x, y, v, W, H)
    # paises de hoy
    for a, g in mundo().items():
        an= proyectada(a, g, lon0)
        _camino(ctx, an, v, W, H)
        ctx.set_source_rgba(*TIERRA, alfa_base)
        ctx.fill_preserve()
        ctx.set_source_rgba(*FRONTERA, alfa_base)
        ctx.set_line_width(1.0)
        ctx.stroke()
    for clave, color, alfa, revelar in capas:
        if alfa <= 0:
            continue
        an= proyectada('F:' + clave, geom(clave), lon0)
        ctx.save()
        if revelar:
            ctx.arc(revelar[0], revelar[1], max(revelar[2], 0.1), 0, 2 * math.pi)
            ctx.clip()
        c= hexrgb(color) if isinstance(color, str) else color
        _camino(ctx, an, v, W, H)
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        ctx.set_source_rgba(*c, 0.82 * alfa)
        ctx.fill_preserve()
        ctx.set_source_rgba(1, 1, 1, 0.9 * alfa)
        ctx.set_line_width(2.2)
        ctx.stroke()
        ctx.restore()


def _linea(ctx, x, y, v, W, H):
    px= W / 2 + (x - v.cx) * v.esc
    py= H / 2 - (y - v.cy) * v.esc
    ctx.move_to(px[0], py[0])
    for i in range(1, len(px)):
        ctx.line_to(px[i], py[i])
    ctx.stroke()


def a_pantalla(lon, lat, lon0, v, W, H):
    l= (lon - lon0 + 180) % 360 - 180
    x, y= equal_earth(np.array([l]), np.array([lat]))
    return W / 2 + (x[0] - v.cx) * v.esc, H / 2 - (y[0] - v.cy) * v.esc


# ---------------------------------------------------------------- globo 3D (ortografica con luz)
def _orto(lon, lat, lon0, lat0):
    d= lon - lon0
    cl= np.cos(lat)
    x= cl * np.sin(d)
    y= math.cos(lat0) * np.sin(lat) - math.sin(lat0) * cl * np.cos(d)
    z= math.sin(lat0) * np.sin(lat) + math.cos(lat0) * cl * np.cos(d)
    return x, y, z


def _recorta_hemisferio(x, y, z):
    """Sutherland-Hodgman contra el plano z=0; entre salida y entrada sigo el borde del disco."""
    n= len(x)
    vis= z >= 0
    if vis.all():
        return np.column_stack([x, y])
    if not vis.any():
        return None
    pts, salida= [], None
    for i in range(n):
        j= (i + 1) % n
        a_in, b_in= vis[i], vis[j]
        if a_in:
            pts.append((x[i], y[i]))
        if a_in != b_in:
            t= z[i] / (z[i] - z[j])
            px, py= x[i] + t * (x[j] - x[i]), y[i] + t * (y[j] - y[i])
            r= math.hypot(px, py) or 1
            px, py= px / r, py / r
            if a_in:
                salida= math.atan2(py, px)
                pts.append((px, py))
            else:
                ent= math.atan2(py, px)
                if salida is not None:
                    d= (ent - salida + math.pi) % (2 * math.pi) - math.pi
                    for k in range(1, max(2, int(abs(d) / 0.05))):
                        ang= salida + d * k / max(2, int(abs(d) / 0.05))
                        pts.append((math.cos(ang), math.sin(ang)))
                pts.append((px, py))
                salida= None
    if len(pts) < 3:
        return None
    return np.array(pts)


def pinta_globo(ctx, gx, gy, R, lon0, lat0, capas, gira_txt=None):
    lo0, la0= math.radians(lon0), math.radians(lat0)
    # halo de atmosfera
    g= cairo.RadialGradient(gx, gy, R * 0.95, gx, gy, R * 1.18)
    g.add_color_stop_rgba(0, 0.35, 0.6, 1, 0.45)
    g.add_color_stop_rgba(1, 0.35, 0.6, 1, 0)
    ctx.set_source(g)
    ctx.arc(gx, gy, R * 1.18, 0, 2 * math.pi)
    ctx.fill()
    # oceano
    g= cairo.RadialGradient(gx - R * 0.35, gy - R * 0.35, R * 0.1, gx, gy, R)
    g.add_color_stop_rgb(0, 0.13, 0.27, 0.52)
    g.add_color_stop_rgb(1, 0.04, 0.09, 0.22)
    ctx.set_source(g)
    ctx.arc(gx, gy, R, 0, 2 * math.pi)
    ctx.fill()

    def poligonos(clave, gm):
        for poli in densa(clave, gm):
            for a in poli:
                x, y, z= _orto(a[:, 0], a[:, 1], lo0, la0)
                r= _recorta_hemisferio(x, y, z)
                if r is None:
                    continue
                ctx.move_to(gx + R * r[0, 0], gy - R * r[0, 1])
                for p in r[1:]:
                    ctx.line_to(gx + R * p[0], gy - R * p[1])
                ctx.close_path()

    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    for a, gm in mundo().items():
        poligonos(a, gm)
        ctx.set_source_rgb(0.34, 0.42, 0.58)
        ctx.fill_preserve()
        ctx.set_source_rgba(0.18, 0.24, 0.38, 0.9)
        ctx.set_line_width(0.8)
        ctx.stroke()
    # reticula
    ctx.set_source_rgba(1, 1, 1, 0.07)
    ctx.set_line_width(1)
    for lo in range(-180, 180, 30):
        la= np.radians(np.linspace(-90, 90, 60))
        _linea_globo(ctx, np.full_like(la, math.radians(lo)), la, lo0, la0, gx, gy, R)
    for la in range(-60, 61, 30):
        lo= np.radians(np.linspace(-180, 180, 120))
        _linea_globo(ctx, lo, np.full_like(lo, math.radians(la)), lo0, la0, gx, gy, R)
    for clave, color, alfa in capas:
        if alfa <= 0:
            continue
        poligonos('F:' + clave, geom(clave))
        c= hexrgb(color)
        ctx.set_source_rgba(*c, 0.85 * alfa)
        ctx.fill_preserve()
        ctx.set_source_rgba(1, 1, 1, 0.85 * alfa)
        ctx.set_line_width(1.6)
        ctx.stroke()
    # luz y sombra para el volumen
    g= cairo.RadialGradient(gx - R * 0.45, gy - R * 0.5, 0, gx - R * 0.2, gy - R * 0.2, R * 1.25)
    g.add_color_stop_rgba(0, 1, 1, 1, 0.22)
    g.add_color_stop_rgba(0.45, 1, 1, 1, 0.0)
    g.add_color_stop_rgba(0.8, 0, 0, 0.05, 0.25)
    g.add_color_stop_rgba(1, 0, 0, 0.05, 0.6)
    ctx.set_source(g)
    ctx.arc(gx, gy, R, 0, 2 * math.pi)
    ctx.fill()


def _linea_globo(ctx, lo, la, lo0, la0, gx, gy, R):
    x, y, z= _orto(lo, la, lo0, la0)
    pen= False
    for i in range(len(x)):
        if z[i] < 0:
            pen= False
            continue
        if pen:
            ctx.line_to(gx + R * x[i], gy - R * y[i])
        else:
            ctx.move_to(gx + R * x[i], gy - R * y[i])
            pen= True
    ctx.stroke()


# ---------------------------------------------------------------- escenas
def _imp(k):
    return FORMAS[k]


def esc_globo(ctx, W, H, t, dur, v):
    fondo(ctx, W, H)
    _estrellas(ctx, W, H)
    lon= v.get('lon', [0, 60])
    lat= v.get('lat', [20, 30])
    f= t / max(dur, 0.1)
    L= lon[0] + (lon[1] - lon[0]) * f
    La= lat[0] + (lat[1] - lat[0]) * f
    z= v.get('zoom', [1.0, 1.0])
    zz= z[0] + (z[1] - z[0]) * ease(f)
    R= min(W, H) * 0.42 * zz
    gx, gy= W / 2, H / 2 + (H * 0.04 if W > H else H * 0.02)
    capas= []
    imps= v.get('imps', [])
    for i, k in enumerate(imps):
        if v.get('aparece'):
            a= ease((t - 0.6 - i * v.get('cada', 0.9)) / 0.5)
        else:
            a= 1.0
        capas.append((k, _imp(k)['color'], a))
    pinta_globo(ctx, gx, gy, R, L, La, capas)
    if v.get('leyenda'):
        _leyenda(ctx, W, H, imps, t, v)


def _estrellas(ctx, W, H):
    rng= np.random.default_rng(7)
    for _ in range(140):
        x, y, r, a= rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0.6, 1.8), rng.uniform(0.15, 0.6)
        ctx.set_source_rgba(1, 1, 1, a)
        ctx.arc(x, y, r, 0, 2 * math.pi)
        ctx.fill()


def _leyenda(ctx, W, H, imps, t, v):
    vertical= H > W
    tam= 34 if not vertical else 40
    y= H * 0.2 if not vertical else H * 0.74
    x= 60 if not vertical else 80
    for i, k in enumerate(imps):
        a= ease((t - 0.6 - i * v.get('cada', 0.9)) / 0.5) if v.get('aparece') else 1
        if a <= 0:
            continue
        d= _imp(k)
        ctx.set_source_rgba(*hexrgb(d['color']), a)
        rr(ctx, x, y - tam * 0.8, tam * 0.8, tam * 0.8, 6)
        ctx.fill()
        texto(ctx, d['nombre'], x + tam * 1.2, y, tam, 'Anton', BLANCO, 'i', borde=6, alfa=a)
        y+= tam * 1.5


def esc_mapa(ctx, W, H, t, dur, v):
    fondo(ctx, W, H)
    k= v.get('imp')
    lon0= v.get('lon0', _imp(k)['lon0'] if k else 0)
    arriba= 0.12 if W > H else 0.18
    fin= vista_de(v['caja'], lon0, W, H, margen=v.get('margen', 1.1), arriba=arriba) if 'caja' in v else vista_de((-180, -58, 180, 80), lon0, W, H, 1.02, arriba)
    ini= vista_de(v['caja0'], lon0, W, H, 1.1, arriba) if 'caja0' in v else fin
    vv= ini.mezcla(fin, ease(t / v.get('t_cam', 1.6)))
    capas= []
    for o in v.get('otros', []):
        capas.append((o, _imp(o)['color'], 0.35, None))
    if k:
        rev= None
        if v.get('crece', True):
            ox, oy= a_pantalla(*_imp(k)['origen'], lon0, vv, W, H)
            rad= math.hypot(W, H) * 1.2 * ease((t - 0.3) / v.get('t_crece', 2.6))
            rev= (ox, oy, rad)
        capas.append((k, _imp(k)['color'], 1.0, rev))
    for o in v.get('encima', []):
        a= ease((t - v.get('t_encima', 2.0)) / 0.6)
        capas.append((o, FORMAS[o]['color'], a, None))
    pinta_mapa(ctx, W, H, vv, lon0, capas)
    for et in v.get('etiquetas', []):
        a= ease((t - et.get('t', 1.0)) / 0.4)
        x, y= a_pantalla(et['lon'], et['lat'], lon0, vv, W, H)
        texto(ctx, et['txt'], x, y, et.get('tam', 40 if W > H else 46), 'Anton', BLANCO, 'c', borde=8, alfa=a)


def esc_compara(ctx, W, H, t, dur, v):
    """Siluetas a la misma escala, una al lado de otra (o una debajo de otra en vertical)."""
    fondo(ctx, W, H)
    claves= v['formas']
    vertical= H > W
    datos= []
    for k in claves:
        g= geom(k)
        lon0= g.centroid.x
        an= proyectada('F:' + k, g, lon0)
        todos= np.concatenate([a for p in an for a in p])
        mn, mx= todos.min(axis=0), todos.max(axis=0)
        datos.append((k, an, mn, mx))
    n= len(datos)
    zona_alto= H * (0.56 if not vertical else 0.22)
    hueco= (W * 0.86) / n if not vertical else W * 0.86
    esc= min(min(hueco / (mx[0] - mn[0]), zona_alto / (mx[1] - mn[1])) for _, _, mn, mx in datos) * 0.92
    for i, (k, an, mn, mx) in enumerate(datos):
        a= ease((t - 0.3 - i * 0.7) / 0.6)
        if a <= 0:
            continue
        if not vertical:
            cx= W * 0.07 + hueco * (i + 0.5)
            cy= H * 0.52
        else:
            cx= W / 2
            cy= H * (0.30 + i * 0.26)
        vv= Vista((mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, esc)
        ctx.save()
        ctx.translate(cx - W / 2, cy - H / 2)
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        _camino(ctx, an, vv, W, H)
        ctx.set_source_rgba(*hexrgb(FORMAS[k]['color']), 0.88 * a)
        ctx.fill_preserve()
        ctx.set_source_rgba(1, 1, 1, 0.9 * a)
        ctx.set_line_width(2)
        ctx.stroke()
        ctx.restore()
        alto_px= (mx[1] - mn[1]) * esc
        ty= cy + alto_px / 2 + (60 if not vertical else 50)
        texto(ctx, FORMAS[k]['nombre'], cx, ty, 44 if not vertical else 50, 'Anton', BLANCO, 'c', borde=8, alfa=a)
        texto(ctx, cifra(k), cx, ty + (52 if not vertical else 58), 38 if not vertical else 44, 'Baloo 2', AMARILLO, 'c', borde=7, alfa=a)
    if v.get('grande'):
        a= ease((t - 0.4 - n * 0.7) / 0.5)
        s= 1 + 0.25 * (1 - a)
        ctx.save()
        cx, cy= (W / 2, H * 0.2) if not vertical else (W / 2, H * 0.135)
        ctx.translate(cx, cy)
        ctx.scale(s, s)
        texto(ctx, v['grande'], 0, 0, 120 if not vertical else 140, 'Anton', AMARILLO, 'c', borde=14, alfa=a)
        ctx.restore()


def esc_cuadros(ctx, W, H, t, dur, v):
    """Superficies como cuadrados a escala (para imperios repartidos por todo el mundo)."""
    fondo(ctx, W, H)
    claves= v['formas']
    vertical= H > W
    lados= [math.sqrt(FORMAS[k]['km2']) for k in claves]
    hueco= 70
    esc= min((W * 0.86 - hueco * (len(claves) - 1)) / sum(lados), (H * (0.5 if not vertical else 0.26)) / max(lados))
    x= (W - (sum(lados) * esc + hueco * (len(claves) - 1))) / 2
    base= H * (0.74 if not vertical else 0.53)
    for i, (k, l) in enumerate(zip(claves, lados)):
        a= ease((t - 0.3 - i * 0.7) / 0.6)
        lp= l * esc
        if a > 0:
            s= ease((t - 0.3 - i * 0.7) / 0.8)
            ctx.set_source_rgba(*hexrgb(FORMAS[k]['color']), 0.9 * a)
            ctx.rectangle(x, base - lp * s, lp, lp * s)
            ctx.fill_preserve()
            ctx.set_source_rgba(1, 1, 1, 0.9 * a)
            ctx.set_line_width(2)
            ctx.stroke()
            cx= x + lp / 2
            tam= 40 if not vertical else (34 if len(claves) > 2 else 44)
            texto(ctx, FORMAS[k]['nombre'], cx, base + 58, tam, 'Anton', BLANCO, 'c', borde=8, alfa=a)
            texto(ctx, cifra(k), cx, base + 58 + tam * 1.2, tam * 0.9, 'Baloo 2', AMARILLO, 'c', borde=7, alfa=a)
        x+= lp + hueco
    if v.get('grande'):
        a= ease((t - 0.4 - len(claves) * 0.7) / 0.5)
        sc= 1 + 0.25 * (1 - a)
        ctx.save()
        ctx.translate(W / 2, H * (0.17 if not vertical else 0.2))
        ctx.scale(sc, sc)
        texto(ctx, v['grande'], 0, 0, 120 if not vertical else 130, 'Anton', AMARILLO, 'c', borde=14, alfa=a)
        ctx.restore()


def esc_ficha(ctx, W, H, t, dur, v):
    """Ficha de puesto: numero, nombre, superficie que sube como contador y anos."""
    k= v['imp']
    d= _imp(k)
    fondo(ctx, W, H)
    lon0= d['lon0']
    vv= vista_de((-180, -58, 180, 80), lon0, W, H, 1.02)
    pinta_mapa(ctx, W, H, vv, lon0, [(k, d['color'], 0.9, None)], alfa_base=0.35)
    ctx.set_source_rgba(*FONDO, 0.55)
    ctx.paint()
    vertical= H > W
    a= ease(t / 0.5)
    s= 1 + 0.4 * (1 - ease(t / 0.45))
    ctx.save()
    ctx.translate(W / 2, H * (0.36 if not vertical else 0.36))
    ctx.scale(s, s)
    texto(ctx, f'#{v["puesto"]}', 0, 0, 230 if not vertical else 260, 'Anton', hexrgb(d['color']), 'c', borde=16, alfa=a)
    ctx.restore()
    texto(ctx, d['nombre'].upper(), W / 2, H * (0.52 if not vertical else 0.47), 110 if not vertical else 104, 'Anton', BLANCO, 'c', borde=12, alfa=ease((t - 0.3) / 0.4))
    c= d['km2'] * ease((t - 0.5) / 1.4)
    texto(ctx, d['cifra'] if d.get('cifra') else km(c), W / 2, H * (0.66 if not vertical else 0.56), 90 if not vertical else 96, 'Anton', AMARILLO, 'c', borde=11, alfa=ease((t - 0.5) / 0.3))
    if v.get('anos'):
        texto(ctx, v['anos'], W / 2, H * (0.76 if not vertical else 0.63), 52 if not vertical else 58, 'Baloo 2', BLANCO, 'c', borde=8, alfa=ease((t - 1.6) / 0.4))


def esc_dato(ctx, W, H, t, dur, v):
    """Tarjeta de texto grande (dato loco, preguntas, cifras)."""
    fondo(ctx, W, H)
    if v.get('imp'):
        d= _imp(v['imp'])
        vv= vista_de((-180, -58, 180, 80), d['lon0'], W, H, 1.02)
        pinta_mapa(ctx, W, H, vv, d['lon0'], [(v['imp'], d['color'], 0.9, None)], alfa_base=0.25)
        ctx.set_source_rgba(*FONDO, 0.7)
        ctx.paint()
    vertical= H > W
    y= H * (0.3 if not vertical else 0.3)
    if v.get('etiqueta'):
        tam= 46 if not vertical else 54
        w= ancho(ctx, v['etiqueta'], tam) + 50
        a= ease(t / 0.3)
        ctx.set_source_rgba(*AMARILLO, a)
        rr(ctx, W / 2 - w / 2, y - tam * 1.05, w, tam * 1.45, 14)
        ctx.fill()
        texto(ctx, v['etiqueta'], W / 2, y, tam, 'Anton', (0.05, 0.05, 0.1), 'c', alfa=a)
        y+= tam * 2.2
    for i, l in enumerate(v.get('lineas', [])):
        a= ease((t - 0.35 - i * 0.45) / 0.4)
        tam= l.get('tam', 84 if not vertical else 86)
        col= AMARILLO if l.get('amarillo') else BLANCO
        texto(ctx, l['txt'], W / 2, y + tam * 0.4, tam, l.get('fuente', 'Anton'), col, 'c', borde=12, alfa=a)
        y+= tam * 1.3


def esc_barras(ctx, W, H, t, dur, v):
    fondo(ctx, W, H)
    items= v['items']
    vertical= H > W
    mx= max(i[1] for i in items)
    x0= W * (0.30 if not vertical else 0.08)
    ancho_max= W * (0.50 if not vertical else 0.66)
    y0= H * (0.2 if not vertical else 0.24)
    paso= (H * (0.72 if not vertical else 0.56)) / len(items)
    alto= paso * 0.7
    for i, (nombre, val, color) in enumerate(items):
        a= ease((t - 0.3 - i * v.get('cada', 0.6)) / 0.5)
        if a <= 0:
            continue
        y= y0 + i * paso
        w= ancho_max * val / mx * ease((t - 0.3 - i * v.get('cada', 0.6)) / 0.9)
        ctx.set_source_rgba(*hexrgb(color), 0.92 * a)
        rr(ctx, x0, y, max(w, 12), alto, 10)
        ctx.fill()
        tam= alto * 0.55
        if not vertical:
            texto(ctx, nombre, x0 - 24, y + alto * 0.72, tam, 'Anton', BLANCO, 'd', borde=8, alfa=a)
            texto(ctx, km(val, v.get('unidad')), x0 + w + 18, y + alto * 0.72, tam * 0.9, 'Baloo 2', AMARILLO, 'i', borde=7, alfa=a)
        else:
            texto(ctx, f'{nombre}  ·  {km(val, v.get("unidad"))}', x0 + 18, y + alto * 0.7, tam * 0.85, 'Anton', BLANCO, 'i', borde=8, alfa=a)
        if i + 1 == v.get('marca'):
            ctx.set_source_rgba(*AMARILLO, a)
            ctx.set_line_width(5)
            rr(ctx, x0 - 8, y - 8, max(w, 12) + 16, alto + 16, 14)
            ctx.stroke()


def esc_titulo(ctx, W, H, t, dur, v):
    esc_globo(ctx, W, H, t, dur, v)
    vertical= H > W
    ctx.set_source_rgba(*FONDO, 0.35)
    ctx.paint()
    y= H * (0.18 if not vertical else 0.2)
    for i, l in enumerate(v['lineas']):
        a= 1.0  # el cartel se ve entero desde el primer fotograma
        tam= l.get('tam', 96 if not vertical else 104)
        texto(ctx, l['txt'], W / 2, y, tam, 'Anton', AMARILLO if l.get('amarillo') else BLANCO, 'c', borde=14, alfa=a)
        y+= tam * 1.2


ESCENAS= {'cuadros': esc_cuadros, 'globo': esc_globo, 'mapa': esc_mapa, 'compara': esc_compara, 'ficha': esc_ficha, 'dato': esc_dato,
          'barras': esc_barras, 'titulo': esc_titulo}
# a partir de que segundo la escena ya no cambia (solo subtitulos encima): la cacheo
ESTATICA= {'cuadros': 4.0, 'mapa': 7.0, 'compara': 4.5, 'ficha': 2.2, 'dato': 4.0, 'barras': 5.0}


# ---------------------------------------------------------------- capa fija (puesto) y subtitulos
def pinta_hud(ctx, W, H, hud):
    if not hud:
        return
    vertical= H > W
    tam= 34 if not vertical else 44
    w= ancho(ctx, hud['txt'], tam) + 48
    x, y= (40, 34) if not vertical else ((W - w) / 2, 150)
    ctx.set_source_rgba(0.03, 0.05, 0.12, 0.78)
    rr(ctx, x, y, w, tam * 1.6, 16)
    ctx.fill()
    if hud.get('color'):
        ctx.set_source_rgb(*hexrgb(hud['color']))
        rr(ctx, x, y, 12, tam * 1.6, 6)
        ctx.fill()
    texto(ctx, hud['txt'], x + 28, y + tam * 1.15, tam, 'Anton', BLANCO, 'i')
    if hud.get('nota') and not vertical:
        texto(ctx, hud['nota'], W - 40, H - 22, 22, 'Baloo 2', (0.75, 0.8, 0.95), 'd', alfa=0.8)


def grupos_sub(marcas, maxp=6):
    """Junta las palabras en trozos cortos que no cruzan el final de frase."""
    out, act= [], []
    for w in marcas:
        act.append(w)
        if len(act) >= maxp or re.search(r'[.!?;:]$', w['p']) or (re.search(r',$', w['p']) and len(act) >= 3):
            out.append(act)
            act= []
    if act:
        out.append(act)
    return out


def pinta_sub(ctx, W, H, grupo, t):
    if not grupo:
        return
    vertical= H > W
    tam= 50 if not vertical else 66
    palabras= [w['p'] for w in grupo]
    esp= ancho(ctx, ' ', tam, 'Baloo 2')
    anchos= [ancho(ctx, p, tam, 'Baloo 2') for p in palabras]
    total= sum(anchos) + esp * (len(palabras) - 1)
    lineas= [list(range(len(palabras)))]
    if total > W * 0.84:
        mitad, acc= 0, 0
        for i, a in enumerate(anchos):
            acc+= a + esp
            if acc > total / 2:
                mitad= i + 1
                break
        lineas= [list(range(mitad)), list(range(mitad, len(palabras)))]
    y= H - (90 if not vertical else H * 0.27) - (len(lineas) - 1) * tam * 1.15
    for ln in lineas:
        w= sum(anchos[i] for i in ln) + esp * (len(ln) - 1)
        x= (W - w) / 2
        for i in ln:
            act= grupo[i]['ini'] <= t
            texto(ctx, palabras[i], x, y, tam, 'Baloo 2', AMARILLO if act and grupo[i]['fin'] >= t - 0.05 else BLANCO, 'i', borde=10)
            x+= anchos[i] + esp
        y+= tam * 1.15


# ---------------------------------------------------------------- voz
_super= {}
TONO_GUION= [None]  # tono_voz del guion en curso


def _beats_edge(beats, idioma, tmp):
    """Cada frase con edge-tts (Jorge en espanol) y sus tiempos de palabra reales. VozFallo si se cae."""
    import voz
    import soundfile as sf
    nombre= voz.VOCES_EDGE[idioma][0]
    piezas= []
    for n, b in enumerate(beats):
        w= os.path.join(tmp, f'b{n:03d}.wav')
        d, pal= voz.sintetizar(voz._hablado(b.get('di', b['texto']), idioma), idioma, w, 'edge', nombre)
        a, sr= sf.read(w, dtype='float32')
        piezas.append((a if a.ndim == 1 else a.mean(axis=1), sr, pal))
    print('voz: edge-tts', nombre, flush=True)
    return piezas


def _beats_qwen(beats, idioma, tmp, tono):
    """Voz Qwen3-TTS elegida el 23/11 (misma voz en es y en), con tiempos de palabra de whisper. VozFallo si falla."""
    import voz
    import soundfile as sf
    piezas= []
    for n, b in enumerate(beats):
        w= os.path.join(tmp, f'q{n:03d}.wav')
        _, por= voz.sintetizar_qwen([b.get('di', b['texto'])], idioma, w, tono)
        a, sr= sf.read(w, dtype='float32')
        piezas.append((a if a.ndim == 1 else a.mean(axis=1), sr, por[0]))
    print('voz: qwen', idioma, tono, flush=True)
    return piezas


def _beats_super(beats, idioma):
    import voz
    if 'm' not in _super:
        from supertonic import TTS
        _super['m']= TTS(model='supertonic-3')
        _super['sr']= getattr(_super['m'], 'sample_rate', 44100)
    tts, sr= _super['m'], _super['sr']
    estilo= tts.get_voice_style(os.environ.get('VOZ_SUPERTONIC', 'M5'))
    piezas= []
    for b in beats:
        wav, _ = tts.synthesize(voz._hablado(b.get('di', b['texto']), idioma), voice_style=estilo, lang=idioma)
        a= np.asarray(wav, dtype=np.float32).squeeze()
        nz= np.where(np.abs(a) > 0.01)[0]
        if len(nz):
            a= a[max(0, nz[0] - int(sr * 0.06)):nz[-1] + int(sr * 0.06)]
        piezas.append((a, sr, None))
    print('voz: supertonic', os.environ.get('VOZ_SUPERTONIC', 'M5'), flush=True)
    return piezas


def voz_beats(beats, wav_out, sin_voz=False, idioma='es'):
    """Una locucion por frase; devuelve (duracion, [ (ini, fin, marcas) por frase ]).
    MOTOR_VOZ=edge_tts y espanol: Jorge (edge-tts) para todo el video; si edge falla, el video entero con Supertonic.
    Ingles o MOTOR_VOZ distinto: Supertonic (VOZ_SUPERTONIC, M5 por defecto)."""
    import wave
    sr= 44100
    if sin_voz:
        piezas= [(np.zeros(int(sr * max(1.0, len(b.get('di', b['texto'])) / 14.5)), dtype=np.float32), sr, None) for b in beats]
    else:
        piezas= None
        quiere_qwen= os.environ.get('VOZ_ES') == 'qwen' if idioma == 'es' else os.environ.get('VOZ_EN') != 'supertonic'
        if quiere_qwen and os.environ.get('MOTOR_VOZ') == 'edge_tts':
            import voz
            try:
                piezas= _beats_qwen(beats, idioma, tempfile.mkdtemp(), voz.tono_de({'tono_voz': TONO_GUION[0], 'serie': 'lab'}))
            except voz.VozFallo as e:
                print('qwen fallo, uso la voz de reserva:', e, flush=True)
        if piezas is None and os.environ.get('MOTOR_VOZ') == 'edge_tts' and idioma == 'es':
            import voz
            try:
                piezas= _beats_edge(beats, idioma, tempfile.mkdtemp())
            except voz.VozFallo as e:
                print('edge-tts no responde, uso Supertonic para todo el video:', e, flush=True)
        if piezas is None:
            piezas= _beats_super(beats, idioma)
    sr= piezas[0][1]
    res, trozos, t0= [], [], 0.0
    for b, (a, sra, pal) in zip(beats, piezas):
        if sra != sr:  # por si acaso: mismo ritmo de muestreo en todo el video
            a= np.interp(np.linspace(0, len(a), int(len(a) * sr / sra), endpoint=False), np.arange(len(a)), a).astype(np.float32)
        d= len(a) / sr
        toks= b['texto'].split()
        marcas= []
        if pal and len(pal) == len(toks):
            # tiempos reales de edge-tts con las palabras tal y como se escriben en pantalla
            marcas= [{'p': w, 'ini': t0 + p['ini'], 'fin': t0 + min(p['fin'], d)} for w, p in zip(toks, pal)]
        else:
            pesos= [max(1, len(re.sub(r'\W', '', w))) for w in toks]
            tot, q= sum(pesos), 0.0
            for w, pw in zip(toks, pesos):
                marcas.append({'p': w, 'ini': t0 + d * q / tot, 'fin': t0 + d * (q + pw) / tot})
                q+= pw
        pausa= b.get('pausa', 0.25)
        res.append((t0, t0 + d, marcas))
        trozos+= [a, np.zeros(int(sr * pausa), dtype=np.float32)]
        t0+= d + pausa
    audio= np.concatenate(trozos)
    pico= np.abs(audio).max() or 1
    audio= np.clip(audio / pico * 0.89, -1, 1)
    with wave.open(wav_out, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((audio * 32767).astype(np.int16).tobytes())
    return t0, res


# ---------------------------------------------------------------- montaje
def capitulos_validos(caps, total):
    """Reglas de YouTube para que los capitulos funcionen (idea de yt-chapters, MIT): el primero en 0:00, al menos 3 y
    cada uno de 10 s o mas. Si un capitulo dura menos de 10 s se junta con el anterior; si quedan menos de 3, no se ponen
    (un bloque invalido se queda en la descripcion sin hacer nada)."""
    out= []
    for ini, nombre in sorted(caps):
        if not out:
            out.append([0.0, nombre])
        elif ini - out[-1][0] >= 10:
            out.append([ini, nombre])
    if out and total - out[-1][0] < 10:
        out.pop()
    if len(out) < 3:
        return []
    return [f'{int(ini // 60)}:{int(ini % 60):02d} {nombre}' for ini, nombre in out]


def construir(guion, dir_salida, sin_voz=False, hasta=None, fotos=None):
    g= json.load(open(guion, encoding='utf-8'))
    cargar_zonas(g)
    idioma= g.get('idioma', 'es')
    TONO_GUION[0]= g.get('tono_voz')
    W, H= (1920, 1080) if g.get('formato', '16:9') == '16:9' else (1080, 1920)
    base= g['id']
    os.makedirs(dir_salida, exist_ok=True)
    tmp= tempfile.mkdtemp()
    wav= os.path.join(tmp, 'voz.wav')
    total, tiempos= voz_beats(g['beats'], wav, sin_voz, idioma)
    total+= g.get('cola', 1.0)
    # escenas: cada beat con "v" empieza una; el hud se hereda
    escenas, hud= [], None
    for b, (ini, fin, marcas) in zip(g['beats'], tiempos):
        if 'hud' in b:
            hud= b['hud']
        if 'v' in b or not escenas:
            escenas.append({'ini': ini, 'v': b.get('v', {'tipo': 'dato'}), 'hud': hud, 'subs': []})
        for gr in grupos_sub(marcas):
            escenas[-1]['subs'].append(gr)
    for i, e in enumerate(escenas):
        e['fin']= escenas[i + 1]['ini'] if i + 1 < len(escenas) else total
    if hasta:
        total= min(total, hasta)
    sup= cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
    ctx= cairo.Context(sup)
    cache= cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
    if fotos:
        for ft in fotos:
            _fotograma(ctx, sup, cache, escenas, ft, W, H, None)
            sup.write_to_png(os.path.join(dir_salida, f'{base}_{ft:07.2f}.png'))
        return
    mp4= os.path.join(dir_salida, base + '.mp4')
    ff= subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS),
                          '-i', '-', '-i', wav, '-c:v', 'libx264', '-preset', 'veryfast', '-tune', 'animation', '-crf', '21',
                          '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-af', 'apad', '-shortest', '-movflags', '+faststart', mp4],
                         stdin=subprocess.PIPE)
    estado= {'clave': None}
    n= int(total * FPS)
    for k in range(n):
        _fotograma(ctx, sup, cache, escenas, k / FPS, W, H, estado)
        sup.flush()
        ff.stdin.write(bytes(sup.get_data()))
        if k % (FPS * 30) == 0:
            print(f'{base}: {k / FPS:.0f}/{total:.0f} s', flush=True)
    ff.stdin.close()
    ff.wait()
    meta= {k: g[k] for k in ('titulo', 'descripcion', 'tags') if k in g}
    caps= capitulos_validos([(ini, b['capitulo']) for b, (ini, _, _) in zip(g['beats'], tiempos) if b.get('capitulo')], total)
    meta['descripcion']= meta.get('descripcion', '').replace('{capitulos}', '\n'.join(caps))
    meta.update({'idioma': idioma, 'formato': g.get('formato_yt', 'largo'), 'duracion': round(total, 1)})
    json.dump(meta, open(os.path.join(dir_salida, base + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('listo:', mp4, f'{total:.1f} s')


def _fotograma(ctx, sup, cache, escenas, t, W, H, estado):
    e= next((e for e in escenas if e['ini'] <= t < e['fin']), escenas[-1])
    lt= t - e['ini']
    dur= e['fin'] - e['ini']
    tipo= e['v']['tipo']
    est= ESTATICA.get(tipo)
    clave= (id(e), 'fijo') if est is not None and lt >= est else None
    if estado is not None and clave is not None and estado['clave'] == clave:
        ctx.set_source_surface(cache)
        ctx.paint()
    else:
        ctx.save()
        ESCENAS[tipo](ctx, W, H, lt, dur, e['v'])
        ctx.restore()
        if estado is not None and clave is not None:
            c2= cairo.Context(cache)
            c2.set_source_surface(sup)
            c2.paint()
            estado['clave']= clave
    # fundido corto al entrar en cada escena
    if lt < 0.18 and e['ini'] > 0:
        ctx.set_source_rgba(*FONDO, 1 - lt / 0.18)
        ctx.paint()
    pinta_hud(ctx, W, H, e['hud'])
    gr= next((g for g in e['subs'] if g[0]['ini'] - 0.05 <= t <= g[-1]['fin'] + 0.25), None)
    pinta_sub(ctx, W, H, gr, t)


def miniatura(salida):
    """Miniatura del largo de imperios: globo con los 5 imperios y el gancho del titulo (1280x720)."""
    W, H= 1280, 720
    sup= cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
    ctx= cairo.Context(sup)
    fondo(ctx, W, H)
    _estrellas(ctx, W, H)
    capas= [(k, IMPERIOS[k]['color'], 1.0) for k in ('ESP', 'QING', 'RUS', 'MONG', 'BRIT')]
    pinta_globo(ctx, W * 0.72, H * 0.55, H * 0.52, 75, 35, capas)
    texto(ctx, 'RUSIA', 40, 180, 150, 'Anton', BLANCO, 'i', borde=18)
    texto(ctx, 'SERÍA LA', 40, 295, 105, 'Anton', BLANCO, 'i', borde=16)
    texto(ctx, '4ª', 40, 600, 230, 'Anton', AMARILLO, 'i', borde=22)
    texto(ctx, 'LOS 5 IMPERIOS MÁS GRANDES, A ESCALA', 40, 670, 44, 'Anton', BLANCO, 'i', borde=10)
    sup.write_to_png(salida)


if __name__ == '__main__':
    args= sys.argv[1:]
    if args and args[0] == '--validar':
        fallos= {r: validar(r) for r in args[1:]}
        for r, m in fallos.items():
            print(r, 'OK' if not m else '\n  - ' + '\n  - '.join(m))
        sys.exit(1 if any(fallos.values()) else 0)
    sin_voz= '--sin-voz' in args
    hasta= float(args[args.index('--hasta') + 1]) if '--hasta' in args else None
    fotos= [float(x) for x in args[args.index('--fotos') + 1].split(',')] if '--fotos' in args else None
    construir(args[0], args[1], sin_voz, hasta, fotos)
