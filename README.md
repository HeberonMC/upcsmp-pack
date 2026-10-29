# UPCSMP · Resource pack

Insignias de rangos y teams para el chat, TAB y el scoreboard de UPCSMP, sobre el pack de animaciones de DEDsafío 3 (By Club Pala).

El pack listo para el server está en [Releases](../../releases). Cada versión trae su enlace de descarga directa y su SHA1 para `server.properties`.

## Generar una versión nueva

1. Edita `rangos.json` (texto, color, logo opcional en `logos/`).
2. `python generar.py "<carpeta del pack base>"`
3. Sube `salida/pack-servidor.zip` como release nueva y copia el SHA1 de `salida/sha1.txt`.

Los comandos de LuckPerms quedan en `salida/comandos-luckperms.txt`; la config de TAB está en `tab-config.yml`.

<sub>by Heleon ST</sub>
