"""Voz Supertonic-3 (M5) para los Shorts. Lee voz_in/<id>_<idioma>.txt (una frase por linea) y escribe voz_out/<id>_<idioma>.wav y .json con el inicio y fin de cada linea."""
import glob, json, os, sys
import numpy as np, soundfile as sf
from supertonic import TTS

VOZ = os.environ.get('VOZ', 'M5')
PAUSA = 0.34

def recortar(w, sr, umbral=0.004):
    idx = np.where(np.abs(w) > umbral)[0]
    if len(idx) == 0:
        return w
    a, b = max(0, idx[0] - int(0.03 * sr)), min(len(w), idx[-1] + int(0.06 * sr))
    return w[a:b]

tts = TTS(model='supertonic-3')
st = tts.get_voice_style(VOZ)
sr = tts.sample_rate
os.makedirs('voz_out', exist_ok=True)
for f in sorted(glob.glob('voz_in/*.txt')):
    nombre = os.path.basename(f)[:-4]
    lang = nombre.rsplit('_', 1)[1]
    lineas = [l.strip() for l in open(f, encoding='utf-8') if l.strip()]
    trozos, segs, t = [], [], 0.0
    for l in lineas:
        wav, _ = tts.synthesize(l, voice_style=st, lang=lang)
        w = recortar(np.asarray(wav).squeeze().astype(np.float32), sr)
        segs.append([round(t, 3), round(t + len(w) / sr, 3)])
        trozos.append(w); trozos.append(np.zeros(int(PAUSA * sr), dtype=np.float32))
        t += len(w) / sr + PAUSA
    out = np.concatenate(trozos[:-1])
    sf.write(f'voz_out/{nombre}.wav', out, sr)
    json.dump({'voz': VOZ, 'sr': sr, 'dur': round(len(out) / sr, 3), 'segs': segs, 'lineas': lineas}, open(f'voz_out/{nombre}.json', 'w'), ensure_ascii=False)
    print(nombre, round(len(out) / sr, 1), 's')
