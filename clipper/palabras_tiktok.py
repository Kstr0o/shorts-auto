"""Palabras que TikTok castiga (lo saca de "Para ti") aunque en el clip no pase nada picante.

23/11: "Kai Cenat Can't Handle Jason And Lucia's Scene" salio "no apto para Para ti": en el video no se ve nada, pero la
franja de texto quemada decia "HE WATCHES GTA 6'S SPICIEST SCENE". TikTok lee el texto en pantalla, el pie y los
subtitulos, asi que basta la palabra.

- SUAVES: insinuaciones. Se cambian por algo neutro en la franja, el pie de TikTok, las palabras resaltadas y los
  subtitulos (el video es el mismo para YouTube y TikTok; el titulo de YouTube no se toca).
- FUERTES: sexual explicito. Si sale en el titulo, la franja o lo que se dice, el clip va solo a YouTube.
Sin IA: solo listas y expresiones regulares.
"""
import re

# expresion -> reemplazo neutro (en ingles, que es el idioma de los clips). Primero las frases largas.
SUAVES = [
    (r"private moments?", "big moment"),
    (r"intimate (moments?|scenes?)", r"big \1"),
    (r"spiciest", "wildest"),
    (r"spicier", "wilder"),
    (r"spicy", "wild"),
    (r"steamy", "intense"),
    (r"sexiest", "coolest"),
    (r"sexy", "cool"),
    (r"seductive(ly)?", "smooth"),
    (r"make ?out", "moment"),
    (r"making out", "having a moment"),
    (r"hook ?up", "date"),
    (r"bedroom", "room"),
    (r"in bed", "at home"),
    (r"hottest", "best"),
    (r"thirsty|thirst trap", "excited"),
    (r"lap ?dance", "dance"),
    (r"strip ?clubs?", "nightclub"),
    (r"strippers?", "dancer"),
    (r"pole ?danc(e|er|ing)", "dance"),
    (r"twerk(s|ing|ed)?", "dance"),
    (r"booty", "moves"),
    (r"thicc?", "big"),
    (r"nsfw|18\+", ""),
    (r"onlyfans", "fans"),
    (r"after ?dark", "at night"),
]

# si sale cualquiera de estas, el clip es picante -> solo YouTube
FUERTES = [
    r"sex", r"sexual(ly)?", r"porn\w*", r"nudes?", r"naked", r"nudity", r"topless", r"boobs?", r"boobies", r"tits?",
    r"titties", r"nipples?", r"horny", r"orgasm\w*", r"cum(ming)?", r"blowjob\w*", r"hookers?", r"prostitut\w*",
    r"escorts?", r"thong", r"lingerie", r"pussy", r"genitals?", r"undress\w*", r"stripp(ing|ed)",
    r"strips (down|naked)",
]

_SUAVES = [(re.compile(rf"\b{p}\b", re.I), r) for p, r in SUAVES]
_FUERTES = re.compile(r"\b(" + "|".join(FUERTES) + r")\b", re.I)
_SUAVE_ALGUNA = re.compile(r"\b(" + "|".join(p for p, _ in SUAVES) + r")\b", re.I)


def _caso(orig, nuevo):
    if not nuevo:
        return nuevo
    if orig.isupper():
        return nuevo.upper()
    if orig[:1].isupper():
        return nuevo[:1].upper() + nuevo[1:]
    return nuevo


def limpiar(texto):
    """Cambia las insinuaciones por algo neutro, respetando mayusculas (la franja va en MAYUSCULAS)."""
    if not texto:
        return texto
    t = texto
    for rx, rep in _SUAVES:
        t = rx.sub(lambda m: _caso(m.group(0), m.expand(rep)), t)
    return re.sub(r"\s{2,}", " ", t).replace(" !", "!").replace(" ?", "?").strip()


def suave(texto):
    return bool(texto and _SUAVE_ALGUNA.search(texto))


def fuerte(texto):
    return bool(texto and _FUERTES.search(texto))


def picante(*textos):
    """True si algun texto lleva una palabra fuerte."""
    return any(fuerte(t) for t in textos if t)


def palabra_sub(w):
    """Subtitulos (una palabra cada vez): la insinuacion pasa a neutra; lo fuerte se tapa con asteriscos."""
    if fuerte(w):
        return re.sub(r"[A-Za-z]+", lambda m: m.group(0)[0] + "*" * (len(m.group(0)) - 1), w)
    return limpiar(w) or w


if __name__ == "__main__":
    for t in ["HE WATCHES GTA 6'S SPICIEST SCENE", "Kai Cenat reacts to Jason and Lucia's private moment in GTA 6",
              "YourRAGE Ends Up On A Strip Club Stage In GTA 6! 💀", "Lacy Tries To Adopt A Dog And Kills It Instead! 💀",
              "She gets naked", "Sexy dance", "Kai Cenat Catches A Sneaky Pic In A GTA 6 Scene! 😳",
              "N3on Gets A Surprise Dance In GTA 6! 😳", "Sussex", "Hot dog stand"]:
        print(f"{t!r:70} -> {limpiar(t)!r}  fuerte={fuerte(t)}  suave={suave(t)}")
