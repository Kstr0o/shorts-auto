# Largos del Laboratorio del Y Si (motor de mapas)

> **Originalidad (obligatorio):** antes de escribir un largo nuevo, su tema pasa por `originalidad.yml` con su id base; `lote.py` no lo planifica si no sale "unico" (ver `lote/README.md`).

Los renderiza solo el lote semanal (`lote_semanal.yml`, miércoles 06:00 Madrid) con `motor/largo_mapas.py`:
16:9 1080p, voz es-MX-JorgeNeural (edge-tts; si cae, Supertonic M5 en todo el vídeo), subtítulos palabra a palabra.
Nada de este flujo usa IA salvo la sesión de guiones de los martes, que solo escribe estos JSON.

## Qué escribir cada semana

Cada semana van **dos** largos (lunes y viernes). Para cada uno, con id `labNNN` (seguir la numeración; el primero automático es `lab002`):

- `largos/labNNN_es.json`: el largo (16:9, `"formato_yt": "largo"`). **1.850-2.100 palabras** de narración (14-16 min). Antes, las reglas de ritmo y variedad de `lote/README.md` y `python3 motor/ritmo.py` con 0 avisos.
- `largos/labNNN_s1_es.json`, `_s2_`, `_s3_`: 3 Shorts anzuelo (9:16, `"formato_yt": "short"`, 30-35 s, ~80-95 palabras, cierre en bucle sin "sígueme"; ver `lote/README.md`),
  cada uno con un dato fuerte del largo y en la descripción `{enlace_largo}` (se cambia por el enlace del largo al subir).
- Añadir `"labNNN"` a `lote/cola_largos.json`.

El lote los programa el **lunes y el viernes a las 18:00** (Madrid) y los anzuelos **después**: ese día a las 22:00 y los dos días siguientes a las 16:30.
Si un JSON no pasa la validación, ese vídeo se salta y se avisa en el log. Probar antes: `python3 motor/largo_mapas.py --validar largos/labNNN_es.json`.

## Tema

Siempre dentro del nicho del canal: «¿Y si...?» de ciencia, geografía, historia o datos que se cuente con **mapas a escala,
globo, comparativas de tamaño, barras y tarjetas de datos** (es lo que sabe dibujar el motor). Ejemplos que encajan:
países o desiertos a escala, «¿y si toda la gente del mundo viviera en un solo país?», ríos, océanos, fronteras antiguas.
No encajan los que necesitan personajes o física animada (esos van como Shorts normales). Datos verificables; si son
estimaciones, decirlo en la descripción.

## Formato del JSON

```json
{
 "id": "lab002_es", "formato": "16:9", "formato_yt": "largo", "idioma": "es",
 "titulo": "¿Y si ...?", "descripcion": "Texto...\n\n{capitulos}\n\nFuentes...\n\n#ysi #mapas",
 "tags": ["..."], "cola": 1.5,
 "zonas": {
  "SAHARA": {"nombre": "Sáhara", "color": "#ffb347", "km2": 9.2,
             "partes": [{"a3": "DZA", "cajas": [[-9, 18, 12, 32]]}, "EGY"]},
  "BRA": {"nombre": "Brasil", "partes": ["BRA"], "km2": 8.5, "cifra": "216 M personas"}
 },
 "beats": [
  {"texto": "Frase que se ve en subtítulos.", "di": "(opcional) cómo se lee: cifras en letra",
   "v": {"tipo": "titulo", ...}, "capitulo": "Intro", "hud": {"txt": "#1 · ...", "color": "#ffd23f", "nota": "pie pequeño"},
   "pausa": 0.25}
 ]
}
```

- Cada frase (`beat`) con `v` abre escena nueva; sin `v`, sigue la escena anterior. La primera frase debe tener `v`.
  Cambiar de escena cada 1-2 frases: **9 s como mucho** por escena (lab002 iba a 13 s de media y aburre). Alternar tipos:
  nunca 3 iguales seguidos y `dato` como mucho el 28 %; usa `compara`, `cuadros`, `barras` y `ficha` para romper el ritmo. El `hud` se hereda hasta que otra frase lo cambie (`null` lo quita).
- `silencio: true` en la frase de una gran revelación: la música se corta justo antes (contraste). 2-4 por vídeo, no más.
- Sonido automático: música propia que cambia en cada capítulo y baja cuando se habla, barrido en cada cambio de escena,
  golpe grave al empezar capítulo y "pop" al aparecer una cifra. La cámara se mueve sola en todas las escenas.
- `capitulo` en la frase donde empieza cada capítulo (salen en la descripción en `{capitulos}`).
- **Zonas**: cada clave que usen las escenas tiene que estar en `zonas` o ser de las ya incluidas
  (imperios `ESP QING RUS MONG BRIT`, `ESP_HOY CHN_HOY RUS_HOY GBR_HOY AUS AMN AFR ALASKA`).
  `partes`: códigos ISO a3 de países (Natural Earth 1:110m), `"cont:Africa"` (continente entero) o
  `{"a3": "USA", "cajas": [[lon0, lat0, lon1, lat1]]}` para quedarse con un trozo. `cifra` cambia el texto de superficie.

Escenas (`v.tipo`):

| tipo | campos |
|---|---|
| `titulo` | `lineas` [{`txt`, `amarillo`, `tam`}] sobre un globo (`lon`, `lat`, `imps`). Primer fotograma = portada |
| `globo` | `lon` [ini, fin], `lat` [ini, fin], `zoom` [ini, fin], `imps` (zonas pintadas), `aparece`, `cada`, `leyenda` |
| `mapa` | `imp` (zona que crece desde su `origen`), `caja` [lon0, lat0, lon1, lat1] encuadre final, `caja0` encuadre inicial, `lon0`, `otros` (zonas tenues), `encima` + `t_encima` (zonas que aparecen encima), `etiquetas` [{`txt`, `lon`, `lat`, `t`}] |
| `compara` | `formas` (2-4 zonas, siluetas a la misma escala), `grande` (texto grande arriba) |
| `cuadros` | `formas` (superficies como cuadrados a escala), `grande` |
| `ficha` | `imp`, `puesto`, `anos` (ficha de ranking con contador) |
| `dato` | `lineas` [{`txt`, `amarillo`, `tam`}], `etiqueta` (cinta amarilla), `imp` (mapa tenue detrás) |
| `barras` | `items` [[nombre, valor, color]], `unidad` (texto tras el número; sin `unidad` = millones de km²), `marca` (nº de barra a resaltar) |

Ritmo medido con Jorge: 1.234 palabras = 9:21 (unas 132 por minuto con pausas). Ejemplo completo: `largos/imperios_es.json` (primer largo) y `largos/imperios_s1_es.json` (anzuelo).
