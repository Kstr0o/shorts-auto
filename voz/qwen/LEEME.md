# Voz inglesa (Qwen3-TTS 1.7B, Apache-2.0)

Elegida por el dueno el 23/11/2026. `misterio.wav` es la muestra original que le parecio "perfecta";
los otros tonos son esa misma voz clonada leyendo un texto de ese tono. `motor/voz.py` (Shorts) y el estudio
(largos HSB) clonan la referencia del tono del guion (`"tono_voz"`). Cada `.txt` es lo que dice su `.wav`.
Volver a la voz de antes: variable `VOZ_EN=supertonic` en el workflow.
Espanol (desde el 23/11, elegido por el dueno): la misma voz (`misterio.wav`) clonando solo el timbre (`x_vector_only_mode`),
sin acento del ingles. Se activa con `VOZ_ES=qwen`; si falla, Jorge (edge-tts) y luego Supertonic.
Subtitulos: tiempos reales por palabra con faster-whisper dentro de cada escena.
