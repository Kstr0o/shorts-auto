"""Narra un json {pieza: [lineas]} con Supertonic-3, una linea cada vez, y deja un wav por pieza con sus tiempos."""
import json, os, re, sys, inspect
import numpy as np, soundfile as sf
from supertonic import TTS

HABLA = [(r'\b3:07\b', 'three oh seven'), (r'\b3:06\b', 'three oh six'), (r'\b7:00\b', 'seven'), (r'\bAM\b', 'A M'),
         (r'\b2 A M\b', 'two A M'), (r'\b2\b', 'two'), (r'\bL\.', 'L.'), (r'déjà vu', 'day-zha voo')]

def hablado(t):
    for a, b in HABLA: t = re.sub(a, b, t)
    return t

src, out = sys.argv[1], sys.argv[2]
voz = os.environ.get('VOZ', 'M1'); vel = float(os.environ.get('VELOCIDAD', '0.95'))
os.makedirs(out, exist_ok=True)
tts = TTS(model='supertonic-3'); sr = getattr(tts, 'sample_rate', 44100); estilo = tts.get_voice_style(voz)
acepta = inspect.signature(tts.synthesize).parameters
print('parametros synthesize:', list(acepta))
for pieza, lineas in json.load(open(src)).items():
    trozos, tiempos, t0 = [], [], 0.0
    for ln in lineas:
        kw = {'voice_style': estilo, 'lang': 'en'}
        if 'speed' in acepta: kw['speed'] = vel
        wav = tts.synthesize(hablado(ln), **kw)
        a = np.asarray(wav[0] if isinstance(wav, tuple) else wav, dtype=np.float32).squeeze()
        nz = np.where(np.abs(a) > 0.01)[0]
        if len(nz): a = a[max(0, nz[0] - int(sr * 0.05)):nz[-1] + int(sr * 0.08)]
        pausa = np.zeros(int(sr * (0.55 if pieza == 'L' else 0.3)), dtype=np.float32)
        tiempos.append({'texto': ln, 'ini': round(t0, 3), 'fin': round(t0 + len(a) / sr, 3)})
        trozos += [a, pausa]; t0 += (len(a) + len(pausa)) / sr
    sf.write(f'{out}/{pieza}.wav', np.concatenate(trozos), sr)
    json.dump(tiempos, open(f'{out}/{pieza}.json', 'w'), indent=1, ensure_ascii=False)
    print(pieza, round(t0, 1), 's')
