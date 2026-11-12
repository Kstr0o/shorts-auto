"""Publica el siguiente video aprobado de cada serie (uno al dia por canal).

cola.json lleva, en orden, los episodios con visto bueno; los mp4 estan en la rama listos.
estado.json lleva los que ya se subieron. No genera nada: solo sube lo ya aprobado.
"""
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

RAIZ= os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERIES= {'ep': 'TONI', 'ysi': 'YSI'}


def main():
    cola= json.load(open(os.path.join(RAIZ, 'cola.json')))
    ruta_estado= os.path.join(RAIZ, 'estado.json')
    estado= json.load(open(ruta_estado))
    for pref, canal in SERIES.items():
        hechos= estado.setdefault(pref, [])
        pendientes= [e for e in cola if e.startswith(pref) and e + '.json' not in hechos]
        if not pendientes:
            print(f'{pref}: no hay episodios aprobados en la cola')
            continue
        ep= pendientes[0]
        import subir
        for idi in ('es', 'en'):
            mp4= os.path.join(RAIZ, 'listos', f'{ep}_{idi}.mp4')
            # espanol sale al subir (13:00 de Madrid); ingles queda programado para las 15:00 de Madrid (9:00 en la costa este)
            hora= None
            if idi == 'en' and os.environ.get('YT_PRIVACIDAD') == 'public':
                ahora= datetime.datetime.now(datetime.timezone.utc)
                cuando= ahora.replace(hour=14, minute=0, second=0, microsecond=0)
                hora= cuando.strftime('%Y-%m-%dT%H:%M:%SZ') if cuando > ahora else None
            subir.subir(mp4, mp4.replace('.mp4', '.json'), f'{canal}_{idi.upper()}', hora)
        hechos.append(ep + '.json')
        # guardo tras cada serie para no repetir una subida si falla la siguiente
        json.dump(estado, open(ruta_estado, 'w'), indent=1)
        print(f'{pref}: subido {ep}, quedan {len(pendientes) - 1} en la cola')


if __name__ == '__main__':
    main()
