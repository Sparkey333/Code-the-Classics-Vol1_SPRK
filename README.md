# Code the Classics → Neo Remix

Assets and source from [*Code the Classics Vol I* (2nd ed.)](https://magazine.raspberrypi.com/books/code-the-classics-vol-I-2ed).

## Original games (`*-master/`)

| Folder | Game |
|--------|------|
| `boing-master/` | Boing! |
| `bunner-master/` | Infinite Bunner |
| `cavern-master/` | Cavern |
| `myriapod-master/` | Myriapod |
| `soccer-master/` | Substitute Soccer |

## Neo Remix remaster (`neo-remix/`)

All five titles are being recreated under the **Neo Remix** brand with unified neon synthwave art direction, revamped sprites, and remixed audio.

```bash
./neo-remix/scripts/prepare.sh      # build manifests + generate v1 assets
cd neo-remix && pgzrun hub.py       # launch collection hub
```

See [neo-remix/README.md](neo-remix/README.md) and [neo-remix/STYLE_GUIDE.md](neo-remix/STYLE_GUIDE.md) for the full pipeline.
