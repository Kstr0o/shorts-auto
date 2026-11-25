"""Sube un video ya aprobado (rama listos) al canal que le toca, o solo comprueba las claves.

Uso: python3 subir_listo.py comprobar
     python3 subir_listo.py subir listos/ep001_es.mp4
     python3 subir_listo.py subir listos/ep001_es@2026-11-14T12:00:00Z.mp4   (programado a esa hora UTC)
El canal sale del nombre del archivo: ep -> TONI, ysi -> YSI, y el idioma del sufijo.
"""
import os
import sys

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

CANALES= ['TONI_ES', 'TONI_EN', 'YSI_ES', 'YSI_EN']


def comprobar():
    # miro a que canal apunta cada clave, sin subir nada
    bien= True
    for canal in CANALES:
        try:
            cred= Credentials(None, refresh_token=os.environ[f'YT_TOKEN_{canal}'], client_id=os.environ['YT_CLIENT_ID'],
                              client_secret=os.environ['YT_CLIENT_SECRET'], token_uri='https://oauth2.googleapis.com/token')
            yt= build('youtube', 'v3', credentials=cred)
            r= yt.channels().list(part='snippet', mine=True).execute()
            print(f'{canal}: {r["items"][0]["snippet"]["title"]}')
        except Exception as e:
            bien= False
            print(f'{canal}: FALLO {type(e).__name__}: {str(e)[:200]}')
    return bien


def canal_de(mp4):
    nombre= os.path.basename(mp4).replace('.mp4', '')
    if nombre.startswith('his'):
        return 'TONI_ES'  # las series de historias en ingles van al antiguo canal de humor en espanol
    serie= 'TONI' if nombre.startswith('ep') else 'YSI'
    return f'{serie}_{nombre.split("_")[-1].upper()}'


def estado(pares):
    # pares: TONI_ES:idvideo ... ; digo como esta cada video (privado, programado o publico)
    for par in pares:
        canal, vid= par.split(':')
        cred= Credentials(None, refresh_token=os.environ[f'YT_TOKEN_{canal}'], client_id=os.environ['YT_CLIENT_ID'],
                          client_secret=os.environ['YT_CLIENT_SECRET'], token_uri='https://oauth2.googleapis.com/token')
        r= build('youtube', 'v3', credentials=cred).videos().list(part='status', id=vid).execute()
        st= r['items'][0]['status'] if r.get('items') else {}
        print('estado:', canal, vid, st.get('privacyStatus', 'NO ENCONTRADO'), 'publishAt=', st.get('publishAt'))


def canal(canales):
    # ultimos 15 videos de cada canal con los metadatos que importan, para comparar los subidos por API con los de Studio
    import json
    for c in canales:
        cred= Credentials(None, refresh_token=os.environ[f'YT_TOKEN_{c}'], client_id=os.environ['YT_CLIENT_ID'],
                          client_secret=os.environ['YT_CLIENT_SECRET'], token_uri='https://oauth2.googleapis.com/token')
        yt= build('youtube', 'v3', credentials=cred)
        lista= yt.channels().list(part='contentDetails', mine=True).execute()['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        ids= [i['contentDetails']['videoId'] for i in yt.playlistItems().list(part='contentDetails', playlistId=lista, maxResults=15).execute().get('items', [])]
        r= yt.videos().list(part='snippet,status,contentDetails,statistics,recordingDetails,fileDetails,processingDetails', id=','.join(ids)).execute()
        for v in r.get('items', []):
            sn, st, cd, fd= v['snippet'], v['status'], v['contentDetails'], v.get('fileDetails', {})
            vs= (fd.get('videoStreams') or [{}])[0]
            print('video:', json.dumps({'canal': c, 'id': v['id'], 'titulo': sn['title'][:60], 'publicado': sn.get('publishedAt'), 'cat': sn.get('categoryId'),
                  'idioma': sn.get('defaultLanguage'), 'audio': sn.get('defaultAudioLanguage'), 'tags': len(sn.get('tags', [])), 'desc': len(sn.get('description', '')),
                  'priv': st.get('privacyStatus'), 'publishAt': st.get('publishAt'), 'ninos': st.get('madeForKids'), 'autoninos': st.get('selfDeclaredMadeForKids'),
                  'sintetico': st.get('containsSyntheticMedia'), 'subida': st.get('uploadStatus'), 'licencia': st.get('license'), 'incrustable': st.get('embeddable'),
                  'dur': cd.get('duration'), 'def': cd.get('definition'), 'ancho': vs.get('widthPixels'), 'alto': vs.get('heightPixels'), 'fps': vs.get('frameRateFps'),
                  'archivo': fd.get('fileName'), 'proceso': v.get('processingDetails', {}).get('processingStatus'), 'grabacion': v.get('recordingDetails'),
                  'vistas': v.get('statistics', {}).get('viewCount')}, ensure_ascii=False))


AVISOS_IA= ['Voz e imágenes creadas con herramientas de IA.', 'Voice and visuals created with AI tools.']


def limpiar_aviso(canales):
    # busca en TODOS los videos del canal (tambien privados y programados) la linea de aviso de IA que metio #77 y la quita
    # solo cambia la descripcion: no toca titulo, etiquetas, estado ni hora programada
    import json
    for c in canales:
        cred= Credentials(None, refresh_token=os.environ[f'YT_TOKEN_{c}'], client_id=os.environ['YT_CLIENT_ID'],
                          client_secret=os.environ['YT_CLIENT_SECRET'], token_uri='https://oauth2.googleapis.com/token')
        yt= build('youtube', 'v3', credentials=cred)
        lista= yt.channels().list(part='contentDetails', mine=True).execute()['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        ids, pag= [], None
        while True:
            r= yt.playlistItems().list(part='contentDetails', playlistId=lista, maxResults=50, pageToken=pag).execute()
            ids+= [i['contentDetails']['videoId'] for i in r.get('items', [])]
            pag= r.get('nextPageToken')
            if not pag:
                break
        con, limpios= 0, 0
        for k in range(0, len(ids), 50):
            for v in yt.videos().list(part='snippet,status', id=','.join(ids[k:k + 50])).execute().get('items', []):
                sn= v['snippet']
                desc= sn.get('description', '')
                if not any(a in desc for a in AVISOS_IA):
                    continue
                con+= 1
                nueva= desc
                for a in AVISOS_IA:
                    nueva= nueva.replace('\n\n' + a, '').replace(a, '')
                nueva= nueva.rstrip()
                cuerpo= {'id': v['id'], 'snippet': {'title': sn['title'], 'description': nueva, 'categoryId': sn['categoryId'], 'tags': sn.get('tags', []),
                         **({'defaultLanguage': sn['defaultLanguage']} if sn.get('defaultLanguage') else {}),
                         **({'defaultAudioLanguage': sn['defaultAudioLanguage']} if sn.get('defaultAudioLanguage') else {})}}
                try:
                    yt.videos().update(part='snippet', body=cuerpo).execute()
                    limpios+= 1
                    res= 'LIMPIO'
                except Exception as e:
                    res= 'NO SE PUDO: ' + str(e)[:160]
                print('aviso:', json.dumps({'canal': c, 'id': v['id'], 'titulo': sn['title'][:70], 'priv': v['status'].get('privacyStatus'),
                      'publishAt': v['status'].get('publishAt'), 'resultado': res}, ensure_ascii=False))
        print(f'resumen {c}: {len(ids)} videos, {con} con aviso, {limpios} limpiados')


if __name__ == '__main__':
    if sys.argv[1] == 'comprobar':
        sys.exit(0 if comprobar() else 1)
    if sys.argv[1] == 'canal' and sys.argv[2:3] == ['LIMPIAR_AVISO']:
        limpiar_aviso(sys.argv[3:] or CANALES)
        sys.exit(0)
    if sys.argv[1] == 'canal':
        canal(sys.argv[2:])
        sys.exit(0)
    if sys.argv[1] == 'estado':
        estado(sys.argv[2:])
        sys.exit(0)
    import subir
    for arg in sys.argv[2:]:
        # listos/ep001_es.mp4 o, para dejarlo programado, listos/ep001_es@2026-11-14T12:00:00Z.mp4
        mp4, _, cuando= arg.replace('.mp4', '').partition('@')
        mp4+= '.mp4'
        subir.subir(mp4, mp4.replace('.mp4', '.json'), canal_de(mp4), cuando or None)
