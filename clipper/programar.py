"""Programa los clips del canal de clips (Daily Streamer Clips) igual que los otros canales: subida por API con publishAt.

Se ejecuta en el portatil justo despues de editar los clips (tarea de las 22:00). Sube cada clip ya PROGRAMADO, asi que
YouTube lo publica solo a su hora aunque el portatil este apagado. Los clips nunca pasan por el repo ni por Actions.

  python clipper/programar.py trabajo/<id>/clips [otra/carpeta ...] [--prueba] [--simular]

  --prueba   sube solo el primer clip pendiente en PRIVADO y sin fecha (para revisarlo) y para
  --simular  solo dice que hora le tocaria a cada clip, sin subir nada

Huecos: HORAS_CLIPS (hora de Madrid, por defecto 8 al dia de 12:00 a 22:30), como mucho DIAS_CLIPS dias por delante (3)
y SUBIDAS_CLIPS subidas por ejecucion (10, para no gastar la cuota de los otros canales). Lo que no quepa se queda
pendiente para la noche siguiente. Lo ya subido se apunta en ESTADO_CLIPS (por defecto trabajo/clips_programados.json,
fuera del repo) con el enlace, la hora y la campana, para mandar luego el enlace a Content Rewards.

Claves (no se imprimen): YT_TOKEN_CLIPS, YT_CLIENT_ID, YT_CLIENT_SECRET en el entorno, o en archivos locales:
  TOKEN_CLIPS_ARCHIVO (texto con el refresh token) y CLIENT_SECRET_ARCHIVO (client_secret.json de Google).
"""
import argparse
import datetime as dt
import glob
import json
import os
import sys
from zoneinfo import ZoneInfo

AQUI= os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..', 'motor'))
MAD= ZoneInfo('Europe/Madrid')
UTC= dt.timezone.utc
CANAL= 'CLIPS'
HORAS= os.environ.get('HORAS_CLIPS', '12:00,13:30,15:00,16:30,18:00,19:30,21:00,22:30').split(',')
DIAS= int(os.environ.get('DIAS_CLIPS', '3'))
MAX_SUBIDAS= int(os.environ.get('SUBIDAS_CLIPS', '10'))
ESTADO= os.environ.get('ESTADO_CLIPS', os.path.join(AQUI, '..', 'trabajo', 'clips_programados.json'))
MARGEN= dt.timedelta(minutes=45)  # YouTube necesita procesar el video antes de su hora


def claves():
    # las cargo de los archivos locales sin mostrarlas
    if not os.environ.get('YT_TOKEN_CLIPS') and os.environ.get('TOKEN_CLIPS_ARCHIVO'):
        os.environ['YT_TOKEN_CLIPS']= open(os.environ['TOKEN_CLIPS_ARCHIVO'], encoding='utf-8').read().strip()
    if not os.environ.get('YT_CLIENT_ID') and os.environ.get('CLIENT_SECRET_ARCHIVO'):
        c= json.load(open(os.environ['CLIENT_SECRET_ARCHIVO'], encoding='utf-8'))
        c= c.get('installed') or c.get('web') or c
        os.environ['YT_CLIENT_ID'], os.environ['YT_CLIENT_SECRET']= c['client_id'], c['client_secret']
    falta= [v for v in ('YT_TOKEN_CLIPS', 'YT_CLIENT_ID', 'YT_CLIENT_SECRET') if not os.environ.get(v)]
    if falta:
        sys.exit('faltan claves: ' + ', '.join(falta))


def huecos_libres(ocupadas, ahora):
    # huecos de los proximos DIAS dias que no esten ya cogidos, en orden
    hoy= ahora.astimezone(MAD).date()
    libres= []
    for d in range(DIAS + 1):
        dia= hoy + dt.timedelta(days=d)
        for h in HORAS:
            hh, mm= (int(x) for x in h.strip().split(':'))
            t= dt.datetime(dia.year, dia.month, dia.day, hh, mm, tzinfo=MAD).astimezone(UTC)
            if t > ahora + MARGEN and t.strftime('%Y-%m-%dT%H:%M:%SZ') not in ocupadas:
                libres.append(t)
    return libres


def main():
    ap= argparse.ArgumentParser()
    ap.add_argument('carpetas', nargs='+')
    ap.add_argument('--prueba', action='store_true')
    ap.add_argument('--simular', action='store_true')
    a= ap.parse_args()

    est= json.load(open(ESTADO, encoding='utf-8')) if os.path.exists(ESTADO) else {'clips': []}
    hechos= {c['archivo'] for c in est['clips']}
    pendientes= [m for c in a.carpetas for m in sorted(glob.glob(os.path.join(c, '*.mp4')))
                 if os.path.abspath(m) not in hechos and os.path.exists(m[:-4] + '.json')]
    if not pendientes:
        print('no hay clips nuevos'); return
    ahora= dt.datetime.now(UTC)
    libres= huecos_libres({c['publishAt'] for c in est['clips'] if c.get('publishAt')}, ahora)
    if not a.simular:
        claves()
        import subir as s

    def apuntar(mp4, vid, cuando):
        meta= json.load(open(mp4[:-4] + '.json', encoding='utf-8'))
        est['clips'].append({'archivo': os.path.abspath(mp4), 'id': vid, 'url': f'https://youtube.com/shorts/{vid}',
                             'publishAt': cuando, 'titulo': meta.get('titulo'), 'campana': meta.get('campana'),
                             'fuente': meta.get('fuente'), 'enlace_enviado': False})
        os.makedirs(os.path.dirname(os.path.abspath(ESTADO)), exist_ok=True)
        json.dump(est, open(ESTADO, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    if a.prueba:
        mp4= pendientes[0]
        if a.simular:
            print('prueba (privado, sin fecha):', mp4); return
        os.environ['YT_PRIVACIDAD']= 'private'
        apuntar(mp4, s.subir(mp4, mp4[:-4] + '.json', CANAL), None)
        print('subido en PRIVADO para revisarlo; cuando este bien, quitar --prueba'); return

    subidos= 0
    for mp4, cuando in zip(pendientes, libres):
        if subidos >= MAX_SUBIDAS:
            break
        hora= cuando.strftime('%Y-%m-%dT%H:%M:%SZ')
        print(f'{os.path.basename(mp4)} -> {cuando.astimezone(MAD):%a %d/%m %H:%M} Madrid')
        if a.simular:
            subidos+= 1
            continue
        try:
            apuntar(mp4, s.subir(mp4, mp4[:-4] + '.json', CANAL, hora), hora)
            subidos+= 1
        except Exception as e:
            print(f'  FALLO {type(e).__name__}: {str(e)[:300]}')
            if 'quota' in str(e).lower() or 'uploadLimitExceeded' in str(e):
                break  # sin cuota o tope de subidas del canal: lo demas queda para manana
    resto= len(pendientes) - subidos
    print(f'programados {subidos}; quedan {resto} para la siguiente noche' + (' (simulado)' if a.simular else ''))


if __name__ == '__main__':
    main()
