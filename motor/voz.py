"""Voz: edge-tts (voces neuronales de Microsoft, gratis) con tiempos por palabra.
Si edge-tts no esta disponible, usa Piper (offline) y estima los tiempos.
"""
import asyncio
import json
import os
import re
import subprocess
import time
import wave

# por idioma, de la preferida a las de reserva; un episodio usa siempre una sola voz
VOCES_EDGE= {'es': ['es-ES-AlvaroNeural', 'es-MX-JorgeNeural'], 'en': ['en-US-GuyNeural', 'en-US-ChristopherNeural', 'en-US-AndrewNeural']}
VOCES_PIPER= {'es': 'es-carlfm-x-low.onnx', 'en': 'en-us-ryan-high.onnx'}
RATE= {'es': '+18%', 'en': '+15%'}


class VozFallo(Exception):
    pass


def _duracion(path):
    out= subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                        capture_output=True, text=True).stdout
    return float(out.strip())


async def _edge(texto, voz_edge, idioma, mp3):
    import edge_tts
    proxy= os.environ.get('EDGE_PROXY')
    c= edge_tts.Communicate(texto, voz_edge, rate=RATE[idioma], boundary='WordBoundary', proxy=proxy)
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


def sintetizar(texto, idioma, wav_out, motor='edge', voz_edge=None, dir_piper=None):
    """Genera wav (mono 44.1k) y devuelve (duracion, palabras[{p, ini, fin}]).
    Con motor 'edge' reintenta y, si no hay manera, lanza VozFallo para que el episodio cambie de voz entero."""
    palabras= None
    if motor == 'edge':
        mp3= wav_out.replace('.wav', '.mp3')
        ultimo= None
        for intento in range(4):
            try:
                palabras= asyncio.run(_edge(texto, voz_edge or VOCES_EDGE[idioma][0], idioma, mp3))
                if os.path.getsize(mp3) > 1000:
                    break
                palabras= None
            except Exception as e:
                ultimo= e
                palabras= None
            time.sleep(2 + 3 * intento)
        if palabras is None:
            raise VozFallo(f'{voz_edge}: {ultimo}')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', mp3, '-ac', '1', '-ar', '44100', wav_out], check=True)
        # los WordBoundary traen la palabra sin puntuacion: recupero los tokens originales
        toks= texto.split()
        if len(toks) == len(palabras):
            for w, t in zip(palabras, toks):
                w['p']= t
        else:
            palabras= []
    else:
        modelo= os.path.join(dir_piper or os.environ.get('DIR_PIPER', '.'), VOCES_PIPER[idioma])
        tmp= wav_out.replace('.wav', '_raw.wav')
        subprocess.run(['python3', '-m', 'piper', '-m', modelo, '-f', tmp, '--length-scale', '0.92'],
                       input=texto.encode(), check=True, capture_output=True)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp, '-ac', '1', '-ar', '44100', wav_out], check=True)
    dur= _duracion(wav_out)
    if not palabras:
        palabras= _estimar(texto, dur)
    return dur, palabras


def opciones(idioma):
    """Lista de (motor, voz) a probar en orden para un episodio completo."""
    if os.environ.get('MOTOR_VOZ', 'edge') != 'edge':
        return [('piper', None)]
    return [('edge', v) for v in VOCES_EDGE[idioma]] + [('piper', None)]
