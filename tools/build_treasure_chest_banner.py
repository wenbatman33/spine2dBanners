#!/usr/bin/env python3
"""Build the portable Spine 3.8 treasure-chest advertising banner."""

from __future__ import annotations

import hashlib
import json
import math
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from ai_typography_material import material_fill


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/banners/champions-league-2026/series/09-treasure-chest"
SOURCE = OUT / "source"
IMAGES = OUT / "spine-3.8/images"
RUNTIME = OUT / "spine-3.8/runtime"
QA = OUT / "qa"

WIDTH, HEIGHT = 620, 272
S = 2
DURATION = 2.65
POSE_DISPLAY_SCALE = 1.43
FONT_CJK = "/System/Library/Fonts/Hiragino Sans GB.ttc"
FONT_LATIN = "/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf"


def cjk(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_CJK, size, index=2)


def crop_alpha(image: Image.Image, padding: int = 0) -> tuple[Image.Image, tuple[int, int, int, int]]:
    image = image.convert("RGBA")
    bbox = image.getchannel("A").getbbox()
    if not bbox:
        raise RuntimeError("empty alpha layer")
    left = max(0, bbox[0] - padding)
    top = max(0, bbox[1] - padding)
    right = min(image.width, bbox[2] + padding)
    bottom = min(image.height, bbox[3] + padding)
    return image.crop((left, top, right, bottom)), (left, top, right, bottom)


def smoothstep(edge0: float, edge1: float, value: float) -> float:
    ratio = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return ratio * ratio * (3.0 - 2.0 * ratio)


def chroma_extract(cell: Image.Image) -> Image.Image:
    """Remove the generated green screen and neutralize edge spill."""
    source = cell.convert("RGB")
    output_pixels: list[tuple[int, int, int, int]] = []
    pixels = source.load()
    for y in range(source.height):
        for x in range(source.width):
            red, green, blue = pixels[x, y]
            dominance = green - max(red, blue)
            keyed = smoothstep(45.0, 180.0, green) * smoothstep(16.0, 120.0, dominance)
            alpha = round(255.0 * (1.0 - keyed))
            if alpha <= 2:
                output_pixels.append((0, 0, 0, 0))
                continue
            if dominance > 3:
                green = min(green, max(red, blue) + 3)
            output_pixels.append((red, green, blue, alpha))
    output = Image.new("RGBA", source.size)
    output.putdata(output_pixels)
    alpha = output.getchannel("A").filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.55))
    output.putalpha(alpha)
    return output


def prepare_keyposes() -> tuple[dict[str, Image.Image], dict[str, dict[str, float]]]:
    master = Image.open(SOURCE / "chest-keyposes-green-v2.png").convert("RGB")
    cell_width = master.width // 3
    cell_height = master.height // 2
    images: dict[str, Image.Image] = {}
    registrations: dict[str, dict[str, float]] = {}
    for index, (column, row) in enumerate(((0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1))):
        cell = master.crop(
            (
                column * cell_width,
                row * cell_height,
                (column + 1) * cell_width,
                (row + 1) * cell_height,
            )
        )
        extracted = chroma_extract(cell)
        cropped, bbox = crop_alpha(extracted, 3)
        name = f"chest_{index}"
        images[name] = cropped
        display_width = cropped.width / S * POSE_DISPLAY_SCALE
        display_height = cropped.height / S * POSE_DISPLAY_SCALE
        registrations[name] = {
            # All poses share one mechanical anchor: the middle of the chest base.
            # This keeps the body fixed while only the generated lid angle changes.
            "x": 0,
            "y": round(display_height / 2, 3),
            "width": round(display_width, 3),
            "height": round(display_height, 3),
        }
    return images, registrations


def alpha_layer(mask: Image.Image, colour: tuple[int, int, int, int]) -> Image.Image:
    result = Image.new("RGBA", mask.size, colour)
    result.putalpha(ImageChops.multiply(mask, Image.new("L", mask.size, colour[3])))
    return result


def gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    image = Image.new("RGBA", size)
    draw = ImageDraw.Draw(image)
    for y in range(size[1]):
        ratio = y / max(1, size[1] - 1)
        colour = tuple(round(a + (b - a) * ratio) for a, b in zip(top, bottom))
        draw.line((0, y, size[0], y), fill=(*colour, 255))
    return image


def render_text_mask(text: str, size: int, max_width: int) -> Image.Image:
    scratch = Image.new("L", (520 * S, 110 * S), 0)
    font = cjk(size * S)
    draw = ImageDraw.Draw(scratch)
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=1 * S)
    draw.text((18 * S - bbox[0], 10 * S - bbox[1]), text, font=font, fill=255, stroke_width=S, stroke_fill=255)
    glyph = scratch.crop(scratch.getbbox())
    if glyph.width > max_width * S:
        glyph = glyph.resize((max_width * S, round(glyph.height * max_width * S / glyph.width)), Image.Resampling.LANCZOS)
    return glyph


def render_title() -> tuple[Image.Image, list[Image.Image]]:
    canvas = Image.new("RGBA", (340 * S, 122 * S), (0, 0, 0, 0))
    face = Image.new("L", canvas.size, 0)
    line1 = render_text_mask("开箱暴击", 52, 290)
    line2 = render_text_mask("史诗宝藏大放送", 30, 280)
    face.paste(line1, (28 * S, 3 * S))
    face.paste(line2, (34 * S, 69 * S))

    # Deep navy drop block, outer bronze rim, bright gold bevel, then gold face.
    for offset in range(9, 1, -1):
        shifted = Image.new("L", canvas.size, 0)
        shifted.paste(face, (offset * S, offset * S))
        canvas.alpha_composite(alpha_layer(shifted.filter(ImageFilter.MaxFilter(7)), (1, 18, 42, 245)))
    canvas.alpha_composite(alpha_layer(face.filter(ImageFilter.MaxFilter(17)), (69, 28, 2, 255)))
    canvas.alpha_composite(alpha_layer(face.filter(ImageFilter.MaxFilter(11)), (255, 123, 9, 255)))
    canvas.alpha_composite(alpha_layer(face.filter(ImageFilter.MaxFilter(5)), (255, 240, 132, 255)))
    canvas.alpha_composite(material_fill(face, 4))

    bevel = ImageChops.subtract(
        face,
        face.transform(face.size, Image.Transform.AFFINE, (1, 0, -2 * S, 0, 1, -2 * S), resample=Image.Resampling.BILINEAR),
    )
    canvas.alpha_composite(alpha_layer(bevel, (255, 255, 255, 150)))
    title, bbox = crop_alpha(canvas, 8 * S)
    title_face = face.crop(bbox)
    glints: list[Image.Image] = []
    for index in range(7):
        center = -30 * S + (title.width + 60 * S) * index / 6
        stripe = Image.new("L", title.size, 0)
        ImageDraw.Draw(stripe).polygon(
            [
                (center - 8 * S, 0),
                (center + 2 * S, 0),
                (center + 44 * S, title.height),
                (center + 29 * S, title.height),
            ],
            fill=120,
        )
        stripe = stripe.filter(ImageFilter.GaussianBlur(2 * S))
        clipped = ImageChops.multiply(title_face, stripe).point(lambda value: round(value * 0.40))
        glint = Image.new("RGBA", title.size, (255, 255, 226, 0))
        glint.putalpha(clipped)
        glints.append(glint)
    return title, glints


def draw_centered(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    **kwargs: object,
) -> None:
    stroke = int(kwargs.get("stroke_width", 0))
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke)
    left, top, right, bottom = box
    x = left + (right - left - (bbox[2] - bbox[0])) / 2 - bbox[0]
    y = top + (bottom - top - (bbox[3] - bbox[1])) / 2 - bbox[1]
    draw.text((round(x), round(y)), text, font=font, **kwargs)


def render_subtitle() -> Image.Image:
    image = Image.new("RGBA", (268 * S, 40 * S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((2 * S, 2 * S, 266 * S, 38 * S), radius=18 * S, fill=(4, 26, 56, 238), outline=(255, 190, 58, 255), width=2 * S)
    draw_centered(draw, (8 * S, 2 * S, 260 * S, 38 * S), "登录即领 · 最高 8,888 金币", cjk(18 * S), fill=(255, 247, 201, 255), stroke_width=S, stroke_fill=(70, 29, 2, 255))
    return image


def render_cta() -> Image.Image:
    image = Image.new("RGBA", (180 * S, 48 * S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    outer = [(13*S,2*S),(167*S,2*S),(178*S,24*S),(167*S,46*S),(13*S,46*S),(2*S,24*S)]
    shadow = [(x + 3 * S, y + 3 * S) for x, y in outer]
    draw.polygon(shadow, fill=(18, 4, 1, 230))
    draw.polygon(outer, fill=(255, 185, 25, 255))
    draw.line(outer + [outer[0]], fill=(255, 251, 180, 255), width=2 * S)
    inner = [(17*S,7*S),(163*S,7*S),(171*S,24*S),(162*S,40*S),(18*S,40*S),(9*S,24*S)]
    draw.polygon(inner, fill=(182, 40, 12, 255))
    draw.line(inner + [inner[0]], fill=(255, 105, 24, 255), width=2 * S)
    draw.line((26*S,11*S,154*S,11*S), fill=(255, 237, 171, 255), width=2 * S)
    draw_centered(draw, (13*S,6*S,167*S,42*S), "立即开启", cjk(24 * S), fill=(255, 249, 210, 255), stroke_width=2*S, stroke_fill=(74, 13, 2, 255))
    return image


def render_kicker() -> Image.Image:
    image = Image.new("RGBA", (235 * S, 27 * S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.text((4 * S, -1 * S), "EPIC TREASURE DROP", font=ImageFont.truetype(FONT_LATIN, 22 * S), fill=(115, 225, 255, 255), stroke_width=S, stroke_fill=(0, 34, 77, 255))
    cropped, _ = crop_alpha(image, 2 * S)
    return cropped


def prepare_images() -> tuple[dict[str, Image.Image], dict[str, dict[str, float]]]:
    background = Image.open(SOURCE / "background-master.png").convert("RGB")
    source_ratio = background.width / background.height
    target_ratio = WIDTH / HEIGHT
    if source_ratio > target_ratio:
        crop_width = round(background.height * target_ratio)
        left = background.width - crop_width
        background = background.crop((left, 0, left + crop_width, background.height))
    else:
        crop_height = round(background.width / target_ratio)
        top = max(0, (background.height - crop_height) // 2)
        background = background.crop((0, top, background.width, top + crop_height))
    background = background.resize((WIDTH * S, HEIGHT * S), Image.Resampling.LANCZOS).convert("RGBA")

    keyposes, registrations = prepare_keyposes()
    title, glints = render_title()
    images: dict[str, Image.Image] = {
        "background": background,
        "title": title,
        "subtitle": render_subtitle(),
        "cta": render_cta(),
        "kicker": render_kicker(),
    }
    images.update(keyposes)
    for index, glint in enumerate(glints):
        images[f"title_glint_{index}"] = glint

    flare_source = Image.open(
        ROOT / "assets/banners/champions-league-2026/series/06-gift-goddess/spine-3.8/images/flare.png"
    ).convert("RGBA")
    flare, _ = crop_alpha(flare_source, 2)
    images["flare"] = flare.resize((340 * S, 210 * S), Image.Resampling.LANCZOS)
    return images, registrations


def next_power(value: int) -> int:
    return 1 << math.ceil(math.log2(max(1, value)))


def pack(images: dict[str, Image.Image]) -> tuple[int, int]:
    padding, max_width = 6, 2048
    placements: list[tuple[str, int, int, int, int]] = []
    x = y = row_height = padding
    for name, image in sorted(images.items(), key=lambda item: item[1].height, reverse=True):
        if x + image.width + padding > max_width:
            x = padding
            y += row_height + padding
            row_height = 0
        placements.append((name, x, y, image.width, image.height))
        x += image.width + padding
        row_height = max(row_height, image.height)
    used_width = max(x + width + padding for _, x, _, width, _ in placements)
    used_height = max(y + height + padding for _, _, y, _, height in placements)
    atlas_width = next_power(used_width)
    atlas_height = next_power(used_height)
    if atlas_width > 2048 or atlas_height > 2048:
        raise RuntimeError(f"atlas too large: {atlas_width}x{atlas_height}")
    atlas = Image.new("RGBA", (atlas_width, atlas_height), (0, 0, 0, 0))
    for name, left, top, _, _ in placements:
        atlas.alpha_composite(images[name], (left, top))
    atlas_path = RUNTIME / "banner.png"
    atlas.save(atlas_path, optimize=True)
    pngquant = shutil.which("pngquant")
    if pngquant:
        quantized = atlas_path.with_suffix(".quant.png")
        result = subprocess.run(
            [
                pngquant,
                "--force",
                "--strip",
                "--speed",
                "1",
                "--quality",
                "70-95",
                "--output",
                str(quantized),
                str(atlas_path),
            ],
            check=False,
            capture_output=True,
        )
        if result.returncode == 0 and quantized.exists():
            quantized.replace(atlas_path)
        elif quantized.exists():
            quantized.unlink()
    digest = hashlib.sha256(atlas_path.read_bytes()).hexdigest()[:12]
    lines = [
        f"banner.png?asset={digest}",
        f"size: {atlas_width},{atlas_height}",
        "format: RGBA8888",
        "filter: Linear,Linear",
        "repeat: none",
    ]
    for name, left, top, width, height in placements:
        lines += [
            name,
            "  rotate: false",
            f"  xy: {left}, {top}",
            f"  size: {width}, {height}",
            f"  orig: {width}, {height}",
            "  offset: 0, 0",
            "  index: -1",
        ]
    (RUNTIME / "banner.atlas").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return atlas_width, atlas_height


def region(path: str, width: float, height: float, x: float = 0, y: float = 0) -> dict[str, object]:
    result: dict[str, object] = {"path": path, "width": round(width, 3), "height": round(height, 3)}
    if x:
        result["x"] = round(x, 3)
    if y:
        result["y"] = round(y, 3)
    return result


def screen_bone(name: str, x: float, y: float, parent: str = "root") -> dict[str, object]:
    return {"name": name, "parent": parent, "x": round(x - WIDTH / 2, 3), "y": round(HEIGHT / 2 - y, 3)}


def build_skeleton(images: dict[str, Image.Image], registrations: dict[str, dict[str, float]]) -> dict[str, object]:
    title_width = images["title"].width / S
    title_height = images["title"].height / S
    bones = [
        {"name": "root"},
        {"name": "background", "parent": "root"},
        screen_bone("light_back", 478, 184),
        screen_bone("chest", 478, 266),
        screen_bone("light_front", 478, 184),
        screen_bone("title", 185, 88),
        {"name": "title_glint", "parent": "title"},
        screen_bone("kicker", 176, 14),
        screen_bone("subtitle", 178, 169),
        screen_bone("cta", 177, 226),
    ]
    slots = [
        {"name": "background", "bone": "background", "attachment": "background"},
        {"name": "light_back", "bone": "light_back", "attachment": "flare", "blend": "additive", "color": "ffffff00"},
        *[
            {
                "name": f"chest_pose_{index}",
                "bone": "chest",
                "attachment": f"chest_{index}",
                "color": "ffffffff" if index == 0 else "ffffff00",
            }
            for index in range(6)
        ],
        {"name": "light_front", "bone": "light_front", "attachment": "flare", "blend": "additive", "color": "fff1a800"},
        {"name": "kicker", "bone": "kicker", "attachment": "kicker"},
        {"name": "title", "bone": "title", "attachment": "title"},
        {"name": "title_glint", "bone": "title_glint", "attachment": "title_glint_0", "blend": "additive", "color": "ffffff70"},
        {"name": "subtitle", "bone": "subtitle", "attachment": "subtitle"},
        {"name": "cta", "bone": "cta", "attachment": "cta"},
    ]
    attachments = {
        "background": {"background": region("background", WIDTH, HEIGHT)},
        "light_back": {"flare": region("flare", 340, 210)},
        **{
            f"chest_pose_{index}": {
                f"chest_{index}": region(
                    f"chest_{index}",
                    registrations[f"chest_{index}"]["width"],
                    registrations[f"chest_{index}"]["height"],
                    registrations[f"chest_{index}"]["x"],
                    registrations[f"chest_{index}"]["y"],
                )
            }
            for index in range(6)
        },
        "light_front": {"flare": region("flare", 340, 210)},
        "kicker": {"kicker": region("kicker", images["kicker"].width / S, images["kicker"].height / S)},
        "title": {"title": region("title", title_width, title_height)},
        "title_glint": {
            f"title_glint_{index}": region(f"title_glint_{index}", title_width, title_height)
            for index in range(7)
        },
        "subtitle": {"subtitle": region("subtitle", images["subtitle"].width / S, images["subtitle"].height / S)},
        "cta": {"cta": region("cta", images["cta"].width / S, images["cta"].height / S)},
    }
    pose_states = [
        (0.00, 0),
        (0.12, 0),
        (0.20, 1),
        (0.28, 2),
        (0.36, 3),
        (0.44, 4),
        (0.52, 5),
        (2.02, 5),
        (2.10, 4),
        (2.18, 3),
        (2.26, 2),
        (2.34, 1),
        (2.42, 0),
        (DURATION, 0),
    ]
    chest_fades = {
        f"chest_pose_{pose}": {
            "color": [
                {
                    **({} if time == 0 else {"time": time}),
                    "color": "ffffffff" if active_pose == pose else "ffffff00",
                }
                for time, active_pose in pose_states
            ]
        }
        for pose in range(6)
    }
    animation = {
        "slots": {
            **chest_fades,
            "light_back": {
                "color": [
                    {"color": "ffffff00"},
                    {"time": 0.24, "color": "ffffff00"},
                    {"time": 0.39, "color": "fff4bfff"},
                    {"time": 0.56, "color": "ffd76eb8"},
                    {"time": 1.94, "color": "ffc9576c"},
                    {"time": 2.16, "color": "ffffff00"},
                    {"time": DURATION, "color": "ffffff00"},
                ]
            },
            "light_front": {
                "color": [
                    {"color": "fff1a800"},
                    {"time": 0.29, "color": "fff1a800"},
                    {"time": 0.40, "color": "fff6c9da"},
                    {"time": 0.55, "color": "ffd66a55"},
                    {"time": 1.94, "color": "ffc45e38"},
                    {"time": 2.16, "color": "fff1a800"},
                    {"time": DURATION, "color": "fff1a800"},
                ]
            },
            "title_glint": {
                "attachment": [
                    {"time": 0, "name": "title_glint_0"},
                    *[
                        {"time": round(0.58 + index * 0.105, 3), "name": f"title_glint_{index}"}
                        for index in range(7)
                    ],
                    {"time": 1.31, "name": "title_glint_6"},
                ]
            },
        },
        "bones": {
            "background": {
                "translate": [{"x": -2}, {"time": 1.32, "x": 2}, {"time": DURATION, "x": -2}],
                "scale": [{"x": 1.018, "y": 1.018}, {"time": 1.32, "x": 1.025, "y": 1.025}, {"time": DURATION, "x": 1.018, "y": 1.018}],
            },
            "chest": {
                "translate": [
                    {},
                    {"time": 0.08, "y": -3},
                    {"time": 0.18, "y": 2},
                    {"time": 0.36},
                    {"time": 2.02},
                    {"time": 2.16, "y": 1},
                    {"time": 2.42},
                    {"time": DURATION},
                ],
                "rotate": [
                    {},
                    {"time": 0.08, "angle": -0.55},
                    {"time": 0.18, "angle": 0.4},
                    {"time": 0.36},
                    {"time": 2.02},
                    {"time": 2.16, "angle": -0.35},
                    {"time": 2.42},
                    {"time": DURATION},
                ],
            },
            "light_back": {
                "scale": [
                    {"x": 0.35, "y": 0.35},
                    {"time": 0.24, "x": 0.35, "y": 0.35},
                    {"time": 0.42, "x": 1.25, "y": 1.25},
                    {"time": 0.66, "x": 0.92, "y": 0.92},
                    {"time": 1.96, "x": 0.82, "y": 0.82},
                    {"time": 2.18, "x": 0.35, "y": 0.35},
                    {"time": DURATION, "x": 0.35, "y": 0.35},
                ],
                "rotate": [{}, {"time": 1.8, "angle": 26}, {"time": DURATION, "angle": 30}],
            },
            "light_front": {
                "scale": [
                    {"x": 0.2, "y": 0.2},
                    {"time": 0.28, "x": 0.2, "y": 0.2},
                    {"time": 0.42, "x": 0.84, "y": 0.84},
                    {"time": 0.66, "x": 0.48, "y": 0.48},
                    {"time": 1.96, "x": 0.38, "y": 0.38},
                    {"time": 2.18, "x": 0.2, "y": 0.2},
                    {"time": DURATION, "x": 0.2, "y": 0.2},
                ],
                "rotate": [{}, {"time": 1.8, "angle": -35}, {"time": DURATION, "angle": -40}],
            },
            "title": {
                "scale": [
                    {},
                    {"time": 0.52, "x": 0.98, "y": 0.98},
                    {"time": 0.67, "x": 1.035, "y": 1.035},
                    {"time": 0.86},
                    {"time": DURATION},
                ]
            },
            "subtitle": {
                "translate": [{}, {"time": 0.58, "x": 3}, {"time": 0.86}, {"time": DURATION}],
            },
            "cta": {
                "scale": [
                    {},
                    {"time": 0.52, "x": 0.93, "y": 0.93},
                    {"time": 0.70, "x": 1.08, "y": 1.08},
                    {"time": 0.90},
                    {"time": 1.48, "x": 1.035, "y": 1.035},
                    {"time": 1.68},
                    {"time": DURATION},
                ]
            },
        },
    }
    return {
        "skeleton": {
            "hash": "codex-treasure-chest-v1",
            "spine": "3.8.99",
            "x": -310,
            "y": -136,
            "width": WIDTH,
            "height": HEIGHT,
            "images": "./images/",
        },
        "bones": bones,
        "slots": slots,
        "skins": [{"name": "default", "attachments": attachments}],
        "animations": {"animation": animation},
    }


def static_preview(images: dict[str, Image.Image], registrations: dict[str, dict[str, float]]) -> None:
    preview = images["background"].copy()

    def paste_center(name: str, x: float, y: float, width: float | None = None) -> None:
        layer = images[name]
        if width is not None:
            target_width = round(width * S)
            target_height = round(layer.height * target_width / layer.width)
            layer = layer.resize((target_width, target_height), Image.Resampling.LANCZOS)
        preview.alpha_composite(layer, (round(x * S - layer.width / 2), round(y * S - layer.height / 2)))

    paste_center("kicker", 176, 14)
    paste_center("title", 185, 88)
    paste_center("subtitle", 178, 169)
    paste_center("cta", 177, 226)
    name = "chest_5"
    registration = registrations[name]
    layer = images[name]
    center_x = (478 + registration["x"]) * S
    center_y = (266 - registration["y"]) * S
    preview.alpha_composite(layer, (round(center_x - layer.width / 2), round(center_y - layer.height / 2)))
    QA.mkdir(parents=True, exist_ok=True)
    preview.save(QA / "treasure-chest-static.png", optimize=True)

    matte = Image.new("RGBA", (preview.width * 2, preview.height), (24, 25, 29, 255))
    matte.alpha_composite(preview, (0, 0))
    light = Image.new("RGBA", preview.size, (238, 238, 238, 255))
    light.alpha_composite(layer, (round(center_x - layer.width / 2), round(center_y - layer.height / 2)))
    matte.alpha_composite(light, (preview.width, 0))
    matte.save(QA / "treasure-chest-matte.png", optimize=True)

    pose_sheet = Image.new("RGBA", (930, 544), (3, 12, 27, 255))
    pose_draw = ImageDraw.Draw(pose_sheet)
    for index in range(6):
        column, row = index % 3, index // 3
        pose_name = f"chest_{index}"
        pose = images[pose_name]
        pose_width = round(registrations[pose_name]["width"])
        pose_height = round(registrations[pose_name]["height"])
        pose = pose.resize((pose_width, pose_height), Image.Resampling.LANCZOS)
        center_x = column * 310 + 155
        bottom = row * 272 + 264
        pose_sheet.alpha_composite(pose, (round(center_x - pose_width / 2), bottom - pose_height))
        pose_draw.text((column * 310 + 14, row * 272 + 12), f"0{index + 1}", font=ImageFont.truetype(FONT_LATIN, 24), fill=(116, 225, 255, 255))
    pose_sheet.save(QA / "treasure-chest-poses.png", optimize=True)


def main() -> None:
    for directory in (IMAGES, RUNTIME, QA):
        directory.mkdir(parents=True, exist_ok=True)
    images, registrations = prepare_images()
    for name, image in images.items():
        image.save(IMAGES / f"{name}.png", optimize=True)
    atlas_width, atlas_height = pack(images)
    skeleton = build_skeleton(images, registrations)
    (RUNTIME / "banner.json").write_text(
        json.dumps(skeleton, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    static_preview(images, registrations)
    report = {
        "atlas": f"{atlas_width}x{atlas_height}",
        "atlas_bytes": (RUNTIME / "banner.png").stat().st_size,
        "duration": DURATION,
        "key_poses": 6,
        "pose_transition": "crossfade",
        "opening_sequence": True,
        "portable": True,
    }
    (QA / "build-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
