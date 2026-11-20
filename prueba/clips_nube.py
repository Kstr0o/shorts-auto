"""Prueba de clips en la nube (Twitch o Kick). No sube nada. Uso: clips_nube.py twitch:lacy"""
import json
import os
import subprocess
import sys
import time

import numpy as np

plataforma, canal = sys.argv[1].split(':')
os.makedirs('out', exist_ok=True)
res = {'canal': sys.argv[1]}


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print('ERR', ' '.join(cmd)[:120], r.stderr[-600:], flush=True)
    return r


def lista(url, intentos=5):
    for i in range(intentos):
        r = run(['yt-dlp', '--flat-playlist', '-J', '--impersonate', 'chrome', url])
        if r.returncode:
            r = run(['yt-dlp', '--flat-playlist', '-J', url])
        try:
            e = json.loads(r.stdout).get('entries', []) or []
        except Exception:
            e = []
        print(f'  intento {i + 1}: {len(e)} entradas', flush=True)
        if e:
            return e, i + 1
        time.sleep(15 * (i + 1))
    return [], intentos


if plataforma == 'twitch':
    url_clips = f'https://www.twitch.tv/{canal}/clips?filter=clips&range=7d'
    url_vods = f'https://www.twitch.tv/{canal}/videos?filter=archives&sort=time'
else:
    url_clips = f'https://kick.com/{canal}/clips'
    url_vods = f'https://kick.com/{canal}/videos'

print('CLIPS de', canal)
clips, n = lista(url_clips)
clips.sort(key=lambda x: -(x.get('view_count') or 0))
res['clips'] = len(clips)
res['intentos_clips'] = n
for c in clips[:5]:
    print(' ', c.get('view_count'), c.get('title'), c.get('url'))

print('VODS de', canal)
vods, n = lista(url_vods, intentos=2)
res['vods'] = len(vods)

# descarga: tramo de 60 s del ultimo VOD si hay; si no, el clip mas visto
fuente = None
if vods:
    r = run(['yt-dlp', '--impersonate', 'chrome', '-f', 'best[height<=1080]', '--download-sections', '*00:20:00-00:21:00',
             '-o', 'out/tramo.mp4', vods[0]['url']])
    fuente = 'vod' if os.path.exists('out/tramo.mp4') else None
if not fuente and clips:
    for i in range(3):
        run(['yt-dlp', '--impersonate', 'chrome', '-f', 'best', '-o', 'out/tramo.mp4', clips[0]['url']])
        if os.path.exists('out/tramo.mp4'):
            fuente = 'clip'
            break
        time.sleep(10)
res['descarga'] = fuente or 'FALLO'

if fuente:
    p = run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,r_frame_rate',
             '-of', 'csv=p=0', 'out/tramo.mp4'])
    res['video'] = p.stdout.strip()
    pcm = subprocess.run(['ffmpeg', '-v', 'error', '-i', 'out/tramo.mp4', '-f', 's16le', '-ac', '1', '-ar', '16000', '-'],
                         capture_output=True).stdout
    audio = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768.0
    from faster_whisper import WhisperModel
    m = WhisperModel('small', device='cpu', compute_type='int8')
    seg, _ = m.transcribe(audio, language='en')
    lineas = [f'{s.start:.1f}-{s.end:.1f} {s.text}' for s in seg]
    open('out/texto.txt', 'w').write('\n'.join(lineas))
    res['frases'] = len(lineas)
    run(['ffmpeg', '-y', '-loglevel', 'error', '-i', 'out/tramo.mp4', '-vf', 'crop=ih*9/16:ih,scale=1080:1920',
         '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-c:a', 'aac', 'out/clip_916.mp4'])
    res['corte'] = os.path.exists('out/clip_916.mp4')

print('RESUMEN', json.dumps(res, ensure_ascii=False))
json.dump(res, open('out/resumen.json', 'w'))
if not (fuente and res.get('corte')):
    raise SystemExit(1)
