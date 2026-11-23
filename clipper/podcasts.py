"""Canal de clips de podcasts (canal aparte del de streamers) 100% en la nube y SIN IA: GitHub Actions, podcasts_nube.yml.

Solo campanas que dan los episodios en descarga (Dropbox o Google Drive): YouTube bloquea la nube (probado 23/11).
Cada noche, por cada campana activa de clipper/podcasts_nube.json:
  1. bajar       baja la carpeta de la campana (enlace en el secreto FUENTES_PODCASTS, nunca en el repo publico)
  2. analizar    cada episodio nuevo: Whisper rapido del episodio entero + energia de la voz -> tramos candidatos de
                 20-55 s que empiezan y acaban en frase completa, puntuados sin IA (frase gancho, cifras, preguntas,
                 palabras fuertes, energia). Se guardan en la rama podcasts-nube (episodios.json), sin el video.
  3. elegir      los mejores tramos sin usar, repartidos entre episodios (por_noche por campana)
  4. editar      corte, Whisper turbo palabra a palabra, vertical siguiendo la cara, subtitulos, franja con la frase gancho
                 (clipper/editar.py, el mismo motor que el canal de streamers)
  5. subir       YouTube programado (publishAt, huecos HORAS_CLIPS) si existe el secreto YT_TOKEN_PODCASTS; si no, solo
                 deja los clips como artefacto para revisarlos. Despues, borradores a TikTok (token en podcasts-nube).

Uso: python clipper/podcasts.py noche [--estado ../podcasts-nube] [--simular] [--solo firstpress]
     python clipper/podcasts.py probar <video> (analiza un archivo local y muestra los tramos, sin subir nada)
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
import urllib.parse

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(AQUI, '..', 'motor'))
import nube  # noqa: E402  (leer, guardar, run, transcribir, frases, hoy)

CONFIG = json.load(open(os.path.join(AQUI, 'podcasts_nube.json'), encoding='utf-8'))
VIDEO = re.compile(r'\.(mp4|mov|m4v|mkv|webm)$', re.I)
MIN_S, MAX_S, IDEAL = 20.0, 55.0, (25.0, 45.0)
UTC = dt.timezone.utc

CONECTORES = {'and', 'but', 'so', 'because', 'or', 'um', 'uh', 'like', 'yeah', 'right', 'okay', 'ok', 'which', 'that',
              'then', 'also', 'mhm', 'exactly', 'cause', "'cause", 'anyway', 'well'}
FUERTES = {'never', 'always', 'biggest', 'worst', 'best', 'secret', 'mistake', 'mistakes', 'million', 'millions', 'billion',
           'failed', 'fail', 'failure', 'fired', 'broke', 'quit', 'crazy', 'truth', 'nobody', 'everyone', 'everybody',
           'hate', 'love', 'money', 'rich', 'lesson', 'advice', 'wish', 'regret', 'only', 'why', 'how', 'scared', 'afraid',
           'risk', 'bet', 'lost', 'lose', 'win', 'won', 'hardest', 'impossible', 'insane', 'wrong', 'stop', 'start',
           'raise', 'raised', 'sold', 'sell', 'customers', 'brand', 'founder', 'company', 'revenue', 'profit', 'debt',
           'dropped', 'dropout', 'mom', 'dad', 'kid', 'years', 'first', 'last', 'real', 'honestly', 'literally'}
RELLENO = re.compile(r"\b(um+|uh+|you know|i mean|kind of|sort of)\b[, ]*", re.I)


def fuentes():
    try:
        return json.loads(os.environ.get('FUENTES_PODCASTS') or '{}')
    except ValueError:
        print('FUENTES_PODCASTS no es JSON valido ({"clave": "enlace"})'); return {}


# ---------- 1. bajar ----------
def bajar(key, url, destino):
    os.makedirs(destino, exist_ok=True)
    if 'dropbox.com' in url:
        u = urllib.parse.urlparse(url)
        q = dict(urllib.parse.parse_qsl(u.query)); q['dl'] = '1'
        zipf = os.path.join(destino, '_carpeta.zip')
        nube.run(['curl', '-sSL', '--retry', '4', '-o', zipf, urllib.parse.urlunparse(u._replace(query=urllib.parse.urlencode(q)))])
        if os.path.exists(zipf) and os.path.getsize(zipf) > 1000:
            import zipfile
            if zipfile.is_zipfile(zipf):
                # unzip da codigo 2 por avisos sin importancia (la entrada "/" de Dropbox): se mira lo extraido, no el codigo
                nube.run(['unzip', '-o', '-q', zipf, '-d', destino])
            else:  # no es zip: era un archivo suelto
                shutil.move(zipf, os.path.join(destino, 'episodio.mp4'))
            if os.path.exists(zipf):
                os.remove(zipf)
    elif 'drive.google.com' in url:
        nube.run(['gdown', '--folder', '--remaining-ok', '-q', '-O', destino, url] if '/folders/' in url
                 else ['gdown', '-q', '--fuzzy', '-O', destino + '/', url])
    else:
        nube.run(['curl', '-sSL', '--retry', '4', '-o', os.path.join(destino, os.path.basename(urllib.parse.urlparse(url).path) or 'episodio.mp4'), url])
    vids = sorted(p for p in glob.glob(os.path.join(destino, '**', '*'), recursive=True) if VIDEO.search(p) and os.path.getsize(p) > 5_000_000)
    print(f'{key}: {len(vids)} episodios en la carpeta', flush=True)
    return vids


def episodio_id(ruta):
    base = os.path.splitext(os.path.basename(ruta))[0]
    return re.sub(r'[^a-z0-9]+', '-', base.lower()).strip('-')[:40] + '-' + str(os.path.getsize(ruta) // 1_000_000)


def invitado(ruta):
    # "Willie Episode.mp4", "Ethan Arpi Episode.mp4" -> "Willie", "Ethan Arpi"
    base = os.path.splitext(os.path.basename(ruta))[0]
    base = re.sub(r'(?i)\b(full\s+)?(episode|ep\.?|podcast|final|v\d+)\b.*$', '', base).strip(' -_')
    return base[:30] or None


# ---------- 2. analizar ----------
_RAPIDO = []


def transcribir_rapido(wav):
    if not _RAPIDO:
        from faster_whisper import WhisperModel
        _RAPIDO.append(WhisperModel(os.environ.get('WHISPER_EPISODIO', 'small.en'), device='cpu', compute_type='int8'))
    import soundfile as sf
    audio, _ = sf.read(wav, dtype='float32')  # como nube.transcribir: sin pasar por PyAV (choca de version en Actions)
    segs, _ = _RAPIDO[0].transcribe(audio, language='en', word_timestamps=True, vad_filter=True)
    return [{'w': p.word.strip(), 's': round(p.start, 2), 'e': round(p.end, 2)}
            for s in segs for p in (s.words or []) if p.word.strip()]


def energia_episodio(wav, paso=0.5):
    import numpy as np
    import soundfile as sf
    audio, sr = sf.read(wav, dtype='float32')
    n = int(sr * paso)
    k = len(audio) // n
    if not k:
        return [], paso
    rms = np.sqrt((audio[:k * n].reshape(k, n) ** 2).mean(axis=1) + 1e-9)
    db = 20 * np.log10(rms)
    voz = db[db > np.percentile(db, 30)]
    m, s = float(voz.mean()), float(voz.std() or 1)
    return [round((float(x) - m) / s, 2) for x in db], paso


def palabras_de(t):
    return re.findall(r"[a-z0-9$%']+", t.lower())


def gancho(t):
    """Puntuacion sin IA de una frase como arranque de clip."""
    ws = palabras_de(t)
    if not ws:
        return -5.0
    p = 0.0
    if ws[0] in CONECTORES:
        p -= 2.0
    if t.strip().endswith('?'):
        p += 1.2
    if re.search(r'\$|\d|%|\b(million|billion|thousand|hundred)\b', t.lower()):
        p += 1.0
    p += min(3.0, 0.6 * sum(w in FUERTES for w in ws))
    p += 0.3 * min(2, sum(w in ('you', 'your') for w in ws))
    if 6 <= len(ws) <= 22:
        p += 1.0
    elif len(ws) < 4:
        p -= 1.0
    if re.search(r'\b(i|we)\b', ' '.join(ws[:3])):
        p += 0.4  # historia en primera persona
    return round(p, 2)


def tramos(fr, ener, paso, n=14):
    """fr: [[inicio, fin, texto], ...] del episodio. Devuelve los mejores tramos sin solaparse."""
    cand = []
    for i, (a, _, t0) in enumerate(fr):
        g0 = gancho(t0)
        if g0 < 0.5:
            continue
        for j in range(i, len(fr)):
            b = fr[j][1]
            dur = b - a
            if dur > MAX_S:
                break
            if dur < MIN_S or not re.search(r'[.?!]$', fr[j][2].strip()):
                continue
            textos = [x[2] for x in fr[i:j + 1]]
            golpe = max(gancho(x) for x in textos)
            e = ener[int(a / paso):int(b / paso) + 1] if ener else []
            en = sum(e) / len(e) if e else 0.0
            pal = sum(len(palabras_de(x)) for x in textos)
            ritmo = pal / dur  # palabras por segundo: 2,3-3,3 es charla viva
            p = 1.5 * g0 + 0.6 * golpe + 1.2 * en + (1.0 if IDEAL[0] <= dur <= IDEAL[1] else 0.0) \
                + (0.8 if 2.3 <= ritmo <= 3.6 else 0.0) - (2.0 if pal < 40 else 0.0)
            cand.append({'a': round(a, 2), 'b': round(b, 2), 'p': round(p, 2), 'gancho': t0.strip(),
                         'golpe': max(textos, key=gancho).strip(), 'texto': ' '.join(textos)[:600]})
    cand.sort(key=lambda c: -c['p'])
    elegidos = []
    for c in cand:
        if all(c['b'] + 5 < x['a'] or c['a'] > x['b'] + 5 for x in elegidos):
            elegidos.append(c)
        if len(elegidos) >= n:
            break
    return elegidos


def analizar(video, tmp):
    wav = os.path.join(tmp, 'episodio.wav')
    nube.run(['ffmpeg', '-v', 'error', '-y', '-i', video, '-vn', '-ac', '1', '-ar', '16000', wav])
    pal = transcribir_rapido(wav)
    ener, paso = energia_episodio(wav)
    os.remove(wav)
    fr = nube.frases(pal)
    return tramos(fr, ener, paso), round(pal[-1]['e'] if pal else 0)


# ---------- 3. elegir ----------
def limpiar(t):
    t = RELLENO.sub('', t).strip()
    return re.sub(r'\s+', ' ', t)


def recortar(t, maximo):
    t = limpiar(t).rstrip('.,;: ')
    if len(t) <= maximo:
        return t
    corto = t[:maximo + 1].rsplit(' ', 1)[0].rstrip('.,;: ')
    return corto + '...'


def tipo_titulo(t):
    pequenas = {'a', 'an', 'the', 'and', 'or', 'but', 'of', 'to', 'in', 'on', 'at', 'for', 'by', 'is'}
    ws = t.split(' ')
    return ' '.join(w if (i and w.lower() in pequenas) or not w[:1].isalpha() else w[:1].upper() + w[1:] for i, w in enumerate(ws))


def elegir(estado, key, cfg, usados_ids):
    eps = estado.get(key, {})
    n = int(cfg.get('por_noche', 2))
    # ronda por episodios: el mejor tramo sin usar de cada uno, empezando por el episodio menos usado
    colas = []
    for eid, ep in eps.items():
        libres = [t for t in ep.get('tramos', []) if f"{key}-{eid}-{int(t['a'])}" not in usados_ids]
        if libres:
            usos = sum(1 for u in usados_ids if u.startswith(f'{key}-{eid}-'))
            colas.append((usos, -libres[0]['p'], eid, libres))
    colas.sort()
    picks = []
    ronda = 0
    while len(picks) < n and any(len(c[3]) > ronda for c in colas):
        for _, _, eid, libres in colas:
            if ronda < len(libres) and len(picks) < n:
                picks.append(dict(libres[ronda], episodio=eid, id=f"{key}-{eid}-{int(libres[ronda]['a'])}"))
        ronda += 1
    return picks


def textos(c, cfg, ep):
    frase = c['gancho'] if gancho(c['gancho']) >= gancho(c['golpe']) - 0.5 else c['golpe']
    titulo = tipo_titulo(recortar(frase, 65))
    if ep.get('invitado') and len(titulo) + len(ep["invitado"]) + 3 <= 85:
        titulo = f"{titulo} | {ep['invitado']}"
    arriba = recortar(frase, 45).upper()
    claves = [w for w in palabras_de(frase) if w in FUERTES or re.search(r'\d|\$', w)][:3]
    tags_hash = ' '.join(cfg.get('hashtags', [])[:2])
    men = cfg.get('menciones', {})
    desc = f"{cfg['pie_obligatorio']} {men.get('youtube', '')}".strip() + f"\n\n{tags_hash}"
    pie_tt = f"{titulo}\n\n{cfg['pie_obligatorio']} {men.get('tiktok', '')}".strip() + f"\n\n{tags_hash}"
    return titulo, arriba, claves, desc, pie_tt


# ---------- 4. editar ----------
def editar(picks, archivos, estado, key, cfg, salida, tmp):
    import editar as ed
    import palabras_tiktok as pt
    os.environ.setdefault('FPS_CLIP', '30'); os.environ.setdefault('CRF_CLIP', '18'); os.environ.setdefault('AUDIO_CLIP', '192k')
    os.makedirs(salida, exist_ok=True)
    hechos = []
    for k, c in enumerate(picks, 1):
        ep = estado[key][c['episodio']]
        video_ep = archivos.get(c['episodio'])
        if not video_ep:
            print('  episodio ya no esta en la carpeta', c['episodio']); continue
        carpeta = os.path.join(tmp, 'trabajo', c['id']); os.makedirs(carpeta, exist_ok=True)
        video = os.path.join(carpeta, 'video.mp4')
        a, b = max(0.0, c['a'] - 0.15), c['b'] + 0.4
        nube.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{a:.2f}', '-to', f'{b:.2f}', '-i', video_ep, '-vf', 'scale=-2:min(ih\\,1080)',
                  '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '14', '-c:a', 'aac', '-b:a', '192k', video])
        if not os.path.exists(video) or os.path.getsize(video) < 100_000:
            print('  no se pudo cortar', c['id']); continue
        pal = nube.transcribir(video, cfg.get('idioma', 'en'))
        titulo, arriba, claves, desc, pie_tt = textos(c, cfg, ep)
        dicho = ' '.join(p['w'] for p in pal)
        picante = pt.picante(titulo, arriba, desc, dicho)
        pal = [dict(p, w=pt.palabra_sub(p['w'])) for p in pal]
        m = {'inicio': 0.0, 'fin': b - a, 'titulo': titulo, 'descripcion': desc, 'tags': cfg.get('tags', []),
             'claves': claves, 'acciones': [], 'texto_arriba': pt.limpiar(arriba), 'nota': c['p'], 'gancho': c['gancho'],
             'campana': cfg.get('campana'), 'encuadre': None}
        ed.render_clip(carpeta, k, m, pal, cfg.get('color', '#FFD400'), cfg.get('idioma', 'en'), {})
        hecho = sorted(glob.glob(os.path.join(carpeta, 'clips', f'{k:02d}_*.mp4')))
        if not hecho:
            continue
        nombre = os.path.join(salida, f'{key}_{k:02d}')
        shutil.move(hecho[0], nombre + '.mp4')
        meta = nube.leer(hecho[0][:-4] + '.json', {})
        meta.update(id=c['id'], key=key, streamer=cfg['nombre'], campana=cfg.get('campana'), fuente=f'podcast:{key}',
                    inicio=a, fin=b, episodio=c['episodio'], formato='clip', sintetico=False, picante=picante,
                    texto_arriba=m['texto_arriba'], titulo_tiktok=pt.limpiar(titulo), pie=pie_tt, nota=c['p'])
        nube.guardar(nombre + '.json', meta)
        nube.run(['ffmpeg', '-v', 'error', '-y', '-ss', '3', '-i', nombre + '.mp4', '-frames:v', '1', '-vf', 'scale=360:-1', nombre + '.jpg'])
        shutil.rmtree(carpeta, ignore_errors=True)
        hechos.append(meta)
        print(f"  {key}_{k:02d}  {b - a:.0f}s  nota {c['p']}  {titulo}", flush=True)
    return hechos


# ---------- 5. subir ----------
def subir_youtube(carpeta, estado_dir, simular=False):
    import programar
    reg = nube.leer(os.path.join(estado_dir, 'programados.json'), {'clips': []})
    metas = sorted(((m, nube.leer(m, {})) for m in glob.glob(os.path.join(carpeta, '*.json'))), key=lambda mj: -float(mj[1].get('nota') or 0))
    metas = [(m, j) for m, j in metas if j.get('formato') == 'clip' and os.path.exists(m[:-5] + '.mp4')]
    if not os.environ.get('YT_TOKEN_PODCASTS'):
        print('Sin YT_TOKEN_PODCASTS (canal aun sin crear): los clips quedan solo como artefacto para revisarlos')
        return 0
    import subir as s
    ahora = dt.datetime.now(UTC)
    libres = programar.huecos_libres({c['publishAt'] for c in reg['clips'] if c.get('publishAt')}, ahora)
    n = 0
    for (mj, meta) in metas:
        if n >= len(libres):
            break
        hora = libres[n].strftime('%Y-%m-%dT%H:%M:%SZ')
        print(f"{meta['titulo'][:60]:<60} -> {hora}", flush=True)
        if simular:
            n += 1; continue
        try:
            vid = s.subir(mj[:-5] + '.mp4', mj, 'PODCASTS', hora)
        except Exception as e:
            print(f'  FALLO {type(e).__name__}: {str(e)[:300]}'); continue
        n += 1
        clip = {'id': meta['id'], 'url': f'https://youtube.com/shorts/{vid}', 'publishAt': hora, 'titulo': meta['titulo'],
                'campana': meta.get('campana'), 'streamer': meta.get('streamer'), 'fuente': meta.get('fuente'),
                'episodio': meta.get('episodio'), 'inicio': meta.get('inicio'), 'fin': meta.get('fin'), 'noche': nube.hoy(),
                'enlace_enviado': False}
        if programar.AVISO_TEMA and clip['campana']:
            try:
                clip['aviso'] = programar.avisar(clip, ahora)
            except Exception as e:
                print('  aviso no enviado', type(e).__name__)
        reg['clips'].append(clip)
        nube.guardar(os.path.join(estado_dir, 'programados.json'), reg)
    print(f'RESUMEN YouTube: {n} subidos' + (' (simulado)' if simular else ''))
    return n


# ---------- noche ----------
def noche(estado_dir, simular=False, solo=None):
    tmp = os.environ.get('PODCASTS_TMP', '/tmp/podcasts')
    os.makedirs(tmp, exist_ok=True)
    import podcasts_config
    podcasts_config.cargar(estado_dir)  # token de YouTube y enlaces guardados cifrados en la rama
    estado = nube.leer(os.path.join(estado_dir, 'episodios.json'), {})
    usados = nube.leer(os.path.join(estado_dir, 'usados.json'), [])
    enlaces = fuentes()
    for key, cfg in CONFIG.items():
        if not cfg.get('activo', True) or (solo and key not in solo):
            continue
        if not enlaces.get(key):
            print(f'{key}: falta su enlace en el secreto FUENTES_PODCASTS'); continue
        carpeta = os.path.join(tmp, key)
        vids = bajar(key, enlaces[key], carpeta)
        archivos = {episodio_id(v): v for v in vids}
        estado.setdefault(key, {})
        for eid, v in archivos.items():
            if eid in estado[key]:
                continue
            print(f'  analizando {os.path.basename(v)}', flush=True)
            try:
                ts, dur = analizar(v, tmp)
            except Exception as e:  # un archivo roto no tumba la noche
                print(f'    no se pudo analizar ({type(e).__name__}): se salta', flush=True); continue
            estado[key][eid] = {'archivo': os.path.basename(v), 'invitado': invitado(v), 'duracion': dur,
                                'analizado': nube.hoy(), 'tramos': ts}
            print(f'    {len(ts)} tramos, mejor nota {ts[0]["p"] if ts else "-"}: {ts[0]["gancho"][:80] if ts else ""}', flush=True)
            nube.guardar(os.path.join(estado_dir, 'episodios.json'), estado)
        picks = elegir(estado, key, cfg, {u['id'] for u in usados})
        print(f'{key}: {len(picks)} tramos para esta noche', flush=True)
        hechos = editar(picks, archivos, estado, key, cfg, 'out/clips', tmp)
        if hechos and not simular and os.environ.get('YT_TOKEN_PODCASTS'):
            usados += [{'id': h['id'], 'noche': nube.hoy()} for h in hechos]
        shutil.rmtree(carpeta, ignore_errors=True)
    nube.guardar(os.path.join(estado_dir, 'usados.json'), usados)
    subir_youtube('out/clips', estado_dir, simular)


def probar(video):
    tmp = os.path.join('out', 'tmp'); os.makedirs(tmp, exist_ok=True)
    ts, dur = analizar(video, tmp)
    print(f'{os.path.basename(video)}: {dur} s, {len(ts)} tramos')
    for t in ts:
        print(f"  {t['p']:>5}  {t['a']:>7.1f}-{t['b']:<7.1f} {t['b'] - t['a']:>4.0f}s  {t['gancho'][:90]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('fase', choices=['noche', 'probar'])
    ap.add_argument('arg', nargs='?')
    ap.add_argument('--estado', default='../podcasts-nube')
    ap.add_argument('--simular', action='store_true')
    ap.add_argument('--solo', default='')
    a = ap.parse_args()
    if a.fase == 'probar':
        probar(a.arg)
    else:
        noche(a.estado, a.simular, {s.strip() for s in a.solo.split(',') if s.strip()} or None)


if __name__ == '__main__':
    main()
