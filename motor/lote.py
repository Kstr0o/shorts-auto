"""Lote semanal: planifica huecos, y sube lo planificado respetando la cuota de YouTube.

  python3 motor/lote.py plan     -> elige episodios de lote/cola_auto.json, asigna huecos libres, escribe lote/plan.json
                                    y deja en lote/render.json la lista de episodios a renderizar (para la matriz de Actions)
  python3 motor/lote.py subir    -> sube de lote/plan.json hasta el tope diario de cuota (ordenado por hora de publicacion)

Largos (16:9, unos 11 min) de lote/cola_largos.json: cada id (p. ej. lab002) es largos/<id>_es.json y sus Shorts anzuelo
largos/<id>_s1_es.json, _s2_, _s3_. Van en el dia y la hora de config.json "largos"; los anzuelos siempre DESPUES del largo
y solo se suben cuando el largo ya esta subido (su descripcion puede llevar {enlace_largo}). Lista para la matriz: lote/render_largos.json.

Variables: CUOTA_SUBIDAS_DIA (20: 4 canales x 2 Shorts + largos; el limite real de la API es 100 al dia, 1 unidad por subida), YT_* (claves), DIR_LISTOS (rama listos, por defecto ./listos).
Los huecos ya ocupados en YouTube (programados o publicados en los canales) se consultan por API y no se tocan.
"""
import datetime as dt
import json
import os
import sys
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L = os.path.join(RAIZ, 'lote')
MAD = ZoneInfo('Europe/Madrid')
PST = ZoneInfo('America/Los_Angeles')  # la cuota de YouTube se repone a medianoche del Pacifico
UTC = dt.timezone.utc


def cargar(nombre, defecto):
    ruta = os.path.join(L, nombre)
    return json.load(open(ruta, encoding='utf-8')) if os.path.exists(ruta) else defecto


def guardar(nombre, datos):
    json.dump(datos, open(os.path.join(L, nombre), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)


def iso(d):
    return d.astimezone(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')


def yt_de(canal):
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    cred = Credentials(None, refresh_token=os.environ[f'YT_TOKEN_{canal}'], client_id=os.environ['YT_CLIENT_ID'],
                       client_secret=os.environ['YT_CLIENT_SECRET'], token_uri='https://oauth2.googleapis.com/token')
    return build('youtube', 'v3', credentials=cred)


def ocupados(canal):
    """Horas (UTC) en que el canal ya tiene un video programado o publicado recientemente."""
    yt = yt_de(canal)
    lista = yt.channels().list(part='contentDetails', mine=True).execute()['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    ids = [i['contentDetails']['videoId'] for i in yt.playlistItems().list(part='contentDetails', playlistId=lista, maxResults=50).execute().get('items', [])]
    horas = []
    for v in yt.videos().list(part='snippet,status', id=','.join(ids)).execute().get('items', []):
        t = v['status'].get('publishAt') or v['snippet'].get('publishedAt')
        if t:
            horas.append(dt.datetime.fromisoformat(t.replace('Z', '+00:00')))
    return horas


def valido(ep_json):
    """Un episodio solo entra si esta completo en los dos idiomas (no copia del espanol)."""
    d = json.load(open(ep_json, encoding='utf-8'))
    if not (d.get('titulo', {}).get('en') and d.get('descripcion', {}).get('en') and d.get('tags', {}).get('en')):
        return 'faltan titulo/descripcion/tags en ingles'
    for i, e in enumerate(d['escenas']):
        t = e['texto']
        if not t.get('en') or not t.get('es'):
            return f'escena {i}: falta texto'
        if t['en'] == t['es'] and len(t['en']) > 25:
            return f'escena {i}: texto en ingles igual al espanol'
    return None


def plan_largos(cfg, pl, ocup, margen, avisos):
    """Asigna a cada largo pendiente su dia de la semana (config "largos") y a sus anzuelos las horas siguientes."""
    import largo_mapas
    cola = cargar('cola_largos.json', [])
    ya = {v['video'] for v in pl['videos']}
    hoy = dt.datetime.now(MAD).date()
    nuevos = []
    for serie, c in (cfg.get('largos') or {}).items():
        pend = [i for i in cola if i.startswith(serie) and f'{i}_{c["idioma"]}' not in ya]
        hechos = 0
        for dia in range(1, cfg['horizonte_dias'] + 1):
            if not pend or hechos >= c.get('max_semana', 1):
                break
            fecha = hoy + dt.timedelta(days=dia)
            if fecha.weekday() not in c['dias']:
                continue
            hh, mm = map(int, c['hora'].split(':'))
            cuando = dt.datetime.combine(fecha, dt.time(hh, mm), MAD)
            canal = c['canal']
            if any(abs(o - cuando) < margen for o in ocup[canal]):
                avisos.append(f'largo {serie}: {fecha} {c["hora"]} ya ocupado en {canal}')
                continue
            while pend:
                lid = pend.pop(0)
                vid = f'{lid}_{c["idioma"]}'
                ruta = os.path.join(RAIZ, 'largos', vid + '.json')
                mal = largo_mapas.validar(ruta) if os.path.exists(ruta) else ['no existe el json']
                if mal:
                    avisos.append(f'{vid}: ' + '; '.join(mal[:5]))
                    continue
                pl['videos'].append({'video': vid, 'canal': canal, 'publishAt': iso(cuando), 'estado': 'pendiente', 'tipo': 'largo'})
                ocup[canal].append(cuando)
                nuevos.append(vid)
                for n, a in enumerate(c.get('anzuelos', []), 1):
                    sid = f'{lid}_s{n}_{c["idioma"]}'
                    rs = os.path.join(RAIZ, 'largos', sid + '.json')
                    if not os.path.exists(rs):
                        continue
                    mal = largo_mapas.validar(rs)
                    if mal:
                        avisos.append(f'{sid}: ' + '; '.join(mal[:5]))
                        continue
                    hh, mm = map(int, a['hora'].split(':'))
                    h = dt.datetime.combine(fecha + dt.timedelta(days=a['dias']), dt.time(hh, mm), MAD)
                    if h <= cuando:  # regla: el anzuelo nunca antes que el largo
                        h = cuando + dt.timedelta(hours=4)
                    while any(abs(o - h) < margen for o in ocup[canal]):
                        h += margen
                    pl['videos'].append({'video': sid, 'canal': canal, 'publishAt': iso(h), 'estado': 'pendiente', 'tipo': 'anzuelo', 'largo': vid})
                    ocup[canal].append(h)
                    nuevos.append(sid)
                hechos += 1
                break
        if pend:
            avisos.append(f'largos {serie} para otra semana: {pend}')
    return nuevos


def plan():
    cfg = cargar('config.json', None)
    cola = cargar('cola_auto.json', [])
    pl = cargar('plan.json', {'videos': []})
    cuota = int(os.environ.get('CUOTA_SUBIDAS_DIA') or 20)
    ya = {v['video'].rsplit('_', 1)[0] for v in pl['videos']}
    pendientes = [e for e in cola if e not in ya]
    avisos = []
    listos_dir = os.environ.get('DIR_LISTOS', os.path.join(RAIZ, 'listos'))
    ocup = {}
    for serie, c in cfg['series'].items():
        for idi in ('ES', 'EN'):
            canal = f'{c["canal"]}_{idi}'
            ocup[canal] = ocupados(canal) + [dt.datetime.fromisoformat(v['publishAt'].replace('Z', '+00:00'))
                                              for v in pl['videos'] if v['canal'] == canal]
    for c in (cfg.get('largos') or {}).values():
        if c['canal'] not in ocup:
            ocup[c['canal']] = ocupados(c['canal']) + [dt.datetime.fromisoformat(v['publishAt'].replace('Z', '+00:00'))
                                                       for v in pl['videos'] if v['canal'] == c['canal']]
    margen = dt.timedelta(minutes=cfg['margen_minutos'])
    ahora = dt.datetime.now(UTC)
    # primero los largos: los Shorts se reparten en los huecos que dejen libres
    largos = plan_largos(cfg, pl, ocup, margen, avisos)
    tope = cuota * cfg['horizonte_dias']  # videos que caben en la cuota del horizonte
    total = sum(1 for v in pl['videos'] if v['estado'] == 'pendiente')  # (los largos de esta semana se suman abajo)
    # huecos futuros ordenados en el tiempo
    huecos = []
    hoy = dt.datetime.now(MAD).date()
    for dia in range(1, cfg['horizonte_dias'] + 1):
        fecha = hoy + dt.timedelta(days=dia)
        for serie, c in cfg['series'].items():
            for h in c['huecos']:
                def hora(txt, mas=0):
                    hh, mm = map(int, txt.split(':'))
                    return dt.datetime.combine(fecha + dt.timedelta(days=mas), dt.time(hh, mm), MAD)
                huecos.append((hora(h['es']), hora(h['en'], h['en_dia_mas']), serie, c['canal']))
    huecos.sort(key=lambda x: x[0])
    total += len(largos)
    nuevos = []
    for es, en, serie, canal in huecos:
        if total + 2 > tope or not any(e.startswith(serie) for e in pendientes):
            continue
        if any(abs(o - es) < margen for o in ocup[f'{canal}_ES']) or any(abs(o - en) < margen for o in ocup[f'{canal}_EN']):
            continue
        ep = next((e for e in pendientes if e.startswith(serie)), None)
        if ep is None:
            continue
        ruta = os.path.join(RAIZ, 'episodios', ep + '.json')
        if not os.path.exists(ruta):
            avisos.append(f'{ep}: no existe el json'); pendientes.remove(ep); continue
        mal = valido(ruta)
        if mal:
            avisos.append(f'{ep}: {mal}'); pendientes.remove(ep); continue
        pendientes.remove(ep)
        for idi, h in (('ES', es), ('EN', en)):
            pl['videos'].append({'video': f'{ep}_{idi.lower()}', 'canal': f'{canal}_{idi}', 'publishAt': iso(h), 'estado': 'pendiente'})
            ocup[f'{canal}_{idi}'].append(h)
        total += 2
        nuevos.append(ep)
    guardar('plan.json', pl)
    guardar('render.json', nuevos)
    guardar('render_largos.json', largos)
    print('largos y anzuelos planificados:', largos)
    print('episodios planificados:', nuevos)
    print('avisos:', avisos)
    print(f'videos pendientes de subir: {total} (tope por cuota: {tope})')
    if pendientes:
        print('sin hueco o fuera de cuota esta semana:', pendientes)


def subir():
    cuota = int(os.environ.get('CUOTA_SUBIDAS_DIA') or 20)
    pl = cargar('plan.json', {'videos': []})
    estado_f = os.path.join(RAIZ, 'estado.json')
    estado = json.load(open(estado_f)) if os.path.exists(estado_f) else {}
    dia = dt.datetime.now(PST).strftime('%Y-%m-%d')
    usadas = estado.setdefault('subidas_dia', {})
    n = usadas.get(dia, 0)
    listos = os.environ.get('DIR_LISTOS', os.path.join(RAIZ, 'listos'))
    import subir as s
    ahora = dt.datetime.now(UTC)
    for v in sorted(pl['videos'], key=lambda x: x['publishAt']):
        if v['estado'] != 'pendiente':
            continue
        cuando = dt.datetime.fromisoformat(v['publishAt'].replace('Z', '+00:00'))
        if cuando < ahora + dt.timedelta(minutes=20):
            v['estado'] = 'perdido'  # ya paso su hora sin poder subirse: lo replanifica la siguiente semana
            print('PERDIDO (sin cuota a tiempo):', v['video'])
            continue
        if n >= cuota:
            print(f'tope diario de {cuota} subidas alcanzado; el resto queda para manana')
            break
        meta = None
        if v.get('largo'):
            lg = next((x for x in pl['videos'] if x['video'] == v['largo']), None)
            if not lg or lg['estado'] != 'subido':
                print('anzuelo en espera hasta que se suba su largo:', v['video'])
                continue
        mp4 = os.path.join(listos, v['video'] + '.mp4')
        if not os.path.exists(mp4) and os.path.exists(mp4 + '.part00'):
            # los videos de mas de 100 MB van a listos en trozos .partNN
            import glob
            with open(mp4, 'wb') as f:
                for parte in sorted(glob.glob(mp4 + '.part*')):
                    f.write(open(parte, 'rb').read())
        if not os.path.exists(mp4):
            print('falta el mp4 en listos:', v['video'])
            continue
        try:
            os.environ['YT_PRIVACIDAD'] = 'private'
            meta = mp4.replace('.mp4', '.json')
            if v.get('largo'):
                d = json.load(open(meta, encoding='utf-8'))
                d['descripcion'] = d.get('descripcion', '').replace('{enlace_largo}', 'https://youtu.be/' + lg['id'])
                meta = meta.replace('.json', '_enlace.json')
                json.dump(d, open(meta, 'w', encoding='utf-8'), ensure_ascii=False)
            v['id'] = s.subir(mp4, meta, v['canal'], v['publishAt'])
            v['estado'] = 'subido'
            n += 1
        except Exception as e:
            print('FALLO', v['video'], type(e).__name__, str(e)[:300])
            if 'quota' in str(e).lower():
                break
        finally:
            usadas[dia] = n
            guardar('plan.json', pl)
            json.dump(estado, open(estado_f, 'w'), indent=1)
    for k in sorted(usadas)[:-10]:
        del usadas[k]
    guardar('plan.json', pl)
    json.dump(estado, open(estado_f, 'w'), indent=1)
    print(f'subidas hoy (dia de cuota {dia}): {n}/{cuota}')


if __name__ == '__main__':
    {'plan': plan, 'subir': subir}[sys.argv[1]]()
