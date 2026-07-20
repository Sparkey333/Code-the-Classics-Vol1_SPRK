# Code the Classics

Assets and playable games from the Raspberry Pi Press books.

## Volume I (existing)

Classic games at the repo root (`boing-master`, `bunner-master`, `cavern-master`, `myriapod-master`, `soccer-master`).

Book: https://magazine.raspberrypi.com/books/code-the-classics-vol-I-2ed

## Volume II (official originals)

Unmodified sources and assets from the official repo:

https://github.com/raspberrypipress/Code-the-Classics-Vol2

Copied into `Code-the-Classics-Vol2/` as published (five games + cover art).

| Game | Inspired by | Run |
| --- | --- | --- |
| **Avenger** | Defender | `./Code-the-Classics-Vol2/play.sh avenger` |
| **Beat Streets** | Double Dragon | `./Code-the-Classics-Vol2/play.sh beatstreets` |
| **Eggzy** | Dizzy | `./Code-the-Classics-Vol2/play.sh eggzy` |
| **Kinetix** | Arkanoid | `./Code-the-Classics-Vol2/play.sh kinetix` |
| **Leading Edge** | Pole Position | `./Code-the-Classics-Vol2/play.sh leadingedge` |

### Setup (once)

```bash
python3 -m venv .venv
.venv/bin/pip install -r Code-the-Classics-Vol2/requirements.txt
```

Requires a graphical desktop (or X11 / Wayland). On Raspberry Pi / Linux / macOS / Windows with Python 3.6+ and Pygame Zero 1.2+.

You can also run from a game folder:

```bash
cd Code-the-Classics-Vol2/avenger
pgzrun avenger.py
```

## Classics Studio (play in the browser)

Boot a local studio dashboard with a live game canvas (TigerVNC + noVNC):

```bash
python3 -m pip install --user -r studio/requirements.txt
./studio/start.sh
```

Then open **http://localhost:8787** — pick a Vol I or Vol II game from the library and play it on the canvas.

### Book / ebook (PDF)

The Volume II **ebook PDF is not a public free download**. Raspberry Pi Press offers it as a free ebook for magazine contributors / print subscribers:

- Book page: https://magazine.raspberrypi.com/books/code-the-classics-vol-ii
- Print store: https://store.rpipress.cc/products/code-the-classics-volume-ii
- Contributor ebook access: https://magazine.raspberrypi.com/books/code-the-classics-vol-ii/ebook

Game source and assets are freely available from the GitHub repo above (included here unchanged).
