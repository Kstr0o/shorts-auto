"""Sube un Short a YouTube con la API oficial.

Uso: python3 subir.py salida/ep001_es.mp4 salida/ep001_es.json CANAL
CANAL es el sufijo del secreto con el refresh token, p. ej. TONI_ES -> YT_TOKEN_TONI_ES
Variables: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_TOKEN_<CANAL>, YT_PRIVACIDAD (private | public)
"""
import json
import os
import sys

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


def subir(mp4, meta_json, canal):
    meta= json.load(open(meta_json, encoding='utf-8'))
    cred= Credentials(None, refresh_token=os.environ[f'YT_TOKEN_{canal}'], client_id=os.environ['YT_CLIENT_ID'],
                      client_secret=os.environ['YT_CLIENT_SECRET'], token_uri='https://oauth2.googleapis.com/token')
    yt= build('youtube', 'v3', credentials=cred)
    cuerpo= {
        'snippet': {'title': meta['titulo'][:100], 'description': meta['descripcion'], 'tags': meta.get('tags', []),
                    'categoryId': '23' if canal.startswith('TONI') else '27',
                    'defaultLanguage': meta['idioma'], 'defaultAudioLanguage': meta['idioma']},
        'status': {'privacyStatus': os.environ.get('YT_PRIVACIDAD', 'private'), 'selfDeclaredMadeForKids': False,
                   'containsSyntheticMedia': True},  # marco siempre que es contenido generado
    }
    req= yt.videos().insert(part='snippet,status', body=cuerpo, media_body=MediaFileUpload(mp4, chunksize=-1, resumable=True))
    resp= None
    while resp is None:
        _, resp= req.next_chunk()
    print('subido:', 'https://youtube.com/shorts/' + resp['id'])
    return resp['id']


if __name__ == '__main__':
    subir(sys.argv[1], sys.argv[2], sys.argv[3])
