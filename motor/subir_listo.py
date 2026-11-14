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


if __name__ == '__main__':
    if sys.argv[1] == 'comprobar':
        sys.exit(0 if comprobar() else 1)
    if sys.argv[1] == 'estado':
        estado(sys.argv[2:])
        sys.exit(0)
    import subir
    for arg in sys.argv[2:]:
        # listos/ep001_es.mp4 o, para dejarlo programado, listos/ep001_es@2026-11-14T12:00:00Z.mp4
        mp4, _, cuando= arg.replace('.mp4', '').partition('@')
        mp4+= '.mp4'
        subir.subir(mp4, mp4.replace('.mp4', '.json'), canal_de(mp4), cuando or None)
