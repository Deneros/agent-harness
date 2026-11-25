---
name: hermes-relay
description: >
  Pedirle algo a Hermes (el agente de operaciones que vive en Acris) desde cualquier
  equipo del tailnet por SSH, con el relay de verbos cerrados. Úsala cuando alguien
  quiera pedirle algo a Hermes, ver el estado de sus tareas, ejecutar ya una tarea de
  Acris (salud de aplicaciones, vulnwatch, respaldos, restauración de prueba, espejo
  de evidencias), consultar o marcar una corrección de vulnwatch (en curso, resuelta,
  excepción aceptada, reabrir), avisar o mandar un mensaje por Telegram a través de
  Hermes, o hacerle un encargo abierto. También con "dile a Hermes", "pídele a Hermes",
  "hermes-relay", "relay de Acris", "marca resuelto X en vulnwatch" o "avísame por Telegram".
  No sirve para crear, editar o borrar tareas de Hermes ni para cambiar su configuración.
---

# Relay de Hermes

Hermes corre en Acris (`acris@100.68.192.64`, solo por Tailscale). El relay es el único camino
acordado para pedirle cosas desde otro equipo: una lista cerrada de verbos, identidad por
`tailscale whois` (no por lo que declares) y un registro de cada llamada en Acris.

Referencias: `~/development/operaciones/acris/relay/README.md` (qué hace cada verbo y por qué) y
`~/development/operaciones/docs/runbooks/hermes-relay.md` (registro, acceso de un equipo nuevo,
qué hacer si no te identifica).

## Requisitos

- El equipo está en el tailnet y tiene **su propia** llave SSH autorizada en `~acris/.ssh/authorized_keys`.
  Si `ssh` falla por llave o huella, sigue la sección 4 del runbook; nunca copies una llave privada de otro equipo.
- Conecta siempre a `100.68.192.64` (la IP de Tailscale). Por la IP de la red local el relay rechaza todo.

## Comandos exactos

Las comillas simples envuelven el comando remoto entero; los argumentos con espacios van además entre
comillas dobles dentro. `BatchMode` evita que se quede esperando una contraseña.

```bash
ssh -o BatchMode=yes acris@100.68.192.64 '~/operaciones/acris/relay/hermes-relay estado'
ssh -o BatchMode=yes acris@100.68.192.64 '~/operaciones/acris/relay/hermes-relay ejecutar "Salud de aplicaciones"'
ssh -o BatchMode=yes acris@100.68.192.64 '~/operaciones/acris/relay/hermes-relay vulnwatch listar'
ssh -o BatchMode=yes acris@100.68.192.64 '~/operaciones/acris/relay/hermes-relay vulnwatch ver dokploy'
ssh -o BatchMode=yes acris@100.68.192.64 '~/operaciones/acris/relay/hermes-relay vulnwatch marcar dokploy en_curso --nota "actualizando"'
ssh -o BatchMode=yes acris@100.68.192.64 '~/operaciones/acris/relay/hermes-relay vulnwatch marcar dokploy resuelto'
ssh -o BatchMode=yes acris@100.68.192.64 '~/operaciones/acris/relay/hermes-relay vulnwatch excepcion pillow-mrh --motivo "solo en tests" --revisar 2027-01-15'
ssh -o BatchMode=yes acris@100.68.192.64 '~/operaciones/acris/relay/hermes-relay vulnwatch reabrir dokploy --nota "reapareció"'
ssh -o BatchMode=yes acris@100.68.192.64 '~/operaciones/acris/relay/hermes-relay avisar "Despliegue de AuditGlow terminado"'
ssh -o BatchMode=yes acris@100.68.192.64 '~/operaciones/acris/relay/hermes-relay encargo "<pedido abierto>"'
```

| Verbo | Para qué | Notas |
|---|---|---|
| `estado` | Ver las tareas de Hermes y cuáles son `[ejecutable]` | Empieza por aquí si no sabes el nombre exacto de una tarea |
| `ejecutar "<nombre o id>"` | Lanzar ya una tarea mecánica permitida | Solo encola; el resultado se ve luego en `estado` o llega por Telegram |
| `vulnwatch listar` / `ver <id>` | Correcciones pendientes / detalle | Solo lectura; `ver` acepta ids de remediación (`dokploy`), no `CVE-...` |
| `vulnwatch marcar <id> en_curso\|resuelto` | Avanzar una corrección | `resuelto` se rechaza si la última foto aún ve el hallazgo: es correcto, no lo fuerces |
| `vulnwatch excepcion <id> --motivo M --revisar AAAA-MM-DD` | Aceptar el riesgo | Motivo de hasta 300 caracteres; revisión entre mañana y 180 días |
| `vulnwatch reabrir <id>` | Reabrir una resuelta o en excepción | |
| `avisar "<texto>"` | Un mensaje al Telegram de Hermes, firmado con tu identidad | Una vez; no lo repitas para "confirmar" |
| `encargo "<texto>"` | Pedido abierto a Hermes con reglas fijas | **Gasta modelo**, hasta 30 min; último recurso |

Resultado: stdout y código `0` = hecho; stderr y código `2` = rechazado, nada se ejecutó (el mensaje dice
por qué); código `1` = se intentó y falló. Informa al usuario el mensaje tal cual.

## Qué no hacer

- **No uses `encargo` para lo que resuelve un verbo mecánico.** Ver tareas → `estado`; lanzar una tarea →
  `ejecutar`; correcciones → `vulnwatch`; avisar → `avisar`. `encargo` es solo para lo que exige criterio de
  Hermes, y conviene confirmarlo con el usuario antes porque gasta modelo.
- **Nada de secretos**: no pongas contraseñas, tokens, llaves ni valores de `.env` en avisos ni encargos, ni
  pidas a Hermes que los muestre. No leas `~/.hermes/.env` ni `config.yaml` de Acris.
- No intentes saltarte el relay para lo mismo (entrar por SSH y llamar a `hermes cron run` o `hermes send`
  a mano): el relay deja registro y aplica la lista de tareas permitidas.
- No intentes lanzar tareas que el relay rechaza (avisos de correo, copia del mailserver, tareas con agente
  o pausadas): el rechazo es a propósito. Díselo al usuario.
- No crees, edites, pauses ni borres tareas de Hermes desde aquí; el relay no lo permite y no debe hacerse
  sin el usuario.
- `encargo` solo funciona por SSH y lleva un preámbulo que prohíbe cambiar producción, borrar datos o
  editar el repo de operaciones; no lo redactes para esquivar esas reglas.
