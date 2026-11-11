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
    'es': 'Este es Toni. Tiene veintitrés años y cero euros en el banco. Y hoy ha decidido que, en cien días, va a ser millonario. '
          'Su madre le dio otra opción: buscar trabajo. Toni dijo que no.',
    'en': "This is Toni. He's twenty-three and has zero dollars in the bank. And today he decided that, in a hundred days, "
          "he'll be a millionaire. His mom gave him another option: get a job. Toni said no.",
}
# (motor, voz, etiqueta, extra)
CANDIDATAS= {
    'es': [('edge', 'es-ES-AlvaroNeural', 'Álvaro (España), la de ahora pero más lenta', '+4%'),
           ('edge', 'es-ES-XimenaNeural', 'Ximena (España)', '+4%'),
           ('edge', 'es-ES-ElviraNeural', 'Elvira (España)', '+4%'),
           ('edge', 'es-MX-JorgeNeural', 'Jorge (México)', '+4%'),
           ('edge', 'es-MX-DaliaNeural', 'Dalia (México)', '+4%'),
           ('edge', 'en-US-AndrewMultilingualNeural', 'Andrew multilingüe', '+4%'),
           ('edge', 'en-US-BrianMultilingualNeural', 'Brian multilingüe', '+4%'),
           ('edge', 'en-US-AvaMultilingualNeural', 'Ava multilingüe', '+4%'),
           ('edge', 'fr-FR-VivienneMultilingualNeural', 'Vivienne multilingüe', '+4%'),
           ('kokoro', 'em_alex', 'Kokoro Alex', 'e'),
           ('kokoro', 'ef_dora', 'Kokoro Dora', 'e'),
           ('kokoro', 'em_santa', 'Kokoro Santa', 'e')],
    'en': [('edge', 'en-US-GuyNeural', 'Guy, current one but slower', '+4%'),
           ('edge', 'en-US-AndrewMultilingualNeural', 'Andrew multilingual', '+4%'),
           ('edge', 'en-US-BrianMultilingualNeural', 'Brian multilingual', '+4%'),
           ('edge', 'en-US-AvaMultilingualNeural', 'Ava multilingual', '+4%'),
           ('edge', 'en-US-EmmaMultilingualNeural', 'Emma multilingual', '+4%'),
           ('edge', 'en-US-ChristopherNeural', 'Christopher', '+4%'),
           ('edge', 'en-GB-RyanNeural', 'Ryan (UK)', '+4%'),
           ('kokoro', 'am_michael', 'Kokoro Michael', 'a'),
           ('kokoro', 'am_fenrir', 'Kokoro Fenrir', 'a'),
           ('kokoro', 'af_heart', 'Kokoro Heart', 'a'),
           ('kokoro', 'am_puck', 'Kokoro Puck', 'a')],
}
_kokoro= {}


async def _edge(texto, voz, rate, mp3):
    import edge_tts
    await edge_tts.Communicate(texto, voz, rate=rate).save(mp3)


def sintetizar(motor, voz, extra, texto, wav):
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
            wav= os.path.join(salida, f'_{idioma}_{voz}.wav')
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
