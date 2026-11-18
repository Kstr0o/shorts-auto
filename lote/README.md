# Lote semanal automatico

Flujo (sin portatil, sin tokens salvo la sesion de guiones):

1. **Sesion de guiones (Claude, 1 vez por semana, antes del miercoles):** escribe los episodios nuevos en `episodios/`
   (completos en es y en: titulo, descripcion, tags y todas las escenas traducidas de verdad) y añade sus ids a `lote/cola_auto.json`.
2. **`lote_semanal.yml` (miercoles 06:00 Madrid, Actions):** `motor/lote.py plan` asigna huecos libres de la semana
   (consulta a YouTube lo ya programado y no lo toca), renderiza cada episodio en paralelo con voz Supertonic M5,
   deja los mp4 en la rama `listos` y sube con `publishAt` hasta el tope de cuota.
3. **`subir_plan.yml` (diario 09:30 Madrid):** sube lo que falte, tope `CUOTA_SUBIDAS_DIA` (variable del repo; 100 desde el 18/11: 1 unidad por subida, limite de 100 al dia).

Huecos y horas: `lote/config.json`. Estado: `lote/plan.json`. Un episodio con ingles incompleto se salta y se avisa en el log.
