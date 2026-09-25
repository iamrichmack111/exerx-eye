#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV="${VENV:-.venv}"

if [[ ! -d "$VENV" ]]; then
  "$PYTHON_BIN" -m venv "$VENV"
fi

# shellcheck disable=SC1090
source "$VENV/bin/activate"

if ! python -c 'import flask' >/dev/null 2>&1; then
  python -m pip install --upgrade pip
  python -m pip install -r requirements.txt
fi

mkdir -p instance
if [[ -z "${EXERXEYE_SECRET:-}" ]]; then
  SECRET_FILE="instance/.secret"
  if [[ ! -s "$SECRET_FILE" ]]; then
    python - <<'PY' > "$SECRET_FILE"
import secrets
print(secrets.token_hex(32))
PY
    chmod 600 "$SECRET_FILE"
  fi
  export EXERXEYE_SECRET="$(cat "$SECRET_FILE")"
fi

export PORT="${PORT:-8000}"
exec python app.py
