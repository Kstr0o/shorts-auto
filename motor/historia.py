"""Validacion de los guiones de Historias Sin Blanca (historias/hisNNN_en.json) sin necesitar el estudio privado.

  python3 motor/historia.py historias/his008_en.json [historias/his008_s1_en.json ...]

El render lo hace el estudio privado (repo estudio-animacion, montar/montar.py) desde lote_semanal.yml.
"""
import json
import os
import re
import sys

PLANOS = ['alarm', 'alley', 'arm', 'brass', 'bus', 'cafe', 'call', 'countdown', 'cup', 'face', 'lottery', 'memory', 'montage',
          'night', 'notes', 'outro', 'phone', 'reset', 'rules', 'shopext', 'sunset', 'title', 'bed3d', 'shop3d', 'street3d']
MOODS = ['tension', 'mystery', 'playful', 'sad', 'epic', 'calm', 'happy', 'dark']


def extra_de(ruta):
    """historias/his008_s1_en.json -> historias/his008.js (planos nuevos de esa historia, si los hay)."""
    base = re.sub(r'(_s\d+)?_[a-z]{2}\.json$', '.js', ruta)
    return base if os.path.exists(base) else None


def validar(ruta, extra=None):
    try:
        g = json.load(open(ruta, encoding='utf-8'))
    except Exception as e:
        return [f'json roto: {e}']
    mal = [f'falta {k}' for k in ('id', 'titulo', 'descripcion', 'tags', 'lineas') if not g.get(k)]
    if mal:
        return mal
    extra = extra or extra_de(ruta)
    ok = set(PLANOS) | set(re.findall(r"reg2?\('([A-Za-z0-9_]+)'", open(extra).read()) if extra else [])
    for i, ln in enumerate(g['lineas']):
        if not ln.get('texto'):
            mal.append(f'linea {i}: sin texto')
        if not ln.get('planos'):
            mal.append(f'linea {i}: sin planos')
        for p in ln.get('planos', []):
            if p.get('t') not in ok:
                mal.append(f'linea {i}: plano desconocido {p.get("t")}')
    for m in g.get('musica', []):
        if len(m) != 3 or m[1] not in MOODS:
            mal.append(f'musica: {m} (formato [linea, mood, intensidad]; moods {MOODS})')
    if extra:
        import shutil
        import subprocess
        if shutil.which('node'):  # un error de sintaxis en los planos nuevos tiraria el render entero
            r = subprocess.run(['node', '--input-type=module', '--check'], stdin=open(extra), capture_output=True, text=True)
            if r.returncode:
                mal.append(f'{os.path.basename(extra)}: error de JavaScript: {' '.join(r.stderr.strip().splitlines()[:4])[:300]}')
    palabras = sum(len(ln['texto'].split()) for ln in g['lineas'])
    if g.get('formato_yt', 'largo') == 'largo' and not 1300 <= palabras <= 1900:
        mal.append(f'largo de {palabras} palabras (hacen falta 1300-1900; 1.389 dieron 8:50, para 11 min unas 1.700)')
    return mal


if __name__ == '__main__':
    fallos = {r: validar(r) for r in sys.argv[1:]}
    for r, m in fallos.items():
        print(r, 'OK' if not m else '\n  - ' + '\n  - '.join(m))
    sys.exit(1 if any(fallos.values()) else 0)
