"""Code the Classics Studio — launch Pygame Zero games into a browser canvas."""

from __future__ import annotations

import asyncio
import os
import signal
import subprocess
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from catalog import get_game, list_games

STUDIO_DIR = Path(__file__).resolve().parent
STATIC_DIR = STUDIO_DIR / "static"
DISPLAY_NUM = int(os.environ.get("STUDIO_DISPLAY", "42"))
DISPLAY = f":{DISPLAY_NUM}"
VNC_PORT = int(os.environ.get("STUDIO_VNC_PORT", str(5900 + DISPLAY_NUM)))
WEBSOCKIFY_PORT = int(os.environ.get("STUDIO_WS_PORT", "6080"))
GEOMETRY = os.environ.get("STUDIO_GEOMETRY", "960x540")
PGZRUN = os.environ.get("STUDIO_PGZRUN", "pgzrun")

_state: dict = {
    "xvnc": None,
    "websockify": None,
    "game": None,
    "active_game_id": None,
    "started_at": None,
    "last_error": None,
}


def _alive(proc: Optional[subprocess.Popen]) -> bool:
    return proc is not None and proc.poll() is None


def _stop_proc(proc: Optional[subprocess.Popen], grace: float = 1.0) -> None:
    if proc is None or proc.poll() is not None:
        return
    try:
        proc.send_signal(signal.SIGTERM)
        deadline = time.time() + grace
        while time.time() < deadline and proc.poll() is None:
            time.sleep(0.05)
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=2)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def stop_game() -> None:
    _stop_proc(_state.get("game"), grace=0.8)
    _state["game"] = None
    _state["active_game_id"] = None


def start_display() -> None:
    if _alive(_state.get("xvnc")):
        return

    lock = Path(f"/tmp/.X{DISPLAY_NUM}-lock")
    sock = Path(f"/tmp/.X11-unix/X{DISPLAY_NUM}")
    if lock.exists():
        lock.unlink(missing_ok=True)
    if sock.exists():
        sock.unlink(missing_ok=True)

    log = open("/tmp/studio-xvnc.log", "ab", buffering=0)
    _state["xvnc"] = subprocess.Popen(
        [
            "Xvnc",
            DISPLAY,
            "-geometry",
            GEOMETRY,
            "-depth",
            "24",
            "-SecurityTypes",
            "None",
            "-localhost",
            "yes",
            "-rfbport",
            str(VNC_PORT),
            "-AlwaysShared",
        ],
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    # Wait for X socket
    for _ in range(40):
        if sock.exists() and _alive(_state["xvnc"]):
            break
        time.sleep(0.1)
    else:
        raise RuntimeError("Xvnc failed to start — see /tmp/studio-xvnc.log")

    # Dark desktop backdrop
    subprocess.run(
        ["xsetroot", "-solid", "#0b1220"],
        env={**os.environ, "DISPLAY": DISPLAY},
        check=False,
    )


def start_websockify() -> None:
    if _alive(_state.get("websockify")):
        return
    log = open("/tmp/studio-websockify.log", "ab", buffering=0)
    _state["websockify"] = subprocess.Popen(
        [
            "websockify",
            "--web",
            str(STATIC_DIR / "novnc"),
            str(WEBSOCKIFY_PORT),
            f"localhost:{VNC_PORT}",
        ],
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    time.sleep(0.4)
    if not _alive(_state["websockify"]):
        raise RuntimeError("websockify failed — see /tmp/studio-websockify.log")


def launch_game(game_id: str) -> dict:
    game = get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Unknown game")
    script_path = game["dir"] / game["script"]
    if not script_path.is_file():
        raise HTTPException(status_code=404, detail="Game script missing")

    start_display()
    start_websockify()
    stop_game()

    env = os.environ.copy()
    env["DISPLAY"] = DISPLAY
    env["SDL_VIDEODRIVER"] = "x11"
    env["SDL_AUDIODRIVER"] = env.get("SDL_AUDIODRIVER", "dummy")
    # Keep window decorations off when possible
    env["SDL_VIDEO_WINDOW_POS"] = "0,0"

    log = open(f"/tmp/studio-game-{game_id}.log", "ab", buffering=0)
    proc = subprocess.Popen(
        [PGZRUN, game["script"]],
        cwd=str(game["dir"]),
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    time.sleep(0.6)
    if proc.poll() is not None:
        _state["last_error"] = f"Game exited immediately — see /tmp/studio-game-{game_id}.log"
        raise HTTPException(status_code=500, detail=_state["last_error"])

    _state["game"] = proc
    _state["active_game_id"] = game_id
    _state["started_at"] = time.time()
    _state["last_error"] = None
    return status_payload()


def status_payload() -> dict:
    game_proc = _state.get("game")
    if game_proc is not None and game_proc.poll() is not None:
        _state["game"] = None
        _state["active_game_id"] = None
    return {
        "display": DISPLAY,
        "vnc_port": VNC_PORT,
        "websockify_port": WEBSOCKIFY_PORT,
        "geometry": GEOMETRY,
        "display_up": _alive(_state.get("xvnc")),
        "stream_up": _alive(_state.get("websockify")),
        "active_game_id": _state.get("active_game_id"),
        "game_running": _alive(_state.get("game")),
        "started_at": _state.get("started_at"),
        "last_error": _state.get("last_error"),
        "ws_path": "/websockify",
    }


def shutdown_all() -> None:
    stop_game()
    _stop_proc(_state.get("websockify"))
    _stop_proc(_state.get("xvnc"))
    _state["websockify"] = None
    _state["xvnc"] = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        start_display()
        start_websockify()
    except Exception as exc:
        _state["last_error"] = str(exc)
    yield
    shutdown_all()


app = FastAPI(title="Code the Classics Studio", lifespan=lifespan)


@app.get("/api/games")
async def api_games():
    return {"games": list_games()}


@app.get("/api/status")
async def api_status():
    return status_payload()


@app.post("/api/play/{game_id}")
async def api_play(game_id: str):
    # Run blocking launch off the event loop
    return await asyncio.to_thread(launch_game, game_id)


@app.post("/api/stop")
async def api_stop():
    await asyncio.to_thread(stop_game)
    return status_payload()


@app.websocket("/websockify")
async def vnc_websockify(websocket: WebSocket):
    """Bridge browser noVNC client to the TigerVNC TCP port (websockify-compatible)."""
    await websocket.accept(subprotocol="binary")
    try:
        start_display()
    except Exception as exc:
        await websocket.close(code=1011, reason=str(exc)[:120])
        return

    try:
        reader, writer = await asyncio.open_connection("127.0.0.1", VNC_PORT)
    except OSError as exc:
        await websocket.close(code=1011, reason=f"VNC connect failed: {exc}"[:120])
        return

    async def client_to_vnc() -> None:
        try:
            while True:
                message = await websocket.receive()
                if message["type"] == "websocket.disconnect":
                    break
                data = message.get("bytes")
                if data is None and message.get("text") is not None:
                    data = message["text"].encode("latin-1")
                if data:
                    writer.write(data)
                    await writer.drain()
        except WebSocketDisconnect:
            pass
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    async def vnc_to_client() -> None:
        try:
            while True:
                data = await reader.read(65536)
                if not data:
                    break
                await websocket.send_bytes(data)
        except Exception:
            pass
        finally:
            try:
                await websocket.close()
            except Exception:
                pass

    await asyncio.wait(
        [
            asyncio.create_task(client_to_vnc()),
            asyncio.create_task(vnc_to_client()),
        ],
        return_when=asyncio.FIRST_COMPLETED,
    )
    writer.close()
    try:
        await writer.wait_closed()
    except Exception:
        pass


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/thumbs", StaticFiles(directory=STATIC_DIR / "thumbs"), name="thumbs")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("STUDIO_HOST", "0.0.0.0")
    port = int(os.environ.get("STUDIO_PORT", "8787"))
    uvicorn.run("server:app", host=host, port=port, reload=False)
