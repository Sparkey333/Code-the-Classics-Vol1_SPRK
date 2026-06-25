"""AI image provider adapters for Neo Remix sprite generation."""

from __future__ import annotations

import base64
import json
import time
from abc import ABC, abstractmethod
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
from PIL import Image

if TYPE_CHECKING:
    from lib.api_config import AISettings

TIMEOUT = 120.0


class SpriteProvider(ABC):
    name: str

    @abstractmethod
    def generate_variations(
        self,
        reference: Path,
        prompt: str,
        count: int,
        seed: int,
        target_size: tuple[int, int],
    ) -> list[bytes]:
        ...


def _pad_for_api(img: Image.Image, min_side: int = 256) -> Image.Image:
    w, h = img.size
    side = max(min_side, w, h)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(img, ((side - w) // 2, (side - h) // 2), img)
    return canvas


def _to_png_bytes(img: Image.Image) -> bytes:
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class OpenAIProvider(SpriteProvider):
    name = "openai"

    def __init__(self, settings: AISettings):
        self.settings = settings
        import os

        self.api_key = os.environ["OPENAI_API_KEY"]

    def generate_variations(
        self,
        reference: Path,
        prompt: str,
        count: int,
        seed: int,
        target_size: tuple[int, int],
    ) -> list[bytes]:
        ref = _pad_for_api(Image.open(reference).convert("RGBA"))
        ref_bytes = _to_png_bytes(ref)
        results: list[bytes] = []

        with httpx.Client(timeout=TIMEOUT) as client:
            for i in range(count):
                variant_prompt = f"{prompt} Variation {i + 1}, seed {seed + i}."
                files = {
                    "image": ("reference.png", ref_bytes, "image/png"),
                }
                data = {
                    "model": self.settings.openai_model,
                    "prompt": variant_prompt,
                    "n": "1",
                    "size": "1024x1024",
                    "background": "transparent",
                }
                resp = client.post(
                    "https://api.openai.com/v1/images/edits",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    files=files,
                    data=data,
                )
                if resp.status_code >= 400:
                    raise RuntimeError(f"OpenAI error {resp.status_code}: {resp.text[:500]}")
                payload = resp.json()
                item = payload["data"][0]
                if "b64_json" in item:
                    results.append(base64.b64decode(item["b64_json"]))
                elif "url" in item:
                    img_resp = client.get(item["url"])
                    img_resp.raise_for_status()
                    results.append(img_resp.content)
        return results


class ReplicateProvider(SpriteProvider):
    name = "replicate"

    def __init__(self, settings: AISettings):
        self.settings = settings
        import os

        self.token = os.environ["REPLICATE_API_TOKEN"]

    def generate_variations(
        self,
        reference: Path,
        prompt: str,
        count: int,
        seed: int,
        target_size: tuple[int, int],
    ) -> list[bytes]:
        ref = _pad_for_api(Image.open(reference).convert("RGBA"))
        ref_b64 = base64.b64encode(_to_png_bytes(ref)).decode()
        results: list[bytes] = []

        with httpx.Client(timeout=TIMEOUT) as client:
            for i in range(count):
                body = {
                    "version": None,
                    "input": {
                        "prompt": prompt,
                        "image": f"data:image/png;base64,{ref_b64}",
                        "num_outputs": 1,
                        "seed": seed + i,
                        "output_format": "png",
                        "guidance": 3.5,
                        "num_inference_steps": 4,
                    },
                }
                # Resolve latest model version
                model = self.settings.replicate_model
                model_resp = client.get(
                    f"https://api.replicate.com/v1/models/{model}",
                    headers={"Authorization": f"Token {self.token}"},
                )
                model_resp.raise_for_status()
                version = model_resp.json()["latest_version"]["id"]
                body["version"] = version

                create = client.post(
                    "https://api.replicate.com/v1/predictions",
                    headers={
                        "Authorization": f"Token {self.token}",
                        "Content-Type": "application/json",
                    },
                    json=body,
                )
                create.raise_for_status()
                pred = create.json()
                pred_id = pred["id"]

                for _ in range(90):
                    poll = client.get(
                        f"https://api.replicate.com/v1/predictions/{pred_id}",
                        headers={"Authorization": f"Token {self.token}"},
                    )
                    poll.raise_for_status()
                    pred = poll.json()
                    if pred["status"] == "succeeded":
                        out = pred["output"]
                        url = out[0] if isinstance(out, list) else out
                        img = client.get(url)
                        img.raise_for_status()
                        results.append(img.content)
                        break
                    if pred["status"] in ("failed", "canceled"):
                        raise RuntimeError(f"Replicate failed: {pred.get('error')}")
                    time.sleep(1)
                else:
                    raise RuntimeError("Replicate prediction timed out")
        return results


class FalProvider(SpriteProvider):
    name = "fal"

    def __init__(self, settings: AISettings):
        self.settings = settings
        import os

        self.key = os.environ["FAL_KEY"]

    def generate_variations(
        self,
        reference: Path,
        prompt: str,
        count: int,
        seed: int,
        target_size: tuple[int, int],
    ) -> list[bytes]:
        ref = _pad_for_api(Image.open(reference).convert("RGBA"))
        ref_b64 = base64.b64encode(_to_png_bytes(ref)).decode()
        results: list[bytes] = []
        endpoint = f"https://fal.run/{self.settings.fal_model}"

        with httpx.Client(timeout=TIMEOUT) as client:
            for i in range(count):
                body = {
                    "prompt": prompt,
                    "image_url": f"data:image/png;base64,{ref_b64}",
                    "seed": seed + i,
                    "num_images": 1,
                    "image_size": "square",
                    "strength": 0.65,
                }
                resp = client.post(
                    endpoint,
                    headers={
                        "Authorization": f"Key {self.key}",
                        "Content-Type": "application/json",
                    },
                    json=body,
                )
                if resp.status_code >= 400:
                    raise RuntimeError(f"Fal error {resp.status_code}: {resp.text[:500]}")
                payload = resp.json()
                images = payload.get("images") or payload.get("output", {}).get("images", [])
                if not images:
                    raise RuntimeError(f"Fal returned no images: {json.dumps(payload)[:300]}")
                url = images[0].get("url") if isinstance(images[0], dict) else images[0]
                img = client.get(url)
                img.raise_for_status()
                results.append(img.content)
        return results


class StabilityProvider(SpriteProvider):
    name = "stability"

    def __init__(self, settings: AISettings):
        self.settings = settings
        import os

        self.key = os.environ["STABILITY_API_KEY"]

    def generate_variations(
        self,
        reference: Path,
        prompt: str,
        count: int,
        seed: int,
        target_size: tuple[int, int],
    ) -> list[bytes]:
        ref = _pad_for_api(Image.open(reference).convert("RGBA"))
        ref_bytes = _to_png_bytes(ref)
        results: list[bytes] = []
        engine = self.settings.stability_engine

        with httpx.Client(timeout=TIMEOUT) as client:
            for i in range(count):
                files = {
                    "init_image": ("reference.png", ref_bytes, "image/png"),
                }
                data = {
                    "text_prompts[0][text]": prompt,
                    "text_prompts[0][weight]": "1",
                    "cfg_scale": "7",
                    "samples": "1",
                    "seed": str(seed + i),
                    "image_strength": "0.35",
                }
                resp = client.post(
                    f"https://api.stability.ai/v1/generation/{engine}/image-to-image",
                    headers={
                        "Authorization": f"Bearer {self.key}",
                        "Accept": "application/json",
                    },
                    files=files,
                    data=data,
                )
                if resp.status_code >= 400:
                    raise RuntimeError(
                        f"Stability error {resp.status_code}: {resp.text[:500]}"
                    )
                artifacts = resp.json().get("artifacts", [])
                if not artifacts:
                    raise RuntimeError("Stability returned no artifacts")
                results.append(base64.b64decode(artifacts[0]["base64"]))
        return results


def get_provider(name: str, settings: AISettings) -> SpriteProvider:
    providers = {
        "openai": OpenAIProvider,
        "replicate": ReplicateProvider,
        "fal": FalProvider,
        "stability": StabilityProvider,
    }
    cls = providers.get(name)
    if not cls:
        raise ValueError(f"Unknown provider: {name}")
    return cls(settings)
