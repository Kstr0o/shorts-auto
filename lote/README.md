# Lote semanal automatico

> **Para la sesion semanal de guiones (martes):** ademas de los Shorts, cada semana escribe **dos largos del Laboratorio del Y Si**
> (`largos/labNNN_es.json`, 1.400-1.600 palabras, unos 11 min) cada uno con sus **3 Shorts anzuelo** (`largos/labNNN_s1_es.json`, `_s2_`, `_s3_`)
> siguiendo `largos/LEEME.md`, valida con `python3 motor/largo_mapas.py --validar largos/labNNN_*.json` si puedes ejecutar python,
> y anade los dos ids (`"labNNN"`) a `lote/cola_largos.json`. Es parte de la tarea, no opcional.
> Igual con **dos largos de Historias Sin Blanca** (ingles, ~1.700 palabras) con sus 3 anzuelos y, si hace falta, planos nuevos:
> `historias/hisNNN_en.json`, `historias/hisNNN_s1_en.json`... y `historias/hisNNN.js`, siguiendo `historias/LEEME.md`;
> valida con `python3 motor/historia.py historias/hisNNN_*.json` y anade los dos ids a `lote/cola_largos.json`.

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
   **sin_comprobar** = fallo la API o la cuota: relanza una vez; si sigue fallando, no lo escribas esta semana.
4. No cambies mucho el titulo despues de comprobarlo (si cambia, `lote.py` pide comprobarlo otra vez).
   En el json del guion anade `"originalidad": "1 frase: que tiene este video que no tengan los parecidos"` (registro corto del porque).

Cuota: ~101 unidades por busqueda (una por idioma y propuesta); tope por ejecucion `ORIG_MAX_BUSQUEDAS` (30 = ~3.000 unidades).
Limites: compara titulos y palabras clave, no ve los videos ni TikTok/Instagram; una idea igual contada con otras palabras puede pasar.

Flujo (sin portatil, sin tokens salvo la sesion de guiones):

1. **Sesion de guiones (Claude, 1 vez por semana, antes del miercoles):** pasa la comprobacion de originalidad (arriba) y escribe los episodios nuevos en `episodios/`
   (completos en es y en: titulo, descripcion, tags y todas las escenas traducidas de verdad) y añade sus ids a `lote/cola_auto.json`.
2. **`lote_semanal.yml` (miercoles 06:00 Madrid, Actions):** `motor/lote.py plan` asigna huecos libres de la semana
   (consulta a YouTube lo ya programado y no lo toca), renderiza cada episodio en paralelo con voz Supertonic M5,
   deja los mp4 en la rama `listos` y sube con `publishAt` hasta el tope de cuota.
3. **`subir_plan.yml` (diario 09:30 Madrid):** sube lo que falte, tope `CUOTA_SUBIDAS_DIA` (variable del repo; 20 por defecto: 4 canales x 2 Shorts + largos. Limite real de la API: 100 al dia, 1 unidad por subida).

Largos: `lote.py plan` los coloca primero (config `largos`: lunes y viernes, 17:00 HSB y 18:00 Laboratorio) y los anzuelos despues
(el mismo dia por la noche y los dos dias siguientes); `lote.py subir` no sube un anzuelo hasta que su largo esta subido y le pone el enlace.
Los mp4 de mas de 100 MB van a `listos` en trozos `.partNN` y se unen al subir.

Huecos y horas: `lote/config.json`. Estado: `lote/plan.json`. Un episodio con ingles incompleto se salta y se avisa en el log.
