"""Paso de originalidad: ANTES de escribir un guion, comprobar que el tema/angulo no lo tenemos ya
y que no esta ya muy cubierto en YouTube. Sin IA: solo la API de YouTube y comparacion de palabras.

Uso (lo lanza el workflow originalidad.yml; la sesion de guiones le pasa las propuestas):
  python3 motor/originalidad.py comprobar propuestas.json [--datos ../datos] [--sin-api]
  python3 motor/originalidad.py estado ID            -> imprime el registro de un id (para lote.py y para la sesion)

propuestas.json = lista de propuestas, una por guion que se quiere escribir:
  {"id": "ysi015", "serie": "ysi", "titulo": {"es": "...", "en": "..."},
   "angulo": "que lo hace distinto (dato, formato, personaje)", "busqueda": {"es": "...", "en": "..."}}
  - titulo puede ser un texto (un idioma, con "idioma": "es"|"en"; por defecto en) o {es, en}. "busqueda" es opcional (por defecto el titulo sin emojis).

Que hace con cada propuesta:
 1. PROPIOS: compara titulo + angulo con todos nuestros videos (titulos de la ultima foto de la rama datos =
    publicados y programados en los 4 canales) y con todos los json de episodios/, largos/ e historias/.
 2. FUERA: una busqueda en YouTube por idioma (search.list, 100 unidades de cuota cada una) + videos.list
    (1 unidad) para las vistas. Cuenta cuantos de los 25 primeros resultados son casi el mismo video.
 3. Veredicto: "unico" | "cubierto" (cambiar angulo/dato/formato y volver a comprobar) | "repetido" (ya lo tenemos).
    Si la busqueda en YouTube falla, la propuesta que no se parece a nada nuestro pasa como "unico" con "parcial": true
    (nunca nos quedamos sin videos por un fallo de la API).
Ademas (idea del 23/11) apunta lo que YouTube AUTOCOMPLETA al escribir la busqueda de cada propuesta: es lo que la
gente busca de verdad, para elegir un titulo que coincida (sobre todo en los largos). No gasta cuota ni cambia el veredicto.
Deja el registro en lote/originalidad.json (por id) y un resumen legible en lote/originalidad.md.
Variables: YT_API_KEY (clave de solo lectura, la misma de estadisticas). ORIG_MAX_BUSQUEDAS (tope de busquedas por
ejecucion, 30 por defecto = unas 3.000 unidades).
"""
import datetime as dt
import glob
import json
import os
import re
import sys
import unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRO = os.path.join(RAIZ, 'lote', 'originalidad.json')
RESUMEN = os.path.join(RAIZ, 'lote', 'originalidad.md')

# umbrales (Dice sobre palabras con contenido). Ajustables aqui sin tocar el resto.
PROPIO_REPETIDO = 0.6   # contra un video nuestro: a partir de aqui es el mismo video
PROPIO_PARECIDO = 0.4   # aviso: se parece a uno nuestro (vale si el angulo es distinto)
FUERA_IGUAL = 0.5       # un resultado de YouTube con este parecido cuenta como "casi el mismo video"
FUERA_CUBIERTO = 3      # con 3 o mas casi iguales en el top 25 -> cubierto
FUERA_GRANDE = 100_000  # o con 1 casi igual de mas de 100.000 vistas en el ultimo ano -> cubierto

VACIAS = set('''
a al algo ante como con cual cuando de del desde donde e el ella ellas ellos en entre era es esa ese eso esta este
esto estos fue ha hay la las le les lo los mas me mi muy no o os para pero por que se si sin sobre su sus te tu tus
un una uno unos y ya yo vas va hoy dia dias asi cada todo todos toda todas
the of and or to in on at for with from by as is are was were be been it its this that these those you your we
our they their he she his her what if how why when who which do does did can could would will would an a i my me
not no so than then there here just about into out up down over day days
'''.split())


def normal(txt):
    """minusculas, sin tildes, sin emojis ni signos."""
    txt = unicodedata.normalize('NFKD', str(txt).lower())
    txt = ''.join(c for c in txt if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9ñ ]+', ' ', txt)


def palabras(txt):
    out = set()
    for p in normal(txt).split():
        if p in VACIAS or len(p) < 3 and not p.isdigit():
            continue
        if len(p) > 4 and p.endswith('es'):
            p = p[:-2]
        elif len(p) > 3 and p.endswith('s'):
            p = p[:-1]
        out.add(p)
    return out


def parecido(a, b):
    a, b = palabras(a), palabras(b)
    if not a or not b:
        return 0.0
    return round(2 * len(a & b) / (len(a) + len(b)), 2)


def textos(v, idioma='?'):
    """titulo como texto o {es, en} -> lista de (idioma, texto)."""
    if isinstance(v, dict):
        return [(k, t) for k, t in v.items() if t]
    return [(idioma, v)] if v else []


def nuestros(datos_dir):
    """(origen, titulo) de todos nuestros videos: publicados/programados y guiones del repo."""
    lista = []
    if datos_dir and os.path.isdir(datos_dir):
        fotos = sorted(glob.glob(os.path.join(datos_dir, '20*', 'datos.json')))
        if fotos:
            for canal, c in json.load(open(fotos[-1], encoding='utf-8')).items():
                for vid, v in (c.get('videos') or {}).items():
                    lista.append((f'{canal}/{vid}', v.get('titulo', '')))
    for patron in ('episodios/*.json', 'largos/*.json', 'historias/*.json'):
        for ruta in glob.glob(os.path.join(RAIZ, patron)):
            try:
                d = json.load(open(ruta, encoding='utf-8'))
            except Exception:
                continue
            nombre = os.path.basename(ruta)[:-5]
            for _, t in textos(d.get('titulo')):
                lista.append((nombre, t))
                if d.get('titulo_fijo'):
                    for _, tf in textos(d['titulo_fijo']):
                        lista.append((nombre, tf))
    return lista


def buscar(yt, q, idioma):
    """Top 25 de YouTube para q: [(titulo, vistas, fecha, canal, id)]. 101 unidades de cuota."""
    extra = {'relevanceLanguage': idioma} if idioma in ('es', 'en') else {}
    r = yt.search().list(part='snippet', q=q, type='video', maxResults=25, order='relevance', **extra).execute()
    items = r.get('items', [])
    ids = [i['id']['videoId'] for i in items]
    vistas = {}
    if ids:
        for v in yt.videos().list(part='statistics', id=','.join(ids)).execute().get('items', []):
            vistas[v['id']] = int(v['statistics'].get('viewCount', 0))
    return [(i['snippet']['title'], vistas.get(i['id']['videoId'], 0), i['snippet']['publishedAt'][:10],
             i['snippet']['channelTitle'], i['id']['videoId']) for i in items]


def autocompletar(q, idioma):
    """Sugerencias del buscador de YouTube para q (endpoint publico de sugerencias, sin clave ni cuota).
    Devuelve [] si falla: es solo una ayuda para el titulo."""
    import urllib.parse
    import urllib.request
    pais = {'es': 'ES', 'en': 'US'}.get(idioma, 'US')
    url = ('https://suggestqueries-clients6.youtube.com/complete/search?client=youtube&ds=yt&hl=%s&gl=%s&q=%s'
           % (idioma if idioma in ('es', 'en') else 'en', pais, urllib.parse.quote(q)))
    try:
        txt = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}),
                                     timeout=10).read().decode('utf-8', 'replace')
        datos = json.loads(txt[txt.index('['):txt.rindex(']') + 1])  # viene como JSONP: window.google.ac.h([...])
        return [x[0] if isinstance(x, list) else x for x in datos[1]][:10]
    except Exception:
        return []


def comprobar(propuestas, datos_dir, con_api=True):
    propios = nuestros(datos_dir)
    yt = None
    if con_api and os.environ.get('YT_API_KEY'):
        from googleapiclient.discovery import build
        yt = build('youtube', 'v3', developerKey=os.environ['YT_API_KEY'], cache_discovery=False)
    tope = int(os.environ.get('ORIG_MAX_BUSQUEDAS') or 30)
    hace_un_ano = (dt.date.today() - dt.timedelta(days=365)).isoformat()
    reg = json.load(open(REGISTRO, encoding='utf-8')) if os.path.exists(REGISTRO) else {}
    busquedas = 0
    salida = []
    for p in propuestas:
        pid = p['id']
        tits = textos(p.get('titulo'), p.get('idioma', 'en'))
        angulo = p.get('angulo', '')
        r = {'id': pid, 'fecha': dt.date.today().isoformat(), 'titulo': p.get('titulo'), 'angulo': angulo,
             'propios': [], 'fuera': {}, 'motivos': []}
        # 1. contra lo nuestro (sin contarse a si mismo si el json ya existe)
        peor = 0.0
        for idi, t in tits:
            for origen, nt in propios:
                if origen == pid or origen.startswith(pid + '_'):
                    continue
                s = max(parecido(t, nt), parecido(t + ' ' + angulo, nt) if angulo else 0)
                if s >= PROPIO_PARECIDO:
                    r['propios'].append({'video': origen, 'titulo': nt, 'parecido': s})
                peor = max(peor, s)
        r['propios'].sort(key=lambda x: -x['parecido'])
        r['propios'] = r['propios'][:5]
        repetido = peor >= PROPIO_REPETIDO
        # 2. fuera: una busqueda por idioma
        cubierto = False
        if yt and not repetido:
            for idi, t in tits:
                if busquedas >= tope:
                    r['motivos'].append('tope de busquedas alcanzado: sin comprobar fuera')
                    break
                q = (p.get('busqueda') or {}).get(idi) if isinstance(p.get('busqueda'), dict) else p.get('busqueda')
                q = q or ' '.join(normal(t).split())
                try:
                    res = buscar(yt, q, idi)
                except Exception as e:  # cuota agotada o red: no se inventa nada
                    r['motivos'].append(f'busqueda {idi} fallo: {str(e)[:120]}')
                    r['fuera'][idi] = None
                    continue
                busquedas += 1
                r.setdefault('autocompletar', {})[idi] = autocompletar(q, idi)
                iguales = [x for x in res if parecido(t, x[0]) >= FUERA_IGUAL]
                grandes = [x for x in iguales if x[1] >= FUERA_GRANDE and x[2] >= hace_un_ano]
                r['fuera'][idi] = {'q': q, 'resultados': len(res), 'casi_iguales': len(iguales),
                                   'grandes_ultimo_ano': len(grandes),
                                   'ejemplos': [{'titulo': x[0], 'vistas': x[1], 'fecha': x[2], 'canal': x[3]}
                                                for x in sorted(iguales, key=lambda x: -x[1])[:3]]}
                if len(iguales) >= FUERA_CUBIERTO or grandes:
                    cubierto = True
        # 3. veredicto
        if repetido:
            r['veredicto'] = 'repetido'
            r['motivos'].append(f'casi igual a nuestro {r["propios"][0]["video"]} ({peor})')
        elif cubierto:
            r['veredicto'] = 'cubierto'
            for idi, f in r['fuera'].items():
                r['motivos'].append(f'{idi}: {f["casi_iguales"]} casi iguales en el top 25, '
                                    f'{f["grandes_ultimo_ano"]} con mas de {FUERA_GRANDE:,} vistas este ano')
        elif not yt or not r['fuera'] or any(v is None for v in r['fuera'].values()):
            # la busqueda fuera fallo (sin clave, sin cuota o error): para no quedarnos sin videos pasa con lo que si se
            # comprobo (no es igual a nada nuestro), marcado para que se vea en el registro
            r['veredicto'] = 'unico'
            r['parcial'] = True
            r['motivos'].append('solo comprobado contra nuestros videos: la busqueda en YouTube fallo (pasa igual, revisar a mano si se puede)')
        else:
            r['veredicto'] = 'unico'
            r['motivos'].append('ninguno nuestro igual y pocos o ningun video casi igual fuera')
        r['firma'] = sorted(palabras(' '.join(t for _, t in tits)))
        reg[pid] = r
        salida.append(r)
    json.dump(reg, open(REGISTRO, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    escribir_resumen(salida, busquedas)
    return salida


def escribir_resumen(salida, busquedas):
    lin = [f'# Originalidad {dt.date.today().isoformat()}', '',
           f'Busquedas en YouTube: {busquedas} (unas {busquedas * 101} unidades de cuota).', '',
           '| id | veredicto | titulo | por que |', '|---|---|---|---|']
    for r in salida:
        t = r['titulo'] if isinstance(r['titulo'], str) else ' / '.join(v for v in r['titulo'].values() if v)
        lin.append(f'| {r["id"]} | {r["veredicto"]} | {t} | {"; ".join(r["motivos"])} |')
    sug = [(r['id'], idi, l) for r in salida for idi, l in (r.get('autocompletar') or {}).items() if l]
    if sug:
        lin += ['', '## Lo que YouTube autocompleta (lo que la gente busca de verdad)',
                'Usalo para el titulo: mejor si contiene una de estas frases tal cual (sin cambiar el nicho).', '']
        lin += [f'- {pid} ({idi}): ' + ' | '.join(l) for pid, idi, l in sug]
    open(RESUMEN, 'w', encoding='utf-8').write('\n'.join(lin) + '\n')
    print('\n'.join(lin))


def estado(pid, titulo=None):
    """Para lote.py: None si el guion pasa; si no, el motivo. Pasa con veredicto 'unico' y titulo comprobado."""
    reg = json.load(open(REGISTRO, encoding='utf-8')) if os.path.exists(REGISTRO) else {}
    r = reg.get(pid)
    if not r:
        return 'sin comprobacion de originalidad (motor/originalidad.py)'
    if r.get('veredicto') != 'unico':
        return f'originalidad: {r.get("veredicto")} ({"; ".join(r.get("motivos", []))[:150]})'
    if titulo is not None:
        ahora = palabras(' '.join(t for _, t in textos(titulo)))
        antes = set(r.get('firma') or [])
        if antes and ahora and 2 * len(ahora & antes) / (len(ahora) + len(antes)) < 0.5:
            return 'originalidad: el titulo cambio mucho desde la comprobacion, volver a comprobar'
    return None


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args or args[0] not in ('comprobar', 'estado'):
        print(__doc__)
        sys.exit(1)
    if args[0] == 'estado':
        print(json.dumps(json.load(open(REGISTRO, encoding='utf-8')).get(args[1]), indent=1, ensure_ascii=False))
        sys.exit(0)
    datos = args[args.index('--datos') + 1] if '--datos' in args else None
    props = json.load(open(args[1], encoding='utf-8'))
    comprobar(props if isinstance(props, list) else props['propuestas'], datos, con_api='--sin-api' not in args)
