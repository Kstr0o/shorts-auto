"""Canal de clips (Daily Streamer Clips) 100% en la nube, en GitHub Actions: sin portatil.

Cada noche (workflow clips_nube.yml):
  1. preparar <key>   por streamer: clips mas vistos de la semana que hizo la gente (Twitch o Kick), agrupados por
                      momento, con su VOD y segundo; baja cada tramo del VOD original y lo transcribe.
                      -> out/cand_<key>.json
  2. juntar           une los candidatos en la rama clips-nube (candidatos.json).
  3. (Claude)         una tarea programada lee candidatos.json y escribe momentos.json: corte exacto, titulo, gancho,
                      colores. Si no lo hace a tiempo, `plan` usa `auto` (corte por frases y titulo del clip mas visto).
  4. plan             decide que se edita esta noche (pendientes primero, hasta llenar los huecos libres de YouTube).
  5. editar <key>     corta cada momento del VOD (1080p60), Whisper palabra a palabra, encuadre automatico
                      (camara arriba y juego abajo si hay webcam), subtitulos y zooms con clipper/editar.py.
  6. subir            sube cada clip ya programado (publishAt) en los huecos libres y lo apunta en la rama clips-nube.

Los clips de la gente solo sirven para localizar el momento: el corte sale del VOD y la edicion es nuestra.
Claves (no se imprimen): YT_TOKEN_CLIPS, YT_CLIENT_ID, YT_CLIENT_SECRET. Aviso al movil opcional: AVISO_TEMA (ntfy).
"""
import argparse
import datetime as dt
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from zoneinfo import ZoneInfo

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(AQUI, '..', 'motor'))
MAD = ZoneInfo('Europe/Madrid')
UTC = dt.timezone.utc
CONFIG = json.load(open(os.path.join(AQUI, 'streamers_nube.json'), encoding='utf-8'))
GQL_ID = 'kimne78kx3ncx6brgo4mv6wki5h1ko'  # client id publico de la web de Twitch
INSULTOS = re.compile(r'\bn[i1]gg(a|ah|as|az|er|ers|uh)?\b', re.I)
MAX_NOCHE = int(os.environ.get('SUBIDAS_CLIPS', '6'))  # menos y mejores: los canales grandes suben 1-2/dia


def hoy():
    return dt.datetime.now(MAD).date().isoformat()


def leer(ruta, defecto):
    try:
        return json.load(open(ruta, encoding='utf-8'))
    except (OSError, ValueError):
        return defecto


def guardar(ruta, datos):
    os.makedirs(os.path.dirname(os.path.abspath(ruta)), exist_ok=True)
    json.dump(datos, open(ruta, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        print('  ERR', ' '.join(map(str, cmd))[:140], r.stderr[-500:], flush=True)
    return r


# ---------- 1. listar los clips de la gente ----------
def ytdlp_lista(url, intentos=5):
    for i in range(intentos):
        r = run(['yt-dlp', '--flat-playlist', '-J', '--impersonate', 'chrome', url])
        try:
            e = json.loads(r.stdout).get('entries') or []
        except ValueError:
            e = []
        if e:
            return e
        time.sleep(15 * (i + 1))
    return []


def gql_clip(slug):
    q = {'query': 'query($s:ID!){clip(slug:$s){title viewCount durationSeconds videoOffsetSeconds createdAt '
                  'video{id} game{name}}}', 'variables': {'s': slug}}
    for i in range(3):
        try:
            req = urllib.request.Request('https://gql.twitch.tv/gql', data=json.dumps(q).encode(),
                                         headers={'Client-ID': GQL_ID, 'Content-Type': 'application/json'})
            return json.load(urllib.request.urlopen(req, timeout=20))['data']['clip'] or {}
        except Exception as e:
            print('  gql', type(e).__name__)
            time.sleep(5 * (i + 1))
    return {}


SUGERIDOS = set()


def clips_twitch(login, n=40, extra=()):
    """extra: urls de clips que sugiere el dueno del canal (sugeridos.json); entran aunque no esten en el top."""
    e = ytdlp_lista(f'https://www.twitch.tv/{login}/clips?filter=clips&range=7d')
    e.sort(key=lambda x: -(x.get('view_count') or 0))
    e = e[:n]
    vistos = {x['url'].rstrip('/').split('/')[-1] for x in e}
    e += [{'url': u, 'sugerido': True} for u in extra if u.split('?')[0].rstrip('/').split('/')[-1] not in vistos]
    out = []
    for x in e:
        slug = x['url'].split('?')[0].rstrip('/').split('/')[-1]
        c = gql_clip(slug)
        x['sugerido'] = x.get('sugerido') or slug in SUGERIDOS
        vod = (c.get('video') or {}).get('id')
        if not vod or c.get('videoOffsetSeconds') is None:
            continue
        out.append({'url': x['url'], 'titulo': c.get('title') or x.get('title') or '', 'vistas': c.get('viewCount') or 0,
                    'dur': c.get('durationSeconds') or 30, 'vod': vod, 'vod_url': f'https://www.twitch.tv/videos/{vod}',
                    'offset': float(c['videoOffsetSeconds']), 'juego': (c.get('game') or {}).get('name') or '',
                    'fecha': c.get('createdAt'), 'sugerido': bool(x.get('sugerido'))})
    return out


def kick_get(url):
    from curl_cffi import requests as cr
    for i in range(4):
        try:
            r = cr.get(url, impersonate='chrome', timeout=30)
            if r.status_code == 200:
                return r.json()
            print('  kick', r.status_code)
        except Exception as e:
            print('  kick', type(e).__name__)
        time.sleep(10 * (i + 1))
    return {}


def clips_kick(login, n=40):
    lista = kick_get(f'https://kick.com/api/v2/channels/{login}/clips?sort=view&time=week').get('clips') or []
    lista.sort(key=lambda x: -(x.get('views') or x.get('view_count') or 0))
    out = []
    for x in lista[:n]:
        c = kick_get(f"https://kick.com/api/v2/clips/{x['id']}").get('clip') or {}
        vod = (c.get('vod') or {}).get('id')
        if not vod:
            continue
        out.append({'url': f"https://kick.com/{login}/clips/{x['id']}", 'titulo': c.get('title') or '',
                    'vistas': c.get('views') or c.get('view_count') or 0, 'dur': c.get('duration') or 30,
                    'vod': vod, 'vod_url': f'https://kick.com/{login}/videos/{vod}', 'offset': float(c.get('vod_starts_at') or 0),
                    'juego': ((c.get('category') or {}).get('name')) or '', 'fecha': c.get('created_at')})
    return out


# ---------- 1b. picos del chat del directo (momentos que nadie clipeo) ----------
HYPE = re.compile(r'(LMA+O|LMFAO|KEKW|OMEGALUL|\bLUL\b|ICANT|HAHA|\bW+\b|\bL+\b|WTF|OMG|AYO|NAH+|DEAD|BRO+|CRAZY|INSANE|'
                  r'CLIP|\?{3,}|!{3,}|\U0001F480|\U0001F62D|\U0001F602|\U0001F923|\U0001F633)', re.I)


def chat_en(vod, o):
    """Una pagina de chat desde el segundo o: (mensajes por segundo, fraccion de mensajes de 'hype', 3 mensajes de muestra)."""
    q = {'query': 'query($id:ID!,$o:Int){video(id:$id){comments(contentOffsetSeconds:$o){edges{node{contentOffsetSeconds '
                  'message{fragments{text}}}}}}}', 'variables': {'id': vod, 'o': int(o)}}
    for i in range(3):
        try:
            req = urllib.request.Request('https://gql.twitch.tv/gql', data=json.dumps(q).encode(),
                                         headers={'Client-ID': GQL_ID, 'Content-Type': 'application/json'})
            ed = json.load(urllib.request.urlopen(req, timeout=20))['data']['video']['comments']['edges']
            break
        except Exception:
            time.sleep(2 * (i + 1))
    else:
        return None
    if not ed:
        return (0.0, 0.0, [])
    t = [e['node']['contentOffsetSeconds'] for e in ed]
    msgs = [''.join(f.get('text') or '' for f in e['node']['message']['fragments']).strip() for e in ed]
    span = max(1.0, max(t) - min(t))
    hype = sum(1 for m in msgs if HYPE.search(m)) / len(msgs)
    return (len(msgs) / span, hype, [m[:40] for m in msgs if HYPE.search(m)][:3])


def picos_chat(login, cfg, ocupados, n=3, horas=30, paso=20):
    """Momentos donde el chat explota en los directos de las ultimas `horas`: ventanas sin clip_top (origen chat).
    El chat reacciona 5-15 s despues de lo que pasa, por eso la ventana empieza 45 s antes del pico."""
    from concurrent.futures import ThreadPoolExecutor
    q = {'query': 'query($l:String!){user(login:$l){videos(first:3,type:ARCHIVE){edges{node{id lengthSeconds createdAt}}}}}',
         'variables': {'l': login}}
    try:
        req = urllib.request.Request('https://gql.twitch.tv/gql', data=json.dumps(q).encode(),
                                     headers={'Client-ID': GQL_ID, 'Content-Type': 'application/json'})
        vids = [e['node'] for e in json.load(urllib.request.urlopen(req, timeout=20))['data']['user']['videos']['edges']]
    except Exception as e:
        print('  picos: sin lista de VODs', type(e).__name__); return []
    limite = dt.datetime.now(UTC) - dt.timedelta(hours=horas)
    puntos = []
    for v in vids:
        ini = dt.datetime.fromisoformat(v['createdAt'].replace('Z', '+00:00'))
        dur = int(v['lengthSeconds'] or 0)
        desde = max(0, int((limite - ini).total_seconds()))
        if desde >= dur:
            continue
        offs = list(range(desde, dur - 30, paso))
        with ThreadPoolExecutor(8) as ex:
            res = list(ex.map(lambda o: chat_en(v['id'], o), offs))
        puntos += [(v['id'], o, r) for o, r in zip(offs, res) if r]
    if len(puntos) < 30:
        return []
    out, elegidos = [], []
    por_vod = {}
    for vid, o, r in puntos:
        por_vod.setdefault(vid, []).append((o, r))
    cand = []
    for vid, lst in por_vod.items():
        lst.sort()
        tasas = [r[0] for _, r in lst]
        for i, (o, r) in enumerate(lst):
            loc = sorted(tasas[max(0, i - 30):i + 30])  # +-10 min: la audiencia cambia a lo largo del directo
            base = loc[len(loc) // 2] or 0.1
            cand.append((r[0] / base * (0.5 + r[1]), vid, o, r))
    cand.sort(key=lambda x: -x[0])
    for sc, vid, o, r in cand:
        if len(out) >= n or sc < 2.5:  # pico claro: al menos 2,5 veces el ritmo normal del chat
            break
        a, b = max(0.0, o - 45.0), o + 15.0
        if any(e[0] == vid and abs(e[1] - o) < 120 for e in elegidos):
            continue
        if any(u['vod'] == vid and solapa(a, b, u['inicio'], u['fin']) for u in ocupados):
            continue
        elegidos.append((vid, o))
        out.append({'id': f"{cfg['key']}_{vid[:12]}_{int(a)}", 'vod': vid, 'vod_url': f'https://www.twitch.tv/videos/{vid}',
                    'a': a, 'b': b, 'vistas': 0, 'clip_top': None, 'origen': 'chat', 'titulos_gente': [],
                    'chat': {'pico': round(sc, 1), 'msg_por_seg': round(r[0], 1), 'hype': round(r[1], 2), 'muestra': r[2]},
                    'fecha': hoy(), 'juego': '', 'sugerido': False})
    print(f"  picos de chat: {len(puntos)} muestras, {len(out)} picos", flush=True)
    return out


def solapa(a1, b1, a2, b2, margen=5):
    return min(b1, b2) - max(a1, a2) > margen


def ventanas(clips, usados, cfg, maximo):
    """Agrupa los clips que marcan el mismo momento y devuelve los tramos del VOD mas vistos."""
    juego = (cfg.get('juego') or '').lower()
    clips = [c for c in clips if not juego or juego in c['juego'].lower() or c.get('sugerido')]
    grupos = []
    for c in sorted(clips, key=lambda c: (c['vod'], c['offset'])):
        a, b = c['offset'], c['offset'] + c['dur']
        g = grupos[-1] if grupos else None
        if g and g['vod'] == c['vod'] and a <= g['b'] + 15:
            g['b'] = max(g['b'], b); g['clips'].append(c)
        else:
            grupos.append({'vod': c['vod'], 'vod_url': c['vod_url'], 'a': a, 'b': b, 'clips': [c]})
    out = []
    for g in grupos:
        g['clips'].sort(key=lambda c: -c['vistas'])
        top = g['clips'][0]
        a, b = g['a'] - 15, g['b'] + 10
        if b - a > 150:  # momento muy largo: centrado en el clip mas visto
            a, b = top['offset'] - 45, top['offset'] + top['dur'] + 45
        a = max(0.0, a)
        if any(u['vod'] == g['vod'] and solapa(a + 10, b - 5, u['inicio'], u['fin']) for u in usados):
            continue
        out.append({'id': f"{cfg['key']}_{g['vod'][:12]}_{int(a)}", 'vod': g['vod'], 'vod_url': g['vod_url'],
                    'a': round(a, 1), 'b': round(b, 1), 'vistas': sum(c['vistas'] for c in g['clips']),
                    'clip_top': {'url': top['url'], 'titulo': top['titulo'], 'offset': top['offset'], 'dur': top['dur']},
                    'titulos_gente': [c['titulo'] for c in g['clips'][:6]], 'fecha': top['fecha'], 'juego': top['juego'],
                    'sugerido': any(c.get('sugerido') for c in g['clips'])})
    out.sort(key=lambda v: (not v['sugerido'], -v['vistas']))  # lo que sugiere el dueno va primero
    return out[:maximo]


# ---------- 2. bajar tramos del VOD y transcribir ----------
_M3U8 = {}


def m3u8(vod_url):
    if vod_url not in _M3U8:
        for i in range(4):
            r = run(['yt-dlp', '--impersonate', 'chrome', '-g', '-f', 'best[height<=1080]/best', vod_url])
            u = (r.stdout or '').strip().splitlines()
            if u:
                _M3U8[vod_url] = u[0]; break
            time.sleep(10 * (i + 1))
    return _M3U8.get(vod_url)


def bajar_tramo(vod_url, a, b, destino, calidad='18'):
    """Corta [a, b] del VOD con ffmpeg recodificando: el segundo 0 es exactamente `a` (mismos tiempos en cada ejecucion)."""
    u = m3u8(vod_url)
    if u:
        r = run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{a:.2f}', '-i', u, '-t', f'{b - a:.2f}', '-c:v', 'libx264',
                 '-preset', 'veryfast', '-crf', calidad, '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', destino])
        if r.returncode == 0 and os.path.exists(destino) and os.path.getsize(destino) > 100_000:
            return True
    # plan B: yt-dlp por secciones (un poco menos exacto)
    run(['yt-dlp', '--impersonate', 'chrome', '-f', 'best[height<=1080]/best', '--download-sections', f'*{a:.1f}-{b:.1f}',
         '--force-keyframes-at-cuts', '-o', destino, vod_url])
    return os.path.exists(destino) and os.path.getsize(destino) > 100_000


_WHISPER = []


def whisper():
    if not _WHISPER:
        from faster_whisper import WhisperModel
        _WHISPER.append(WhisperModel(os.environ.get('WHISPER_MODELO', 'large-v3-turbo'), device='cpu', compute_type='int8'))
    return _WHISPER[0]


def transcribir(mp4, idioma='en'):
    """Palabras con su tiempo (segundos desde el inicio del archivo)."""
    import numpy as np
    pcm = subprocess.run(['ffmpeg', '-v', 'error', '-i', mp4, '-f', 's16le', '-ac', '1', '-ar', '16000', '-'],
                         capture_output=True).stdout
    audio = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768.0
    segs, _ = whisper().transcribe(audio, language=idioma, word_timestamps=True, vad_filter=True)
    pal = []
    for s in segs:
        for p in s.words or []:
            if p.word.strip():
                pal.append({'w': p.word.strip(), 's': round(p.start, 2), 'e': round(p.end, 2)})
    return pal


def frases(pal, base=0.0):
    out, act = [], []
    for i, p in enumerate(pal):
        act.append(p)
        pausa = i + 1 < len(pal) and pal[i + 1]['s'] - p['e'] > 0.8
        if re.search(r'[.?!]$', p['w']) or pausa or len(act) >= 25:
            out.append([round(act[0]['s'] + base, 1), round(act[-1]['e'] + base, 1), ' '.join(x['w'] for x in act)]); act = []
    if act:
        out.append([round(act[0]['s'] + base, 1), round(act[-1]['e'] + base, 1), ' '.join(x['w'] for x in act)])
    return out


def preparar(key, estado_dir, salida):
    cfg = dict(CONFIG[key], key=key)
    usados = leer(os.path.join(estado_dir, 'usados.json'), [])
    print('CLIPS de', cfg['login'], f"({cfg['plataforma']})", flush=True)
    sug = [x['url'] for x in leer(os.path.join(estado_dir, 'sugeridos.json'), []) if x.get('key') == key]
    SUGERIDOS.update(u.split('?')[0].rstrip('/').split('/')[-1] for u in sug)
    clips = clips_twitch(cfg['login'], extra=sug) if cfg['plataforma'] == 'twitch' else clips_kick(cfg['login'])
    print(f'  {len(clips)} clips con VOD', flush=True)
    vs = ventanas(clips, usados, cfg, int(cfg.get('ventanas', 4)))
    if cfg['plataforma'] == 'twitch' and int(cfg.get('picos', 3)):
        ocup = usados + [{'vod': v['vod'], 'inicio': v['a'], 'fin': v['b']} for v in vs]
        vs += picos_chat(cfg['login'], cfg, ocup, n=int(cfg.get('picos', 3)))
    tmp = os.path.join('out', 'tmp'); os.makedirs(tmp, exist_ok=True)
    listos = []
    for v in vs:
        mp4 = os.path.join(tmp, v['id'] + '.mp4')
        if not bajar_tramo(v['vod_url'], v['a'], v['b'], mp4, calidad='30'):
            print('  sin tramo', v['id']); continue
        pal = transcribir(mp4)
        os.remove(mp4)
        texto = ' '.join(p['w'] for p in pal)
        v['frases'] = frases(pal, base=v['a'])
        v['insultos'] = bool(INSULTOS.search(texto))
        print(f"  {v['vistas']:>7} vistas  {v['a']:.0f}-{v['b']:.0f}s  {len(v['frases'])} frases"
              f"{'  INSULTOS' if v['insultos'] else ''}  | {(v.get('clip_top') or {}).get('titulo', 'PICO DE CHAT ' + str((v.get('chat') or {}).get('pico')))[:60]}", flush=True)
        listos.append(v)
    info = {k: cfg.get(k) for k in ('key', 'streamer', 'plataforma', 'login', 'campana', 'hashtag', 'credito', 'prioridad')}
    guardar(salida, dict(info, ventanas=listos))
    print(f'RESUMEN {key}: {len(listos)} momentos')


def juntar(entradas, estado_dir):
    todo = {'fecha': hoy(), 'creado': dt.datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ'), 'streamers': []}
    for f in sorted(entradas):
        todo['streamers'].append(leer(f, {}))
    guardar(os.path.join(estado_dir, 'candidatos.json'), todo)
    n = sum(len(s.get('ventanas', [])) for s in todo['streamers'])
    print(f'candidatos: {n} momentos de {len(todo["streamers"])} streamers')


# ---------- 3. momentos automaticos (si Claude no los escribe a tiempo) ----------
def titulo_auto(streamer, v, usados):
    t = re.sub(r'\s+', ' ', re.sub(r'[^\w\s\'!?.,-]', '', v['clip_top']['titulo'])).strip()
    t = re.sub(r'(.)\1{2,}', r'\1', t)  # DOGGGG -> DOG
    if len(t.split()) >= 3:
        t = t.lower() if t.isupper() else t
        tit = t if streamer.lower().split()[0] in t.lower() else f'{streamer}: {t}'
    else:
        fr = max(v.get('frases') or [[0, 0, 'GTA 6']], key=lambda f: len(f[2].split()) if 3 <= len(f[2].split()) <= 10 else 0)
        tit = f'{streamer}: "{" ".join(fr[2].split()[:9]).strip(",. ")}"'
    # Title Case como los canales grandes ("Kai Cenat Realises There's A Samsung Duo! 😭"); .title() rompe los apostrofes
    tit = ' '.join(re.sub(r'^(\W*)(\w)', lambda m: m.group(1) + m.group(2).upper(), w) for w in tit.split())
    if len(tit) > 55:  # el remate tiene que caber en el movil
        tit = tit[:55].rsplit(' ', 1)[0]
        tit = re.sub(r'(\s+(the|a|an|in|on|of|and|to|his|her|their|with|for|at|is|so))+$', '', tit, flags=re.I).rstrip(',:;-')
    if not re.search(r'[!?"]$', tit):
        tit += '!'
    if tit in usados:
        tit = (tit[:45] + ' in GTA 6')[:55]
    usados.add(tit)
    if not re.search(r'[\U0001F300-\U0001FAFF]', tit):
        tit = f'{tit} {EMOJIS[len(usados) % len(EMOJIS)]}'
    return tit


def sin_arranque_muerto(ini, fin, fr, muerto=1.5, antes=0.4):
    """El primer segundo es el gancho: si el clip tarda mas de `muerto` s en arrancar a hablar, empieza justo antes."""
    primera = next((f[0] for f in fr if f[1] > ini and f[0] < fin), None)
    if primera is not None and primera - ini > muerto and fin - (primera - antes) >= 8:
        return round(primera - antes, 2)
    return ini


EMOJIS = ('\U0001F480', '\U0001F62D', '\U0001F633')  # calavera, llorando, sorpresa: lo que usan los canales grandes


def auto(cand):
    clips, titulos = [], set()
    for s in cand.get('streamers', []):
        for k, v in enumerate(s.get('ventanas', [])):
            if v.get('insultos') or not v.get('frases') or not v.get('clip_top'):  # los picos de chat los elige Claude
                continue
            # el corte es EXACTAMENTE el clip mas visto de Twitch/Kick (el que la gente ya valido), sin alargarlo
            o, d = v['clip_top']['offset'], v['clip_top']['dur']
            fr = v['frases']
            ini, fin = round(o, 2), round(o + d, 2)
            ini = sin_arranque_muerto(ini, fin, fr)
            clips.append({'id': v['id'], 'key': s['key'], 'inicio': round(ini, 2), 'fin': round(fin, 2),
                          'titulo': titulo_auto(s['streamer'], v, titulos), 'claves': [], 'color': '#FFD400',
                          'nota': max(5, 9 - k), 'gancho': next((f[2] for f in fr if f[0] >= ini), ''), 'origen': v['clip_top']['url']})
    return {'fecha': cand.get('fecha'), 'creado': cand.get('creado'), 'fuente': 'auto', 'clips': clips}


def texto_corto(t, maximo=60):
    """Texto en pantalla: de que va el clip, en dos lineas como mucho."""
    t = t.strip()
    if len(t) <= maximo:
        return t
    return t[:maximo].rsplit(' ', 1)[0].rstrip(',.;:') + '...'


# ---------- 4. plan de la noche ----------
def youtube():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    cred = Credentials(None, refresh_token=os.environ['YT_TOKEN_CLIPS'], client_id=os.environ['YT_CLIENT_ID'],
                       client_secret=os.environ['YT_CLIENT_SECRET'], token_uri='https://oauth2.googleapis.com/token')
    return build('youtube', 'v3', credentials=cred)


def programados_youtube():
    """publishAt de los videos que aun no han salido (lo que ya esta programado, desde el portatil o desde aqui)."""
    yt = youtube()
    up = yt.channels().list(part='contentDetails', mine=True).execute()['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    ids = [i['contentDetails']['videoId'] for i in
           yt.playlistItems().list(part='contentDetails', playlistId=up, maxResults=50).execute().get('items', [])]
    vs = yt.videos().list(part='status', id=','.join(ids)).execute().get('items', []) if ids else []
    return {v['status']['publishAt'].replace('.000Z', 'Z') for v in vs if v['status'].get('publishAt')}


def huecos(ocupadas):
    import programar
    return programar.huecos_libres(ocupadas, dt.datetime.now(UTC))


def plan(estado_dir, forzar_auto=False):
    """Escribe out/plan.json con los momentos de esta noche y la lista de streamers (matriz de editar)."""
    reg = leer(os.path.join(estado_dir, 'programados.json'), {'clips': []})
    cand = leer(os.path.join(estado_dir, 'candidatos.json'), {})
    lote = cand.get('creado')  # cada tanda de candidatos se sube una sola vez
    if lote and any(c.get('lote') == lote for c in reg['clips']) and not os.environ.get('REPETIR'):
        print('esta tanda ya se subio: nada que hacer'); guardar('out/plan.json', {'clips': [], 'streamers': []}); return
    mom = leer(os.path.join(estado_dir, 'momentos.json'), {})
    if forzar_auto or mom.get('creado') != lote:
        print('momentos de Claude no disponibles para hoy: uso los automaticos')
        mom = auto(cand) if cand.get('fecha', '') >= (dt.date.fromisoformat(hoy()) - dt.timedelta(days=1)).isoformat() else {'clips': []}
    pend = [c for c in leer(os.path.join(estado_dir, 'pendientes.json'), [])
            if c.get('fecha', '') >= (dt.date.fromisoformat(hoy()) - dt.timedelta(days=4)).isoformat()]
    ocupadas = programados_youtube() | {c['publishAt'] for c in reg['clips'] if c.get('publishAt')}
    libres = len(huecos(ocupadas))
    cupo = min(libres, MAX_NOCHE)
    hechos = {c['id'] for c in reg['clips']}
    nuevos = [dict(c, fecha=mom.get('fecha') or hoy()) for c in mom.get('clips', []) if c['id'] not in hechos]
    prio = {k: int(v.get('prioridad', 5)) for k, v in CONFIG.items()}
    nuevos.sort(key=lambda c: (-float(c.get('nota', 0)), prio.get(c['key'], 5)))
    # reparto: pendientes primero, luego mezcla de streamers (uno de cada en cada vuelta)
    cola, vistos = [c for c in pend if c['id'] not in hechos], set()
    por = {}
    for c in nuevos:
        por.setdefault(c['key'], []).append(c)
    orden = sorted(por, key=lambda k: prio.get(k, 5))
    while any(por.values()):
        for k in orden:
            if por[k]:
                cola.append(por[k].pop(0))
    elegidos, resto = [], []
    for c in cola:
        if c['id'] in vistos:
            continue
        vistos.add(c['id'])
        (elegidos if len(elegidos) < cupo else resto).append(c)
    porid = {v['id']: v for s in cand.get('streamers', []) for v in s.get('ventanas', [])}
    for c in elegidos + resto:  # el VOD va con el momento (los pendientes de otros dias no estan en candidatos de hoy)
        if not c.get('vod_url') and c['id'] in porid:
            c['vod_url'] = porid[c['id']]['vod_url']
    guardar(os.path.join(estado_dir, 'pendientes.json'), resto)
    streamers = sorted({c['key'] for c in elegidos})
    guardar('out/plan.json', {'clips': elegidos, 'streamers': streamers, 'fuente': mom.get('fuente', 'claude'), 'lote': lote})
    print(f"huecos libres {libres}, esta noche {len(elegidos)} clips ({mom.get('fuente', 'claude')}), pendientes {len(resto)}")
    for c in elegidos:
        print(f"  {c['key']:<10} {c['inicio']:.0f}-{c['fin']:.0f}s  nota {c.get('nota')}  {c['titulo']}")


# ---------- 5. editar ----------
def detectar_camara(mp4):
    """Busca la webcam del streamer: cara pequena y quieta en el mismo sitio en casi todos los fotogramas.
    Devuelve (encuadre, camara): ('split', [x, y, w, h]) / ('cara', None) / ('centro', None)."""
    import cv2
    import numpy as np
    cap = cv2.VideoCapture(mp4)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    W, H = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    det = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    caras, muestras = [], 16
    for i in range(muestras):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(n * (i + 0.5) / muestras))
        ok, fr = cap.read()
        if not ok:
            continue
        esc = 960 / W
        g = cv2.cvtColor(cv2.resize(fr, (960, int(H * esc))), cv2.COLOR_BGR2GRAY)
        fs = det.detectMultiScale(g, 1.1, 6, minSize=(24, 24))
        for x, y, w, h in fs:
            caras.append(((x + w / 2) / esc / W, (y + h / 2) / esc / H, w / esc / W))
    cap.release()
    if not caras:
        return 'centro', None
    c = np.array(caras)
    med = np.median(c, axis=0)
    cerca = c[(abs(c[:, 0] - med[0]) < 0.06) & (abs(c[:, 1] - med[1]) < 0.08)]
    if len(cerca) < muestras * 0.4:
        return 'centro', None
    fx, fy, fw = np.median(cerca, axis=0)
    if fw > 0.22:  # la camara ocupa casi toda la pantalla
        return 'cara', None
    cw = min(0.5, fw * 3.6)                      # ancho de la webcam en fraccion del ancho
    ch = min(0.6, cw * (W / H) / (1080 / 700))   # misma proporcion que la franja de arriba
    x = min(max(fx - cw / 2, 0), 1 - cw)
    y = min(max(fy - ch * 0.45, 0), 1 - ch)
    return 'split', [round(x, 4), round(y, 4), round(cw, 4), round(ch, 4)]


def descripcion(c, cfg):
    base = (c.get('descripcion') or f"{cfg['streamer']} in GTA 6.").split('\n\nCredit:')[0].strip()
    base = re.sub(r'\s*#\w+', '', base).strip()
    tags = ' '.join(t for t in [cfg.get('hashtag'), '#GTA6', '#GTAVI'] if t)
    return f"{base}\n\nCredit: {cfg['credito']}\n\n{tags}"


def editar(key, plan_json, salida):
    import editar as ed
    cfg = dict(CONFIG[key], key=key)
    clips = [c for c in leer(plan_json, {}).get('clips', []) if c['key'] == key]
    cand = {v['id']: v for s in leer(os.environ.get('CANDIDATOS', ''), {}).get('streamers', []) for v in s.get('ventanas', [])}
    os.makedirs(salida, exist_ok=True)
    os.environ.setdefault('FPS_CLIP', '60'); os.environ.setdefault('CRF_CLIP', '18')
    os.environ.setdefault('AUDIO_CLIP', '192k')
    for k, c in enumerate(clips, 1):
        v = cand.get(c['id'], {})
        vod_url = c.get('vod_url') or v.get('vod_url')
        if not vod_url:
            print('  sin VOD', c['id']); continue
        carpeta = os.path.join('out', 'trabajo', c['id']); os.makedirs(carpeta, exist_ok=True)
        video = os.path.join(carpeta, 'video.mp4')
        ini, fin = float(c['inicio']), float(c['fin'])
        if not bajar_tramo(vod_url, ini, fin, video, calidad='14'):
            print('  no se pudo bajar', c['id']); continue
        pal = transcribir(video)
        dur = fin - ini
        encuadre, camara = (c.get('encuadre'), c.get('camara')) if c.get('encuadre') else detectar_camara(video)
        m = {'inicio': 0.0, 'fin': dur, 'titulo': c['titulo'], 'descripcion': descripcion(c, cfg),
             'tags': c.get('tags') or ['GTA6', cfg['streamer'], 'Twitch' if cfg['plataforma'] == 'twitch' else 'Kick', 'gaming'],
             'claves': c.get('claves') or [], 'acciones': c.get('acciones') or [], 'texto_arriba': texto_corto(c.get('texto_arriba') or c['titulo']),
             'nota': c.get('nota'), 'gancho': c.get('gancho'), 'campana': cfg.get('campana') or None,
             'encuadre': encuadre, 'camara': camara, 'juego': c.get('juego_zona')}
        ed.render_clip(carpeta, k, m, pal, c.get('color', '#FFD400'), 'en', {})
        hecho = sorted(glob.glob(os.path.join(carpeta, 'clips', f'{k:02d}_*.mp4')))
        if not hecho:
            continue
        nombre = os.path.join(salida, f"{key}_{k:02d}")
        shutil.move(hecho[0], nombre + '.mp4')
        meta = leer(hecho[0][:-4] + '.json', {})
        meta.update(id=c['id'], key=key, streamer=cfg['streamer'], hashtag=cfg.get('hashtag'), campana=cfg.get('campana') or None,
                    fuente=vod_url, inicio=ini, fin=fin, origen=c.get('origen'), encuadre=encuadre, nota=c.get('nota'),
                    sintetico=False, formato='clip')
        guardar(nombre + '.json', meta)
        # fotograma de muestra (para revisar el encuadre)
        run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{min(3, dur / 2):.1f}', '-i', nombre + '.mp4', '-frames:v', '1',
             '-vf', 'scale=360:-1', nombre + '.jpg'])
        shutil.rmtree(carpeta, ignore_errors=True)
        print(f"  {key}_{k:02d}  {dur:.0f}s  {encuadre}  {c['titulo']}", flush=True)


# ---------- 6. subir ya programado ----------
def subir(carpeta, estado_dir, simular=False):
    import programar
    import subir as s
    reg = leer(os.path.join(estado_dir, 'programados.json'), {'clips': []})
    usados = leer(os.path.join(estado_dir, 'usados.json'), [])
    prio = {k: int(v.get('prioridad', 5)) for k, v in CONFIG.items()}
    metas = [(m, leer(m, {})) for m in glob.glob(os.path.join(carpeta, '**', '*.json'), recursive=True)]
    metas = [(m, j) for m, j in metas if j.get('formato') == 'clip' and os.path.exists(m[:-5] + '.mp4')]
    orden = [x['id'] for x in leer('out/plan.json', {}).get('clips', [])]
    metas.sort(key=lambda mj: (orden.index(mj[1]['id']) if mj[1]['id'] in orden else 99, prio.get(mj[1].get('key'), 5)))
    ocupadas = programados_youtube() | {c['publishAt'] for c in reg['clips'] if c.get('publishAt')}
    libres = huecos(ocupadas)
    ahora = dt.datetime.now(UTC)
    no_subidos, subidos = [], 0
    plan_clips = {x['id']: x for x in leer('out/plan.json', {}).get('clips', [])}
    for (mj, meta) in metas:
        if subidos >= min(MAX_NOCHE, len(libres)):
            no_subidos.append(meta); continue
        hora = libres[subidos].strftime('%Y-%m-%dT%H:%M:%SZ')
        print(f"{meta['titulo'][:60]:<60} -> {libres[subidos].astimezone(MAD):%a %d/%m %H:%M} Madrid", flush=True)
        if simular:
            subidos += 1; continue
        try:
            vid = s.subir(mj[:-5] + '.mp4', mj, 'CLIPS', hora)
        except Exception as e:
            print(f'  FALLO {type(e).__name__}: {str(e)[:300]}')
            no_subidos.append(meta)
            if 'quota' in str(e).lower() or 'uploadLimitExceeded' in str(e):
                no_subidos += [j for _, j in metas[metas.index((mj, meta)) + 1:]]
                break
            continue
        subidos += 1
        clip = {'id': meta['id'], 'url': f'https://youtube.com/shorts/{vid}', 'publishAt': hora, 'titulo': meta['titulo'],
                'campana': meta.get('campana'), 'streamer': meta.get('streamer'), 'fuente': meta.get('fuente'),
                'inicio': meta.get('inicio'), 'fin': meta.get('fin'), 'noche': hoy(), 'lote': leer('out/plan.json', {}).get('lote'), 'enlace_enviado': False}
        if programar.AVISO_TEMA and clip['campana']:
            try:
                clip['aviso'] = programar.avisar(clip, ahora)
            except Exception as e:
                print('  aviso no enviado', type(e).__name__)
        reg['clips'].append(clip)
        vod = str(meta.get('fuente', '')).rstrip('/').split('/')[-1]
        usados.append({'vod': vod, 'inicio': meta.get('inicio'), 'fin': meta.get('fin'), 'id': meta['id']})
        guardar(os.path.join(estado_dir, 'programados.json'), reg)
        guardar(os.path.join(estado_dir, 'usados.json'), usados)
    if no_subidos and not simular:
        pend = leer(os.path.join(estado_dir, 'pendientes.json'), [])
        pend = [plan_clips[m['id']] for m in no_subidos if m['id'] in plan_clips] + pend
        guardar(os.path.join(estado_dir, 'pendientes.json'), pend)
    print(f'RESUMEN subidos {subidos}, sin subir {len(no_subidos)}' + (' (simulado)' if simular else ''))
    resumen_md(estado_dir, reg)


def resumen_md(estado_dir, reg):
    lin = ['# Clips programados (nube)', '', '| Sale (Madrid) | Streamer | Campana | Titulo | Enlace |', '|---|---|---|---|---|']
    for c in sorted(reg['clips'], key=lambda c: c.get('publishAt') or '')[-40:]:
        t = dt.datetime.strptime(c['publishAt'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=UTC).astimezone(MAD)
        lin.append(f"| {t:%a %d/%m %H:%M} | {c.get('streamer')} | {c.get('campana') or '-'} | {c['titulo']} | {c['url']} |")
    open(os.path.join(estado_dir, 'programados.md'), 'w', encoding='utf-8').write('\n'.join(lin) + '\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('fase', choices=['preparar', 'juntar', 'plan', 'editar', 'subir', 'auto'])
    ap.add_argument('args', nargs='*')
    ap.add_argument('--estado', default='../clips-nube')
    ap.add_argument('--auto', action='store_true')
    ap.add_argument('--simular', action='store_true')
    a = ap.parse_args()
    if a.fase == 'preparar':
        preparar(a.args[0], a.estado, f'out/cand_{a.args[0]}.json')
    elif a.fase == 'juntar':
        juntar(a.args, a.estado)
    elif a.fase == 'plan':
        plan(a.estado, a.auto)
    elif a.fase == 'editar':
        editar(a.args[0], 'out/plan.json', 'out/clips')
    elif a.fase == 'subir':
        subir(a.args[0] if a.args else 'out/clips', a.estado, a.simular)
    elif a.fase == 'auto':
        print(json.dumps(auto(leer(os.path.join(a.estado, 'candidatos.json'), {})), ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
