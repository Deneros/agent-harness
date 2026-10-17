# Agent Harness

Snapshot portable y reproducible de mi harness de Claude Code y Pi. Un `git clone` y
un `./bootstrap.sh` dejan una máquina nueva configurada para ambos.

**Repositorio privado.** Contiene configuración personal, memoria del agente y
la postura de seguridad completa (hooks y permisos). No hacer público.

## Qué contiene

```
home/.claude/
  settings.json     configuración activa (sin rutas absolutas, portable tal cual)
  agents/           67 agentes    (ECC)
  commands/         92 comandos   (ECC)
  scripts/          150 scripts de hooks (ECC)
  hooks/            runtime de hooks (ECC)
  rules/ecc/        114 reglas ECC + simplicity.md (propia)
  skills/           paquete ECC (137 archivos) + 40 skills propias
  ecc/              install-state.json — manifiesto de lo que ECC gestiona
  memory/           memoria persistente del agente
home/.agents/skills/  32 skills (destino real de los symlinks de skills/)
home/.pi/agent/
  settings.json       paquetes/modelo por defecto (sin deviceId ni credenciales)
  extensions/         extensiones propias de Pi
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
`~/.claude-backup-<timestamp>` antes de escribir.

Windows nativo: `install.ps1` (port sin probar; en WSL usar `bootstrap.sh`).

## Sincronizar cambios desde una máquina

```bash
./update.sh         # copia el harness vivo al repo
git add -A && git commit -m "chore: sync desde <máquina>" && git push
```

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

- `settings.json` no tiene ni una ruta absoluta: usa `${CLAUDE_PLUGIN_ROOT}` y `os.homedir()`.
- `install-state.json` **sí** guarda rutas absolutas del `$HOME` de origen; `bootstrap.sh` las reescribe al `$HOME` local.
- La memoria vive bajo `projects/<slug>/`, donde el slug deriva del `$HOME`; el bootstrap lo recalcula.

## Terceros

ECC, ponytail y las skills de Emil Kowalski se incluyen bajo MIT. Ver [NOTICE.md](NOTICE.md).
