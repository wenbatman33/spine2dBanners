#!/usr/bin/env python3
"""Build a layered, anatomy-safe Spine 3.8 Champions League banner."""

from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
BANNER_DIR = ROOT / "assets/banners/champions-league-2026"
SPINE_DIR = BANNER_DIR / "spine-3.8"
REGEN_DIR = SPINE_DIR / "source-character/regen-v1"
SOURCE_VFX_DIR = SPINE_DIR / "source-vfx"
SOURCE_TEXT_DIR = SPINE_DIR / "source-text-v1"
IMAGES_DIR = SPINE_DIR / "images"
RUNTIME_DIR = SPINE_DIR / "runtime"
QA_DIR = BANNER_DIR / "qa"

WIDTH = 620
HEIGHT = 272
TEXTURE_SCALE = 2
DURATION = 0.97
HALF_DURATION = DURATION / 2

# Complete-person layers only. The pivot is at the bottom centre of each image,
# so the entire head/neck/shoulder/body silhouette always moves as one unit.
LAYOUT = {
    "player_left": {"source": "left-player-rgba-v2.png", "height": 175, "x": 369, "bottom": 272},
    "player_right": {"source": "right-player-rgba-v2.png", "height": 180, "x": 552, "bottom": 272},
    "player_central": {"source": "central-player-rgba-v2.png", "height": 250, "x": 458, "bottom": 277},
    "trophy": {"source": "trophy-rgba.png", "height": 120, "x": 332, "bottom": 270},
}

TEXT_LAYOUT = {
    "title": {"x": 162, "y": 52},
    "subtitle": {"x": 140, "y": 106},
    "date": {"x": 128, "y": 151},
    "cta": {"x": 140, "y": 208},
}


def next_power_of_two(value: int) -> int:
    return 1 << math.ceil(math.log2(value))


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


def clean_transparent_rgb(image: Image.Image) -> Image.Image:
    image = image.convert("RGBA")
    pixels = []
    for red, green, blue, alpha in image.getdata():
        if alpha == 0:
            pixels.append((0, 0, 0, 0))
        else:
            pixels.append((red, green, blue, alpha))
    cleaned = Image.new("RGBA", image.size)
    cleaned.putdata(pixels)
    return cleaned


def prepare_layer(source: Path, target_height: int) -> Image.Image:
    image = clean_transparent_rgb(Image.open(source))
    alpha = image.getchannel("A")
    bbox = alpha.point(lambda value: 255 if value >= 4 else 0).getbbox()
    if not bbox:
        raise RuntimeError(f"Empty alpha silhouette: {source}")
    image = image.crop(bbox)
    target_width = round(image.width * target_height / image.height)
    return image.resize((target_width, target_height), Image.Resampling.LANCZOS)


def clean_additive_flare(source: Path) -> Image.Image:
    """Flatten a real flare onto black and suppress low-level coloured fringe."""
    image = contain(Image.open(source), (256, 256))
    flattened = Image.new("RGBA", image.size, (0, 0, 0, 255))
    flattened.alpha_composite(image)
    pixels = []
    for red, green, blue, _ in flattened.getdata():
        peak = max(red, green, blue)
        t = max(0.0, min(1.0, (peak - 42.0) / 92.0))
        strength = t * t * (3.0 - 2.0 * t)
        pixels.append(
            (
                round(red * strength),
                round(green * strength),
                round(blue * strength),
                255,
            )
        )
    cleaned = Image.new("RGBA", image.size)
    cleaned.putdata(pixels)
    return cleaned


def write_images() -> dict[str, Image.Image]:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    QA_DIR.mkdir(parents=True, exist_ok=True)

    from build_banner_typography_assets import build_typography_assets

    build_typography_assets()
    background = Image.open(REGEN_DIR / "background-textless.png").convert("RGBA")
    background = background.resize(
        (WIDTH * TEXTURE_SCALE, HEIGHT * TEXTURE_SCALE), Image.Resampling.LANCZOS
    )

    images: dict[str, Image.Image] = {"background": background}
    for name, config in LAYOUT.items():
        images[name] = prepare_layer(
            REGEN_DIR / str(config["source"]),
            int(config["height"]) * TEXTURE_SCALE,
        )

    for name in ("title", "subtitle", "date", "cta"):
        images[name] = clean_transparent_rgb(Image.open(SOURCE_TEXT_DIR / f"{name}.png"))
    for index in range(5):
        name = f"title_glint_{index}"
        images[name] = clean_transparent_rgb(Image.open(SOURCE_TEXT_DIR / f"{name}.png"))

    images["fx_flare_clean"] = clean_additive_flare(
        SOURCE_VFX_DIR / "fx-flare-source.png"
    )

    for name, image in images.items():
        image.save(IMAGES_DIR / f"{name}.png", optimize=True)

    preview = background.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    for name in ("player_left", "player_right", "player_central", "trophy"):
        layer = images[name]
        config = LAYOUT[name]
        preview_layer = layer.resize(
            (
                round(layer.width / TEXTURE_SCALE),
                round(layer.height / TEXTURE_SCALE),
            ),
            Image.Resampling.LANCZOS,
        )
        position = (
            round(float(config["x"]) - preview_layer.width / 2),
            round(float(config["bottom"]) - preview_layer.height),
        )
        preview.alpha_composite(preview_layer, position)
    for name, config in TEXT_LAYOUT.items():
        layer = images[name]
        preview_layer = layer.resize(
            (
                round(layer.width / TEXTURE_SCALE),
                round(layer.height / TEXTURE_SCALE),
            ),
            Image.Resampling.LANCZOS,
        )
        preview.alpha_composite(
            preview_layer,
            (
                round(float(config["x"]) - preview_layer.width / 2),
                round(float(config["y"]) - preview_layer.height / 2),
            ),
        )
    preview.save(QA_DIR / "advertising-v2-static-composition.png", optimize=True)
    preview.convert("RGB").save(BANNER_DIR / "champions-league-2026-banner-620x272.png", quality=95)
    return images


def pack_atlas(images: dict[str, Image.Image]) -> None:
    padding = 10
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

    used_width = max(item[1] + item[3] + padding for item in placements)
    used_height = y + row_height + padding
    atlas = Image.new(
        "RGBA",
        (next_power_of_two(used_width), next_power_of_two(used_height)),
        (0, 0, 0, 0),
    )
    for name, px, py, _, _ in placements:
        image = images[name]
        # Two-pixel colour bleed in transparent atlas padding prevents linear
        # filtering from sampling black/garbage RGB around moving cutouts.
        bleed_size = 4
        expanded_rgb = Image.new(
            "RGB",
            (image.width + bleed_size * 2, image.height + bleed_size * 2),
            (0, 0, 0),
        )
        expanded_rgb.paste(image.convert("RGB"), (bleed_size, bleed_size))
        channels = [
            channel.filter(ImageFilter.MaxFilter(bleed_size * 2 + 1))
            for channel in expanded_rgb.split()
        ]
        bleed = Image.merge("RGB", channels).convert("RGBA")
        bleed.putalpha(0)
        atlas.paste(bleed, (px - bleed_size, py - bleed_size))
        atlas.paste(image, (px, py))
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


def attachment(path: str, width: int, height: int, **extra: float | str) -> dict:
    result: dict[str, float | int | str] = {"path": path, "width": width, "height": height}
    result.update(extra)
    return result


def loop_translate(x: float, y: float, mid_x: float, mid_y: float) -> list[dict]:
    return [
        {"x": x, "y": y},
        {"time": HALF_DURATION, "x": mid_x, "y": mid_y},
        {"time": DURATION, "x": x, "y": y},
    ]


def loop_rotate(start: float, middle: float) -> list[dict]:
    return [
        {"angle": start},
        {"time": HALF_DURATION, "angle": middle},
        {"time": DURATION, "angle": start},
    ]


def skeleton_data(images: dict[str, Image.Image]) -> dict:
    bones = [{"name": "root"}, {"name": "background", "parent": "root"}]
    for name, config in LAYOUT.items():
        bones.append(
            {
                "name": name,
                "parent": "root",
                "x": float(config["x"]) - WIDTH / 2,
                "y": HEIGHT / 2 - float(config["bottom"]),
            }
        )
    for name, config in TEXT_LAYOUT.items():
        bones.append(
            {
                "name": name,
                "parent": "root",
                "x": float(config["x"]) - WIDTH / 2,
                "y": HEIGHT / 2 - float(config["y"]),
            }
        )
    bones.extend(
        [
            {"name": "cta_flare", "parent": "cta", "x": 112},
            {"name": "trophy_flare", "parent": "trophy", "y": 60},
        ]
    )

    slots = [
        {"name": "background", "bone": "background", "attachment": "background"},
        {"name": "player_left", "bone": "player_left", "attachment": "player_left"},
        {"name": "player_right", "bone": "player_right", "attachment": "player_right"},
        {"name": "player_central", "bone": "player_central", "attachment": "player_central"},
        {"name": "trophy", "bone": "trophy", "attachment": "trophy"},
        {"name": "title", "bone": "title", "attachment": "title"},
        {"name": "title_glint", "bone": "title", "attachment": "title_glint_0", "blend": "additive"},
        {"name": "subtitle", "bone": "subtitle", "attachment": "subtitle"},
        {"name": "date", "bone": "date", "attachment": "date"},
        {"name": "cta", "bone": "cta", "attachment": "cta"},
        {"name": "cta_flare", "bone": "cta_flare", "attachment": "cta_flare", "blend": "additive"},
        {"name": "trophy_flare", "bone": "trophy_flare", "attachment": "trophy_flare", "blend": "additive"},
    ]

    skin_attachments: dict[str, dict] = {
        "background": {"background": attachment("background", WIDTH, HEIGHT)},
        "cta_flare": {"cta_flare": attachment("fx_flare_clean", 56, 56)},
        "trophy_flare": {"trophy_flare": attachment("fx_flare_clean", 96, 96)},
    }
    for name in LAYOUT:
        image = images[name]
        logical_width = image.width / TEXTURE_SCALE
        logical_height = image.height / TEXTURE_SCALE
        skin_attachments[name] = {
            name: attachment(
                name,
                logical_width,
                logical_height,
                y=logical_height / 2,
            )
        }
    for name in ("title", "subtitle", "date", "cta"):
        image = images[name]
        skin_attachments[name] = {
            name: attachment(
                name,
                image.width / TEXTURE_SCALE,
                image.height / TEXTURE_SCALE,
            )
        }
    title_image = images["title"]
    skin_attachments["title_glint"] = {
        f"title_glint_{index}": attachment(
            f"title_glint_{index}",
            title_image.width / TEXTURE_SCALE,
            title_image.height / TEXTURE_SCALE,
        )
        for index in range(5)
    }

    animation = {
        "slots": {
            "title_glint": {
                "color": [
                    {"color": "ffffff00"},
                    {"time": 0.11, "color": "ffffff00"},
                    {"time": 0.16, "color": "ffffffd8"},
                    {"time": 0.49, "color": "ffffffd8"},
                    {"time": 0.55, "color": "ffffff00"},
                    {"time": DURATION, "color": "ffffff00"},
                ],
                "attachment": [
                    {"name": "title_glint_0"},
                    {"time": 0.14, "name": "title_glint_0"},
                    {"time": 0.22, "name": "title_glint_1"},
                    {"time": 0.30, "name": "title_glint_2"},
                    {"time": 0.38, "name": "title_glint_3"},
                    {"time": 0.46, "name": "title_glint_4"},
                    {"time": 0.56, "name": None},
                    {"time": DURATION, "name": None},
                ],
            },
            "cta_flare": {
                "color": [
                    {"color": "ffffff00"},
                    {"time": 0.43, "color": "ffffff00"},
                    {"time": 0.56, "color": "ffffffd8"},
                    {"time": 0.72, "color": "ffffff00"},
                    {"time": DURATION, "color": "ffffff00"},
                ]
            },
            "trophy_flare": {
                "color": [
                    {"color": "ffffff00"},
                    {"time": 0.04, "color": "ffffff00"},
                    {"time": 0.18, "color": "ffffffd8"},
                    {"time": 0.34, "color": "ffffff00"},
                    {"time": DURATION, "color": "ffffff00"},
                ]
            },
        },
        "bones": {
            "background": {
                "translate": [
                    {"x": 0, "y": 0},
                    {"time": 0.22, "x": -4.2, "y": -1.4},
                    {"time": 0.5, "x": 3.4, "y": 1.8},
                    {"time": 0.75, "x": -2.0, "y": 0.8},
                    {"time": DURATION, "x": 0, "y": 0},
                ],
                "scale": [
                    {"x": 1.0, "y": 1.0},
                    {"time": 0.22, "x": 1.04, "y": 1.04},
                    {"time": 0.5, "x": 1.015, "y": 1.015},
                    {"time": 0.75, "x": 1.032, "y": 1.032},
                    {"time": DURATION, "x": 1.0, "y": 1.0},
                ],
            },
            "player_left": {
                "translate": [
                    {"x": 0, "y": -1},
                    {"time": 0.13, "x": -3.4, "y": 8.5},
                    {"time": 0.31, "x": 2.2, "y": 1.2},
                    {"time": 0.49, "x": -2.0, "y": 7.5},
                    {"time": 0.72, "x": 2.8, "y": 0},
                    {"time": DURATION, "x": 0, "y": -1},
                ],
                "rotate": [
                    {"angle": -1.4},
                    {"time": 0.13, "angle": 1.7},
                    {"time": 0.34, "angle": -0.4},
                    {"time": 0.53, "angle": 1.45},
                    {"time": 0.76, "angle": -1.55},
                    {"time": DURATION, "angle": -1.4},
                ],
            },
            "player_right": {
                "translate": [
                    {"x": 0.8, "y": 0},
                    {"time": 0.16, "x": 4.2, "y": 7.2},
                    {"time": 0.35, "x": -2.8, "y": 1.0},
                    {"time": 0.55, "x": 2.0, "y": 8.0},
                    {"time": 0.77, "x": -3.2, "y": 0},
                    {"time": DURATION, "x": 0.8, "y": 0},
                ],
                "rotate": [
                    {"angle": 1.4},
                    {"time": 0.16, "angle": -1.6},
                    {"time": 0.37, "angle": 0.5},
                    {"time": 0.57, "angle": -1.35},
                    {"time": 0.78, "angle": 1.55},
                    {"time": DURATION, "angle": 1.4},
                ],
            },
            "player_central": {
                "translate": [
                    {"x": -2.0, "y": 0},
                    {"time": 0.16, "x": 1.0, "y": 8.8},
                    {"time": 0.34, "x": 3.8, "y": 2.4},
                    {"time": 0.53, "x": 0, "y": 9.4},
                    {"time": 0.74, "x": -3.0, "y": 1.0},
                    {"time": DURATION, "x": -2.0, "y": 0},
                ],
                "rotate": [
                    {"angle": -1.3},
                    {"time": 0.18, "angle": 1.0},
                    {"time": 0.36, "angle": 1.6},
                    {"time": 0.55, "angle": -0.2},
                    {"time": 0.75, "angle": -1.45},
                    {"time": DURATION, "angle": -1.3},
                ],
            },
            "trophy": {
                "translate": [
                    {"x": 0, "y": 0},
                    {"time": 0.19, "x": -2.2, "y": 7.2},
                    {"time": 0.43, "x": 2.0, "y": -0.8},
                    {"time": 0.68, "x": -1.4, "y": 5.4},
                    {"time": DURATION, "x": 0, "y": 0},
                ],
                "rotate": [
                    {"angle": -1.2},
                    {"time": 0.22, "angle": 1.5},
                    {"time": 0.48, "angle": -0.8},
                    {"time": 0.72, "angle": 1.1},
                    {"time": DURATION, "angle": -1.2},
                ],
                "scale": [
                    {"x": 0.94, "y": 0.94},
                    {"time": 0.22, "x": 1.10, "y": 1.10},
                    {"time": 0.48, "x": 1.0, "y": 1.0},
                    {"time": 0.72, "x": 1.07, "y": 1.07},
                    {"time": DURATION, "x": 0.94, "y": 0.94},
                ],
            },
            "title": {
                "translate": [
                    {"x": -4.0, "y": 0},
                    {"time": 0.12, "x": 6.0, "y": 3.0},
                    {"time": 0.30, "x": -3.5, "y": -1.5},
                    {"time": 0.52, "x": 4.0, "y": 2.5},
                    {"time": 0.74, "x": -2.0, "y": 0},
                    {"time": DURATION, "x": -4.0, "y": 0},
                ],
                "rotate": [
                    {"angle": -1.25},
                    {"time": 0.12, "angle": 1.0},
                    {"time": 0.32, "angle": -0.3},
                    {"time": 0.55, "angle": 0.4},
                    {"time": DURATION, "angle": -1.25},
                ],
                "scale": [
                    {"x": 0.94, "y": 0.94},
                    {"time": 0.12, "x": 1.08, "y": 1.08},
                    {"time": 0.30, "x": 0.995, "y": 0.995},
                    {"time": 0.52, "x": 1.05, "y": 1.05},
                    {"time": DURATION, "x": 0.94, "y": 0.94},
                ],
            },
            "subtitle": {
                "translate": [
                    {"x": -5.0, "y": -1.5},
                    {"time": 0.18, "x": 5.0, "y": 3.0},
                    {"time": 0.42, "x": -2.0, "y": 0},
                    {"time": 0.68, "x": 4.0, "y": 2.0},
                    {"time": DURATION, "x": -5.0, "y": -1.5},
                ],
                "scale": [
                    {"x": 0.96, "y": 0.96},
                    {"time": 0.18, "x": 1.06, "y": 1.06},
                    {"time": 0.48, "x": 1.0, "y": 1.0},
                    {"time": DURATION, "x": 0.96, "y": 0.96},
                ],
            },
            "date": {
                "translate": [
                    {"x": 5.0, "y": -1.5},
                    {"time": 0.21, "x": -5.0, "y": 3.5},
                    {"time": 0.45, "x": 4.2, "y": 0},
                    {"time": 0.7, "x": -3.0, "y": 3.0},
                    {"time": DURATION, "x": 5.0, "y": -1.5},
                ],
                "scale": [
                    {"x": 0.95, "y": 0.95},
                    {"time": 0.21, "x": 1.08, "y": 1.08},
                    {"time": 0.45, "x": 1.0, "y": 1.0},
                    {"time": 0.7, "x": 1.055, "y": 1.055},
                    {"time": DURATION, "x": 0.95, "y": 0.95},
                ],
            },
            "cta": {
                "translate": [
                    {"x": 0, "y": -2.0},
                    {"time": 0.16, "x": 0, "y": 7.0},
                    {"time": 0.38, "x": 0, "y": 0},
                    {"time": 0.62, "x": 0, "y": 5.5},
                    {"time": DURATION, "x": 0, "y": -2.0},
                ],
                "scale": [
                    {"x": 0.94, "y": 0.94},
                    {"time": 0.16, "x": 1.12, "y": 1.12},
                    {"time": 0.38, "x": 1.0, "y": 1.0},
                    {"time": 0.62, "x": 1.08, "y": 1.08},
                    {"time": DURATION, "x": 0.94, "y": 0.94},
                ],
                "shear": [
                    {"y": 0},
                    {"time": 0.16, "y": -2.8},
                    {"time": 0.38, "y": 1.2},
                    {"time": 0.62, "y": -1.3},
                    {"time": DURATION, "y": 0},
                ],
            },
            "cta_flare": {
                "scale": [
                    {"x": 0.1, "y": 0.1},
                    {"time": 0.43, "x": 0.1, "y": 0.1},
                    {"time": 0.58, "x": 0.9, "y": 0.9},
                    {"time": 0.72, "x": 0.14, "y": 0.14},
                    {"time": DURATION, "x": 0.1, "y": 0.1},
                ],
                "rotate": [
                    {"angle": -16},
                    {"time": 0.58, "angle": 18},
                    {"time": DURATION, "angle": -16},
                ],
            },
            "trophy_flare": {
                "scale": [
                    {"x": 0.1, "y": 0.1},
                    {"time": 0.04, "x": 0.1, "y": 0.1},
                    {"time": 0.2, "x": 0.86, "y": 0.86},
                    {"time": 0.34, "x": 0.14, "y": 0.14},
                    {"time": DURATION, "x": 0.1, "y": 0.1},
                ],
                "rotate": [
                    {"angle": 14},
                    {"time": 0.2, "angle": -18},
                    {"time": DURATION, "angle": 14},
                ],
            },
        },
    }

    return {
        "skeleton": {
            "hash": "codex-ucl-banner-2026-commercial-motion-v4",
            "spine": "3.8.99",
            "x": -WIDTH / 2,
            "y": -HEIGHT / 2,
            "width": WIDTH,
            "height": HEIGHT,
            "images": "./images/",
            "audio": "",
        },
        "bones": bones,
        "slots": slots,
        "skins": [{"name": "default", "attachments": skin_attachments}],
        "animations": {"animation": animation},
    }


def write_skeleton(images: dict[str, Image.Image]) -> None:
    text = json.dumps(skeleton_data(images), ensure_ascii=False, separators=(",", ":")) + "\n"
    (SPINE_DIR / "champions-league-2026.json").write_text(text, encoding="utf-8")
    (RUNTIME_DIR / "champions-league-2026.json").write_text(text, encoding="utf-8")


def main() -> None:
    images = write_images()
    pack_atlas(images)
    write_skeleton(images)
    print(f"Built layered Spine 3.8 runtime in {RUNTIME_DIR}")
    print(f"Static QA: {QA_DIR / 'advertising-v2-static-composition.png'}")


if __name__ == "__main__":
    main()
