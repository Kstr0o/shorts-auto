# shorts-auto

Genera y publica Shorts de dibujos de forma automatica, en español e ingles.

- `motor/` dibuja las escenas (SVG), pone la voz, los subtitulos palabra a palabra y monta el video.
- `episodios/` es la cola de guiones (JSON bilingue). `ep###` = serie de Toni, `ysi###` = "¿Y si...?".
- `.github/workflows/publicar.yml` publica cada dia el siguiente episodio de cada serie.
- `estado.json` apunta lo ya publicado.

## Probar en local

    pip install -r requirements.txt
    python3 motor/render.py episodios/ep001.json salida es en

## Pasos unicos (los hace el dueño de los canales)

1. Crear los 4 canales de YouTube (Toni ES, Toni EN, Y si ES, What if EN) con la misma cuenta de Google.
2. En Google Cloud: crear un proyecto, activar "YouTube Data API v3", configurar la pantalla de consentimiento
   y crear credenciales OAuth de tipo "App de escritorio". Descargar `client_secret.json`.
3. Ejecutar `python motor/obtener_token.py client_secret.json` una vez por canal y guardar cada token.
4. En el repositorio, Settings > Secrets and variables > Actions, crear los secretos:
   `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_TOKEN_TONI_ES`, `YT_TOKEN_TONI_EN`, `YT_TOKEN_YSI_ES`, `YT_TOKEN_YSI_EN`.
5. Pedir a Google la auditoria de la API. Hasta que la aprueben los videos suben en privado.
   Cuando la aprueben, crear la variable `YT_PRIVACIDAD` = `public`.

Todos los videos se suben marcados como contenido sintetico (generado).

## Cadencia y cuota

Cada ejecucion publica el siguiente episodio de cada serie en sus dos idiomas (4 subidas). Con dos ejecuciones al dia son 8 subidas.
La cuota por defecto de la API de YouTube (10.000 unidades/dia, 1.600 por subida) solo da para unas 6 subidas al dia por proyecto
de Google Cloud: para 2 episodios al dia por canal hay que pedir ampliacion de cuota o repartir los canales en dos proyectos.
