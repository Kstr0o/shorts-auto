# Largos de Historias Sin Blanca (estudio de animación privado)

> **Originalidad (obligatorio):** antes de escribir un largo nuevo, su tema pasa por `originalidad.yml` con su id base; `lote.py` no lo planifica si no sale "unico" (ver `lote/README.md`).

El lote semanal (`lote_semanal.yml`, miércoles 06:00 Madrid) los renderiza solo con el estudio de animación, que vive en el
repo **privado** `estudio-animacion` (no tiene licencia para publicarse: aquí solo van los guiones). 16:9 1080p 24 fps,
inglés, voz **Supertonic M1** (la del canal), subtítulos palabra a palabra, música y efectos generados.

## Qué escribir cada semana

Cada semana van **dos** historias (lunes y viernes). Para cada una, con id `hisNNN` (seguir la numeración; el primer automático es `his008`):

- `historias/hisNNN_en.json`: el largo (`"formato": "16:9"`, `"formato_yt": "largo"`). **1.650-1.750 palabras** (con M1,
  1.389 palabras dieron 8:50, unas 157 por minuto: 1.700 son unos 11 min).
- `historias/hisNNN_s1_en.json`, `_s2_`, `_s3_`: 3 Shorts anzuelo (`"formato": "9:16"`, `"formato_yt": "short"`, 20-30 s,
  55-75 palabras, autoconclusivos y sin "Part N"; ver `lote/README.md`), cada uno con un momento fuerte del largo, que acaba con plano `outro` (`l1: "FULL STORY"`, `l2: "ON THE CHANNEL"`)
  y `{enlace_largo}` en la descripción.
- `historias/hisNNN.js` (opcional pero recomendado): **2-5 planos nuevos** para esta historia (escenarios o personajes que la
  biblioteca no tiene), para que no se repitan siempre los mismos sitios. Mismo formato que la biblioteca: `import` de
  `/engine/core.js`, `/engine/rig2d.js`, `/engine/fx2d.js`, `/engine/ui2d.js` y `../cast.js`; registrar con `registerShot('id', { draw(g, t, info) {...} })`.
  Si no estás seguro de que funcione, mejor no lo uses: un error de JavaScript tira el render de esa semana.
- Añadir `"hisNNN"` a `lote/cola_largos.json`.

El lote las programa el **lunes y el viernes a las 17:00** (Madrid) y los anzuelos **después**: ese día a las 20:00 y los dos días siguientes a las 17:00.
Validar antes: `python3 motor/historia.py historias/hisNNN_*.json`.

## Estilo del canal

Inglés de EE. UU., segunda persona ("you"), premisa de un giro imposible (bucle temporal, solo tú tienes un poder,
apocalíptico, misterio), días numerados o cuenta atrás, gancho en la primera línea (empezar por el momento más tenso y
volver atrás), giro final y pregunta a los comentarios. Historias propias: nada copiado de otros canales ni personas reales.

## Formato del guion

```json
{
 "id": "his008_en", "formato": "16:9", "formato_yt": "largo", "idioma": "en",
 "titulo": "...", "descripcion": "...\n\n{capitulos}\n\n...", "tags": ["story", "animation"],
 "hud": "DAY",
 "reparto": {"YOU": {"top": "hoodie", "color": "#37c8b4", "head": "none"}, "LENA": {"top": "trench", "color": "#c8504a", "head": "ponytail", "headColor": "#3a2014"}},
 "pronuncia": {"3:07": "three oh seven"},
 "musica": [[0, "tension", 0.6], [6, "mystery", 0.5]],
 "lineas": [
  {"texto": "Forty seconds. That's all you have left.", "capitulo": "Intro", "dia": 7,
   "planos": [{"t": "countdown", "from": 40, "caption": "SECONDS LEFT"}]}
 ]
}
```

- `lineas`: un párrafo de narración cada una (1-3 frases). Cada frase va a un plano: los `planos` de la línea se reparten
  entre sus frases en orden (si sobran frases, se repiten con otra cámara). Cambiar de plano cada 2-4 s.
- `dia`: número que sale arriba a la izquierda (`hud` + número; sin `dia` no sale). Al cambiar de día hay fundido.
- `capitulo`: donde empieza cada capítulo (salen en la descripción en `{capitulos}`).
- `musica`: `[línea donde empieza, mood, intensidad 0-1]`. Moods seguros: tension, mystery, playful, sad (happy NO existe y tira el render).
- `reparto`: ropa y colores de los personajes. Las claves son fijas: `YOU` (protagonista), `LENA` (segundo personaje:
  puede ser cualquiera), `MOM`, `DAD`, `BARISTA`, `BOSS`, `WORKER`. Ropa: `top` hoodie, trench, tshirt, suit; `head` none,
  ponytail, bun, cap.
- `pronuncia`: cómo leer horas, siglas o nombres raros (también ayuda a sincronizar los subtítulos).
- Parámetros comunes de todos los planos: `v` (0-3, otra cámara o variante), `caption` (rótulo grande), `capColor`.

## Planos de la biblioteca

| plano | qué es | parámetros |
|---|---|---|
| `title` | portada con reloj y lluvia | `l1`, `l2` (dos líneas de título) |
| `countdown` | número grande que baja | `from`, `rate`, `caption` |
| `reset` | destello de rebobinado | `caption`, `loop` |
| `face` | primer plano de cara | `e` (neutral, happy, sad, angry, scared, shocked, confused, thinking, determined, worried, smirk, smile, cry), `who` (lena, mom). No usar `bg` ni `glow` con textos o true: rompen el plano |
| `alarm` | despertador digital | `time`, `ring`, `night`, `blink`, `color` |
| `phone` | móvil en mano | `screen` (date, msg, news, call), `big`, `text` (líneas con `|`), `from`, `hot` |
| `call` | pantalla partida tú / madre | `e`, `momE` |
| `rules` | libreta con lista | `titulo`, `lista` (hasta 4 frases), `n` (cuántas se ven, 0-3) |
| `notes` | tablero de pistas | `items` (hasta 6 textos cortos) |
| `cup` | vaso con nombre mal escrito | `name` |
| `lottery` | boleto de lotería | `win`, `gone`, `numeros`, `premio`, `cabecera` |
| `arm` | brazo con texto escrito | `text` (con `|`), `clean` |
| `brass` | reloj de latón | `tick`, `hand`, `scratch` |
| `memory` | recuerdo con padre e hijo | `blur` |
| `montage` | escenas rápidas | `kind` (restaurant, boss, guitar, echo) |
| `night` | exterior de noche | `place` (room, parking, highway), `time` |
| `sunset` | atardecer | `pose` (sit, stand), `e` |
| `bus` | parada de autobús con lluvia | `run`, `pose`, `e`, `leave` |
| `cafe` | cafetería | `cup`, `lena`, `lenaE`, `e`, `pose` |
| `alley` | callejón | `lenaE`, `lenaFace`, `follow`, `e` |
| `shopext` | fachada de tienda | `flicker`, `who` |
| `outro` | cierre | `l1`, `l2` |
| `bed3d` | dormitorio 3D | `time`, `pose` (sit, lie), `night` |
| `street3d` | calle 3D con lluvia | `night`, `pose`, `bus`, `run`, `walk`, `who`, `both` |
| `shop3d` | tienda de relojes 3D | `who` (none, you, both), `chime` |

Ejemplo completo: `historias/his007_en.json` (el primer largo, "Every Night at 3:07 AM the World Resets").
