#!/usr/bin/env bash
# migrate.sh — mueve una sesión de Claude Code a otro host (Tailscale/SSH) y la retoma allá.
# Uso: migrate.sh <host> [--session ID] [--dir PATH] [--via auto|git|sync] [--no-code]
#                        [--with-env] [--mux tmux|herdr] [--no-rc] [--dry-run]

PROJECTS_ROOT="${PROJECTS_ROOT:-$HOME/.claude/projects}"
EXCLUDES=(node_modules .venv venv dist build target .next .turbo __pycache__ .gradle)

die() { echo "migrate: $*" >&2; exit 1; }
log() { echo "==> $*" >&2; }

# --- lógica local (cubierta por test.sh) ------------------------------------

# Claude Code nombra la carpeta del proyecto cambiando todo lo no alfanumérico por '-'
encode_path() { printf '%s' "$1" | sed 's/[^a-zA-Z0-9]/-/g'; }

pick_via() { # pick_via <auto|git|sync> <dir>
  if [ "$1" != auto ]; then echo "$1"; return; fi
  if git -C "$2" rev-parse --is-inside-work-tree >/dev/null 2>&1 \
     && git -C "$2" remote get-url origin >/dev/null 2>&1; then echo git; else echo sync; fi
}

safe_sync_dir() { # nunca copiar $HOME ni / completos
  local d; d="$(cd "$1" && pwd -P)"
  case "$d" in
    / | "$(cd "$HOME" && pwd -P)")
      echo "migrate: no sincronizo '$d' completo; usa --no-code o --dir <proyecto>" >&2; return 1 ;;
  esac
}

find_session() { # find_session <dir> <id|""> -> id
  local proj f; proj="$PROJECTS_ROOT/$(encode_path "$1")"
  if [ -n "$2" ]; then
    [ -f "$proj/$2.jsonl" ] || { echo "migrate: no existe la sesión $2 en $proj" >&2; return 1; }
    echo "$2"; return
  fi
  f="$(ls -t "$proj"/*.jsonl 2>/dev/null | head -1)"
  [ -n "$f" ] || { echo "migrate: no hay sesiones en $proj" >&2; return 1; }
  basename "$f" .jsonl
}

# --- transporte ---------------------------------------------------------------

rsh() { $SSH_CMD "$HOST" "$@"; }   # SSH_CMD se separa en palabras a propósito
q() { printf '%q ' "$@"; }

copy_dir() { # copy_dir <src> <dest> <exclude...> — rsync si ambos lados lo tienen, si no tar por ssh
  local src=$1 dest=$2 ex=() e; shift 2
  rsh "mkdir -p $(q "$dest")"
  if [ "$USE_RSYNC" = 1 ]; then
    for e in "$@"; do ex+=(--exclude "$e"); done
    rsync -az "${ex[@]}" -e "$SSH_CMD" "$src/" "$HOST:$dest/"
  else
    for e in "$@"; do ex+=("--exclude=$e"); done
    tar -C "$src" "${ex[@]}" -czf - . | rsh "tar -C $(q "$dest") -xzf -"
  fi
}

copy_files() { # copy_files <base> <dest> < rutas relativas separadas por NUL
  local list; list="$(mktemp)"; cat > "$list"
  if [ -s "$list" ]; then
    rsh "mkdir -p $(q "$2")"
    tar -C "$1" --null -T "$list" -czf - | rsh "tar -C $(q "$2") -xzf -"
  fi
  rm -f "$list"
}

env_files() { # archivos .env* del proyecto, relativos y separados por NUL
  (cd "$1" && find . -maxdepth 3 -name '.env*' -type f -not -path '*/node_modules/*' -print0)
}

# --- pasos remotos ------------------------------------------------------------

remote_preflight() { # imprime clave=valor
  rsh 'bash -l -s' <<'EOF'
echo "home=$HOME"
C="$(command -v claude || true)"; echo "claude=$C"
if [ -n "$C" ] && "$C" auth status 2>/dev/null | grep -q '"loggedIn": true'; then echo login=1; else echo login=0; fi
for t in tmux herdr git gh rsync; do echo "$t=$(command -v "$t" || true)"; done
if command -v gh >/dev/null && gh auth status >/dev/null 2>&1; then echo gh_auth=1; else echo gh_auth=0; fi
EOF
}

sync_code_git() {
  local root branch url
  root="$(git -C "$DIR" rev-parse --show-toplevel)"
  branch="$(git -C "$root" branch --show-current)"
  [ -n "$branch" ] || die "HEAD desacoplado en $root; cámbiate a una rama"
  url="$(git -C "$root" remote get-url origin)"
  log "git push origin $branch"
  git -C "$root" push -u origin "$branch"
  rsh "bash -l -s -- $(q "$root" "$url" "$branch")" <<'EOF'
set -e; root=$1 url=$2 branch=$3
if [ ! -d "$root/.git" ]; then
  mkdir -p "$(dirname "$root")"
  if command -v gh >/dev/null && gh auth status >/dev/null 2>&1; then gh repo clone "$url" "$root"
  else git clone "$url" "$root"; fi
fi
cd "$root"
[ -z "$(git status --porcelain)" ] || { echo "migrate: el repo remoto tiene cambios sin commitear: $root" >&2; exit 1; }
git fetch -q origin "$branch"
git checkout -q "$branch" 2>/dev/null || git checkout -q -b "$branch" "origin/$branch"
git merge -q --ff-only "origin/$branch"
EOF
  # Lo no commiteado viaja aparte, sin tocar el historial del repo.
  # ponytail: los archivos borrados localmente no se borran en el destino.
  log "copiando cambios sin commitear"
  git -C "$root" ls-files -z -m -o --exclude-standard \
    | while IFS= read -r -d '' f; do if [ -e "$root/$f" ]; then printf '%s\0' "$f"; fi; done \
    | copy_files "$root" "$root"
  if [ "$WITH_ENV" = 1 ]; then env_files "$root" | copy_files "$root" "$root"; fi
}

sync_code_files() {
  safe_sync_dir "$DIR" || exit 1
  local ex=("${EXCLUDES[@]}")
  [ "$WITH_ENV" = 1 ] || ex+=('.env*')
  log "copiando $DIR ($( [ "$USE_RSYNC" = 1 ] && echo rsync || echo tar ))"
  copy_dir "$DIR" "$DIR" "${ex[@]}"
}

sync_session() {
  local proj="$PROJECTS_ROOT/$ENC" rel=".claude/projects/$ENC"
  log "copiando sesión $SID"
  { printf '%s\0' "$SID.jsonl"; if [ -d "$proj/$SID" ]; then printf '%s\0' "$SID"; fi; } \
    | copy_files "$proj" "$REMOTE_HOME/$rel"
}

launch_tmux() {
  rsh "bash -l -s -- $(q "$NAME" "$DIR" "$CLAUDE_BIN" "$SID" "$PROMPT" "$RC")" <<'EOF'
set -e; name=$1 dir=$2 claude=$3 sid=$4 prompt=$5 rc=$6
tmux has-session -t "$name" 2>/dev/null && { echo "migrate: ya existe la sesión tmux $name" >&2; exit 1; }
args=(--resume "$sid"); [ "$rc" = 1 ] && args+=(--remote-control "$name")
# 'exec bash -l' deja la ventana abierta si claude sale, para poder leer el error
tmux new-session -d -s "$name" -c "$dir" "$(printf '%q ' "$claude" "${args[@]}" "$prompt"); exec bash -l"
sleep 8
tmux capture-pane -p -t "$name" | grep -v '^\s*$' | tail -12
EOF
}

launch_herdr() {
  # ponytail: experimental. El servidor de herdr vive dentro de su TUI, así que si no
  # corre lo levanto en un tmux; y la forma del JSON de 'workspace create' sale de su --skill.
  rsh "bash -l -s -- $(q "$NAME" "$DIR" "$SID" "$PROMPT" "$RC")" <<'EOF'
set -e; name=$1 dir=$2 sid=$3 prompt=$4 rc=$5
if ! herdr status 2>/dev/null | grep -q 'status: running'; then
  tmux new-session -d -s herdr herdr; sleep 3
fi
args=(--resume "$sid"); [ "$rc" = 1 ] && args+=(--remote-control "$name")
pane="$(herdr workspace create --cwd "$dir" --label "$name" --no-focus \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["result"]["root_pane"]["pane_id"])')"
herdr agent start "$name" --kind claude --pane "$pane" --timeout 60000 -- "${args[@]}"
herdr agent prompt "$name" "$prompt"
herdr agent get "$name"
EOF
}

# --- main -----------------------------------------------------------------------

main() {
  set -euo pipefail
  HOST="" SID="" DIR="$PWD" VIA=auto NO_CODE=0 WITH_ENV=0 MUX=tmux RC=1 DRY=0
  while [ $# -gt 0 ]; do
    case "$1" in
      --session) SID=$2; shift ;;
      --dir) DIR="$(cd "$2" && pwd)"; shift ;;
      --via) VIA=$2; shift ;;
      --no-code) NO_CODE=1 ;;
      --with-env) WITH_ENV=1 ;;
      --mux) MUX=$2; shift ;;
      --no-rc) RC=0 ;;
      --dry-run) DRY=1 ;;
      -h|--help) sed -n 2,4p "$0"; exit 0 ;;
      -*) die "opción desconocida: $1" ;;
      *) HOST=$1 ;;
    esac
    shift
  done
  [[ "$HOST" =~ ^[A-Za-z0-9._@-]+$ ]] || die "falta el host (o tiene caracteres inválidos)"
  [[ "$VIA" =~ ^(auto|git|sync)$ ]] || die "--via debe ser auto, git o sync"
  [[ "$MUX" =~ ^(tmux|herdr)$ ]] || die "--mux debe ser tmux o herdr"

  ENC="$(encode_path "$DIR")"
  SID="$(find_session "$DIR" "$SID")" || exit 1
  [[ "$SID" =~ ^[A-Za-z0-9-]+$ ]] || die "id de sesión inválido: $SID"
  NAME="claude-${SID:0:8}"
  VIA="$(pick_via "$VIA" "$DIR")"

  if [ -n "${MIGRATE_SSH:-}" ]; then SSH_CMD=$MIGRATE_SSH
  elif tailscale status 2>/dev/null | awk '{print $2}' | grep -qx "${HOST#*@}"; then SSH_CMD="tailscale ssh"
  else SSH_CMD=ssh; fi

  log "chequeo previo en $HOST ($SSH_CMD)"
  declare -A R
  local k v
  while IFS='=' read -r k v; do R[$k]=$v; done < <(remote_preflight) || die "no pude conectarme a $HOST"
  REMOTE_HOME=${R[home]:-}
  CLAUDE_BIN=${R[claude]:-}
  [ -n "$REMOTE_HOME" ] || die "no pude conectarme a $HOST"
  [ -n "$CLAUDE_BIN" ] || die "$HOST no tiene Claude Code instalado"
  [ "${R[login]:-}" = 1 ] || die "Claude Code en $HOST no tiene sesión iniciada: corre 'claude' allá una vez"
  [ -n "${R[$MUX]:-}" ] || die "$HOST no tiene $MUX"
  [ "$MUX" = tmux ] || [ -n "${R[tmux]:-}" ] || die "--mux herdr necesita tmux en $HOST para levantar su servidor"
  # ponytail: el transcript guarda rutas absolutas; si el $HOME difiere habría que reescribir 'cwd'.
  case "$DIR" in "$HOME"/*|"$HOME") [ "$REMOTE_HOME" = "$HOME" ] \
    || die "el home remoto ($REMOTE_HOME) no coincide con el local ($HOME); aún no reescribo rutas" ;; esac
  if [ "$VIA" = git ] && [ "$NO_CODE" = 0 ]; then [ -n "${R[git]:-}" ] || die "$HOST no tiene git"; fi
  USE_RSYNC=0; if command -v rsync >/dev/null && [ -n "${R[rsync]:-}" ]; then USE_RSYNC=1; fi

  PROMPT="Esta sesión fue migrada desde $(hostname) a este host con /migrate. Antes de seguir: \
1) confirma que estás en $DIR y que el código está al día; \
2) instala las dependencias y herramientas que el proyecto necesite y falten aquí; \
3) revisa variables de entorno y servicios que la tarea requiera y avísame si falta algún secreto, sin inventarlo; \
4) después continúa la tarea pendiente donde quedó."

  cat >&2 <<PLAN
Plan de migración
  host     $HOST  (home $REMOTE_HOME, claude $CLAUDE_BIN)
  sesión   $SID
  carpeta  $DIR
  código   $([ "$NO_CODE" = 1 ] && echo "no se copia" || echo "$VIA$([ "$VIA" = sync ] && { [ "$USE_RSYNC" = 1 ] && echo " (rsync)" || echo " (tar por ssh)"; })")
  secretos $([ "$WITH_ENV" = 1 ] && echo ".env* incluidos" || echo "no se copian .env*")
  arranque $MUX '$NAME'$([ "$RC" = 1 ] && echo " + Remote Control")
PLAN
  [ "$DRY" = 1 ] && { log "dry-run: no se copió ni lanzó nada"; exit 0; }

  if [ "$NO_CODE" = 0 ]; then
    if [ "$VIA" = git ]; then sync_code_git; else sync_code_files; fi
  fi
  sync_session
  log "lanzando claude en $HOST"
  if [ "$MUX" = herdr ]; then launch_herdr; else launch_tmux; fi

  echo
  echo "Sesión migrada a $HOST. No la reanudes aquí: dos instancias sobre la misma sesión se desincronizan."
  if [ "$MUX" = herdr ]; then echo "  Ver:    $SSH_CMD $HOST -t herdr"
  else echo "  Ver:    $SSH_CMD $HOST -t tmux attach -t $NAME"; fi
  [ "$RC" = 1 ] && echo "  Móvil:  claude.ai/code → Remote Control → $NAME"
  echo "  Volver: desde $HOST, /migrate $(hostname)"
}

[[ "${BASH_SOURCE[0]}" == "$0" ]] && main "$@"
