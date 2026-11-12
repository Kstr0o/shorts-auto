"""Prueba a oido las reescrituras experimentales de motor/pronunciacion.json (clave _es_rr_experimental).

Para cada palabra genera la misma frase dos veces con Chatterbox: A tal cual y B con la reescritura,
y lo junta todo en un video con tarjetas para escucharlo seguido. Ademas escucho cada toma con whisper
y apunto el parecido con el texto, para ver si la reescritura hace patinar al motor.

Uso: python3 motor/probar_pronuncia.py salida [palabra1,palabra2,...]
"""
import glob
import json
import os
import re
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import voz  # noqa: E402

RAIZ= os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTE= os.path.join(RAIZ, 'assets', 'fuentes', 'Anton-Regular.ttf')


def _frases_es():
    # saco las frases en espanol de los guiones para probar cada palabra en su contexto real
    res= []

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == 'es' and isinstance(v, str):
                    res.append(v)
                else:
                    walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    for f in sorted(glob.glob(os.path.join(RAIZ, 'episodios', '*.json'))):
        walk(json.load(open(f, encoding='utf-8')))
    return res


def frase_para(palabra, frases):
    for fr in frases:
        if re.search(rf'\b{re.escape(palabra)}\b', fr, flags=re.IGNORECASE):
            return fr.strip()
    return f'Mira, {palabra}. Otra vez {palabra}.'


def tarjeta(titulo, sub, texto, png):
    img= Image.new('RGB', (1080, 1920), '#16161c')
    d= ImageDraw.Draw(img)
    d.text((540, 700), titulo, font=ImageFont.truetype(FUENTE, 300), fill='#ffd60a', anchor='mm')
    f= ImageFont.truetype(FUENTE, 80)
    while f.getlength(sub) > 980:
        f= ImageFont.truetype(FUENTE, f.size - 4)
    d.text((540, 1000), sub, font=f, fill='#ffffff', anchor='mm')
    f= ImageFont.truetype(FUENTE, 46)
    y, linea= 1200, ''
    for w in texto.split():
        if f.getlength(linea + ' ' + w) > 960:
            d.text((540, y), linea.strip(), font=f, fill='#bdbdc7', anchor='mm')
            y+= 64
            linea= ''
        linea+= ' ' + w
    if linea.strip():
        d.text((540, y), linea.strip(), font=f, fill='#bdbdc7', anchor='mm')
    img.save(png)


def main(salida, solo=None):
    os.makedirs(salida, exist_ok=True)
    datos= json.load(open(os.path.join(RAIZ, 'motor', 'pronunciacion.json'), encoding='utf-8'))
    exp= {k: v for k, v in datos.get('_es_rr_experimental', {}).items() if not k.startswith('_')}
    if solo:
        exp= {k: v for k, v in exp.items() if k in solo}
    frases= _frases_es()
    partes, informe= [], []
    for n, (palabra, reescrita) in enumerate(exp.items(), 1):
        frase= frase_para(palabra, frases)
        variante= re.sub(rf'\b{re.escape(palabra)}\b', reescrita, frase, flags=re.IGNORECASE)
        for letra, texto in (('A', frase), ('B', variante)):
            wav= os.path.join(salida, f'_{n}{letra}.wav')
            try:
                dur, _= voz.sintetizar_chatter([texto], 'es', wav)
            except voz.VozFallo as e:
                print(f'{palabra} {letra}: fallo {e}', flush=True)
                continue
            marcas= voz._marcas_whisper(wav, 'es')
            oido= ' '.join(x['p'] for x in marcas)
            informe.append({'n': n, 'palabra': palabra, 'toma': letra, 'texto': texto, 'oido': oido, 'segundos': round(dur, 2)})
            png= os.path.join(salida, f'_{n}{letra}.png')
            tarjeta(f'{n}{letra}', ('normal' if letra == 'A' else 'reforzada') + f': {palabra}', frase, png)
            mp4= os.path.join(salida, f'_{n}{letra}.mp4')
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-i', png, '-i', wav, '-c:v', 'libx264', '-tune', 'stillimage',
                            '-r', '10', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-ar', '44100', '-ac', '1', '-shortest', mp4], check=True)
            partes.append(mp4)
            print(f'{n}{letra} {palabra}: oido "{oido}"', flush=True)
    if not partes:
        print('nada que probar', flush=True)
        return
    lista= os.path.join(salida, '_lista.txt')
    open(lista, 'w').write(''.join(f"file '{os.path.abspath(p)}'\n" for p in partes))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lista, '-c:v', 'libx264', '-r', '10', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '160k', os.path.join(salida, 'pronuncia_es.mp4')], check=True)
    json.dump(informe, open(os.path.join(salida, 'pronuncia_es.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2].split(',') if len(sys.argv) > 2 and sys.argv[2] else None)
