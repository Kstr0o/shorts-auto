# Lote semanal automatico

> **Para la sesion semanal de guiones (martes):** ademas de los Shorts, cada semana escribe **dos largos del Laboratorio del Y Si**
> (`largos/labNNN_es.json`, 1.400-1.600 palabras, unos 11 min) cada uno con sus **3 Shorts anzuelo** (`largos/labNNN_s1_es.json`, `_s2_`, `_s3_`)
> siguiendo `largos/LEEME.md`, valida con `python3 motor/largo_mapas.py --validar largos/labNNN_*.json` si puedes ejecutar python,
> y anade los dos ids (`"labNNN"`) a `lote/cola_largos.json`. Es parte de la tarea, no opcional.
> Igual con **dos largos de Historias Sin Blanca** (ingles, ~1.700 palabras) con sus 3 anzuelos y, si hace falta, planos nuevos:
> `historias/hisNNN_en.json`, `historias/hisNNN_s1_en.json`... y `historias/hisNNN.js`, siguiendo `historias/LEEME.md`;
> valida con `python3 motor/historia.py historias/hisNNN_*.json` y anade los dos ids a `lote/cola_largos.json`.

Flujo (sin portatil, sin tokens salvo la sesion de guiones):

1. **Sesion de guiones (Claude, 1 vez por semana, antes del miercoles):** escribe los episodios nuevos en `episodios/`
   (completos en es y en: titulo, descripcion, tags y todas las escenas traducidas de verdad) y añade sus ids a `lote/cola_auto.json`.
2. **`lote_semanal.yml` (miercoles 06:00 Madrid, Actions):** `motor/lote.py plan` asigna huecos libres de la semana
   (consulta a YouTube lo ya programado y no lo toca), renderiza cada episodio en paralelo con voz Supertonic M5,
   deja los mp4 en la rama `listos` y sube con `publishAt` hasta el tope de cuota.
3. **`subir_plan.yml` (diario 09:30 Madrid):** sube lo que falte, tope `CUOTA_SUBIDAS_DIA` (variable del repo; 20 por defecto: 4 canales x 2 Shorts + largos. Limite real de la API: 100 al dia, 1 unidad por subida).

Largos: `lote.py plan` los coloca primero (config `largos`: lunes y viernes, 17:00 HSB y 18:00 Laboratorio) y los anzuelos despues
(el mismo dia por la noche y los dos dias siguientes); `lote.py subir` no sube un anzuelo hasta que su largo esta subido y le pone el enlace.
Los mp4 de mas de 100 MB van a `listos` en trozos `.partNN` y se unen al subir.

Huecos y horas: `lote/config.json`. Estado: `lote/plan.json`. Un episodio con ingles incompleto se salta y se avisa en el log.
