"""Ritmo y variedad de un largo antes de renderizarlo (sin IA, sin red).

Uso: python3 motor/ritmo.py largos/lab003_es.json historias/his009_en.json ...

No bloquea el render (eso lo hace --validar): da avisos que la sesion de guiones debe corregir hasta dejar 0.
Reglas del dueno 24/11: si los largos duran mas, tienen que ser mucho mas entretenidos (mas escenas, mas variadas,
personajes y cambios de ritmo), para que la gente se quede.
"""
import collections
import json
import os
import re
import sys

PPM = {'lab': 132, 'his': 157}          # palabras por minuto medidas (Jorge y voz de HSB)
MIN_OBJ = {'lab': (14, 16), 'his': (14, 16)}   # minutos objetivo de los largos
MAX_SEG_ESCENA = {'lab': 9, 'his': 6}     # segundos como mucho en la misma escena/plano
MIN_DISTINTOS = {'lab': 7, 'his': 16}     # tipos de escena/plano distintos en el video
MAX_CUOTA = {'lab': 0.28, 'his': 0.25}    # ningun tipo puede pasar de esta parte de las escenas
SEG_CAPITULO = 150                        # un capitulo (re-gancho) cada 2,5 min como mucho


def palabras(t):
    return len(re.findall(r"[\wÀ-ÿ']+", t or ''))


def serie(g, ruta):
    if 'lineas' in g:
        return 'his'
    return 'lab' if 'beats' in g else os.path.basename(ruta)[:3]


def escenas_lab(g):
    """[(tipo, palabras)] por escena: una escena dura desde su beat con v hasta el siguiente."""
    out = []
    for b in g['beats']:
        if b.get('v') or not out:
            out.append([(b.get('v') or {}).get('tipo', '?'), 0])
        out[-1][1] += palabras(b.get('di') or b.get('texto'))
    return out


def escenas_his(g):
    """[(plano, palabras)]: los planos de una linea se reparten sus frases (aprox. a partes iguales).
    Un plano `escena` lo trocea el montaje cada ~2,4 s con otro encuadre: cuenta como varios planos de ese sitio."""
    out, sitio = [], None
    for l in g['lineas']:
        if l.get('escena'):
            sitio = None if l['escena'] == 'ninguno' else (l['escena'] or {}).get('sitio', '?')
        p = [x.get('t', '?') for x in l.get('planos', [])] or ['(sin plano)']
        w = palabras(l.get('texto'))
        for t in p:
            if t == 'escena':
                trozos = max(1, round(w / len(p) / (PPM['his'] / 60 * 2.4)))
                out += [[f'escena/{sitio}', w / len(p) / trozos] for _ in range(trozos)]
            else:
                out.append([t, w / len(p)])
    return out


def capitulos(g):
    filas = g.get('beats') or g.get('lineas') or []
    return sum(1 for f in filas if f.get('capitulo'))


def revisar(ruta):
    g = json.load(open(ruta, encoding='utf-8'))
    if g.get('formato_yt') != 'largo':
        return None, ['no es un largo (formato_yt != largo): no aplica']
    s = serie(g, ruta)
    ppm = PPM.get(s, 150)
    esc = escenas_lab(g) if s == 'lab' else escenas_his(g)
    total_w = sum(w for _, w in esc)
    minutos = total_w / ppm
    seg = [w / ppm * 60 for _, w in esc]
    tipos = [t for t, _ in esc]
    cuenta = collections.Counter(tipos)
    av = []
    lo, hi = MIN_OBJ.get(s, (14, 16))
    if minutos < lo - 0.5 or minutos > hi + 0.5:
        av.append(f'duracion estimada {minutos:.1f} min (objetivo {lo}-{hi}): unas {int(lo * ppm)}-{int(hi * ppm)} palabras')
    largas = [(i, t, x) for i, (t, x) in enumerate(zip(tipos, seg)) if x > MAX_SEG_ESCENA.get(s, 8)]
    if largas:
        ej = ', '.join(f'#{i} {t} {x:.0f}s' for i, t, x in largas[:6])
        av.append(f'{len(largas)} escenas pasan de {MAX_SEG_ESCENA.get(s)} s (partirlas o cambiar de escena): {ej}')
    seguidas = [i for i in range(2, len(tipos)) if tipos[i] == tipos[i - 1] == tipos[i - 2]]
    if seguidas:
        av.append(f'{len(seguidas)} veces el mismo tipo 3 escenas seguidas (alternar): desde la escena #{seguidas[0] - 2}')
    if len(cuenta) < MIN_DISTINTOS.get(s, 8):
        av.append(f'solo {len(cuenta)} tipos de escena distintos (minimo {MIN_DISTINTOS.get(s)}): {dict(cuenta)}')
    for t, n in cuenta.most_common(3):
        if n / max(1, len(tipos)) > MAX_CUOTA.get(s, 0.3):
            av.append(f'"{t}" es el {n / len(tipos):.0%} de las escenas (maximo {MAX_CUOTA.get(s):.0%}): sustituir parte por otros')
    caps = capitulos(g)
    if caps < minutos * 60 / SEG_CAPITULO:
        av.append(f'{caps} capitulos para {minutos:.0f} min: hace falta uno cada 2,5 min como mucho (con re-gancho al final del anterior)')
    if s == 'his':
        mus = len(g.get('musica', []))
        if mus < caps:
            av.append(f'{mus} cambios de musica para {caps} capitulos: al menos uno por capitulo')
        base = re.sub(r'_[a-z]{2}$', '', os.path.splitext(os.path.basename(ruta))[0])
        js = os.path.join(os.path.dirname(ruta), base + '.js')
        nuevos = len(re.findall(r"reg2?\('[A-Za-z0-9_]+'", open(js, encoding='utf-8').read())) if os.path.exists(js) else 0
        con_escenas = len({(l['escena'] or {}).get('sitio') for l in g['lineas'] if isinstance(l.get('escena'), dict)}) >= 8
        if nuevos < (1 if con_escenas else 3):
            av.append(f'{nuevos} planos nuevos en {os.path.basename(js)} (minimo {1 if con_escenas else 3}: escenarios, objetos o personajes que la biblioteca no tiene)')
        reparto = len(g.get('reparto', {}))
        if reparto < 3:
            av.append(f'{reparto} personajes en reparto (minimo 3 con nombre y objetivo propio)')
        # escenas de verdad (25/11): sitios completos con rotulo, marcador que cambia, detalles y pregunta final
        escs = [l['escena'] for l in g['lineas'] if isinstance(l.get('escena'), dict)]
        sitios = {(e.get('sitio'), e.get('hora', 'dia')) for e in escs}
        if len(sitios) < 8:
            av.append(f'{len(sitios)} escenas distintas (sitio+hora; minimo 8): cambiar de sitio cada 30-90 s con "escena"')
        sin_rot = sum(1 for e in escs if not e.get('rotulo'))
        if sin_rot:
            av.append(f'{sin_rot} escenas sin "rotulo" ("SITIO · HORA" al entrar)')
        marc = len({l.get('marcador') for l in g['lineas'] if l.get('marcador')})
        if marc < minutos / 1.5:
            av.append(f'{marc} valores de "marcador" para {minutos:.0f} min: que cambie cada 30-60 s (la apuesta que sube o baja)')
        ins = sum(1 for l in g['lineas'] for x in l.get('planos', []) if x.get('t') == 'inserto')
        if ins < minutos / 1.5:
            av.append(f'{ins} planos "inserto" (movil, factura, carta, billetes, reloj, llaves): uno cada ~1 min')
        if '?' not in (g['lineas'][-1].get('texto') or '') if g['lineas'] else True:
            av.append('la ultima linea no es una pregunta al espectador ("Would you have forgiven him?"): sube los comentarios')
    else:
        rot = sum(1 for b in g['beats'] if b.get('rotulo'))
        if rot < caps:
            av.append(f'{rot} "rotulo" para {caps} capitulos: uno al menos en la frase que abre cada capitulo ("Sahara · año 2150")')
        huds = len({(b.get('hud') or {}).get('txt') for b in g['beats'] if b.get('hud')})
        if huds < minutos / 1.5:
            av.append(f'{huds} valores de "hud" para {minutos:.0f} min: que cambie cada 30-60 s (salta y suena al cambiar)')
    if not g.get('promesa'):
        av.append('falta "promesa": 1 frase de lo que el espectador vera al final (se dice antes del segundo 30 y se cumple al final)')
    if not g.get('paquete'):
        av.append('falta "paquete": {"titulo": ..., "miniatura": "que se ve y que pone"} decidido ANTES del guion')
    datos = {'serie': s, 'minutos': round(minutos, 1), 'escenas': len(esc), 'seg_medio_escena': round(sum(seg) / max(1, len(seg)), 1),
             'tipos_distintos': len(cuenta), 'capitulos': caps}
    return datos, av


if __name__ == '__main__':
    malos = 0
    for r in sys.argv[1:]:
        try:
            d, av = revisar(r)
        except Exception as e:  # json roto: lo dice --validar
            d, av = None, [f'no se pudo leer: {e}']
        print(r, d or '')
        for a in av:
            print('  - aviso:', a)
        print('  OK: ritmo y variedad bien' if not av else f'  {len(av)} avisos: corregir antes de dar el guion por terminado')
        malos += bool(av)
    sys.exit(0)
