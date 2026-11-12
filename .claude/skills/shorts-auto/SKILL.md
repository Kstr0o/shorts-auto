---
name: shorts-auto
description: Generar, revisar y arreglar los Shorts de shorts-auto (Historias Sin Blanca / Broke Toons y El Laboratorio del Y Si / The Mad Maybe Lab), sobre todo la voz en espanol (pronunciacion, erres dobles, palabras inventadas) y la sincronia de los subtitulos. Usar al escribir episodios nuevos, al tocar el diccionario de pronunciacion o cuando un video suene o se vea mal.
---

# shorts-auto

Motor en Python que dibuja escenas SVG, pone voz, subtitulos palabra a palabra y sube a YouTube desde
GitHub Actions. Esta skill explica como funciona la voz y los subtitulos y como arreglarlos **sin
reescribir el motor**: lo que ya hace `motor/voz.py` se usa tal cual.

## Mapa rapido

| Pieza | Donde |
|---|---|
| Guiones (JSON bilingue, `ep###` Toni, `ysi###` "Y si") | `episodios/` |
| Voz, comprobacion con whisper, diccionario, cifras en letra | `motor/voz.py` |
| Dibujo, subtitulos y montaje | `motor/render.py` |
| Diccionario de pronunciacion (sin tocar codigo) | `motor/pronunciacion.json` |
| Prueba a oido de reescrituras | `motor/probar_pronuncia.py` + workflow "Probar pronunciacion" |
| Publicacion diaria / pruebas de render | `.github/workflows/publicar.yml` |

## Como sale la voz (ya implementado, no duplicar)

- **Espanol**: Chatterbox multilingue en CPU (unos 10 min por video), timbre fijo con `assets/voz/ref_es.wav`.
  **Ingles**: edge-tts (`en-US-AndrewMultilingualNeural`, -6 %). Piper es la reserva offline.
- El texto se junta en **tramos de ~120 letras**. Cada tramo pasa por `_hablado()` (diccionario + cifras,
  euros y porcentajes en letra), se genera y se **escucha con faster-whisper** (`small`, int8).
- `_generar_tramo()` compara lo oido con el texto (`difflib`, sin tildes ni signos via `_norm`). Si el
  parecido baja de 0.93 lo **repite hasta 3 veces** con otra semilla y se queda con la mejor toma. Si al
  final dice 2 o mas palabras que no estan en el texto, **corta ahi** (palabras inventadas).
- Los **subtitulos usan los tiempos reales de whisper**: `alinear()` reparte las marcas entre escenas y,
  si no casa, reparte cada tramo por longitud de palabra. El subtitulo muestra siempre la palabra del
  guion, no la reescrita.

## Arreglar una palabra mal dicha

1. Mira el log del run (`tramo N intento K: parecido 0.xx` y `whisper oyo: ...`) para ver que palabra patina.
2. Anadela a `motor/pronunciacion.json` en `"es"` (o `"en"`): `"palabra": "como se lee"`. Se aplica como
   palabra completa, sin distinguir mayusculas, y admite expresiones de varias palabras (`"low cost"`).
3. Reglas para escribir la lectura: anglicismos como suenan en Espana (`youtube` -> `yutub`,
   `whatsapp` -> `guasap`), letras alargadas a como mucho dos (`tíooo` -> `tíoo`), palabras pegadas
   separadas (`findemes` -> `fin de mes`). Nada de cifras ni simbolos: ya los pasa a letra `_hablado()`.
4. Ojo: whisper suele transcribir la palabra original ("YouTube"), asi que una reescritura muy distinta
   baja un poco el parecido del tramo. Si un tramo repite de mas por eso, acorta la reescritura.

## Erres dobles (experimental)

Chatterbox a veces suaviza la `rr` y la `r` inicial, y whisper **no lo detecta** (transcribe "perro"
igual), asi que esto solo se decide a oido:

1. Las reescrituras candidatas viven en `"_es_rr_experimental"` de `motor/pronunciacion.json`.
   **Estan inactivas**: el motor solo aplica las claves `"es"` y `"en"`.
2. Lanza en GitHub Actions el workflow **Probar pronunciacion** (vacio = todas, o `perro,error`).
   Deja en la rama `pronuncia` el video `pronuncia_es.mp4` con cada frase en dos tomas: **A normal** y
   **B reforzada**, y `pronuncia_es.json` con lo que oyo whisper en cada toma.
3. El usuario escucha y dice cuales B suenan mejor. Solo esas se mueven a `"es"`. Si una B hace que
   whisper oiga otra palabra o patine, se descarta aunque suene mas fuerte.

## Escribir un episodio nuevo

- Frases cortas y completas (el tramo de 120 letras corta mejor entre frases). Nada de parentesis.
- Cifras con numeros (`28`, `4 €`, `50 %`): el motor las lee en letra y el subtitulo las ensena en cifra.
- Antes de anadir anglicismos o nombres raros, mira si estan en el diccionario y si no, anadelos.
- Para ganchos, titulos, SEO y retencion usa las skills `yt-script`, `yt-package`, `yt-seo` y
  `yt-retention` (instaladas en la carpeta del proyecto del portatil). Nada se publica desde ellas.

## Revisar un video ya generado (portatil)

Con la skill `ffmpeg-skill` (necesita FFmpeg 6.1+ en el PATH del portatil):
- `loudness.py` para medir el volumen (YouTube normaliza a -14 LUFS).
- `caption.py --transcribe --language es --write-srt` para sacar lo que se oye y compararlo con el guion.

## Reglas

- No tocar `motor/voz.py`, `motor/render.py` ni `publicar.yml` sin avisar al hilo del canal de Shorts,
  que trabaja en `main`. Haz `git pull` antes de cada commit.
- Todo es solo de este proyecto: nada de instalar skills ni configuraciones globales.
- Los canales son de la cuenta personal de Google, nunca de la cuenta de la universidad.
