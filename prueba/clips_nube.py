"""Prueba de clips en la nube (Lacy, Twitch). No sube nada."""
import json
import os
import subprocess

os.makedirs('out', exist_ok=True)


def run(cmd):
    print('>>', ' '.join(cmd), flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout[-2000:], r.stderr[-2000:], flush=True)
    return r


# 1) clips mas vistos de la semana
r = run(['yt-dlp', '--flat-playlist', '-J', 'https://www.twitch.tv/lacy/clips?filter=clips&range=7d'])
clips = json.loads(r.stdout).get('entries', []) if r.returncode == 0 else []
clips.sort(key=lambda x: -(x.get('view_count') or 0))
print('CLIPS:', len(clips))
for c in clips[:10]:
    print(' ', c.get('view_count'), c.get('title'), c.get('url'))

# 2) ultimo VOD y tramo de 60 s
r = run(['yt-dlp', '--flat-playlist', '-J', 'https://www.twitch.tv/lacy/videos?filter=archives&sort=time'])
vods = json.loads(r.stdout).get('entries', []) if r.returncode == 0 else []
print('VODS:', len(vods))
if vods:
    run(['yt-dlp', '-f', 'best[height<=1080]', '--download-sections', '*00:30:00-00:31:00',
         '-o', 'out/tramo.mp4', vods[0]['url']])
elif clips:
    run(['yt-dlp', '-o', 'out/tramo.mp4', clips[0]['url']])

if not os.path.exists('out/tramo.mp4'):
    print('RESULTADO: FALLO DESCARGA')
    raise SystemExit(1)

# 3) transcripcion
from faster_whisper import WhisperModel
m = WhisperModel('small', device='cpu', compute_type='int8')
seg, _ = m.transcribe('out/tramo.mp4')
lineas = [f'{s.start:.1f}-{s.end:.1f} {s.text}' for s in seg]
open('out/texto.txt', 'w').write('\n'.join(lineas))
print('TRANSCRIPCION:', len(lineas), 'frases')

# 4) corte 9:16
r = run(['ffmpeg', '-y', '-loglevel', 'error', '-i', 'out/tramo.mp4', '-vf', 'crop=ih*9/16:ih,scale=1080:1920',
         '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-c:a', 'aac', 'out/clip_916.mp4'])
print('RESULTADO:', 'OK' if os.path.exists('out/clip_916.mp4') else 'FALLO CORTE')
