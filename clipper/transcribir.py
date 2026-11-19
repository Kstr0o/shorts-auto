"""Transcribe trabajo/<id>/video.mp4 con Whisper en local (gratis, sin tokens) y guarda el tiempo de cada palabra.

Uso: python clipper/transcribir.py trabajo/<id> [--modelo large-v3-turbo|small] [--idioma es|en]
Salida: palabras.json ([{w, s, e}]) y transcripcion.txt (una frase por linea con [inicio-fin] en segundos),
que es lo que lee Claude para elegir los momentos.
Motor: faster-whisper (portatil). Si no esta, usa sherpa-onnx con el modelo whisper turbo de la carpeta SHERPA_WHISPER
(en ese caso el tiempo de cada palabra se reparte dentro de cada trozo: vale para subtitulos, algo menos fino).
"""
import argparse, json, os, re, subprocess, sys


def wav16(carpeta):
    w= os.path.join(carpeta, 'audio16k.wav')
    if not os.path.exists(w):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', os.path.join(carpeta, 'video.mp4'), '-ac', '1', '-ar', '16000', w], check=True)
    return w


def con_faster_whisper(wav, modelo, idioma):
    from faster_whisper import WhisperModel
    m= WhisperModel(modelo, device='auto', compute_type='int8')
    segs, _= m.transcribe(wav, language=idioma, word_timestamps=True, vad_filter=True)
    out= []
    for s in segs:
        for p in s.words or []:
            out.append({'w': p.word.strip(), 's': round(p.start, 2), 'e': round(p.end, 2)})
        print(f'  {s.end/60:6.1f} min', end='\r', flush=True)
    return out


def trozos_por_silencio(wav, maximo=25.0):
    """Corta en silencios para que ningun trozo pase de 25 s (limite de whisper en sherpa)."""
    r= subprocess.run(['ffmpeg', '-i', wav, '-af', 'silencedetect=n=-35dB:d=0.3', '-f', 'null', '-'], capture_output=True, text=True)
    silencios= [float(x) for x in re.findall(r'silence_end: ([\d.]+)', r.stderr)]
    dur= float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', wav],
                              capture_output=True, text=True).stdout)
    cortes, ini= [], 0.0
    while ini < dur - 0.2:
        cand= [s for s in silencios if ini + 4 < s <= ini + maximo]
        fin= cand[-1] if cand else min(ini + maximo, dur)
        cortes.append((ini, fin)); ini= fin
    return cortes


def con_sherpa(wav, idioma):
    import sherpa_onnx, soundfile as sf
    d= os.environ.get('SHERPA_WHISPER', 'sherpa-onnx-whisper-turbo')
    r= sherpa_onnx.OfflineRecognizer.from_whisper(encoder=f'{d}/turbo-encoder.int8.onnx', decoder=f'{d}/turbo-decoder.int8.onnx',
                                                  tokens=f'{d}/turbo-tokens.txt', language=idioma or '', num_threads=os.cpu_count() or 4)
    a, sr= sf.read(wav, dtype='float32'); out= []
    for ini, fin in trozos_por_silencio(wav):
        st= r.create_stream(); st.accept_waveform(sr, a[int(ini*sr):int(fin*sr)]); r.decode_stream(st)
        pal= st.result.text.split()
        if not pal:
            continue
        pesos= [len(p) + 2 for p in pal]; t= ini; paso= (fin - ini) / sum(pesos)
        for p, k in zip(pal, pesos):
            out.append({'w': p, 's': round(t, 2), 'e': round(t + k*paso, 2)}); t+= k*paso
        print(f'  {fin/60:6.1f} min', end='\r', flush=True)
    return out


def frases(palabras):
    """Agrupa en frases (corta en . ? ! o en pausas de mas de 0,8 s o a las 30 palabras)."""
    grupos, act= [], []
    for i, p in enumerate(palabras):
        act.append(p)
        pausa= i + 1 < len(palabras) and palabras[i+1]['s'] - p['e'] > 0.8
        if re.search(r'[.?!]$', p['w']) or pausa or len(act) >= 30:
            grupos.append(act); act= []
    if act:
        grupos.append(act)
    return grupos


def main():
    ap= argparse.ArgumentParser()
    ap.add_argument('carpeta'); ap.add_argument('--modelo', default='large-v3-turbo'); ap.add_argument('--idioma')
    a= ap.parse_args()
    wav= wav16(a.carpeta)
    try:
        if os.environ.get('SHERPA_WHISPER'):
            raise RuntimeError('SHERPA_WHISPER definido')
        palabras= con_faster_whisper(wav, a.modelo, a.idioma)
    except Exception as e:   # sin faster-whisper o sin poder bajar su modelo
        print(f'faster-whisper no disponible ({e}): uso sherpa-onnx', file=sys.stderr)
        palabras= con_sherpa(wav, a.idioma)
    json.dump(palabras, open(os.path.join(a.carpeta, 'palabras.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    with open(os.path.join(a.carpeta, 'transcripcion.txt'), 'w', encoding='utf-8') as f:
        for g in frases(palabras):
            f.write(f"[{g[0]['s']:.1f}-{g[-1]['e']:.1f}] {' '.join(p['w'] for p in g)}\n")
    print(f'\n{len(palabras)} palabras -> transcripcion.txt')


if __name__ == '__main__':
    main()
