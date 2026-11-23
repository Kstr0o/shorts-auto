"""TikTok del canal de clips (Daily Streamer Clips): manda cada clip ya editado a la bandeja de TikTok como BORRADOR.

Content Posting API, modo "Upload to TikTok" (scope video.upload): el clip llega al buzon de la app y el dueno lo
publica a mano desde el movil (pie, hashtags y envio a Content Rewards). Asi no hace falta la revision de TikTok para
publicar en directo, y la cuenta no parece un bot.

  token <codigo>          cambia el codigo de autorizacion (pagina tiktok-callback) por el token y lo guarda cifrado
  subir <carpeta>         manda a TikTok los clips de esta noche que ya se programaron en YouTube

Al acabar avisa al movil (prioridad alta) de cuantos borradores entraron y si la bandeja se lleno (TikTok admite ~5
pendientes). El modo borrador no deja poner pie por API, asi que cada borrador manda al movil (ntfy, AVISO_TEMA) el pie con
hashtags listo para copiar y pegar, en el momento en que entra el borrador.

Claves (secretos del repo, no se imprimen): TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET.
El token de refresco vive CIFRADO (AES-256, clave = TIKTOK_CLIENT_SECRET) en la rama clips-nube, tiktok_token.enc,
porque el repo es publico y TikTok lo renueva en cada uso.
"""
import argparse
import datetime as dt
import glob
import json
import math
import os
import subprocess
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import palabras_tiktok as pt  # noqa: E402

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


# ---------- pie para TikTok ----------
def pie(c, meta):
    cfg = leer(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'streamers_nube.json'), {}).get(meta.get('key'), {})
    tags = ' '.join(t for t in [meta.get('hashtag') or cfg.get('hashtag'), '#GTA6'] if t)
    credito = cfg.get('credito') or meta.get('streamer') or ''
    titulo = meta.get('titulo_tiktok') or pt.limpiar(c['titulo'])
    return f"{titulo}\n\nCredit: {credito}\n\n{tags}".replace('\n\nCredit: \n', '\n')


def avisar_pie(c, texto, ya=False):
    # aviso al movil con el pie listo para copiar. Se programa para la hora de publicacion en YouTube (cuando el dueno
    # publica en TikTok y manda a Content Rewards): de noche llegaban 6-7 avisos juntos y alguno se perdia (22/11).
    tema = os.environ.get('AVISO_TEMA', '').strip()
    if not tema:
        return False
    nombre = c.get('streamer') or c['titulo'].split(' ')[0]
    cab = {'Title': f"TikTok: descripcion para {nombre} (manten pulsado para copiar)",
           'Tags': 'memo', 'Priority': 'high'}
    ahora = dt.datetime.now(dt.timezone.utc)
    try:
        cuando = dt.datetime.strptime(c.get('publishAt') or '', '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=dt.timezone.utc)
    except ValueError:
        cuando = None
    # ntfy admite avisos diferidos hasta 3 dias
    if not ya and cuando and ahora + dt.timedelta(minutes=1) < cuando < ahora + dt.timedelta(days=3) - dt.timedelta(minutes=5):
        cab['At'] = str(int(cuando.timestamp()))
    servidor = os.environ.get('AVISO_SERVIDOR', 'https://ntfy.sh').rstrip('/')
    req = urllib.request.Request(f'{servidor}/{tema}', data=texto.encode('utf-8'), headers=cab, method='POST')
    with urllib.request.urlopen(req, timeout=20) as r:
        return 200 <= r.status < 300


def avisar_resumen(enviados, quedan):
    # aviso al movil en cuanto la nube deja borradores (y si la bandeja se lleno), para que el dueno se entere
    tema = os.environ.get('AVISO_TEMA', '').strip()
    if not tema or not (enviados or quedan):
        return False
    hora = dt.datetime.now(dt.timezone.utc).astimezone(dt.timezone(dt.timedelta(hours=1))).strftime('%H:%M')
    texto = f'{enviados} borradores nuevos en tu bandeja de TikTok ({hora}). Abre TikTok > bandeja y publicalos con el pie que te llega de cada uno.'
    if quedan:
        texto += (f' La bandeja se lleno: {quedan} clips se quedan solo en YouTube. '
                  'Publica o borra los borradores para que manana entren los nuevos.')
    titulo = 'TikTok: bandeja llena' if quedan and not enviados else f'TikTok: {enviados} borradores listos'
    servidor = os.environ.get('AVISO_SERVIDOR', 'https://ntfy.sh').rstrip('/')
    req = urllib.request.Request(f'{servidor}/{tema}', data=texto.encode('utf-8'), method='POST',
                                 headers={'Title': titulo, 'Tags': 'warning' if quedan else 'inbox_tray', 'Priority': 'high'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return 200 <= r.status < 300


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
    prio = {k: int(v.get('prioridad', 5)) for k, v in
            leer(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'streamers_nube.json'), {}).items()}
    cola = [c for c in reg['clips'] if not c.get('tiktok') and metas.get(c['id']) and os.path.exists(metas[c['id']][:-5] + '.mp4')]
    # TikTok saca del feed "Para ti" lo insinuado/sexual aunque sea una escena del juego (22/11, clip de Jason y Lucia):
    # esos clips se quedan solo en YouTube
    # segunda red sin IA (23/11): aunque la seleccion no lo marcara, fuera si el titulo lleva algo sexual explicito o si la
    # franja quemada en el video lleva una insinuacion (eso ya no se puede cambiar en el borrador)
    def es_picante(c):
        m = leer(metas[c['id']], {})
        return bool(m.get('picante')) or pt.picante(c['titulo'], m.get('texto_arriba')) or pt.suave(m.get('texto_arriba'))
    fuera = [c for c in cola if es_picante(c)]
    for c in fuera:
        print(f"  solo YouTube (picante): {c['titulo'][:60]}")
    cola = [c for c in cola if c not in fuera]
    # TikTok solo admite ~5 borradores sin publicar: primero los mejores (nota del plan, luego prioridad del streamer)
    cola.sort(key=lambda c: (-float(leer(metas[c['id']], {}).get('nota') or 0), prio.get(leer(metas[c['id']], {}).get('key'), 5),
                             c.get('publishAt') or ''))
    enviados, llena = 0, False
    for c in cola:
        m = metas[c['id']]
        try:
            c['tiktok'] = {'publish_id': subir_borrador(m[:-5] + '.mp4', token), 'estado': 'borrador',
                           'pie': pie(c, leer(m, {}))}
            enviados += 1
            try:
                c['tiktok']['aviso'] = avisar_pie(c, c['tiktok']['pie'])
            except Exception as e:
                print('  aviso del pie no enviado', type(e).__name__)
            print(f"  TikTok borrador: {c['titulo'][:60]}", flush=True)
        except Exception as e:
            print(f'  TikTok FALLO {type(e).__name__}: {str(e)[:200]}')
            if 'spam_risk' in str(e) or 'rate_limit' in str(e):
                llena = True
                break
        guardar(os.path.join(estado, 'programados.json'), reg)
    try:
        avisar_resumen(enviados, len(cola) - enviados if llena else 0)
    except Exception as e:
        print('  aviso de resumen no enviado', type(e).__name__)
    print(f'RESUMEN TikTok: {enviados} borradores en la bandeja' + (f', bandeja llena ({len(cola) - enviados} sin mandar)' if llena else ''))


def consultar(pid, token):
    """Estado real del borrador en TikTok (la subida solo dice que el archivo llego, no que entro en la bandeja)."""
    r = peticion(f'{API}/post/publish/status/fetch/', {'publish_id': pid}, token=token)
    d = r.get('data') or {}
    err = (r.get('error') or {}).get('code', 'ok')
    return d.get('status') or f'error {err}', d.get('fail_reason') or ''


def revisar(estado, dias=3):
    """Pregunta a TikTok como acabo cada borrador de los ultimos dias y lo apunta en programados.json."""
    token = acceso(estado)
    if not token:
        print('TikTok sin configurar'); return
    ruta = os.path.join(estado, 'programados.json')
    reg = leer(ruta, {'clips': []})
    limite = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=dias)).strftime('%Y-%m-%dT%H:%M:%SZ')
    for c in reg['clips']:
        t = c.get('tiktok') or {}
        if not t.get('publish_id') or (c.get('publishAt') or '') < limite:
            continue
        t['tiktok_estado'], t['motivo'] = consultar(t['publish_id'], token)
        print(f"  {t['tiktok_estado']:<22} {t['motivo'][:40]:<40} {c['titulo'][:55]}", flush=True)
    guardar(ruta, reg)


def prueba(estado):
    """Manda un video de prueba de 5 s a la bandeja, dice a que cuenta llega y espera a que TikTok confirme."""
    import time
    token = acceso(estado)
    if not token:
        print('TikTok sin configurar'); return
    r = peticion(f'{API}/user/info/?fields=open_id,display_name,username', token=token)
    u = (r.get('data') or {}).get('user') or {}
    print(f"cuenta autorizada: @{u.get('username', '?')} ({u.get('display_name', '?')}) error={(r.get('error') or {}).get('code')}")
    mp4 = 'prueba_tiktok.mp4'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'color=c=0x1a1a2e:s=1080x1920:r=30:d=5',
                    '-f', 'lavfi', '-i', 'sine=frequency=440:duration=5', '-shortest', '-c:v', 'libx264',
                    '-pix_fmt', 'yuv420p', '-c:a', 'aac', mp4], check=True)
    pid = subir_borrador(mp4, token)
    print('prueba enviada, esperando a TikTok...', flush=True)
    for _ in range(18):
        time.sleep(10)
        st, motivo = consultar(pid, token)
        print(' ', st, motivo, flush=True)
        if st in ('SEND_TO_USER_INBOX', 'PUBLISH_COMPLETE', 'FAILED') or st.startswith('error'):
            break


def pies(filtro, estado):
    """Repite ya mismo el pie de los borradores que siguen en la bandeja (filtro: texto del titulo, vacio = todos)."""
    reg = leer(os.path.join(estado, 'programados.json'), {'clips': []})
    filtros = [f.strip().lower() for f in (filtro or '').split(',') if f.strip()]
    n = 0
    for c in reg['clips']:
        t = c.get('tiktok') or {}
        if t.get('estado') != 'borrador' or not t.get('pie'):
            continue
        if filtros and not any(f in c['titulo'].lower().replace(' ', '') or f in c['titulo'].lower() for f in filtros):
            continue
        n += bool(avisar_pie(c, t['pie'], ya=True))
        print('  pie reenviado:', c['titulo'][:60])
    print(f'RESUMEN: {n} pies reenviados')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('fase', choices=['token', 'subir', 'pies', 'revisar', 'prueba'])
    ap.add_argument('arg', nargs='?')
    ap.add_argument('--estado', default='../clips-nube')
    a = ap.parse_args()
    if a.fase == 'token':
        token_nuevo(a.arg, a.estado)
    elif a.fase == 'prueba':
        prueba(a.estado)
    elif a.fase == 'revisar':
        revisar(a.estado, int(a.arg or 3))
    elif a.fase == 'pies':
        pies(a.arg, a.estado)
    else:
        subir(a.arg or 'out/clips', a.estado)


if __name__ == '__main__':
    main()
