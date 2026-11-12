"""Elige el siguiente episodio sin publicar de cada serie, lo renderiza en es/en y lo sube.

Lleva la cuenta en estado.json. Con SOLO_RENDER=1 no sube nada (deja los mp4 en salida/).
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render

RAIZ= os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERIES= {'ep': 'TONI', 'ysi': 'YSI'}  # prefijo del archivo -> canal


def main():
    ruta_estado= os.path.join(RAIZ, 'estado.json')
    estado= json.load(open(ruta_estado)) if os.path.exists(ruta_estado) else {}
    salida= os.path.join(RAIZ, 'salida')
    solo_render= os.environ.get('SOLO_RENDER') == '1'
    for pref, canal in SERIES.items():
        hechos= set(estado.get(pref, []))
        cola= sorted(f for f in glob.glob(os.path.join(RAIZ, 'episodios', f'{pref}[0-9]*.json'))
                     if os.path.basename(f) not in hechos)
        if not cola:
            print(f'{pref}: no quedan episodios en la cola')
            continue
        if solo_render and os.environ.get('TODOS') == '1':
            for ep in cola:
                if os.environ.get('SOLO_EP') and os.environ['SOLO_EP'] not in os.path.basename(ep):
                    continue
                for idi in os.environ.get('IDIOMAS', 'es,en').split(','):
                    render.render(ep, salida, idi.strip())
            continue
        ep= cola[0]
        ok= True
        for idi in ('es', 'en'):
            mp4= render.render(ep, salida, idi)
            if solo_render:
                continue
            if not os.environ.get(f'YT_TOKEN_{canal}_{idi.upper()}'):
                print(f'falta YT_TOKEN_{canal}_{idi.upper()}: no subo')
                ok= False
                continue
            import subir
            subir.subir(mp4, mp4.replace('.mp4', '.json'), f'{canal}_{idi.upper()}')
        if ok and not solo_render:
            estado.setdefault(pref, []).append(os.path.basename(ep))
    json.dump(estado, open(ruta_estado, 'w'), indent=1)


if __name__ == '__main__':
    main()
