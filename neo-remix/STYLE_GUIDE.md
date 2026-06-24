# Neo Remix — Art & Audio Style Guide

Unified creative direction for all five **Code the Classics Vol I** remakes in this collection.

## Brand Identity

| Element | Value |
|---------|-------|
| Collection name | **Neo Remix** |
| Tagline | *Classics, recharged.* |
| Era reference | Late-80s arcade DNA, 2020s neon synthwave finish |
| Mood | Fast, punchy, readable at a glance |

## Visual Language

### Palette (core)

| Role | Hex | Usage |
|------|-----|-------|
| Void Black | `#0B0E17` | Backgrounds, letterboxing |
| Deep Space | `#151B2E` | UI panels, playfield shadows |
| Neon Cyan | `#00F5FF` | Primary highlights, player accents |
| Hot Magenta | `#FF2E97` | Enemies, danger, score pops |
| Solar Gold | `#FFD447` | Pickups, bonuses, menu focus |
| Ghost White | `#E8EEFF` | HUD text, neutral sprites |
| Grid Violet | `#6B4CFF` | Secondary UI, grid lines |

Per-game accent colors layer on top (see `manifests/games.json`) so each title keeps a distinct silhouette while sharing chrome.

### Sprite Rules

1. **Silhouette first** — gameplay readability beats detail; every interactive object must read in under 100 ms.
2. **1px neon rim** — outer edge glow in the game’s accent color on dark fills.
3. **Flat shading** — max 3 tones per sprite; no photoreal gradients.
4. **Preserve hitboxes** — neo assets match original dimensions and anchor points exactly.
5. **Animation cadence** — keep original frame counts; add subtle pulse on idle loops where applicable.
6. **Digits & HUD** — use shared `shared/images/digit*.png` wherever possible (7-segment neon style).

### Resolution

| Game | Viewport | Notes |
|------|----------|-------|
| Boing | 800×480 | Landscape Pong variant |
| Bunner | 480×800 | Portrait endless hopper |
| Cavern | 800×480 | Landscape platformer |
| Myriapod | 480×800 | Portrait shooter |
| Soccer | 800×480 | Landscape sports |

## Audio Language

### Music

- **BPM band:** 118–132 per title
- **Instrumentation:** FM-style bass, gated pads, punchy drum machines
- **Structure:** 16-bar loop, intro sting on game start, breakdown on game over
- **Loudness target:** −14 LUFS integrated (streaming-friendly)

### SFX

| Category | Design |
|----------|--------|
| UI | Short blips, 80–120 ms, sine + noise layer |
| Impacts | Layered transient + sub thump; pitch scales with intensity |
| Pickups | Ascending two-note chime in game accent |
| Death / fail | Downward pitch bend, bit-crush tail |
| Ambient loops | Low-passed bed, −24 dB under music |

### File Format

- Music: `.ogg` Vorbis, 44.1 kHz stereo
- SFX: `.ogg` Vorbis, 44.1 kHz mono (stereo only for panning-critical sounds)
- Naming: `{event}{variant}.ogg` — e.g. `hit0.ogg`, `hit1.ogg`

## Neo Title Names

| Original | Neo Remix |
|----------|-----------|
| Boing! | Neo Boing |
| Infinite Bunner | Neo Bunner |
| Cavern | Neo Cavern |
| Myriapod | Neo Myriapod |
| Substitute Soccer | Neo Soccer |

## Asset Pipeline

```
classics-master/          # Original Code the Classics sources (read-only reference)
neo-remix/
  shared/                 # Cross-game UI, palette swatches, hub art
  games/<id>/             # Per-game code + remixed assets
  manifests/              # Machine-readable asset inventories
  scripts/                # Manifest build + neo asset generation
```

Run from repo root:

```bash
python3 neo-remix/scripts/build_manifest.py
python3 neo-remix/scripts/generate_neo_assets.py --all
python3 neo-remix/scripts/validate_assets.py
```

## Quality Checklist (per asset)

- [ ] Dimensions match manifest entry
- [ ] Transparent PNG where original was transparent
- [ ] `neo_status` set to `ready` in manifest after drop-in
- [ ] Playtested: no anchor drift, no collision regressions
- [ ] Audio normalized; no clipping
