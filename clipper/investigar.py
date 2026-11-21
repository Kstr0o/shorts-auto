"""Investigacion (solo lectura): que clips eligen los canales de clips grandes de cada streamer y con que formato.

Uso (GitHub Actions, investigar_clips.yml): python3 clipper/investigar.py <key>
  1. Busca en YouTube Shorts de la ultima semana del streamer y agrupa por canal -> canales de clips mas fuertes.
  2. Lista los ultimos Shorts de esos canales (titulo, vistas, duracion).
  3. Lista los clips mas vistos de Twitch de la semana (los mismos que usa nube.py).
  4. Transcribe el audio de los Shorts mas vistos y de los clips de Twitch y los empareja por texto:
     asi se ve que clip de Twitch eligieron, donde cortaron (inicio/fin) y que clips top NO eligieron.
  5. Hoja de fotogramas de los Shorts top (0,3 s / 2 s / 6 s / 12 s) para copiar el formato.
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
    return lista(url, 120)


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


def hoja(url, nombre):
    mp4 = os.path.join(TMP, nombre + '.mp4')
    nube.run(['yt-dlp', '-q', '-f', 'best[height<=720]/best', '--download-sections', '*0-14', '-o', mp4, url])
    if not os.path.exists(mp4):
        return None
    fr = []
    for i, t in enumerate((0.3, 2, 6, 12)):
        f = os.path.join(TMP, f'{nombre}_{i}.jpg')
        nube.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t), '-i', mp4, '-frames:v', '1', '-vf', 'scale=270:-2', f])
        if os.path.exists(f):
            fr.append(f)
    if not fr:
        return None
    out = os.path.join(TMP, nombre + '_hoja.jpg')
    ins = sum([['-i', f] for f in fr], [])
    nube.run(['ffmpeg', '-v', 'error', '-y', *ins, '-filter_complex',
              ''.join(f'[{i}]' for i in range(len(fr))) + f'hstack=inputs={len(fr)}' if len(fr) > 1 else 'null',
              '-q:v', '6', out])
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
    top = shorts[:12]
    tt = []
    for i, t in enumerate(tw[:25]):
        tt.append(texto(audio(t['url'], 70, f'tw{i}')))
    for j, s in enumerate(top):
        url = f'https://www.youtube.com/shorts/{s["id"]}'
        st = texto(audio(url, 70, f'sh{j}'))
        mejor = max(((emparejar(st, tt[i]) + (i,)) for i in range(len(tt))), default=(0, None, None))
        sc, desf, i = mejor
        res['emparejados'].append({
            'short': s, 'url': url, 'dur_aprox': st[-1][1] if st else None,
            'primeras_palabras': ' '.join(x[0] for x in st[:18]),
            'twitch_idx': i if sc >= 0.2 else None, 'score': round(sc, 2),
            'empieza_en_seg_del_clip': desf if sc >= 0.2 else None,
            'twitch_titulo': tw[i]['titulo'] if sc >= 0.2 else None,
            'twitch_vistas': tw[i]['vistas'] if sc >= 0.2 else None,
            'twitch_dur': tw[i]['dur'] if sc >= 0.2 else None})
    print('===RESUMEN_INICIO===')
    print(json.dumps(res, ensure_ascii=False))
    print('===RESUMEN_FIN===', flush=True)
    # 4. hojas de fotogramas (5 Shorts top de canales distintos si se puede)
    hechos, canales_h = 0, collections.Counter()
    for j, s in enumerate(top):
        if hechos >= 5 or canales_h[s['canal']] >= 2:
            continue
        h = hoja(f'https://www.youtube.com/shorts/{s["id"]}', f'f{j}')
        if h:
            hechos += 1
            canales_h[s['canal']] += 1
            print(f'===HOJA {s["id"]} {s["canal"]}===')
            print(base64.b64encode(open(h, 'rb').read()).decode())
            print('===HOJA_FIN===', flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
