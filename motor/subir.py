"""Sube un Short a YouTube con la API oficial.

Uso: python3 subir.py salida/ep001_es.mp4 salida/ep001_es.json CANAL
CANAL es el sufijo del secreto con el refresh token, p. ej. TONI_ES -> YT_TOKEN_TONI_ES (canal de clips: CLIPS -> YT_TOKEN_CLIPS)
Variables: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_TOKEN_<CANAL>, YT_PRIVACIDAD (private | public)
"""
import json
import os
import sys

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

AVISO_IA= {'es': 'Voz e imágenes creadas con herramientas de IA.', 'en': 'Voice and visuals created with AI tools.'}


def con_aviso_ia(descripcion, idioma, sintetico):
    """Linea de transparencia al final de la descripcion (ley de IA espanola y art. 50 del reglamento europeo). Los clips reales no la llevan."""
    if not sintetico:
        return descripcion
    aviso= AVISO_IA['es' if str(idioma).lower().startswith('es') else 'en']
    if aviso in descripcion:
        return descripcion
    return descripcion.rstrip()[:5000 - len(aviso) - 2] + '\n\n' + aviso if descripcion.strip() else aviso


def subir(mp4, meta_json, canal, publicar_a=None):
    """publicar_a: hora ISO en UTC (2026-11-13T14:00:00Z) para dejarlo programado; YouTube lo exige en privado hasta entonces."""
    meta= json.load(open(meta_json, encoding='utf-8'))
    es_clip= meta.get('formato') == 'clip'
    if es_clip and str(meta.get('fuente', '')).startswith('http') and canal in ('TONI_ES', 'TONI_EN', 'YSI_ES', 'YSI_EN'):
        # clips de videos ajenos nunca a los 4 canales de siempre (avisos de copyright pueden arrastrar la cuenta)
        sys.exit(f'clip de {meta["fuente"]} bloqueado en {canal}: usar un canal de clips en otra cuenta de Google')
    cred= Credentials(None, refresh_token=os.environ[f'YT_TOKEN_{canal}'], client_id=os.environ['YT_CLIENT_ID'],
                      client_secret=os.environ['YT_CLIENT_SECRET'], token_uri='https://oauth2.googleapis.com/token')
    yt= build('youtube', 'v3', credentials=cred)
    sintetico= meta.get('sintetico', True)
    cuerpo= {
        'snippet': {'title': meta['titulo'][:100], 'description': con_aviso_ia(meta['descripcion'], meta.get('idioma', 'en'), sintetico), 'tags': meta.get('tags', []),
                    'categoryId': str(meta['categoria']) if meta.get('categoria') else '24' if es_clip or str(meta.get('formato', '')).startswith('cuento') else ('23' if canal.startswith('TONI') else '27'),
                    'defaultLanguage': meta['idioma'], 'defaultAudioLanguage': meta['idioma']},
        'status': {'privacyStatus': os.environ.get('YT_PRIVACIDAD', 'private'), 'selfDeclaredMadeForKids': False,
                   'containsSyntheticMedia': sintetico},  # marco que es generado salvo clips de video real
    }
    if publicar_a:
        cuerpo['status']['privacyStatus']= 'private'
        cuerpo['status']['publishAt']= publicar_a
    req= yt.videos().insert(part='snippet,status', body=cuerpo, media_body=MediaFileUpload(mp4, chunksize=-1, resumable=True))
    resp= None
    while resp is None:
        _, resp= req.next_chunk()
    print('subido:', 'https://youtube.com/shorts/' + resp['id'])
    mini= meta.get('miniatura')
    if mini:
        ruta= os.path.join(os.path.dirname(mp4), mini)
        try:
            yt.thumbnails().set(videoId=resp['id'], media_body=MediaFileUpload(ruta)).execute(); print('miniatura puesta:', mini)
        except Exception as e:
            print('miniatura NO puesta:', str(e)[:200])
    if publicar_a:
        # compruebo como lo ha dejado YouTube: debe seguir programado, no privado sin fecha
        try:
            st= yt.videos().list(part='status', id=resp['id']).execute()['items'][0]['status']
            print('estado:', resp['id'], st.get('privacyStatus'), 'publishAt=', st.get('publishAt'))
        except Exception as e:  # el token del canal de clips solo tiene permiso de subida: no puede leer
            print('estado: sin permiso de lectura para comprobarlo', type(e).__name__)
    return resp['id']


if __name__ == '__main__':
    subir(sys.argv[1], sys.argv[2], sys.argv[3])
