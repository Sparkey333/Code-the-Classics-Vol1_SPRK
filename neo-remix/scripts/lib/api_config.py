"""Load API keys and generation settings for Neo Remix AI pipeline."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

NEO = Path(__file__).resolve().parents[2]
ENV_FILE = NEO / ".env"
EXAMPLE_ENV = NEO / "config" / "api_keys.example.env"

PROVIDER_ORDER = ("openai", "replicate", "fal", "stability")

KEY_ENV = {
    "openai": "OPENAI_API_KEY",
    "replicate": "REPLICATE_API_TOKEN",
    "fal": "FAL_KEY",
    "stability": "STABILITY_API_KEY",
}


def _load_dotenv() -> None:
    path = ENV_FILE if ENV_FILE.exists() else EXAMPLE_ENV
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if value and key not in os.environ:
            os.environ[key] = value


@dataclass
class AISettings:
    variations: int = 4
    provider: str = "auto"
    randomize: bool = True
    openai_model: str = "gpt-image-1"
    replicate_model: str = "black-forest-labs/flux-schnell"
    fal_model: str = "fal-ai/flux/dev/image-to-image"
    stability_engine: str = "stable-diffusion-xl-1024-v1-0"
    available_providers: list[str] = field(default_factory=list)

    def pick_provider(self, requested: str | None = None) -> str:
        req = (requested or self.provider or "auto").lower()
        if req != "auto":
            if req not in self.available_providers:
                raise RuntimeError(
                    f"Provider '{req}' not configured. "
                    f"Available: {', '.join(self.available_providers) or 'none'}. "
                    f"Copy config/api_keys.example.env to .env and add keys."
                )
            return req
        if not self.available_providers:
            raise RuntimeError(
                "No AI providers configured. Copy neo-remix/config/api_keys.example.env "
                "to neo-remix/.env and set at least one API key."
            )
        return self.available_providers[0]


def load_settings() -> AISettings:
    _load_dotenv()
    available = [p for p in PROVIDER_ORDER if os.environ.get(KEY_ENV[p], "").strip()]
    return AISettings(
        variations=int(os.environ.get("NEO_AI_VARIATIONS", "4")),
        provider=os.environ.get("NEO_AI_PROVIDER", "auto"),
        randomize=os.environ.get("NEO_AI_RANDOMIZE", "true").lower() in ("1", "true", "yes"),
        openai_model=os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-1"),
        replicate_model=os.environ.get("REPLICATE_MODEL", "black-forest-labs/flux-schnell"),
        fal_model=os.environ.get("FAL_MODEL", "fal-ai/flux/dev/image-to-image"),
        stability_engine=os.environ.get(
            "STABILITY_ENGINE", "stable-diffusion-xl-1024-v1-0"
        ),
        available_providers=available,
    )


def mask_key(value: str) -> str:
    if not value:
        return "(not set)"
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}...{value[-4:]}"
