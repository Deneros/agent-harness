#!/usr/bin/env bash
# Instala el harness de Claude Code en esta máquina. Idempotente.
set -euo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/home"
STAMP=$(date +%Y%m%d-%H%M%S)
BACKUP="$HOME/.claude-backup-$STAMP"

echo "==> destino: $HOME"

# 1. Respaldar lo que vamos a pisar
if [ -d "$HOME/.claude" ]; then
  mkdir -p "$BACKUP"
  for d in agents commands scripts hooks rules ecc skills settings.json; do
    [ -e "$HOME/.claude/$d" ] && cp -r "$HOME/.claude/$d" "$BACKUP/" || true
  done
  echo "==> respaldo en $BACKUP"
fi

# 2. Copiar el harness (los symlinks de skills/ son relativos y resuelven solos)
mkdir -p "$HOME/.agents" "$HOME/.claude"
cp -a "$SRC/.agents/skills" "$HOME/.agents/"
for d in agents commands scripts hooks rules ecc skills; do
  cp -a "$SRC/.claude/$d" "$HOME/.claude/"
done
cp -a "$SRC/.claude/settings.json" "$HOME/.claude/settings.json"

# 3. La memoria vive bajo un slug derivado del HOME, distinto en cada máquina
SLUG=$(printf '%s' "$HOME" | tr '/' '-')
MEM="$HOME/.claude/projects/$SLUG/memory"
mkdir -p "$MEM"
cp -a "$SRC/.claude/memory/." "$MEM/"
echo "==> memoria instalada en $MEM"

# 3b. install-state.json guarda rutas absolutas del HOME de origen: reescribirlas
STATE="$HOME/.claude/ecc/install-state.json"
if [ -f "$STATE" ]; then
  python3 - "$STATE" "$HOME" <<'PYEOF'
import sys
path,home=sys.argv[1],sys.argv[2]
raw=open(path).read()
old="/home/nicol"
if old!=home and old in raw:
    open(path,'w').write(raw.replace(old,home))
    print(f"==> install-state.json reescrito a {home}")
PYEOF
fi

# 3c. Compartir skills con Codex y OpenCode (solo si el host existe)
SHARED="$(dirname "$SRC")/shared-skills.txt"
if [ -f "$SHARED" ]; then
  for h in "$HOME/.codex/skills" "$HOME/.opencode/skills"; do
    [ -d "$h" ] || continue
    n=0
    while read -r sk; do
      [ -n "$sk" ] && [ -d "$HOME/.agents/skills/$sk" ] || continue
      ln -sfn "../../.agents/skills/$sk" "$h/$sk" && n=$((n+1))
    done < "$SHARED"
    echo "==> $n skills enlazadas en $h"
  done
fi

# 4. Ejecutables
find "$HOME/.claude/scripts" -name '*.sh' -exec chmod +x {} + 2>/dev/null || true

echo
echo "LISTO. Falta un paso manual:"
echo "  claude login    # las credenciales NUNCA se sincronizan"
echo
echo "Overrides propios de esta máquina: ~/.claude/settings.local.json (ignorado por git)"
