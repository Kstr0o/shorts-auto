"""Prueba de clips en la nube (Lacy, Twitch). No sube nada."""
import json
import os
import subprocess

import numpy as np

os.makedirs('out', exist_ok=True)


def run(cmd):
    print('>>', ' '.join(cmd), flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stderr[-1500:], flush=True)
    return r


# 1) clips mas vistos de la semana (ranking)
r = run(['yt-dlp', '--flat-playlist', '-J', 'https://www.twitch.tv/lacy/clips?filter=clips&range=7d'])
clips = json.loads(r.stdout).get('entries', []) if r.returncode == 0 else []
clips.sort(key=lambda x: -(x.get('view_count') or 0))
print('CLIPS:', len(clips))
for c in clips[:5]:
    print(' ', c.get('view_count'), c.get('title'), c.get('url'))

# 2) info del mejor clip: VOD de origen y segundo
if clips:
    r = run(['yt-dlp', '-J', clips[0]['url']])
    if r.returncode == 0:
        info = json.loads(r.stdout)
        print('VOD_ORIGEN:', {k: info.get(k) for k in ('video_id', 'vod_id', 'vod_offset', 'section_start') if info.get(k) is not None})
    run(['yt-dlp', '-f', 'best', '-o', 'out/tramo.mp4', clips[0]['url']])

if not os.path.exists('out/tramo.mp4'):
    print('RESULTADO: FALLO DESCARGA')
    raise SystemExit(1)
run(['ffprobe', '-v', 'error', '-show_entries', 'stream=width,height,r_frame_rate', '-of', 'csv=p=0', 'out/tramo.mp4'])

# 3) transcripcion (audio decodificado con ffmpeg, sin av)
pcm = subprocess.run(['ffmpeg', '-v', 'error', '-i', 'out/tramo.mp4', '-f', 's16le', '-ac', '1', '-ar', '16000', '-'],
                     capture_output=True).stdout
audio = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768.0
from faster_whisper import WhisperModel
m = WhisperModel('small', device='cpu', compute_type='int8')
seg, _ = m.transcribe(audio, language='en')
lineas = [f'{s.start:.1f}-{s.end:.1f} {s.text}' for s in seg]
open('out/texto.txt', 'w').write('\n'.join(lineas))
print('TRANSCRIPCION:', len(lineas), 'frases')
print('\n'.join(lineas[:5]))

# 4) corte 9:16
run(['ffmpeg', '-y', '-loglevel', 'error', '-i', 'out/tramo.mp4', '-vf', 'crop=ih*9/16:ih,scale=1080:1920',
     '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-c:a', 'aac', 'out/clip_916.mp4'])
print('RESULTADO:', 'OK' if os.path.exists('out/clip_916.mp4') else 'FALLO CORTE')
