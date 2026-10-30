"""Eventos de ConditionalEvents para el ciclo de PvP, mostrado en el scoreboard de TAB.

Uso:
    python generar_pvp.py

Escribe salida/ce-pvp.yml: los eventos pvp_inicio, pvp_desactivado y pvp_activado. En vez de
una bossbar, cada 30 s guardan el estado y el tiempo en variables de ServerVariables
(pvp_on y pvp_tiempo), que TAB lee con %servervariables_globalvalue_...%.

by Heleon ST
"""
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SALIDA = AQUI / "salida"

DESACTIVADO_SEG = 10 * 60
ACTIVADO_SEG = 40 * 60
PASO = 30


def mmss(seg):
    return f"{seg // 60}:{seg % 60:02d}"


def ciclo(nombre, encendido, segundos, siguiente, gamerule, mensaje, sonido):
    lineas = [
        f"  {nombre}:",
        "    type: call",
        "    actions:",
        "      default:",
        f"      - 'console_command: gamerule minecraft:pvp {gamerule}'",
        f"      - 'console_command: svar set pvp_on {'si' if encendido else 'no'}'",
        f"      - 'to_all: json_message: {mensaje}'",
        f"      - 'console_command: execute as @a at @s run playsound {sonido}'",
    ]
    for restante in range(segundos, 0, -PASO):
        lineas.append(f"      - 'console_command: svar set pvp_tiempo {mmss(restante)}'")
        lineas.append(f"      - 'wait: {PASO}'")
    lineas.append(f"      - 'call_event: {siguiente}'")
    return lineas


def main():
    texto = [
        "# Ciclo de PvP para ConditionalEvents (generado por generar_pvp.py, by Heleon ST).",
        "# Reemplaza tus eventos pvp_inicio, pvp_barra_join, pvp_desactivado y pvp_activado por estos.",
        "Events:",
        "  pvp_inicio:",
        "    type: server_start",
        "    actions:",
        "      default:",
        "      - 'console_command: bossbar remove pvp:estado'",
        "      - 'call_event: pvp_desactivado'",
    ]
    texto += ciclo("pvp_desactivado", False, DESACTIVADO_SEG, "pvp_activado", "false",
                   '{"text":"El PVP se ha DESACTIVADO","color":"green","bold":true}',
                   "minecraft:block.beacon.deactivate master @s ~ ~ ~ 1 1")
    texto += ciclo("pvp_activado", True, ACTIVADO_SEG, "pvp_desactivado", "true",
                   '{"text":"El PVP se ha ACTIVADO","color":"red","bold":true}',
                   "minecraft:entity.wither.spawn master @s ~ ~ ~ 0.6 1.5")
    SALIDA.mkdir(exist_ok=True)
    (SALIDA / "ce-pvp.yml").write_text("\n".join(texto) + "\n", encoding="utf-8")
    print(f"Eventos: {SALIDA / 'ce-pvp.yml'} ({len(texto)} lineas)")


if __name__ == "__main__":
    main()
