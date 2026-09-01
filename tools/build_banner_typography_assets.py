#!/usr/bin/env python3
"""Render separated Simplified-Chinese advertising typography to PNG layers."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps

from ai_typography_material import material_fill


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "assets/banners/champions-league-2026/spine-3.8/source-text-v1"
FONT = Path("/System/Library/Fonts/Hiragino Sans GB.ttc")
FONT_INDEX = 2
SCALE = 3
OUTPUT_SCALE = 2


def linear_gradient(size: tuple[int, int], top: tuple[int, ...], bottom: tuple[int, ...]) -> Image.Image:
    image = Image.new("RGBA", size)
    pixels = image.load()
    denominator = max(1, size[1] - 1)
    for y in range(size[1]):
        t = y / denominator
        colour = tuple(round(top[i] * (1 - t) + bottom[i] * t) for i in range(4))
        for x in range(size[0]):
            pixels[x, y] = colour
    return image


def render_text_layer(
    text: str,
    font_size: int,
    top: tuple[int, int, int, int],
    bottom: tuple[int, int, int, int],
    outer_stroke: tuple[int, int, int, int],
    stroke_width: int,
    shadow: bool = True,
    extrude_depth: int = 0,
    material_index: int | None = None,
) -> Image.Image:
    font = ImageFont.truetype(str(FONT), font_size * SCALE, index=FONT_INDEX)
    probe = Image.new("L", (8, 8))
    bbox = ImageDraw.Draw(probe).textbbox(
        (0, 0), text, font=font, stroke_width=stroke_width * SCALE
    )
    pad = (stroke_width + 7) * SCALE
    width = bbox[2] - bbox[0] + pad * 2
    height = bbox[3] - bbox[1] + pad * 2
    origin = (pad - bbox[0], pad - bbox[1])

    layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    if shadow:
        shadow_mask = Image.new("L", layer.size, 0)
        ImageDraw.Draw(shadow_mask).text(
            (origin[0] + 3 * SCALE, origin[1] + 4 * SCALE),
            text,
            font=font,
            fill=220,
            stroke_width=(stroke_width + 2) * SCALE,
            stroke_fill=235,
        )
        shadow_rgba = Image.new("RGBA", layer.size, (0, 3, 15, 0))
        shadow_rgba.putalpha(shadow_mask.filter(ImageFilter.GaussianBlur(2.4 * SCALE)))
        layer.alpha_composite(shadow_rgba)

    if extrude_depth:
        extrusion = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        extrusion_draw = ImageDraw.Draw(extrusion)
        for offset in range(extrude_depth * SCALE, 0, -SCALE):
            extrusion_draw.text(
                (origin[0] + offset, origin[1] + offset),
                text,
                font=font,
                fill=(91, 45, 3, 255),
                stroke_width=(stroke_width + 1) * SCALE,
                stroke_fill=(1, 4, 18, 255),
            )
        layer.alpha_composite(extrusion)

    outline = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    ImageDraw.Draw(outline).text(
        origin,
        text,
        font=font,
        fill=outer_stroke,
        stroke_width=stroke_width * SCALE,
        stroke_fill=(1, 5, 22, 255),
    )
    layer.alpha_composite(outline)

    fill_mask = Image.new("L", layer.size, 0)
    ImageDraw.Draw(fill_mask).text(origin, text, font=font, fill=255)
    if material_index is None:
        fill = linear_gradient(layer.size, top, bottom)
        fill.putalpha(fill_mask)
    else:
        fill = material_fill(fill_mask, material_index)
    layer.alpha_composite(fill)

    # A restrained top-edge specular highlight gives the title a bevel without
    # sacrificing Chinese glyph readability.
    highlight = Image.new("RGBA", layer.size, (255, 250, 205, 0))
    highlight_mask = fill_mask.filter(ImageFilter.GaussianBlur(0.55 * SCALE))
    highlight_mask = ImageChops.subtract(highlight_mask, fill_mask.filter(ImageFilter.MinFilter(3)))
    highlight.putalpha(highlight_mask.point(lambda value: round(value * 0.72)))
    layer.alpha_composite(highlight)

    return layer.resize(
        (
            round(layer.width * OUTPUT_SCALE / SCALE),
            round(layer.height * OUTPUT_SCALE / SCALE),
        ),
        Image.Resampling.LANCZOS,
    )


def render_cta() -> Image.Image:
    size = (254 * SCALE, 55 * SCALE)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    shadow = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        (8 * SCALE, 9 * SCALE, 246 * SCALE, 52 * SCALE),
        radius=13 * SCALE,
        fill=(0, 0, 0, 190),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(3 * SCALE))
    canvas.alpha_composite(shadow)

    button_mask = Image.new("L", size, 0)
    ImageDraw.Draw(button_mask).rounded_rectangle(
        (5 * SCALE, 4 * SCALE, 249 * SCALE, 49 * SCALE),
        radius=12 * SCALE,
        fill=255,
    )
    button = linear_gradient(size, (224, 42, 26, 255), (103, 3, 8, 255))
    button.putalpha(button_mask)
    canvas.alpha_composite(button)

    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(
        (5 * SCALE, 4 * SCALE, 249 * SCALE, 49 * SCALE),
        radius=12 * SCALE,
        outline=(255, 211, 88, 255),
        width=2 * SCALE,
    )
    draw.rounded_rectangle(
        (9 * SCALE, 8 * SCALE, 245 * SCALE, 45 * SCALE),
        radius=9 * SCALE,
        outline=(255, 120, 53, 220),
        width=SCALE,
    )
    font = ImageFont.truetype(str(FONT), 26 * SCALE, index=FONT_INDEX)
    text = "立即关注赛程"
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=SCALE)
    position = ((size[0] - (bbox[2] - bbox[0])) // 2, 23 * SCALE - (bbox[3] - bbox[1]) // 2 - bbox[1])
    draw.text(
        position,
        text,
        font=font,
        fill=(255, 248, 213, 255),
        stroke_width=SCALE,
        stroke_fill=(77, 4, 6, 255),
    )
    return canvas.resize(
        (254 * OUTPUT_SCALE, 55 * OUTPUT_SCALE), Image.Resampling.LANCZOS
    )


def render_title_glints(title: Image.Image, frame_count: int = 5) -> list[Image.Image]:
    alpha = title.getchannel("A")
    luminance = ImageOps.grayscale(title.convert("RGB"))
    bright_fill = luminance.point(
        lambda value: 0 if value < 105 else min(255, round((value - 105) * 1.7))
    )
    glyph_fill = ImageChops.multiply(alpha, bright_fill)
    glints: list[Image.Image] = []
    travel = title.width + 54
    for index in range(frame_count):
        centre = -27 + travel * index / (frame_count - 1)
        stripe = Image.new("L", title.size, 0)
        polygon = [
            (centre - 8, 0),
            (centre + 3, 0),
            (centre + 18, title.height),
            (centre + 7, title.height),
        ]
        ImageDraw.Draw(stripe).polygon(polygon, fill=78)
        stripe = stripe.filter(ImageFilter.GaussianBlur(2.2))
        clipped = ImageChops.multiply(glyph_fill, stripe)
        glint = Image.new("RGBA", title.size, (255, 241, 151, 0))
        glint.putalpha(clipped)
        glints.append(glint)
    return glints


def build_typography_assets() -> dict[str, Image.Image]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    assets = {
        "title": render_text_layer(
            "欧冠巅峰之夜",
            43,
            (255, 252, 214, 255),
            (205, 126, 14, 255),
            (64, 34, 4, 255),
            3,
            extrude_depth=5,
            material_index=0,
        ),
        "subtitle": render_text_layer(
            "2026/27 群星决战欧洲之巅",
            18,
            (255, 255, 255, 255),
            (172, 204, 245, 255),
            (15, 34, 75, 255),
            2,
            shadow=False,
            material_index=1,
        ),
        "date": render_text_layer(
            "9月8日  热血开战",
            25,
            (255, 251, 218, 255),
            (240, 176, 54, 255),
            (76, 41, 5, 255),
            2,
            material_index=0,
        ),
        "cta": render_cta(),
    }
    for name, image in assets.items():
        image.save(OUTPUT_DIR / f"{name}.png", optimize=True)

    for index, glint in enumerate(render_title_glints(assets["title"])):
        name = f"title_glint_{index}"
        assets[name] = glint
        glint.save(OUTPUT_DIR / f"{name}.png", optimize=True)
    return assets


def main() -> None:
    assets = build_typography_assets()
    print("typography assets:")
    for name, image in assets.items():
        print(f"  {name}: {image.width}x{image.height}")


if __name__ == "__main__":
    main()
