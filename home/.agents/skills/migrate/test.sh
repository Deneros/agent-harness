#!/usr/bin/env bash
# Tests de la lógica local de migrate.sh (no tocan la red). Uso: ./test.sh
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
# shellcheck source=migrate.sh
source ./migrate.sh

fails=0
check() { # check <nombre> <esperado> <obtenido>
  if [ "$2" = "$3" ]; then echo "ok   $1"; else echo "FAIL $1: esperado '$2', obtuvo '$3'"; fails=$((fails+1)); fi
}

T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT

# encode_path replica el nombre de carpeta que usa Claude Code en ~/.claude/projects
check "encode home"      "-home-acris"                 "$(encode_path /home/acris)"
check "encode proyecto"  "-home-acris-projects-a-b-c"  "$(encode_path /home/acris/projects/a.b_c)"

# pick_via: auto elige git solo si hay repo con origin
mkdir -p "$T/plain" "$T/repo"
git -C "$T/repo" init -q && git -C "$T/repo" remote add origin https://example.invalid/r.git
mkdir -p "$T/noorigin" && git -C "$T/noorigin" init -q
check "auto sin repo"        "sync" "$(pick_via auto "$T/plain")"
check "auto repo+origin"     "git"  "$(pick_via auto "$T/repo")"
check "auto repo sin origin" "sync" "$(pick_via auto "$T/noorigin")"
check "forzado sync"         "sync" "$(pick_via sync "$T/repo")"

# safe_sync_dir: nunca sincronizar $HOME ni / completos
safe_sync_dir "$HOME" 2>/dev/null; check "rechaza HOME" "1" "$?"
safe_sync_dir / 2>/dev/null;       check "rechaza raiz" "1" "$?"
safe_sync_dir "$T/plain";          check "acepta proyecto" "0" "$?"

# find_session: la más reciente del proyecto, o la pedida si existe
P="$T/projects/$(encode_path /x/y)"; mkdir -p "$P"
touch -d '2 hours ago' "$P/aaa.jsonl"; touch "$P/bbb.jsonl"
check "sesion mas reciente" "bbb" "$(PROJECTS_ROOT="$T/projects" find_session /x/y "")"
check "sesion pedida"       "aaa" "$(PROJECTS_ROOT="$T/projects" find_session /x/y aaa)"
PROJECTS_ROOT="$T/projects" find_session /x/y zzz >/dev/null 2>&1; check "sesion inexistente" "1" "$?"

# sync_session con un SSH falso que ejecuta local: copia el .jsonl aunque no exista la carpeta
# de la sesión, bajo set -eo pipefail como corre main
fake_ssh() { shift; bash -c "$*"; }
out="$(set -eo pipefail; SSH_CMD=fake_ssh HOST=h PROJECTS_ROOT="$T/projects" ENC="$(encode_path /x/y)" \
  SID=aaa REMOTE_HOME="$T/remote"; sync_session 2>/dev/null && echo copied)"
check "sesion sin carpeta" "copied" "$out"
check "jsonl en destino" "yes" "$([ -f "$T/remote/.claude/projects/$(encode_path /x/y)/aaa.jsonl" ] && echo yes)"
mkdir -p "$P/bbb/subagents" && touch "$P/bbb/subagents/x.jsonl"
(set -eo pipefail; SSH_CMD=fake_ssh HOST=h PROJECTS_ROOT="$T/projects" ENC="$(encode_path /x/y)" \
  SID=bbb REMOTE_HOME="$T/remote"; sync_session 2>/dev/null)
check "carpeta de sesion" "yes" "$([ -f "$T/remote/.claude/projects/$(encode_path /x/y)/bbb/subagents/x.jsonl" ] && echo yes)"

echo; [ "$fails" -eq 0 ] && echo "todos los tests pasan" || { echo "$fails fallos"; exit 1; }
