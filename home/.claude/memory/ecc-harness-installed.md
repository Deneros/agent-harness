---
name: ecc-harness-installed
description: "ECC agent harness installed globally for Claude, Codex, and OpenCode"
metadata: 
  node_type: memory
  type: project
  originSessionId: 82221210-0989-456a-9a4f-258d8aa7a5a7
---

On 2026-06-26 the ECC harness (github.com/affaan-m/ecc) was installed globally via `node scripts/install-apply.js`:
- **Claude** (`~/.claude/`): profile `developer` → 80 skills under `skills/ecc/`, 67 agents, 92 commands, 22 rules under `rules/ecc/`, 150 scripts under `scripts/`. Install-state: `~/.claude/ecc/install-state.json`.
- **Codex** (`~/.codex/`): profile `developer`. State: `~/.codex/ecc-install-state.json`.
- **OpenCode** (`~/.opencode/`): profile `opencode` (required `npm run build:opencode` first). State: `~/.opencode/ecc-install-state.json`.

Nicolás's 23 original skills are untouched (ECC is namespaced under `ecc/`).

**Hooks are ACTIVE** (activated 2026-06-26): all 28 ECC hooks merged into `~/.claude/settings.json` across PreToolUse, PostToolUse, PreCompact, SessionStart, SessionEnd, Stop, PostToolUseFailure. User chose to keep ALL enabled including the intrusive `gateguard-fact-force` — it BLOCKS the first Bash command and the first Edit per file each session until facts are presented (confirmed active in-session). To tame later: set `ECC_GATEGUARD=off` and/or add hook IDs to `ECC_DISABLED_HOOKS` in settings.json env. Backup of pre-hooks settings at `~/.claude/settings.json.bak.1782535374`. AgentShield scored hooks 100/100 (clean).

Security review before install found: no exfiltration/telemetry, clean npm deps (only @iarna/toml, ajv, sql.js, no preinstall), scary URLs were defensive IOC-scanning tests. Main concern is surface area, not malice. The repo's 222k GitHub stars look inflated (created 2026-01-18, only 1126 watchers) — trust the reviewed code, not the star count.

Related: [[user_profile]]
