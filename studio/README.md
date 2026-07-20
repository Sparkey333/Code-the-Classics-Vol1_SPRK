# Classics Studio

Browser dashboard for playing **Code the Classics** Volume I & II games on a live canvas.

## Run

```bash
python3 -m pip install --user -r requirements.txt
./start.sh
```

Open http://localhost:8787

Requires `Xvnc` (TigerVNC) and `pgzrun` (Pygame Zero). The studio starts a virtual display, launches the selected game with Pygame Zero, and streams it into the page via noVNC over `/websockify`.

noVNC client code under `static/novnc/` is from https://github.com/novnc/noVNC (MPL-2.0).
