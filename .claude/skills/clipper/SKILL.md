---
name: clipper
description: Convierte un video largo (largo propio, directo de Twitch o video de YouTube) en Shorts verticales editados con subtitulos, zooms y whoosh. Usar cuando pidan sacar clips, recortes o Shorts de un video o directo.
---

# Clipper

Objetivo: de un enlace o archivo, devolver 5-8 Shorts listos para subir, ordenados del mejor al peor, sin que el usuario toque nada.

## 0. Preparacion (solo la primera vez)
- Comprobar `ffmpeg -version` y `python --version`. Si falta algo: `pip install -r clipper/requirements.txt` (y ffmpeg con winget en Windows).
- La primera transcripcion baja el modelo de Whisper (tarda un poco mas; es normal).

## 1. Descargar
`python clipper/descargar.py "<enlace o archivo>"` -> imprime la carpeta `trabajo/<id>`.
Directos de Twitch de varias horas: si el usuario da la franja, `--desde`/`--hasta`; si no, procesar entero.

## 2. Transcribir
`python clipper/transcribir.py trabajo/<id> --idioma <en|es>` (si va lento: `--modelo small`).

## 3. Elegir momentos (el unico paso con IA)
Leer `trabajo/<id>/transcripcion.txt` entero (tiene [inicio-fin] en segundos por frase) y `info.json`.
Reglas para cada clip:
- Se entiende sin contexto: un desconocido lo ve y lo pilla.
- Empieza EXACTAMENTE en el gancho: dato sorprendente, frase atrevida, inicio de una historia, pregunta fuerte o reaccion exagerada. Nada de saludos, "so, um", ni frases a medias. Saltar el relleno de antes.
- Termina en el remate (risa, conclusion, giro), no a mitad de idea.
- 20-60 s (mejor 25-45). Sin solapes entre clips.
- Nota de 0 a 10 por potencial viral; quedarse con los 5-8 mejores (>= 6).
- `titulo`: corto y con gancho, en el idioma del video, sin clickbait falso ni ragebait (max 70 caracteres).
- `descripcion`: 1-2 frases + 3 hashtags. El credito al original lo anade el script solo.
- `claves`: 2-5 palabras del clip que deben salir en color (cifras, nombres, palabras fuertes).
- `texto_arriba` (opcional): 2-5 palabras de gancho fijas arriba.
- `color` (global): el color de marca del creador si se conoce; si no, `#FFD400`.
- Encuadre: si es un directo con camara del streamer en una esquina, sacar un fotograma
  (`ffmpeg -ss <t> -i trabajo/<id>/video.mp4 -frames:v 1 trabajo/<id>/f.jpg`), mirarlo, y usar
  `"encuadre": "split", "camara": [x, y, ancho, alto]` en fracciones (0-1) del fotograma. Podcasts y videos con caras: dejar el de por defecto.

Escribir `trabajo/<id>/momentos.json`:
```json
{"idioma": "en", "color": "#FFD400", "clips": [
  {"inicio": 812.4, "fin": 851.0, "titulo": "...", "descripcion": "...", "tags": ["..."],
   "claves": ["million"], "texto_arriba": "...", "nota": 9, "gancho": "bold claim"}]}
```

## 4. Editar
`python clipper/editar.py trabajo/<id>` (o `--solo 1,3` para rehacer algunos). Salida en `trabajo/<id>/clips/`.
Revisar 2-3 fotogramas de cada clip (ffmpeg -ss ... -frames:v 1) para ver que la cara sale bien encuadrada y los subtitulos se leen.
Cambios del usuario en lenguaje normal ("solo el mejor, menos de 30 s, subtitulos azules"): tocar momentos.json y re-editar.

## 5. Subir (solo si el usuario lo pide)
`python motor/subir.py <clip.mp4> <clip.json> <CANAL>` con publishAt como el resto.
- Clips de NUESTROS largos: a su canal (anzuelos SIEMPRE despues de que el largo sea publico).
- Clips de videos ajenos (Twitch/YouTube): SOLO a un canal de clips en otra cuenta de Google; subir.py lo bloquea en los 4 canales de siempre.
- Nunca subir ni borrar sin que el usuario lo haya pedido.

Al acabar: lista de clips con nota, duracion y titulo.
