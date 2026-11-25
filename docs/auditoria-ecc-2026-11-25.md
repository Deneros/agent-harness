# Auditoria de ECC 2.2.3 en el harness de Nicolas

Fecha: 2026-11-24 (datos hasta 2026-11-25 03:29 UTC). Solo lectura: no se cambio
ninguna configuracion; las pruebas de hooks se hicieron con `HOME` y
`GATEGUARD_STATE_DIR` temporales. No hay commit.

Fuentes: `~/.claude/settings.json`, `scripts/hooks/*.js` (codigo leido, no
supuesto), `rules/`, `agents/`, `commands/`, `skills/`, `ecc/install-state.json`,
`~/.ecc-src` (clon local de ECC, version 2.0.0, solo para leer manifiestos),
`~/development/agent-harness`, y 235 transcripts (57 de sesion y 178 de
subagentes) entre 2026-10-23 y 2026-11-25 (33 dias) en 4 carpetas de proyecto.
En el informe solo hay conteos; no se copio contenido de conversaciones.

---

## 1. Resumen de una pagina

**Veredicto.** ECC esta instalado en perfil `full` (28 modulos, 298 skills, 94
comandos, 68 agentes, 27 entradas de hook). En 33 dias de uso real se invocaron 5
skills y 13 agentes de ECC (de 183 llamadas a Agent, 143 fueron `general-purpose`).
ECC aporta poco valor medible y cuesta contexto y friccion en cada sesion.

**Desactivar (recomendado, en orden de retorno):**

1. GateGuard de **Edit/Write** (`pre:edit-write:gateguard-fact-force`): 118
   bloqueos, 18,5 % de todos los Edit/Write. En ~80 % de los casos el agente
   reintento el mismo archivo sin hacer ninguna lectura intermedia.
2. GateGuard **rutinario de Bash** (`GATEGUARD_BASH_ROUTINE_DISABLED=1`): 68
   bloqueos, uno por sesion (29 % de los 235 transcripts empiezan con un turno
   perdido). Es la unica variable que lo apaga sin quitar el chequeo destructivo.
3. Contexto inyectado: listado de skills/comandos (48,8 KB, ~12k tokens) y de
   agentes (30 KB, ~7,5k tokens) por sesion; 36,9 KB de reglas y `AGENTS.md` de ECC
   (~9k tokens) que duplican o contradicen las reglas `nicol`; resumen de sesion
   previa de SessionStart (~4,3 KB, ~1,1k tokens, 43 veces).
4. Hooks sin efecto observable: `pre:observe`/`post:observe` (el observer esta
   `enabled:false`), `governance-capture` (sale sin hacer nada si no existe
   `ECC_GOVERNANCE_CAPTURE=1`), `mcp-health-check` (no sondea los conectores de
   claude.ai), `auto-tmux-dev` (tmux no esta instalado), `suggest-compact` (31
   avisos en una ventana de 1M), `session-activity-tracker` (sin consumidor),
   `command-log-*` (59 MB de logs en claro, sin rotacion), `quality-gate`,
   `stop:format-typecheck`, `evaluate-session`, `design-quality-check`.

**Conservar:** `block-no-verify` (protege los pre-commit de mrh-backend),
`config-protection` (impide debilitar eslint/biome/ruff), el chequeo
**destructivo** de GateGuard (unico freno a `git push --force`, `reset --hard`,
`rm -rf` mientras `skipDangerousModePermissionPrompt` esta en `true`),
`ecc-metrics-bridge` + `ecc-context-monitor` (aviso de bucle) sin avisos de
costo, `cost-tracker`, los hooks de `impeccable` (propios) y plan-canvas.

**Ahorro estimado por sesion.**

| Concepto | Hoy | Despues | Ahorro |
|---|---|---|---|
| Reglas + AGENTS.md ECC | 36,9 KB | ~8,6 KB | ~28 KB (~7,1k tokens) |
| Listado skills + comandos | 48,8 KB | ~13 KB | ~36 KB (~9,0k tokens) |
| Listado agentes | 30,1 KB | ~12,8 KB | ~17 KB (~4,3k tokens) |
| SessionStart (resumen previo) | ~4,3 KB | 0 | ~1,1k tokens |
| **Total** | ~45k tokens base | ~23k | **~21,5k tokens (-48 %)** |

Friccion: de 271 denegaciones de GateGuard en 33 dias quedarian 85 (las
destructivas); desaparecen ademas ~31 avisos StrategicCompact, ~22 avisos de
costo y ~56 recordatorios "DESIGN CHECK". Latencia: cada hook cuesta ~100 ms de
arranque de node (node vacio: 44 ms) y los de un mismo matcher corren en
paralelo, asi que la mejora de latencia es modesta (de ~150-250 ms a ~100 ms por
llamada); el costo real es de tokens y turnos, no de reloj.

**Hallazgos que importan mas que el ahorro:**

- **El repo del harness esta atrasado respecto a la maquina viva**: el repo tiene
  ECC 2.1.0 (`install-state.json`) y la Mac ejecuta 2.2.3 (scripts, hooks,
  reglas, AGENTS.md y `settings.json` difieren). Antes de aplicar cualquier
  cambio hay que resincronizar (seccion 6, paso 0).
- **El `settings.json` vivo no es portable**: embebe en base64 la ruta
  `/Users/myrighthand/.claude` (24 apariciones). Copiarlo tal cual a Linux/WSL
  rompe los hooks. Se verifico que sustituir el literal por `Buffer.from('','base64')`
  funciona (el hook resuelve la raiz por `~/.claude`).
- **El `settings.json` del harness contiene un PAT de Artiforge dentro de la URL
  de `mcpServers`** (parametro `pat=`), versionado en git. Rotarlo y sacarlo del
  repo (variable de entorno o `~/.claude.json`). No se reproduce aqui.
- `bootstrap.sh` copia directorios con `cp -a` sin borrar: **un skill que se
  mueve a la biblioteca seguira existiendo en las maquinas ya instaladas**. El
  procedimiento de la seccion 6 lo resuelve con un paso `prune` idempotente.
- `ecc/install-state.json` usa la estrategia `merge-hook-ids`: una reinstalacion
  de ECC **vuelve a insertar los hooks** que se borren de `settings.json`. Por
  eso la desactivacion se hace por `env` (que el instalador no toca), no
  editando el arreglo `hooks`.

---

## 2. Evidencia de uso (como se midio)

Transcripts: 235 archivos; 11.951 llamadas Bash, 265 Edit, 373 Write, 183 Agent,
5 Skill, ~116 llamadas MCP de claude.ai Docs. Una denegacion de hook aparece como
`tool_result` con `is_error` y el texto `PreToolUse:<Tool> hook error`; se
contaron por `tool_use_id` unico. Los 205 + 66 (subagentes) = **271 errores de
hook son todos de GateGuard**: ningun otro hook (block-no-verify,
config-protection, mcp-health, doc-file-warning) bloqueo nunca.

| Bloqueo GateGuard | Total | Reintento identico | Cambio de accion | Sin reintento |
|---|---|---|---|---|
| Bash rutinario (1a vez por sesion) | 68 | 47 (69 %) | 21 (31 %) | 0 |
| Edit/Write, mensaje completo | 61 | 53 (87 %) | 6 | 2 |
| Edit/Write, mensaje condensado | 57 | 43 (75 %) | 13 | 1 |
| Bash destructivo | 85 | 27 (32 %) | 56 | 2 |

Por proyecto: auditglow 141, mrh-scaffold 99, `~/development` 30, `~` 1. El
ordinal de denegacion llego a 24 en una sesion. Los 5 bloqueos rutinarios en
subagentes muestran que el gate rutinario de Bash tambien les aplica.

Lectura de "cambio de accion":

- Rutinario y Edit/Write: es ceremonia. En el gate de archivos, ~80 % de los
  reintentos ocurrio sin ningun Read/Grep/ls entre la denegacion y el reintento;
  Claude Code ya exige un Read previo para Edit. El rutinario pide "la solicitud
  en una frase y que verifica el comando": no cambia ninguna accion.
- Destructivo: el clasificador (`gateguard.bash-compatible-destructive`) dispara
  por `rm`, `git checkout --`, `git stash drop`, `--amend`, `worktree remove`,
  `branch -D`, `push --force`, SQL destructivo. En 27 de 82 casos con token
  identificable (33 %) el comando siguiente ya no contenia la parte destructiva
  (p. ej. `rm -rf` de un scratchpad sustituido por `mkdir -p`; `--amend` por un
  commit nuevo; `git stash drop` precedido de `stash list`; un
  `git checkout HEAD~1 -- .` que se abandono). En 48 (59 %) se repitio la parte
  destructiva. **No se puede demostrar ningun error evitado**: a lo sumo 3-5
  casos plausibles. Aun asi es el unico freno automatico al force-push y al
  `reset --hard`, y cuesta ~0,7 % de las llamadas Bash.
- Tiempo del turno extra: mediana 2,4-4,6 s hasta el siguiente mensaje del
  asistente. 271 denegaciones suman ~15-20 minutos y 271 viajes de ida y vuelta
  extra. Los tokens de salida no se pueden atribuir (el reintento de un Write
  incluye el contenido del archivo).

Otros avisos inyectados (`hook_additional_context`): StrategicCompact 31, COST
NOTICE/WARNING/CRITICAL 22, LOOP WARNING 1, SessionStart 43 (media 4.329 bytes,
maximo 6.753; tope por defecto 8.000), "DESIGN CHECK" ~56.

Costo de contexto medido en el adjunto `instructions` de la sesion mas reciente
(98.140 bytes en total) y en `skill_listing` (mediana 48.822 B) y
`agent_listing_delta` (mediana 30.110 B). Tokens ~ bytes / 4.

---

## 3. Hooks

Perfil activo: `standard` (no hay `ECC_HOOK_PROFILE`, ni `env` en settings).
Entradas vivas: PreToolUse 9, PreCompact 1, SessionStart 3, PostToolUse 3,
PostToolUseFailure 2, Stop 8, SessionEnd 1. Los hooks marcados "strict" no corren
en `standard`. "Disparos" es una cota superior basada en el numero de llamadas a
la herramienta (Bash 11.951, Edit 265, Write 373, MCP ~116, sesiones 235).
Los hooks de Stop no dejan traza en el transcript salvo cancelaciones (1).

| Hook (id) | Que hace | Disparos | Bloqueos | Evidencia de valor | Recomendacion |
|---|---|---|---|---|---|
| `pre:bash:block-no-verify` | Bloquea `--no-verify` y `core.hooksPath=` | ~11.951 | 0 | Ninguna medida; protege pre-commit de mrh-backend (ruff, conventional commits) | **Conservar** |
| `pre:bash:gateguard-fact-force` (rutina) | Exige presentar hechos en el primer Bash de la sesion | 68 sesiones | 68 | Nula: 69 % reintento identico, no cambia accion | **Desactivar** (`GATEGUARD_BASH_ROUTINE_DISABLED=1`) |
| `pre:bash:gateguard-fact-force` (destructivo) | Pide archivos afectados, rollback y cita de la orden antes de `rm`, `reset --hard`, `push --force`, stash drop, SQL destructivo | 85 | 85 | Baja pero real: unico freno a force-push/reset en modo bypass; 33 % de los casos cambio de comando | **Acotar/conservar** (sin tocar; anadir `permissions.deny` nativo, seccion 6) |
| `pre:bash:auto-tmux-dev` | Reescribe `npm run dev` a una sesion tmux | 11 en el historico | 0 | Nula: tmux no esta instalado, cae al comando original | **Desactivar** |
| `pre:bash:tmux-reminder`, `git-push-reminder`, `commit-quality` | Recordatorios | 0 (perfil strict) | 0 | n/a | Ya inactivos |
| `pre:powershell:gateguard-fact-force` | Idem GateGuard para PowerShell | 0 (PowerShell no usado) | 0 | n/a | Dejar |
| `pre:edit-write:gateguard-fact-force` | Bloquea el primer Edit/Write por archivo y pide importadores, esquemas y cita literal | 638 | 118 (18,5 %) | Nula medible: ~80 % reintento sin lecturas | **Desactivar** |
| `pre:write:doc-file-warning` | Avisa de `NOTES.md`/`TODO.md`/`SCRATCH.md` fuera de docs | 373 Write | 0 avisos vistos | Baja; solo advierte, nunca bloquea | Conservar (barato) |
| `pre:edit-write:suggest-compact` | Sugiere `/compact` a 50 llamadas o 250k tokens | 638 | 0 (31 avisos) | Baja: con ventana 1M y handoffs en `docs/` el aviso es ruido | **Desactivar** |
| `pre:observe` + `post:observe:continuous-learning` | Ejecuta `observe.sh` en cada herramienta (Pre y Post, async) | ~2 x 12.800 | 0 | Nula: `observer.enabled=false`; el directorio homunculus pesa 8 KB | **Desactivar** (ambos) |
| `pre:governance-capture` + `post:governance-capture` | Registra secretos/violaciones | ~12.600 x 2 | 0 | Nula: devuelve sin hacer nada si falta `ECC_GOVERNANCE_CAPTURE=1` | **Desactivar** (ambos) |
| `pre:config-protection` | Bloquea editar configs de lint/format existentes (eslint, biome, prettier, ruff) | 638 | 0 | No observada, pero cubre un fallo real de agentes; `pyproject.toml` y `tsconfig` excluidos | **Conservar** |
| `pre:mcp-health-check` + `post:mcp-health-check` | Sondea servidores MCP y reconecta | ~116 | 0 | Nula: los conectores claude.ai no estan en la config que sondea; ~160 ms por llamada MCP | **Desactivar** |
| `pre:compact` | Resumen LLM (Haiku, `claude -p`) antes de compactar | n/d | 0 | Solo alimenta el resumen de SessionStart; 39 transcripts son subprocesos `claude -p` de resumen | **Desactivar** junto con SessionStart |
| `session:start` | Inyecta resumen de sesion previa ("HISTORICAL REFERENCE ONLY") y detecta tipo de proyecto | 43 inyecciones (media 4,3 KB) | 0 | Baja: la continuidad real esta en MEMORY.md y `docs/estado-*.md` | **Desactivar contexto** (`ECC_SESSION_START_CONTEXT=off`) |
| `session-start:plan-canvas-sessions` | Muestra sesiones plan-canvas abiertas | 96 arranques | 0 | Sin uso visible; casi siempre sin salida | Conservar (barato) |
| `impeccable ... hook` (SessionStart/PostToolUse Edit|Write/Stop) | Detector de diseno propio | n/d | 0 | Propio; no es ECC | Conservar |
| `post:edit:design-quality-check` | Recordatorio "DESIGN CHECK" tras editar frontend | ~56 avisos | 0 | Baja: solapa con `impeccable`, mismo mensaje en cada edicion | **Desactivar** |
| `post:edit:accumulator` | Acumula archivos editados para el Stop | 638 | 0 | Solo alimenta `stop:format-typecheck` | **Desactivar** con este |
| `post:edit:console-warn` | Avisa de `console.log` tras Edit en JS/TS | 265 | 0 | Baja; aplica solo a React/Expo | Conservar (barato) |
| `post:governance-capture` | (ver arriba) | | | | Desactivar |
| `post:session-activity-tracker` | Escribe `metrics/tool-usage.jsonl` para ECC2 | ~12.600 | 0 | Nula: ningun consumidor | **Desactivar** |
| `post:ecc-metrics-bridge` | Agregado de sesion en `/tmp` para statusline y monitor | ~12.600 | 0 | Alimenta el monitor de bucles | **Conservar** |
| `post:ecc-context-monitor` | Avisos de contexto, costo, alcance y bucle | 22 avisos | 0 | Media: el LOOP WARNING sirve; los avisos de costo son ruido | **Acotar** (`ECC_CONTEXT_MONITOR_COST_WARNINGS=off`) |
| `post:bash:command-log-audit` y `-cost` | Registran cada comando Bash en `bash-commands.log` y `cost-tracker.log` | 41.301 filas | 0 | Nula y con costo: 59 MB, permisos 0644, sin rotacion, redaccion parcial (siguen 7 lineas con apariencia de clave/bearer) | **Desactivar** (y rotar/borrar los logs) |
| `post:bash:pr-created`, `build-complete` | Mensajes informativos | n/d | 0 | Baja | Conservar (barato) |
| `post:quality-gate` (async) | Chequeo prettier/ruff tras editar (solo avisa salvo `ECC_QUALITY_GATE_FIX=true`) | 638 | 0 | Baja: los repos tienen pre-commit/lint propios | **Desactivar** |
| `post:skill:track` | Registra uso de skills (11 filas en total) | 5 | 0 | Baja | Conservar (barato) |
| `stop:plan-canvas-pending` | Entrega feedback pendiente de plan-canvas | 235 | 0 | Sin uso visible | Conservar |
| `stop:format-typecheck` | `biome/prettier --write` + `tsc --noEmit` sobre JS/TS editados (timeout 300 s) | n/d | 0 | Baja y reescribe fuente sin pedir; el proyecto ya verifica con `npm run lint/test` | **Desactivar** |
| `stop:check-console-log` | Revisa `console.log` en archivos modificados | n/d | 0 | Baja: duplica `post:edit:console-warn` | **Desactivar** |
| `stop:session-end` | Persiste resumen; llama a Haiku (`claude -p`) cada 50 mensajes o con <20 % de contexto libre | n/d | 0 | Baja: solo alimenta SessionStart | **Desactivar** junto con SessionStart |
| `stop:evaluate-session` | Extrae patrones para aprendizaje continuo | n/d | 0 | Nula: `skills/learned` casi vacio | **Desactivar** |
| `stop:cost-tracker` | Una fila por sesion en `metrics/costs.jsonl` (2.602 filas, 1 MB) | 235 | 0 | Media: respalda `/cost-report` | **Conservar** |
| `stop:desktop-notify` | Notificacion nativa al terminar | n/d | 0 | Duplica la del plugin Warp en la Mac; util en WSL | Dejar; en la Mac se puede apagar via `settings.local.json` |
| `session:end:marker` | Marca de fin de sesion | 235 | 0 | Trivial | Conservar |

Notas de comportamiento verificadas ejecutando los hooks con entornos aislados
(`ls`, `rm -rf build`, `git push --force`, Edit/Write en `src/` y `docs/`):

| Entorno | `ls` (rutina) | `rm -rf` / `push --force` | Edit/Write |
|---|---|---|---|
| (por defecto) | bloquea 1a vez | bloquea 1a vez | bloquea 1a vez |
| `GATEGUARD_BASH_ROUTINE_DISABLED=1` | pasa | **sigue bloqueando** | bloquea |
| `ECC_GATEGUARD=off` (o `GATEGUARD_DISABLED=1`) | pasa | **pasa (se pierde)** | pasa |
| `ECC_DISABLED_HOOKS=pre:bash:gateguard-fact-force` | pasa | **pasa (se pierde)** | bloquea |
| `ECC_DISABLED_HOOKS=pre:edit-write:gateguard-fact-force` | bloquea | sigue bloqueando | pasa |
| `GATEGUARD_EXEMPT_GLOBS=**` | bloquea | sigue bloqueando | pasa dentro del proyecto; **no** cubre rutas absolutas fuera (`/private/tmp/...`) |
| `GATEGUARD_EXEMPT_GLOBS=docs/**,/private/tmp/**` | bloquea | sigue bloqueando | pasa solo en esas rutas |
| `ECC_HOOK_PROFILE=minimal` | pasa | **pasa (se pierde)** | pasa; `block-no-verify` sigue activo |
| `GATEGUARD_BASH_ROUTINE_DISABLED=1` + `ECC_DISABLED_HOOKS=pre:edit-write:gateguard-fact-force` | pasa | **bloquea** | pasa |

Conclusion: la combinacion de la ultima fila es la unica que quita ~186 de las
271 denegaciones y mantiene el chequeo destructivo. `ECC_GATEGUARD=off` y el
perfil `minimal` apagan tambien la proteccion destructiva.

Semantica de las variables, leida del codigo:

- `ECC_HOOKS_ENABLED=false`: apaga todos los hooks.
- `ECC_HOOK_PROFILE=minimal|standard|strict`: filtra por el campo `profiles` de
  cada id (`scripts/lib/hook-flags.js`). `ecc/setup.json` (`{"hooks":{"profile":..,"enabled":..}}`)
  es el ultimo respaldo si no hay variable de entorno.
- `ECC_DISABLED_HOOKS=id,id`: ids exactos, sin distinguir mayusculas. Los
  dispatchers (`pre:bash:dispatcher`, `post:*`) evaluan tambien cada id
  interno, de modo que se puede apagar un subhook sin apagar el dispatcher
  (apagar `pre:bash:dispatcher` quitaria tambien `block-no-verify`).
- `ECC_GATEGUARD` en `0|false|off|disabled|disable`, o `GATEGUARD_DISABLED=1`:
  GateGuard completo.
- `GATEGUARD_BASH_ROUTINE_DISABLED` en `1|true|on|enabled|yes`: solo el gate
  rutinario.
- `GATEGUARD_EXEMPT_GLOBS`: globs relativos al proyecto (`*` dentro de un
  segmento, `**` entre segmentos) o absolutos; solo Edit/Write/MultiEdit.
- `GATEGUARD_FACT_FORCE_FULL_DENIALS` (por defecto 3): cuantas denegaciones
  llevan el mensaje largo antes de pasar al condensado.
- `GATEGUARD_BASH_EXTRA_DESTRUCTIVE`: regex que se suma al clasificador
  destructivo (no permite quitar patrones).
- `ECC_SESSION_START_CONTEXT=off` o `ECC_SESSION_START_MAX_CHARS=0`: sin
  inyeccion en SessionStart.
- `ECC_CONTEXT_MONITOR_COST_WARNINGS=off`: sin avisos de costo.
- `ECC_GOVERNANCE_CAPTURE=1`: unica forma de que governance-capture haga algo.
- `ECC_LLM_SUMMARY_INTERVAL`, `ECC_LLM_SUMMARY_MODEL`, `ECC_SKIP_LLM_SUMMARY`:
  controlan la llamada a Haiku del resumen de sesion.

---

## 4. Reglas ECC frente a las convenciones `nicol`

Precedencia (README de `nicol`): lo especifico gana, **salvo** el piso de
verificacion de `ecc/common/testing.md` y los controles de
`ecc/common/security.md`. Los archivos `rules/ecc/<lenguaje>/*` llevan
`paths:` y solo se cargan al abrir archivos de ese lenguaje; no cuestan contexto
global. Los siguientes si se cargan siempre (bytes reales de la sesion):

| Archivo ECC (bytes) | Regla que choca | Regla `nicol` / criterio que manda | Accion |
|---|---|---|---|
| `~/.claude/AGENTS.md` (12.969) | "Agent-First" como principio 1; "usar agentes proactivamente sin pedir" (30 disparadores); 80 % de cobertura obligatoria; envelope de API y Repository como patron; conteos obsoletos (68 agentes, 293 skills; hoy 298 skills) | `nicol/common/patterns.md` (envelope solo si 100 % de endpoints; Repository solo con mas de una fuente o test sin BD), `simplicity.md` (proporcionalidad), `nicol/common/testing.md` | **Reducir a ~1,2 KB** (seguridad, identidad del harness); duplica `ecc/common/*` |
| `ecc/README.md` (5.535) | Documentacion de instalacion, no una regla; trae "Rule Priority" y comandos `install.sh` | n/a | **Borrar** del contexto (mover a `docs/`) |
| `ecc/common/patterns.md` (1.021) | "Repository Pattern: encapsula siempre el acceso a datos"; "API Response Format: envelope consistente para todas las respuestas" | `nicol/common/patterns.md` ya lo declara como complemento sin contrapartida; manda el umbral (cuando vale la pena / cuando no) | **Borrar** y corregir los enlaces `../../ecc/common/patterns.md` de nicol |
| `ecc/common/development-workflow.md` (2.251) | Paso 0 obligatorio "GitHub code search primero, Exa, registros de paquetes" antes de toda implementacion; "Plan First: generar PRD, architecture, system_design, tech_doc, task_list"; "TDD con tdd-guide, 80 %+" | `simplicity.md`: la escalera empieza por "esto necesita existir" y "el codigo ya lo tiene"; proporcionalidad para cambios triviales; `nicol/architecture.md` (empezar simple, umbral escrito) | **Borrar**; si se quiere conservar algo, una linea: investigar fuera solo al anadir una dependencia o capacidad nueva. Actualizar el enlace en `simplicity.md` |
| `ecc/common/agents.md` (2.893) | "Invoca ecc:planner..." (en esta instalacion los agentes se llaman `planner`, no `ecc:planner`: el prefijo no existe); "SIEMPRE ejecucion paralela de Task"; "Immediate Agent Usage: no hace falta pedirlo"; "Multi-Perspective Analysis" con 5 roles | `simplicity.md` (proporcionalidad); criterio propio Haiku mecanico/Sonnet pesado (memoria); uso real: 7 % de las llamadas a Agent son ECC | **Reducir** a la seccion "Delegation Completion Contract" (valiosa, ~0,9 KB); borrar el resto |
| `ecc/common/performance.md` (1.646) | Perfiles de modelo obsoletos (Haiku "90 % de Sonnet, 3x ahorro"; Sonnet "mejor modelo de codigo"); "evitar el ultimo 20 % del contexto" (ventana de 200k; hoy `opus[1m]`); "31.999 tokens de thinking" y atajos Option+T | Modelos y ventana actuales (`opus[1m]`, `effortLevel: xhigh`) | **Borrar** |
| `ecc/common/code-review.md` (3.662) | "Revision OBLIGATORIA tras cualquier modificacion"; "cobertura 80 %" en la checklist; tabla de 6 agentes revisores | `simplicity.md`: "para un cambio de una linea el pipeline es sobreingenieria"; checklist de sobreingenieria ya presente | **Matizar**: conservar la tabla de severidades y los disparadores de seguridad (~1,2 KB), quitar "obligatoria" y la tabla de agentes |
| `ecc/common/coding-style.md` (3.021) | "Inmutabilidad CRITICA: NUNCA mutar"; "MUCHOS archivos pequenos, 200-400 lineas" | `simplicity.md` (piso: no crear archivo sin responsabilidad propia); modismos de Django ORM, Java/JPA y Dart donde mutar es lo idiomatico (la propia nota de lenguaje lo admite) | **Matizar** "NEVER" a "preferir"; resto **dejar** |
| `ecc/common/testing.md` (1.399) | "80 % minimo, los 3 tipos obligatorios, TDD obligatorio con tdd-guide" | `nicol/common/testing.md`: la cobertura es evidencia por comportamiento, "no un objetivo del tipo 100 % de lineas", E2E solo para recorridos criticos, capa mas baja que pueda fallar por la razon real | **Dejar** (es el piso que `nicol` declara intocable); sugerencia: anadir en el README de `nicol` una linea que lea "80 %" como piso sobre lo tocado, no como meta global |
| `ecc/common/security.md` (861) | "Rate limiting en todos los endpoints", "CSRF activo" | `nicol/common/api-security.md` (proteger endpoints publicos de alto riesgo) | **Dejar** (piso declarado intocable) |
| `ecc/common/git-workflow.md` (836) | Tipos de commit en ingles; flujo de PR con plan de pruebas | `mrh-scaffold/AGENTS.md` (sin PR, commits convencionales en espanol con scope) y `nicol/delivery/*` | **Borrar** global (los proyectos ya definen su flujo) |
| `ecc/common/hooks.md` (767) | "Nunca usar dangerously-skip-permissions"; guia de TodoWrite | La configuracion real tiene `skipDangerousModePermissionPrompt: true` | **Borrar** |
| `ecc/common/simplicity.md` (5.844) | n/a | Es propia y coherente con `nicol` | **Conservar** |

Reglas `nicol` fuera del alcance de ECC pero con el mayor ahorro individual:
`nicol/react/ux.md` (12,7 KB) y `nicol/react/engineering.md` (9 KB) se cargan en
proyectos Django/Flutter donde no aplican, y `nicol/common/testing.md` (11,5 KB)
es en buena parte de Spring/Gradle. Anadirles `paths:` (p. ej. `**/*.tsx`,
`**/*.ts`) como hacen las reglas ECC por lenguaje ahorraria ~5,4k tokens en cada
sesion no-React. Decision de Nicolas.

---

## 5. Skills, agentes y comandos

### Conteos y uso real

| Superficie | Instalados | De ECC | Propios/otros | Uso en 33 dias |
|---|---|---|---|---|
| Skills (`~/.claude/skills`) | 341 | 298 | 43 (33 symlinks a `~/.agents/skills`) | 5 invocaciones de la herramienta Skill: `agent-browser` 2, `plan` 1+2 (adjunto), `devops-rollout-plan` 1, `docs` 1; `skill-runs.jsonl` registra 11 en total (`brag-slim`, `agent-browser`...). Ninguna skill de ECC por nombre |
| Comandos (`~/.claude/commands`) | 94 | 94 | 0 | `/plan` 3, `/clear` 9; ningun otro comando ECC |
| Agentes (`~/.claude/agents`) | 68 | 68 | 0 | 183 llamadas Agent: `general-purpose` 143, `fork` 12, `Explore` 4, ECC: `tdd-guide` 6, `e2e-runner` 2, `react-reviewer` 2, `java-reviewer` 1 (13 en total, 7 %). `mobile-developer` (8), `fullstack-developer` y `frontend-developer` no existen hoy en la instalacion |

Los comandos tambien aparecen como skills en el listado. Dominios que no se
usan en los 4 proyectos reales (Django/DRF, Flutter, Spring Boot, React/Vite,
Expo, PostgreSQL, Docker/Dokploy): HarmonyOS/ArkTS, Rust, C/C++, C#, F#, Go,
Kotlin/Android, Swift/SwiftUI (siete skills Apple), PHP/Laravel (cuatro),
Perl (tres), Rails, Quarkus, NestJS, Nuxt/Vue/Angular, healthcare (cinco),
trading/DeFi/prediction-market/Ito (once), redes empresariales y homelab (diez),
supply chain y logistica (ocho), marketing/SEO/social/video/media (unas treinta),
GAN, ML/PyTorch, openclaw/nanoclaw/hermes, Jira y Google Workspace.

### Conjunto DIARIO propuesto (instalado en `~/.claude`)

Skills de ECC (30): `django-patterns`, `django-security`, `django-tdd`,
`django-verification`, `django-celery`, `python-patterns`, `python-testing`,
`postgres-patterns`, `database-migrations`, `redis-patterns`,
`dart-flutter-patterns`, `flutter-dart-code-review`, `springboot-patterns`,
`springboot-security`, `springboot-tdd`, `springboot-verification`,
`jpa-patterns`, `java-coding-standards`, `react-patterns`,
`react-performance`, `react-testing`, `vite-patterns`,
`react-native-patterns`, `docker-patterns`, `deployment-patterns`,
`security-review`, `api-design`, `e2e-testing`, `verification-loop`,
`architecture-decision-records`.

Skills propias/otras (43, no se tocan; son elecciones de Nicolas, no de ECC).
Candidatas a biblioteca si quiere recortar mas: `write-swift`, `apple-design`
(no usa Swift), `brag-slim`, y las 8 de animacion si no las usa a menudo.

Comandos (17): `code-review`, `review-pr`, `build-fix`, `plan`, `test-coverage`,
`refactor-clean`, `update-docs`, `flutter-build`, `flutter-review`,
`flutter-test`, `python-review`, `react-build`, `react-review`, `react-test`,
`save-session`, `resume-session`, `checkpoint`.

Agentes (22): `code-reviewer`, `security-reviewer`, `python-reviewer`,
`django-reviewer`, `java-reviewer`, `java-build-resolver`, `react-reviewer`,
`react-build-resolver`, `typescript-reviewer`, `flutter-reviewer`,
`dart-build-resolver`, `database-reviewer`, `e2e-runner`, `tdd-guide`,
`build-error-resolver`, `code-explorer`, `silent-failure-hunter`,
`refactor-cleaner`, `docs-lookup`, `planner`, `architect`,
`performance-optimizer`.

### BIBLIOTECA (instalable bajo demanda, fuera de `~/.claude`)

- 268 skills de ECC restantes, agrupadas por modulo de `install-state.json`:
  `agentic-patterns` (35), `operator-workflows` (19), `business-content` (14),
  `media-generation` (11), `research-apis` (9), `optimization-workflows` (8),
  `supply-chain-domain` (8), `prediction-market-skills`/`ito-compute`/
  `nasiko-control-plane`/`operator-desk-patterns` (15), `swift-apple` (7),
  `machine-learning` (4), `social-distribution` (3), `document-processing` (2),
  los frameworks y lenguajes no usados de `framework-language` (~45) y los de
  `security`/`devops-infra` ajenos al stack (~25: `kubernetes-patterns`,
  `hipaa-compliance`, `defi-amm-security`, `laravel-security`...).
- 77 comandos (todos los `*-build/-review/-test` de Go, Rust, C++, Kotlin, Vue;
  `epic-*`, `orch-*`, `multi-*`, `prp-*`, `gan-*`, `hookify*`, `instinct-*`,
  `pm2`, `jira`, `loop-*`, `santa-loop`, `model-route`, `evolve`, `learn*`...).
- 46 agentes (`cpp-*`, `csharp-reviewer`, `fsharp-reviewer`, `go-*`, `kotlin-*`,
  `rust-*`, `swift-*`, `php-reviewer`, `vue-reviewer`, `fastapi-reviewer`,
  `harmonyos-app-resolver`, `healthcare-reviewer`, `network-*`,
  `homelab-architect`, `marketing-agent`, `seo-specialist`, `opensource-*`,
  `gan-*`, `chief-of-staff`, `mle-reviewer`, `rag-pipeline-reviewer`,
  `pytorch-build-resolver`, `loop-operator`, `harness-optimizer`,
  `agent-evaluator`, `spec-miner`, `type-design-analyzer`, `comment-analyzer`,
  `pr-test-analyzer`, `code-architect`, `doc-updater`, `conversation-analyzer`).

Ahorro del listado (proporcional al numero de entradas): skills+comandos
345 de ~470 entradas = ~36 KB (~9,0k tokens); agentes 46 de ~80 = ~17 KB
(~4,3k tokens).

---

## 6. Cambios concretos propuestos

Nada de esto se aplico. Todo se hace en el repo del harness y se propaga con
`bootstrap.sh`.

### Paso 0. Resincronizar el repo con la Mac (prerrequisito)

El repo esta en ECC 2.1.0 y la Mac en 2.2.3; hay que traerlo antes de aplicar
el recorte, para que los ids de hook coincidan. Y `update.sh` debe volver
portable el `settings.json` (la ruta base64 de la Mac).

`update.sh` (despues de `cp -a "$HOME/.claude/settings.json" ...`):

```diff
 cp -a "$HOME/.claude/settings.json" "$DEST/.claude/settings.json"
+# El settings vivo de ECC 2.2.x embebe la ruta del HOME en base64: neutralizarla
+python3 - "$DEST/.claude/settings.json" <<'PYEOF'
+import re,sys
p=sys.argv[1]; s=open(p).read()
s=re.sub(r"Buffer\.from\('[A-Za-z0-9+/=]+','base64'\)","Buffer.from('','base64')",s)
open(p,'w').write(s)
PYEOF
```

Y en el bucle de directorios de `update.sh` y de `bootstrap.sh`:

```diff
-for d in agents commands scripts hooks rules ecc skills .agents; do
+for d in agents commands scripts hooks rules ecc skills .agents skills-library agents-library commands-library; do
```

(En `update.sh` el origen es `$HOME/.claude/$d`; en `bootstrap.sh`
`$SRC/.claude/$d`. Los `*-library` no los lee Claude Code: solo `skills/`,
`agents/` y `commands/` se escanean.)

Despues: ejecutar `./update.sh` en la Mac, revisar `git diff --stat` y rotar el
PAT de Artiforge antes de hacer commit del `settings.json` (o sacar
`mcpServers` del archivo versionado).

### Paso 1. `env` en `home/.claude/settings.json` (sobrevive a reinstalaciones de ECC)

```diff
   "model": "opus[1m]",
+  "env": {
+    "GATEGUARD_BASH_ROUTINE_DISABLED": "1",
+    "ECC_SESSION_START_CONTEXT": "off",
+    "ECC_CONTEXT_MONITOR_COST_WARNINGS": "off",
+    "ECC_DISABLED_HOOKS": "pre:edit-write:gateguard-fact-force,pre:edit-write:suggest-compact,pre:observe,post:observe:continuous-learning,pre:governance-capture,post:governance-capture,pre:mcp-health-check,post:mcp-health-check,pre:bash:auto-tmux-dev,post:bash:command-log-audit,post:bash:command-log-cost,post:edit:design-quality-check,post:edit:accumulator,post:session-activity-tracker,post:quality-gate,stop:format-typecheck,stop:check-console-log,stop:evaluate-session,stop:session-end,pre:compact"
+  },
   "enabledPlugins": {
```

Notas:

- Los ids son los de 2.2.3 (paso 0 obligatorio); en 2.1.0 se llaman distinto
  (`post:edit:accumulate`, `post:observe`).
- `stop:session-end`, `pre:compact` y `ECC_SESSION_START_CONTEXT=off` forman el
  bloque "resumenes de sesion". Si Nicolas quiere conservar los resumenes,
  quitar las tres.
- No se desactivan: `pre:bash:block-no-verify`, el chequeo destructivo,
  `pre:config-protection`, `post:ecc-metrics-bridge`,
  `post:ecc-context-monitor`, `stop:cost-tracker`, `stop:plan-canvas-pending`,
  `session:end:marker`, los hooks de `impeccable`.
- Ajuste por maquina en `~/.claude/settings.local.json` (ignorado por git), p. ej.
  en la Mac `{"env":{"ECC_DISABLED_HOOKS":"<lista anterior>,stop:desktop-notify"}}`
  (la clave `env` del local reemplaza a la del global: copiar la lista completa).

Control adicional recomendado (nativo, independiente de ECC), en el mismo
`settings.json`, porque el modo bypass vuelve al gate destructivo la unica
defensa y las reglas `deny` si se aplican:

```diff
+  "permissions": {
+    "deny": [
+      "Bash(git push --force:*)",
+      "Bash(git push -f:*)",
+      "Bash(rm -rf /:*)",
+      "Bash(rm -rf ~:*)"
+    ]
+  },
```

(Verificar que `deny` se respeta con `skipDangerousModePermissionPrompt: true`
en la primera maquina antes de propagarlo.)

### Paso 2. Recorte de contexto con un paso `prune` idempotente

Por que un script y no editar `install-state.json`: el instalador es dueno de
esos archivos (`ownership: managed`); `doctor`/`repair` los restauraria y una
reinstalacion del perfil `full` los volveria a copiar. Un `prune` que se
vuelve a ejecutar tras cada instalacion es robusto. Nuevo archivo propuesto
`prune-ecc.sh` en la raiz del repo (no se creo) y listas en `ecc-daily/`:

```bash
#!/usr/bin/env bash
# Mueve a *-library todo lo gestionado por ECC que no este en la lista diaria.
set -euo pipefail
ROOT="${1:-$HOME/.claude}"; HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 - "$ROOT" "$HERE/ecc-daily" <<'PY'
import json,os,shutil,sys
root,daily=sys.argv[1:3]
st=json.load(open(f"{root}/ecc/install-state.json"))
managed={k:set() for k in("skills","agents","commands")}
for o in st["operations"]:
    p=os.path.relpath(o["destinationPath"],root).split(os.sep)
    if p[0] in managed and len(p)>1: managed[p[0]].add(p[1].removesuffix(".md"))
for kind in managed:
    keep={l.strip() for l in open(f"{daily}/{kind}.txt") if l.strip()}
    lib=f"{root}/{kind}-library"; os.makedirs(lib,exist_ok=True)
    for name in sorted(managed[kind]-keep):
        for cand in (f"{root}/{kind}/{name}",f"{root}/{kind}/{name}.md"):
            if os.path.lexists(cand): shutil.move(cand,f"{lib}/{os.path.basename(cand)}")
# reglas ECC y AGENTS.md
for f in ("README.md","common/patterns.md","common/performance.md","common/hooks.md","common/git-workflow.md","common/development-workflow.md"):
    p=f"{root}/rules/ecc/{f}"
    if os.path.exists(p): os.remove(p)
PY
# Sustituir AGENTS.md y recortar agents.md/code-review.md con las versiones del repo
install -m 0644 "$HERE/ecc-daily/AGENTS.md" "$ROOT/AGENTS.md"
install -m 0644 "$HERE/ecc-daily/rules-agents.md" "$ROOT/rules/ecc/common/agents.md"
install -m 0644 "$HERE/ecc-daily/rules-code-review.md" "$ROOT/rules/ecc/common/code-review.md"
```

Archivos que acompanan (a crear al aprobar):

- `ecc-daily/skills.txt` (30 ids), `ecc-daily/commands.txt` (17),
  `ecc-daily/agents.txt` (22): las listas de la seccion 5. Los 43 skills propios
  no estan en `install-state.json`, por lo que `prune` nunca los toca.
- `ecc-daily/AGENTS.md` (~1,2 KB): seguridad antes de commit, inmutabilidad
  como preferencia, referencia a `rules/nicol` y a la biblioteca.
- `ecc-daily/rules-agents.md`: solo "Delegation Completion Contract".
- `ecc-daily/rules-code-review.md`: severidades y disparadores de seguridad.
- En `rules/nicol/common/patterns.md` y `simplicity.md`: actualizar los enlaces
  a archivos borrados.

Enganche en `bootstrap.sh`, justo antes de "5. Ejecutables":

```diff
+# 4b. Recorte de ECC a lo diario (idempotente; repetir tras cualquier reinstalacion de ECC)
+"$(dirname "$SRC")/prune-ecc.sh" "$HOME/.claude"
```

### Paso 3. Reinstalacion de ECC (fase 2, opcional)

Evita depender del `prune`: instalar con perfil `core` mas las skills
diarias, `node scripts/install-plan.js --profile core --skills <ids> --dry-run`
(o un `ecc-install.json` con `--config`). El clon local `~/.ecc-src` es 2.0.0
y su manifiesto no coincide con los 28 modulos instalados en 2.2.3, asi que
hay que clonar 2.2.3 y verificar con `--dry-run` antes. Perfiles de 2.0.0:
`minimal` (5 modulos), `core` (6, con hooks), `developer` (9), `full` (23).
`hookConsent: declined` en una reinstalacion deja el runtime de hooks sin
instalar (mas drastico que la lista de `env`).

### Procedimiento en las 4 maquinas (Mac, Acris, escritorio WSL, Arch)

1. Mac: pasos 0-2, `./update.sh`, rotar el PAT, `git commit` y `git push`
   (requiere aprobacion; esta auditoria no commitea).
2. Mac: antes de ejecutar `./bootstrap.sh` (usa `$HOME`, no hay modo de prueba),
   respaldar a mano: `cp -a ~/.claude ~/.claude-pre-recorte`.
3. En cada maquina: `git pull && ./bootstrap.sh` (el script ya respalda en
   `~/.claude-backup-<fecha>`), luego `claude login` solo si hace falta.
4. Verificacion en cada maquina (sesion nueva):
   - `python3 -c "import json;print(json.load(open('$HOME/.claude/settings.json'))['env'])"` muestra el bloque.
   - Primer `ls`: no aparece "Fact-Forcing Gate".
   - `rm -rf /tmp/prueba-audit` y `git push --force` siguen pidiendo hechos
     (o el `deny` nativo los rechaza).
   - Primer Edit de un archivo nuevo pasa sin denegacion.
   - `/context` baja de ~45k a ~23k tokens de base; `ls ~/.claude/skills | wc -l` ~73.
   - Linux/WSL: confirmar que los hooks resuelven la raiz (sin la ruta de la Mac).
5. Mantenimiento: tras cualquier reinstalacion de ECC volver a ejecutar
   `./prune-ecc.sh`; no usar `repair` sin hacerlo despues.

### Rollback

- Inmediato por maquina (sin red): borrar el bloque `env` de
  `~/.claude/settings.json` (o poner `ECC_DISABLED_HOOKS` vacio en
  `settings.local.json`); efecto en la sesion siguiente.
- Skills/agentes/comandos: `mv ~/.claude/skills-library/* ~/.claude/skills/`
  (idem `agents-library`, `commands-library`); o restaurar
  `~/.claude-backup-<fecha>`.
- Reglas y AGENTS.md: se recuperan del respaldo o del commit anterior
  (`git revert` del commit del harness y `./bootstrap.sh`).
- Limpieza de logs opcional y reversible solo desde respaldo: `bash-commands.log`
  y `cost-tracker.log` (59 MB).

---

## 7. Riesgos de cada recomendacion

| Recomendacion | Proteccion que se pierde | Mitigacion |
|---|---|---|
| Desactivar GateGuard Edit/Write | Obligar a mirar importadores/esquemas antes del primer edit de cada archivo. En la practica el agente ya debe leer el archivo (Claude Code exige Read previo para Edit) y ~80 % de las veces no investigo mas | Reglas `nicol/testing` (evidencia por capa), revisor tras cambios no triviales |
| Desactivar gate rutinario de Bash | El "declara que vas a hacer" del primer comando; sin efecto medible en el comportamiento | Ninguna necesaria |
| Conservar solo el destructivo | Nada nuevo; sigue siendo ceremonia (33 % cambia el comando) y no es infalible: rodeable con wrappers | `permissions.deny` nativo para force-push y `rm -rf` de raiz/home; en modo bypass el `deny` es la defensa real |
| No usar `ECC_GATEGUARD=off` ni `minimal` | Evitado a proposito: ambos apagan el chequeo destructivo | n/a |
| Desactivar `pre:observe`/`post:observe`, `evaluate-session` | Aprendizaje continuo (instintos): hoy inerte (`observer.enabled=false`) | Reactivar con `observer.enabled=true` y quitar los ids de la lista |
| Desactivar `governance-capture` | Registro de secretos/politicas (solo funciona con `ECC_GOVERNANCE_CAPTURE=1`, no activado) | Nada que perder hoy |
| Desactivar `mcp-health-check` | Sondeo y reconexion de MCP propios (HTTP/stdio). Solo hay uno en el harness (Artiforge) | Reconexion manual; riesgo bajo |
| Desactivar `auto-tmux-dev` | Que `npm run dev` corra desacoplado si se instala tmux | Reactivar si se instala tmux |
| Desactivar `suggest-compact` | Recordatorios de `/compact` | Ventana 1M, handoffs en `docs/`; el monitor de contexto sigue |
| Quitar avisos de costo | Aviso al superar umbrales de gasto | `stop:cost-tracker` y `/cost-report` siguen disponibles |
| Desactivar `command-log-*` | Auditoria local de comandos Bash (hoy sin consumidor, 0644, redaccion parcial) | Mejor: rotar y borrar los logs existentes |
| Desactivar `stop:format-typecheck` y `post:quality-gate` | Formateo/typecheck automatico al terminar cada respuesta | Pre-commit y `npm run lint`/`make check` por proyecto; el formateo automatico reescribe fuente sin pedirlo |
| Desactivar `design-quality-check` | Recordatorio de calidad de UI de ECC | `impeccable` sigue activo |
| Desactivar contexto de SessionStart, `session-end` y `pre:compact` | Resumen automatico de sesiones previas (puede ser util al retomar una tarea larga sin handoff) | MEMORY.md y `docs/estado-*.md`; `/save-session` y `/resume-session` quedan en el set diario. Tambien deja de existir la llamada a Haiku via `claude -p` |
| Mover skills/agentes/comandos a biblioteca | Descubrimiento automatico: un skill fuera del listado no se invoca solo | Biblioteca instalable (`mv` o reinstalacion); revisar con `find-skills`. Ninguna skill ECC se invoco por nombre en 33 dias |
| Reducir AGENTS.md y reglas ECC | Recordatorios genericos duplicados | Piso de seguridad y testing se conserva (`ecc/common/security.md`, `testing.md`), `simplicity.md` y `nicol/*` intactos |
| `prune` en `bootstrap.sh` | Si `install-state.json` falta, el script no hace nada (falla segura) | Idempotente; las listas viven en el repo |
| Resincronizar el repo a 2.2.3 | Cambia ~150 archivos de `scripts/` y `rules/` en el diff | Revisar `git diff --stat`; respaldo de `bootstrap.sh` |

## 8. Limitaciones de esta auditoria

- Ventana de 33 dias y 4 carpetas de proyecto: los transcripts anteriores no
  existen o fueron limpiados. 5 invocaciones de skills es una muestra pequena;
  si una skill ECC se usa en trimestres, la biblioteca la conserva.
- "Cambio de accion" se infiere comparando el siguiente comando/archivo
  tras la denegacion; no se puede conocer la intencion. Ningun error evitado
  quedo demostrado; los 3-5 casos plausibles estan descritos sin copiar contenido.
- Los Stop hooks y los hooks asincronos no dejan traza en el transcript; sus
  disparos se estiman por sesiones y llamadas, no se cuentan.
- Las latencias (~100 ms por hook, ~150-250 ms por llamada) se midieron con
  `HOME` aislado, en la Mac, con 6 repeticiones; no incluyen el viaje del modelo.
- El clon `~/.ecc-src` es 2.0.0; los perfiles listados son de esa version y
  hay que reverificarlos contra 2.2.3 antes de la fase 2.
- El adjunto `instructions` medido no incluia aun `nicol/delivery/versioning.md`
  ni `changelog.md` (~9 KB), que se cargaran en sesiones nuevas y elevan la base.
- Hallazgo menor: `~/.claude/agent-harness.settings.json` contiene solo hooks
  vacios y parece un resto; no se usa.
