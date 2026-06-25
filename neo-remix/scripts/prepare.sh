#!/usr/bin/env bash
# One-shot Neo Remix workspace bootstrap
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

pip install -q -r neo-remix/requirements.txt
python3 neo-remix/scripts/build_manifest.py
python3 neo-remix/scripts/setup_games.py
python3 neo-remix/scripts/generate_neo_assets.py
python3 neo-remix/scripts/validate_assets.py

echo ""
echo "Neo Remix ready. Launch hub: cd neo-remix && pgzrun hub.py"
echo ""
echo "AI sprites: cp neo-remix/config/api_keys.example.env neo-remix/.env"
echo "            python3 neo-remix/scripts/link_api_keys.py"
echo "            python3 neo-remix/scripts/generate_ai_sprites.py --game boing --limit 5"
