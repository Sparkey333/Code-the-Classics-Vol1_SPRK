# Neo Remix

**Classics, recharged.** A unified remaster workspace for all five games from [*Code the Classics Vol I*](https://magazine.raspberrypi.com/books/code-the-classics-vol-I-2ed).

| # | Classic | Neo Remix | Viewport | Assets |
|---|---------|-----------|----------|--------|
| 1 | Boing! | **Neo Boing** | 800×480 | 49 sprites · 20 audio |
| 2 | Infinite Bunner | **Neo Bunner** | 480×800 | 129 sprites · 28 audio |
| 3 | Cavern | **Neo Cavern** | 800×480 | 169 sprites · 34 audio |
| 4 | Myriapod | **Neo Myriapod** | 480×800 | 329 sprites · 21 audio |
| 5 | Substitute Soccer | **Neo Soccer** | 800×480 | 167 sprites · 10 audio |

Original sources remain in `*-master/` folders for reference. All remixed work lives under `neo-remix/`.

## Quick Start

```bash
pip install -r neo-remix/requirements.txt

# 1. Inventory every sprite & sound
python3 neo-remix/scripts/build_manifest.py

# 2. Stage game code with Neo titles
python3 neo-remix/scripts/setup_games.py

# 3. Generate v1 neo sprites + copy audio placeholders
python3 neo-remix/scripts/generate_neo_assets.py --all

# 4. Verify nothing is missing
python3 neo-remix/scripts/validate_assets.py

# 5. Launch the collection hub
cd neo-remix && pgzrun hub.py
```

Run an individual title from its folder:

```bash
cd neo-remix/games/boing && pgzrun boing.py
```

## Project Layout

```
neo-remix/
├── hub.py                  # Collection launcher
├── STYLE_GUIDE.md          # Shared art & audio direction
├── requirements.txt
├── shared/                 # Cross-game UI (digits, hub art, palette)
├── games/
│   ├── boing/
│   ├── bunner/
│   ├── cavern/
│   ├── myriapod/
│   └── soccer/
├── manifests/              # Asset inventories (games.json + per-game)
└── scripts/
    ├── build_manifest.py
    ├── setup_games.py
    ├── generate_neo_assets.py
    └── validate_assets.py
```

## Asset Workflow

1. **Manifest** — `build_manifest.py` scans originals and writes `manifests/games.json` with dimensions, paths, and `neo_status`.
2. **Generate v1** — `generate_neo_assets.py` applies the Neo palette (neon rim, flat shading) as a baseline pass. Audio is copied as placeholders until remixed tracks land.
3. **Hand polish** — Artists replace files in `games/<id>/images/` and update `neo_status` to `ready` in the manifest.
4. **Validate** — `validate_assets.py` confirms every manifest entry exists on disk.

See [STYLE_GUIDE.md](STYLE_GUIDE.md) for palette, audio targets, and quality checklist.

## Replacing Assets

Drop finished PNG/OGG files into the matching `neo_path` from the manifest, then mark ready:

```bash
python3 -c "
import json
from pathlib import Path
p = Path('neo-remix/manifests/games.json')
m = json.loads(p.read_text())
for img in m['games']['boing']['images']:
    if img['id'] == 'ball':
        img['neo_status'] = 'ready'
p.write_text(json.dumps(m, indent=2) + '\n')
"
```

## License Note

Original game code and assets are from the Code the Classics book materials. Neo Remix derivative assets and tooling in this folder are part of this remaster project.
