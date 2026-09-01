#!/usr/bin/env python3
"""Build the 620x272 Champions League banner as a Spine 3.8 runtime bundle."""

from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
BANNER_DIR = ROOT / "assets/banners/champions-league-2026"
SPINE_DIR = BANNER_DIR / "spine-3.8"
SOURCE_VFX_DIR = SPINE_DIR / "source-vfx"
SOURCE_CHARACTER_DIR = SPINE_DIR / "source-character"
IMAGES_DIR = SPINE_DIR / "images"
RUNTIME_DIR = SPINE_DIR / "runtime"

HEAD_REGIONS = [
    [(310, 65), (325, 39), (360, 37), (379, 62), (379, 124), (351, 149), (319, 126)],
    [(392, 34), (408, 12), (458, 12), (487, 39), (489, 119), (454, 153), (411, 121)],
    [(505, 58), (522, 38), (568, 36), (596, 61), (596, 122), (565, 147), (523, 122)],
]


def contain(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    image = image.convert("RGBA")
    ratio = min(size[0] / image.width, size[1] / image.height)
    resized = image.resize(
        (round(image.width * ratio), round(image.height * ratio)),
        Image.Resampling.LANCZOS,
    )
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    canvas.alpha_composite(
        resized,
        ((size[0] - resized.width) // 2, (size[1] - resized.height) // 2),
    )
    return canvas


def trim_faint_alpha(image: Image.Image, cutoff: int = 3) -> Image.Image:
    image = image.convert("RGBA")
    red, green, blue, alpha = image.split()
    alpha = alpha.point(lambda value: 0 if value <= cutoff else value)
    return Image.merge("RGBA", (red, green, blue, alpha))


def extract_arm() -> Image.Image:
    """Extract the exact original fist/forearm pixels with a hand-traced matte."""
    source = Image.open(BANNER_DIR / "champions-league-2026-keyart-master.png").convert("RGBA")
    reference_width, reference_height = 620, 272
    sx = source.width / reference_width
    sy = source.height / reference_height
    outline = [
        (294, 152), (310, 152), (320, 155), (326, 160), (330, 165),
        (331, 173), (330, 180), (327, 187), (322, 192), (318, 199),
        (316, 207), (312, 214), (310, 217), (312, 222), (315, 227),
        (312, 232), (307, 235), (299, 237), (290, 234), (284, 230),
        (281, 224), (281, 218), (284, 211), (285, 202), (285, 190),
        (285, 179), (286, 168), (289, 158),
    ]
    scaled_outline = [(round(x * sx), round(y * sy)) for x, y in outline]
    matte = Image.new("L", source.size, 0)
    ImageDraw.Draw(matte).polygon(scaled_outline, fill=255)
    matte = matte.filter(ImageFilter.GaussianBlur(max(1.0, 1.6 * sx)))
    source.putalpha(matte)
    bbox = matte.getbbox()
    if not bbox:
        raise RuntimeError("Arm extraction matte is empty")
    padding = round(3 * sx)
    bbox = (
        max(0, bbox[0] - padding),
        max(0, bbox[1] - padding),
        min(source.width, bbox[2] + padding),
        min(source.height, bbox[3] + padding),
    )
    return contain(source.crop(bbox), (60, 92))


def head_box(region: list[tuple[int, int]], padding: int = 9) -> tuple[int, int, int, int]:
    return (
        max(0, min(point[0] for point in region) - padding),
        max(0, min(point[1] for point in region) - padding),
        min(620, max(point[0] for point in region) + padding + 1),
        min(272, max(point[1] for point in region) + padding + 1),
    )


def head_setup(region: list[tuple[int, int]]) -> tuple[float, float, int, int]:
    left, top, right, bottom = head_box(region)
    return (
        (left + right) / 2 - 310,
        136 - (top + bottom) / 2,
        right - left,
        bottom - top,
    )


def extract_heads(base: Image.Image) -> dict[str, Image.Image]:
    heads: dict[str, Image.Image] = {}
    for index, region in enumerate(HEAD_REGIONS, start=1):
        left, top, right, bottom = head_box(region)
        crop = base.crop((left, top, right, bottom)).convert("RGBA")
        mask = Image.new("L", crop.size, 0)
        local_region = [(x - left, y - top) for x, y in region]
        ImageDraw.Draw(mask).polygon(local_region, fill=255)
        crop.putalpha(mask.filter(ImageFilter.GaussianBlur(4)))
        heads[f"head_{index}"] = crop
    return heads


def write_images() -> dict[str, Image.Image]:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

    base = Image.open(SOURCE_CHARACTER_DIR / "base-clean-master.png").convert("RGBA")
    base = base.resize((620, 272), Image.Resampling.LANCZOS)
    arm = extract_arm()
    # Disabled after visual QA: cutout heads over a flattened banner read as
    # collage pieces. Keep character pixels intact until clean layers exist.
    heads: dict[str, Image.Image] = {}
    flare = contain(
        trim_faint_alpha(Image.open(SOURCE_VFX_DIR / "fx-flare-source.png")),
        (256, 256),
    )
    sparks = contain(
        trim_faint_alpha(Image.open(SOURCE_VFX_DIR / "fx-sparks-source.png")),
        (620, 349),
    )

    images = {
        "base": base,
        "arm": arm,
        **heads,
        "fx_flare": flare,
        "fx_sparks": sparks,
    }
    for name, image in images.items():
        image.save(IMAGES_DIR / f"{name}.png", optimize=True)
    for index in range(1, 4):
        (IMAGES_DIR / f"head_{index}.png").unlink(missing_ok=True)
    return images


def next_power_of_two(value: int) -> int:
    return 1 << math.ceil(math.log2(value))


def pack_atlas(images: dict[str, Image.Image]) -> list[tuple[str, int, int, int, int]]:
    padding = 4
    max_row_width = 1024
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

    used_width = max(x + padding, max(item[1] + item[3] + padding for item in placements))
    used_height = y + row_height + padding
    atlas_size = (next_power_of_two(used_width), next_power_of_two(used_height))
    atlas = Image.new("RGBA", atlas_size, (0, 0, 0, 0))
    for name, px, py, _, _ in placements:
        atlas.alpha_composite(images[name], (px, py))
    atlas.save(RUNTIME_DIR / "champions-league-2026.png", optimize=True)

    lines = [
        "champions-league-2026.png",
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
    (RUNTIME_DIR / "champions-league-2026.atlas").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    return placements


def attachment(path: str, width: int, height: int, **extra: float | str) -> dict:
    result: dict[str, float | int | str] = {"path": path, "width": width, "height": height}
    result.update(extra)
    return result


def skeleton_data() -> dict:
    # Spine 3.8's JSON reader is strict about bezier fields. Linear interpolation
    # keeps this hand-authored runtime data portable across all 3.8 Player builds.
    ease: dict[str, float] = {}
    head_setups: list[tuple[float, float, int, int]] = []
    data = {
        "skeleton": {
            "hash": "codex-ucl-banner-2026-v1",
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
            {"name": "arm_pump", "parent": "camera", "x": -8, "y": -99},
            {"name": "stadium_glow", "parent": "camera", "x": -4, "y": -48},
            {"name": "sparks", "parent": "camera", "x": 0, "y": -46},
            {"name": "headline_flare", "parent": "camera", "x": -178, "y": 69},
            {"name": "trophy_flare", "parent": "camera", "x": 148, "y": -84},
            *[
                {"name": f"head_{index}", "parent": "camera", "x": setup[0], "y": setup[1]}
                for index, setup in enumerate(head_setups, start=1)
            ],
        ],
        "slots": [
            {"name": "base", "bone": "base", "attachment": "base"},
            {"name": "arm", "bone": "arm_pump", "attachment": "arm"},
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
                "name": "trophy_flare",
                "bone": "trophy_flare",
                "attachment": "trophy_flare",
                "blend": "additive",
            },
            *[
                {"name": f"head_{index}", "bone": f"head_{index}", "attachment": f"head_{index}"}
                for index in range(1, len(head_setups) + 1)
            ],
        ],
        "skins": [
            {
                "name": "default",
                "attachments": {
                    "base": {"base": attachment("base", 620, 272)},
                    "arm": {
                        "arm": attachment("arm", 60, 92, x=6, y=43)
                    },
                    "stadium_glow": {
                        "stadium_glow": attachment("fx_flare", 330, 330)
                    },
                    "sparks": {"sparks": attachment("fx_sparks", 620, 349)},
                    "headline_flare": {
                        "headline_flare": attachment("fx_flare", 116, 116)
                    },
                    "trophy_flare": {
                        "trophy_flare": attachment("fx_flare", 210, 210)
                    },
                    **{
                        f"head_{index}": {
                            f"head_{index}": attachment(
                                f"head_{index}", setup[2], setup[3]
                            )
                        }
                        for index, setup in enumerate(head_setups, start=1)
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
                            {"time": 0.28, "color": "ffffff46", **ease},
                            {"time": 0.6, "color": "ffffff12", **ease},
                            {"time": 0.97, "color": "ffffff08"},
                        ]
                    },
                    "sparks": {
                        "color": [
                            {"color": "ffffff5c"},
                            {"time": 0.42, "color": "ffffffed", **ease},
                            {"time": 0.97, "color": "ffffff5c"},
                        ]
                    },
                    "headline_flare": {
                        "color": [
                            {"color": "ffffff00", "curve": "stepped"},
                            {"time": 0.44, "color": "ffffff00"},
                            {"time": 0.57, "color": "ffffffff", **ease},
                            {"time": 0.76, "color": "ffffff00", **ease},
                            {"time": 0.97, "color": "ffffff00"},
                        ]
                    },
                    "trophy_flare": {
                        "color": [
                            {"color": "ffffff00"},
                            {"time": 0.1, "color": "ffffff00"},
                            {"time": 0.22, "color": "ffffffff", **ease},
                            {"time": 0.46, "color": "ffffff00", **ease},
                            {"time": 0.97, "color": "ffffff00"},
                        ]
                    },
                },
                "bones": {
                    "camera": {
                        "translate": [
                            {"x": 0, "y": 0, **ease},
                            {"time": 0.48, "x": 1.5, "y": -1.5, **ease},
                            {"time": 0.97, "x": 0, "y": 0},
                        ],
                        "scale": [
                            {"x": 1.0, "y": 1.0, **ease},
                            {"time": 0.48, "x": 1.022, "y": 1.022, **ease},
                            {"time": 0.97, "x": 1.0, "y": 1.0},
                        ],
                    },
                    "arm_pump": {
                        "translate": [
                            {"x": 0, "y": -2},
                            {"time": 0.22, "x": -1, "y": 4},
                            {"time": 0.48, "x": 0, "y": -2},
                            {"time": 0.72, "x": -1, "y": 4},
                            {"time": 0.97, "x": 0, "y": -2},
                        ],
                        "rotate": [
                            {"angle": -2.5},
                            {"time": 0.22, "angle": 3.5},
                            {"time": 0.48, "angle": -3},
                            {"time": 0.72, "angle": 3.5},
                            {"time": 0.97, "angle": -2.5},
                        ],
                        "scale": [
                            {"x": 1.0, "y": 1.0},
                            {"time": 0.22, "x": 1.01, "y": 1.01},
                            {"time": 0.48, "x": 0.998, "y": 0.998},
                            {"time": 0.72, "x": 1.01, "y": 1.01},
                            {"time": 0.97, "x": 1.0, "y": 1.0},
                        ],
                    },
                    "stadium_glow": {
                        "scale": [
                            {"x": 0.55, "y": 0.38, **ease},
                            {"time": 0.3, "x": 0.84, "y": 0.55, **ease},
                            {"time": 0.62, "x": 0.6, "y": 0.42, **ease},
                            {"time": 0.97, "x": 0.55, "y": 0.38},
                        ],
                        "rotate": [
                            {"angle": -4, **ease},
                            {"time": 0.5, "angle": 5, **ease},
                            {"time": 0.97, "angle": -4},
                        ],
                    },
                    "sparks": {
                        "translate": [
                            {"x": 0, "y": -7, **ease},
                            {"time": 0.48, "x": 0, "y": 7, **ease},
                            {"time": 0.97, "x": 0, "y": -7},
                        ],
                        "scale": [
                            {"x": 0.985, "y": 0.985, **ease},
                            {"time": 0.48, "x": 1.035, "y": 1.035, **ease},
                            {"time": 0.97, "x": 0.985, "y": 0.985},
                        ],
                        "rotate": [
                            {"angle": -0.8, **ease},
                            {"time": 0.48, "angle": 1.1, **ease},
                            {"time": 0.97, "angle": -0.8},
                        ],
                    },
                    "headline_flare": {
                        "scale": [
                            {"x": 0.12, "y": 0.12, "curve": "stepped"},
                            {"time": 0.44, "x": 0.12, "y": 0.12},
                            {"time": 0.61, "x": 0.9, "y": 0.9, **ease},
                            {"time": 0.76, "x": 0.24, "y": 0.24, **ease},
                            {"time": 0.97, "x": 0.12, "y": 0.12},
                        ],
                        "rotate": [
                            {"angle": -16},
                            {"time": 0.97, "angle": 18},
                        ],
                    },
                    "trophy_flare": {
                        "scale": [
                            {"x": 0.18, "y": 0.18},
                            {"time": 0.1, "x": 0.18, "y": 0.18},
                            {"time": 0.25, "x": 1.08, "y": 1.08, **ease},
                            {"time": 0.46, "x": 0.28, "y": 0.28, **ease},
                            {"time": 0.97, "x": 0.18, "y": 0.18},
                        ],
                        "rotate": [
                            {"angle": -12},
                            {"time": 0.46, "angle": 16, **ease},
                            {"time": 0.97, "angle": -12},
                        ],
                    },
                    "head_1": {
                        "translate": [
                            {"x": -1.5, "y": 0},
                            {"time": 0.48, "x": 1.8, "y": 3.0},
                            {"time": 0.97, "x": -1.5, "y": 0},
                        ],
                        "rotate": [
                            {"angle": -0.6},
                            {"time": 0.48, "angle": 0.8},
                            {"time": 0.97, "angle": -0.6},
                        ],
                        "scale": [
                            {"x": 1, "y": 1},
                            {"time": 0.48, "x": 1.015, "y": 1.015},
                            {"time": 0.97, "x": 1, "y": 1},
                        ],
                    },
                    "head_2": {
                        "translate": [
                            {"x": 1.2, "y": 0},
                            {"time": 0.48, "x": -2.2, "y": 3.5},
                            {"time": 0.97, "x": 1.2, "y": 0},
                        ],
                        "rotate": [
                            {"angle": 0.5},
                            {"time": 0.48, "angle": -0.9},
                            {"time": 0.97, "angle": 0.5},
                        ],
                        "scale": [
                            {"x": 1, "y": 1},
                            {"time": 0.48, "x": 1.017, "y": 1.017},
                            {"time": 0.97, "x": 1, "y": 1},
                        ],
                    },
                    "head_3": {
                        "translate": [
                            {"x": -1.2, "y": 0},
                            {"time": 0.48, "x": 1.6, "y": 2.6},
                            {"time": 0.97, "x": -1.2, "y": 0},
                        ],
                        "rotate": [
                            {"angle": -0.5},
                            {"time": 0.48, "angle": 0.7},
                            {"time": 0.97, "angle": -0.5},
                        ],
                        "scale": [
                            {"x": 1, "y": 1},
                            {"time": 0.48, "x": 1.014, "y": 1.014},
                            {"time": 0.97, "x": 1, "y": 1},
                        ],
                    },
                },
            }
        },
    }
    for name in ("head_1", "head_2", "head_3"):
        data["animations"]["animation"]["bones"].pop(name, None)
    return data


def write_skeleton() -> None:
    data = skeleton_data()
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n"
    (SPINE_DIR / "champions-league-2026.json").write_text(text, encoding="utf-8")
    (RUNTIME_DIR / "champions-league-2026.json").write_text(text, encoding="utf-8")


def main() -> None:
    # Keep the historical entry point working, but route all future builds to
    # the anatomy-safe complete-person-layer pipeline.
    from build_champions_league_regen import main as build_layered_regen

    build_layered_regen()


if __name__ == "__main__":
    main()
