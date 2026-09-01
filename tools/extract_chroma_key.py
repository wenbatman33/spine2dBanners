#!/usr/bin/env python3
"""Remove a green-screen background while preserving anti-aliased edges."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageFilter


def smoothstep(edge0: float, edge1: float, value: float) -> float:
    t = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--alpha-mask",
        type=Path,
        help="Optional RGBA image whose alpha channel supplies the foreground mask.",
    )
    args = parser.parse_args()

    source = Image.open(args.source).convert("RGB")
    mask_alpha = None
    if args.alpha_mask:
        mask_image = Image.open(args.alpha_mask).convert("RGBA")
        if mask_image.size != source.size:
            raise ValueError("alpha mask must match source dimensions")
        mask_alpha = list(mask_image.getchannel("A").getdata())
    output_pixels: list[tuple[int, int, int, int]] = []
    for index, (red, green, blue) in enumerate(source.getdata()):
        dominance = green - max(red, blue)
        keyed = smoothstep(55.0, 185.0, green) * smoothstep(12.0, 82.0, dominance)
        chroma_alpha = round(255.0 * (1.0 - keyed))
        alpha = (
            round(mask_alpha[index] * chroma_alpha / 255.0)
            if mask_alpha is not None
            else chroma_alpha
        )
        if dominance > 4 and alpha > 0:
            green = min(green, max(red, blue) + 2)
        output_pixels.append((red, green, blue, alpha) if alpha else (0, 0, 0, 0))

    rgba = Image.new("RGBA", source.size)
    rgba.putdata(output_pixels)
    if mask_alpha is not None:
        # Contract the segmentation edge by roughly two source pixels, then
        # restore a sub-pixel feather. This removes green-screen contamination
        # without carving visible hard steps into hair or clothing.
        refined_alpha = rgba.getchannel("A").filter(ImageFilter.MinFilter(5))
        refined_alpha = refined_alpha.filter(ImageFilter.GaussianBlur(0.7))
        rgba.putalpha(refined_alpha)
        rgba.putdata(
            [
                (red, green, blue, alpha) if alpha else (0, 0, 0, 0)
                for red, green, blue, alpha in rgba.getdata()
            ]
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    rgba.save(args.output)
    extrema = rgba.getchannel("A").getextrema()
    print(f"saved {args.output} alpha={extrema[0]}..{extrema[1]}")


if __name__ == "__main__":
    main()
