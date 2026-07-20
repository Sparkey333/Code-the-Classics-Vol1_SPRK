"""Game catalog for Code the Classics Studio."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

GAMES = [
    {
        "id": "avenger",
        "title": "Avenger",
        "volume": 2,
        "inspired_by": "Defender",
        "blurb": "Fly a scrolling landscape and rescue humans from alien raids.",
        "dir": ROOT / "Code-the-Classics-Vol2" / "avenger",
        "script": "avenger.py",
        "thumb": "/thumbs/avenger.png",
        "controls": "Arrows move · Z / Space fire · X smart bomb",
    },
    {
        "id": "beatstreets",
        "title": "Beat Streets",
        "volume": 2,
        "inspired_by": "Double Dragon",
        "blurb": "Brawl through the streets and take down the crime boss.",
        "dir": ROOT / "Code-the-Classics-Vol2" / "beatstreets",
        "script": "beatstreets.py",
        "thumb": "/thumbs/beatstreets.png",
        "controls": "Arrows move · Z punch · X kick · C jump",
    },
    {
        "id": "eggzy",
        "title": "Eggzy",
        "volume": 2,
        "inspired_by": "Dizzy",
        "blurb": "Collect gems and outlast the clock in a haunted world.",
        "dir": ROOT / "Code-the-Classics-Vol2" / "eggzy",
        "script": "eggzy.py",
        "thumb": "/thumbs/eggzy.png",
        "controls": "Arrows move · Z / Space jump · X dash",
    },
    {
        "id": "kinetix",
        "title": "Kinetix",
        "volume": 2,
        "inspired_by": "Arkanoid",
        "blurb": "Break bricks, catch powerups, and survive every menace.",
        "dir": ROOT / "Code-the-Classics-Vol2" / "kinetix",
        "script": "kinetix.py",
        "thumb": "/thumbs/kinetix.png",
        "controls": "Left / Right move · Space launch",
    },
    {
        "id": "leadingedge",
        "title": "Leading Edge",
        "volume": 2,
        "inspired_by": "Pole Position",
        "blurb": "Race a pseudo-3D track and stay ahead of the pack.",
        "dir": ROOT / "Code-the-Classics-Vol2" / "leadingedge",
        "script": "leadingedge.py",
        "thumb": "/thumbs/leadingedge.png",
        "controls": "Left / Right steer · Up accelerate · Down brake",
    },
    {
        "id": "boing",
        "title": "Boing",
        "volume": 1,
        "inspired_by": "Pong",
        "blurb": "A two-bat classic. Keep the ball in play.",
        "dir": ROOT / "boing-master",
        "script": "boing.py",
        "thumb": "/thumbs/boing.png",
        "controls": "Player 1: A/Z · Player 2: K/M · Space serve",
    },
    {
        "id": "bunner",
        "title": "Bunner",
        "volume": 1,
        "inspired_by": "Frogger",
        "blurb": "Hop across traffic and river logs to the top.",
        "dir": ROOT / "bunner-master",
        "script": "bunner.py",
        "thumb": "/thumbs/bunner.png",
        "controls": "Arrow keys hop",
    },
    {
        "id": "cavern",
        "title": "Cavern",
        "volume": 1,
        "inspired_by": "Scramble",
        "blurb": "Pilot through a scrolling cavern and blast fuel tanks.",
        "dir": ROOT / "cavern-master",
        "script": "cavern.py",
        "thumb": "/thumbs/cavern.png",
        "controls": "Arrows fly · Space fire",
    },
    {
        "id": "myriapod",
        "title": "Myriapod",
        "volume": 1,
        "inspired_by": "Centipede",
        "blurb": "Blast the segmented invader before it reaches you.",
        "dir": ROOT / "myriapod-master",
        "script": "myriapod.py",
        "thumb": "/thumbs/myriapod.png",
        "controls": "Arrows move · Space fire",
    },
    {
        "id": "soccer",
        "title": "Soccer",
        "volume": 1,
        "inspired_by": "Sensible Soccer",
        "blurb": "Arcade football with crisp passes and sharp shots.",
        "dir": ROOT / "soccer-master",
        "script": "soccer.py",
        "thumb": "/thumbs/soccer.png",
        "controls": "Arrows move · Space kick / tackle",
    },
]


def list_games() -> list[dict]:
    out = []
    for g in GAMES:
        item = {k: v for k, v in g.items() if k not in ("dir", "script")}
        item["available"] = (g["dir"] / g["script"]).is_file()
        out.append(item)
    return out


def get_game(game_id: str) -> dict | None:
    for g in GAMES:
        if g["id"] == game_id:
            return g
    return None
