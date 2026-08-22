---
name: agent-harness-repo
description: Deneros/agent-harness (privado) es el snapshot portable del harness de Claude Code; bootstrap.sh restaura una máquina entera.
metadata: 
  node_type: memory
  type: project
  originSessionId: 947f5f8b-8c69-44fc-a78d-a2d0e5227021
  modified: 2026-08-22T06:03:29.193Z
---

`Deneros/agent-harness` (GitHub, **privado**) dejó de ser plantillas vacías el 2026-08-21 y ahora es el snapshot reproducible del harness completo: ECC v2.0.0 perfil `developer`, las 40 skills propias, `settings.json`, memoria del agente y las reglas.

- `./bootstrap.sh` restaura una máquina nueva (probado end-to-end); luego `claude login`, porque las credenciales nunca se versionan.
- `./update.sh` sincroniza la máquina viva de vuelta al repo y regenera `shared-skills.txt`.
- Es privado a propósito: lleva `user_profile.md` y la postura de seguridad completa (hooks y permisos). No hacerlo público sin sanear.

Detalles no obvios: `install-state.json` guarda rutas absolutas del `$HOME` de origen y el bootstrap las reescribe; la memoria vive bajo `projects/<slug>/`, donde el slug deriva del `$HOME`. `settings.json` no tiene rutas absolutas.

El instalador de ECC (`install-executor.js`) **no borra nada** — solo copia rutas gestionadas — así que los archivos propios en `rules/ecc/common/simplicity.md` y todo `rules/nicol/` sobreviven a un reinstall.

**Pendiente:** Codex (`~/.codex`) y OpenCode (`~/.opencode`) no están en el snapshot. Cada host tiene su propio `ecc-install-state.json` con perfiles distintos — OpenCode usa `full`, los otros `developer` — así que no se reproducen uno desde otro.

Ver [[ecc-harness-installed]] y [[aes-front-build-state]].
