"""Recoge cada dia las estadisticas y los comentarios de los canales (los 4 de siempre y el de clips).

Uso: python3 motor/estadisticas.py datos
Deja en datos/:
  historial.csv          una fila por video y dia (vistas, retencion, likes...), para ver como crece cada video
  AAAA-MM-DD/informe.md  resumen legible: mejores y peores videos, publico, comentarios nuevos
  AAAA-MM-DD/datos.json  lo mismo en bruto, para analizarlo
Variables: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_TOKEN_<CANAL>. Los tokens necesitan los permisos
youtube.readonly y yt-analytics.readonly (ver obtener_token.py). Un canal sin token se salta.
Gasta muy poca cuota de la API (unas decenas de unidades por canal).

Senales de crecimiento (idea del 23/11, video "5 senales de que tu canal va a explotar"):
  1. impresiones que suben aunque las vistas no -> informe de alcance de la YouTube Reporting API (solo se crea el
     trabajo la primera vez; YouTube tarda ~2 dias en dar el primer informe). Necesita la "YouTube Reporting API"
     activada en Google Cloud (mismo proyecto que la Analytics API) y el mismo permiso yt-analytics.readonly.
  2. espectadores recurrentes -> la API no da "recurrentes"; se usa el % de vistas de suscritos como aproximacion.
  3. comentarios por cada 1.000 vistas.
  4. un video que tira del canal -> "destacados": 3 veces o mas la mediana de vistas del canal (minimo 100 vistas).
  5. trafico de busqueda -> % de vistas desde la busqueda de YouTube (canal y por video) y que terminos buscan.

Donde se va la gente (idea del 24/11, del lector de retencion de youtube-agent-skill, MIT): para los RET_MAX videos mas
vistos de cada canal (con MIN_VISTAS o mas) pide la curva de retencion por segundo a la Analytics API
(dimension elapsedVideoTimeRatio, 100 puntos; mismo permiso yt-analytics.readonly, sin coste de cuota de la Data API) y
apunta: % que se va en el gancho (3 s en Shorts, 30 s en largos), las caidas mas bruscas con su segundo y lo que se decia
ahi (aprox., buscando el guion por el titulo) y la formula de gancho de la primera frase (motor/ganchos.py). Agrupa por
formula para ver con datos propios cuales retienen mejor.
"""
import csv
import datetime as dt
import glob
import json
import os
import re
import sys

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

CANALES= {'TONI_ES': 'Historias Sin Blanca', 'TONI_EN': 'Broke Toons',
          'YSI_ES': 'El Laboratorio del Y Si', 'YSI_EN': 'The Mad Maybe Lab',
          'CLIPS': 'Daily Streamer Clips'}  # canal de clips: su token necesita los mismos permisos de lectura
OBJETIVO_PCT_VISTO= 80  # objetivo orientativo de % visto en Shorts (no es regla oficial de YouTube)
METRICAS= 'views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,likes,comments,shares,subscribersGained'
INICIO= '2026-11-01'
MIN_VISTAS= 100       # regla del dueno: por debajo no cuenta para analisis (lo ven el y sus amigos)
DESTACA_X= 3          # un video destaca si tiene 3 veces o mas la mediana de vistas del canal
POR_TITULO= {}
TOP_POR_VIDEO= 10     # videos (los mas vistos) a los que se mira el origen del trafico uno a uno
REPORTE_ALCANCE= 'channel_reach_basic_a1'  # impresiones y CTR de miniaturas (Reporting API)
# los comentarios publicos se leen con una clave de API (YT_API_KEY): los tokens no tienen permiso para ello
LECTOR= build('youtube', 'v3', developerKey=os.environ['YT_API_KEY']) if os.environ.get('YT_API_KEY') else None
RET_MAX= 15           # videos por canal (los mas vistos, con MIN_VISTAS o mas) a los que se pide la curva de retencion
RAIZ= os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'motor'))
import ganchos  # noqa: E402  (formulas de gancho, sin IA)


def credenciales(canal):
    token= os.environ.get(f'YT_TOKEN_{canal}')
    if not token:
        return None
    return Credentials(None, refresh_token=token, client_id=os.environ['YT_CLIENT_ID'],
                       client_secret=os.environ['YT_CLIENT_SECRET'], token_uri='https://oauth2.googleapis.com/token')


def tabla(resp):
    # paso la respuesta de Analytics a una lista de diccionarios
    cols= [c['name'] for c in resp.get('columnHeaders', [])]
    return [dict(zip(cols, fila)) for fila in resp.get('rows', [])]


def videos_del_canal(yt):
    canal= yt.channels().list(part='id,statistics,contentDetails', mine=True).execute()['items'][0]
    lista= canal['contentDetails']['relatedPlaylists']['uploads']
    ids, pagina= [], None
    while True:
        r= yt.playlistItems().list(part='contentDetails', playlistId=lista, maxResults=50, pageToken=pagina).execute()
        ids+= [i['contentDetails']['videoId'] for i in r['items']]
        pagina= r.get('nextPageToken')
        if not pagina:
            break
    videos= {}
    for i in range(0, len(ids), 50):
        r= yt.videos().list(part='snippet,statistics,contentDetails,status', id=','.join(ids[i:i + 50])).execute()
        for v in r['items']:
            videos[v['id']]= {'titulo': v['snippet']['title'], 'publicado': v['snippet']['publishedAt'],
                              'privacidad': v['status']['privacyStatus'],
                              'programado': v['status'].get('publishAt'), 'duracion': v['contentDetails']['duration'],
                              'vistas_publicas': int(v['statistics'].get('viewCount', 0)),
                              'likes_publicos': int(v['statistics'].get('likeCount', 0)),
                              'comentarios_publicos': int(v['statistics'].get('commentCount', 0))}
    return canal, videos


def analitica(ya, hoy):
    base= dict(ids='channel==MINE', startDate=INICIO, endDate=hoy)
    salida= {}
    consultas= {
        'por_video': dict(metrics=METRICAS, dimensions='video', sort='-views', maxResults=200),
        'por_dia': dict(metrics='views,subscribersGained,estimatedMinutesWatched', dimensions='day', sort='day'),
        'edad_genero': dict(metrics='viewerPercentage', dimensions='ageGroup,gender'),
        'paises': dict(metrics='views', dimensions='country', sort='-views', maxResults=15),
        'origen_trafico': dict(metrics='views', dimensions='insightTrafficSourceType', sort='-views'),
        'suscritos_o_no': dict(metrics='views,averageViewPercentage', dimensions='subscribedStatus'),
        # terminos que la gente escribio en el buscador de YouTube antes de vernos (senal 5 e ideas de titulos)
        'terminos_busqueda': dict(metrics='views', dimensions='insightTrafficSourceDetail',
                                  filters='insightTrafficSourceType==YT_SEARCH', sort='-views', maxResults=15),
    }
    for nombre, q in consultas.items():
        try:
            salida[nombre]= tabla(ya.reports().query(**base, **q).execute())
        except Exception as e:  # con canales nuevos algunas consultas aun no devuelven nada
            salida[nombre]= {'error': str(e)[:200]}
    # origen del trafico de los videos mas vistos, uno a uno (la API no cruza video x origen en una sola consulta)
    salida['trafico_por_video']= {}
    filas= salida.get('por_video')
    for f in (filas if isinstance(filas, list) else [])[:TOP_POR_VIDEO]:
        try:
            r= tabla(ya.reports().query(**base, metrics='views', dimensions='insightTrafficSourceType',
                                        filters=f'video=={f["video"]}').execute())
            salida['trafico_por_video'][f['video']]= {x['insightTrafficSourceType']: x['views'] for x in r}
        except Exception:
            pass
    return salida


def alcance(cred, dias=7):
    """Impresiones y CTR de miniatura por video (ultimos `dias` informes diarios) de la Reporting API.
    La primera vez crea el trabajo y devuelve {'aviso': ...}: los datos llegan ~2 dias despues."""
    import io
    from googleapiclient.http import MediaIoBaseDownload
    try:
        yr= build('youtubereporting', 'v1', credentials=cred, cache_discovery=False)
        trabajos= yr.jobs().list().execute().get('jobs', [])
        job= next((j for j in trabajos if j.get('reportTypeId') == REPORTE_ALCANCE), None)
        if not job:
            tipos= [t['id'] for t in yr.reportTypes().list().execute().get('reportTypes', [])]
            if REPORTE_ALCANCE not in tipos:
                return {'error': 'YouTube no ofrece el informe de alcance a este canal todavia'}
            yr.jobs().create(body={'reportTypeId': REPORTE_ALCANCE, 'name': 'alcance shorts-auto'}).execute()
            return {'aviso': 'trabajo de alcance creado hoy: las impresiones salen en ~2 dias'}
        informes= yr.jobs().reports().list(jobId=job['id']).execute().get('reports', [])
        informes= sorted(informes, key=lambda r: r['startTime'], reverse=True)[:dias]
        if not informes:
            return {'aviso': 'trabajo de alcance creado, YouTube aun no ha generado ningun informe'}
        por_video= {}
        for inf in informes:
            req= yr.media().download(resourceName=' ')
            req.uri= inf['downloadUrl']
            buf= io.BytesIO()
            bajada= MediaIoBaseDownload(buf, req)
            hecho= False
            while not hecho:
                _, hecho= bajada.next_chunk()
            filas= list(csv.DictReader(io.StringIO(buf.getvalue().decode('utf-8'))))
            for f in filas:
                vid= f.get('video_id')
                if not vid:
                    continue
                imp= float(f.get('video_thumbnail_impressions') or 0)
                ctr= float(f.get('video_thumbnail_impressions_ctr') or 0)
                d= por_video.setdefault(vid, {'impresiones': 0, 'clics': 0.0})
                d['impresiones']+= imp
                d['clics']+= imp * ctr
        for d in por_video.values():
            d['ctr']= round(100 * d.pop('clics') / d['impresiones'], 1) if d['impresiones'] else 0
            d['impresiones']= int(d['impresiones'])
        return {'dias': len(informes), 'desde': informes[-1]['startTime'][:10], 'por_video': por_video}
    except Exception as e:  # API sin activar en Google Cloud, permisos, etc.: no rompe el resto del informe
        msg= str(e)[:200]
        if 'has not been used' in msg or 'disabled' in msg or 'SERVICE_DISABLED' in msg:
            msg= 'falta activar la "YouTube Reporting API" en Google Cloud (mismo proyecto que la Analytics API)'
        return {'error': msg}


def segundos(iso):
    m= re.match(r'P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', iso or '')
    d, h, mi, se= (int(x or 0) for x in m.groups()) if m else (0, 0, 0, 0)
    return d * 86400 + h * 3600 + mi * 60 + se


def guiones():
    """titulo exacto -> (ruta, idioma, json) de nuestros guiones, para saber que se decia en cada segundo."""
    out= {}
    for patron in ('episodios/*.json', 'largos/*.json', 'historias/*.json'):
        for ruta in glob.glob(os.path.join(RAIZ, patron)):
            try:
                ep= json.load(open(ruta, encoding='utf-8'))
            except Exception:
                continue
            tit= ep.get('titulo')
            for idi, t in (tit.items() if isinstance(tit, dict) else [(ep.get('idioma', 'en'), tit)]):
                if t:
                    out[t.strip()]= (os.path.relpath(ruta, RAIZ), idi, ep)
    return out


def partes_guion(ep):
    # Shorts: escenas; largos del Laboratorio: beats; historias de HSB: lineas
    return ep.get('escenas') or ep.get('beats') or ep.get('lineas') or []


def texto_escena(esc, idi):
    t= esc.get('texto') or esc.get('narracion') or ''
    return (t.get(idi) or '') if isinstance(t, dict) else str(t)


def que_se_decia(ep, idi, seg, dur):
    """Escena que sonaba en el segundo `seg` (aprox.: reparte la duracion por numero de palabras de cada escena)."""
    escenas= [texto_escena(e, idi) for e in partes_guion(ep) if isinstance(e, dict)]
    pesos= [max(1, len(t.split())) for t in escenas]
    if not escenas or not dur:
        return None
    total, acum= sum(pesos), 0
    for i, (t, w) in enumerate(zip(escenas, pesos)):
        acum+= w
        if seg <= dur * acum / total:
            return f'escena {i + 1}: {t[:90]}'
    return f'escena {len(escenas)}: {escenas[-1][:90]}'


def analizar_curva(filas, dur):
    """filas = [(ratio 0-1, audienceWatchRatio, relativeRetentionPerformance)]. Devuelve el resumen de la curva.
    Idea del lector de retencion de youtube-agent-skill (MIT): perdida en el gancho, caidas bruscas y deslizamiento."""
    if len(filas) < 8 or not dur:
        return None
    filas= sorted(filas)
    y0= filas[0][1] or 1.0
    corte= 3.0 if dur <= 180 else 30.0  # Short: los 3 primeros segundos; largo: los 30 primeros
    tras= [y for x, y, _ in filas if x * dur <= corte] or [filas[0][1]]
    caidas= []
    for (x0, a, _), (x1, b, _) in zip(filas, filas[1:]):
        if a - b > 0:
            caidas.append((round(100 * (a - b) / y0, 1), round(x0 * dur, 1)))
    caidas.sort(reverse=True)
    rel= [r for _, _, r in filas if r is not None]
    mitad= [100 * (a - b) / y0 for (x0, a, _), (x1, b, _) in zip(filas, filas[1:]) if x0 * dur > corte]
    return {'duracion': dur, 'inicio': round(y0, 3), 'corte_gancho_s': corte,
            'pierde_gancho_pct': round(100 * (y0 - tras[-1]) / y0, 1),
            'caidas': [{'seg': s_, 'pierde_pct': p} for p, s_ in caidas[:3] if p >= 1.0],
            'final_pct': round(100 * filas[-1][1] / y0, 1),
            'desliza_pct_por_punto': round(sum(mitad) / len(mitad), 2) if mitad else None,
            'vs_parecidos': round(sum(rel) / len(rel), 2) if rel else None}


def retencion(ya, hoy, filas, videos, por_titulo):
    """Curva de retencion por segundo de los videos mas vistos (>= MIN_VISTAS) y donde se va la gente."""
    out= {}
    for f in [f for f in filas if f['views'] >= MIN_VISTAS][:RET_MAX]:
        vid= f['video']
        v= videos.get(vid, {})
        dur= segundos(v.get('duracion'))
        try:
            r= tabla(ya.reports().query(ids='channel==MINE', startDate=INICIO, endDate=hoy,
                                        metrics='audienceWatchRatio,relativeRetentionPerformance',
                                        dimensions='elapsedVideoTimeRatio', filters=f'video=={vid}').execute())
        except Exception as e:
            out[vid]= {'error': str(e)[:160]}
            continue
        a= analizar_curva([(x['elapsedVideoTimeRatio'], x['audienceWatchRatio'], x.get('relativeRetentionPerformance'))
                           for x in r], dur)
        if not a:
            continue
        g= por_titulo.get((v.get('titulo') or '').strip())
        if g:
            ruta, idi, ep= g
            a['guion']= ruta
            for c in a['caidas']:
                c['se_decia']= que_se_decia(ep, idi, c['seg'], dur)
            primera= ganchos.primera_frase(texto_escena((partes_guion(ep) or [{}])[0], idi))
            fm= (ep.get('gancho') or {}).get('formula') if isinstance(ep.get('gancho'), dict) else None
            a['gancho']= primera[:120]
            a['formula']= fm or ganchos.clasificar(primera)[0]
        else:
            a['formula']= ganchos.clasificar(v.get('titulo', ''))[0] + ' (titulo)'
        a['pct_visto']= f['averageViewPercentage']
        a['vistas']= f['views']
        out[vid]= a
    return out


def por_formula(ret):
    """Media de perdida en el gancho y de % visto por formula de gancho (solo videos con MIN_VISTAS o mas)."""
    g= {}
    for a in ret.values():
        if 'error' in a or 'formula' not in a:
            continue
        x= g.setdefault(a['formula'].replace(' (titulo)', ''), {'n': 0, 'pierde': 0.0, 'visto': 0.0})
        x['n']+= 1
        x['pierde']+= a['pierde_gancho_pct']
        x['visto']+= a['pct_visto']
    return sorted(((k, x['n'], round(x['pierde'] / x['n'], 1), round(x['visto'] / x['n'], 1)) for k, x in g.items()),
                  key=lambda t: t[2])


def senales(d):
    """Las 5 senales de crecimiento de un canal a partir de lo ya recogido."""
    a= d['analitica']
    filas= a.get('por_video') if isinstance(a.get('por_video'), list) else []
    s= {}
    total= sum(f['views'] for f in filas)
    # 2. % de vistas de suscritos (aproximacion a recurrentes)
    sus= a.get('suscritos_o_no') if isinstance(a.get('suscritos_o_no'), list) else []
    vs= sum(x['views'] for x in sus)
    s['pct_suscritos']= round(100 * sum(x['views'] for x in sus if x['subscribedStatus'] == 'SUBSCRIBED') / vs, 1) if vs else None
    # 3. comentarios por cada 1.000 vistas
    coms= sum(f['comments'] for f in filas)
    s['comentarios_por_mil']= round(1000 * coms / total, 1) if total else None
    # 5. busqueda
    org= a.get('origen_trafico') if isinstance(a.get('origen_trafico'), list) else []
    vo= sum(x['views'] for x in org)
    s['pct_busqueda']= round(100 * sum(x['views'] for x in org if x['insightTrafficSourceType'] == 'YT_SEARCH') / vo, 1) if vo else None
    s['terminos']= [(x['insightTrafficSourceDetail'], x['views']) for x in a.get('terminos_busqueda') or []
                    if isinstance(x, dict)][:10]
    # 4. destacados: >= DESTACA_X veces la mediana de vistas del canal y al menos MIN_VISTAS
    vistas= sorted(f['views'] for f in filas)
    mediana= vistas[len(vistas) // 2] if vistas else 0
    s['mediana_vistas']= mediana
    s['destacados']= [{'video': f['video'], 'titulo': d['videos'].get(f['video'], {}).get('titulo', f['video']),
                       'vistas': f['views'], 'veces_mediana': round(f['views'] / mediana, 1) if mediana else None}
                      for f in filas if f['views'] >= MIN_VISTAS and f['views'] >= DESTACA_X * max(mediana, 1)][:5]
    return s


def comentarios(yt, videos, desde):
    # voy video a video: la consulta de todo el canal pide mas permisos de los que tienen los tokens
    nuevos= []
    for vid, v in videos.items():
        if v['privacidad'] != 'public':  # los privados no tienen comentarios publicos
            continue
        try:
            r= (LECTOR or yt).commentThreads().list(part='snippet', videoId=vid, maxResults=100, order='time',
                                        textFormat='plainText').execute()
        except Exception as e:
            nuevos.append({'video': vid, 'error': str(e)[:150]})
            continue
        for t in r['items']:
            c= t['snippet']['topLevelComment']['snippet']
            if c['publishedAt'] < desde:
                continue
            nuevos.append({'video': vid, 'autor': c.get('authorDisplayName'), 'texto': c['textDisplay'],
                           'likes': c.get('likeCount', 0), 'fecha': c['publishedAt'],
                           'respuestas': t['snippet'].get('totalReplyCount', 0)})
    return nuevos


def resumen_comentarios(yt, videos, canal_id):
    # todos los comentarios de primer nivel de cada video publico y cuantos no tienen respuesta del canal
    total, sin_responder, pendientes= 0, 0, []
    for vid, v in videos.items():
        if v['privacidad'] != 'public' or not v['comentarios_publicos']:
            continue
        try:
            r= (LECTOR or yt).commentThreads().list(part='snippet,replies', videoId=vid, maxResults=100,
                                                    textFormat='plainText').execute()
        except Exception:
            continue
        for t in r['items']:
            c= t['snippet']['topLevelComment']['snippet']
            if c.get('authorChannelId', {}).get('value') == canal_id:
                continue  # comentario del propio canal
            total+= 1
            respuestas= t.get('replies', {}).get('comments', [])
            if not any(x['snippet'].get('authorChannelId', {}).get('value') == canal_id for x in respuestas):
                sin_responder+= 1
                pendientes.append({'video': vid, 'texto': c['textDisplay'][:200]})
    return {'total': total, 'sin_responder': sin_responder, 'pendientes': pendientes}


def informe_md(hoy, todo):
    l= [f'# Informe de los canales {hoy}', '']
    for canal, d in todo.items():
        l.append(f'## {CANALES[canal]}')
        if 'error' in d:
            l+= [f'Error: {d["error"]}', '']
            continue
        l.append(f'Suscriptores: {d["suscriptores"]}. Videos: {len(d["videos"])}.')
        s= d.get('senales') or {}
        al= d.get('alcance') or {}
        imp= al.get('por_video') or {}
        l+= ['', '### Senales de crecimiento',
             f'- Impresiones (miniaturas, ultimos {al.get("dias", "?")} dias): '
             + (f'{sum(x["impresiones"] for x in imp.values())}, CTR medio '
                f'{(sum(x["ctr"]*x["impresiones"] for x in imp.values())/max(1, sum(x["impresiones"] for x in imp.values()))):.1f}%'
                if imp else al.get('error') or al.get('aviso') or 'sin datos')
             + '. Si suben sin que suban las vistas, YouTube esta probando el video: mejorar titulo y miniatura.',
             f'- % de vistas de suscritos (la API no da "recurrentes"; es lo mas parecido): {s.get("pct_suscritos", "?")}%',
             f'- Comentarios por cada 1.000 vistas: {s.get("comentarios_por_mil", "?")}',
             f'- % de vistas desde la busqueda de YouTube: {s.get("pct_busqueda", "?")}%'
             + (' | buscan: ' + ', '.join(f'"{t}" ({v})' for t, v in s['terminos']) if s.get('terminos') else ''),
             f'- Destacados (>= {DESTACA_X}x la mediana de {s.get("mediana_vistas", "?")} vistas): '
             + ('; '.join(f'{x["titulo"]} ({x["vistas"]} vistas, x{x["veces_mediana"]})' for x in s.get('destacados', []))
                or 'ninguno') + '. Sacar pronto mas del mismo estilo (mismo nicho, formato, titulo y miniatura parecidos).']
        ret= {k: v for k, v in (d.get('retencion') or {}).items() if 'error' not in v}
        errs= [v['error'] for v in (d.get('retencion') or {}).values() if 'error' in v]
        if ret or errs:
            l+= ['', '### Donde se va la gente (retencion por segundo, videos con 100 vistas o mas)',
                 'Pierde en el gancho = % del publico inicial que se va en los 3 primeros segundos (Short) o 30 (largo); '
                 'en Shorts, por debajo de 25 va bien. Caida = el momento con la bajada mas brusca y lo que sonaba ahi (aprox., '
                 'por palabras de cada escena). vs parecidos: 0,5 = igual que videos de la misma duracion en YouTube; mas es mejor.',
                 '', '| video | dur | pierde en el gancho | mayor caida | final | vs parecidos | formula |', '|---|---|---|---|---|---|---|']
            for vid, a in sorted(ret.items(), key=lambda kv: -kv[1]['pierde_gancho_pct']):
                tit= d['videos'].get(vid, {}).get('titulo', vid).replace('|', '/')[:50]
                c= a['caidas'][0] if a['caidas'] else None
                caida= (f'-{c["pierde_pct"]}% en el seg {c["seg"]:.0f}' + (f' ({c["se_decia"]})' if c.get('se_decia') else '')
                        if c else 'ninguna brusca').replace('|', '/')
                l.append(f'| {tit} | {a["duracion"]} s | {a["pierde_gancho_pct"]}% | {caida} | {a["final_pct"]}% | '
                         f'{a["vs_parecidos"] if a["vs_parecidos"] is not None else "?"} | {a["formula"]} |')
            pf= por_formula(ret)
            if pf:
                l+= ['', 'Por formula de gancho (menos perdida = mejor; con pocas muestras es solo una pista): '
                     + '; '.join(f'{k}: {n} videos, pierde {p}% en el gancho, {v}% visto' for k, n, p, v in pf)]
            if errs:
                l.append(f'No se pudo leer la curva de {len(errs)} videos: {errs[0]}')
        filas= d['analitica'].get('por_video')
        if isinstance(filas, list) and filas:
            vis= sum(f['views'] for f in filas)
            media= sum(f['averageViewPercentage']*f['views'] for f in filas)/vis if vis else 0
            bajos= sum(1 for f in filas if f['averageViewPercentage'] < OBJETIVO_PCT_VISTO)
            l+= ['', f'% visto medio (ponderado por vistas): {media:.0f}%. Objetivo Shorts: {OBJETIVO_PCT_VISTO}% o mas '
                     f'(lo ideal, mas de 100% = lo ven otra vez). Por debajo: {bajos} de {len(filas)} videos (marcados con *).',
                 'El swipe rate (se quedan vs deslizan) solo sale en Studio, no en la API.']
            l+= ['', 'Videos por vistas (vistas, % visto de media, likes, compartidos, subs ganados, '
                     'impresiones y CTR si hay, % busqueda en los mas vistos):']
            tpv= d['analitica'].get('trafico_por_video') or {}
            for f in filas:
                v= d['videos'].get(f['video'], {})
                extra= ''
                if f['video'] in imp:
                    extra+= f', {imp[f["video"]]["impresiones"]} impresiones, CTR {imp[f["video"]]["ctr"]}%'
                if f['video'] in tpv and sum(tpv[f['video']].values()):
                    extra+= f', {100 * tpv[f["video"]].get("YT_SEARCH", 0) / sum(tpv[f["video"]].values()):.0f}% busqueda'
                l.append(f'- {"* " if f["averageViewPercentage"] < OBJETIVO_PCT_VISTO else ""}{v.get("titulo", f["video"])} [{v.get("publicado", "")[:16]}]: {f["views"]} vistas, '
                         f'{f["averageViewPercentage"]:.0f}% visto, {f["likes"]} likes, {f["shares"]} compartidos, '
                         f'+{f["subscribersGained"]} subs{extra}')
        else:
            l.append('Aun no hay analitica (YouTube tarda 1-2 dias en dar datos).')
        errores= [c for c in d['comentarios_nuevos'] if 'error' in c]
        coms= [c for c in d['comentarios_nuevos'] if 'error' not in c]
        if errores:
            l.append(f'No pude leer los comentarios de {len(errores)} videos: {errores[0]["error"]}')
        res= d.get('comentarios_resumen', {})
        prog= sorted(v['programado'] for v in d['videos'].values() if v.get('programado'))
        l+= ['', f'Programados: {len(prog)}' + (f' (del {prog[0][:16]} al {prog[-1][:16]} UTC)' if prog else ''),
             f'Comentarios de primer nivel: {res.get("total", "?")}, sin responder: {res.get("sin_responder", "?")}',
             '', f'Comentarios nuevos: {len(coms)}']
        for c in coms[:40]:
            titulo= d['videos'].get(c['video'], {}).get('titulo', c['video'])
            l.append(f'- ({titulo}) {c["texto"][:300]!r} [{c["likes"]} likes]')
        l.append('')
    return '\n'.join(l)


def main(carpeta):
    ahora= dt.datetime.now(dt.timezone.utc)
    hoy= ahora.date().isoformat()
    desde= (ahora - dt.timedelta(days=2)).strftime('%Y-%m-%dT%H:%M:%SZ')  # solapo un dia por si falla una ejecucion
    os.makedirs(f'{carpeta}/{hoy}', exist_ok=True)
    todo= {}
    global POR_TITULO
    POR_TITULO= guiones()
    for canal in CANALES:
        cred= credenciales(canal)
        if not cred:
            print('sin token:', canal)
            continue
        try:
            yt= build('youtube', 'v3', credentials=cred)
            ya= build('youtubeAnalytics', 'v2', credentials=cred)
            info, videos= videos_del_canal(yt)
            todo[canal]= {'canal_id': info['id'], 'suscriptores': info['statistics'].get('subscriberCount'),
                          'videos': videos, 'analitica': analitica(ya, hoy),
                          'comentarios_nuevos': comentarios(yt, videos, desde),
                          'comentarios_resumen': resumen_comentarios(yt, videos, info['id']),
                          'alcance': alcance(cred)}
            todo[canal]['senales']= senales(todo[canal])
            filas= todo[canal]['analitica'].get('por_video')
            todo[canal]['retencion']= retencion(ya, hoy, filas, videos, POR_TITULO) if isinstance(filas, list) else {}
        except Exception as e:
            todo[canal]= {'error': str(e)[:300]}
        print(canal, 'ok' if 'error' not in todo[canal] else todo[canal]['error'])
    json.dump(todo, open(f'{carpeta}/{hoy}/datos.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    open(f'{carpeta}/{hoy}/informe.md', 'w', encoding='utf-8').write(informe_md(hoy, todo))
    # impresiones por video y dia en un csv aparte (historial.csv mantiene sus columnas)
    with open(f'{carpeta}/impresiones.csv', 'a', newline='', encoding='utf-8') as f:
        w= csv.writer(f)
        if f.tell() == 0:
            w.writerow(['fecha', 'canal', 'video', 'impresiones_7d', 'ctr'])
        for canal, d in todo.items():
            for vid, i in ((d.get('alcance') or {}).get('por_video') or {}).items():
                w.writerow([hoy, canal, vid, i['impresiones'], i['ctr']])
    # historial: una fila por video y dia, para ver vistas a las 24 h, 48 h... segun la hora de publicacion
    ruta= f'{carpeta}/historial.csv'
    nuevo= not os.path.exists(ruta)
    with open(ruta, 'a', newline='', encoding='utf-8') as f:
        w= csv.writer(f)
        if nuevo:
            w.writerow(['fecha', 'canal', 'video', 'titulo', 'publicado', 'vistas', 'pct_visto', 'likes', 'comentarios',
                        'compartidos', 'subs'])
        for canal, d in todo.items():
            if 'error' in d:
                continue
            filas= d['analitica'].get('por_video')
            filas= {r['video']: r for r in filas} if isinstance(filas, list) else {}
            for vid, v in d['videos'].items():
                r= filas.get(vid, {})
                w.writerow([ahora.isoformat(timespec='minutes'), canal, vid, v['titulo'], v['publicado'],
                            v['vistas_publicas'], r.get('averageViewPercentage', ''), v['likes_publicos'],
                            v['comentarios_publicos'], r.get('shares', ''), r.get('subscribersGained', '')])


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'datos')
