#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
CACHE="${PIPER_CACHE:-$ROOT/.demo-cache}"
CAPTURES="$ROOT/demo/captures"
OUTPUT="$ROOT/DEMOS/exerx-eye-v10-piper-hq-demo.mp4"
PORT="${DEMO_PORT:-8017}"

for tool in python3 node npm ffmpeg ffprobe curl; do
  command -v "$tool" >/dev/null || { echo "Missing required command: $tool"; exit 1; }
done

mkdir -p "$CAPTURES" "$ROOT/DEMOS" "$CACHE"

if [[ "${DEMO_SKIP_SETUP:-0}" != "1" ]]; then
  if [[ ! -x .demo-venv/bin/python ]]; then
    python3 -m venv .demo-venv
  fi
  .demo-venv/bin/python -m pip install -q --upgrade pip
  .demo-venv/bin/python -m pip install -q -r requirements.txt
  [[ -f package.json ]] || npm init -y >/dev/null 2>&1
  npm install --silent
  npx playwright install chromium
  PYTHON="$ROOT/.demo-venv/bin/python"
else
  PYTHON="${DEMO_PYTHON:-python3}"
fi

bash demo/fetch_piper.sh
PIPER_BIN="$(cat "$CACHE/PIPER_BIN")"
PIPER_MODEL="$(cat "$CACHE/PIPER_MODEL")"
PIPER_CONFIG="$(cat "$CACHE/PIPER_CONFIG")"

rm -f "$CACHE/demo.db"
rm -rf "$CAPTURES" "$ROOT/demo/render"
mkdir -p "$CAPTURES"

cleanup() {
  if [[ -n "${APP_PID:-}" ]]; then kill "$APP_PID" 2>/dev/null || true; fi
}
trap cleanup EXIT

EXERCISE_DB_PATH="$CACHE/demo.db" \
EXERXEYE_SECRET="exerxeye-hq-demo-secret" \
PORT="$PORT" \
"$PYTHON" app.py >"$CACHE/app.log" 2>&1 &
APP_PID=$!

for _ in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:$PORT/health" >/dev/null; then break; fi
  sleep 1
done
curl -fsS "http://127.0.0.1:$PORT/health" >/dev/null || {
  cat "$CACHE/app.log"; echo "Demo app failed to start"; exit 1;
}

DEMO_BASE_URL="http://127.0.0.1:$PORT" \
DEMO_CAPTURE_DIR="$CAPTURES" \
node demo/capture_demo.cjs

kill "$APP_PID" 2>/dev/null || true
APP_PID=""

"$PYTHON" demo/render_demo.py \
  --piper "$PIPER_BIN" \
  --model "$PIPER_MODEL" \
  --config "$PIPER_CONFIG" \
  --output "$OUTPUT"

echo
echo "HQ demo ready: $OUTPUT"
ffprobe -v error -show_entries format=duration,size -show_entries stream=codec_name,width,height -of default=nw=1 "$OUTPUT"
