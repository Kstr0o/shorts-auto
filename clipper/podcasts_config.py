"""Configura el canal de podcasts desde la nube, sin portatil y sin pegar nada en los ajustes de GitHub.

Todo se guarda CIFRADO (AES-256, clave = YT_CLIENT_SECRET, que solo tiene el repo) en la rama podcasts-nube, porque el repo
es publico:
  enlace                       imprime el enlace de autorizacion de YouTube (se abre, se elige el canal de podcasts y se
                               acepta; el navegador acaba en una pagina de error de 127.0.0.1: esa direccion lleva el codigo)
  youtube <direccion o codigo> cambia el codigo por el token de subida -> yt_token.enc
  fuente <clave> <enlace>      guarda el enlace de la carpeta de episodios de una campana -> fuentes.enc

podcasts.py lee los dos archivos si no existen los secretos YT_TOKEN_PODCASTS / FUENTES_PODCASTS.
"""
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request

REDIRECT = 'http://127.0.0.1:8765'
SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube.readonly',
          'https://www.googleapis.com/auth/yt-analytics.readonly']


def ocultar(valor):
    if valor:
        print(f'::add-mask::{valor}', flush=True)


def cifrar(texto, ruta):
    subprocess.run(['openssl', 'enc', '-aes-256-cbc', '-pbkdf2', '-salt', '-a', '-pass', 'env:YT_CLIENT_SECRET', '-out', ruta],
                   input=texto.encode(), check=True)


def descifrar(ruta):
    r = subprocess.run(['openssl', 'enc', '-d', '-aes-256-cbc', '-pbkdf2', '-a', '-pass', 'env:YT_CLIENT_SECRET', '-in', ruta],
                       capture_output=True)
    return r.stdout.decode().strip() if r.returncode == 0 else ''


def cargar(estado):
    """Pone en el entorno lo guardado en la rama (sin pisar los secretos si existen)."""
    if not os.environ.get('YT_CLIENT_SECRET'):
        return
    tok = os.path.join(estado, 'yt_token.enc')
    if not os.environ.get('YT_TOKEN_PODCASTS') and os.path.exists(tok):
        v = descifrar(tok); ocultar(v)
        if v:
            os.environ['YT_TOKEN_PODCASTS'] = v
    fue = os.path.join(estado, 'fuentes.enc')
    if os.path.exists(fue):
        try:
            guardadas = json.loads(descifrar(fue) or '{}')
        except ValueError:
            guardadas = {}
        for v in guardadas.values():
            ocultar(v)
        try:
            actuales = json.loads(os.environ.get('FUENTES_PODCASTS') or '{}')
        except ValueError:
            actuales = {}
        os.environ['FUENTES_PODCASTS'] = json.dumps({**guardadas, **actuales})


def enlace():
    q = {'client_id': os.environ['YT_CLIENT_ID'], 'redirect_uri': REDIRECT, 'response_type': 'code', 'scope': ' '.join(SCOPES),
         'access_type': 'offline', 'prompt': 'consent select_account'}
    print('\nABRE ESTE ENLACE, elige el canal de podcasts y acepta:\n')
    print('https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode(q))
    print('\nAl final el navegador dara error en 127.0.0.1: copia esa direccion entera y pegala en "codigo_youtube".\n')


def youtube(entrada, estado):
    codigo = entrada.strip()
    if codigo.startswith('http'):
        codigo = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(codigo).query)).get('code', '')
    ocultar(codigo)
    datos = urllib.parse.urlencode({'code': codigo, 'client_id': os.environ['YT_CLIENT_ID'],
                                    'client_secret': os.environ['YT_CLIENT_SECRET'], 'redirect_uri': REDIRECT,
                                    'grant_type': 'authorization_code'}).encode()
    try:
        r = json.load(urllib.request.urlopen(urllib.request.Request('https://oauth2.googleapis.com/token', data=datos), timeout=30))
    except urllib.error.HTTPError as e:
        sys.exit(f'Google rechazo el codigo ({e.code}): {e.read().decode()[:200]}. Vuelve a abrir el enlace (el codigo caduca en minutos).')
    ocultar(r.get('access_token')); ocultar(r.get('refresh_token'))
    if not r.get('refresh_token'):
        sys.exit('Google no devolvio token de refresco: vuelve a abrir el enlace y acepta todos los permisos')
    cifrar(r['refresh_token'], os.path.join(estado, 'yt_token.enc'))
    # compruebo a que canal apunta (sin imprimir nada secreto)
    req = urllib.request.Request('https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true',
                                 headers={'Authorization': 'Bearer ' + r['access_token']})
    try:
        canal = json.load(urllib.request.urlopen(req, timeout=30))['items'][0]['snippet']
        print('Token guardado para el canal:', canal['title'], canal.get('customUrl', ''))
    except Exception as e:
        print('Token guardado (no pude leer el nombre del canal:', type(e).__name__, ')')


def fuente(clave, url, estado):
    ocultar(url)
    ruta = os.path.join(estado, 'fuentes.enc')
    try:
        todas = json.loads(descifrar(ruta) or '{}') if os.path.exists(ruta) else {}
    except ValueError:
        todas = {}
    todas[clave] = url.strip()
    cifrar(json.dumps(todas), ruta)
    print(f'Enlace de {clave} guardado (cifrado).')


if __name__ == '__main__':
    estado = os.environ.get('ESTADO', '../podcasts-nube')
    if sys.argv[1] == 'enlace':
        enlace()
    elif sys.argv[1] == 'youtube':
        youtube(sys.argv[2], estado)
    elif sys.argv[1] == 'fuente':
        fuente(sys.argv[2], sys.argv[3], estado)
