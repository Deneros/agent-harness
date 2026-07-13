#!/usr/bin/env sh
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

mkdir -p "$HOME/.claude" "$HOME/.codex" "$HOME/.config/opencode/plugins"
cp "$root/claude/settings.template.json" "$HOME/.claude/agent-harness.settings.json"
cp "$root/codex/config.template.toml" "$HOME/.codex/agent-harness.toml"
cp "$root/opencode/plugins/ecc-parity.js" "$HOME/.config/opencode/plugins/ecc-parity.js"

printf '%s\n' "Installed templates. Merge the Claude and Codex templates into their active configuration files."
