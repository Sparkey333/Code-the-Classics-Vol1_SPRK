# Neo Remix Collection Hub
# Launch any Code the Classics Vol I title from one menu.

import json
import subprocess
import sys
from pathlib import Path

WIDTH = 800
HEIGHT = 480
TITLE = "Neo Remix"

HUB_DIR = Path(__file__).resolve().parent
MANIFEST = HUB_DIR / "manifests" / "games.json"

CARD_W, CARD_H = 360, 220
CARD_GAP = 24
MARGIN = 40


class GameCard:
    def __init__(self, index, game_id, title, accent_hex, resolution):
        self.index = index
        self.game_id = game_id
        self.title = title
        self.accent = accent_hex
        col = index % 2
        row = index // 2
        self.x = MARGIN + col * (CARD_W + CARD_GAP) + CARD_W // 2
        self.y = 120 + row * (CARD_H + CARD_GAP) + CARD_H // 2
        self.w = CARD_W
        self.h = CARD_H
        self.resolution = resolution
        self.selected = index == 0

    def contains(self, pos):
        px, py = pos
        return (
            self.x - self.w // 2 <= px <= self.x + self.w // 2
            and self.y - self.h // 2 <= py <= self.y + self.h // 2
        )


def load_games():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cards = []
    for i, (gid, game) in enumerate(data["games"].items()):
        cards.append(
            GameCard(
                i,
                gid,
                game["neo_title"],
                game["accent_color"],
                game["resolution"],
            )
        )
    return cards


def launch_game(card):
    game_dir = HUB_DIR / "games" / card.game_id
    py_files = sorted(game_dir.glob("*.py"))
    if not py_files:
        print(f"No game found in {game_dir}")
        return
    entry = py_files[0]
    subprocess.Popen(
        [sys.executable, "-m", "pgzrun", str(entry)],
        cwd=str(game_dir),
    )


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


cards = load_games()
selected = 0


def draw():
    screen.fill((11, 14, 23))
    screen.blit("hub_logo", (0, 0))

    for i, card in enumerate(cards):
        is_sel = i == selected
        color = hex_to_rgb(card.accent)
        rect = Rect(
            (card.x - card.w // 2, card.y - card.h // 2),
            (card.w, card.h),
        )
        screen.draw.filled_rect(rect, (21, 27, 46))
        border = 3 if is_sel else 1
        screen.draw.rect(rect, color)
        if is_sel:
            screen.draw.rect(
                Rect((rect.x - 2, rect.y - 2), (rect.width + 4, rect.height + 4)),
                color,
            )

        screen.draw.text(
            card.title,
            (card.x - card.w // 2 + 20, card.y - 30),
            fontsize=28,
            color=(232, 238, 255),
        )
        res = card.resolution
        screen.draw.text(
            f"{res['width']}x{res['height']}",
            (card.x - card.w // 2 + 20, card.y + 10),
            fontsize=18,
            color=color,
        )
        screen.draw.text(
            "ENTER to play",
            (card.x - card.w // 2 + 20, card.y + 40),
            fontsize=16,
            color=(140, 150, 180),
        )

    screen.draw.text(
        "Arrow keys · select   ENTER · launch   ESC · quit",
        (MARGIN, HEIGHT - 36),
        fontsize=18,
        color=(140, 150, 180),
    )


def on_key_down(key):
    global selected
    if key == keys.ESCAPE:
        quit()
    elif key in (keys.LEFT, keys.UP):
        selected = (selected - 1) % len(cards)
    elif key in (keys.RIGHT, keys.DOWN):
        selected = (selected + 1) % len(cards)
    elif key in (keys.RETURN, keys.SPACE):
        launch_game(cards[selected])


def on_mouse_down(pos):
    global selected
    for i, card in enumerate(cards):
        if card.contains(pos):
            selected = i
            launch_game(card)
            break
