#!/usr/bin/env bash
# Boot Code the Classics Studio dashboard + live game canvas.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STUDIO="$ROOT/studio"
export PATH="${HOME}/.local/bin:/usr/local/bin:${PATH}"
export STUDIO_HOST="${STUDIO_HOST:-0.0.0.0}"
export STUDIO_PORT="${STUDIO_PORT:-8787}"
export STUDIO_DISPLAY="${STUDIO_DISPLAY:-42}"
export STUDIO_VNC_PORT="${STUDIO_VNC_PORT:-5942}"
export STUDIO_WS_PORT="${STUDIO_WS_PORT:-6080}"
export STUDIO_GEOMETRY="${STUDIO_GEOMETRY:-960x540}"
export SDL_AUDIODRIVER="${SDL_AUDIODRIVER:-dummy}"

if ! command -v Xvnc >/dev/null 2>&1; then
  echo "Xvnc (TigerVNC) is required."
  exit 1
fi
if ! command -v websockify >/dev/null 2>&1; then
  echo "websockify is required."
  exit 1
fi
if ! command -v pgzrun >/dev/null 2>&1; then
  echo "pgzrun not found. Install with: python3 -m pip install --user pgzero pygame"
  exit 1
fi
if ! command -v uvicorn >/dev/null 2>&1; then
  echo "uvicorn not found. Install with: python3 -m pip install --user -r studio/requirements.txt"
  exit 1
fi

cd "$STUDIO"
echo "Classics Studio → http://${STUDIO_HOST}:${STUDIO_PORT}"
echo "VNC stream     → ws://localhost:${STUDIO_WS_PORT}/  (display ${STUDIO_DISPLAY})"
exec python3 -m uvicorn server:app --host "$STUDIO_HOST" --port "$STUDIO_PORT"
