#!/usr/bin/env python3
"""Build four additional 620x272 Spine 3.8 football banner runtimes."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parents[1]
BANNER_ROOT = ROOT / "assets/banners/champions-league-2026"
SERIES_ROOT = BANNER_ROOT / "series"
COMMON_IMAGES = BANNER_ROOT / "spine-3.8/images"


@dataclass(frozen=True)
class Variant:
    slug: str
    title: str
    primary: tuple[int, int, int]
    secondary: tuple[int, int, int]
    headline: tuple[float, float]
    accent: tuple[float, float]
    camera_x: float
    camera_y: float
    motion: str
    duration: float


VARIANTS = (
    Variant(
        "02-star-summit",
        "群星巅峰夜",
        (95, 190, 255),
        (255, 196, 70),
        (-176, 64),
        (160, -72),
        1.4,
        -1.0,
        "celebration",
        1.35,
    ),
    Variant(
        "03-rivalry",
        "豪门生死战",
        (255, 76, 36),
        (255, 178, 45),
        (178, 62),
        (-4, 76),
        -1.5,
        -0.8,
        "impact",
        0.82,
    ),
    Variant(
        "04-champion-road",
        "冠军之路",
        (158, 77, 255),
        (70, 215, 255),
        (-184, 48),
        (-78, 76),
        1.0,
        -1.4,
        "orbit",
        1.6,
    ),
    Variant(
        "05-striker-storm",
        "锋线风暴",
        (65, 220, 190),
        (255, 177, 45),
        (175, 62),
        (18, 105),
        -1.2,
        -1.0,
        "goal_blast",
        1.05,
    ),
)


def next_power_of_two(value: int) -> int:
    return 1 << math.ceil(math.log2(value))


def tint_effect(image: Image.Image, color: tuple[int, int, int]) -> Image.Image:
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    gray = ImageOps.grayscale(rgba)
    colored = ImageOps.colorize(gray, black=(0, 0, 0), white=color).convert("RGBA")
    colored.putalpha(alpha)
    return colored


def headline_box(variant: Variant) -> tuple[int, int, int, int]:
    return {
        "celebration": (18, 54, 314, 142),
        "impact": (344, 42, 620, 132),
        "orbit": (16, 56, 268, 158),
        "goal_blast": (350, 42, 620, 140),
    }[variant.motion]


def head_regions(variant: Variant) -> list[list[tuple[int, int]]]:
    return {
        "celebration": [
            [(345, 62), (352, 40), (395, 38), (410, 64), (409, 120), (385, 135), (352, 116)],
            [(440, 45), (452, 27), (491, 29), (510, 55), (511, 116), (480, 138), (445, 118)],
            [(536, 58), (546, 42), (589, 44), (608, 70), (608, 121), (576, 137), (543, 116)],
        ],
        "impact": [
            [(45, 55), (55, 37), (98, 37), (116, 61), (116, 121), (86, 142), (52, 120)],
            [(142, 35), (160, 18), (210, 20), (232, 48), (229, 119), (194, 145), (153, 119)],
            [(250, 58), (263, 41), (313, 40), (335, 65), (335, 120), (305, 144), (264, 121)],
        ],
        "orbit": [
            [(315, 55), (326, 36), (368, 35), (389, 61), (389, 119), (360, 141), (325, 118)],
            [(428, 49), (440, 30), (486, 31), (510, 58), (509, 119), (478, 142), (440, 118)],
            [(540, 57), (551, 39), (597, 39), (616, 66), (616, 120), (586, 141), (550, 119)],
        ],
        "goal_blast": [
            [(45, 49), (57, 28), (111, 28), (133, 57), (131, 116), (96, 139), (57, 116)],
            [(170, 34), (185, 17), (235, 18), (259, 48), (257, 116), (225, 143), (184, 118)],
            [(290, 57), (302, 39), (350, 40), (374, 65), (374, 119), (343, 141), (303, 118)],
        ],
    }[variant.motion]


def head_box(region: list[tuple[int, int]], padding: int = 9) -> tuple[int, int, int, int]:
    left = max(0, min(point[0] for point in region) - padding)
    top = max(0, min(point[1] for point in region) - padding)
    right = min(620, max(point[0] for point in region) + padding + 1)
    bottom = min(272, max(point[1] for point in region) + padding + 1)
    return left, top, right, bottom


def head_setup(region: list[tuple[int, int]]) -> tuple[float, float, int, int, float, float]:
    left, top, right, bottom = head_box(region)
    center_x = (left + right) / 2
    center_y = (top + bottom) / 2
    lowest = max(point[1] for point in region)
    neck_points = [point for point in region if point[1] >= lowest - 20]
    pivot_x = sum(point[0] for point in neck_points) / len(neck_points)
    pivot_y = lowest - 4
    return (
        pivot_x - 310,
        136 - pivot_y,
        right - left,
        bottom - top,
        center_x - pivot_x,
        pivot_y - center_y,
    )


def make_head_overlays(base: Image.Image, variant: Variant) -> dict[str, Image.Image]:
    heads: dict[str, Image.Image] = {}
    for index, region in enumerate(head_regions(variant), start=1):
        left, top, right, bottom = head_box(region)
        crop = base.crop((left, top, right, bottom)).convert("RGBA")
        mask = Image.new("L", crop.size, 0)
        local_region = [(x - left, y - top) for x, y in region]
        ImageDraw.Draw(mask).polygon(local_region, fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(4))
        crop.putalpha(mask)
        heads[f"head_{index}"] = crop
    return heads


def make_shine_frames(base: Image.Image, variant: Variant) -> dict[str, Image.Image]:
    box = headline_box(variant)
    crop = base.crop(box).convert("RGB")
    width, height = crop.size
    text_mask = Image.new("L", crop.size, 0)
    mask_pixels = []
    for red, green, blue in crop.getdata():
        high = max(red, green, blue)
        low = min(red, green, blue)
        luminance = (red * 54 + green * 183 + blue * 19) // 256
        saturation = high - low
        if luminance >= 185:
            alpha = min(255, (luminance - 160) * 3)
        elif luminance >= 112 and saturation >= 34:
            alpha = min(230, (luminance - 95) * 4)
        else:
            alpha = 0
        mask_pixels.append(alpha)
    text_mask.putdata(mask_pixels)
    text_mask = text_mask.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.7))

    frames: dict[str, Image.Image] = {}
    band_width = max(18, width // 9)
    direction = -1 if variant.motion == "orbit" else 1
    for index in range(8):
        progress = index / 7
        if direction < 0:
            progress = 1 - progress
        center = -band_width + progress * (width + band_width * 2)
        band = Image.new("L", crop.size, 0)
        band_pixels = []
        for y in range(height):
            for x in range(width):
                diagonal_x = x + y * 0.32
                distance = abs(diagonal_x - center)
                strength = max(0.0, 1.0 - distance / band_width)
                band_pixels.append(round(255 * strength * strength))
        band.putdata(band_pixels)
        alpha = ImageOps.autocontrast(ImageChops.multiply(text_mask, band))
        frame = Image.new("RGBA", crop.size, (*variant.secondary, 0))
        frame.putalpha(alpha)
        frames[f"shine_{index:02d}"] = frame
    return frames


def write_images(variant: Variant) -> tuple[Path, dict[str, Image.Image]]:
    variant_dir = SERIES_ROOT / variant.slug
    spine_dir = variant_dir / "spine-3.8"
    images_dir = spine_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    master = Image.open(variant_dir / "keyart-master.png").convert("RGB")
    base = ImageOps.fit(
        master,
        (620, 272),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    ).convert("RGBA")
    base.save(variant_dir / "banner-620x272.png", optimize=True)
    # Disabled after visual QA: moving cutout heads over a flattened character
    # creates collage seams. Human motion requires clean layered art or frames.
    heads: dict[str, Image.Image] = {}
    shine_frames = make_shine_frames(base, variant)

    flare_source = Image.open(COMMON_IMAGES / "fx_flare.png")
    sparks_source = Image.open(COMMON_IMAGES / "fx_sparks.png")
    images = {
        "base": base,
        **heads,
        "fx_primary": tint_effect(flare_source, variant.primary),
        "fx_secondary": tint_effect(flare_source, variant.secondary),
        "fx_sparks": tint_effect(sparks_source, variant.secondary),
        **shine_frames,
    }
    (images_dir / "players.png").unlink(missing_ok=True)
    for index in range(1, 4):
        (images_dir / f"head_{index}.png").unlink(missing_ok=True)
    for name, image in images.items():
        image.save(images_dir / f"{name}.png", optimize=True)
    return spine_dir, images


def pack_atlas(runtime_dir: Path, images: dict[str, Image.Image]) -> None:
    padding = 4
    max_row_width = 2048
    placements: list[tuple[str, int, int, int, int]] = []
    x = padding
    y = padding
    row_height = 0
    for name, image in images.items():
        if x + image.width + padding > max_row_width:
            x = padding
            y += row_height + padding
            row_height = 0
        placements.append((name, x, y, image.width, image.height))
        x += image.width + padding
        row_height = max(row_height, image.height)

    used_width = max(px + width + padding for _, px, _, width, _ in placements)
    used_height = y + row_height + padding
    atlas = Image.new(
        "RGBA",
        (next_power_of_two(used_width), next_power_of_two(used_height)),
        (0, 0, 0, 0),
    )
    for name, px, py, _, _ in placements:
        atlas.alpha_composite(images[name], (px, py))
    atlas.save(runtime_dir / "banner.png", optimize=True)

    lines = [
        "banner.png",
        f"size: {atlas.width},{atlas.height}",
        "format: RGBA8888",
        "filter: Linear,Linear",
        "repeat: none",
    ]
    for name, px, py, width, height in placements:
        lines.extend(
            [
                name,
                "  rotate: false",
                f"  xy: {px}, {py}",
                f"  size: {width}, {height}",
                f"  orig: {width}, {height}",
                "  offset: 0, 0",
                "  index: -1",
            ]
        )
    (runtime_dir / "banner.atlas").write_text("\n".join(lines) + "\n", encoding="utf-8")


def attachment(path: str, width: int, height: int, **extra: float) -> dict:
    result = {"path": path, "width": width, "height": height}
    result.update(extra)
    return result


def motion_profile(variant: Variant) -> dict:
    """Return a genuinely distinct animation module for each banner."""
    t = variant.duration

    if variant.motion == "celebration":
        return {
            "slots": {
                "stadium_glow": {"color": [
                    {"color": "ffffff08"}, {"time": 0.42, "color": "ffffff34"},
                    {"time": 0.92, "color": "ffffff18"}, {"time": t, "color": "ffffff08"},
                ]},
                "sparks": {"color": [
                    {"color": "ffffff40"}, {"time": 0.66, "color": "ffffffd8"},
                    {"time": t, "color": "ffffff40"},
                ]},
                "headline_flare": {"color": [
                    {"color": "ffffff00"}, {"time": 0.12, "color": "ffffff00"},
                    {"time": 0.3, "color": "ffffffe8"}, {"time": 0.54, "color": "ffffff00"},
                    {"time": t, "color": "ffffff00"},
                ]},
                "accent_flare": {"color": [
                    {"color": "ffffff00"}, {"time": 0.48, "color": "ffffff00"},
                    {"time": 0.66, "color": "ffffffff"}, {"time": 0.8, "color": "ffffff18"},
                    {"time": 0.94, "color": "ffffffd8"}, {"time": 1.12, "color": "ffffff00"},
                    {"time": t, "color": "ffffff00"},
                ]},
            },
            "bones": {
                "camera": {
                    "translate": [
                        {"x": 0, "y": 0},
                        {"time": 0.68, "x": variant.camera_x, "y": variant.camera_y},
                        {"time": t, "x": 0, "y": 0},
                    ],
                    "scale": [
                        {"x": 1.0, "y": 1.0}, {"time": 0.68, "x": 1.016, "y": 1.016},
                        {"time": t, "x": 1.0, "y": 1.0},
                    ],
                },
                "stadium_glow": {
                    "scale": [
                        {"x": 0.46, "y": 0.34}, {"time": 0.48, "x": 0.74, "y": 0.5},
                        {"time": 0.96, "x": 0.55, "y": 0.41}, {"time": t, "x": 0.46, "y": 0.34},
                    ],
                    "rotate": [
                        {"angle": -5}, {"time": 0.68, "angle": 6}, {"time": t, "angle": -5},
                    ],
                },
                "sparks": {
                    "translate": [
                        {"x": 0, "y": -12}, {"time": 0.68, "x": 0, "y": 13},
                        {"time": t, "x": 0, "y": -12},
                    ],
                    "rotate": [
                        {"angle": -1.5}, {"time": 0.68, "angle": 1.5}, {"time": t, "angle": -1.5},
                    ],
                },
                "headline_flare": {
                    "scale": [
                        {"x": 0.16, "y": 0.16}, {"time": 0.32, "x": 0.92, "y": 0.92},
                        {"time": 0.54, "x": 0.2, "y": 0.2}, {"time": t, "x": 0.16, "y": 0.16},
                    ],
                    "rotate": [
                        {"angle": -12}, {"time": 0.54, "angle": 12}, {"time": t, "angle": -12},
                    ],
                },
                "accent_flare": {
                    "scale": [
                        {"x": 0.18, "y": 0.18}, {"time": 0.48, "x": 0.18, "y": 0.18},
                        {"time": 0.68, "x": 1.0, "y": 1.0}, {"time": 0.8, "x": 0.3, "y": 0.3},
                        {"time": 0.96, "x": 0.78, "y": 0.78}, {"time": 1.12, "x": 0.2, "y": 0.2},
                        {"time": t, "x": 0.18, "y": 0.18},
                    ],
                },
            },
        }

    if variant.motion == "impact":
        return {
            "slots": {
                "stadium_glow": {"color": [
                    {"color": "ffffff12"}, {"time": 0.06, "color": "ffffffb0"},
                    {"time": 0.2, "color": "ffffff20"}, {"time": 0.44, "color": "ffffff78"},
                    {"time": 0.62, "color": "ffffff12"}, {"time": t, "color": "ffffff12"},
                ]},
                "sparks": {"color": [
                    {"color": "ffffff30"}, {"time": 0.1, "color": "ffffff78"},
                    {"time": 0.32, "color": "ffffff44"}, {"time": 0.5, "color": "ffffff68"},
                    {"time": t, "color": "ffffff30"},
                ]},
                "headline_flare": {"color": [
                    {"color": "ffffff00"}, {"time": 0.04, "color": "ffffffff"},
                    {"time": 0.2, "color": "ffffff00"}, {"time": 0.4, "color": "ffffffc8"},
                    {"time": 0.56, "color": "ffffff00"}, {"time": t, "color": "ffffff00"},
                ]},
                "accent_flare": {"color": [
                    {"color": "ffffff00"}, {"time": 0.28, "color": "ffffff00"},
                    {"time": 0.42, "color": "ffffffff"}, {"time": 0.62, "color": "ffffff00"},
                    {"time": t, "color": "ffffff00"},
                ]},
            },
            "bones": {
                "camera": {
                    "translate": [
                        {"x": 0, "y": 0}, {"time": 0.05, "x": 2.4, "y": -1.4},
                        {"time": 0.1, "x": -2.2, "y": 1.1}, {"time": 0.16, "x": 1.2, "y": -0.8},
                        {"time": 0.24, "x": 0, "y": 0}, {"time": 0.42, "x": -1.5, "y": 0.8},
                        {"time": 0.48, "x": 1.5, "y": -0.8}, {"time": 0.56, "x": 0, "y": 0},
                        {"time": t, "x": 0, "y": 0},
                    ],
                    "scale": [
                        {"x": 1.0, "y": 1.0}, {"time": 0.06, "x": 1.026, "y": 1.026},
                        {"time": 0.2, "x": 1.006, "y": 1.006}, {"time": 0.44, "x": 1.018, "y": 1.018},
                        {"time": 0.6, "x": 1.0, "y": 1.0}, {"time": t, "x": 1.0, "y": 1.0},
                    ],
                },
                "stadium_glow": {
                    "scale": [
                        {"x": 0.42, "y": 0.32}, {"time": 0.08, "x": 0.96, "y": 0.68},
                        {"time": 0.22, "x": 0.5, "y": 0.38}, {"time": 0.46, "x": 0.82, "y": 0.58},
                        {"time": 0.64, "x": 0.44, "y": 0.34}, {"time": t, "x": 0.42, "y": 0.32},
                    ],
                },
                "sparks": {
                    "translate": [
                        {"x": 0, "y": -2}, {"time": 0.34, "x": 0, "y": 8},
                        {"time": t, "x": 0, "y": -2},
                    ],
                    "rotate": [
                        {"angle": -2}, {"time": 0.42, "angle": 2}, {"time": t, "angle": -2},
                    ],
                },
                "headline_flare": {
                    "scale": [
                        {"x": 0.22, "y": 0.22}, {"time": 0.08, "x": 1.12, "y": 1.12},
                        {"time": 0.2, "x": 0.22, "y": 0.22}, {"time": 0.44, "x": 0.9, "y": 0.9},
                        {"time": 0.58, "x": 0.2, "y": 0.2}, {"time": t, "x": 0.22, "y": 0.22},
                    ],
                },
                "accent_flare": {
                    "scale": [
                        {"x": 0.16, "y": 0.16}, {"time": 0.3, "x": 0.16, "y": 0.16},
                        {"time": 0.44, "x": 1.18, "y": 1.18}, {"time": 0.62, "x": 0.2, "y": 0.2},
                        {"time": t, "x": 0.16, "y": 0.16},
                    ],
                },
            },
        }

    if variant.motion == "orbit":
        return {
            "slots": {
                "stadium_glow": {"color": [
                    {"color": "ffffff18"}, {"time": 0.8, "color": "ffffff68"},
                    {"time": t, "color": "ffffff18"},
                ]},
                "sparks": {"color": [
                    {"color": "ffffff50"}, {"time": 0.8, "color": "ffffffa8"},
                    {"time": t, "color": "ffffff50"},
                ]},
                "headline_flare": {"color": [
                    {"color": "ffffff28"}, {"time": 0.4, "color": "ffffffc8"},
                    {"time": 0.8, "color": "ffffff48"}, {"time": 1.2, "color": "ffffffb8"},
                    {"time": t, "color": "ffffff28"},
                ]},
                "accent_flare": {"color": [
                    {"color": "ffffff38"}, {"time": 0.8, "color": "ffffffa0"},
                    {"time": t, "color": "ffffff38"},
                ]},
            },
            "bones": {
                "camera": {
                    "translate": [
                        {"x": -1.5, "y": 0}, {"time": 0.8, "x": 1.5, "y": -1.2},
                        {"time": t, "x": -1.5, "y": 0},
                    ],
                    "scale": [
                        {"x": 1.0, "y": 1.0}, {"time": 0.8, "x": 1.012, "y": 1.012},
                        {"time": t, "x": 1.0, "y": 1.0},
                    ],
                },
                "stadium_glow": {
                    "scale": [
                        {"x": 0.48, "y": 0.32}, {"time": 0.8, "x": 0.78, "y": 0.54},
                        {"time": t, "x": 0.48, "y": 0.32},
                    ],
                    "rotate": [
                        {"angle": -24}, {"time": 0.8, "angle": 24}, {"time": t, "angle": -24},
                    ],
                },
                "sparks": {
                    "translate": [
                        {"x": -5, "y": -4}, {"time": 0.8, "x": 5, "y": 8},
                        {"time": t, "x": -5, "y": -4},
                    ],
                    "rotate": [
                        {"angle": -2}, {"time": 0.8, "angle": 2}, {"time": t, "angle": -2},
                    ],
                },
                "headline_flare": {
                    "translate": [
                        {"x": -5, "y": -3}, {"time": 0.8, "x": 5, "y": 3},
                        {"time": t, "x": -5, "y": -3},
                    ],
                    "scale": [
                        {"x": 0.3, "y": 0.3}, {"time": 0.4, "x": 0.82, "y": 0.82},
                        {"time": 0.8, "x": 0.4, "y": 0.4}, {"time": 1.2, "x": 0.76, "y": 0.76},
                        {"time": t, "x": 0.3, "y": 0.3},
                    ],
                },
                "accent_flare": {
                    "scale": [
                        {"x": 0.46, "y": 0.46}, {"time": 0.8, "x": 0.84, "y": 0.84},
                        {"time": t, "x": 0.46, "y": 0.46},
                    ],
                    "rotate": [
                        {"angle": -28}, {"time": 0.8, "angle": 42}, {"time": t, "angle": -28},
                    ],
                },
            },
        }

    if variant.motion == "goal_blast":
        return {
            "slots": {
                "stadium_glow": {"color": [
                    {"color": "ffffff0c"}, {"time": 0.28, "color": "ffffff14"},
                    {"time": 0.4, "color": "ffffff88"}, {"time": 0.7, "color": "ffffff18"},
                    {"time": t, "color": "ffffff0c"},
                ]},
                "sparks": {"color": [
                    {"color": "ffffff30"}, {"time": 0.26, "color": "ffffff50"},
                    {"time": 0.48, "color": "ffffffe8"}, {"time": 0.88, "color": "ffffff00"},
                    {"time": t, "color": "ffffff30"},
                ]},
                "headline_flare": {"color": [
                    {"color": "ffffff00"}, {"time": 0.52, "color": "ffffff00"},
                    {"time": 0.68, "color": "ffffffe8"}, {"time": 0.9, "color": "ffffff00"},
                    {"time": t, "color": "ffffff00"},
                ]},
                "accent_flare": {"color": [
                    {"color": "ffffff00"}, {"time": 0.26, "color": "ffffff00"},
                    {"time": 0.38, "color": "ffffffff"}, {"time": 0.6, "color": "ffffff00"},
                    {"time": t, "color": "ffffff00"},
                ]},
            },
            "bones": {
                "camera": {
                    "translate": [
                        {"x": 0, "y": 0}, {"time": 0.3, "x": 0, "y": 0},
                        {"time": 0.34, "x": -2.2, "y": 1.2}, {"time": 0.39, "x": 2.0, "y": -1.0},
                        {"time": 0.46, "x": 0, "y": 0}, {"time": t, "x": 0, "y": 0},
                    ],
                    "scale": [
                        {"x": 1.0, "y": 1.0}, {"time": 0.28, "x": 1.0, "y": 1.0},
                        {"time": 0.38, "x": 1.035, "y": 1.035}, {"time": 0.52, "x": 1.012, "y": 1.012},
                        {"time": 0.78, "x": 1.0, "y": 1.0}, {"time": t, "x": 1.0, "y": 1.0},
                    ],
                },
                "stadium_glow": {
                    "scale": [
                        {"x": 0.42, "y": 0.3}, {"time": 0.28, "x": 0.46, "y": 0.34},
                        {"time": 0.42, "x": 0.96, "y": 0.68}, {"time": 0.72, "x": 0.5, "y": 0.36},
                        {"time": t, "x": 0.42, "y": 0.3},
                    ],
                },
                "sparks": {
                    "translate": [
                        {"x": 0, "y": -8}, {"time": 0.28, "x": 0, "y": -8},
                        {"time": 0.65, "x": 0, "y": 24}, {"time": 0.9, "x": 0, "y": 28},
                        {"time": t, "x": 0, "y": -8, "curve": "stepped"},
                    ],
                    "scale": [
                        {"x": 0.9, "y": 0.9}, {"time": 0.28, "x": 0.9, "y": 0.9},
                        {"time": 0.55, "x": 1.08, "y": 1.08}, {"time": t, "x": 0.9, "y": 0.9},
                    ],
                },
                "headline_flare": {
                    "scale": [
                        {"x": 0.16, "y": 0.16}, {"time": 0.52, "x": 0.16, "y": 0.16},
                        {"time": 0.7, "x": 1.0, "y": 1.0}, {"time": 0.9, "x": 0.2, "y": 0.2},
                        {"time": t, "x": 0.16, "y": 0.16},
                    ],
                },
                "accent_flare": {
                    "translate": [
                        {"x": 0, "y": 0}, {"time": 0.38, "x": -3, "y": 2},
                        {"time": 0.6, "x": 0, "y": 0}, {"time": t, "x": 0, "y": 0},
                    ],
                    "scale": [
                        {"x": 0.12, "y": 0.12}, {"time": 0.26, "x": 0.12, "y": 0.12},
                        {"time": 0.4, "x": 1.28, "y": 1.28}, {"time": 0.6, "x": 0.24, "y": 0.24},
                        {"time": t, "x": 0.12, "y": 0.12},
                    ],
                    "rotate": [
                        {"angle": -8}, {"time": 0.6, "angle": 18}, {"time": t, "angle": -8},
                    ],
                },
            },
        }

    raise ValueError(f"Unknown motion profile: {variant.motion}")


def head_motion(variant: Variant, index: int) -> dict:
    """Visible but restrained motion for one separated head attachment."""
    t = variant.duration
    factor = (0.92, 1.08, 0.98)[index]
    direction = (-1, 1, -1)[index]
    if variant.motion == "celebration":
        move_x = direction * 2.4 * factor
        move_y = (3.5, 4.2, 3.3)[index]
        turn = direction * 1.1 * factor
        return {
            "translate": [
                {"x": -move_x * 0.3, "y": 0},
                {"time": 0.68, "x": move_x, "y": move_y},
                {"time": t, "x": -move_x * 0.3, "y": 0},
            ],
            "rotate": [
                {"angle": -turn * 0.4},
                {"time": 0.68, "angle": turn},
                {"time": t, "angle": -turn * 0.4},
            ],
            "scale": [
                {"x": 1, "y": 1},
                {"time": 0.68, "x": 1.016, "y": 1.016},
                {"time": t, "x": 1, "y": 1},
            ],
        }
    if variant.motion == "impact":
        move_x = direction * 3.0 * factor
        turn = direction * 1.25 * factor
        return {
            "translate": [
                {"x": 0, "y": 0},
                {"time": 0.06, "x": move_x, "y": 2.4 * factor},
                {"time": 0.16, "x": -move_x * 0.6, "y": -1.1 * factor},
                {"time": 0.24, "x": 0, "y": 0},
                {"time": 0.44, "x": move_x * 0.62, "y": 1.4 * factor},
                {"time": 0.56, "x": 0, "y": 0},
                {"time": t, "x": 0, "y": 0},
            ],
            "rotate": [
                {"angle": 0},
                {"time": 0.06, "angle": turn},
                {"time": 0.18, "angle": -turn * 0.58},
                {"time": 0.26, "angle": 0},
                {"time": 0.44, "angle": turn * 0.52},
                {"time": 0.58, "angle": 0},
                {"time": t, "angle": 0},
            ],
            "scale": [
                {"x": 1, "y": 1},
                {"time": 0.06, "x": 1.018, "y": 1.018},
                {"time": 0.2, "x": 1, "y": 1},
                {"time": 0.44, "x": 1.007, "y": 1.007},
                {"time": 0.6, "x": 1, "y": 1},
                {"time": t, "x": 1, "y": 1},
            ],
        }
    if variant.motion == "orbit":
        move_x = direction * 3.0 * factor
        move_y = (2.2, 2.8, 2.4)[index]
        turn = direction * 1.05 * factor
        return {
            "translate": [
                {"x": -move_x, "y": 0},
                {"time": 0.8, "x": move_x, "y": move_y},
                {"time": t, "x": -move_x, "y": 0},
            ],
            "rotate": [
                {"angle": -turn},
                {"time": 0.8, "angle": turn},
                {"time": t, "angle": -turn},
            ],
            "scale": [
                {"x": 1, "y": 1},
                {"time": 0.8, "x": 1.014, "y": 1.014},
                {"time": t, "x": 1, "y": 1},
            ],
        }
    if variant.motion == "goal_blast":
        move_x = direction * 2.5 * factor
        turn = -direction * 1.4 * factor
        return {
            "translate": [
                {"x": 0, "y": 0},
                {"time": 0.28, "x": 0, "y": 0},
                {"time": 0.4, "x": move_x, "y": 4.2 * factor},
                {"time": 0.72, "x": move_x * 0.28, "y": 1.2 * factor},
                {"time": t, "x": 0, "y": 0},
            ],
            "rotate": [
                {"angle": 0},
                {"time": 0.28, "angle": 0},
                {"time": 0.4, "angle": turn},
                {"time": 0.72, "angle": -turn * 0.24},
                {"time": t, "angle": 0},
            ],
            "scale": [
                {"x": 1, "y": 1},
                {"time": 0.28, "x": 1, "y": 1},
                {"time": 0.4, "x": 1.018, "y": 1.018},
                {"time": 0.72, "x": 1.005, "y": 1.005},
                {"time": t, "x": 1, "y": 1},
            ],
        }
    raise ValueError(f"Unknown head motion profile: {variant.motion}")


def shine_timeline(variant: Variant) -> dict:
    """Frame-by-frame highlight clipped to the headline pixels."""
    if variant.motion == "celebration":
        sweeps = [(0.14, 0.055)]
    elif variant.motion == "impact":
        sweeps = [(0.02, 0.025), (0.4, 0.025)]
    elif variant.motion == "orbit":
        sweeps = [(0.24, 0.11)]
    elif variant.motion == "goal_blast":
        sweeps = [(0.56, 0.04)]
    else:
        raise ValueError(f"Unknown shine profile: {variant.motion}")

    frames: list[dict] = [{"name": None}]
    for start, step in sweeps:
        for index in range(8):
            frames.append({"time": round(start + step * index, 4), "name": f"shine_{index:02d}"})
        frames.append({"time": round(start + step * 8, 4), "name": None})
    frames.append({"time": variant.duration, "name": None})
    return {"attachment": frames}


def skeleton_data(variant: Variant) -> dict:
    headline_x, headline_y = variant.headline
    accent_x, accent_y = variant.accent
    head_setups: list[tuple[float, float, int, int, float, float]] = []
    shine_left, shine_top, shine_right, shine_bottom = headline_box(variant)
    shine_width = shine_right - shine_left
    shine_height = shine_bottom - shine_top
    shine_x = (shine_left + shine_right) / 2 - 310
    shine_y = 136 - (shine_top + shine_bottom) / 2
    sparks_y = -78 if variant.motion == "impact" else -48
    data = {
        "skeleton": {
            "hash": f"codex-ucl-{variant.slug}-v1",
            "spine": "3.8.99",
            "x": -310,
            "y": -136,
            "width": 620,
            "height": 272,
            "images": "./images/",
            "audio": "",
        },
        "bones": [
            {"name": "root"},
            {"name": "camera", "parent": "root"},
            {"name": "base", "parent": "camera"},
            {"name": "stadium_glow", "parent": "camera", "x": 0, "y": -46},
            {"name": "sparks", "parent": "camera", "x": 0, "y": sparks_y},
            {"name": "headline_flare", "parent": "camera", "x": headline_x, "y": headline_y},
            {"name": "accent_flare", "parent": "camera", "x": accent_x, "y": accent_y},
            *[
                {"name": f"head_{index}", "parent": "camera", "x": setup[0], "y": setup[1]}
                for index, setup in enumerate(head_setups, start=1)
            ],
            {"name": "text_shine", "parent": "camera", "x": shine_x, "y": shine_y},
        ],
        "slots": [
            {"name": "base", "bone": "base", "attachment": "base"},
            {
                "name": "stadium_glow",
                "bone": "stadium_glow",
                "attachment": "stadium_glow",
                "blend": "additive",
            },
            {
                "name": "sparks",
                "bone": "sparks",
                "attachment": "sparks",
                "blend": "additive",
            },
            {
                "name": "headline_flare",
                "bone": "headline_flare",
                "attachment": "headline_flare",
                "blend": "additive",
            },
            {
                "name": "accent_flare",
                "bone": "accent_flare",
                "attachment": "accent_flare",
                "blend": "additive",
            },
            *[
                {"name": f"head_{index}", "bone": f"head_{index}", "attachment": f"head_{index}"}
                for index in range(1, len(head_setups) + 1)
            ],
            {"name": "text_shine", "bone": "text_shine", "blend": "additive"},
        ],
        "skins": [
            {
                "name": "default",
                "attachments": {
                    "base": {"base": attachment("base", 620, 272)},
                    "stadium_glow": {
                        "stadium_glow": attachment("fx_primary", 340, 340)
                    },
                    "sparks": {"sparks": attachment("fx_sparks", 620, 349)},
                    "headline_flare": {
                        "headline_flare": attachment("fx_secondary", 104, 104)
                    },
                    "accent_flare": {
                        "accent_flare": attachment("fx_primary", 190, 190)
                    },
                    **{
                        f"head_{index}": {
                            f"head_{index}": attachment(
                                f"head_{index}", setup[2], setup[3], x=setup[4], y=setup[5]
                            )
                        }
                        for index, setup in enumerate(head_setups, start=1)
                    },
                    "text_shine": {
                        f"shine_{index:02d}": attachment(
                            f"shine_{index:02d}", shine_width, shine_height
                        )
                        for index in range(8)
                    },
                },
            }
        ],
        "animations": {
            "animation": {
                "slots": {
                    "stadium_glow": {
                        "color": [
                            {"color": "ffffff08"},
                            {"time": 0.3, "color": "ffffff38"},
                            {"time": 0.62, "color": "ffffff12"},
                            {"time": 0.97, "color": "ffffff08"},
                        ]
                    },
                    "sparks": {
                        "color": [
                            {"color": "ffffff46"},
                            {"time": 0.44, "color": "ffffffbd"},
                            {"time": 0.97, "color": "ffffff46"},
                        ]
                    },
                    "headline_flare": {
                        "color": [
                            {"color": "ffffff00"},
                            {"time": 0.12, "color": "ffffff00"},
                            {"time": 0.26, "color": "ffffffe8"},
                            {"time": 0.48, "color": "ffffff00"},
                            {"time": 0.97, "color": "ffffff00"},
                        ]
                    },
                    "accent_flare": {
                        "color": [
                            {"color": "ffffff00"},
                            {"time": 0.48, "color": "ffffff00"},
                            {"time": 0.62, "color": "ffffffff"},
                            {"time": 0.86, "color": "ffffff00"},
                            {"time": 0.97, "color": "ffffff00"},
                        ]
                    },
                },
                "bones": {
                    "camera": {
                        "translate": [
                            {"x": 0, "y": 0},
                            {"time": 0.48, "x": variant.camera_x, "y": variant.camera_y},
                            {"time": 0.97, "x": 0, "y": 0},
                        ],
                        "scale": [
                            {"x": 1.0, "y": 1.0},
                            {"time": 0.48, "x": 1.018, "y": 1.018},
                            {"time": 0.97, "x": 1.0, "y": 1.0},
                        ],
                    },
                    "stadium_glow": {
                        "scale": [
                            {"x": 0.46, "y": 0.34},
                            {"time": 0.34, "x": 0.78, "y": 0.52},
                            {"time": 0.68, "x": 0.55, "y": 0.4},
                            {"time": 0.97, "x": 0.46, "y": 0.34},
                        ],
                        "rotate": [
                            {"angle": -4},
                            {"time": 0.5, "angle": 5},
                            {"time": 0.97, "angle": -4},
                        ],
                    },
                    "sparks": {
                        "translate": [
                            {"x": 0, "y": -6},
                            {"time": 0.48, "x": 0, "y": 7},
                            {"time": 0.97, "x": 0, "y": -6},
                        ],
                        "scale": [
                            {"x": 0.985, "y": 0.985},
                            {"time": 0.48, "x": 1.03, "y": 1.03},
                            {"time": 0.97, "x": 0.985, "y": 0.985},
                        ],
                    },
                    "headline_flare": {
                        "scale": [
                            {"x": 0.18, "y": 0.18},
                            {"time": 0.28, "x": 0.94, "y": 0.94},
                            {"time": 0.48, "x": 0.22, "y": 0.22},
                            {"time": 0.97, "x": 0.18, "y": 0.18},
                        ],
                        "rotate": [
                            {"angle": -14},
                            {"time": 0.48, "angle": 14},
                            {"time": 0.97, "angle": -14},
                        ],
                    },
                    "accent_flare": {
                        "scale": [
                            {"x": 0.2, "y": 0.2},
                            {"time": 0.48, "x": 0.2, "y": 0.2},
                            {"time": 0.65, "x": 1.0, "y": 1.0},
                            {"time": 0.86, "x": 0.26, "y": 0.26},
                            {"time": 0.97, "x": 0.2, "y": 0.2},
                        ],
                        "rotate": [
                            {"angle": -10},
                            {"time": 0.86, "angle": 16},
                            {"time": 0.97, "angle": -10},
                        ],
                    },
                },
            }
        },
    }
    profile = motion_profile(variant)
    for index in range(len(head_setups)):
        profile["bones"][f"head_{index + 1}"] = head_motion(variant, index)
    profile["slots"]["text_shine"] = shine_timeline(variant)
    data["animations"]["animation"] = profile
    return data


def build_variant(variant: Variant) -> None:
    spine_dir, images = write_images(variant)
    runtime_dir = spine_dir / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    pack_atlas(runtime_dir, images)
    data = skeleton_data(variant)
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n"
    (spine_dir / "banner.json").write_text(text, encoding="utf-8")
    (runtime_dir / "banner.json").write_text(text, encoding="utf-8")
    print(f"Built {variant.slug}: {variant.title}")


def main() -> None:
    for variant in VARIANTS:
        build_variant(variant)


if __name__ == "__main__":
    main()
