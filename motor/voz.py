"""Voz: edge-tts (voces neuronales de Microsoft, gratis) con tiempos por palabra.
Si edge-tts no esta disponible, usa Piper (offline) y estima los tiempos.
"""
import asyncio
import json
import os
import re
import subprocess
import wave

VOCES_EDGE= {'es': 'es-ES-AlvaroNeural', 'en': 'en-US-AndrewNeural'}
VOCES_PIPER= {'es': 'es-carlfm-x-low.onnx', 'en': 'en-us-ryan-high.onnx'}
RATE= {'es': '+12%', 'en': '+8%'}


def _duracion(path):
    out= subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                        capture_output=True, text=True).stdout
    return float(out.strip())


async def _edge(texto, idioma, mp3):
    import edge_tts
    proxy= os.environ.get('EDGE_PROXY')
    c= edge_tts.Communicate(texto, VOCES_EDGE[idioma], rate=RATE[idioma], boundary='WordBoundary', proxy=proxy)
    palabras= []
    with open(mp3, 'wb') as f:
        async for m in c.stream():
            if m['type'] == 'audio':
                f.write(m['data'])
            elif m['type'] == 'WordBoundary':
                ini= m['offset'] / 1e7
                palabras.append({'p': m['text'], 'ini': ini, 'fin': ini + m['duration'] / 1e7})
    return palabras


def _estimar(texto, dur):
    # reparto el tiempo por longitud de palabra y sumo pausas en la puntuacion
    toks= texto.split()
    pesos= [len(re.sub(r'\W', '', t)) + 2 + (4 if re.search(r'[.,!?;:…]$', t) else 0) for t in toks]
    tot= sum(pesos) or 1
    t= 0.05
    util= dur - 0.15
    res= []
    for tok, w in zip(toks, pesos):
        d= util * w / tot
        res.append({'p': tok, 'ini': t, 'fin': t + d * 0.85})
        t+= d
    return res


def sintetizar(texto, idioma, wav_out, dir_piper=None):
    """Genera wav (mono 44.1k) y devuelve (duracion, palabras[{p, ini, fin}])."""
    motor= os.environ.get('MOTOR_VOZ', 'edge')
    palabras= None
    if motor == 'edge':
        try:
            mp3= wav_out.replace('.wav', '.mp3')
            palabras= asyncio.run(_edge(texto, idioma, mp3))
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', mp3, '-ac', '1', '-ar', '44100', wav_out], check=True)
            # los WordBoundary traen la palabra sin puntuacion: recupero los tokens originales
            toks= texto.split()
            if len(toks) == len(palabras):
                for w, t in zip(palabras, toks):
                    w['p']= t
        except Exception as e:  # si el servicio falla, sigo con la voz offline
            print(f'edge-tts fallo ({e}); uso piper')
            motor, palabras= 'piper', None
    if motor != 'edge':
        modelo= os.path.join(dir_piper or os.environ.get('DIR_PIPER', '.'), VOCES_PIPER[idioma])
        tmp= wav_out.replace('.wav', '_raw.wav')
        subprocess.run(['python3', '-m', 'piper', '-m', modelo, '-f', tmp, '--length-scale', '0.92'],
                       input=texto.encode(), check=True, capture_output=True)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp, '-ac', '1', '-ar', '44100', wav_out], check=True)
    dur= _duracion(wav_out)
    if not palabras:
        palabras= _estimar(texto, dur)
    return dur, palabras
