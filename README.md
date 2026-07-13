# Agent Harness

Portable quality-harness configuration for Claude Code, Codex, and OpenCode.

This repository contains templates and adapters only. It does not contain API
keys, authentication files, sessions, caches, metrics, or third-party ECC
runtime files.

## Components

- `claude/`: Claude Code hook template.
- `codex/`: Codex hook-adapter template.
- `opencode/`: OpenCode ECC parity plugin.
- `shared/`: common environment and safety guidance.

## Install

Install ECC separately, then run:

```bash
./install.sh
```

The installer copies templates to the user's home configuration directories.
Review the generated files before enabling them in a production environment.

## Environment

Set `ECC_ROOT` when ECC is installed outside `~/.opencode`:

```bash
export ECC_ROOT=/path/to/ecc-runtime
```

## Security

Never commit credentials, token files, session data, local MCP configuration,
or generated metrics. See `SECURITY.md`.
