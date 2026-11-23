"""Prueba de motores de voz en CPU (GitHub Actions). Uso: python bench.py <motor>
Genera la misma frase en espanol e ingles y apunta tiempos en tiempos.txt."""
import asyncio, os, sys, time
from pathlib import Path
import numpy as np
import soundfile as sf

ES = ("Aquella noche, Toni encontró una puerta que no estaba ahí el día anterior. "
      "Dudó un segundo, respiró hondo y la abrió. "
      "Lo que vio al otro lado le cambió la vida para siempre. ¿Tú la habrías abierto?")
EN = ("That night, Toni found a door that wasn't there the day before. "
      "He hesitated for a second, took a deep breath, and opened it. "
      "What he saw on the other side changed his life forever. Would you have opened it?")
OUT = Path("salida"); OUT.mkdir(exist_ok=True)
LOG = OUT / "tiempos.txt"


def guardar(nombre, wav, sr, t_sint, t_carga):
    wav = np.asarray(wav, dtype=np.float32).squeeze()
    pico = np.abs(wav).max() or 1
    sf.write(OUT / f"{nombre}.wav", wav / pico * 0.89, sr, subtype="PCM_16")
    dur = len(wav) / sr
    linea = f"{nombre}\tcarga {t_carga:.1f}s\tsintesis {t_sint:.1f}s\taudio {dur:.1f}s\tRTF {t_sint/dur:.2f}"
    print(linea, flush=True)
    with open(LOG, "a") as f:
        f.write(linea + "\n")


def medir(nombre, fn, t_carga):
    t = time.time(); wav, sr = fn(); guardar(nombre, wav, sr, time.time() - t, t_carga)


def supertonic():
    from supertonic import TTS
    t = time.time(); tts = TTS(model="supertonic-3"); c = time.time() - t
    sr = getattr(tts, "sample_rate", 44100)
    for voz in ("M5", "M1"):
        st = tts.get_voice_style(voice_name=voz)
        for lang, txt in (("es", ES), ("en", EN)):
            medir(f"supertonic_{voz}_{lang}", lambda: (tts.synthesize(text=txt, voice_style=st, total_steps=10, speed=1.05, lang=lang)[0], sr), c)


def edge():
    import edge_tts, subprocess
    for nombre, voz, txt in (("edge_jorge_es", "es-MX-JorgeNeural", ES), ("edge_alvaro_es", "es-ES-AlvaroNeural", ES), ("edge_andrew_en", "en-US-AndrewNeural", EN)):
        t = time.time()
        asyncio.run(edge_tts.Communicate(txt, voz).save("/tmp/e.mp3"))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "/tmp/e.mp3", "/tmp/e.wav"], check=True)
        w, sr = sf.read("/tmp/e.wav"); guardar(nombre, w, sr, time.time() - t, 0)


def kokoro():
    from kokoro import KPipeline
    for lang_code, voces, txt, tag in (("e", ("em_alex", "em_santa", "ef_dora"), ES, "es"), ("a", ("am_michael", "am_fenrir", "af_heart"), EN, "en"), ("b", ("bm_george", "bm_fable"), EN, "enGB")):
        t = time.time(); p = KPipeline(lang_code=lang_code, repo_id="hexgrad/Kokoro-82M"); c = time.time() - t
        for v in voces:
            medir(f"kokoro_{v}_{tag}", lambda: (np.concatenate([a.numpy() if hasattr(a, "numpy") else a for _, _, a in p(txt, voice=v, speed=1.0)]), 24000), c)


def qwen(tam):
    import torch
    torch.set_num_threads(os.cpu_count())
    from qwen_tts import Qwen3TTSModel
    if tam == "design":
        t = time.time(); m = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign", device_map="cpu", dtype=torch.float32); c = time.time() - t
        voz_es = "Voz masculina grave y cálida de narrador de historias, unos 35 años, acento de España, ritmo pausado y con intriga."
        voz_en = "Deep, warm male storyteller voice, about 35, American accent, calm pace with suspense."
        medir("qwen17_design_es", lambda: (lambda r: (r[0][0], r[1]))(m.generate_voice_design(text=ES, language="Spanish", instruct=voz_es)), c)
        medir("qwen17_design_en", lambda: (lambda r: (r[0][0], r[1]))(m.generate_voice_design(text=EN, language="English", instruct=voz_en)), c)
    else:
        t = time.time(); m = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice", device_map="cpu", dtype=torch.float32); c = time.time() - t
        for spk in ("Ryan", "Aiden"):
            medir(f"qwen06_{spk}_es", lambda: (lambda r: (r[0][0], r[1]))(m.generate_custom_voice(text=ES, language="Spanish", speaker=spk)), c)
            medir(f"qwen06_{spk}_en", lambda: (lambda r: (r[0][0], r[1]))(m.generate_custom_voice(text=EN, language="English", speaker=spk)), c)


def voxcpm():
    from voxcpm import VoxCPM
    t = time.time(); m = VoxCPM.from_pretrained("openbmb/VoxCPM2", load_denoiser=False); c = time.time() - t
    sr = m.tts_model.sample_rate
    medir("voxcpm2_design_es", lambda: (m.generate(text="(Voz masculina grave y cálida de narrador, acento de España, ritmo pausado)" + ES, cfg_value=2.0, inference_timesteps=10), sr), c)
    medir("voxcpm2_design_en", lambda: (m.generate(text="(Deep warm male storyteller voice, American accent, calm pace)" + EN, cfg_value=2.0, inference_timesteps=10), sr), c)


VARIANTES_ES = {
    "a": "Voz masculina adulta de narrador de documental, tono firme y claro, acento de España, ritmo normal y fluido, sin susurros.",
    "b": "Hombre joven de unos 25 años, voz natural y enérgica, acento castellano de España, habla con ritmo ágil como un youtuber contando una historia.",
    "c": "Locutor de radio español, voz grave, segura y neutra, dicción clara, ritmo constante y sin pausas largas.",
}


def recortar_pausas(wav, sr, max_s=0.35, thr=0.01):
    """Acorta los silencios internos a max_s segundos."""
    wav = np.asarray(wav, dtype=np.float32).squeeze()
    ventana = int(0.02 * sr)
    n = len(wav) // ventana
    activo = np.array([np.abs(wav[i*ventana:(i+1)*ventana]).max() > thr for i in range(n)])
    out, sil = [], 0
    for i in range(n):
        trozo = wav[i*ventana:(i+1)*ventana]
        if activo[i]:
            sil = 0; out.append(trozo)
        else:
            sil += ventana
            if sil <= max_s * sr:
                out.append(trozo)
    return np.concatenate(out)


def qwen_es():
    import torch
    torch.set_num_threads(os.cpu_count())
    from qwen_tts import Qwen3TTSModel
    v = os.environ["VARIANTE"]
    t = time.time(); m = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign", device_map="cpu", dtype=torch.float32); c = time.time() - t
    def fn():
        wavs, sr = m.generate_voice_design(text=ES, language="Spanish", instruct=VARIANTES_ES[v])
        return recortar_pausas(wavs[0], sr), sr
    medir(f"qwen17_es_v2_{v}", fn, c)


if __name__ == "__main__":
    mot = sys.argv[1]
    {"supertonic": supertonic, "edge": edge, "kokoro": kokoro, "qwen06": lambda: qwen("06"), "qwen17": lambda: qwen("design"), "voxcpm": voxcpm, "qwen_es": qwen_es}[mot]()
