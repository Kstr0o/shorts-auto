"""Ranking del nicho por "cuanto supero a su propio canal" (outliers) y formula de gancho de cada titulo. Sin IA.

Uso (lo lanza nicho.yml los martes antes de la sesion de guiones; tambien a mano):
  python3 motor/nicho.py [lote/nicho.json]
Deja lote/nicho.md (legible, lo lee la sesion de guiones) y lote/nicho_datos.json (en bruto).

Por que: las vistas a secas premian canales grandes, no ideas. Un video de 400.000 vistas en un canal cuya mediana es
2 millones es un martes normal; en un canal con mediana de 30.000 es algo que estudiar. Cada video se puntua como
VECES LA MEDIANA DE SU CANAL (de sus subidas del mismo tipo: Short con Short, largo con largo), con al menos 4 videos
para que la mediana signifique algo. Idea: youtube-agent-skill (yt-viral, MIT, Jake Schincariol); aqui con la API.
La formula sale de motor/ganchos.json mirando el TITULO: es la forma del titulo, no el porque del exito.

Para que sirve: ver que FORMA de video y de titulo despega ahora DENTRO de nuestro nicho (nunca cambiar de nicho).
No copiar temas ni guiones: lo que se copia es la estructura. Los temas siguen pasando por originalidad.py.

Cuota (YT_API_KEY, la misma de estadisticas/originalidad): ~100 unidades por busqueda + ~1-2 por canal nuevo.
Con 10 busquedas, unas 1.500 unidades. Tope: "tope_busquedas" en lote/nicho.json.
"""
import datetime as dt
import html
import json
import os
import re
import statistics
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import ganchos  # noqa: E402

CORTO_S = 180  # hasta 3 min cuenta como Short


def segundos(iso):
    m = re.match(r'P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', iso or '')
    if not m:
        return 0
    d, h, mi, s = (int(x or 0) for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


def alfabeto_latino(t):
    letras = [c for c in t if c.isalpha()]
    return not letras or sum(ord(c) < 0x250 for c in letras) / len(letras) >= 0.7


def tipo(seg):
    return 'short' if seg <= CORTO_S else 'largo'


class Api:
    def __init__(self, yt):
        self.yt = yt
        self.unidades = 0
        self.subidas = {}   # canal -> lista de playlist de subidas
        self.videos = {}    # id -> {vistas, seg, fecha, titulo}

    def buscar(self, q, idioma, dias, duracion):
        desde = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=dias)).strftime('%Y-%m-%dT%H:%M:%SZ')
        extra = {'relevanceLanguage': idioma} if idioma in ('es', 'en') else {}
        if duracion in ('short', 'medium', 'long'):
            extra['videoDuration'] = duracion
        r = self.yt.search().list(part='snippet', q=q, type='video', maxResults=25, order='viewCount',
                                  publishedAfter=desde, **extra).execute()
        self.unidades += 100
        return [{'id': i['id']['videoId'], 'canal': i['snippet']['channelId'], 'nombre_canal': html.unescape(i['snippet']['channelTitle']),
                 'titulo': html.unescape(i['snippet']['title'])} for i in r.get('items', [])]

    def detalles(self, ids):
        faltan = [i for i in dict.fromkeys(ids) if i not in self.videos]
        for k in range(0, len(faltan), 50):
            r = self.yt.videos().list(part='statistics,contentDetails,snippet', id=','.join(faltan[k:k + 50])).execute()
            self.unidades += 1
            for v in r.get('items', []):
                self.videos[v['id']] = {'vistas': int(v['statistics'].get('viewCount', 0)),
                                        'seg': segundos(v['contentDetails'].get('duration')),
                                        'fecha': v['snippet']['publishedAt'][:10], 'titulo': html.unescape(v['snippet']['title'])}

    def subidas_de(self, canales, por_canal):
        nuevos = [c for c in dict.fromkeys(canales) if c not in self.subidas]
        listas = {}
        for k in range(0, len(nuevos), 50):
            r = self.yt.channels().list(part='contentDetails', id=','.join(nuevos[k:k + 50])).execute()
            self.unidades += 1
            for c in r.get('items', []):
                listas[c['id']] = c['contentDetails']['relatedPlaylists']['uploads']
        for c in nuevos:
            ids = []
            if c in listas:
                try:
                    r = self.yt.playlistItems().list(part='contentDetails', playlistId=listas[c],
                                                     maxResults=por_canal).execute()
                    self.unidades += 1
                    ids = [i['contentDetails']['videoId'] for i in r.get('items', [])]
                except Exception:  # listas ocultas o borradas
                    ids = []
            self.subidas[c] = ids
        self.detalles([i for c in canales for i in self.subidas.get(c, [])])


def mediana_canal(api, canal, clase, excluir, min_videos, hoy):
    """Mediana de vistas de las subidas del canal del mismo tipo (Short/largo), sin contar las de menos de 3 dias."""
    vistas = []
    for i in api.subidas.get(canal, []):
        v = api.videos.get(i)
        if not v or i == excluir or tipo(v['seg']) != clase:
            continue
        if (hoy - dt.date.fromisoformat(v['fecha'])).days < 3:
            continue
        vistas.append(v['vistas'])
    return (statistics.median(vistas), len(vistas)) if len(vistas) >= min_videos else (None, len(vistas))


def ranking(api, cfg):
    hoy = dt.date.today()
    tope = int(cfg.get('tope_busquedas', 10))
    minx = float(cfg.get('min_veces', 2.0))
    min_videos = int(cfg.get('min_videos_canal', 4))
    hechas = 0
    salida = {}
    for canal, c in cfg['canales'].items():
        filas, vistos, errores = [], set(), []
        for b in c['busquedas']:
            if hechas >= tope:
                errores.append(f'tope de {tope} busquedas: "{b["q"]}" sin hacer')
                continue
            try:
                res = api.buscar(b['q'], c['idioma'], int(b.get('dias', cfg.get('dias', 60))), b.get('duracion', 'any'))
                hechas += 1
                api.detalles([r['id'] for r in res])
                api.subidas_de([r['canal'] for r in res], int(cfg.get('subidas_por_canal', 30)))
            except Exception as e:  # cuota o red: se apunta y se sigue
                errores.append(f'"{b["q"]}": {str(e)[:120]}')
                continue
            for r in res:
                v = api.videos.get(r['id'])
                if not v or r['id'] in vistos or not alfabeto_latino(r['titulo']):
                    continue  # relevanceLanguage no filtra bien: fuera titulos en otro alfabeto (hindi, arabe...)
                vistos.add(r['id'])
                clase = tipo(v['seg'])
                med, n = mediana_canal(api, r['canal'], clase, r['id'], min_videos, hoy)
                if not med:
                    continue
                veces = round(v['vistas'] / med, 1) if med else None
                fid, fnombre = ganchos.clasificar(r['titulo'])
                filas.append({'veces': veces, 'vistas': v['vistas'], 'mediana': int(med), 'n_mediana': n,
                              'canal': r['nombre_canal'], 'titulo': r['titulo'], 'tipo': clase, 'seg': v['seg'],
                              'fecha': v['fecha'], 'formula': fid, 'formula_nombre': fnombre, 'busqueda': b['q'],
                              'url': f'https://youtu.be/{r["id"]}'})
        filas = sorted((f for f in filas if f['veces'] and f['veces'] >= minx), key=lambda f: -f['veces'])
        cuenta = {}
        for f in filas:
            cuenta[f['formula_nombre']] = cuenta.get(f['formula_nombre'], 0) + 1
        salida[canal] = {'nombre': c.get('nombre', canal), 'outliers': filas[:15],
                         'formulas': sorted(cuenta.items(), key=lambda x: -x[1]), 'errores': errores}
    return salida, hechas


def informe(salida, hechas, unidades, minx):
    l = [f'# Lo que despega en el nicho ({dt.date.today().isoformat()})', '',
         f'Videos que han hecho {minx:g} veces o mas la mediana de SU canal (mismo tipo: Short con Short, largo con largo).',
         'La formula es la forma del titulo (motor/ganchos.json), no el porque del exito. Copiar la ESTRUCTURA, nunca el tema;',
         'los temas siguen pasando por originalidad. Mismo nicho siempre.', '',
         f'Busquedas: {hechas}. Cuota gastada: ~{unidades} unidades.', '']
    for canal, d in salida.items():
        l += [f'## {d["nombre"]}', '']
        if d['formulas']:
            l += ['Formulas entre los que despegan: ' + ', '.join(f'{n} ({k})' for n, k in d['formulas']), '']
        if d['outliers']:
            l += ['| veces | vistas | mediana canal | tipo | canal | titulo | formula |', '|---|---|---|---|---|---|---|']
            for f in d['outliers']:
                tit = f['titulo'].replace('|', '/')[:80]
                l.append(f'| x{f["veces"]} | {f["vistas"]:,} | {f["mediana"]:,} | {f["tipo"]} {f["seg"] // 60}:{f["seg"] % 60:02d} | '
                         f'{f["canal"][:24]} | [{tit}]({f["url"]}) | {f["formula_nombre"]} |')
        else:
            l.append('Nada por encima del umbral esta semana (o la busqueda fallo).')
        for e in d['errores']:
            l.append(f'- aviso: {e}')
        l.append('')
    l += ['## Como usarlo en la sesion de guiones', '',
          '- Mira las 2-3 formulas que mas se repiten en tu canal y usa al menos una en los ganchos de esta semana.',
          '- Fijate en la duracion y el tipo de los que despegan (Short o largo, cuanto duran).',
          '- Nada de copiar temas: el tema sale de la propuesta y pasa por originalidad.']
    return '\n'.join(l)


def main(ruta_cfg):
    cfg = json.load(open(ruta_cfg, encoding='utf-8'))
    if not os.environ.get('YT_API_KEY'):
        print('falta YT_API_KEY')
        return 1
    from googleapiclient.discovery import build
    api = Api(build('youtube', 'v3', developerKey=os.environ['YT_API_KEY'], cache_discovery=False))
    salida, hechas = ranking(api, cfg)
    md = informe(salida, hechas, api.unidades, float(cfg.get('min_veces', 2.0)))
    open(os.path.join(RAIZ, 'lote', 'nicho.md'), 'w', encoding='utf-8').write(md)
    json.dump({'fecha': dt.date.today().isoformat(), 'unidades': api.unidades, 'canales': salida},
              open(os.path.join(RAIZ, 'lote', 'nicho_datos.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(md)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'lote', 'nicho.json')))
