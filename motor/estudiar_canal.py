"""Saca los datos publicos de un canal de YouTube para estudiarlo (solo lectura, con la clave de API).

Uso: python3 motor/estudiar_canal.py @handle carpeta_salida
Deja carpeta_salida/<handle>.json con el canal y todos sus videos (fecha, duracion, vistas, likes, comentarios).
"""
import json
import os
import sys

from googleapiclient.discovery import build


def main(handle, carpeta):
    yt= build('youtube', 'v3', developerKey=os.environ['YT_API_KEY'])
    c= yt.channels().list(part='snippet,statistics,contentDetails,brandingSettings', forHandle=handle).execute()['items'][0]
    lista= c['contentDetails']['relatedPlaylists']['uploads']
    ids, pagina= [], None
    while True:
        r= yt.playlistItems().list(part='contentDetails', playlistId=lista, maxResults=50, pageToken=pagina).execute()
        ids+= [i['contentDetails']['videoId'] for i in r['items']]
        pagina= r.get('nextPageToken')
        if not pagina or len(ids) >= 2000:
            break
    videos= []
    for i in range(0, len(ids), 50):
        r= yt.videos().list(part='snippet,statistics,contentDetails,status', id=','.join(ids[i:i + 50])).execute()
        for v in r['items']:
            s= v['statistics']
            videos.append({'id': v['id'], 'titulo': v['snippet']['title'], 'publicado': v['snippet']['publishedAt'],
                           'duracion': v['contentDetails']['duration'], 'vistas': int(s.get('viewCount', 0)),
                           'likes': int(s.get('likeCount', 0)), 'comentarios': int(s.get('commentCount', 0)),
                           'descripcion': v['snippet'].get('description', '')[:300],
                           'tags': v['snippet'].get('tags', [])[:15],
                           'idioma': v['snippet'].get('defaultAudioLanguage'),
                           'sintetico': v['status'].get('containsSyntheticMedia')})
    # comentarios mas votados de los 5 videos mas vistos, para ver que pide su publico
    top= sorted(videos, key=lambda v: -v['vistas'])[:5]
    for v in top:
        try:
            r= yt.commentThreads().list(part='snippet', videoId=v['id'], maxResults=20, order='relevance',
                                        textFormat='plainText').execute()
            v['comentarios_top']= [{'texto': t['snippet']['topLevelComment']['snippet']['textDisplay'][:200],
                                    'likes': t['snippet']['topLevelComment']['snippet'].get('likeCount', 0)}
                                   for t in r['items']]
        except Exception as e:
            v['comentarios_top']= [{'error': str(e)[:100]}]
    salida= {'canal': {'id': c['id'], 'titulo': c['snippet']['title'], 'creado': c['snippet']['publishedAt'],
                       'descripcion': c['snippet'].get('description', ''), 'pais': c['snippet'].get('country'),
                       'suscriptores': c['statistics'].get('subscriberCount'), 'vistas': c['statistics'].get('viewCount'),
                       'n_videos': c['statistics'].get('videoCount')},
             'videos': videos}
    os.makedirs(carpeta, exist_ok=True)
    json.dump(salida, open(f'{carpeta}/{handle.lstrip("@")}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(salida['canal'], len(videos), 'videos')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
