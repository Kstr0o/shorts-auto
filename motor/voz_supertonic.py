"""Voz Supertonic-3 (M5) para los Shorts. Lee voz_in/<id>_<idioma>.txt (una frase por linea) y escribe voz_out/<id>_<idioma>.wav y .json con el inicio y fin de cada linea."""
import glob, json, os, sys
import difflib, re, unicodedata
import numpy as np, soundfile as sf
from supertonic import TTS

VOZ = os.environ.get('VOZ', 'M5')
PAUSA = 0.34

def recortar(w, sr, umbral=0.0015):
    idx = np.where(np.abs(w) > umbral)[0]
    if len(idx) == 0:
        return w
    a, b = max(0, idx[0] - int(0.03 * sr)), min(len(w), idx[-1] + int(0.14 * sr))
    return w[a:b]

from faster_whisper import WhisperModel
asr = WhisperModel('small', device='cpu', compute_type='int8')
norm = lambda x: re.sub(r'[^a-z0-9 ]', '', unicodedata.normalize('NFD', x.lower()).encode('ascii', 'ignore').decode()).strip()
def mejor_toma(linea, lang, tts, st, sr, n=4):
    mejores = None
    for k in range(n):
        wav, _ = tts.synthesize(linea, voice_style=st, lang=lang, total_steps=8 + 2 * (k % 3)) if k else tts.synthesize(linea, voice_style=st, lang=lang)
        w = recortar(np.asarray(wav).squeeze().astype(np.float32), sr)
        sf.write('/tmp/t.wav', w, sr)
        segs, _ = asr.transcribe('/tmp/t.wav', language=lang)
        txt = ' '.join(s.text for s in segs)
        r = difflib.SequenceMatcher(None, norm(txt), norm(linea)).ratio()
        print('  toma', k, round(r, 3), round(len(w) / sr, 2), txt)
        if mejores is None or (r, len(w)) > (mejores[0], len(mejores[1])):
            mejores = (r, w)
    return mejores[1]
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
        w = mejor_toma(l, lang, tts, st, sr)
        segs.append([round(t, 3), round(t + len(w) / sr, 3)])
        trozos.append(w); trozos.append(np.zeros(int(PAUSA * sr), dtype=np.float32))
        t += len(w) / sr + PAUSA
    out = np.concatenate(trozos[:-1])
    sf.write(f'voz_out/{nombre}.wav', out, sr)
    json.dump({'voz': VOZ, 'sr': sr, 'dur': round(len(out) / sr, 3), 'segs': segs, 'lineas': lineas}, open(f'voz_out/{nombre}.json', 'w'), ensure_ascii=False)
    print(nombre, round(len(out) / sr, 1), 's')
