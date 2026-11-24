"""Revisar titulo + cartel (texto de portada) + descripcion ANTES de escribir el guion entero. Sin IA.

Uso (sesion de guiones del martes):
  python3 motor/titulos.py titulos.txt [--cartel "TEXTO"] [--busqueda "palabras"]   10 titulos, uno por linea -> ranking
  python3 motor/titulos.py --titulo "..." [--cartel "..."] [--busqueda "..."]
  python3 motor/titulos.py guion episodios/ysi020.json [--busqueda "..."]           titulo, cartel y descripcion de un guion

Ideas de youtube-agent-skill (yt-package y yt-seo, MIT, Jake Schincariol), reescritas para espanol/ingles y Shorts:
- Titulo y cartel son UNA pieza: el cartel no repite las palabras del titulo (misma promesa, otras palabras).
- 60 caracteres: corte en la busqueda de escritorio; 40: lo que se ve en el movil. Se avisa de los dos.
- Un numero, un nombre o una fecha ganan a cualquier adjetivo. Mas de 2 palabras en MAYUSCULAS parece spam.
- Cartel: 3-4 palabras como mucho (a tamano de feed una mas es una mancha).
- Prueba de busqueda (yt-seo): las palabras de la busqueda (la de originalidad o el autocompletado) tienen que estar en el
  titulo o en las 2 primeras lineas de la descripcion, que son lo unico que se lee y el fragmento de la busqueda.
- 1-2 hashtags (regla del dueno 20/11), sin contar #shorts.
"""
import json
import re
import sys
import unicodedata

ESCRITORIO, MOVIL, MAXIMO = 60, 40, 100
VAGO = {'increible', 'brutal', 'loco', 'locura', 'enorme', 'epico', 'definitivo', 'perfecto',
        'amazing', 'incredible', 'insane', 'crazy', 'huge', 'massive', 'ultimate', 'best', 'secret', 'epic', 'perfect'}
VACIAS = {'el', 'la', 'los', 'las', 'un', 'una', 'de', 'del', 'en', 'y', 'o', 'a', 'que', 'si', 'como', 'cuanto', 'cuantos', 'tu', 'te', 'se',
          'por', 'con', 'para', 'es', 'lo', 'al', 'the', 'a', 'an', 'of', 'for', 'to', 'in', 'on', 'and', 'or', 'is',
          'are', 'at', 'by', 'from', 'with', 'your', 'you', 'my', 'i', 'this', 'that', 'it', 'how', 'what', 'why', 'if', 'shorts'}


def palabras(t):
    t = unicodedata.normalize('NFKD', re.sub(r'#\w+', ' ', t.lower()))
    t = ''.join(c for c in t if not unicodedata.combining(c))  # sin tildes: apagón = apagon
    return re.findall(r"[a-z0-9ñ']+", t)


def raiz(w):
    return w[:-2] if len(w) > 4 and w.endswith('es') else w[:-1] if len(w) > 3 and w.endswith('s') else w


def revisar(titulo, cartel=None, busqueda=None, descripcion=None):
    t = titulo.strip()
    limpio = re.sub(r'\s*#shorts\b', '', t, flags=re.I).strip()
    n = len(limpio)
    mal, bien = [], []
    if n > MAXIMO:
        mal.append(('largo', f'{n} caracteres: YouTube corta a {MAXIMO}'))
    elif n > ESCRITORIO:
        mal.append(('largo', f'{n} caracteres: la busqueda de escritorio corta cerca de {ESCRITORIO}'))
    else:
        bien.append(f'{n} caracteres, dentro de los {ESCRITORIO}')
    if n > MOVIL + 3:
        mal.append(('movil', f'en el movil se ve "{limpio[:MOVIL].rsplit(" ", 1)[0]}...": que el tema siga ahi'))
    mayus = [w for w in t.split() if len(w) > 2 and w.isupper() and not w.startswith('#')]
    if len(mayus) > 2:
        mal.append(('gritos', f'{len(mayus)} palabras en mayusculas: 2 como mucho'))
    vagas = sorted({w for w in palabras(t) if w in VAGO})
    if vagas:
        mal.append(('vago', ', '.join(vagas) + ': cambialo por un numero, un nombre o una fecha'))
    if re.search(r'\d', limpio):
        bien.append('lleva una cifra')
    elif not any(w[:1].isupper() for w in limpio.split()[1:]):
        mal.append(('sin-cifra', 'sin numero, fecha ni nombre: es el arreglo mas fiable'))
    if limpio.rstrip(' ' + ''.join(c for c in limpio if ord(c) > 0x2000)).endswith('?'):
        bien.append('pregunta abierta')
    if not [w for w in palabras(limpio)[:3] if w not in VACIAS]:
        mal.append(('delante', 'las 3 primeras palabras son relleno: adelanta el tema'))
    tags = [h for h in re.findall(r'#\w+', t + ' ' + (descripcion or '')) if h.lower() != '#shorts']
    if len(set(h.lower() for h in tags)) > 2:
        mal.append(('hashtags', f'{len(set(tags))} hashtags (sin contar #shorts): 1-2 como mucho'))
    if cartel:
        comunes = {raiz(w) for w in palabras(t) if w not in VACIAS} & {raiz(w) for w in palabras(cartel) if w not in VACIAS}
        if comunes:
            mal.append(('repite', f'el cartel repite el titulo ({", ".join(sorted(comunes))}): que diga lo que el titulo no dice'))
        else:
            bien.append('cartel y titulo con palabras distintas')
        if len(palabras(cartel)) > 4:
            mal.append(('cartel-largo', f'{len(palabras(cartel))} palabras en el cartel: 3-4 como mucho'))
    if busqueda:
        arriba = t + ' ' + ' '.join((descripcion or '').splitlines()[:2])
        faltan = [w for w in palabras(busqueda) if w not in VACIAS and raiz(w) not in {raiz(x) for x in palabras(arriba)}]
        if faltan:
            mal.append(('busqueda', f'faltan {", ".join(faltan)} de la busqueda en el titulo o en las 2 primeras lineas'))
        else:
            bien.append('pasa la prueba de busqueda')
    nota = max(0, min(100, 100 - 14 * len(mal) + 4 * len(bien)))
    return {'titulo': t, 'caracteres': n, 'nota': nota, 'mal': mal, 'bien': bien}


def imprimir(r):
    print(f'\n  "{r["titulo"]}"\n  {r["caracteres"]} caracteres   nota {r["nota"]}/100')
    for k, m in r['mal']:
        print(f'    x  {k:<12} {m}')
    for m in r['bien']:
        print(f'    ok              {m}')


def arg(a, k):
    return a[a.index(k) + 1] if k in a else None


def cartel_de(ep, idi):
    """Primer cartel del guion (Shorts: capa 'cartel' de la escena 1)."""
    for c in ((ep.get('escenas') or [{}])[0].get('capas') or []):
        if isinstance(c, dict) and c.get('t') == 'cartel':
            tx = c.get('texto')
            return tx.get(idi) if isinstance(tx, dict) else tx
    return None


def main(a):
    como_json = '--json' in a
    a = [x for x in a if x != '--json']
    cartel, busqueda = arg(a, '--cartel'), arg(a, '--busqueda')
    if '--titulo' in a:
        filas = [revisar(arg(a, '--titulo'), cartel, busqueda)]
    elif a and a[0] == 'guion':
        ep = json.load(open(a[1], encoding='utf-8'))
        tit, des = ep.get('titulo'), ep.get('descripcion')
        pares = tit.items() if isinstance(tit, dict) else [(ep.get('idioma', '?'), tit)]
        filas = [revisar(t, cartel_de(ep, i), busqueda, des.get(i) if isinstance(des, dict) else des) for i, t in pares if t]
    elif a and not a[0].startswith('--'):
        filas = sorted((revisar(l, cartel, busqueda) for l in open(a[0], encoding='utf-8').read().splitlines() if l.strip()),
                       key=lambda r: -r['nota'])
    else:
        print(__doc__)
        return 1
    if como_json:
        print(json.dumps(filas, ensure_ascii=False, indent=1))
    else:
        for r in filas:
            imprimir(r)
        print()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
