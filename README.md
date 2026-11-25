# Agent Harness

Snapshot portable y reproducible de mi harness de Claude Code y Pi. Un `git clone` y
un `./bootstrap.sh` dejan una máquina nueva configurada para ambos.

**Repositorio privado.** Contiene configuración personal, memoria del agente y
la postura de seguridad completa (hooks y permisos). No hacer público.

## Qué contiene

```
home/.claude/
  settings.json     configuración activa (portable; sin mcpServers, ver abajo)
  AGENTS.md         instrucciones globales mínimas (de ecc-daily/)
  agents/           23 agentes de ECC de uso diario
  commands/         17 comandos de ECC de uso diario
  skills/           30 skills de ECC de uso diario + 43 skills propias
  skills-library/ agents-library/ commands-library/
                    el resto de ECC (268 skills, 45 agentes, 77 comandos); Claude Code no los carga
  scripts/ hooks/   runtime de hooks (ECC)
  rules/ecc/        reglas ECC que se conservan + simplicity.md (propia)
  rules/nicol/      convenciones propias
  ecc/              install-state.json — manifiesto de lo que ECC gestiona
  memory/           memoria persistente del agente
home/.agents/skills/  skills propias (destino real de los symlinks de skills/)
home/.pi/agent/       settings.json y extensiones de Pi (sin deviceId ni credenciales)
prune-ecc.sh        recorta ECC a lo diario (lo ejecuta bootstrap.sh)
ecc-daily/          listas del conjunto diario y versiones recortadas de AGENTS.md y reglas
docs/               auditoría de ECC y sus fundamentos
```

Las skills propias van como symlinks relativos hacia `.agents/skills`, así que
resuelven solas dentro del repo y tras el bootstrap.

## Instalar en una máquina nueva

```bash
git clone git@github.com:Deneros/agent-harness.git
cd agent-harness
./bootstrap.sh      # Linux, macOS, WSL
claude login        # las credenciales nunca se sincronizan
# Pi usa su autenticación local; vuelve a autenticarte en cada máquina si hace falta.
```

El bootstrap es idempotente: respalda lo que va a pisar en
`~/.claude-backup-<timestamp>` antes de escribir, instala `settings.json`
conservando el `mcpServers` local y termina ejecutando `prune-ecc.sh`.

Windows nativo: `install.ps1` (port sin probar; en WSL usar `bootstrap.sh`).

## Sincronizar cambios desde una máquina

```bash
./update.sh         # copia el harness vivo al repo
git add -A && git commit -m "chore: sync desde <máquina>" && git push
```

## Recorte de ECC y bloque `env`

Resultado de la auditoría `docs/auditoria-ecc-2026-11-25.md` (ECC 2.2.3).

**Bloque `env` de `settings.json`.** Desactiva hooks de ECC sin valor medible sin
editar el arreglo `hooks` (una reinstalación de ECC los volvería a insertar, el
`env` no lo toca): `ECC_DISABLED_HOOKS` (20 ids: GateGuard de Edit/Write,
observe, governance, mcp-health, command-log, quality-gate, session-end y
otros), `GATEGUARD_BASH_ROUTINE_DISABLED=1`, `ECC_SESSION_START_CONTEXT=off` y
`ECC_CONTEXT_MONITOR_COST_WARNINGS=off`. Se conservan `block-no-verify`, el
chequeo destructivo de GateGuard, `config-protection`, `ecc-metrics-bridge`,
`ecc-context-monitor`, `cost-tracker`, plan-canvas, `session:end:marker` y los
hooks de impeccable. `permissions.deny` bloquea `git push --force`, `-f` y
`rm -rf` de `/` y `~` (coincidencia exacta: un prefijo bloquearía cualquier
`rm -rf /ruta`).

**`prune-ecc.sh`.** Mueve a `skills-library/`, `agents-library/` y
`commands-library/` todo lo que `ecc/install-state.json` marca como gestionado
por ECC y no figura en `ecc-daily/{skills,agents,commands}.txt`; borra reglas ECC
que chocan con `rules/nicol`; sustituye `AGENTS.md` y recorta
`rules/ecc/common/{agents,code-review}.md`. Es idempotente y nunca toca las
skills propias (no están en `install-state.json`). **Repetirlo tras cualquier
reinstalación o `repair` de ECC.**

**Reactivar algo.** La biblioteca no se carga, pero está en disco:

```bash
mv ~/.claude/skills-library/<nombre> ~/.claude/skills/        # skill
mv ~/.claude/agents-library/<nombre>.md ~/.claude/agents/      # agente
mv ~/.claude/commands-library/<nombre>.md ~/.claude/commands/  # comando
```

Sesión nueva para que lo vea. Para que `prune-ecc.sh` no lo vuelva a mover,
añadir el nombre a `ecc-daily/*.txt` y hacer commit. Para reactivar un hook,
quitar su id de `ECC_DISABLED_HOOKS`. Rollback completo: borrar el bloque `env`
(o dejar `ECC_DISABLED_HOOKS` vacío en `settings.local.json`) y
`mv ~/.claude/*-library/* ` a su carpeta.

## `mcpServers` no se versiona

`update.sh` quita `mcpServers` del `settings.json` del repo y `bootstrap.sh`
conserva el que ya exista en la máquina. Motivo: la URL de Artiforge lleva un
token (`pat=`) y no debe estar en git. En cada máquina, añadir Artiforge a mano
**sin escribir el token en el repo**:

```bash
claude mcp add --transport http --scope user Artiforge "https://tools.artiforge.ai/mcp?pat=$ARTIFORGE_PAT"
```

con `ARTIFORGE_PAT` exportado solo en esa shell (o pegado en el prompt), de modo
que quede en `~/.claude.json` local, fuera del repo. El token que estuvo en el
historial de git debe considerarse comprometido: rotarlo.

## Actualizar las otras máquinas (Acris, escritorio WSL, Arch)

```bash
cd ~/development/agent-harness     # o donde esté el clon
git pull && ./bootstrap.sh         # respalda en ~/.claude-backup-<fecha>
```

Verificación (sesión nueva de Claude Code):

```bash
python3 -c "import json,os;s=json.load(open(os.path.expanduser('~/.claude/settings.json')));print(s['env'].keys(), s['permissions']['deny'])"
echo $(ls ~/.claude/skills | wc -l) $(ls ~/.claude/agents | wc -l) $(ls ~/.claude/commands | wc -l)   # 73 23 17
ls ~/.claude/skills-library | wc -l                                                                    # 268
```

- El primer `ls` no debe mostrar "Fact-Forcing Gate"; un Edit de un archivo nuevo pasa.
- `rm -rf /tmp/prueba` y `git push --force` siguen pidiendo hechos o los rechaza el `deny`.
- Linux/WSL: los hooks resuelven la raíz por `~/.claude` (la ruta base64 está neutralizada).
- Si hay Artiforge en esa máquina, comprobar que `mcpServers` sigue en su `settings.json`.

`update.sh` borra con `rsync --delete`: ejecutarlo solo desde la máquina de
referencia, porque una máquina con menos skills de Codex/OpenCode las eliminaría
del repo.

## Qué queda fuera, y por qué

| Excluido | Motivo |
|---|---|
| `.credentials.json` | Tokens OAuth. Se regeneran con `claude login` |
| `projects/` (902 MB) | Transcripts de sesión. Solo viaja `memory/` |
| `plugins/` | Se reinstalan desde sus marketplaces vía `settings.json` |
| Logs, cachés, métricas, snapshots de shell | Estado local por máquina |

Overrides propios de una máquina: `~/.claude/settings.local.json`, ignorado por git.
Pi sincroniza únicamente `settings.json` sin `deviceId` y las extensiones propias;
`auth.json`, sesiones, paquetes descargados, cachés y modelos locales quedan fuera.

## Detalles de portabilidad

- `settings.json` no tiene rutas absolutas: `update.sh` neutraliza la ruta base64 de ECC 2.2.x y reescribe los comandos de impeccable a `$HOME`.
- `install-state.json` **sí** guarda rutas absolutas del `$HOME` de origen; `prune-ecc.sh` solo usa la parte posterior a `/.claude/` y `bootstrap.sh` las reescribe al `$HOME` local.
- La memoria vive bajo `projects/<slug>/`, donde el slug deriva del `$HOME`; el bootstrap lo recalcula.

## Terceros

ECC, ponytail y las skills de Emil Kowalski se incluyen bajo MIT. Ver [NOTICE.md](NOTICE.md).
