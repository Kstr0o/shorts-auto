# Lote semanal automatico

> **OBLIGATORIO CADA MARTES (decision del dueno 23/11):** la sesion de guiones escribe SIEMPRE, ademas de los Shorts, los **2 largos del Laboratorio**
> de la semana (viernes y lunes, 18:00, voz Jorge) con sus 3 anzuelos cada uno, y los anade a `lote/cola_largos.json`. Aunque el prompt de la tarea
> solo hable de episodios, esto forma parte de ella; los largos tambien pasan por la comprobacion de originalidad. Sin ellos el viernes sale vacio.
>
> **Para la sesion semanal de guiones (martes):** ademas de los Shorts, cada semana escribe **dos largos del Laboratorio del Y Si**
> (`largos/labNNN_es.json`, 1.400-1.600 palabras, unos 11 min) cada uno con sus **3 Shorts anzuelo** (`largos/labNNN_s1_es.json`, `_s2_`, `_s3_`)
> siguiendo `largos/LEEME.md`, valida con `python3 motor/largo_mapas.py --validar largos/labNNN_*.json` si puedes ejecutar python,
> y anade los dos ids (`"labNNN"`) a `lote/cola_largos.json`. Es parte de la tarea, no opcional.
> Igual con **dos largos de Historias Sin Blanca** (ingles, ~1.700 palabras) con sus 3 anzuelos y, si hace falta, planos nuevos:
> `historias/hisNNN_en.json`, `historias/hisNNN_s1_en.json`... y `historias/hisNNN.js`, siguiendo `historias/LEEME.md`;
> valida con `python3 motor/historia.py historias/hisNNN_*.json` y anade los dos ids a `lote/cola_largos.json`.

## Senales de los canales (antes de elegir temas, idea del dueno 23/11)

Lee el ultimo informe de estadisticas (`gh api "repos/Kstr0o/shorts-auto/contents/$(gh api 'repos/Kstr0o/shorts-auto/git/trees/datos' --jq '[.tree[].path|select(startswith("20"))]|max')/informe.md?ref=datos" -H "Accept: application/vnd.github.raw"`),
apartado **Senales de crecimiento** de cada canal:
- **Destacados** (3x o mas la mediana de vistas): esta semana escribe **al menos 2 guiones del mismo estilo** que cada destacado
  (mismo nicho, mismo formato y estructura, titulo con la misma forma). Distinto tema, eso si: tambien pasan la originalidad.
- **Terminos de busqueda**: lo que la gente escribio para encontrarnos; buenas pistas para temas y titulos.

## Lo que despega en el nicho (antes de elegir temas, desde el 24/11)

`nicho.yml` (martes 18:30 Madrid, sin IA) deja en `lote/nicho.md` de main los videos de NUESTRO nicho que han hecho 2 veces
o mas la mediana de su propio canal (Short con Short, largo con largo) y la formula de gancho de su titulo.
Leelo (`gh api "repos/Kstr0o/shorts-auto/contents/lote/nicho.md" -H "Accept: application/vnd.github.raw"`) y usa en la semana
las 2-3 formulas y duraciones que mas se repiten en cada canal. Se copia la FORMA, nunca el tema (los temas pasan por originalidad).
Las busquedas de cada canal estan en `lote/nicho.json` y siempre son de su mismo nicho.

## Ganchos: 5 opciones puntuadas antes del guion (obligatorio desde el 24/11)

Para cada guion (Short, largo, historia o anzuelo), antes de escribir el resto:
1. Escribe **5 ganchos** (la primera frase, 10 palabras como mucho en Shorts) con **formulas distintas** de `motor/ganchos.json`
   (21 formulas con ejemplo y "falla si"; `python3 motor/ganchos.py formulas`). Prioriza las que salen en `lote/nicho.md`
   y las que mejor retienen en nuestro informe (apartado "Donde se va la gente", linea "Por formula de gancho").
2. Puntualos: `python3 motor/ganchos.py puntuar ganchos.txt` (una opcion por linea; `--largo` para largos e historias).
   Si no puedes ejecutar python, aplica a ojo sus 4 criterios: concreto (numero/nombre), conflicto (tu o algo en juego),
   curiosidad (pregunta abierta) y brevedad.
3. Usa el de mas nota salvo que otro encaje claramente mejor con el titulo (el gancho confirma el titulo). Nada de "vamos a ver".
4. Apunta en el json del guion: `"gancho": {"formula": "<id>", "nota": N, "descartados": ["...", "..."]}`.
   Asi el informe diario cruza formula con retencion real y en unas semanas sabremos cuales funcionan en cada canal.
La nota es orientativa (mira la forma de la frase, no el video): manda la retencion real.

## Titulos con lo que la gente busca

La comprobacion de originalidad apunta en `lote/originalidad.md` lo que **YouTube autocompleta** con la `busqueda` de cada propuesta.
Para los **largos** (Laboratorio e HSB) el titulo debe contener, si encaja, una de esas frases tal cual (el resto del titulo puede
anadir el gancho). En los Shorts es opcional. Si para ello el titulo cambia mucho, vuelve a pasar esa propuesta por la comprobacion
(cuenta como la segunda ronda). Pon en "busqueda" 2-4 palabras genericas del tema para que el autocompletado de ideas.

## Tono de la voz inglesa (desde el 23/11)

La voz en ingles es Qwen3-TTS (la elegida por el dueno) y cambia de tono segun el video. En cada guion nuevo (episodio, historia o largo)
pon `"tono_voz"`: `misterio` (intriga, historias raras), `energia` (curiosidad, ciencia, "y si..."), `humor` (situaciones graciosas, Toni)
o `drama` (emotivo, serio). Elige por el contenido, no por el canal. Si falta, se usa el de la serie (ep humor, how/ysi energia, his misterio).
El espanol no cambia (Jorge).

## Originalidad (obligatorio antes de escribir cualquier guion, pedido del dueno 22/11)

Ningun episodio, largo ni historia entra en el plan si `lote/originalidad.json` no lo da por **"unico"** (lo exige `motor/lote.py`).
Siempre dentro del mismo nicho de cada canal: se cambia el angulo, el dato o el formato, nunca el tipo de canal.

1. Escribe `propuestas.json` con mas temas de los que necesitas (unos 1,5 por guion): por cada uno
   `{"id": "ysi015", "serie": "ysi", "titulo": {"es": "...", "en": "..."}, "angulo": "que lo hace distinto",
   "busqueda": {"es": "3-6 palabras como lo buscaria alguien", "en": "..."}}`. Los largos e historias van por su id base (`lab003`, `his008`) y
   pueden llevar solo un idioma (`"titulo": "...", "idioma": "en"`).
2. Lanza la comprobacion en la nube (sin IA, solo API de YouTube):
   `B=$(gzip -9c propuestas.json | base64 -w0)` y
   `gh api -X POST repos/Kstr0o/shorts-auto/actions/workflows/originalidad.yml/dispatches -f ref=main -f "inputs[propuestas]=$B"`.
   A los ~2 min lee `lote/originalidad.md` de main (`gh api "repos/Kstr0o/shorts-auto/contents/lote/originalidad.md" -H "Accept: application/vnd.github.raw"`).
3. Veredictos: **unico** = escribelo. **cubierto** = ya hay 3 o mas videos casi iguales en el top 25 de YouTube o uno de mas de 100.000
   vistas este ano: busca un angulo propio (dato concreto poco conocido, caso real, escala o personaje distinto, comparativa, serie por partes),
   cambia titulo y busqueda y vuelve a comprobar (una segunda ronda como mucho). **repetido** = ya lo tenemos: descartalo.
   Si la busqueda en YouTube falla (API o cuota), lo que no se parece a nada nuestro sale **unico** con `"parcial": true`: relanza una vez
   y, si sigue fallando, haz 1 busqueda web por tema para descartar los trillados y escribelo igual (nunca nos quedamos sin videos por la API).
4. No cambies mucho el titulo despues de comprobarlo (si cambia, `lote.py` pide comprobarlo otra vez).
   En el json del guion anade `"originalidad": "1 frase: que tiene este video que no tengan los parecidos"` (registro corto del porque).

Cuota: ~101 unidades por busqueda (una por idioma y propuesta); tope por ejecucion `ORIG_MAX_BUSQUEDAS` (30 = ~3.000 unidades).
Limites: compara titulos y palabras clave, no ve los videos ni TikTok/Instagram; una idea igual contada con otras palabras puede pasar.

Flujo (sin portatil, sin tokens salvo la sesion de guiones):

1. **Sesion de guiones (Claude, 1 vez por semana, antes del miercoles):** pasa la comprobacion de originalidad (arriba) y escribe los episodios nuevos en `episodios/`
   (completos en es y en: titulo, descripcion, tags y todas las escenas traducidas de verdad) y añade sus ids a `lote/cola_auto.json`.
2. **`lote_semanal.yml` (miercoles 06:00 Madrid, Actions):** `motor/lote.py plan` asigna huecos libres de la semana
   (consulta a YouTube lo ya programado y no lo toca), renderiza cada episodio en paralelo (ingles Qwen3-TTS por tono, espanol Jorge),
   deja los mp4 en la rama `listos` y sube con `publishAt` hasta el tope de cuota.
3. **`subir_plan.yml` (diario 09:30 Madrid):** sube lo que falte, tope `CUOTA_SUBIDAS_DIA` (variable del repo; 20 por defecto: 4 canales x 2 Shorts + largos. Limite real de la API: 100 al dia, 1 unidad por subida).

Largos: `lote.py plan` los coloca primero (config `largos`: lunes y viernes, 17:00 HSB y 18:00 Laboratorio) y los anzuelos despues
(el mismo dia por la noche y los dos dias siguientes); `lote.py subir` no sube un anzuelo hasta que su largo esta subido y le pone el enlace.
Los mp4 de mas de 100 MB van a `listos` en trozos `.partNN` y se unen al subir.

Huecos y horas: `lote/config.json`. Estado: `lote/plan.json`. Un episodio con ingles incompleto se salta y se avisa en el log.
