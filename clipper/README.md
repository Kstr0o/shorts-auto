# Clipper: de un video largo a Shorts editados

Coge un video largo (nuestros largos, un directo de Twitch o un video de YouTube), elige los mejores momentos
y saca Shorts 9:16 editados: empiezan en el gancho, siguen la cara, zooms al final de frase con whoosh,
subtitulos de 2-3 palabras con las palabras clave en color y titulo opcional arriba.

Solo gasta IA en un paso: Claude lee la transcripcion y elige los momentos (skill `clipper` en `.claude/skills`).
Descarga, Whisper, recorte y render van en local y gratis.

## Pasos
```
pip install -r clipper/requirements.txt         # y ffmpeg instalado
python clipper/descargar.py <enlace o archivo> [--desde 1:00:00 --hasta 2:00:00]   # -> trabajo/<id>
python clipper/transcribir.py trabajo/<id> [--idioma en]                          # -> transcripcion.txt
# Claude escribe trabajo/<id>/momentos.json (ver la skill)
python clipper/editar.py trabajo/<id>                                             # -> trabajo/<id>/clips/
python motor/subir.py trabajo/<id>/clips/01_x.mp4 trabajo/<id>/clips/01_x.json CANAL
python clipper/programar.py trabajo/<id>/clips                                    # canal de clips: sube ya programado (publishAt)
```
En Claude Code basta con: "usa la skill clipper con <enlace>".

## Encuadres (por clip en momentos.json)
- `cara` (por defecto): sigue la cara mas grande y recentra en cada cambio de plano.
- `split`: directos con camara: arriba la camara (`camara`: [x, y, ancho, alto] en fracciones del video), abajo el juego.
- `centro`: recorte fijo al centro.

## Notas
- Videos de YouTube: la descarga tiene que hacerse en el portatil (desde la nube YouTube la bloquea). Twitch y Kick si funcionan desde GitHub Actions.
- `motor/subir.py` no deja subir clips de videos ajenos a los 4 canales de siempre: van a un canal de clips en otra cuenta de Google.
- `trabajo/` no se sube al repo.

## Canal de clips (Daily Streamer Clips): programado como los demas
Los clips de directos ajenos no pueden ir al repo (es publico, pesan y son material de otros) y Actions no puede descargarlos,
asi que el portatil los sube en cuanto los edita, cada uno ya programado con `publishAt`: desde ese momento YouTube los publica
solo a su hora y el portatil puede estar apagado.
- `clipper/programar.py trabajo/<id>/clips`: 8 huecos al dia (12:00 a 22:30 de Madrid, `HORAS_CLIPS`), hasta 3 dias por delante,
  como mucho 10 subidas por noche (`SUBIDAS_CLIPS`); lo que no quepa sale la noche siguiente. `--simular` para ver las horas,
  `--prueba` para subir el primero en privado y sin fecha.
- Lo subido queda en `trabajo/clips_programados.json` (enlace, hora y campana) para mandar el enlace a Content Rewards al salir.
- Claves: `YT_TOKEN_CLIPS` (solo permiso de subida) + cliente OAuth, leidas de los archivos locales (`TOKEN_CLIPS_ARCHIVO`,
  `CLIENT_SECRET_ARCHIVO`). No se imprimen y nunca van al repo.

## Canal de clips 100% en la nube (sin portatil, desde el 20/11)
`clips_nube.yml` + `clipper/nube.py`, estado en la rama `clips-nube`. Cada noche (hora de Madrid):
1. 21:00 `preparar`: por streamer de `clipper/streamers_nube.json`, los clips mas vistos de la semana que hizo la gente
   (Twitch por GQL, Kick por su API) dan el VOD y el segundo; se agrupan por momento, se baja ese tramo del VOD y se transcribe.
   Se saltan los tramos ya usados (`usados.json`, incluye los del portatil) y los juegos fuera de campana.
2. 21:45 Claude (tarea programada) lee `candidatos.json` y escribe `momentos.json`: mezcla de momentos epicos, importantes y
   graciosos, corte exacto (gancho al principio), titulo, descripcion, claves y color. Luego lanza la fase `editar`.
3. `editar`: corta cada momento del VOD original en 1080p60, Whisper palabra a palabra sobre ese mismo corte (subtitulos
   sincronizados), encuadre automatico (webcam arriba y juego abajo si se detecta camara) y render 60 fps con `editar.py`.
4. `subir`: lo sube ya programado en los huecos libres (lee de YouTube lo ya programado, tambien lo del portatil), maximo 8
   por noche; lo que no cabe queda en `pendientes.json` para la noche siguiente.
5. 23:30: si Claude no llego, la fase `editar` corre sola con momentos automaticos.
Clips de la gente: solo localizan el momento; el corte sale del VOD y la edicion es nuestra. Aviso al movil: secreto `AVISO_TEMA`.
A mano: Actions > Clips en la nube > Run workflow (`fase`: preparar, editar o todo; `streamers`; `simular`).
