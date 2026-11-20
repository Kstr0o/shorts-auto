"""TikTok del canal de clips (Daily Streamer Clips): manda cada clip ya editado a la bandeja de TikTok como BORRADOR.

Content Posting API, modo "Upload to TikTok" (scope video.upload): el clip llega al buzon de la app y el dueno lo
publica a mano desde el movil (pie, hashtags y envio a Content Rewards). Asi no hace falta la revision de TikTok para
publicar en directo, y la cuenta no parece un bot.

  token <codigo>          cambia el codigo de autorizacion (pagina tiktok-callback) por el token y lo guarda cifrado
  subir <carpeta>         manda a TikTok los clips de esta noche que ya se programaron en YouTube

Claves (secretos del repo, no se imprimen): TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET.
El token de refresco vive CIFRADO (AES-256, clave = TIKTOK_CLIENT_SECRET) en la rama clips-nube, tiktok_token.enc,
porque el repo es publico y TikTok lo renueva en cada uso.
"""
import argparse
import glob
import json
import math
import os
import subprocess
import sys
import urllib.parse
import urllib.request

API = 'https://open.tiktokapis.com/v2'
REDIRECT = 'https://kstr0o.github.io/shorts-auto-privacidad/tiktok-callback.html'
TROZO = 10 * 1024 * 1024  # TikTok pide trozos de 5-64 MB (el ultimo puede ser mayor)


def leer(ruta, defecto):
    try:
        return json.load(open(ruta, encoding='utf-8'))
    except (OSError, ValueError):
        return defecto


def guardar(ruta, datos):
    json.dump(datos, open(ruta, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def ocultar(valor):
    if valor and os.environ.get('GITHUB_ACTIONS'):
        print(f'::add-mask::{valor}', flush=True)


def peticion(url, datos=None, token=None, form=False):
    cab = {'Authorization': f'Bearer {token}'} if token else {}
    if form:
        cuerpo = urllib.parse.urlencode(datos).encode()
        cab['Content-Type'] = 'application/x-www-form-urlencoded'
    else:
        cuerpo = json.dumps(datos).encode()
        cab['Content-Type'] = 'application/json; charset=UTF-8'
    try:
        return json.load(urllib.request.urlopen(urllib.request.Request(url, data=cuerpo, headers=cab), timeout=60))
    except urllib.error.HTTPError as e:
        return json.loads(e.read() or b'{}') or {'error': {'code': str(e.code)}}


# ---------- token cifrado ----------
def cifrar(texto, ruta):
    subprocess.run(['openssl', 'enc', '-aes-256-cbc', '-pbkdf2', '-salt', '-a', '-pass', 'env:TIKTOK_CLIENT_SECRET',
                    '-out', ruta], input=texto.encode(), check=True)


def descifrar(ruta):
    r = subprocess.run(['openssl', 'enc', '-d', '-aes-256-cbc', '-pbkdf2', '-a', '-pass', 'env:TIKTOK_CLIENT_SECRET',
                        '-in', ruta], capture_output=True, check=True)
    return r.stdout.decode().strip()


def guardar_token(r, estado):
    if not r.get('refresh_token'):
        sys.exit(f"TikTok no devolvio token: {r.get('error')} {r.get('error_description', '')}")
    ocultar(r.get('access_token')); ocultar(r['refresh_token'])
    cifrar(r['refresh_token'], os.path.join(estado, 'tiktok_token.enc'))
    return r['access_token']


def token_nuevo(codigo, estado):
    r = peticion(f'{API}/oauth/token/', {'client_key': os.environ['TIKTOK_CLIENT_KEY'],
                                         'client_secret': os.environ['TIKTOK_CLIENT_SECRET'],
                                         'code': urllib.parse.unquote(codigo.strip()), 'grant_type': 'authorization_code',
                                         'redirect_uri': REDIRECT}, form=True)
    guardar_token(r, estado)
    print(f"token guardado (cuenta {r.get('open_id', '?')[:6]}..., permisos: {r.get('scope')})")


def acceso(estado):
    ruta = os.path.join(estado, 'tiktok_token.enc')
    if not os.path.exists(ruta) or not os.environ.get('TIKTOK_CLIENT_SECRET'):
        return None
    viejo = descifrar(ruta); ocultar(viejo)
    r = peticion(f'{API}/oauth/token/', {'client_key': os.environ['TIKTOK_CLIENT_KEY'],
                                         'client_secret': os.environ['TIKTOK_CLIENT_SECRET'],
                                         'grant_type': 'refresh_token', 'refresh_token': viejo}, form=True)
    return guardar_token(r, estado)


# ---------- subir borrador ----------
def subir_borrador(mp4, token):
    tam = os.path.getsize(mp4)
    trozo = tam if tam <= 64 * 1024 * 1024 else TROZO
    n = max(1, tam // trozo)
    r = peticion(f'{API}/post/publish/inbox/video/init/', {'source_info': {
        'source': 'FILE_UPLOAD', 'video_size': tam, 'chunk_size': trozo, 'total_chunk_count': n}}, token=token)
    if (r.get('error') or {}).get('code', 'ok') != 'ok':
        raise RuntimeError(f"init: {r['error'].get('code')} {r['error'].get('message', '')}")
    url, pid = r['data']['upload_url'], r['data']['publish_id']
    with open(mp4, 'rb') as f:
        for i in range(n):
            a = i * trozo
            b = tam - 1 if i == n - 1 else a + trozo - 1
            f.seek(a)
            req = urllib.request.Request(url, data=f.read(b - a + 1), method='PUT', headers={
                'Content-Type': 'video/mp4', 'Content-Length': str(b - a + 1), 'Content-Range': f'bytes {a}-{b}/{tam}'})
            urllib.request.urlopen(req, timeout=300).read()
    return pid


def subir(carpeta, estado):
    token = acceso(estado)
    if not token:
        print('TikTok sin configurar (falta tiktok_token.enc o los secretos): no se manda nada'); return
    reg = leer(os.path.join(estado, 'programados.json'), {'clips': []})
    metas = {leer(m, {}).get('id'): m for m in glob.glob(os.path.join(carpeta, '**', '*.json'), recursive=True)}
    enviados = 0
    for c in sorted(reg['clips'], key=lambda c: c.get('publishAt') or ''):
        m = metas.get(c['id'])
        if c.get('tiktok') or not m or not os.path.exists(m[:-5] + '.mp4'):
            continue
        try:
            c['tiktok'] = {'publish_id': subir_borrador(m[:-5] + '.mp4', token), 'estado': 'borrador'}
            enviados += 1
            print(f"  TikTok borrador: {c['titulo'][:60]}", flush=True)
        except Exception as e:
            print(f'  TikTok FALLO {type(e).__name__}: {str(e)[:200]}')
            if 'spam_risk' in str(e) or 'rate_limit' in str(e):
                break
        guardar(os.path.join(estado, 'programados.json'), reg)
    print(f'RESUMEN TikTok: {enviados} borradores en la bandeja')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('fase', choices=['token', 'subir'])
    ap.add_argument('arg', nargs='?')
    ap.add_argument('--estado', default='../clips-nube')
    a = ap.parse_args()
    if a.fase == 'token':
        token_nuevo(a.arg, a.estado)
    else:
        subir(a.arg or 'out/clips', a.estado)


if __name__ == '__main__':
    main()
