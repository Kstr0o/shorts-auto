# Estado del canal de clips en la nube

Lo escribe el workflow `clips_nube.yml` (codigo en `clipper/nube.py` de main). No tocar a mano salvo `momentos.json`.
- `candidatos.json`: momentos mas clipeados de la semana por streamer, con su transcripcion (21:00 Madrid).
- `momentos.json`: los que elige Claude cada noche (corte exacto, titulo, gancho, colores).
- `programados.json` / `programados.md`: lo subido y su hora de salida.
- `usados.json`: tramos de VOD ya usados (no se repiten). `pendientes.json`: editados que no cupieron.
