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
# Glifos del resource pack (generar.py): numeros grandes 1-10 y el icono de reloj.
NUMERO_BASE = 0xEC00
RELOJ = ""

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
    """Cuenta regresiva configurable: bossbar con m:ss que se vacia y los ultimos 10 s con numeros grandes."""
    sc = "heleon_contador"
    def obj(nombre, color=None):
        estilo = f',"color":"{color}","bold":true' if color else ""
        return f'{{"score":{{"name":"{nombre}","objective":"{sc}"}}{estilo}}}'
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
            "schedule clear heleon:contador/ocultar",
            f"$scoreboard players set #n {sc} $(segundos)",
            f"$scoreboard players set #total {sc} $(segundos)",
            f"scoreboard players set #60 {sc} 60",
            f"scoreboard players set #100 {sc} 100",
            'bossbar add heleon:contador ""',
            "$bossbar set heleon:contador max $(segundos)",
            "bossbar set heleon:contador style progress",
            "bossbar set heleon:contador visible true",
            "title @a times 0 25 5",
            "function heleon:contador/tick",
        ]) + "\n",
        f + "tick.mcfunction": "\n".join([
            "# Bossbar: se vacia y pasa de verde a amarillo a rojo",
            "bossbar set heleon:contador players @a",
            f"execute store result bossbar heleon:contador value run scoreboard players get #n {sc}",
            f"scoreboard players operation #pct {sc} = #n {sc}",
            f"scoreboard players operation #pct {sc} *= #100 {sc}",
            f"scoreboard players operation #pct {sc} /= #total {sc}",
            f"execute if score #pct {sc} matches 51.. run bossbar set heleon:contador color green",
            f"execute if score #pct {sc} matches 21..50 run bossbar set heleon:contador color yellow",
            f"execute if score #pct {sc} matches ..20 run bossbar set heleon:contador color red",
            f"scoreboard players operation #min {sc} = #n {sc}",
            f"scoreboard players operation #min {sc} /= #60 {sc}",
            f"scoreboard players operation #seg {sc} = #n {sc}",
            f"scoreboard players operation #seg {sc} %= #60 {sc}",
            f'execute if score #seg {sc} matches 10.. run bossbar set heleon:contador name [{{"text":"{RELOJ} ","color":"white"}},{{"text":"Tiempo  ","color":"gray"}},{obj("#min", "white")},{{"text":":","color":"white","bold":true}},{obj("#seg", "white")}]',
            f'execute if score #seg {sc} matches ..9 run bossbar set heleon:contador name [{{"text":"{RELOJ} ","color":"white"}},{{"text":"Tiempo  ","color":"gray"}},{obj("#min", "white")},{{"text":":0","color":"white","bold":true}},{obj("#seg", "white")}]',
            f"execute if score #n {sc} matches 11.. if score #seg {sc} matches 0 as @a at @s run playsound minecraft:block.note_block.hat master @s ~ ~ ~ 1 1",
            "# Ultimos 10 s: numeros grandes del pack y un pling que sube de tono",
        ] + [
            f"execute if score #n {sc} matches {n} run title @a title {json.dumps(chr(NUMERO_BASE + n), ensure_ascii=False)}"
            for n in range(10, 0, -1)
        ] + [
            f"execute if score #n {sc} matches {n} as @a at @s run playsound minecraft:block.note_block.pling master @s ~ ~ ~ 1 {0.7 + (10 - n) * 0.13:.2f}"
            for n in range(10, 0, -1)
        ] + [
            f"scoreboard players remove #n {sc} 1",
            f"execute if score #n {sc} matches 1.. run schedule function heleon:contador/tick 1s",
            f"execute if score #n {sc} matches ..0 run schedule function heleon:contador/fin 1s",
        ]) + "\n",
        f + "fin.mcfunction": "\n".join([
            "bossbar set heleon:contador value 0",
            "bossbar set heleon:contador color red",
            'bossbar set heleon:contador name {"nbt":"final","storage":"heleon:contador","color":"red","bold":true}',
            "title @a times 0 40 10",
            'title @a title {"nbt":"final","storage":"heleon:contador","color":"dark_red","bold":true}',
            "execute as @a at @s run playsound minecraft:entity.ender_dragon.growl master @s ~ ~ ~ 1 1",
            "execute as @a at @s run playsound minecraft:entity.firework_rocket.large_blast master @s ~ ~ ~ 1 1",
            "schedule function heleon:contador/ocultar 3s",
        ]) + "\n",
        f + "ocultar.mcfunction": "bossbar remove heleon:contador\n",
        f + "parar.mcfunction": "\n".join([
            "schedule clear heleon:contador/tick",
            "schedule clear heleon:contador/fin",
            "schedule clear heleon:contador/ocultar",
            "bossbar remove heleon:contador",
            "title @a clear",
        ]) + "\n",
    }


def anuncios():
    """Anuncios de anuncios.json: rotan solos cada X minutos desde que carga el datapack."""
    ruta = AQUI / "anuncios.json"
    if not ruta.exists():
        return {}
    cfg = json.loads(ruta.read_text(encoding="utf-8"))
    lista = cfg["anuncios"]
    segundos = int(cfg.get("cada_minutos", 5) * 60)
    sonido = cfg.get("sonido", "minecraft:block.note_block.chime")
    sc = "heleon_anuncio"
    f = f"data/{NS}/function/anuncios/"
    archivos = {}

    for i, a in enumerate(lista):
        partes = [
            "",
            {"text": "\n▬▬▬▬▬▬▬▬ ", "color": "dark_gray"},
            {"text": "✦ UPCSMP ✦", "color": "#3fd0ff", "bold": True},
            {"text": " ▬▬▬▬▬▬▬▬\n", "color": "dark_gray"},
            {"text": f"  » {a['titulo']}\n", "color": "gold", "bold": True},
        ]
        for linea in a.get("lineas", []):
            partes.append({"text": f"  {linea}\n", "color": "gray"})
        boton = a.get("boton")
        if boton:
            if "url" in boton:
                click = {"action": "open_url", "url": boton["url"]}
                ayuda = "Clic para abrir"
            else:
                click = {"action": "run_command", "command": boton["comando"].lstrip("/")}
                ayuda = f"Clic para usar /{boton['comando'].lstrip('/')}"
            partes.append({"text": f"  {boton['texto']}\n", "color": "aqua", "bold": True,
                           "click_event": click,
                           "hover_event": {"action": "show_text", "value": {"text": ayuda, "color": "gray"}}})
        partes.append({"text": "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n", "color": "dark_gray"})
        archivos[f + f"{i}.mcfunction"] = "\n".join([
            f"tellraw @a {json.dumps(partes, ensure_ascii=False)}",
            f"execute as @a at @s run playsound {sonido} master @s ~ ~ ~ 0.6 1.2",
        ]) + "\n"

    archivos[f + "iniciar.mcfunction"] = "\n".join([
        f"# Arranca solo al cargar el datapack. Un anuncio cada {segundos} s.",
        f"scoreboard objectives add {sc} dummy",
        f"scoreboard players set #total {sc} {len(lista)}",
        f"schedule function {NS}:anuncios/siguiente {segundos}s replace",
    ]) + "\n"
    archivos[f + "siguiente.mcfunction"] = "\n".join(
        [f"execute if score #n {sc} matches {i} run function {NS}:anuncios/{i}" for i in range(len(lista))] + [
            f"scoreboard players add #n {sc} 1",
            f"scoreboard players operation #n {sc} %= #total {sc}",
            f"schedule function {NS}:anuncios/siguiente {segundos}s replace",
        ]) + "\n"
    archivos[f + "parar.mcfunction"] = f"schedule clear {NS}:anuncios/siguiente\n"
    archivos["data/minecraft/tags/function/load.json"] = json.dumps(
        {"values": [f"{NS}:anuncios/iniciar"]}, indent=2) + "\n"
    return archivos


def anuncio_banner(segundos=8):
    """Banner en la esquina superior izquierda. Elige tamano por el largo del texto, se abre desde
    la izquierda, pasa un reflejo y queda en pantalla. Las medidas salen de salida/anuncio.json,
    que escribe generar.py junto con el resource pack."""
    meta_path = SALIDA / "anuncio.json"
    if not meta_path.exists():
        print("Aviso: falta salida/anuncio.json (corre primero generar.py); el anuncio no se incluye")
        return {}
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    f = f"data/{NS}/function/anuncio/"
    sc = "heleon_anuncio_largo"
    tope_letras = list(meta.values())[-1]["letras"]
    mostrar = [
        "# Uso: /function heleon:anuncio/mostrar {texto:\"¡EVENTO ESTE SÁBADO!\"}",
        "$data modify storage heleon:anuncio texto set value \"$(texto)\"",
        'data modify storage heleon:anuncio cola set value ""',
        f"scoreboard objectives add {sc} dummy",
        f"execute store result score #largo {sc} run data get storage heleon:anuncio texto",
        f"# Mas de {tope_letras} letras no caben en el banner mas grande: se corta y termina en ...",
        f"execute if score #largo {sc} matches {tope_letras + 1}.. run data modify storage heleon:anuncio cola set value \"...\"",
        f"execute if score #largo {sc} matches {tope_letras + 1}.. run data modify storage heleon:anuncio texto "
        f"set string storage heleon:anuncio texto 0 {tope_letras - 3}",
        f"execute if score #largo {sc} matches {tope_letras + 1}.. run scoreboard players set #largo {sc} {tope_letras}",
    ]
    archivos = {}
    tope = 0
    for clave, m in meta.items():
        rango = f"{tope + 1}..{m['letras']}" if clave != list(meta)[-1] else f"{tope + 1}.."
        tope = m["letras"]
        mostrar.append(f"execute if score #largo {sc} matches {rango} run function {NS}:anuncio/{clave}/0")
        glifo = lambda i: json.dumps([{"text": chr(m["base"] + i) + m["espacio_banner"], "font": f"{NS}:anuncio"}],
                                     ensure_ascii=False)
        subtitulo = json.dumps([{"nbt": "texto", "storage": "heleon:anuncio", "font": f"{NS}:anuncio_texto",
                                 "color": "#ffe9a8"},
                                {"nbt": "cola", "storage": "heleon:anuncio", "font": f"{NS}:anuncio_texto",
                                 "color": "#ffe9a8"},
                                {"text": m["espacio_texto"], "font": f"{NS}:anuncio_texto"}], ensure_ascii=False)
        for i in range(m["cuadros"]):
            lineas = []
            if i == 0:
                lineas += ["title @a times 0 3 0", 'title @a subtitle ""']
            if i == m["apertura"] - 1:
                # El texto aparece cuando el banner ya esta abierto del todo
                lineas.append(f"title @a subtitle {subtitulo}")
            if i == m["cuadros"] - 1:
                lineas.append(f"title @a times 0 {segundos * 20} 20")
            lineas.append(f"title @a title {glifo(i)}")
            if i < m["cuadros"] - 1:
                lineas.append(f"schedule function {NS}:anuncio/{clave}/{i + 1} 1t")
            archivos[f + f"{clave}/{i}.mcfunction"] = "\n".join(lineas) + "\n"
    mostrar.append(f"execute as @a at @s run playsound {NS}:anuncio master @s ~ ~ ~ 1 1")
    archivos[f + "mostrar.mcfunction"] = "\n".join(mostrar) + "\n"

    # Enlaces: el banner avisa y el chat lleva el enlace clicable (un /title no se puede clicar)
    def chat_enlace(texto_boton):
        return json.dumps(["",
            {"text": "\n▬▬▬▬▬▬▬▬ ", "color": "dark_gray"},
            {"text": "✦ UPCSMP ✦", "color": "#3fd0ff", "bold": True},
            {"text": " ▬▬▬▬▬▬▬▬\n", "color": "dark_gray"},
            {"text": f"  {texto_boton}\n", "color": "aqua", "bold": True, "underlined": True,
             "click_event": {"action": "open_url", "url": "$(url)"},
             "hover_event": {"action": "show_text", "value": {"text": "$(url)", "color": "gray"}}},
            {"text": "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n", "color": "dark_gray"}], ensure_ascii=False)
    archivos[f + "enlace.mcfunction"] = "\n".join([
        "# Uso: /function heleon:anuncio/enlace {url:\"https://...\"}",
        f"$tellraw @a {chat_enlace('[ Clic aquí para abrir el enlace ]')}",
        f"function {NS}:anuncio/mostrar {{texto:\"¡Nuevo enlace en el chat!\"}}",
    ]) + "\n"
    archivos[f + "enlace_con_texto.mcfunction"] = "\n".join([
        "# Uso: /function heleon:anuncio/enlace_con_texto {url:\"https://...\",texto:\"Fotos del evento\"}",
        f"$tellraw @a {chat_enlace('[ $(texto) ]')}",
        f"$function {NS}:anuncio/mostrar {{texto:\"$(texto)\"}}",
    ]) + "\n"
    return archivos


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    pack = Path(sys.argv[1])
    cuadros = leer_cuadros(pack)
    if not cuadros:
        raise SystemExit("No encontre cuadros de ruleta ni de muerte en el pack")

    archivos = funciones(cuadros)
    archivos.update(contador())
    archivos.update(anuncios())
    archivos.update(anuncio_banner())
    # Solo pack_format, como el datapack de Club Pala que si carga en el server: declarar
    # supported_formats + min/max_format a la vez puede hacer que el juego lo descarte.
    archivos["pack.mcmeta"] = json.dumps({"pack": {
        "description": "Animaciones de UPCSMP §8· by Heleon ST",
        "pack_format": 48,
    }}, indent=2, ensure_ascii=False) + "\n"

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
