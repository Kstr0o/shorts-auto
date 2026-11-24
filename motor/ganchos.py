"""Puntuar ganchos ANTES de escribir el guion y clasificar la formula de un titulo o de una primera frase. Sin IA.

Uso (lo usa la sesion de guiones del martes; tambien lo importan estadisticas.py y nicho.py):
  python3 motor/ganchos.py puntuar ganchos.txt [--largo] [--json]   una opcion por linea -> ranking
  python3 motor/ganchos.py --gancho "una frase" [--largo]            puntuar una sola
  python3 motor/ganchos.py episodio episodios/ysi020.json            la primera frase de un guion (es y en)
  python3 motor/ganchos.py formulas                                  lista de las 21 formulas con ejemplo

Cuatro propiedades de 0 a 100 (concreto, conflicto = a ti o riesgo, curiosidad, brevedad). La nota final es 60 % la media y 40 % la
peor: un gancho con una propiedad muerta se escapa por ahi aunque las demas sean buenas. Idea de la puntuacion y de las
21 formulas: youtube-agent-skill (MIT, Jake Schincariol); aqui reescrito para espanol e ingles y para Shorts (el gancho
de un Short es la primera frase, 10 palabras como mucho, ver formula de retencion del 14/11).
LIMITES: mira la forma de la frase, no el video. Una nota baja es motivo para mirarlo otra vez; una alta no promete nada.
Lo que manda es la retencion real (estadisticas.py, apartado "Donde se va la gente", agrupa por formula).
"""
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
FORMULAS = json.load(open(os.path.join(AQUI, 'ganchos.json'), encoding='utf-8'))['formulas']

RELLENO = {'basicamente', 'básicamente', 'literalmente', 'realmente', 'muy', 'hola', 'hoy', 'video', 'vídeo', 'canal',
           'suscribete', 'suscríbete', 'bienvenidos', 'vamos', 'pues', 'bueno',
           'basically', 'actually', 'literally', 'just', 'really', 'very', 'guys', 'hey', 'welcome', 'today',
           'subscribe', 'channel', 'so'}
VAGO = {'increible', 'increíble', 'brutal', 'loco', 'locura', 'enorme', 'epico', 'épico', 'secreto', 'definitivo',
        'amazing', 'incredible', 'insane', 'crazy', 'huge', 'massive', 'secret', 'ultimate', 'unbelievable', 'epic'}
PROHIBIDO = re.compile(r"\b(vamos a ver|vamos hora a hora|vamos dia a dia|vamos día a día|en este video|en este vídeo|"
                       r"hola a todos|let'?s see|in this video|hey guys)\b", re.I)
CONCRETO = re.compile(r"(\d[\d.,]*\s?(%|€|\$|km|kg|°|k\b|m\b|x\b)?|\$\d|\d+\s?(segundos?|minutos?|horas?|d[ií]as?|semanas?|"
                      r"meses|mes|a[nñ]os?|seconds?|minutes?|hours?|days?|weeks?|months?|years?))", re.I)
TU = re.compile(r"\b(tu|tú|te|tus|ti|contigo|you|your|you'?re|yourself)\b", re.I)
RIESGO = re.compile(r"\b(perder|pierdes|muere|mueres|morir|muerto|muerte|peligro|deuda|debes|cuesta|sin|nunca|antes de|"
                    r"castigo|crac|ruina|lose|lost|die|dies|dying|dead|death|danger|debt|owe|cost|broke|never|before|"
                    r"without|stop)\b", re.I)
CURIOSIDAD = re.compile(r"\b(por que|por qué|como|cómo|que pasa|qué pasa|que pasaria|qué pasaría|cual|cuál|hasta|"
                        r"pero|nadie|casi|excepto|solo uno|why|how|what|which|until|but|nobody|almost|except|only one)\b",
                        re.I)
GIRO = re.compile(r"\b(y sobrevivi[oó]|y nadie|pero|solo uno|nadie sabe|and lived|and survived|but|only one|nobody knows)\b", re.I)
CIERRA = re.compile(r"\b(porque|asi que|así que|lo que significa|because|so that|which means)\b", re.I)


def palabras(t):
    return re.findall(r"[a-záéíóúñü0-9'%$€.]+", t.lower())


def concreto(t):
    w = palabras(t)
    if not w:
        return 0
    s = 34 + 22 * len(CONCRETO.findall(t)) - 16 * sum(x in VAGO for x in w) - 5 * sum(x in RELLENO for x in w)
    s += min(18, 6 * sum(1 for x in t.split()[1:] if x[:1].isupper()))  # nombres propios (Toni, Luna...)
    return max(0, min(100, s))


def a_ti(t):
    primeras = ' '.join(t.split()[:6])
    return max(0, min(100, 26 + 20 * len(TU.findall(t)) + (30 if TU.search(primeras) else 0)))


def riesgo(t):
    return max(0, min(100, 22 + 26 * len(RIESGO.findall(t)) + (14 if CONCRETO.search(t) else 0)))


def curiosidad(t):
    s = 34 + 17 * len(CURIOSIDAD.findall(t)) + (18 if '?' in t else 0) + (14 if GIRO.search(t) else 0) - (18 if CIERRA.search(t) else 0)
    return max(0, min(100, s))


def brevedad(t, largo=False):
    n = len(palabras(t))
    lo, hi = (9, 24) if largo else (5, 12)  # Short: 1a frase de 10 palabras max (algo de margen); largo: ~10 s hablados
    if n == 0:
        return 0
    if lo <= n <= hi:
        return 100
    return max(30, 100 - (lo - n) * 11) if n < lo else max(10, 100 - (n - hi) * 8)


def conflicto(t):
    # en nuestros nichos el gancho puede ir en 2a persona ("te despiertas...") o en 3a con algo en juego ("Toni, 0 EUR"):
    # vale lo que mas tenga de las dos
    return max(a_ti(t), riesgo(t))


PROPIEDADES = [('concreto', concreto), ('conflicto', conflicto), ('curiosidad', curiosidad)]
ARREGLO = {
    'concreto': 'cambia un adjetivo por un numero, un nombre o una fecha',
    'conflicto': 'mete al espectador ("tu/you" en las 6 primeras palabras) o di que se pierde, que cuesta o que peligro hay',
    'curiosidad': 'quita la mitad de la frase que ya se responde sola',
    'brevedad': 'Short: 10 palabras como mucho en la primera frase; largo: 9-24',
}


def clasificar(t):
    """(id, nombre) de la formula cuya forma encaja mejor con la frase o el titulo; ('sin-formula', ...) si ninguna."""
    mejor, clave = None, (0, 0)
    for f in FORMULAS:
        ms = [m for m in (re.search(p, t, re.I) for p in f['patrones']) if m]
        k = (len(ms), -min(m.start() for m in ms)) if ms else (0, 0)  # empate: gana la que aparece antes en la frase
        if k[0] and (mejor is None or k > clave):
            mejor, clave = f, k
    return (mejor['id'], mejor['nombre']) if mejor else ('sin-formula', 'Sin formula (suele ser un resumen, no un gancho)')


def puntuar(t, largo=False):
    partes = {n: fn(t) for n, fn in PROPIEDADES}
    partes['brevedad'] = brevedad(t, largo)
    vals = list(partes.values())
    nota = round(0.6 * sum(vals) / len(vals) + 0.4 * min(vals))
    if PROHIBIDO.search(t):
        nota = min(nota, 30)  # regla de la formula de retencion: nada de "vamos a ver", saludos...
    fid, nombre = clasificar(t)
    peor = min(partes, key=partes.get)
    return {'gancho': t.strip(), 'nota': nota, 'banda': banda(nota), 'formula': fid, 'formula_nombre': nombre,
            'partes': partes, 'mejorar': ARREGLO[peor], 'prohibido': bool(PROHIBIDO.search(t))}


def banda(v):
    return 'FUERTE' if v >= 65 else 'VALE' if v >= 50 else 'FLOJO'


def primera_frase(texto):
    m = re.split(r'(?<=[.!?¿¡])\s+', texto.strip(), maxsplit=1)
    return m[0] if m else texto


def imprimir(r):
    print(f"\n  {r['gancho']}")
    for k, v in r['partes'].items():
        print(f"    {k:<11} {v:3d}  {'#' * (v // 5)}")
    print(f"    NOTA        {r['nota']:3d}  {r['banda']}" + ('  (frase prohibida: saludos / "vamos a ver")' if r['prohibido'] else ''))
    print(f"    formula     {r['formula_nombre']}")
    print(f"    mejorar     {r['mejorar']}")


def main(a):
    como_json = '--json' in a
    largo = '--largo' in a
    a = [x for x in a if x not in ('--json', '--largo')]
    if not a:
        print(__doc__)
        return 1
    if a[0] == 'formulas':
        for f in FORMULAS:
            print(f"{f['id']:<16} {f['nombre']:<22} {f['forma']}\n{'':<16} ej.: {f['ejemplo']['es']} | falla si: {f['falla_si']}")
        return 0
    if a[0] == '--gancho':
        filas = [puntuar(a[1], largo)]
    elif a[0] == 'puntuar':
        filas = [puntuar(l, largo) for l in open(a[1], encoding='utf-8').read().splitlines() if l.strip()]
        filas.sort(key=lambda r: -r['nota'])
    elif a[0] == 'episodio':
        ep = json.load(open(a[1], encoding='utf-8'))
        partes = ep.get('escenas') or ep.get('beats') or ep.get('lineas') or [{}]
        texto = partes[0].get('texto', '')
        filas = []
        idiomas = ('es', 'en') if isinstance(texto, dict) else (ep.get('idioma', '?'),)
        for idi in idiomas:
            t = texto.get(idi) if isinstance(texto, dict) else texto
            if t:
                r = puntuar(primera_frase(t), largo or ep.get('serie') in ('lab', 'his'))
                r['idioma'] = idi
                filas.append(r)
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
