#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CACHE="${PIPER_CACHE:-$ROOT/.demo-cache}"
PIPER_HOME="$CACHE/piper-bin"
VOICE_HOME="$CACHE/voices"
mkdir -p "$PIPER_HOME" "$VOICE_HOME"

PIPER_BIN="$PIPER_HOME/piper/piper"
MODEL="$VOICE_HOME/en_US-ryan-high.onnx"
CONFIG="$VOICE_HOME/en_US-ryan-high.onnx.json"
MODEL_CARD="$VOICE_HOME/en_US-ryan-high.MODEL_CARD"

if [[ ! -x "$PIPER_BIN" ]]; then
  echo "Downloading Piper v1.2.0 for Linux amd64..."
  curl -fL --retry 4 --retry-delay 2 \
    https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_amd64.tar.gz \
    -o "$CACHE/piper_amd64.tar.gz"
  rm -rf "$PIPER_HOME/piper"
  tar -xzf "$CACHE/piper_amd64.tar.gz" -C "$PIPER_HOME"
  chmod +x "$PIPER_BIN"
fi

BASE="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high"
if [[ ! -s "$MODEL" ]]; then
  echo "Downloading Piper high-quality Ryan voice (~121 MB)..."
  curl -fL --retry 4 --retry-delay 2 "$BASE/en_US-ryan-high.onnx?download=true" -o "$MODEL"
fi
if [[ ! -s "$CONFIG" ]]; then
  curl -fL --retry 4 --retry-delay 2 "$BASE/en_US-ryan-high.onnx.json?download=true" -o "$CONFIG"
fi
if [[ ! -s "$MODEL_CARD" ]]; then
  curl -fL --retry 4 --retry-delay 2 "$BASE/MODEL_CARD?download=true" -o "$MODEL_CARD" || true
fi

printf '%s\n' "$PIPER_BIN" > "$CACHE/PIPER_BIN"
printf '%s\n' "$MODEL" > "$CACHE/PIPER_MODEL"
printf '%s\n' "$CONFIG" > "$CACHE/PIPER_CONFIG"
echo "Piper voice ready: en_US-ryan-high"
