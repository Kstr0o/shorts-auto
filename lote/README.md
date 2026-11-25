# Lote semanal automatico

> **LOTE COMPLETO CADA MARTES (decision del dueno 24/11, manda sobre cualquier tope del prompt de la tarea).**
> Este README es la fuente de verdad del lote: cantidades, largos, originalidad y cuota. Si el prompt de la tarea dice otra cosa
> (por ejemplo "maximo 7 ysi y 7 ep" o "los largos de HSB no van en este flujo"), vale lo de aqui.
>
> **Objetivo: 2 Shorts al dia en cada uno de los 4 canales + 4 largos por semana.** Cada martes, de primeras, se escribe:
>
> | Que | Cuantos | Canal(es) | Donde |
> |---|---|---|---|
> | Y si (`ysiNNN`, es + en) | **14** | El Laboratorio del Y Si (es) y The Mad Maybe Lab (en): cada uno sale en los dos | `episodios/` + `lote/cola_auto.json` |
> | Toni "Day N" (`epNNN`, solo en) | **14** | Broke Toons | `episodios/` + `lote/cola_auto.json` |
> | Largos del Laboratorio (`labNNN_es`) | **2** (lunes y viernes 18:00) con **3 anzuelos** cada uno | Laboratorio | `largos/` + `lote/cola_largos.json` |
> | Largos de Historias Sin Blanca (`hisNNN_en`) | **2** (lunes y viernes 17:00) con **7 anzuelos** cada uno | Historias Sin Blanca | `historias/` + `lote/cola_largos.json` |
>
> - Los Shorts de Historias Sin Blanca son SOLO sus anzuelos (historias cerradas de 20-30 s que se entienden sin el largo, ver mas abajo):
>   7 por largo = 14 por semana = 2 al dia. `lote/config.json` (`largos.his.anzuelos`) tiene ya las 7 horas; un anzuelo que no exista se salta.
> - El Laboratorio recibe 14 Y si + 6 anzuelos de sus largos (algun dia sale un tercero: esta bien).
> - Antes de elegir ids, mira la rama `listos` (`gh api repos/Kstr0o/shorts-auto/git/trees/listos`): ahi hay ids que no estan en `episodios/`.
>   La deuda y el dia de Toni siguen al ultimo `epNNN_en.json` de `listos`.
>
> **Originalidad con cuota (todo pasa por ella, sin excepcion):**
> - Propuestas: unas 1,4 por guion (~20 Y si, ~20 Toni, 3 Lab, 3 HSB). Cada Y si gasta 2 busquedas (es y en), el resto 1.
> - Tope por ejecucion de `originalidad.yml`: 30 busquedas (~3.000 unidades). Como mucho **3 ejecuciones el martes (~90 busquedas, ~9.000 unidades)**,
>   lanzadas una detras de otra (esperar a que acabe cada una y hacer `git pull`). Orden: primero largos y Toni (1 busqueda), luego Y si.
>   La cuota de la API se reinicia a las 09:00 Madrid: lo que se gaste el martes por la noche comparte dia con la subida del miercoles 06:00.
>   Si se acaba la cuota (sale `"parcial": true`), seguir la regla de siempre (1 busqueda web por tema y escribir).
> - Rondas: los "cubierto" cambian de angulo y se comprueban una segunda vez como mucho; si aun asi faltan guiones, se proponen temas NUEVOS
>   (no es una tercera ronda del mismo tema) hasta llegar a la cantidad, dentro del tope de ejecuciones.
> - Si no se llega a la cantidad con la cuota del dia, se dice en el resumen cuantos faltan y se completan al dia siguiente despues de las 09:00
>   (comprobacion, guiones, commit y una ejecucion de `lote_semanal.yml` con `hoy` = fecha del martes para que planifique y renderice lo nuevo).
> - Minutos de Actions: el repo es publico (no gastan); aun asi, una sola ejecucion extra de `lote_semanal.yml` como mucho.
>
> **Prompt de la tarea programada (lo cambia el dueno):** "Sigue lote/README.md como fuente de verdad (seccion LOTE COMPLETO CADA MARTES):
> cantidades, largos del Laboratorio y de Historias Sin Blanca, originalidad y cuota. Sin topes propios."

> **LARGOS MAS LARGOS Y MUCHO MAS ENTRETENIDOS (OBLIGATORIO desde el lote del 24/11, decision del dueno).**
> Los largos pasan de ~11 a **14-16 min** (mas horas de visualizacion por vista y mas anuncios), pero SOLO si son mucho mas
> entretenidos: mejores escenas, mas variadas, personajes con vida y cambios de ritmo constantes. Datos nuestros: el largo de HSB
> se vio al 26 % y el del Laboratorio al 45 %; lab002 cambiaba de escena cada 13 s de media (30 % tarjetas de texto) y his008
> tenia un 36 % de primeros planos de cara. Eso es lo que hay que romper. Mismo nicho siempre.
>
> **Orden de trabajo de cada largo:**
> 1. **Paquete primero:** antes del guion, titulo (10 opciones, `titulos.py`) y miniatura/portada (que se ve y que pone, 3-4 palabras).
>    Si ninguna combinacion convence (nota baja o no se entiende a tamano de movil), **se descarta la idea** y se coge otra propuesta.
>    Se apunta en el json: `"paquete": {"titulo": "...", "miniatura": "que se ve + texto"}`.
> 2. **Promesa:** antes del segundo 30 el narrador promete algo concreto que se vera al final ("al final veras que pais sobrevive",
>    "by the end you'll know who wrote the note"). Se cumple en el ultimo capitulo. Campo `"promesa"` en el json.
> 3. **Estructura en capitulos de 2-2,5 min** (6-7 en 15 min). Cada capitulo cierra con un **re-gancho** (pregunta abierta o giro a medias)
>    que se resuelve en el siguiente; a mitad del video un **giro grande** que cambia lo que el espectador creia; nada de resumenes ni relleno.
> 4. **Interrupciones de ritmo cada 20-40 s:** cambio de sitio, cifra que sorprende, contador, comparacion visual, efecto de sonido,
>    cambio de musica o de plano de camara. Nunca mas de 6 s (HSB) o 9 s (Laboratorio) en la misma escena.
> 5. **Variedad:** ningun tipo de escena mas del 25-28 % del video ni 3 veces seguido; HSB con al menos 16 planos distintos y
>    **3-5 planos nuevos** en `historias/hisNNN.js` (sitios o personajes que la biblioteca no tiene; 1 basta si el largo usa 8+ escenas montadas); Laboratorio con los 8 tipos de escena.
> 5b. **Fondos que acompanen la emocion (pedido del dueno 24/11):** nada de un solo color todo el video. Laboratorio: `"lugar"` (cielo, casa, clase,
>    parque, ciudad, laboratorio, espacio, playa) y `"ambiente"` (alegre, calido, fiesta, fresco, misterio, tension) segun el momento. HSB: escenarios
>    variados y `"lugar"` en los planos `face` (ver `historias/LEEME.md`); momentos alegres con sitios luminosos, no siempre la noche roja.
> 5c. **Escenas de verdad (pedido del dueno 25/11, tras estudiar 5 videos de animacion que enganchan):** HSB se cuenta con
>    `escena` (sitio completo + personajes + hora + rotulo "SITIO · HORA") y planos `{"t": "escena"}`: el montaje corta cada 2-3 s
>    alternando general, medio, primer plano y hombro. 8-12 sitios distintos por largo (cambio cada 30-90 s), dialogos cortos con `habla`,
>    `etiquetas` para presentar personajes, un `marcador` que cambia cada 30-60 s (el "ding" de la apuesta), un `inserto` (movil, factura,
>    carta, billetes, reloj, llaves) cada ~1 min y `cartel` para las cifras fuertes. Laboratorio: `"rotulo"` (sitio · momento) en la frase
>    que abre cada capitulo y un `hud` que cambie cada 30-60 s (salta y suena al cambiar). Ver `historias/LEEME.md` y `largos/LEEME.md`.
> 6. **Personajes (HSB):** al menos 3 del reparto con nombre y un objetivo propio que choca con el del protagonista; sus frases se cuentan
>    con su reaccion en pantalla (cara, gesto o sitio distinto), no siempre la cara del protagonista.
> 7. **Picos al 25, 50 y 75 %** del video (la revelacion o cifra mas fuerte de cada tramo) y, cada 2-3 min, volver a la premisa
>    con una frase ("y todo esto, recuerda, porque..."). En el Laboratorio marca la frase de cada gran revelacion con
>    `"silencio": true` (la musica se corta justo antes: contraste). Nada de despedida: el video acaba en el ultimo giro o en una pregunta abierta.
> 8. **Comprobar:** `python3 motor/ritmo.py <largo>.json` (sin IA) y corregir hasta **0 avisos**; despues el `--validar` de siempre.
>    Si no puedes ejecutar python, aplica las mismas cifras a ojo.
>
> **Laboratorio: ideas de otro mercado (desde el 24/11).** `lote/nicho.md` trae ahora largos en ingles de canales pequenos marcados
> "(semilla)" y la columna vistas/subs (mas de 1 = el video gano por la idea). Se adapta la ESTRUCTURA al espanol (tipo de premisa,
> escala, orden de la revelacion), nunca el tema ni el titulo traducido; y pasa por originalidad en espanol como todo.

> **MEJORAS DEL ANALISIS DEL 24/11 (OBLIGATORIAS desde el lote del 24/11, aprobadas por el dueno).**
> Datos: los Shorts enganchan bien en el segundo 0 (pierden 1-20 %, sano) pero se van en el medio y en el FINAL.
> El cierre "vota / sigueme / follow for part 2" es la mayor caida del video en 8 de 15 curvas del Laboratorio y casi no da comentarios.
> Se miden en la revision del 30/11 (Broke Toons el 7/12). Nada de cambiar de nicho.
>
> **Para TODOS los Shorts (episodios, historias y anzuelos):**
> - Prohibido terminar con "vota el siguiente", "sigueme para el proximo", "follow for the next what if", "follow for part N",
>   "comment it" o cualquier peticion. La ultima frase hablada **cierra en bucle**: prepara o repite la idea de la primera,
>   de forma que al volver a empezar el video suene a continuacion.
> - La pregunta para comentar (si la hay) va **escrita en pantalla** con una capa `{"t": "cartel", "texto": "...", "y": 1540}`
>   en una escena del MEDIO (la 3 o la 4), no al final; y se repite en el comentario fijado. No se dice en voz.
>
> **Por canal:**
> - **El Laboratorio del Y Si:** 30-35 s (unas 80-95 palabras). Cierre en bucle, sin "vota/sigueme".
> - **The Mad Maybe Lab:** la PRIMERA frase es la pregunta del titulo dicha tal cual ("Why do...?", "What if...?") y el dato va
>   en la segunda. Abrir con un dato ("There is a 660 ton ball...", "30 days in total darkness...") pierde el 17-20 % en el gancho;
>   abrir con la pregunta, el 4-8 %. 30-35 s. Cierre en bucle.
> - **Historias Sin Blanca:** historias CERRADAS en un solo Short de **20-25 s** (premisa, giro y final que enlaza con el inicio).
>   Prohibido "Part N", "Parte N" y series por partes en Shorts (las Part 1 se quedaron en 3-8 vistas y las ultimas partes en 31-37 % visto).
>   Bucles temporales, cuentas atras y poderes funcionan (938-1.143 vistas, 80-87 % visto los de 22-33 s).
>   Los anzuelos de los largos tambien son autoconclusivos (20-30 s) y mantienen su plano `outro` FULL STORY, que dura poco.
>   Los de HSB se cuentan por escenas como el largo (1-3 sitios con `rotulo`, `marcador` que cambia, un `inserto` o `cartel`); los del
>   Laboratorio llevan `rotulo` en la primera frase y un `hud` que cambie (salta y suena). Los Y si siguen con su estilo de infografia.
> - **Broke Toons:** Toni "Day N" en **30-35 s como mucho** (unas 75-90 palabras): se alargo a 46-54 s y se hundio (11-231 vistas).
>   La pregunta "what should Toni do next?" va como cartel en pantalla en la escena del medio y en el comentario fijado,
>   NO como frase final (era la mayor caida en 6 de 10 curvas). Seguir haciendo lo que proponen los comentarios: es lo que mejor funciona.

> **OBLIGATORIO CADA MARTES (decision del dueno 23/11):** la sesion de guiones escribe SIEMPRE, ademas de los Shorts, los **2 largos del Laboratorio**
> de la semana (viernes y lunes, 18:00, voz Jorge) con sus 3 anzuelos cada uno, y los anade a `lote/cola_largos.json`. Aunque el prompt de la tarea
> solo hable de episodios, esto forma parte de ella; los largos tambien pasan por la comprobacion de originalidad. Sin ellos el viernes sale vacio.
>
> **Para la sesion semanal de guiones (martes):** ademas de los Shorts, cada semana escribe **dos largos del Laboratorio del Y Si**
> (`largos/labNNN_es.json`, 1.850-2.100 palabras, 14-16 min) cada uno con sus **3 Shorts anzuelo** (`largos/labNNN_s1_es.json`, `_s2_`, `_s3_`)
> siguiendo `largos/LEEME.md`, valida con `python3 motor/largo_mapas.py --validar largos/labNNN_*.json` si puedes ejecutar python,
> y anade los dos ids (`"labNNN"`) a `lote/cola_largos.json`. Es parte de la tarea, no opcional.
> Igual con **dos largos de Historias Sin Blanca** (ingles, 2.200-2.500 palabras, 14-16 min) con sus **7 anzuelos** (`_s1_` a `_s7_`) y, si hace falta, planos nuevos:
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

## Titulo y cartel: 10 opciones, se quedan 2 (desde el 24/11)

Titulo y cartel de portada son una sola pieza. Por guion escribe **10 titulos** y pasalos por
`python3 motor/titulos.py titulos.txt --cartel "TEXTO DEL CARTEL" --busqueda "la busqueda de originalidad"`.
Quedate con el de mas nota que pase la prueba de busqueda. Reglas que comprueba: 60 caracteres (40 en movil), una cifra,
nombre o fecha, 2 palabras en mayusculas como mucho, el cartel NO repite palabras del titulo y tiene 3-4 palabras,
1-2 hashtags (sin contar #shorts) y las palabras de la busqueda en el titulo o en las 2 primeras lineas de la descripcion
(son lo unico que se lee). Con el guion ya escrito: `python3 motor/titulos.py guion episodios/xxx.json --busqueda "..."`.
Tags: pocos (hasta 15) y solo para desambiguar (grafias, nombres); nada de muros de tags.

## Anzuelos y Shorts sacados de un largo (desde el 24/11)

Un anzuelo no es "el mejor momento": es un tramo que se entiende sin el resto del largo. Cada `_sN_` debe:
1. empezar con una frase completa NUEVA (la del largo da por sabido el contexto), puntuada con `ganchos.py`;
2. tener un giro dentro (una afirmacion y algo que la complica o la demuestra) y acabar en una frase, no a medias;
3. llevar un cartel de los 2 primeros segundos con palabras distintas a las que se dicen;
4. cerrar en bucle: la ultima frase prepara la primera.

## Revision semanal de los lunes (auditoria y plan, desde el 24/11)

La revision termina en **UNA sola mejora** para la semana, no en una lista. Orden para encontrarla:
1. los ultimos 10 titulos de cada canal como lista (`titulos.py`): si todos tienen la misma forma, el problema es el formato;
2. los carteles a tamano de feed: si 3 no se leen, esa es la mejora y nada mas;
3. el gancho de los 3 ultimos (apartado "Donde se va la gente" y `ganchos.py`);
4. regularidad de subidas (constancia, no cantidad);
5. la forma de la retencion (perdida en el gancho, caidas, deslizamiento).
Escribe en `aprendizajes.md`: la mejora de la semana, 3 cosas que ya funcionan (concretas, para no romperlas) y que NO tocar
todavia y por que. Nunca cambiar de nicho.

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
