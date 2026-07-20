import RFB from "/static/novnc/core/rfb.js";

const gameListEl = document.getElementById("gameList");
const statusChip = document.getElementById("statusChip");
const statusText = document.getElementById("statusText");
const nowTitle = document.getElementById("nowTitle");
const nowBlurb = document.getElementById("nowBlurb");
const controlsLine = document.getElementById("controlsLine");
const canvasShell = document.getElementById("canvasShell");
const vncContainer = document.getElementById("vncContainer");
const stopBtn = document.getElementById("stopBtn");
const focusBtn = document.getElementById("focusBtn");

let games = [];
let volumeFilter = "all";
let activeId = null;
let rfb = null;
let connecting = false;

function wsUrl() {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  return `${proto}://${location.host}/websockify`;
}

function setStatus(state, text) {
  statusChip.dataset.state = state;
  statusText.textContent = text;
}

function renderGames() {
  const filtered = games.filter((g) => {
    if (volumeFilter === "all") return true;
    return String(g.volume) === String(volumeFilter);
  });

  gameListEl.innerHTML = filtered
    .map(
      (g) => `
      <li>
        <button class="game-item ${g.id === activeId ? "is-active" : ""}" data-id="${g.id}" type="button" ${
          g.available ? "" : "disabled"
        }>
          <img src="${g.thumb}" alt="" width="64" height="64" loading="lazy" />
          <span>
            <h3>${g.title}</h3>
            <p class="meta">Vol ${g.volume} · ${g.inspired_by}</p>
            <p class="blurb">${g.blurb}</p>
          </span>
        </button>
      </li>`
    )
    .join("");
}

async function fetchGames() {
  const res = await fetch("/api/games");
  const data = await res.json();
  games = data.games || [];
  renderGames();
}

async function fetchStatus() {
  const res = await fetch("/api/status");
  return res.json();
}

function disconnectVnc() {
  if (rfb) {
    try {
      rfb.disconnect();
    } catch (_) {
      /* ignore */
    }
    rfb = null;
  }
  vncContainer.innerHTML = "";
  canvasShell.classList.remove("is-live");
}

function connectVnc() {
  if (connecting || rfb) return;
  connecting = true;
  disconnectVnc();

  try {
    rfb = new RFB(vncContainer, wsUrl(), {
      wsProtocols: ["binary"],
    });
    rfb.scaleViewport = true;
    rfb.resizeSession = false;
    rfb.focusOnClick = true;
    rfb.background = "#02060c";

    rfb.addEventListener("connect", () => {
      connecting = false;
      canvasShell.classList.add("is-live");
      setStatus("playing", activeId ? `Playing ${activeId}` : "Canvas live");
    });

    rfb.addEventListener("disconnect", () => {
      connecting = false;
      rfb = null;
      canvasShell.classList.remove("is-live");
      if (activeId) {
        setStatus("ready", "Stream disconnected — relaunch a game");
      }
    });

    rfb.addEventListener("securityfailure", () => {
      connecting = false;
      setStatus("error", "VNC security failure");
    });
  } catch (err) {
    connecting = false;
    setStatus("error", err.message || "Could not connect canvas");
  }
}

async function playGame(id) {
  const game = games.find((g) => g.id === id);
  if (!game) return;

  setStatus("ready", `Launching ${game.title}…`);
  nowTitle.textContent = game.title;
  nowBlurb.textContent = game.blurb;
  controlsLine.textContent = game.controls;
  stopBtn.disabled = false;

  const res = await fetch(`/api/play/${id}`, { method: "POST" });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    setStatus("error", data.detail || "Launch failed");
    return;
  }

  activeId = id;
  renderGames();
  connectVnc();
  setStatus("playing", `Playing ${game.title}`);
  vncContainer.focus();
}

async function stopGame() {
  await fetch("/api/stop", { method: "POST" });
  activeId = null;
  stopBtn.disabled = true;
  nowTitle.textContent = "Select a game";
  nowBlurb.textContent = "Pick anything from the library to load it on the canvas.";
  controlsLine.textContent = "Controls appear once a game is running.";
  renderGames();
  disconnectVnc();
  setStatus("ready", "Display ready");
}

gameListEl.addEventListener("click", (event) => {
  const btn = event.target.closest(".game-item");
  if (!btn || btn.disabled) return;
  playGame(btn.dataset.id);
});

document.querySelectorAll(".vol-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".vol-tab").forEach((t) => t.classList.remove("is-active"));
    tab.classList.add("is-active");
    volumeFilter = tab.dataset.volume;
    renderGames();
  });
});

stopBtn.addEventListener("click", () => stopGame());
focusBtn.addEventListener("click", () => {
  if (!rfb) connectVnc();
  vncContainer.focus();
});

async function boot() {
  try {
    await fetchGames();
    const status = await fetchStatus();
    if (status.display_up && status.stream_up) {
      setStatus("ready", "Display ready — choose a game");
    } else if (status.last_error) {
      setStatus("error", status.last_error);
    } else {
      setStatus("ready", "Starting display stack…");
    }
    if (status.active_game_id) {
      activeId = status.active_game_id;
      const game = games.find((g) => g.id === activeId);
      if (game) {
        nowTitle.textContent = game.title;
        nowBlurb.textContent = game.blurb;
        controlsLine.textContent = game.controls;
        stopBtn.disabled = false;
        renderGames();
      }
      connectVnc();
    }
  } catch (err) {
    setStatus("error", err.message || "Studio boot failed");
  }
}

boot();
setInterval(async () => {
  try {
    const status = await fetchStatus();
    if (status.game_running && status.active_game_id) {
      if (status.active_game_id !== activeId) {
        activeId = status.active_game_id;
        renderGames();
      }
      if (!rfb && !connecting) connectVnc();
    }
  } catch (_) {
    /* ignore poll errors */
  }
}, 4000);
