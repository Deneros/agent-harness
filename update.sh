#!/usr/bin/env bash
# Copia el harness vivo de esta máquina al repo. Ejecutar antes de commitear.
set -euo pipefail
DEST="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/home"

for d in agents commands scripts hooks rules ecc skills; do
  rsync -a --delete "$HOME/.claude/$d/" "$DEST/.claude/$d/"
done
cp -a "$HOME/.claude/settings.json" "$DEST/.claude/settings.json"
rsync -a --delete "$HOME/.agents/skills/" "$DEST/.agents/skills/"

SLUG=$(printf '%s' "$HOME" | tr '/' '-')
MEM="$HOME/.claude/projects/$SLUG/memory"
[ -d "$MEM" ] && rsync -a --delete "$MEM/" "$DEST/.claude/memory/"

echo "==> harness sincronizado al repo. Revisa 'git status' antes de commitear."
