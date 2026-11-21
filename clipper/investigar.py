"""Investigacion (solo lectura): que clips eligen los canales de clips grandes de cada streamer y con que formato.

Uso (GitHub Actions, investigar_clips.yml): python3 clipper/investigar.py <key>
  1. Busca en YouTube Shorts de la ultima semana del streamer y agrupa por canal -> canales de clips mas fuertes.
  2. Lista los ultimos Shorts de esos canales (titulo, vistas, duracion).
  3. Lista los clips mas vistos de Twitch de la semana (los mismos que usa nube.py).
  4. (YouTube no deja bajar video desde Actions: el emparejado Short-clip se hace por titulo, a mano.)
  5. Hoja con la portada y los fotogramas automaticos de YouTube (25/50/75 %) para copiar el formato.
No sube nada ni guarda videos: imprime el resumen en el log entre marcas.
"""
import base64
import collections
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nube  # noqa: E402

TMP = tempfile.mkdtemp()
_W = []


def w():
    if not _W:
        from faster_whisper import WhisperModel
        _W.append(WhisperModel('small', device='cpu', compute_type='int8'))
    return _W[0]


def lista(url, fin=80):
    r = nube.run(['yt-dlp', '--flat-playlist', '-J', '--playlist-end', str(fin), url])
    try:
        return json.loads(r.stdout).get('entries') or []
    except ValueError:
        return []


def buscar(q):
    # sp=EgIIAw%3D%3D -> subidos esta semana
    url = 'https://www.youtube.com/results?search_query=' + urllib.parse.quote(q) + '&sp=EgIIAw%3D%3D'
    for i in range(4):
        e = lista(url, 120)
        if e:
            return e
        import time
        time.sleep(20 * (i + 1))
    return []


def audio(url, seg, nombre):
    dst = os.path.join(TMP, nombre + '.m4a')
    nube.run(['yt-dlp', '-q', '-f', 'bestaudio/best', '--download-sections', f'*0-{seg}', '-o', dst, url])
    if not os.path.exists(dst):
        alt = [f for f in os.listdir(TMP) if f.startswith(nombre + '.')]
        dst = os.path.join(TMP, alt[0]) if alt else None
    return dst


def texto(ruta):
    if not ruta:
        return []
    import numpy as np
    pcm = subprocess.run(['ffmpeg', '-v', 'error', '-i', ruta, '-f', 's16le', '-ac', '1', '-ar', '16000', '-'],
                         capture_output=True).stdout
    if len(pcm) < 32000:
        return []
    segs, _ = w().transcribe(np.frombuffer(pcm, np.int16).astype(np.float32) / 32768.0, language='en',
                             word_timestamps=True, vad_filter=True)
    out = []
    for s in segs:
        for p in s.words or []:
            t = re.sub(r'[^a-z0-9]', '', p.word.lower())
            if t:
                out.append((t, round(p.start, 1)))
    return out


def ngr(pal, n=3):
    return {tuple(x[0] for x in pal[i:i + n]): pal[i][1] for i in range(len(pal) - n + 1)}


def emparejar(short, clip):
    a, b = ngr(short), ngr(clip)
    comunes = set(a) & set(b)
    if not a or not b:
        return 0, None
    score = len(comunes) / min(len(a), len(b))
    if not comunes:
        return score, None
    # desfase: segundo del clip de Twitch donde empieza el Short (mediana de diferencias)
    difs = sorted(b[g] - a[g] for g in comunes)
    return score, difs[len(difs) // 2]


def hoja(vid, nombre):
    """YouTube pide login para bajar video desde Actions: uso sus fotogramas automaticos (25/50/75 %) y la portada."""
    fr = []
    for i, n in enumerate(('oar2', '1', '2', '3')):
        f = os.path.join(TMP, f'{nombre}_{i}.jpg')
        try:
            req = urllib.request.Request(f'https://i.ytimg.com/vi/{vid}/{n}.jpg', headers={'User-Agent': 'Mozilla/5.0'})
            open(f, 'wb').write(urllib.request.urlopen(req, timeout=20).read())
        except Exception:
            continue
        g = f + '.s.jpg'
        nube.run(['ffmpeg', '-v', 'error', '-y', '-i', f, '-vf', 'scale=-2:480,setsar=1', g])
        if os.path.exists(g):
            fr.append(g)
    if not fr:
        return None
    out = os.path.join(TMP, nombre + '_hoja.jpg')
    ins = sum([['-i', f] for f in fr], [])
    nube.run(['ffmpeg', '-v', 'error', '-y', *ins, '-filter_complex',
              ''.join(f'[{i}]' for i in range(len(fr))) + f'hstack=inputs={len(fr)}' if len(fr) > 1 else 'null',
              '-q:v', '5', out])
    return out if os.path.exists(out) else fr[0]


def main(key):
    cfg = nube.CONFIG[key]
    nombre = cfg['streamer']
    nl = re.sub(r'[^a-z0-9]', '', nombre.lower())
    # 1. canales
    vistos, por_canal = set(), collections.defaultdict(lambda: {'n': 0, 'vistas': 0, 'titulos': []})
    for q in (nombre, nombre + ' clips', nombre + ' shorts'):
        for e in buscar(q):
            vid = e.get('id')
            if not vid or vid in vistos or (e.get('duration') or 999) > 180:
                continue
            vistos.add(vid)
            c = por_canal[(e.get('channel_id'), e.get('channel') or e.get('uploader') or '?')]
            c['n'] += 1
            c['vistas'] += e.get('view_count') or 0
            c['titulos'].append(e.get('title'))
    canales = sorted(por_canal.items(), key=lambda kv: -(kv[1]['vistas']))[:6]
    res = {'streamer': nombre, 'canales': [], 'twitch': [], 'emparejados': []}
    shorts = []
    for (cid, cname), c in canales:
        if not cid:
            continue
        ult = lista(f'https://www.youtube.com/channel/{cid}/shorts', 30)
        sh = [{'id': e['id'], 'titulo': e.get('title'), 'vistas': e.get('view_count') or 0, 'canal': cname}
              for e in ult if e.get('id')]
        res['canales'].append({'canal': cname, 'id': cid, 'busqueda_n': c['n'], 'busqueda_vistas': c['vistas'],
                               'ultimos_shorts': sh[:30]})
        # solo los Shorts de este streamer (titulo lo nombra) o canal dedicado
        ded = nl in re.sub(r'[^a-z0-9]', '', cname.lower())
        shorts += [s for s in sh if ded or nl in re.sub(r'[^a-z0-9]', '', (s['titulo'] or '').lower())]
    # 2. twitch
    tw = nube.clips_twitch(cfg['login'], n=25) if cfg['plataforma'] == 'twitch' else nube.clips_kick(cfg['login'], 25)
    res['twitch'] = [{'titulo': t['titulo'], 'vistas': t['vistas'], 'dur': t['dur'], 'url': t['url'],
                      'juego': t.get('juego')} for t in tw]
    # 3. emparejar
    shorts.sort(key=lambda s: -s['vistas'])
    top = shorts[:15]
    res['shorts_top'] = top
    print('===RESUMEN_INICIO===')
    print(json.dumps(res, ensure_ascii=False))
    print('===RESUMEN_FIN===', flush=True)
    # 4. hojas de fotogramas (5 Shorts top de canales distintos si se puede)
    hechos, canales_h = 0, collections.Counter()
    for j, s in enumerate(top):
        if hechos >= 6 or canales_h[s['canal']] >= 2:
            continue
        h = hoja(s['id'], f'f{j}')
        if h:
            hechos += 1
            canales_h[s['canal']] += 1
            print(f'===HOJA {s["id"]} {s["canal"]}===')
            print(base64.b64encode(open(h, 'rb').read()).decode())
            print('===HOJA_FIN===', flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
