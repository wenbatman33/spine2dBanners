#!/usr/bin/env python3
"""Convert an AI-baked neutral checker background into real PNG alpha.

Only neutral, bright pixels connected to the image boundary are removed. This
keeps the white jersey because its outer silhouette is bounded by darker edge
pixels and its interior is not connected to the canvas boundary.
"""

from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path

from PIL import Image, ImageFilter


def is_background(red: int, green: int, blue: int) -> bool:
    return max(red, green, blue) - min(red, green, blue) <= 9 and (red + green + blue) >= 690


def extract(source_path: Path, output_path: Path) -> None:
    source = Image.open(source_path).convert("RGB")
    width, height = source.size
    pixels = source.load()
    visited = bytearray(width * height)
    queue: deque[tuple[int, int]] = deque()

    def enqueue(x: int, y: int) -> None:
        offset = y * width + x
        if visited[offset]:
            return
        if not is_background(*pixels[x, y]):
            return
        visited[offset] = 1
        queue.append((x, y))

    for x in range(width):
        enqueue(x, 0)
        enqueue(x, height - 1)
    for y in range(height):
        enqueue(0, y)
        enqueue(width - 1, y)

    while queue:
        x, y = queue.popleft()
        if x:
            enqueue(x - 1, y)
        if x + 1 < width:
            enqueue(x + 1, y)
        if y:
            enqueue(x, y - 1)
        if y + 1 < height:
            enqueue(x, y + 1)

    alpha = Image.new("L", source.size, 255)
    alpha_pixels = alpha.load()
    for y in range(height):
        row = y * width
        for x in range(width):
            if visited[row + x]:
                alpha_pixels[x, y] = 0

    alpha = alpha.filter(ImageFilter.GaussianBlur(0.65))
    output = source.convert("RGBA")
    output.putalpha(alpha)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output.save(output_path, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    extract(args.source, args.output)


if __name__ == "__main__":
    main()
