"""Voz: edge-tts (voces neuronales de Microsoft, gratis) con tiempos por palabra.
Si edge-tts no esta disponible, usa Piper (offline) y estima los tiempos.
"""
import asyncio
import json
import os
import re
import subprocess
import time
import wave

# por idioma, de la preferida a las de reserva; un episodio usa siempre una sola voz
VOCES_EDGE= {'es': ['es-ES-AlvaroNeural'],
             'en': ['en-US-AndrewMultilingualNeural', 'en-US-BrianMultilingualNeural', 'en-US-GuyNeural']}
VOCES_PIPER= {'es': 'es-carlfm-x-low.onnx', 'en': 'en-us-ryan-high.onnx'}
RATE= {'es': '+0%', 'en': '-6%'}


class VozFallo(Exception):
    pass


def _duracion(path):
    out= subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                        capture_output=True, text=True).stdout
    return float(out.strip())


async def _edge(texto, voz_edge, idioma, mp3):
    import edge_tts
    proxy= os.environ.get('EDGE_PROXY')
    c= edge_tts.Communicate(texto, voz_edge, rate=RATE[idioma], boundary='WordBoundary', proxy=proxy)
    palabras= []
    with open(mp3, 'wb') as f:
        async for m in c.stream():
            if m['type'] == 'audio':
                f.write(m['data'])
            elif m['type'] == 'WordBoundary':
                ini= m['offset'] / 1e7
                palabras.append({'p': m['text'], 'ini': ini, 'fin': ini + m['duration'] / 1e7})
    return palabras


def _estimar(texto, dur):
    # reparto el tiempo por longitud de palabra y sumo pausas en la puntuacion
    toks= texto.split()
    pesos= [len(re.sub(r'\W', '', t)) + 2 + (4 if re.search(r'[.,!?;:…]$', t) else 0) for t in toks]
    tot= sum(pesos) or 1
    t= 0.05
    util= dur - 0.15
    res= []
    for tok, w in zip(toks, pesos):
        d= util * w / tot
        res.append({'p': tok, 'ini': t, 'fin': t + d * 0.85})
        t+= d
    return res


def sintetizar(texto, idioma, wav_out, motor='edge', voz_edge=None, dir_piper=None):
    """Genera wav (mono 44.1k) y devuelve (duracion, palabras[{p, ini, fin}]).
    Con motor 'edge' reintenta y, si no hay manera, lanza VozFallo para que el episodio cambie de voz entero."""
    palabras= None
    if motor == 'edge':
        mp3= wav_out.replace('.wav', '.mp3')
        ultimo= None
        for intento in range(4):
            try:
                palabras= asyncio.run(_edge(texto, voz_edge or VOCES_EDGE[idioma][0], idioma, mp3))
                if os.path.getsize(mp3) > 1000:
                    break
                palabras= None
            except Exception as e:
                ultimo= e
                palabras= None
            time.sleep(2 + 3 * intento)
        if palabras is None:
            raise VozFallo(f'{voz_edge}: {ultimo}')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', mp3, '-ac', '1', '-ar', '44100', wav_out], check=True)
        # los WordBoundary traen la palabra sin puntuacion: recupero los tokens originales
        toks= texto.split()
        if len(toks) == len(palabras):
            for w, t in zip(palabras, toks):
                w['p']= t
        else:
            palabras= []
    else:
        modelo= os.path.join(dir_piper or os.environ.get('DIR_PIPER', '.'), VOCES_PIPER[idioma])
        tmp= wav_out.replace('.wav', '_raw.wav')
        subprocess.run(['python3', '-m', 'piper', '-m', modelo, '-f', tmp, '--length-scale', '0.92'],
                       input=texto.encode(), check=True, capture_output=True)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp, '-ac', '1', '-ar', '44100', wav_out], check=True)
    dur= _duracion(wav_out)
    if not palabras:
        palabras= _estimar(texto, dur)
    return dur, palabras


_LENG= ['es']  # idioma del episodio que se esta alineando


def _norm(t):
    # las cifras cuentan como su lectura en letra, asi "28" y "veintiocho" casan; sin tildes para tolerar al transcriptor
    num= _numero_en if _LENG[0] == 'en' else _numero_es
    t= re.sub(r'\$(\d+)', r'\1 dollars', t.lower()).replace('€', 'euros')
    t= re.sub(r'\d+', lambda m: num(int(m.group(0))) if len(m.group(0)) < 7 else m.group(0), t)
    t= t.translate(str.maketrans('áéíóúü', 'aeiouu'))
    return re.sub(r'[^0-9a-zñ]', '', t)


def alinear(textos, marcas):
    """Reparte las marcas de palabra (de una narracion continua) entre las escenas.
    textos: lista de textos por escena. marcas: [{p, ini, fin}] en orden.
    Tolera que el servicio junte, parta o cambie palabras (cifras, simbolos): lo que no encuentra lo reparte en el hueco.
    Devuelve una lista por escena de [{p, ini, fin}] con los tokens tal y como se muestran, o None si no cuadra."""
    ms= [(_norm(m['p']), m['ini'], m['fin']) for m in marcas if _norm(m['p'])]
    toks= []  # [escena, texto, ini, fin]
    for i, texto in enumerate(textos):
        for tok in texto.split():
            if not _norm(tok) and toks and toks[-1][0] == i:
                toks[-1][1]+= ' ' + tok
            elif _norm(tok):
                toks.append([i, tok, None, None])
    j, hallados= 0, 0
    for t in toks:
        n= _norm(t[1])
        k_ok= None
        for k in range(j, min(j + 5, len(ms))):
            m= ms[k][0]
            if m == n or (len(m) >= 3 and n.startswith(m)) or (len(n) >= 3 and m.startswith(n)):
                k_ok= k
                break
        if k_ok is None:
            continue
        t[2], t[3]= ms[k_ok][1], ms[k_ok][2]
        acum= len(ms[k_ok][0])
        j= k_ok + 1
        while acum < len(n) and j < len(ms) and n[acum:].startswith(ms[j][0]):
            acum+= len(ms[j][0])
            t[3]= ms[j][2]
            j+= 1
        hallados+= 1
    if not toks or hallados < 0.8 * len(toks):
        # el emparejado paso a paso se perdio: busco anclas con un alineado global de las dos secuencias
        import difflib
        for t in toks:
            t[2]= t[3]= None
        hallados= 0
        sm= difflib.SequenceMatcher(None, [_norm(t[1]) for t in toks], [m[0] for m in ms], autojunk=False)
        for blo in sm.get_matching_blocks():
            for q in range(blo.size):
                toks[blo.a + q][2], toks[blo.a + q][3]= ms[blo.b + q][1], ms[blo.b + q][2]
                hallados+= 1
        print(f'  alineado global: {hallados}/{len(toks)} palabras', flush=True)
        if not toks or hallados < 0.5 * len(toks):
            return None
    # relleno los huecos repartiendo el tiempo entre la palabra conocida anterior y la siguiente
    fin_total= marcas[-1]['fin']
    i= 0
    while i < len(toks):
        if toks[i][2] is None:
            k= i
            while k < len(toks) and toks[k][2] is None:
                k+= 1
            t_a= toks[i - 1][3] if i > 0 else 0.0
            t_b= toks[k][2] if k < len(toks) else fin_total
            paso= max(t_b - t_a, 0.05 * (k - i)) / (k - i)
            for q in range(i, k):
                toks[q][2]= t_a + paso * (q - i)
                toks[q][3]= t_a + paso * (q - i + 1)
            i= k
        else:
            i+= 1
    for a, b in zip(toks, toks[1:]):  # nunca hacia atras
        b[2]= max(b[2], a[2] + 0.01)
        b[3]= max(b[3], b[2] + 0.05)
    res= [[] for _ in textos]
    for e, p, ini, fin in toks:
        res[e].append({'p': p, 'ini': ini, 'fin': max(fin, ini + 0.05)})
    if any(not r for r in res):
        return None
    return res


def sintetizar_continuo(textos, idioma, wav_out, voz_edge):
    """Lee todo el episodio de un tiron (la entonacion fluye entre frases) y devuelve (duracion, palabras por escena)."""
    texto= ' '.join(t.strip() for t in textos)
    _LENG[0]= idioma
    mp3= wav_out.replace('.wav', '.mp3')
    marcas, ultimo= None, None
    for intento in range(4):
        try:
            marcas= asyncio.run(_edge(texto, voz_edge, idioma, mp3))
            if marcas and os.path.getsize(mp3) > 1000:
                break
            marcas= None
        except Exception as e:
            ultimo= e
            marcas= None
        time.sleep(2 + 3 * intento)
    if not marcas:
        raise VozFallo(f'{voz_edge}: {ultimo}')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', mp3, '-ac', '1', '-ar', '44100', wav_out], check=True)
    por_escena= alinear(textos, marcas)
    if por_escena is None:
        raise VozFallo(f'{voz_edge}: no pude alinear las palabras ({len(marcas)} marcas)')
    return _duracion(wav_out), por_escena


# como se escribe para que lo lea bien (el subtitulo sigue mostrando la palabra original)
PRONUNCIA= {'es': {'app': 'ap', 'apps': 'aps'}, 'en': {}}
# diccionario ampliable sin tocar codigo: motor/pronunciacion.json con {"es": {"palabra": "como se lee"}, "en": {...}}
try:
    for _idi, _d in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pronunciacion.json'), encoding='utf-8')).items():
        PRONUNCIA.setdefault(_idi, {}).update(_d)
except (OSError, ValueError):
    pass
# idiomas que narra el motor expresivo (Chatterbox); el resto sigue con edge
CHATTER= {'es': {'exaggeration': 0.5, 'cfg_weight': 0.5},
          'en': {'exaggeration': 0.5, 'cfg_weight': 0.4}}  # cfg mas bajo = ritmo algo mas pausado
_chatter= {}
# muestra de la propia voz del motor (sacada de un video que sono bien) para que el timbre sea siempre el mismo
REF_VOZ= {'es': os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'voz', 'ref_es.wav')}


def _hablado(texto, idioma):
    for a, b in PRONUNCIA.get(idioma, {}).items():
        texto= re.sub(rf'\b{re.escape(a)}\b', b, texto, flags=re.IGNORECASE)
    # cifras y simbolos en letra, que este motor no los lee bien
    if idioma == 'es':
        texto= re.sub(r'(\d+)\s*€', lambda m: re.sub(r'uno$', 'un', _numero_es(int(m.group(1))).replace('veintiuno', 'veintiún')) + (' euro' if m.group(1) == '1' else ' euros'), texto)
        texto= re.sub(r'(\d+)\s*%', lambda m: _numero_es(int(m.group(1))) + ' por ciento', texto)
        texto= re.sub(r'\d+', lambda m: _numero_es(int(m.group(0))), texto)
    elif idioma == 'en':
        texto= re.sub(r'\$(\d+)(?= (?:fine|bill|bet|prize|tip|check|loan)\b)', lambda m: _numero_en(int(m.group(1))) + ' dollar', texto)  # a three hundred dollar fine
        texto= re.sub(r'\$(\d+)', lambda m: _numero_en(int(m.group(1))) + (' dollar' if m.group(1) == '1' else ' dollars'), texto)
        texto= re.sub(r'(\d+)\s*%', lambda m: _numero_en(int(m.group(1))) + ' percent', texto)
        texto= re.sub(r'\d+', lambda m: _numero_en(int(m.group(0))), texto)
    return texto


_UE= 'zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen'.split()
_DE= 'twenty thirty forty fifty sixty seventy eighty ninety'.split()


def _numero_en(n):
    if n < 20:
        return _UE[n]
    if n < 100:
        return _DE[n // 10 - 2] + ('-' + _UE[n % 10] if n % 10 else '')
    if 1100 <= n < 2000 and n % 100:
        return _numero_en(n // 100) + ' ' + ('oh ' if n % 100 < 10 else '') + _numero_en(n % 100)  # anos: nineteen sixty-four
    if n < 1000:
        return _UE[n // 100] + ' hundred' + (' ' + _numero_en(n % 100) if n % 100 else '')
    if n < 1000000:
        return _numero_en(n // 1000) + ' thousand' + (' ' + _numero_en(n % 1000) if n % 1000 else '')
    return str(n)


_U= 'cero uno dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince dieciséis diecisiete dieciocho diecinueve veinte veintiuno veintidós veintitrés veinticuatro veinticinco veintiséis veintisiete veintiocho veintinueve'.split()
_D= {30: 'treinta', 40: 'cuarenta', 50: 'cincuenta', 60: 'sesenta', 70: 'setenta', 80: 'ochenta', 90: 'noventa'}
_C= ['', 'ciento', 'doscientos', 'trescientos', 'cuatrocientos', 'quinientos', 'seiscientos', 'setecientos', 'ochocientos', 'novecientos']


def _numero_es(n):
    if n < 30:
        return _U[n]
    if n < 100:
        return _D[n // 10 * 10] + (' y ' + _U[n % 10] if n % 10 else '')
    if n == 100:
        return 'cien'
    if n < 1000:
        return _C[n // 100] + (' ' + _numero_es(n % 100) if n % 100 else '')
    if n < 1000000:
        miles= 'mil' if n // 1000 == 1 else re.sub(r'uno$', 'ún' if n // 1000 == 21 else 'un', _numero_es(n // 1000)) + ' mil'
        return miles + (' ' + _numero_es(n % 1000) if n % 1000 else '')
    return str(n)


def _marcas_whisper(wav, idioma):
    """Tiempos por palabra escuchando el audio ya generado."""
    from faster_whisper import WhisperModel
    if 'w' not in _chatter:
        _chatter['w']= WhisperModel('small', device='cpu', compute_type='int8')
    segs, _= _chatter['w'].transcribe(wav, language=idioma, word_timestamps=True, vad_filter=False)
    return [{'p': w.word.strip(), 'ini': w.start, 'fin': w.end} for sg in segs for w in sg.words]


def _limpiar_bordes(a, marcas, sr):
    """Quita los ruiditos sueltos que el motor deja antes de la primera palabra y despues de la ultima,
    y suaviza los extremos para que la union entre tramos no haga clic."""
    import torch
    if not marcas:
        return a, marcas
    v= int(sr * 0.03)
    x= a[0]
    rms= lambda i: float(torch.sqrt(torch.mean(x[max(i, 0):i + v] ** 2) + 1e-12))
    umbral= max(0.004, 0.04 * float(torch.sqrt(torch.mean(x ** 2))))
    # desde la primera palabra voy hacia atras hasta encontrar silencio; desde la ultima, hacia delante
    i= int(marcas[0]['ini'] * sr)
    while i > 0 and rms(i - v) >= umbral:
        i-= v
    j= min(int(marcas[-1]['fin'] * sr), x.shape[0])
    while j < x.shape[0] and rms(j) >= umbral:
        j+= v
    i= max(i - int(sr * 0.04), 0)
    j= min(j + int(sr * 0.08), x.shape[0])
    if j - i < sr * 0.3:
        return a, marcas
    b= a[:, i:j].clone()
    f= int(sr * 0.02)
    rampa= torch.linspace(0, 1, f)
    b[0, :f]*= rampa
    b[0, -f:]*= rampa.flip(0)
    t0= i / sr
    return b, [{'p': w['p'], 'ini': max(w['ini'] - t0, 0), 'fin': max(w['fin'] - t0, 0.02)} for w in marcas]


def _generar_tramo(m, txt, idioma, n, tmp, original=None):
    """Genera un tramo y lo escucha: si patina o inventa palabras lo repite (hasta 3 veces) y se queda con el mejor.
    Devuelve (audio, marcas de palabra relativas al tramo, parecido con el texto)."""
    import difflib
    import torch
    import torchaudio
    esperado= [_norm(t) for t in txt.split() if _norm(t)]
    # whisper suele escribir la palabra original (YouTube) y no su lectura (yutub): comparo con las dos formas
    esperado_o= [_norm(t) for t in (original or txt).split() if _norm(t)]
    mejor= None
    for intento in range(3):
        torch.manual_seed(1000 * n + intento)
        kw= dict(CHATTER[idioma])
        con_ref= os.path.exists(REF_VOZ.get(idioma, ''))
        if con_ref and _chatter.get('ref') != idioma:
            kw['audio_prompt_path']= REF_VOZ[idioma]  # misma voz en todos los videos; queda cargada para los siguientes tramos
        elif not con_ref and _chatter.get('ref') and _chatter.get('conds0') is not None:
            m.conds= _chatter['conds0']  # este idioma usa la voz de serie del motor
        try:
            a= m.generate(txt, language_id=idioma, temperature=0.7, **kw)
        except TypeError:
            a= m.generate(txt, language_id=idioma, **kw)
        _chatter['ref']= idioma if con_ref else None
        marcas, parecido= [], 0.0
        try:
            torchaudio.save(tmp, a, m.sr)
            marcas= _marcas_whisper(tmp, idioma)
            oido= [_norm(x['p']) for x in marcas]
            sm= difflib.SequenceMatcher(None, ''.join(esperado), ''.join(oido), autojunk=False)
            parecido= max(sm.ratio(), difflib.SequenceMatcher(None, ''.join(esperado_o), ''.join(oido), autojunk=False).ratio())
            # si al final dice algo que no esta en el texto, corto ahi
            ult= 0
            for esp in (esperado, esperado_o):
                bloques= difflib.SequenceMatcher(None, esp, oido, autojunk=False).get_matching_blocks()
                ult= max([ult] + [bl.b + bl.size for bl in bloques if bl.size])
            # solo recorto si de verdad sobra texto: con cifras whisper parte las palabras distinto y no hay que cortar nada
            if 0 < ult < len(oido) and len(oido) - ult >= 2 and parecido < 0.9 and len(''.join(oido[ult:])) >= 10:
                corte= marcas[ult - 1]['fin'] + 0.15
                a= a[:, :int(corte * m.sr)]
                marcas= marcas[:ult]
                print(f'    tramo {n}: recorto {len(oido) - ult} palabras sobrantes al final', flush=True)
        except Exception as e:
            print(f'    sin comprobacion ({e!r})', flush=True)
            return a, [], 0.0
        a, marcas= _limpiar_bordes(a, marcas, m.sr)
        print(f'    tramo {n} intento {intento}: parecido {parecido:.2f}', flush=True)
        if mejor is None or parecido > mejor[2]:
            mejor= (a, marcas, parecido)
        if parecido >= 0.93:
            break
    return mejor


def sintetizar_chatter(textos, idioma, wav_out):
    """Narra el episodio con Chatterbox (entonacion mas humana) por tramos cortos y devuelve (duracion, palabras por escena)."""
    try:
        import torch
        import torchaudio
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        if 'm' not in _chatter:
            _chatter['m']= ChatterboxMultilingualTTS.from_pretrained(device='cpu')
            _chatter['conds0']= getattr(_chatter['m'], 'conds', None)
        m= _chatter['m']
        _LENG[0]= idioma
        # junto escenas seguidas en tramos de hasta ~120 letras para que la frase fluya sin desviarse
        tramos, act= [], []
        for i, t in enumerate(textos):
            if act and sum(len(textos[k]) for k in act) + len(t) > 120:
                tramos.append(act)
                act= []
            act.append(i)
        if act:
            tramos.append(act)
        trozos, limites, marcas, t0= [], [], [], 0.0
        pausa= torch.zeros(1, int(m.sr * 0.18))
        for n, tr in enumerate(tramos):
            orig= ' '.join(textos[k].strip() for k in tr)
            txt= _hablado(orig, idioma)
            a, ms, parecido= _generar_tramo(m, txt, idioma, n, wav_out.replace('.wav', '_t.wav'), orig)
            d= a.shape[1] / m.sr
            limites.append((tr, t0, t0 + d))
            marcas+= [{'p': x['p'], 'ini': x['ini'] + t0, 'fin': min(x['fin'], d) + t0} for x in ms]
            trozos+= [a, pausa]
            t0+= d + 0.18
        crudo= wav_out.replace('.wav', '_c.wav')
        torchaudio.save(crudo, torch.cat(trozos, dim=1), m.sr)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', crudo, '-ac', '1', '-ar', '44100', wav_out], check=True)
    except Exception as e:
        raise VozFallo(f'chatter: {e!r}')
    dur= _duracion(wav_out)
    por_escena= alinear(textos, marcas) if marcas else None
    if por_escena is None:
        # sin marcas fiables: reparto cada tramo (cuyos limites si conozco) por longitud de palabra
        print('  tiempos estimados por tramo', flush=True)
        if marcas:
            print('  whisper oyo: ' + ' '.join(x['p'] for x in marcas), flush=True)
        por_escena= [[] for _ in textos]
        for tr, a, b in limites:
            est= _estimar(' '.join(textos[k].strip() for k in tr), b - a)
            q= 0
            for k in tr:
                c= len(textos[k].split())
                por_escena[k]= [{'p': w['p'], 'ini': w['ini'] + a, 'fin': w['fin'] + a} for w in est[q:q + c]]
                q+= c
        if any(not r for r in por_escena):
            raise VozFallo('chatter: escena sin palabras')
    return dur, por_escena


def opciones(idioma):
    """Lista de (motor, voz) a probar en orden para un episodio completo."""
    if os.environ.get('MOTOR_VOZ', 'edge') != 'edge':
        return [('piper', None)]
    antes= [('chatter', None)] if idioma in CHATTER else []
    return antes + [('edge', v) for v in VOCES_EDGE[idioma]] + [('piper', None)]
