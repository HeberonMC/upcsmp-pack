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
ICONO_ALTO = 36                     # px reales; en el juego mide 9, como las insignias

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
                    px[x0 + fx, 2 + fy] = (255, 255, 255, 255)
        x0 += len(filas[0]) + 1
    return img


def cargar_icono(ruta, alto=ICONO_ALTO):
    """Logo con fondo blanco -> transparente, recortado y escalado a alta resolucion."""
    img = Image.open(ruta).convert("RGBA")
    px = img.load()
    for y in range(img.height):
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
    if carpeta.exists():
        shutil.rmtree(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)

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
            icono = cargar_icono(AQUI / ins["imagen"])
            icono.save(carpeta / f"{ins['id']}-logo.png")
            fuente["providers"].append({
                "type": "bitmap",
                "file": f"minecraft:{TEXTURAS}/{ins['id']}-logo.png",
                "ascent": 8,
                "height": 9,
                "chars": [ch_ico],
            })
        previas.append((ins, img, icono))

    fuente_path.parent.mkdir(parents=True, exist_ok=True)
    fuente_path.write_text(json.dumps(fuente, ensure_ascii=True, indent=2), encoding="utf-8")

    meta_path = destino / "pack.mcmeta"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    desc = meta["pack"].get("description", "")
    if isinstance(desc, str) and FIRMA not in desc:
        meta["pack"]["description"] = desc + FIRMA
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    zip_path = SALIDA / "pack-servidor.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(destino.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(destino).as_posix())
    sha1 = hashlib.sha1(zip_path.read_bytes()).hexdigest()
    (SALIDA / "sha1.txt").write_text(sha1 + "\n", encoding="utf-8")

    vista_previa(previas, SALIDA / "vista-previa.png")

    # LuckPerms no entiende \uXXXX: los comandos llevan el caracter real, para copiar y pegar.
    lineas = []
    for ins in insignias:
        ch = "" if ins.get("solo_icono") else chr(int(ins["char"], 16))
        if "imagen" in ins:
            ch = chr(int(ins["char_icono"], 16)) + ch
        prio = ins.get("prioridad", 100 if ins["tipo"] == "rango" else 10)
        # Primero se borra el prefijo/sufijo viejo para que no gane uno anterior con mas prioridad.
        if ins["tipo"] == "rango":
            lineas.append(f'lp group {ins["id"]} meta clear prefix')
            lineas.append(f'lp group {ins["id"]} meta setprefix {prio} "{ch} "')
        else:
            lineas.append(f'lp group {ins["id"]} meta clear suffix')
            lineas.append(f'lp group {ins["id"]} meta setsuffix {prio} " {ch}"')
    (SALIDA / "comandos-luckperms.txt").write_text("\n".join(lineas) + "\n", encoding="utf-8")

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
