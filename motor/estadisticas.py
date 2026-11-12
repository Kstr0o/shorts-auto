"""Recoge cada dia las estadisticas y los comentarios de los 4 canales.

Uso: python3 motor/estadisticas.py datos
Deja en datos/:
  historial.csv          una fila por video y dia (vistas, retencion, likes...), para ver como crece cada video
  AAAA-MM-DD/informe.md  resumen legible: mejores y peores videos, publico, comentarios nuevos
  AAAA-MM-DD/datos.json  lo mismo en bruto, para analizarlo
Variables: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_TOKEN_<CANAL>. Los tokens necesitan los permisos
youtube.readonly y yt-analytics.readonly (ver obtener_token.py). Un canal sin token se salta.
Gasta muy poca cuota de la API (unas decenas de unidades por canal).
"""
import csv
import datetime as dt
import json
import os
import sys

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

CANALES= {'TONI_ES': 'Historias Sin Blanca', 'TONI_EN': 'Broke Toons',
          'YSI_ES': 'El Laboratorio del Y Si', 'YSI_EN': 'The Mad Maybe Lab'}
METRICAS= 'views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,likes,comments,shares,subscribersGained'
INICIO= '2026-11-01'


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
                              'privacidad': v['status']['privacyStatus'], 'duracion': v['contentDetails']['duration'],
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
    }
    for nombre, q in consultas.items():
        try:
            salida[nombre]= tabla(ya.reports().query(**base, **q).execute())
        except Exception as e:  # con canales nuevos algunas consultas aun no devuelven nada
            salida[nombre]= {'error': str(e)[:200]}
    return salida


def comentarios(yt, videos, desde):
    # voy video a video: la consulta de todo el canal pide mas permisos de los que tienen los tokens
    nuevos= []
    for vid in videos:
        try:
            r= yt.commentThreads().list(part='snippet', videoId=vid, maxResults=100, order='time',
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


def informe_md(hoy, todo):
    l= [f'# Informe de los canales {hoy}', '']
    for canal, d in todo.items():
        l.append(f'## {CANALES[canal]}')
        if 'error' in d:
            l+= [f'Error: {d["error"]}', '']
            continue
        l.append(f'Suscriptores: {d["suscriptores"]}. Videos: {len(d["videos"])}.')
        filas= d['analitica'].get('por_video')
        if isinstance(filas, list) and filas:
            l+= ['', 'Videos por vistas (vistas, % visto de media, likes, compartidos, subs ganados):']
            for f in filas:
                v= d['videos'].get(f['video'], {})
                l.append(f'- {v.get("titulo", f["video"])} [{v.get("publicado", "")[:16]}]: {f["views"]} vistas, '
                         f'{f["averageViewPercentage"]:.0f}% visto, {f["likes"]} likes, {f["shares"]} compartidos, '
                         f'+{f["subscribersGained"]} subs')
        else:
            l.append('Aun no hay analitica (YouTube tarda 1-2 dias en dar datos).')
        errores= [c for c in d['comentarios_nuevos'] if 'error' in c]
        coms= [c for c in d['comentarios_nuevos'] if 'error' not in c]
        if errores:
            l.append(f'No pude leer los comentarios de {len(errores)} videos: {errores[0]["error"]}')
        l+= ['', f'Comentarios nuevos: {len(coms)}']
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
                          'comentarios_nuevos': comentarios(yt, videos, desde)}
        except Exception as e:
            todo[canal]= {'error': str(e)[:300]}
        print(canal, 'ok' if 'error' not in todo[canal] else todo[canal]['error'])
    json.dump(todo, open(f'{carpeta}/{hoy}/datos.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    open(f'{carpeta}/{hoy}/informe.md', 'w', encoding='utf-8').write(informe_md(hoy, todo))
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
