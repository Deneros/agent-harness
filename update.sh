#!/usr/bin/env bash
# Copia el harness vivo de esta máquina al repo. Ejecutar antes de commitear.
set -euo pipefail
DEST="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/home"

for d in agents commands scripts hooks rules ecc skills .agents; do
  [ -d "$HOME/.claude/$d" ] && mkdir -p "$DEST/.claude/$d" && rsync -a --delete "$HOME/.claude/$d/" "$DEST/.claude/$d/"
done
for f in AGENTS.md README.md marketplace.json plugin.json PLUGIN_SCHEMA_NOTES.md the-security-guide.md; do
  [ -f "$HOME/.claude/$f" ] && cp -a "$HOME/.claude/$f" "$DEST/.claude/$f"
done
cp -a "$HOME/.claude/settings.json" "$DEST/.claude/settings.json"
rsync -a --delete "$HOME/.agents/skills/" "$DEST/.agents/skills/"

SLUG=$(printf '%s' "$HOME" | tr '/' '-')
MEM="$HOME/.claude/projects/$SLUG/memory"
[ -d "$MEM" ] && rsync -a --delete "$MEM/" "$DEST/.claude/memory/"


# Registrar qué skills del store comun se comparten con Codex/OpenCode
: > "$(dirname "$DEST")/shared-skills.txt"
for h in "$HOME/.codex/skills" "$HOME/.opencode/skills"; do
  [ -d "$h" ] || continue
  find "$h" -maxdepth 1 -type l -lname '*.agents/skills/*' -printf '%f\n' 2>/dev/null
done | sort -u > "$(dirname "$DEST")/shared-skills.txt"
echo "==> $(wc -l < "$(dirname "$DEST")/shared-skills.txt") skills compartidas registradas"

echo "==> harness sincronizado al repo. Revisa 'git status' antes de commitear."
