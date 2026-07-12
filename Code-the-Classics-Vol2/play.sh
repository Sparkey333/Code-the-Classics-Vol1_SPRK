#!/usr/bin/env bash
# Run a Code the Classics Volume II game with Pygame Zero.
# Usage: ./play.sh [avenger|beatstreets|eggzy|kinetix|leadingedge]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
GAME="${1:-}"

usage() {
  echo "Usage: $0 <game>"
  echo "Games: avenger  beatstreets  eggzy  kinetix  leadingedge"
  exit 1
}

[[ -n "$GAME" ]] || usage

case "$GAME" in
  avenger|beatstreets|eggzy|kinetix|leadingedge) ;;
  *)
    echo "Unknown game: $GAME"
    usage
    ;;
esac

if [[ -x "$ROOT/../.venv/bin/pgzrun" ]]; then
  PGZRUN="$ROOT/../.venv/bin/pgzrun"
elif command -v pgzrun >/dev/null 2>&1; then
  PGZRUN="$(command -v pgzrun)"
else
  echo "pgzrun not found. Install with:"
  echo "  python3 -m venv .venv && .venv/bin/pip install -r Code-the-Classics-Vol2/requirements.txt"
  exit 1
fi

cd "$ROOT/$GAME"
exec "$PGZRUN" "${GAME}.py"
