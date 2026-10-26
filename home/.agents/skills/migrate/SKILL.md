---
name: migrate
description: Mueve la sesión actual de Claude Code a otro host propio (por Tailscale/SSH) y la retoma allá con todo su contexto, para poder apagar esta máquina. Usar cuando el usuario diga "migra la sesión a <host>", "/migrate <host>", "hop a <host>", "sigue en el servidor" o "quiero apagar el PC y que continúe en otro lado".
---

# /migrate <host>

Copia el código y el transcript de esta sesión a `<host>`, arranca allá
`claude --resume <id>` dentro de tmux (o herdr) con Remote Control, y le pasa
un prompt para que prepare el entorno y siga con la tarea.

Script: `~/.claude/skills/migrate/migrate.sh`. Tests de la lógica local: `test.sh`.

## Pasos

1. **Dry-run primero, siempre.** Ejecuta desde el directorio de trabajo de la sesión:
   ```bash
   bash ~/.claude/skills/migrate/migrate.sh <host> --dry-run [flags]
   ```
   Hace el chequeo previo real en el host (Claude instalado y con login, tmux/herdr,
   git, rsync, mismo `$HOME`) y muestra el plan sin copiar nada. Si falla, explica al
   usuario qué falta en el host y detente.

2. **Elige los flags según la sesión:**
   | Situación | Flag |
   |---|---|
   | El directorio es `$HOME` o la tarea no tiene código | `--no-code` |
   | Repo git con `origin` (por defecto `auto` usa git) | `--via git`: hace `git push` de la rama actual; en el host clona con `gh` (o git) o hace pull, y copia aparte lo no commiteado |
   | Sin repo, o no quieres pushear | `--via sync`: rsync si ambos lados lo tienen, si no tar por SSH; excluye `node_modules`, `.venv`, builds |
   | La tarea necesita los `.env` | `--with-env` (por defecto no viajan) |
   | Prefieres herdr a tmux | `--mux herdr` (experimental) |
   | Sin Remote Control | `--no-rc` |

3. **Confirma con el usuario** mostrando el plan. Pide confirmación explícita si
   habrá `git push` o si se copian `.env`: ambos sacan cosas de esta máquina.

4. **Ejecuta sin `--dry-run`** y muestra al usuario la salida, incluidas las
   últimas líneas de la terminal remota y los comandos para conectarse.

5. **Deja de trabajar aquí.** No sigas con la tarea en esta máquina ni la vuelvas a
   abrir con `--resume`: dos instancias sobre la misma sesión se desincronizan. Lo
   último que escribas en esta sesión después de copiar el transcript no llega al
   host; por eso la migración es el último paso del turno.

## En el host destino

El agente retomado recibe un prompt que le pide confirmar carpeta y código,
instalar dependencias que falten, avisar de secretos o servicios faltantes sin
inventarlos, y seguir con la tarea. Para volver, se usa la misma skill desde el
host: `/migrate <esta-máquina>`.

## Requisitos del host (una vez)

- Tailscale con SSH (`sudo tailscale up --ssh`) o SSH normal. Fuerza el comando con
  `MIGRATE_SSH="ssh -p 2222"` si hace falta.
- Claude Code instalado y con login (`claude`, o `CLAUDE_CODE_OAUTH_TOKEN` de
  `claude setup-token`). La cuenta del host es la suya; las credenciales no se copian.
- tmux. Opcionales: `gh` con `gh auth login`, rsync, herdr.
- Mismo usuario y `$HOME` que el origen (el transcript guarda rutas absolutas).
- MCPs, skills y settings vienen de este repo (`bootstrap.sh`), no de la migración.

## Límites conocidos (marcados `ponytail:` en el script)

- No reescribe rutas si el `$HOME` remoto es distinto; aborta.
- En `--via git`, los archivos borrados localmente no se borran en el host.
- `--mux herdr` levanta el servidor de herdr dentro de un tmux si no está corriendo.
