#!/usr/bin/env bash
# Copia el harness vivo de esta máquina al repo. Ejecutar antes de commitear.
set -euo pipefail
DEST="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/home"

for d in agents commands scripts hooks rules ecc skills .agents skills-library agents-library commands-library; do
  [ -d "$HOME/.claude/$d" ] && mkdir -p "$DEST/.claude/$d" && rsync -a --delete "$HOME/.claude/$d/" "$DEST/.claude/$d/"
done
for f in AGENTS.md README.md marketplace.json plugin.json PLUGIN_SCHEMA_NOTES.md the-security-guide.md; do
  [ -f "$HOME/.claude/$f" ] && cp -a "$HOME/.claude/$f" "$DEST/.claude/$f"
done
cp -a "$HOME/.claude/settings.json" "$DEST/.claude/settings.json"
# Portabilidad y secretos del settings versionado (la copia viva no se toca):
#  - ECC 2.2.x embebe la ruta del HOME en base64: neutralizarla
#  - rutas absolutas del HOME en comandos propios (impeccable) -> $HOME
#  - mcpServers fuera: puede llevar tokens en la URL y nunca debe versionarse
python3 - "$DEST/.claude/settings.json" <<'PYEOF'
import json,re,sys
p=sys.argv[1]
s=json.load(open(p))
s.pop('mcpServers',None)
abs_home=re.compile(r"'(?:/Users/[^/']+|/home/[^/']+)/\.claude/([^']*)'")
for entries in s.get('hooks',{}).values():
    for e in entries:
        for h in e.get('hooks',[]):
            c=h.get('command','')
            c=re.sub(r"Buffer\.from\('[A-Za-z0-9+/=]+','base64'\)","Buffer.from('','base64')",c)
            c=abs_home.sub(lambda m:'"$HOME/.claude/%s"'%m.group(1),c)
            h['command']=c
with open(p,'w') as f:
    json.dump(s,f,indent=2,ensure_ascii=False); f.write('\n')
PYEOF
rsync -a --delete "$HOME/.agents/skills/" "$DEST/.agents/skills/"

# Pi: guardar solo settings sin identificador local y extensiones propias.
if [ -f "$HOME/.pi/agent/settings.json" ]; then
  mkdir -p "$DEST/.pi/agent"
  python3 - "$HOME/.pi/agent/settings.json" "$DEST/.pi/agent/settings.json" <<'PYEOF'
import json,sys
settings=json.load(open(sys.argv[1]))
settings.pop('deviceId',None)
with open(sys.argv[2],'w') as f:
    json.dump(settings,f,indent=2)
    f.write('\n')
PYEOF
fi
if [ -d "$HOME/.claude/.pi/extensions" ]; then
  mkdir -p "$DEST/.pi/agent/extensions"
  rsync -a --delete "$HOME/.claude/.pi/extensions/" "$DEST/.pi/agent/extensions/"
fi

SLUG=$(printf '%s' "$HOME" | tr '/' '-')
MEM="$HOME/.claude/projects/$SLUG/memory"
[ -d "$MEM" ] && rsync -a --delete "$MEM/" "$DEST/.claude/memory/"


# Registrar qué skills del store comun se comparten con Codex/OpenCode
: > "$(dirname "$DEST")/shared-skills.txt"
for h in "$HOME/.codex/skills" "$HOME/.opencode/skills"; do
  [ -d "$h" ] || continue
  for l in "$h"/*; do
    [ -L "$l" ] && readlink "$l" | grep -q '\.agents/skills/' && basename "$l"  || true
  done
done | sort -u > "$(dirname "$DEST")/shared-skills.txt"
echo "==> $(wc -l < "$(dirname "$DEST")/shared-skills.txt") skills compartidas registradas"


# Codex y OpenCode: solo configuracion
for h in codex opencode; do
  [ -d "$HOME/.$h" ] || continue
  if [ "$h" = codex ]; then DIRS="skills agents mcp-configs memories"; FILES="config.toml AGENTS.md ecc-install-state.json"; else DIRS="skills scripts commands hooks tools prompts dist plugin"; FILES="opencode.json ecc-install-state.json AGENTS.md the-security-guide.md package.json"; fi
  mkdir -p "$DEST/.$h"
  for d in $DIRS; do [ -d "$HOME/.$h/$d" ] && mkdir -p "$DEST/.$h/$d" && rsync -a --delete "$HOME/.$h/$d/" "$DEST/.$h/$d/"; done
  for f in $FILES; do [ -f "$HOME/.$h/$f" ] && cp -a "$HOME/.$h/$f" "$DEST/.$h/$f"; done
done

echo "==> harness sincronizado al repo. Revisa 'git status' antes de commitear."
