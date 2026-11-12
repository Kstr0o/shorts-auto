"""Genera un video por idioma con la misma frase leida por varias voces gratuitas, numeradas.

Uso: python3 motor/muestra_voces.py salida
"""
import asyncio
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

RAIZ= os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTE= os.path.join(RAIZ, 'assets', 'fuentes', 'Anton-Regular.ttf')

TEXTO= {
    'es': 'Es día veintiocho. Abres la app del banco. Cuatro euros. Con once céntimos. Te escribe tu colega. ¿Cenamos esta noche? '
          'Dices que sí. Tú siempre dices que sí. En el restaurante, estudias la carta como si fuera un examen final.',
}
# (motor, voz, etiqueta, extra). Solo voces nativas en espanol; las que el servicio no tenga se saltan solas
CANDIDATAS= {
    'es': [('piper', 'es_ES-davefx-medium', 'Dave (España)', ''),
           ('piper', 'es_ES-sharvard-medium', 'Sharvard hombre (España)', '0'),
           ('piper', 'es_ES-sharvard-medium', 'Sharvard mujer (España)', '1'),
           ('chatter', 'base', 'Motor expresivo, voz base', '|0.5|0.5'),
           ('chatter', 'dave', 'Motor expresivo, acento de España', 'es_ES-davefx-medium|0.5|0.3'),
           ('chatter', 'dave-vivo', 'Motor expresivo, España, más vivo', 'es_ES-davefx-medium|0.75|0.3'),
           ('chatter', 'shar', 'Motor expresivo, España, otra voz', 'es_ES-sharvard-medium:0|0.6|0.3')],
}
DIR_PIPER= os.environ.get('DIR_PIPER', 'voces_piper')
_chatter= {}


def _piper(voz, speaker, texto, wav):
    cmd= ['python3', '-m', 'piper', '-m', os.path.join(DIR_PIPER, voz + '.onnx'), '-f', wav + '.p.wav']
    if speaker:
        cmd+= ['--speaker', speaker]
    subprocess.run(cmd, input=texto.encode(), check=True, capture_output=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', wav + '.p.wav', '-ac', '1', '-ar', '44100', wav], check=True)


def _chatterbox(extra, texto, wav):
    import torchaudio
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    if 'm' not in _chatter:
        _chatter['m']= ChatterboxMultilingualTTS.from_pretrained(device='cpu')
    m= _chatter['m']
    ref, exag, cfg= extra.split('|')
    kw= {'exaggeration': float(exag), 'cfg_weight': float(cfg)}
    if ref:
        # la voz de referencia la saco de una voz libre de Piper con acento de Espana
        voz, _, spk= ref.partition(':')
        refwav= wav + '.ref.wav'
        _piper(voz, spk, 'Hola, qué tal. Hoy te voy a contar una historia que no te vas a creer. Empieza un martes cualquiera, a las ocho de la mañana.', refwav)
        kw['audio_prompt_path']= refwav
    # frase a frase en grupos cortos para que no se desvie
    import re
    import torch
    frases= re.findall(r'[^.?!]+[.?!]+', texto)
    grupos, act= [], ''
    for f in frases:
        if len(act) + len(f) > 120 and act:
            grupos.append(act.strip())
            act= ''
        act+= f
    if act.strip():
        grupos.append(act.strip())
    trozos= [m.generate(g, language_id='es', **kw) for g in grupos]
    torchaudio.save(wav + '.c.wav', torch.cat(trozos, dim=1), m.sr)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', wav + '.c.wav', '-ac', '1', '-ar', '44100', wav], check=True)


_kokoro= {}


async def _edge(texto, voz, rate, mp3):
    import edge_tts
    await edge_tts.Communicate(texto, voz, rate=rate).save(mp3)


def sintetizar(motor, voz, extra, texto, wav):
    if motor in ('piper', 'chatter'):
        try:
            _piper(voz, extra, texto, wav) if motor == 'piper' else _chatterbox(extra, texto, wav)
            return True
        except Exception as e:
            print(f'  {motor} {voz}: {e!r} {getattr(e, "stderr", b"")[-400:]}', flush=True)
            return False
    if motor == 'edge':
        mp3= wav + '.mp3'
        for intento in range(3):
            try:
                asyncio.run(_edge(texto, voz, extra, mp3))
                if os.path.getsize(mp3) > 1000:
                    break
            except Exception as e:
                print(f'  {voz} intento {intento}: {e}', flush=True)
        else:
            return False
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', mp3, '-ac', '1', '-ar', '44100', wav], check=True)
        return True
    try:
        import numpy as np
        import soundfile as sf
        from kokoro import KPipeline
        if extra not in _kokoro:
            _kokoro[extra]= KPipeline(lang_code=extra)
        trozos= [a for _, _, a in _kokoro[extra](texto, voice=voz, speed=1.05)]
        sf.write(wav + '.k.wav', np.concatenate([np.asarray(t) for t in trozos]), 24000)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', wav + '.k.wav', '-ac', '1', '-ar', '44100', wav], check=True)
        return True
    except Exception as e:
        print(f'  kokoro {voz}: {e}', flush=True)
        return False


def tarjeta(n, etiqueta, idioma, png):
    img= Image.new('RGB', (1080, 1920), '#16161c')
    d= ImageDraw.Draw(img)
    d.text((540, 620), ('VOZ' if idioma == 'es' else 'VOICE'), font=ImageFont.truetype(FUENTE, 150), fill='#ffffff', anchor='mm')
    d.text((540, 930), str(n), font=ImageFont.truetype(FUENTE, 460), fill='#ffd60a', anchor='mm')
    f= ImageFont.truetype(FUENTE, 64)
    while f.getlength(etiqueta) > 980:
        f= ImageFont.truetype(FUENTE, f.size - 4)
    d.text((540, 1280), etiqueta, font=f, fill='#bdbdc7', anchor='mm')
    img.save(png)


def main(salida):
    os.makedirs(salida, exist_ok=True)
    for idioma, cands in CANDIDATAS.items():
        partes, n= [], 0
        for motor, voz, etiqueta, extra in cands:
            wav= os.path.join(salida, f'_{idioma}_{len(partes)}_{voz}.wav')
            if not sintetizar(motor, voz, extra, TEXTO[idioma], wav):
                print(f'{idioma} {voz}: NO disponible', flush=True)
                continue
            n+= 1
            png= os.path.join(salida, f'_{idioma}_{n}.png')
            tarjeta(n, etiqueta, idioma, png)
            mp4= os.path.join(salida, f'_{idioma}_{n}.mp4')
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-i', png, '-i', wav, '-c:v', 'libx264', '-tune', 'stillimage',
                            '-r', '10', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-ar', '44100', '-ac', '1', '-shortest', mp4], check=True)
            partes.append(mp4)
            print(f'{idioma} VOZ {n}: {motor} {voz}', flush=True)
        lista= os.path.join(salida, f'_{idioma}.txt')
        open(lista, 'w').write(''.join(f"file '{os.path.abspath(p)}'\n" for p in partes))
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lista, '-c:v', 'libx264', '-r', '10', '-pix_fmt', 'yuv420p',
                        '-c:a', 'aac', '-b:a', '160k', os.path.join(salida, f'voces_{idioma}.mp4')], check=True)


if __name__ == '__main__':
    main(sys.argv[1])
