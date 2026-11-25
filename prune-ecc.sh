#!/usr/bin/env bash
# Recorta ECC a lo de uso diario. Idempotente: repetir tras cualquier instalacion
# o `repair` de ECC.
#
#  - Mueve a skills-library/, agents-library/ y commands-library/ lo que ECC
#    gestiona (segun ecc/install-state.json) y no esta en ecc-daily/*.txt.
#    Claude Code solo escanea skills/, agents/ y commands/, asi que la biblioteca
#    no cuesta contexto. Lo que ECC no gestiona (skills propias) no se toca.
#  - Borra reglas ECC que duplican o contradicen rules/nicol.
#  - Sustituye AGENTS.md y recorta rules/ecc/common/{agents,code-review}.md.
#
# Uso: ./prune-ecc.sh [raiz-claude]   (por defecto ~/.claude)
set -euo pipefail
ROOT="${1:-$HOME/.claude}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DAILY="$HERE/ecc-daily"

if [ ! -f "$ROOT/ecc/install-state.json" ]; then
  echo "==> prune-ecc: sin $ROOT/ecc/install-state.json, no se hace nada"
  exit 0
fi

python3 - "$ROOT" "$DAILY" <<'PY'
import json, os, shutil, sys

root, daily = sys.argv[1:3]
state = json.load(open(f"{root}/ecc/install-state.json"))

# destinationPath guarda el HOME de la maquina de origen: usar solo lo que sigue a /.claude/
managed = {"skills": set(), "agents": set(), "commands": set()}
for op in state["operations"]:
    dest = op["destinationPath"]
    if "/.claude/" not in dest:
        continue
    parts = dest.split("/.claude/", 1)[1].split("/")
    if parts[0] in managed and len(parts) > 1:
        name = parts[1][:-3] if parts[1].endswith(".md") else parts[1]
        managed[parts[0]].add(name)

moved = {}
for kind in managed:
    keep = {l.strip() for l in open(f"{daily}/{kind}.txt") if l.strip()}
    lib = f"{root}/{kind}-library"
    os.makedirs(lib, exist_ok=True)
    n = 0
    for name in sorted(managed[kind] - keep):
        for base in (f"{root}/{kind}/{name}", f"{root}/{kind}/{name}.md"):
            if not os.path.lexists(base):
                continue
            target = f"{lib}/{os.path.basename(base)}"
            if os.path.lexists(target):  # ya esta en la biblioteca: la copia activa sobra
                if os.path.isdir(base) and not os.path.islink(base):
                    shutil.rmtree(base)
                else:
                    os.remove(base)
            else:
                shutil.move(base, target)
            n += 1
    moved[kind] = n

# Reglas ECC que chocan con rules/nicol o ya no aplican
removed = 0
for f in ("README.md", "common/patterns.md", "common/performance.md", "common/hooks.md",
          "common/git-workflow.md", "common/development-workflow.md"):
    p = f"{root}/rules/ecc/{f}"
    if os.path.exists(p):
        os.remove(p)
        removed += 1

# Inmutabilidad: de "NUNCA" a preferencia (Django ORM, JPA y Dart mutan de forma idiomatica)
cs = f"{root}/rules/ecc/common/coding-style.md"
if os.path.exists(cs):
    t = open(cs).read()
    t2 = (t.replace("## Immutability (CRITICAL)", "## Immutability (preference)")
           .replace("ALWAYS create new objects, NEVER mutate existing ones:",
                    "PREFER creating new objects over mutating existing ones (follow the language or ORM idiom where mutation is natural):"))
    if t2 != t:
        open(cs, "w").write(t2)

print("==> prune-ecc: movidos a biblioteca "
      + ", ".join(f"{k}={v}" for k, v in moved.items()) + f"; reglas borradas={removed}")
PY

mkdir -p "$ROOT/rules/ecc/common"
install -m 0644 "$DAILY/AGENTS.md" "$ROOT/AGENTS.md"
install -m 0644 "$DAILY/rules-agents.md" "$ROOT/rules/ecc/common/agents.md"
install -m 0644 "$DAILY/rules-code-review.md" "$ROOT/rules/ecc/common/code-review.md"
echo "==> prune-ecc: AGENTS.md y reglas agents/code-review instalados"
