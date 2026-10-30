"""Insignias de rangos y teams para el resource pack del server.

Uso:
    python generar.py "C:\\ruta\\al\\pack\\extraido"

Lee rangos.json, dibuja cada insignia como PNG, las agrega a la fuente
minecraft:default del pack (sin tocar los glifos que ya tiene) y deja en
salida/ el pack listo para subir (.zip), su SHA1 y una vista previa.

by Heleon ST
"""
import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path

from PIL import Image

AQUI = Path(__file__).resolve().parent
SALIDA = AQUI / "salida"
TEXTURAS = "heleon/rangos"          # assets/minecraft/textures/heleon/rangos/
FIRMA = " §8· by Heleon ST"
ITEMS_NS = "heleon"                 # assets/heleon/ para items custom
ICONO_ALTO = 36                    # px reales; en el juego mide 9, como las insignias

# Fuente de 5 filas. Cada letra es una lista de filas; '#' = pixel.
LETRAS = {
    "A": [".#.", "#.#", "###", "#.#", "#.#"],
    "B": ["##.", "#.#", "##.", "#.#", "##."],
    "C": [".##", "#..", "#..", "#..", ".##"],
    "D": ["##.", "#.#", "#.#", "#.#", "##."],
    "E": ["###", "#..", "##.", "#..", "###"],
    "F": ["###", "#..", "##.", "#..", "#.."],
    "G": [".##", "#..", "#.#", "#.#", ".##"],
    "H": ["#.#", "#.#", "###", "#.#", "#.#"],
    "I": ["###", ".#.", ".#.", ".#.", "###"],
    "J": ["..#", "..#", "..#", "#.#", ".#."],
    "K": ["#.#", "#.#", "##.", "#.#", "#.#"],
    "L": ["#..", "#..", "#..", "#..", "###"],
    "M": ["#...#", "##.##", "#.#.#", "#...#", "#...#"],
    "N": ["#..#", "##.#", "#.##", "#..#", "#..#"],
    "Ñ": ["####", "#..#", "##.#", "#.##", "#..#"],
    "O": [".#.", "#.#", "#.#", "#.#", ".#."],
    "P": ["##.", "#.#", "##.", "#..", "#.."],
    "Q": [".#.", "#.#", "#.#", "##.", ".##"],
    "R": ["##.", "#.#", "##.", "#.#", "#.#"],
    "S": [".##", "#..", ".#.", "..#", "##."],
    "T": ["###", ".#.", ".#.", ".#.", ".#."],
    "U": ["#.#", "#.#", "#.#", "#.#", "###"],
    "V": ["#.#", "#.#", "#.#", "#.#", ".#."],
    "W": ["#...#", "#...#", "#.#.#", "##.##", "#...#"],
    "X": ["#.#", "#.#", ".#.", "#.#", "#.#"],
    "Y": ["#.#", "#.#", ".#.", ".#.", ".#."],
    "Z": ["###", "..#", ".#.", "#..", "###"],
    "0": [".#.", "#.#", "#.#", "#.#", ".#."],
    "1": [".#.", "##.", ".#.", ".#.", "###"],
    "2": ["##.", "..#", ".#.", "#..", "###"],
    "3": ["##.", "..#", ".#.", "..#", "##."],
    "4": ["#.#", "#.#", "###", "..#", "..#"],
    "5": ["###", "#..", "##.", "..#", "##."],
    "6": [".##", "#..", "###", "#.#", "###"],
    "7": ["###", "..#", ".#.", ".#.", ".#."],
    "8": ["###", "#.#", "###", "#.#", "###"],
    "9": ["###", "#.#", "###", "..#", "##."],
    "+": ["...", ".#.", "###", ".#.", "..."],
    "-": ["...", "...", "###", "...", "..."],
    " ": ["..", "..", "..", "..", ".."],
}


# Iconos de 8x8 para el scoreboard (alto 8 = igual que el texto). char, colores, dibujo.
ICONOS = {
    "jugador": ("EB00", {"b": "#5a3a1e", "s": "#e8b48a", "k": "#3b5bdb", "m": "#a0684a"}, [
        ".bbbbbb.", "bbbbbbbb", "bssssssb", "skksskks",
        "ssssssss", "sssmmsss", ".ssssss.", "........"]),
    "team": ("EB01", {"g": "#9ca3af", "r": "#e03131", "d": "#a51d1d"}, [
        "grrrrrr.", "grrrrrrr", "grrddrrr", "grrrrrr.",
        "g.......", "g.......", "g.......", "g......."]),
    "rango": ("EB02", {"y": "#ffd43b", "o": "#f08c00"}, [
        "...yy...", "...yy...", "yyyyyyyy", ".yyyyyy.",
        "..yyyy..", ".yyooyy.", ".yo..oy.", "o......o"]),
    "espada": ("EB03", {"s": "#adb5bd", "w": "#f1f3f5", "y": "#f59f00", "b": "#7c4a1e"}, [
        "......ss", ".....sws", "....sws.", "y..sws..",
        ".yysws..", "..yy....", ".byyy...", "bb......"]),
    "calavera": ("EB04", {"w": "#f1f3f5", "k": "#212529", "g": "#adb5bd"}, [
        ".wwwwww.", "wwwwwwww", "wkkwwkkw", "wkkwwkkw",
        "wwwkkwww", ".wwwwww.", "..wgwg..", "..wwww.."]),
    "reloj": ("EB05", {"y": "#4dabf7", "w": "#f1f3f5", "k": "#212529"}, [
        "..yyyy..", ".ywwwwy.", "ywwkwwwy", "ywwkwwwy",
        "ywwkkkwy", "ywwwwwwy", ".ywwwwy.", "..yyyy.."]),
    "online": ("EB06", {"g": "#2f9e44", "G": "#69db7c"}, [
        "........", "..gggg..", ".gGGGGg.", ".gGGGGg.",
        ".gGGGGg.", ".gGGGGg.", "..gggg..", "........"]),
    "ping": ("EB07", {"G": "#69db7c"}, [
        "......G.", "......G.", "....G.G.", "....G.G.",
        "..G.G.G.", "..G.G.G.", "G.G.G.G.", "G.G.G.G."]),
}


def dibujar_icono(colores, filas):
    img = Image.new("RGBA", (len(filas[0]), len(filas)), (0, 0, 0, 0))
    px = img.load()
    for y, fila in enumerate(filas):
        for x, c in enumerate(fila):
            if c != ".":
                px[x, y] = hex_rgb(colores[c]) + (255,)
    return img


# Numeros grandes del contador (1-10) en U+EC01..U+EC0A: dorados del 10 al 6, rojos del 5 al 1.
NUMERO_BASE = 0xEC00
DIGITOS = {
    "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
}


def dibujar_numero(n):
    """Digitos 5x7 al doble, con degradado vertical, brillo arriba y borde oscuro."""
    if n > 5:
        arriba, abajo, borde = hex_rgb("#fff3a0"), hex_rgb("#f08c00"), hex_rgb("#4a2c00")
    else:
        arriba, abajo, borde = hex_rgb("#ffb3a8"), hex_rgb("#d61f1f"), hex_rgb("#3d0000")
    filas = DIGITOS[str(n)] if n < 10 else [DIGITOS["1"][y] + "." + DIGITOS["0"][y] for y in range(7)]
    esc = 2
    w, h = len(filas[0]) * esc + 2, len(filas) * esc + 2
    lleno = {(1 + x * esc + dx, 1 + y * esc + dy)
             for y, fila in enumerate(filas) for x, c in enumerate(fila) if c == "#"
             for dx in range(esc) for dy in range(esc)}
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    for (x, y) in lleno:
        t = (y - 1) / max(1, h - 3)
        color = mezclar(arriba, abajo, t)
        if (x, y - 1) not in lleno:
            color = mezclar(color, (255, 255, 255), 0.5)
        px[x, y] = color + (255,)
    for y in range(h):
        for x in range(w):
            if (x, y) in lleno:
                continue
            if any((x + dx, y + dy) in lleno for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                px[x, y] = borde + (255,)
    return img


# Anuncio en la esquina superior izquierda (fuentes propias heleon:anuncio y heleon:anuncio_texto;
# no toca minecraft:default). El /title y el subtitulo siempre salen centrados: para moverlos a la
# esquina, cada uno termina con un "espacio" de ancho calculado que corre su centro, y el banner y
# la letra llevan relleno transparente abajo para poder subirlos con un ascent grande.
# Medidas en px de GUI respecto al centro de la pantalla (pensado para escala de GUI Auto / 3).
ANUNCIO_IZQ, ANUNCIO_ARRIBA = -250, -140
BANNER_H = 32                       # alto visible del banner (1 px de imagen = 1 px de GUI)
BANNER_LIENZO = 128                 # alto total con relleno: en /title (x4) son 32 unidades
CAP_IZQ, CAP_DER = 34, 20           # zona del logo y de la estrella
# ancho del texto en px y letras aprox. El ultimo es el tope: el datapack recorta lo que no quepa.
TAMANOS = {"s": (150, 12), "m": (240, 20), "l": (360, 30), "xl": (460, 38)}
APERTURA = [0.12, 0.28, 0.46, 0.64, 0.82, 1.0]
BRILLO_CUADROS = 12
TEXTO_ASCENT = {"ascii.png": 78, "nonlatin_european.png": 78, "accented.png": 81}


def dibujar_banner(ancho, logo=None, brillo=None):
    """Panel azul con borde dorado y celeste, remaches, el logo y una estrella; brillo = reflejo."""
    w, h = max(40, ancho), BANNER_H
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    contorno, oro, oro_osc, celeste = hex_rgb("#050b18"), hex_rgb("#f5c542"), hex_rgb("#a8740f"), hex_rgb("#3fa9ff")
    arriba, abajo = hex_rgb("#163a72"), hex_rgb("#08142e")

    def dentro(x, y, m):
        # rectangulo con esquinas cortadas en diagonal (estilo pixel)
        c = 4 - m if m < 4 else 0
        if x < m or y < m or x >= w - m or y >= h - m:
            return False
        return min(x - m, w - 1 - m - x) + min(y - m, h - 1 - m - y) >= c

    for y in range(h):
        for x in range(w):
            if not dentro(x, y, 0):
                continue
            if not dentro(x, y, 1):
                px[x, y] = contorno + (255,)
            elif not dentro(x, y, 2):
                px[x, y] = (oro if y < h // 2 else oro_osc) + (255,)
            elif not dentro(x, y, 3):
                px[x, y] = celeste + (255,)
            else:
                c = mezclar(arriba, abajo, (y - 3) / (h - 7))
                if y == 3:
                    c = mezclar(c, (255, 255, 255), 0.18)
                px[x, y] = c + (255,)

    for x in range(CAP_IZQ, w - 8):
        if (x // 2) % 2 == 0:
            px[x, 5] = mezclar(oro, arriba, 0.55) + (255,)
            px[x, h - 6] = mezclar(oro, abajo, 0.55) + (255,)
    for cx, cy in ((w - 7, 4), (w - 7, h - 6)):
        for dx in (0, 1):
            for dy in (0, 1):
                px[cx + dx, cy + dy] = oro + (255,)

    # Insignia redonda con el logo a la izquierda y estrella dorada pegada al borde derecho
    r, cx, cy = 12, 17, h // 2
    for y in range(h):
        for x in range(min(w, 32)):
            d = ((x - cx + 0.5) ** 2 + (y - cy + 0.5) ** 2) ** 0.5
            if d <= r - 1.5:
                px[x, y] = hex_rgb("#0a1838") + (255,)
            elif d <= r:
                px[x, y] = oro + (255,)
    if logo is not None:
        l = logo.copy()
        l.thumbnail((20, 20), Image.LANCZOS)
        img.alpha_composite(l, (cx - l.width // 2, cy - l.height // 2))
    if w >= 70:
        estrella = ["...#...", "...#...", "..###..", "#######", "..###..", "...#...", "...#..."]
        sx, sy = w - 17, h // 2 - 3
        for y, fila in enumerate(estrella):
            for x, c in enumerate(fila):
                if c == "#":
                    px[sx + x, sy + y] = (hex_rgb("#fff2a8") if (x, y) == (3, 3) else oro) + (255,)

    if brillo is not None:
        for y in range(3, h - 3):
            for x in range(3, w - 3):
                if px[x, y][3] and brillo <= x + y * 0.6 < brillo + 7:
                    r_, g_, b_, a_ = px[x, y]
                    px[x, y] = mezclar((r_, g_, b_), (255, 255, 255), 0.35) + (a_,)
    return img


def cuadros_anuncio(logo, area):
    """Cuadros de un tamano: se abre desde la izquierda, pasa el reflejo y queda quieto.
    Todos miden lo mismo de ancho (un pixel casi invisible a la derecha) para que no se muevan."""
    total = CAP_IZQ + area + CAP_DER
    contenidos = [dibujar_banner(round(total * f), logo) for f in APERTURA]
    recorrido = total + BANNER_H
    contenidos += [dibujar_banner(total, logo, brillo=-20 + recorrido * i / (BRILLO_CUADROS - 1))
                   for i in range(BRILLO_CUADROS)]
    contenidos.append(dibujar_banner(total, logo))
    cuadros = []
    for c in contenidos:
        lienzo = Image.new("RGBA", (total, BANNER_LIENZO), (0, 0, 0, 0))
        lienzo.alpha_composite(c, (0, 0))
        if lienzo.getpixel((total - 1, 0))[3] == 0:
            lienzo.putpixel((total - 1, 0), (0, 0, 0, 1))
        cuadros.append(lienzo)
    return cuadros, total


def fuente_texto_movible(destino):
    """Copia la letra del juego con relleno debajo de cada celda para poder subirla con el ascent."""
    vanilla = AQUI / "vanilla"
    include = vanilla / "default.json"
    if not include.exists():
        raise SystemExit("Falta vanilla/default.json (se saca del .jar de Minecraft 1.21.11)")
    tex = destino / "assets" / ITEMS_NS / "textures" / "font" / "anuncio_texto"
    tex.mkdir(parents=True, exist_ok=True)
    providers = []
    for p in json.loads(include.read_text(encoding="utf-8"))["providers"]:
        nombre = p["file"].split("/")[-1]
        img = Image.open(vanilla / nombre).convert("RGBA")
        filas, cols = len(p["chars"]), len(p["chars"][0])
        cw, ch = img.width // cols, img.height // filas
        ascent = TEXTO_ASCENT[nombre]
        alto = max(ascent, ch)                       # alto de celda nuevo (escala 1: px = unidades)
        nueva = Image.new("RGBA", (img.width, alto * filas), (0, 0, 0, 0))
        for f in range(filas):
            nueva.alpha_composite(img.crop((0, f * ch, img.width, (f + 1) * ch)), (0, f * alto))
        nueva.save(tex / nombre)
        providers.append({"type": "bitmap", "file": f"{ITEMS_NS}:font/anuncio_texto/{nombre}",
                          "ascent": ascent, "height": alto, "chars": p["chars"]})
    return providers


def agregar_anuncio(destino):
    """Banner (heleon:anuncio), letra movible (heleon:anuncio_texto) y sonido heleon:anuncio."""
    logo_path = AQUI / "logos" / "heleon.png"
    logo = Image.open(logo_path).convert("RGBA") if logo_path.exists() else None
    tex = destino / "assets" / ITEMS_NS / "textures" / "font" / "anuncio"
    tex.mkdir(parents=True, exist_ok=True)
    for viejo in tex.iterdir():
        viejo.unlink()

    banner_prov, espacios_banner, espacios_texto, meta = [], {}, {" ": 4, "‌": 0}, {}
    finales = []
    for n, (clave, (area, letras)) in enumerate(TAMANOS.items()):
        cuadros, total = cuadros_anuncio(logo, area)
        base = 0xE000 + n * 0x20
        for i, img in enumerate(cuadros):
            img.save(tex / f"{clave}-{i}.png")
            banner_prov.append({"type": "bitmap", "file": f"{ITEMS_NS}:font/anuncio/{clave}-{i}.png",
                                "ascent": BANNER_LIENZO // 4, "height": BANNER_LIENZO // 4,
                                "chars": [chr(base + i)]})
        # Centro del banner y del texto en unidades de /title (x4) y de subtitulo (x2)
        centro_banner = (ANUNCIO_IZQ + total / 2) / 4
        centro_texto = (ANUNCIO_IZQ + CAP_IZQ + area / 2) / 2
        esp_b, esp_t = chr(0xE0F0 + n), chr(0xE1F0 + n)
        espacios_banner[esp_b] = round(-2 * centro_banner, 2)
        espacios_texto[esp_t] = round(-2 * centro_texto, 2)
        meta[clave] = {"base": base, "cuadros": len(cuadros), "apertura": len(APERTURA),
                       "letras": letras, "espacio_banner": esp_b, "espacio_texto": esp_t}
        finales.append(cuadros[-1])
    banner_prov.append({"type": "space", "advances": espacios_banner})

    fuentes = destino / "assets" / ITEMS_NS / "font"
    fuentes.mkdir(parents=True, exist_ok=True)
    (fuentes / "anuncio.json").write_text(json.dumps({"providers": banner_prov}, indent=2), encoding="utf-8")
    # El espacio va primero: ascii.png tambien trae " " (celda vacia, ancho 0) y gana el primer proveedor.
    texto_prov = [{"type": "space", "advances": espacios_texto}] + fuente_texto_movible(destino)
    (fuentes / "anuncio_texto.json").write_text(json.dumps({"providers": texto_prov}, indent=2), encoding="utf-8")
    (SALIDA / "anuncio.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    sonido = AQUI / "sonidos" / "anuncio.ogg"
    if sonido.exists():
        (destino / "assets" / ITEMS_NS / "sounds").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(sonido, destino / "assets" / ITEMS_NS / "sounds" / "anuncio.ogg")
        (destino / "assets" / ITEMS_NS / "sounds.json").write_text(json.dumps(
            {"anuncio": {"sounds": [{"name": f"{ITEMS_NS}:anuncio", "stream": False}]}}, indent=2), encoding="utf-8")

    # Vista previa: pantalla de 640x360 px de GUI con los tres tamanos en su posicion
    for clave, img in zip(TAMANOS, finales):
        pantalla = Image.new("RGBA", (640, 360), (108, 143, 191, 255))
        pantalla.paste((91, 143, 58, 255), (0, 200, 640, 360))
        x0, y0 = 320 + ANUNCIO_IZQ, 180 + ANUNCIO_ARRIBA
        pantalla.alpha_composite(img.crop((0, 0, img.width, BANNER_H)), (x0, y0))
        pantalla.resize((1280, 720), Image.NEAREST).save(SALIDA / f"vista-anuncio-{clave}.png")
    return meta


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mezclar(c, otro, t):
    return tuple(round(a + (b - a) * t) for a, b in zip(c, otro))


def dibujar(texto, color):
    """Insignia de 9 px de alto: borde, relleno con brillo arriba, texto con sombra."""
    texto = texto.upper()
    for ch in texto:
        if ch not in LETRAS:
            raise SystemExit(f"Caracter no soportado en '{texto}': {ch!r}")
    ancho_txt = sum(len(LETRAS[ch][0]) for ch in texto) + len(texto) - 1
    w, h = ancho_txt + 6, 9
    base = hex_rgb(color)
    borde = mezclar(base, (0, 0, 0), 0.45)
    brillo = mezclar(base, (255, 255, 255), 0.25)
    sombra = mezclar(base, (0, 0, 0), 0.35)
    # En fondos claros (blanco, amarillo) el texto blanco no se lee: se usa oscuro.
    claro = 0.299 * base[0] + 0.587 * base[1] + 0.114 * base[2] > 170
    letra = (33, 37, 41, 255) if claro else (255, 255, 255, 255)
    if claro:
        sombra = mezclar(base, (0, 0, 0), 0.15)
    # En fondos casi negros el borde oscuro se pierde con el chat: se aclara.
    if 0.299 * base[0] + 0.587 * base[1] + 0.114 * base[2] < 60:
        borde = mezclar(base, (255, 255, 255), 0.35)

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    for y in range(h):
        for x in range(w):
            esquina = (x in (0, w - 1)) and (y in (0, h - 1))
            if esquina:
                continue
            if x in (0, w - 1) or y in (0, h - 1):
                px[x, y] = borde + (255,)
            elif y == 1:
                px[x, y] = brillo + (255,)
            else:
                px[x, y] = base + (255,)

    x0 = 3
    for ch in texto:
        filas = LETRAS[ch]
        for fy, fila in enumerate(filas):
            for fx, c in enumerate(fila):
                if c == "#":
                    px[x0 + fx, 2 + fy + 1] = sombra + (255,)
        for fy, fila in enumerate(filas):
            for fx, c in enumerate(fila):
                if c == "#":
                    px[x0 + fx, 2 + fy] = letra
        x0 += len(filas[0]) + 1
    return img


def cargar_icono(ruta, alto=ICONO_ALTO, quitar_fondo=True):
    """Logo con fondo blanco -> transparente, recortado y escalado a alta resolucion."""
    img = Image.open(ruta).convert("RGBA")
    px = img.load()
    # Si el PNG ya trae transparencia, el blanco es parte del logo (letras, brillos): no se toca.
    # Con quitar_fondo: false se deja tal cual (logos que ya son una placa con su fondo).
    ya_transparente = img.getextrema()[3][0] < 255
    if quitar_fondo == "oscuro" and not ya_transparente:
        # Fondo negro (con texturas tenues): cuanto mas oscuro, mas transparente; se "desmezcla" del negro.
        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = px[x, y]
                t = min(1.0, max(0.0, (max(r, g, b) - 45) / 130))
                px[x, y] = (0, 0, 0, 0) if t <= 0.02 else \
                    tuple(min(255, round(c / t)) for c in (r, g, b)) + (round(a * t),)
        quitar_fondo = False
    for y in range(img.height if quitar_fondo and not ya_transparente else 0):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            # Cuanto mas blanco, mas transparente; el borde suavizado se "desmezcla" del blanco.
            t = min(1.0, (255 - min(r, g, b)) / 200)
            if t <= 0.02:
                px[x, y] = (0, 0, 0, 0)
                continue
            r, g, b = (max(0, min(255, round((c - 255 * (1 - t)) / t))) for c in (r, g, b))
            px[x, y] = (r, g, b, round(a * t))
    img = img.crop(img.getbbox())
    ancho = max(1, round(img.width * alto / img.height))
    return img.resize((ancho, alto), Image.LANCZOS)


def agregar_items(destino):
    """Items custom de items.json: textura + modelo (1.21.4+) y su comando /give."""
    ruta = AQUI / "items.json"
    if not ruta.exists():
        return []
    items = json.loads(ruta.read_text(encoding="utf-8"))["items"]
    assets = destino / "assets" / ITEMS_NS
    for sub in ("items", "models/item", "textures/item"):
        carpeta = assets / sub
        if carpeta.exists():
            shutil.rmtree(carpeta)
        carpeta.mkdir(parents=True)
    comandos = []
    for it in items:
        iid = it["id"]
        textura = Image.open(AQUI / it["textura"])
        if textura.size != (16, 16):
            print(f"Aviso: la textura de {iid} mide {textura.size}, lo normal es 16x16")
        shutil.copyfile(AQUI / it["textura"], assets / "textures/item" / f"{iid}.png")
        (assets / "models/item" / f"{iid}.json").write_text(json.dumps({
            "parent": "minecraft:item/generated",
            "textures": {"layer0": f"{ITEMS_NS}:item/{iid}"},
        }, indent=2), encoding="utf-8")
        (assets / "items" / f"{iid}.json").write_text(json.dumps({
            "model": {"type": "minecraft:model", "model": f"{ITEMS_NS}:item/{iid}"},
        }, indent=2), encoding="utf-8")
        componentes = [f'item_model="{ITEMS_NS}:{iid}"'] + it.get("componentes", [])
        comandos.append(f"give @p {it['base']}[{','.join(componentes)}] 1")
    return comandos


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    pack = Path(sys.argv[1])
    if not (pack / "pack.mcmeta").is_file():
        raise SystemExit(f"No encuentro pack.mcmeta en {pack}")

    cfg = json.loads((AQUI / "rangos.json").read_text(encoding="utf-8"))
    insignias = cfg["insignias"]
    chars = [i["char"].upper() for i in insignias] + [i["char_icono"].upper() for i in insignias if "imagen" in i]
    if len(set(chars)) != len(chars):
        raise SystemExit("Hay dos insignias con el mismo char en rangos.json")

    destino = SALIDA / "pack"
    # Se copia encima en vez de borrar: Windows (antivirus, miniaturas) a veces deja bloqueados
    # los miles de PNG del pack. Solo se limpia la carpeta propia de insignias.
    shutil.copytree(pack, destino, dirs_exist_ok=True)

    carpeta = destino / "assets/minecraft/textures" / TEXTURAS
    # Se vacia en vez de borrarla: en Windows una carpeta abierta (Explorador, terminal) no se puede quitar.
    carpeta.mkdir(parents=True, exist_ok=True)
    for viejo in carpeta.iterdir():
        viejo.unlink()

    fuente_path = destino / "assets/minecraft/font/default.json"
    fuente = json.loads(fuente_path.read_text(encoding="utf-8")) if fuente_path.exists() else {"providers": []}
    # Quita insignias de una pasada anterior para que el script se pueda repetir.
    fuente["providers"] = [p for p in fuente["providers"] if f"/{TEXTURAS}/" not in "/" + p.get("file", "").split(":", 1)[-1]]
    usados = {c for p in fuente["providers"] for fila in p.get("chars", []) for c in fila}

    previas = []
    for ins in insignias:
        ch = chr(int(ins["char"], 16))
        if ch in usados:
            raise SystemExit(f"El char {ins['char']} de '{ins['id']}' ya lo usa el pack")
        img = None
        if not ins.get("solo_icono"):
            img = dibujar(ins["texto"], ins["color"])
            img.save(carpeta / f"{ins['id']}.png")
            fuente["providers"].append({
                "type": "bitmap",
                "file": f"minecraft:{TEXTURAS}/{ins['id']}.png",
                "ascent": 8,
                "height": 9,
                "chars": [ch],
            })
        elif "imagen" not in ins:
            raise SystemExit(f"'{ins['id']}' tiene solo_icono pero no imagen")
        icono = None
        if "imagen" in ins:
            ch_ico = chr(int(ins["char_icono"], 16))
            if ch_ico in usados:
                raise SystemExit(f"El char_icono {ins['char_icono']} de '{ins['id']}' ya lo usa el pack")
            icono = cargar_icono(AQUI / ins["imagen"], quitar_fondo=ins.get("quitar_fondo", True))
            icono.save(carpeta / f"{ins['id']}-logo.png")
            fuente["providers"].append({
                "type": "bitmap",
                "file": f"minecraft:{TEXTURAS}/{ins['id']}-logo.png",
                "ascent": 8,
                "height": 9,
                "chars": [ch_ico],
            })
        previas.append((ins, img, icono))

    iconos = []
    for nombre, (cp, colores, filas) in ICONOS.items():
        ch = chr(int(cp, 16))
        if ch in usados or cp in chars:
            raise SystemExit(f"El char {cp} del icono '{nombre}' ya esta en uso")
        img = dibujar_icono(colores, filas)
        img.save(carpeta / f"icono-{nombre}.png")
        fuente["providers"].append({
            "type": "bitmap",
            "file": f"minecraft:{TEXTURAS}/icono-{nombre}.png",
            "ascent": 7,
            "height": 8,
            "chars": [ch],
        })
        iconos.append(img)

    numeros = []
    for n in range(1, 11):
        ch = chr(NUMERO_BASE + n)
        if ch in usados:
            raise SystemExit(f"El char {NUMERO_BASE + n:X} del numero {n} ya esta en uso")
        img = dibujar_numero(n)
        img.save(carpeta / f"numero-{n}.png")
        fuente["providers"].append({
            "type": "bitmap",
            "file": f"minecraft:{TEXTURAS}/numero-{n}.png",
            "ascent": 10,
            "height": 20,
            "chars": [ch],
        })
        numeros.append(img)

    comandos_items = agregar_items(destino)
    agregar_anuncio(destino)
    # Bossbar blanca invisible: el contador la usa para mostrar solo el texto, sin barra.
    # Las demas colores (las de otros plugins) siguen normales.
    sprites = destino / "assets/minecraft/textures/gui/sprites/boss_bar"
    sprites.mkdir(parents=True, exist_ok=True)
    for nombre in ("white_background", "white_progress"):
        Image.new("RGBA", (182, 5), (0, 0, 0, 0)).save(sprites / f"{nombre}.png")

    fuente_path.parent.mkdir(parents=True, exist_ok=True)
    fuente_path.write_text(json.dumps(fuente, ensure_ascii=True, indent=2), encoding="utf-8")

    meta_path = destino / "pack.mcmeta"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    desc = meta["pack"].get("description", "")
    if isinstance(desc, str) and FIRMA not in desc:
        meta["pack"]["description"] = desc + FIRMA
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    zip_path = SALIDA / "pack-servidor.zip"
    # Fecha fija en cada entrada: si el contenido no cambia, el SHA1 tampoco,
    # y no hace falta volver a subir el pack solo por regenerarlo.
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(destino.rglob("*")):
            if f.is_file():
                info = zipfile.ZipInfo(f.relative_to(destino).as_posix(), date_time=(2024, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, f.read_bytes())
    sha1 = hashlib.sha1(zip_path.read_bytes()).hexdigest()
    (SALIDA / "sha1.txt").write_text(sha1 + "\n", encoding="utf-8")

    vista_previa(previas, SALIDA / "vista-previa.png")
    vista_previa([(None, i, None) for i in iconos], SALIDA / "vista-iconos.png")
    fila = Image.new("RGBA", (sum(i.width + 2 for i in numeros) + 4, numeros[0].height + 4), (24, 24, 28, 255))
    x = 2
    for img in reversed(numeros):
        fila.alpha_composite(img, (x, 2))
        x += img.width + 2
    fila.resize((fila.width * 6, fila.height * 6), Image.NEAREST).save(SALIDA / "vista-numeros.png")

    # LuckPerms no entiende \uXXXX: los comandos llevan el caracter real, para copiar y pegar.
    lineas = []
    for ins in insignias:
        ch = "" if ins.get("solo_icono") else chr(int(ins["char"], 16))
        if "imagen" in ins:
            ch = chr(int(ins["char_icono"], 16)) + ch
        # Los & van antes de la insignia; &r evita que el color tina el nombre.
        if ins.get("antes"):
            ch = ins["antes"] + "&r" + ch
        prio = ins.get("prioridad", 100 if ins["tipo"] == "rango" else 10)
        # creategroup no hace nada si el grupo ya existe. Despues se borra el prefijo/sufijo
        # viejo para que no gane uno anterior con mas prioridad.
        if ins["id"] != "default":
            lineas.append(f'lp creategroup {ins["id"]}')
        if ins["tipo"] == "rango":
            lineas.append(f'lp group {ins["id"]} meta clear prefix')
            lineas.append(f'lp group {ins["id"]} meta setprefix {prio} "{ch} "')
        else:
            # Los teams solo llevan sufijo: se borra cualquier prefijo viejo tipo "[LASFARK]".
            lineas.append(f'lp group {ins["id"]} meta clear prefix')
            lineas.append(f'lp group {ins["id"]} meta clear suffix')
            lineas.append(f'lp group {ins["id"]} meta setsuffix {prio} " {ch}"')
        for jugador in ins.get("miembros", []):
            lineas.append(f'lp user {jugador} parent add {ins["id"]}')
        lineas.append("")
    (SALIDA / "comandos-luckperms.txt").write_text("\n".join(lineas) + "\n", encoding="utf-8")

    (SALIDA / "comandos-items.txt").write_text("\n".join(comandos_items) + "\n", encoding="utf-8")

    print(f"Pack: {zip_path}")
    print(f"SHA1: {sha1}")
    print(f"Comandos: {SALIDA / 'comandos-luckperms.txt'}")


def vista_previa(previas, ruta):
    """Muestra cada insignia (y su logo) sobre fondo oscuro, a escala 4x como en el juego con GUI grande."""
    esc = ICONO_ALTO // 9
    margen, sep = 6 * esc, 4 * esc
    filas = []
    for _, img, icono in previas:
        grande = img.resize((img.width * esc, img.height * esc), Image.NEAREST) if img else None
        ancho_ico = icono.width + esc if icono else 0
        fila = Image.new("RGBA", (ancho_ico + (grande.width if grande else 0), ICONO_ALTO), (0, 0, 0, 0))
        if icono:
            fila.alpha_composite(icono, (0, 0))
        if grande:
            fila.alpha_composite(grande, (ancho_ico, 0))
        filas.append(fila)
    ancho = max(f.width for f in filas) + margen * 2
    alto = sum(f.height + sep for f in filas) - sep + margen * 2
    lienzo = Image.new("RGBA", (ancho, alto), (24, 24, 28, 255))
    y = margen
    for f in filas:
        lienzo.alpha_composite(f, (margen, y))
        y += f.height + sep
    lienzo.save(ruta)


if __name__ == "__main__":
    main()
