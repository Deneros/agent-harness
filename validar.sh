#!/usr/bin/env bash
# Comprobaciones locales del harness (antes vivian en GitHub Actions). Sin CI: se ejecutan
# a mano o desde el hook de pre-commit (instalar con: ./validar.sh --instalar-hook).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
if [ "${1:-}" = "--instalar-hook" ]; then
  printf '#!/usr/bin/env bash\nexec "$(git rev-parse --show-toplevel)/validar.sh"\n' > .git/hooks/pre-commit
  chmod +x .git/hooks/pre-commit; echo "hook de pre-commit instalado"; exit 0
fi
fallo=0
bash -n bootstrap.sh && bash -n update.sh && bash -n prune-ecc.sh || { echo "ERROR: sintaxis de los scripts"; fallo=1; }
if [ -f opencode/plugins/ecc-parity.js ] && command -v node >/dev/null; then node --check opencode/plugins/ecc-parity.js || fallo=1; fi
# Patrones anclados y con longitud realista (evita falsos positivos como "task-name").
if git grep -nIE '(ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{22,}|sk-ant-[A-Za-z0-9_-]{20,}|\bsk-[A-Za-z0-9]{32,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|pat=[A-Za-z0-9_-]{16,})'; then
  echo "ERROR: posible secreto en archivos versionados"; fallo=1; fi
if git ls-files | grep -E '(\.credentials\.json|settings\.local\.json|\.pem$)'; then
  echo "ERROR: archivo de credenciales versionado"; fallo=1; fi
[ "$fallo" = 0 ] && echo "validar: ok" || exit 1
