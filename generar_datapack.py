"""Datapack para reproducir las animaciones del pack (ruleta y muerte) con /function.

Uso:
    python generar_datapack.py "C:\\ruta\\al\\pack\\extraido"

Lee los cuadros de assets/minecraft/font/default.json y crea una funcion por cuadro
que muestra el glifo como /title y programa el siguiente para el tick siguiente.
Deja salida/heleon-animaciones.zip listo para copiar a world/datapacks/.

by Heleon ST
"""
import json
import re
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SALIDA = AQUI / "salida"
NS = "heleon"
FECHA = (2024, 1, 1, 0, 0, 0)

ANIMACIONES = {
    # nombre de la animacion -> (regex sobre el archivo del glifo, sonido)
    "ruleta": (re.compile(r"cpala-dedsafio3-ruleta/([a-z]+)/\1-(\d+)\.png$"), "cpaladeds3:ruleta"),
    "muerte": (re.compile(r"cpala-dedsafio3-(muerte)/muerte-(\d+)\.png$"), "cpaladeds3:muerte"),
}


def leer_cuadros(pack):
    fuente = json.loads((pack / "assets/minecraft/font/default.json").read_text(encoding="utf-8"))
    cuadros = defaultdict(lambda: defaultdict(list))   # animacion -> variante -> [(n, char)]
    for p in fuente["providers"]:
        archivo = p.get("file", "")
        for anim, (rx, _) in ANIMACIONES.items():
            m = rx.search(archivo)
            if m:
                cuadros[anim][m.group(1)].append((int(m.group(2)), p["chars"][0]))
    for variantes in cuadros.values():
        for lista in variantes.values():
            lista.sort()
    return cuadros


def funciones(cuadros):
    """Devuelve {ruta dentro del datapack: contenido}."""
    archivos = {}

    def agregar(ruta, lineas):
        archivos[f"data/{NS}/function/{ruta}.mcfunction"] = "\n".join(lineas) + "\n"

    for anim, variantes in cuadros.items():
        sonido = ANIMACIONES[anim][1]
        for variante, lista in variantes.items():
            base = anim if anim == variante else f"{anim}/{variante}"
            agregar(base if anim != variante else anim, [
                f"# {base}: {len(lista)} cuadros, 1 por tick",
                "title @a times 0 3 0",
                f"execute as @a at @s run playsound {sonido} master @s ~ ~ ~ 1 1",
                f"function {NS}:{anim}/cuadros/{variante}/1",
            ])
            for i, (_, ch) in enumerate(lista, start=1):
                lineas = []
                ultimo = i == len(lista)
                if ultimo:
                    # El resultado de la ruleta se queda 2 segundos en pantalla.
                    lineas.append("title @a times 0 40 10")
                lineas.append(f"title @a title {json.dumps(ch, ensure_ascii=False)}")
                if not ultimo:
                    lineas.append(f"schedule function {NS}:{anim}/cuadros/{variante}/{i + 1} 1t")
                agregar(f"{anim}/cuadros/{variante}/{i}", lineas)

    colores = sorted(cuadros.get("ruleta", {}))
    if colores:
        lineas = [
            "# Ruleta con color al azar",
            "scoreboard objectives add heleon_ruleta dummy",
            f"execute store result score #r heleon_ruleta run random value 0..{len(colores) - 1}",
        ]
        for n, color in enumerate(colores):
            lineas.append(f"execute if score #r heleon_ruleta matches {n} run function {NS}:ruleta/{color}")
        agregar("ruleta/azar", lineas)
    return archivos


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    pack = Path(sys.argv[1])
    cuadros = leer_cuadros(pack)
    if not cuadros:
        raise SystemExit("No encontre cuadros de ruleta ni de muerte en el pack")

    archivos = funciones(cuadros)
    archivos["pack.mcmeta"] = json.dumps({"pack": {
        "description": "Animaciones de UPCSMP §8· by Heleon ST",
        "pack_format": 48,
        "supported_formats": [48, 120],
        "min_format": 48,
        "max_format": 120,
    }}, indent=2) + "\n"

    SALIDA.mkdir(exist_ok=True)
    zip_path = SALIDA / "heleon-animaciones.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for ruta in sorted(archivos):
            info = zipfile.ZipInfo(ruta, date_time=FECHA)
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, archivos[ruta].encode("utf-8"))

    print(f"Datapack: {zip_path}")
    for anim, variantes in cuadros.items():
        for variante, lista in sorted(variantes.items()):
            nombre = anim if anim == variante else f"{anim}/{variante}"
            print(f"  /function {NS}:{nombre}   ({len(lista)} cuadros, {len(lista) / 20:.1f} s)")
    if "ruleta" in cuadros:
        print(f"  /function {NS}:ruleta/azar   (color al azar)")


if __name__ == "__main__":
    main()
