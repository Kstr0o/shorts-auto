"""Prueba de viabilidad (solo lectura) para elegir clips por los picos del directo:
chat del VOD por GQL, descarga de solo audio y velocidad de Whisper pequeno en CPU. Uso: python3 clipper/prueba_picos.py <login>"""
import json
import os
import subprocess
import sys
import time
import urllib.request

GQL_ID = 'kimne78kx3ncx6brgo4mv6wki5h1ko'


def gql(q, v=None, hash_=None, op=None):
    body = {'query': q, 'variables': v or {}} if q else {'operationName': op, 'variables': v or {},
                                                           'extensions': {'persistedQuery': {'version': 1, 'sha256Hash': hash_}}}
    req = urllib.request.Request('https://gql.twitch.tv/gql', data=json.dumps(body).encode(),
                                 headers={'Client-ID': GQL_ID, 'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(req, timeout=30))


def err(nombre, e):
    print(nombre, type(e).__name__, getattr(e, 'code', ''), (e.read()[:300] if hasattr(e, 'read') else ''))


login = sys.argv[1]
r = gql('query($l:String!){user(login:$l){videos(first:3,type:ARCHIVE){edges{node{id lengthSeconds createdAt title}}}}}', {'l': login})
vids = [e['node'] for e in r['data']['user']['videos']['edges']]
print('VODS', json.dumps(vids))
vid = vids[0]['id']

# 1) chat: consulta directa
try:
    r = gql('query($id:ID!,$o:Int){video(id:$id){comments(contentOffsetSeconds:$o){edges{node{contentOffsetSeconds '
            'message{fragments{text}}}}pageInfo{hasNextPage}}}}', {'id': vid, 'o': 600})
    print('CHAT_DIRECTO', json.dumps(r)[:600])
except Exception as e:
    err('CHAT_DIRECTO_ERR', e)
# 2) chat: consulta persistida de la web
try:
    r = gql(None, {'videoID': vid, 'contentOffsetSeconds': 600},
            'b70a3591ff0f4e0313d126c6a1502d79a1c02baebb288227c582044aa76adf6a', 'VideoCommentsByOffsetOrCursor')
    print('CHAT_PERSIST', json.dumps(r)[:600])
except Exception as e:
    err('CHAT_PERSIST_ERR', e)

# 3) solo audio, 30 min
t = time.time()
subprocess.run(['yt-dlp', '-q', '--impersonate', 'chrome', '-F', f'https://www.twitch.tv/videos/{vid}'])
subprocess.run(['yt-dlp', '-q', '--impersonate', 'chrome', '-f', 'Audio_Only/audio_only/worstaudio/worst',
                '--download-sections', '*0-1800', '-o', 'a.%(ext)s', f'https://www.twitch.tv/videos/{vid}'])
f = [x for x in os.listdir('.') if x.startswith('a.')]
print('AUDIO', f, os.path.getsize(f[0]) if f else 0, 'seg_descarga', round(time.time() - t))
if f:
    import numpy as np
    pcm = subprocess.run(['ffmpeg', '-v', 'error', '-i', f[0], '-f', 's16le', '-ac', '1', '-ar', '16000', '-'],
                         capture_output=True).stdout
    a = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768.0
    print('AUDIO_SEG', len(a) / 16000)
    from faster_whisper import WhisperModel
    for modelo in ('base.en', 'small.en'):
        m = WhisperModel(modelo, device='cpu', compute_type='int8', cpu_threads=4)
        t = time.time()
        segs, _ = m.transcribe(a[:600 * 16000], language='en', vad_filter=True)
        txt = ' '.join(s.text for s in segs)
        print('WHISPER', modelo, '600 s de audio en', round(time.time() - t), 's', txt[:300])
