"""Sube un video ya aprobado (rama listos) al canal que le toca, o solo comprueba las claves.

Uso: python3 subir_listo.py comprobar
     python3 subir_listo.py subir listos/ep001_es.mp4
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
    serie= 'TONI' if nombre.startswith('ep') else 'YSI'
    return f'{serie}_{nombre.split("_")[-1].upper()}'


if __name__ == '__main__':
    if sys.argv[1] == 'comprobar':
        sys.exit(0 if comprobar() else 1)
    import subir
    for mp4 in sys.argv[2:]:
        subir.subir(mp4, mp4.replace('.mp4', '.json'), canal_de(mp4))
