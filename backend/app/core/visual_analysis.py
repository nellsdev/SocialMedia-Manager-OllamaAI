"""Visual reference analysis.

Extracts a dominant color palette and rough mood descriptors from the
reference images the creator uploads during the onboarding aesthetic
step. Deterministic and fast (no LLM needed for the palette itself);
the LLM then interprets the palette into brand colors/style.

Supported image formats: PNG, JPEG, WEBP, GIF (first frame).
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Very light heuristic keywords derived from hue/lightness
_PALETTE_NAMES = {
    "warm": "cálido",
    "cool": "frío",
    "neutral": "neutral",
    "muted": "apagado",
    "vibrant": "vibrante",
    "dark": "oscuro",
    "light": "claro",
}


@dataclass
class VisualAnalysis:
    dominant_colors: list[dict]  # [{hex, name-ish}] top 5
    mood_hints: list[str]
    style_hint: str


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb).upper()


def _hue_bucket(hue: float) -> str:
    if hue is None:
        return "neutral"
    if hue < 20 or hue >= 340:
        return "rojo"
    if hue < 50:
        return "naranja"
    if hue < 80:
        return "amarillo"
    if hue < 170:
        return "verde"
    if hue < 260:
        return "azul"
    return "violeta"


def analyze_image_bytes(data: bytes) -> VisualAnalysis:
    """Extract the dominant palette and mood hints from raw image bytes."""
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(data))
        img = img.convert("RGB")
        # Downscale to speed up quantization (capped at ~120px longest side)
        img.thumbnail((120, 120))

        # Quantize to 8 colors, count usage
        q = img.quantize(colors=8, method=Image.Quantize.MEDIANCUT)
        palette = q.getpalette() or []
        counts = sorted(q.getcolors(), reverse=True)

        top: list[tuple[int, int, int]] = []
        for count, idx in counts[:5]:
            r, g, b = palette[idx * 3 : idx * 3 + 3]
            top.append((r, g, b))

        # Compute average lightness and saturation for mood hints
        avg_lightness = sum(0.213 * r + 0.715 * g + 0.072 * b for r, g, b in top) / len(top)
        avg_sat = sum(
            (max(r, g, b) - min(r, g, b)) for r, g, b in top
        ) / len(top)

        dominant = [
            {"hex": _rgb_to_hex(rgb), "name": _hue_bucket(_hue_of(rgb))}
            for rgb in top
        ]

        hints: list[str] = []
        if avg_lightness < 80:
            hints.append(_PALETTE_NAMES["dark"])
        elif avg_lightness > 190:
            hints.append(_PALETTE_NAMES["light"])
        else:
            hints.append(_PALETTE_NAMES["neutral"])
        if avg_sat > 90:
            hints.append(_PALETTE_NAMES["vibrant"])
        elif avg_sat < 35:
            hints.append(_PALETTE_NAMES["muted"])
        else:
            hints.append(_PALETTE_NAMES["warm"])

        return VisualAnalysis(
            dominant_colors=dominant,
            mood_hints=hints,
            style_hint=", ".join(hints) or "neutral",
        )
    except Exception as exc:
        logger.warning("Image analysis failed: %s", exc)
        return VisualAnalysis(dominant_colors=[], mood_hints=[], style_hint="")


def _hue_of(rgb: tuple[int, int, int]) -> float | None:
    r, g, b = [x / 255.0 for x in rgb]
    mx, mn = max(r, g, b), min(r, g, b)
    if mx == mn:
        return None
    d = mx - mn
    if mx == r:
        h = (g - b) / d + (6 if g < b else 0)
    elif mx == g:
        h = (b - r) / d + 2
    else:
        h = (r - g) / d + 4
    return h * 60