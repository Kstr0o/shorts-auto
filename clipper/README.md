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
```
En Claude Code basta con: "usa la skill clipper con <enlace>".

## Encuadres (por clip en momentos.json)
- `cara` (por defecto): sigue la cara mas grande y recentra en cada cambio de plano.
- `split`: directos con camara: arriba la camara (`camara`: [x, y, ancho, alto] en fracciones del video), abajo el juego.
- `centro`: recorte fijo al centro.

## Notas
- La descarga tiene que hacerse en el portatil: desde la nube y GitHub Actions YouTube la bloquea.
- `motor/subir.py` no deja subir clips de videos ajenos a los 4 canales de siempre: van a un canal de clips en otra cuenta de Google.
- `trabajo/` no se sube al repo.
