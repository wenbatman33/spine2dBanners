#!/usr/bin/env python3
"""Apply ImageGen-created advertising surfaces to deterministic text masks."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parents[1]
MATERIAL_SHEET = ROOT / "assets/banners/champions-league-2026/typography/ai-lettering-materials.png"


def material_panel(index: int, size: tuple[int, int]) -> Image.Image:
    """Return one clean ImageGen material panel fitted to ``size``."""
    sheet = Image.open(MATERIAL_SHEET).convert("RGB")
    cell_width, cell_height = sheet.width // 3, sheet.height // 2
    column, row = index % 3, index // 3
    panel = sheet.crop(
        (
            column * cell_width + 8,
            row * cell_height + 8,
            (column + 1) * cell_width - 8,
            (row + 1) * cell_height - 8,
        )
    )
    fitted = ImageOps.fit(
        panel,
        size,
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.52),
    ).convert("RGB")
    # Large swirls are attractive as a full material swatch, but inside a
    # Chinese glyph they look like missing strokes. Retain only a restrained
    # ten-percent trace over a broad, smooth metallic colour field.
    radius = max(18, round(min(size) * 0.16))
    smooth = fitted.filter(ImageFilter.GaussianBlur(radius))
    fitted = Image.blend(smooth, fitted, 0.10)
    fitted = ImageEnhance.Contrast(fitted).enhance(0.82)
    fitted = ImageEnhance.Color(fitted).enhance(1.02)
    fitted = ImageEnhance.Brightness(fitted).enhance(1.12)
    white_mix = (0.12, 0.24, 0.28, 0.18, 0.14, 0.08)[index]
    fitted = Image.blend(fitted, Image.new("RGB", size, (255, 255, 255)), white_mix)
    return fitted.convert("RGBA")


def material_fill(mask: Image.Image, index: int, opacity: int = 255) -> Image.Image:
    """Clip an ImageGen material to an exact, readable glyph mask."""
    material = material_panel(index, mask.size)
    material.putalpha(mask.point(lambda value: round(value * opacity / 255)))
    return material
