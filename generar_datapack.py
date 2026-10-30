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


def contador():
    """Cuenta regresiva configurable: mas de 10 s en el actionbar (m:ss), los ultimos 10 en grande."""
    sc = "heleon_contador"
    obj = lambda nombre: f'{{"score":{{"name":"{nombre}","objective":"{sc}"}}}}'
    f = f"data/{NS}/function/contador/"
    return {
        f + "iniciar.mcfunction": "\n".join([
            "# Uso: /function heleon:contador/iniciar {segundos:30}",
            "data modify storage heleon:contador final set value \"¡YA!\"",
            "$function heleon:contador/arrancar {segundos:$(segundos)}",
        ]) + "\n",
        f + "iniciar_con_texto.mcfunction": "\n".join([
            "# Uso: /function heleon:contador/iniciar_con_texto {segundos:30,final:\"¡PELEA!\"}",
            "$data modify storage heleon:contador final set value \"$(final)\"",
            "$function heleon:contador/arrancar {segundos:$(segundos)}",
        ]) + "\n",
        f + "arrancar.mcfunction": "\n".join([
            f"scoreboard objectives add {sc} dummy",
            "schedule clear heleon:contador/tick",
            "schedule clear heleon:contador/fin",
            f"$scoreboard players set #n {sc} $(segundos)",
            f"scoreboard players set #60 {sc} 60",
            "title @a times 0 25 5",
            "function heleon:contador/tick",
        ]) + "\n",
        f + "tick.mcfunction": "\n".join([
            "# Mas de 10 s: actionbar con minutos:segundos",
            f"scoreboard players operation #min {sc} = #n {sc}",
            f"scoreboard players operation #min {sc} /= #60 {sc}",
            f"scoreboard players operation #seg {sc} = #n {sc}",
            f"scoreboard players operation #seg {sc} %= #60 {sc}",
            f'execute if score #n {sc} matches 11.. if score #seg {sc} matches 10.. run title @a actionbar [{{"text":"Tiempo ","color":"yellow"}},{obj("#min")},{{"text":":"}},{obj("#seg")}]',
            f'execute if score #n {sc} matches 11.. if score #seg {sc} matches ..9 run title @a actionbar [{{"text":"Tiempo ","color":"yellow"}},{obj("#min")},{{"text":":0"}},{obj("#seg")}]',
            f"execute if score #n {sc} matches 11.. if score #seg {sc} matches 0 as @a at @s run playsound minecraft:block.note_block.hat master @s ~ ~ ~ 1 1",
            "# Ultimos 10 s: numero grande con sonido",
            f'execute if score #n {sc} matches 6..10 run title @a title {{"score":{{"name":"#n","objective":"{sc}"}},"color":"gold","bold":true}}',
            f'execute if score #n {sc} matches ..5 run title @a title {{"score":{{"name":"#n","objective":"{sc}"}},"color":"red","bold":true}}',
            f"execute if score #n {sc} matches ..10 as @a at @s run playsound minecraft:block.note_block.pling master @s ~ ~ ~ 1 1",
            f"scoreboard players remove #n {sc} 1",
            f"execute if score #n {sc} matches 1.. run schedule function heleon:contador/tick 1s",
            f"execute if score #n {sc} matches ..0 run schedule function heleon:contador/fin 1s",
        ]) + "\n",
        f + "fin.mcfunction": "\n".join([
            "title @a times 0 40 10",
            'title @a title {"nbt":"final","storage":"heleon:contador","color":"dark_red","bold":true}',
            "execute as @a at @s run playsound minecraft:entity.ender_dragon.growl master @s ~ ~ ~ 1 1",
        ]) + "\n",
        f + "parar.mcfunction": "\n".join([
            "schedule clear heleon:contador/tick",
            "schedule clear heleon:contador/fin",
            "title @a clear",
            'title @a actionbar ""',
        ]) + "\n",
    }


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    pack = Path(sys.argv[1])
    cuadros = leer_cuadros(pack)
    if not cuadros:
        raise SystemExit("No encontre cuadros de ruleta ni de muerte en el pack")

    archivos = funciones(cuadros)
    archivos.update(contador())
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
    print(f"  /function {NS}:contador/iniciar {{segundos:30}}")
    print(f'  /function {NS}:contador/iniciar_con_texto {{segundos:30,final:"¡PELEA!"}}')
    print(f"  /function {NS}:contador/parar")


if __name__ == "__main__":
    main()
