#!/usr/bin/env python3
"""Build the connected-character, 2x Spine 3.8 gift campaign banner.

The character is one continuous image and one mesh.  A small deform timeline
only moves vertices around the presenting hand, so there is no shoulder seam
or replacement arm.  The gift remains a separate compact attachment that
follows the hand.  Foreground crowd groups, title glints, and stationary light
pulses provide the advertising motion seen in the commercial reference.
"""

from __future__ import annotations

import json
import hashlib
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from ai_typography_material import material_fill


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "assets/banners/champions-league-2026/series/06-gift-goddess"
SOURCE = OUT_ROOT / "source"
SPINE_DIR = OUT_ROOT / "spine-3.8"
IMAGES_DIR = SPINE_DIR / "images"
RUNTIME_DIR = SPINE_DIR / "runtime"
QA_DIR = OUT_ROOT / "qa"

WIDTH = 620
HEIGHT = 272
TEXTURE_SCALE = 2
CHARACTER_TEXTURE_SCALE = 3
DURATION = 0.97
FONT_CJK = "/System/Library/Fonts/Hiragino Sans GB.ttc"
FONT_LATIN = "/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf"
FONT_DISPLAY_LATIN = "/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf"


def next_power_of_two(value: int) -> int:
    return 1 << math.ceil(math.log2(max(1, value)))


def crop_alpha(image: Image.Image, threshold: int = 5) -> Image.Image:
    image = image.convert("RGBA")
    bbox = image.getchannel("A").point(
        lambda value: 255 if value >= threshold else 0
    ).getbbox()
    if not bbox:
        raise RuntimeError("Layer has no visible pixels")
    return image.crop(bbox)


def resize_height(image: Image.Image, height: int) -> Image.Image:
    image = crop_alpha(image)
    width = round(image.width * height / image.height)
    return image.resize((width, height), Image.Resampling.LANCZOS)


def fit_width(image: Image.Image, width: int) -> Image.Image:
    if image.width == width:
        return image
    height = round(image.height * width / image.width)
    return image.resize((width, height), Image.Resampling.LANCZOS)


def bold_cjk(size: int) -> ImageFont.FreeTypeFont:
    # Index 2 is Hiragino Sans GB W6, not the default W3 face.
    return ImageFont.truetype(FONT_CJK, size, index=2)


def display_text_mask(
    text: str,
    font: ImageFont.FreeTypeFont,
    *,
    max_width: int,
    embolden: int,
    width_scale: float = 0.88,
) -> Image.Image:
    """Build a compact, artificially emboldened display-type mask.

    Hiragino W6 is the heaviest bundled simplified-Chinese sans face on this
    machine, but it is still too light for a commercial banner headline.
    Expanding the glyph face before slightly condensing it recreates the dense
    block-letter proportion used by the reference without sacrificing Chinese
    legibility at 620x272.
    """
    s = TEXTURE_SCALE
    scratch = Image.new("L", (520 * s, 100 * s), 0)
    draw = ImageDraw.Draw(scratch)
    bbox = draw.textbbox((0, 0), text, font=font)
    draw.text(
        (12 * s - bbox[0], 10 * s - bbox[1]),
        text,
        font=font,
        fill=255,
    )
    bbox = scratch.getbbox()
    if not bbox:
        raise RuntimeError(f"Text rendered empty: {text}")
    glyphs = scratch.crop(bbox)
    kernel = embolden * 2 * s + 1
    glyphs = glyphs.filter(ImageFilter.MaxFilter(kernel))
    target_width = min(max_width * s, round(glyphs.width * width_scale))
    return glyphs.resize((target_width, glyphs.height), Image.Resampling.LANCZOS)


def vertical_gradient(
    size: tuple[int, int], stops: list[tuple[float, tuple[int, int, int, int]]]
) -> Image.Image:
    """Return a smooth multi-stop RGBA vertical gradient."""
    width, height = size
    gradient = Image.new("RGBA", size, (0, 0, 0, 0))
    pixels = gradient.load()
    for y in range(height):
        position = y / max(1, height - 1)
        left_pos, left_colour = stops[0]
        right_pos, right_colour = stops[-1]
        for index in range(len(stops) - 1):
            if stops[index][0] <= position <= stops[index + 1][0]:
                left_pos, left_colour = stops[index]
                right_pos, right_colour = stops[index + 1]
                break
        amount = (position - left_pos) / max(0.0001, right_pos - left_pos)
        colour = tuple(
            round(left_colour[channel] + (right_colour[channel] - left_colour[channel]) * amount)
            for channel in range(4)
        )
        for x in range(width):
            pixels[x, y] = colour
    return gradient


def alpha_layer(mask: Image.Image, colour: tuple[int, int, int, int]) -> Image.Image:
    layer = Image.new("RGBA", mask.size, colour)
    layer.putalpha(ImageChops.multiply(mask, Image.new("L", mask.size, colour[3])))
    return layer


def render_title() -> tuple[Image.Image, list[Image.Image]]:
    """Render a condensed, metal-edged two-line headline plus glints."""
    s = TEXTURE_SCALE
    canvas = Image.new("RGBA", (346 * s, 132 * s), (0, 0, 0, 0))
    top_mask = Image.new("L", canvas.size, 0)
    bottom_mask = Image.new("L", canvas.size, 0)
    top_text = "女神生日限定"
    bottom_text = "礼物加码开送！"
    top_line = display_text_mask(
        top_text,
        bold_cjk(47 * s),
        max_width=286,
        embolden=1,
        width_scale=0.94,
    )
    bottom_line = display_text_mask(
        bottom_text,
        bold_cjk(42 * s),
        max_width=302,
        embolden=1,
        width_scale=0.92,
    )
    top_mask.paste(top_line, ((canvas.width - top_line.width) // 2, 5 * s))
    bottom_mask.paste(
        bottom_line,
        ((canvas.width - bottom_line.width) // 2, 65 * s),
    )
    combined = ImageChops.lighter(top_mask, bottom_mask)

    # Repeated offsets form a real lower-right extrusion instead of a blurry
    # drop shadow.  The final near-black outline keeps every glyph crisp.
    extrusion_mask = combined.filter(ImageFilter.MaxFilter(19))
    for offset in range(7, 0, -1):
        shifted = Image.new("L", canvas.size, 0)
        shifted.paste(extrusion_mask, (offset * s, offset * s))
        colour = (
            round(3 + offset * 2.2),
            round(2 + offset * 0.7),
            round(28 + offset * 5.0),
            250,
        )
        canvas.alpha_composite(alpha_layer(shifted, colour))

    outer = combined.filter(ImageFilter.MaxFilter(19))
    canvas.alpha_composite(alpha_layer(outer, (4, 2, 25, 255)))
    top_rim = top_mask.filter(ImageFilter.MaxFilter(11))
    bottom_rim = bottom_mask.filter(ImageFilter.MaxFilter(11))
    canvas.alpha_composite(alpha_layer(top_rim, (255, 68, 218, 255)))
    canvas.alpha_composite(alpha_layer(bottom_rim, (44, 226, 255, 255)))
    inner = combined.filter(ImageFilter.MaxFilter(5))
    canvas.alpha_composite(alpha_layer(inner, (255, 237, 255, 255)))

    # Bright upper faces, saturated midtones and dark lower edges create the
    # same metal-sign depth as the gold reference while retaining this
    # campaign's magenta/cyan identity.
    canvas.alpha_composite(material_fill(top_mask, 3))
    canvas.alpha_composite(material_fill(bottom_mask, 5))

    # Fine upper-left bevel and a dark lower-right inner lip.
    upper_shift = combined.transform(
        combined.size,
        Image.Transform.AFFINE,
        (1, 0, -2 * s, 0, 1, -2 * s),
        resample=Image.Resampling.BILINEAR,
    )
    lower_shift = combined.transform(
        combined.size,
        Image.Transform.AFFINE,
        (1, 0, 2 * s, 0, 1, 2 * s),
        resample=Image.Resampling.BILINEAR,
    )
    canvas.alpha_composite(
        alpha_layer(ImageChops.subtract(combined, upper_shift), (255, 255, 255, 220))
    )
    canvas.alpha_composite(
        alpha_layer(ImageChops.subtract(combined, lower_shift), (35, 3, 62, 135))
    )

    title_bbox = canvas.getchannel("A").point(
        lambda value: 255 if value >= 2 else 0
    ).getbbox()
    if not title_bbox:
        raise RuntimeError("Title rendered empty")
    title = canvas.crop(title_bbox)
    # Clip the glint to the actual glyph faces only.  Using the finished title
    # alpha would also include the connected extrusion/outline and create an
    # ugly white bar through the line gap.
    title_alpha = combined.crop(title_bbox)
    glints: list[Image.Image] = []
    band_width = 5 * s
    slant = 34 * s
    for index in range(8):
        centre = -24 * s + (title.width + 48 * s) * index / 7
        stripe = Image.new("L", title.size, 0)
        ImageDraw.Draw(stripe).polygon(
            [
                (round(centre - band_width), 0),
                (round(centre + band_width // 3), 0),
                (round(centre + slant + band_width), title.height),
                (round(centre + slant - band_width // 3), title.height),
            ],
            fill=196,
        )
        stripe = stripe.filter(ImageFilter.GaussianBlur(2 * s))
        clipped = ImageChops.multiply(title_alpha, stripe).point(lambda value: round(value * 0.40))
        lit_bbox = clipped.getbbox()
        if lit_bbox:
            spark = Image.new("L", title.size, 0)
            spark_draw = ImageDraw.Draw(spark)
            spark_x = (lit_bbox[0] + lit_bbox[2]) // 2
            spark_y = (lit_bbox[1] + lit_bbox[3]) // 2
            spark_draw.line(
                (spark_x - 7 * s, spark_y, spark_x + 7 * s, spark_y),
                fill=245,
                width=1 * s,
            )
            spark_draw.line(
                (spark_x, spark_y - 7 * s, spark_x, spark_y + 7 * s),
                fill=245,
                width=1 * s,
            )
            spark = spark.filter(ImageFilter.GaussianBlur(0.7 * s))
            clipped = ImageChops.lighter(
                clipped, ImageChops.multiply(title_alpha, spark)
            )
        glint = Image.new("RGBA", title.size, (255, 246, 205, 0))
        glint.putalpha(clipped)
        glints.append(glint)
    return title, glints


def render_kicker() -> Image.Image:
    s = TEXTURE_SCALE
    image = Image.new("RGBA", (190 * s, 24 * s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(FONT_LATIN, 19 * s)
    draw.text(
        (3 * s, -1 * s),
        "HAPPY BIRTHDAY",
        font=font,
        fill=(119, 255, 220, 255),
        stroke_width=1 * s,
        stroke_fill=(7, 62, 87, 255),
    )
    return crop_alpha(image)


def draw_centered(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    **kwargs: object,
) -> None:
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=int(kwargs.get("stroke_width", 0)))
    left, top, right, bottom = box
    x = left + (right - left - (bbox[2] - bbox[0])) / 2 - bbox[0]
    y = top + (bottom - top - (bbox[3] - bbox[1])) / 2 - bbox[1]
    draw.text((round(x), round(y)), text, font=font, **kwargs)


def render_bonus() -> Image.Image:
    s = TEXTURE_SCALE
    width, height = 142 * s, 76 * s
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    points = [
        (11 * s, 3 * s),
        (131 * s, 3 * s),
        (139 * s, 11 * s),
        (139 * s, 64 * s),
        (131 * s, 72 * s),
        (11 * s, 72 * s),
        (3 * s, 64 * s),
        (3 * s, 11 * s),
    ]
    shadow_points = [(x + 2 * s, y + 3 * s) for x, y in points]
    draw = ImageDraw.Draw(image)
    draw.polygon(shadow_points, fill=(2, 1, 18, 240))
    draw.line(
        shadow_points + [shadow_points[0]],
        fill=(61, 8, 91, 255),
        width=3 * s,
    )
    draw.polygon(points, fill=(232, 143, 31, 255))
    draw.line(points + [points[0]], fill=(255, 243, 157, 255), width=2 * s)
    inner = [
        (12 * s, 8 * s),
        (130 * s, 8 * s),
        (134 * s, 12 * s),
        (134 * s, 61 * s),
        (129 * s, 66 * s),
        (13 * s, 66 * s),
        (8 * s, 61 * s),
        (8 * s, 13 * s),
    ]
    draw.polygon(inner, fill=(25, 4, 63, 255))
    draw.line(inner + [inner[0]], fill=(255, 55, 223, 255), width=2 * s)
    draw.line(
        (14 * s, 11 * s, 128 * s, 11 * s),
        fill=(114, 245, 255, 245),
        width=2 * s,
    )
    draw.rounded_rectangle(
        (13 * s, 47 * s, 129 * s, 64 * s),
        radius=5 * s,
        fill=(95, 5, 111, 255),
        outline=(245, 72, 224, 220),
        width=1 * s,
    )
    draw_centered(
        draw,
        (10 * s, 7 * s, 132 * s, 49 * s),
        "130%",
        ImageFont.truetype(FONT_DISPLAY_LATIN, 38 * s),
        fill=(255, 244, 170, 255),
        stroke_width=2 * s,
        stroke_fill=(91, 26, 3, 255),
    )
    draw_centered(
        draw,
        (14 * s, 45 * s, 128 * s, 65 * s),
        "加码",
        bold_cjk(17 * s),
        fill=(255, 255, 255, 255),
        stroke_width=1 * s,
        stroke_fill=(49, 0, 64, 255),
    )
    for x in (16, 126):
        draw.ellipse(
            (x * s - 2 * s, 35 * s, x * s + 2 * s, 39 * s),
            fill=(255, 245, 167, 255),
        )
    return image


def render_cta() -> Image.Image:
    s = TEXTURE_SCALE
    width, height = 158 * s, 46 * s
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    outer = [
        (13 * s, 2 * s),
        (145 * s, 2 * s),
        (156 * s, 22 * s),
        (145 * s, 42 * s),
        (13 * s, 42 * s),
        (2 * s, 22 * s),
    ]
    shadow = [(x + 1 * s, y + 3 * s) for x, y in outer]
    draw.polygon(shadow, fill=(22, 1, 30, 245))
    draw.line(shadow + [shadow[0]], fill=(76, 11, 74, 255), width=3 * s)
    draw.polygon(outer, fill=(238, 132, 24, 255))
    draw.line(outer + [outer[0]], fill=(255, 244, 157, 255), width=2 * s)
    inner = [
        (15 * s, 7 * s),
        (142 * s, 7 * s),
        (150 * s, 22 * s),
        (141 * s, 37 * s),
        (16 * s, 37 * s),
        (8 * s, 22 * s),
    ]
    draw.polygon(inner, fill=(183, 13, 139, 255))
    draw.line(inner + [inner[0]], fill=(255, 73, 225, 255), width=2 * s)
    gloss = [
        (17 * s, 9 * s),
        (140 * s, 9 * s),
        (145 * s, 18 * s),
        (13 * s, 18 * s),
    ]
    draw.polygon(gloss, fill=(255, 112, 222, 150))
    draw.line(
        (20 * s, 9 * s, 137 * s, 9 * s),
        fill=(255, 246, 219, 245),
        width=2 * s,
    )
    draw_centered(
        draw,
        (11 * s, 6 * s, 147 * s, 39 * s),
        "立即领取",
        bold_cjk(22 * s),
        fill=(255, 249, 201, 255),
        stroke_width=2 * s,
        stroke_fill=(80, 4, 55, 255),
    )
    return image


def black_to_additive_alpha(image: Image.Image) -> Image.Image:
    image = image.convert("RGBA")
    luminance = image.convert("RGB").convert("L")
    image.putalpha(ImageChops.multiply(image.getchannel("A"), luminance))
    return crop_alpha(image, threshold=3)


def prepare_gift_turntable() -> dict[str, Image.Image]:
    """Extract eight real perspective views from the generated 4x2 sheet."""
    sheet = Image.open(SOURCE / "gift-turntable-8views.png").convert("RGB")
    result: dict[str, Image.Image] = {}
    for index in range(8):
        column = index % 4
        row = index // 4
        left = round(sheet.width * column / 4)
        right = round(sheet.width * (column + 1) / 4)
        top = round(sheet.height * row / 2)
        bottom = round(sheet.height * (row + 1) / 2)
        cell = sheet.crop((left, top, right, bottom))

        # The generated turntable uses a neutral grey background. Saturation
        # cleanly separates it from the cobalt/cyan/magenta object while
        # retaining the dark blue box faces and ribbon interiors.
        alpha_values: list[int] = []
        for red, green, blue in cell.getdata():
            chroma = max(red, green, blue) - min(red, green, blue)
            alpha_values.append(max(0, min(255, round((chroma - 9) * 255 / 30))))
        alpha = Image.new("L", cell.size)
        alpha.putdata(alpha_values)
        alpha = alpha.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.65))
        layer = cell.convert("RGBA")
        layer.putalpha(alpha)
        layer = crop_alpha(layer, threshold=5)
        layer = resize_height(layer, 82 * TEXTURE_SCALE)
        result[f"gift_view_{index}"] = layer
    return result


def prepare_crowd() -> tuple[dict[str, Image.Image], dict[str, tuple[float, float]]]:
    source = crop_alpha(Image.open(SOURCE / "crowd.png").convert("RGBA"), threshold=4)
    full = fit_width(source, WIDTH * TEXTURE_SCALE)
    # Cuts are placed in natural gaps between hands.  Each crop retains the
    # common baseline and can move independently without duplicated pixels.
    cuts = [0, 327, 635, full.width]
    images: dict[str, Image.Image] = {}
    positions: dict[str, tuple[float, float]] = {}
    bottom = 330.0
    for index, (left, right) in enumerate(zip(cuts, cuts[1:])):
        name = ("crowd_left", "crowd_center", "crowd_right")[index]
        layer = full.crop((left, 0, right, full.height))
        images[name] = layer
        positions[name] = (
            (left + right) / (2 * TEXTURE_SCALE),
            bottom - full.height / (2 * TEXTURE_SCALE),
        )
    return images, positions


def prepare_images() -> tuple[dict[str, Image.Image], dict[str, tuple[float, float]]]:
    background = Image.open(SOURCE / "background.png").convert("RGB")
    background = background.resize(
        (WIDTH * TEXTURE_SCALE, HEIGHT * TEXTURE_SCALE), Image.Resampling.LANCZOS
    ).convert("RGBA")

    character = resize_height(
        Image.open(SOURCE / "character.png").convert("RGBA"),
        286 * CHARACTER_TEXTURE_SCALE,
    )
    gift_views = prepare_gift_turntable()
    title, title_glints = render_title()
    flare = Image.open(
        ROOT / "assets/banners/champions-league-2026/spine-3.8/images/fx_flare_clean.png"
    ).convert("RGBA")
    flare = black_to_additive_alpha(flare).resize(
        (104 * TEXTURE_SCALE, 104 * TEXTURE_SCALE), Image.Resampling.LANCZOS
    )
    crowd_images, crowd_positions = prepare_crowd()

    images = {
        "background": background,
        "character": character,
        "flare": flare,
        "kicker": render_kicker(),
        "title": title,
        "bonus": render_bonus(),
        "cta": render_cta(),
        **gift_views,
        **crowd_images,
    }
    # Glints are translucent light only, so a 1x overlay is sufficient.  This
    # frees enough atlas space for the character to retain a genuine 3x
    # texture instead of throwing away face and hair detail.
    for index, glint in enumerate(title_glints):
        images[f"title_glint_{index}"] = glint.resize(
            (glint.width // 2, glint.height // 2), Image.Resampling.LANCZOS
        )
    return images, crowd_positions


def pack_atlas(images: dict[str, Image.Image]) -> tuple[int, int]:
    padding = 6
    placements: list[tuple[str, int, int, int, int]] = []
    # MaxRects-style packing keeps the 3x character and 2x background while
    # filling their unused corners with the eight compact turntable views.
    free: list[tuple[int, int, int, int]] = [(padding, padding, 2048-padding*2, 2048-padding*2)]

    def intersects(a: tuple[int,int,int,int], b: tuple[int,int,int,int]) -> bool:
        ax,ay,aw,ah=a; bx,by,bw,bh=b
        return ax < bx+bw and ax+aw > bx and ay < by+bh and ay+ah > by

    def contains(a: tuple[int,int,int,int], b: tuple[int,int,int,int]) -> bool:
        ax,ay,aw,ah=a; bx,by,bw,bh=b
        return bx >= ax and by >= ay and bx+bw <= ax+aw and by+bh <= ay+ah

    for name, image in sorted(
        images.items(), key=lambda item: (item[1].width*item[1].height, max(item[1].size)), reverse=True
    ):
        required_w, required_h = image.width + padding, image.height + padding
        candidates = [
            (min(w-required_w,h-required_h), max(w-required_w,h-required_h), i, x, y)
            for i,(x,y,w,h) in enumerate(free)
            if required_w <= w and required_h <= h
        ]
        if not candidates:
            raise RuntimeError(f"2x atlas exceeded 2048 while placing {name}")
        _,_,_,px,py = min(candidates)
        placed = (px,py,required_w,required_h)
        placements.append((name,px,py,image.width,image.height))

        split: list[tuple[int,int,int,int]] = []
        for fx,fy,fw,fh in free:
            current=(fx,fy,fw,fh)
            if not intersects(current,placed):
                split.append(current)
                continue
            pr=px+required_w; pb=py+required_h; fr=fx+fw; fb=fy+fh
            if px>fx: split.append((fx,fy,px-fx,fh))
            if pr<fr: split.append((pr,fy,fr-pr,fh))
            if py>fy: split.append((fx,fy,fw,py-fy))
            if pb<fb: split.append((fx,pb,fw,fb-pb))
        free=[]
        for candidate in split:
            if candidate[2] <= 0 or candidate[3] <= 0:
                continue
            if any(candidate != other and contains(other,candidate) for other in split):
                continue
            free.append(candidate)

    used_width = max(px + width + padding for _, px, _, width, _ in placements)
    used_height = max(py + height + padding for _, _, py, _, height in placements)
    atlas_width = next_power_of_two(used_width)
    atlas_height = next_power_of_two(used_height)
    if atlas_width > 2048 or atlas_height > 2048:
        raise RuntimeError(f"2x atlas exceeded 2048: {atlas_width}x{atlas_height}")

    atlas = Image.new("RGBA", (atlas_width, atlas_height), (0, 0, 0, 0))
    for name, px, py, _, _ in placements:
        atlas.alpha_composite(images[name], (px, py))
    texture_path = RUNTIME_DIR / "banner.png"
    atlas.save(texture_path, optimize=True)
    texture_hash = hashlib.sha256(texture_path.read_bytes()).hexdigest()[:12]

    lines = [
        f"banner.png?asset={texture_hash}",
        f"size: {atlas_width},{atlas_height}",
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
    (RUNTIME_DIR / "banner.atlas").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return atlas_width, atlas_height


def region(path: str, image: Image.Image, **values: float) -> dict:
    result: dict[str, float | str] = {
        "path": path,
        "width": round(image.width / TEXTURE_SCALE, 3),
        "height": round(image.height / TEXTURE_SCALE, 3),
    }
    result.update(values)
    return result


def character_mesh(image: Image.Image, columns: int = 9, rows: int = 9) -> dict:
    width = image.width / CHARACTER_TEXTURE_SCALE
    height = image.height / CHARACTER_TEXTURE_SCALE
    vertices: list[float] = []
    uvs: list[float] = []
    for row in range(rows):
        v = row / (rows - 1)
        for column in range(columns):
            u = column / (columns - 1)
            vertices.extend([round((u - 0.5) * width, 4), round((1 - v) * height, 4)])
            uvs.extend([round(u, 5), round(v, 5)])
    triangles: list[int] = []
    for row in range(rows - 1):
        for column in range(columns - 1):
            top_left = row * columns + column
            top_right = top_left + 1
            bottom_left = top_left + columns
            bottom_right = bottom_left + 1
            triangles.extend(
                [top_left, bottom_left, top_right, top_right, bottom_left, bottom_right]
            )
    return {
        "type": "mesh",
        "path": "character",
        "uvs": uvs,
        "triangles": triangles,
        "vertices": vertices,
        "hull": 2 * columns + 2 * rows - 4,
        "width": round(width, 3),
        "height": round(height, 3),
    }


def hand_deform(amount: float, columns: int = 9, rows: int = 9) -> list[float]:
    """Taper deformation from the palm through forearm to a fixed shoulder."""
    values: list[float] = []
    for row in range(rows):
        v = row / (rows - 1)
        for column in range(columns):
            u = column / (columns - 1)
            x_weight = max(0.0, min(1.0, (0.44 - u) / 0.38))
            y_weight = max(0.0, 1.0 - abs(v - 0.72) / 0.27)
            weight = x_weight * y_weight
            dx = -15.5 * amount * weight
            dy = 3.2 * amount * weight * (1.05 - 0.45 * u)
            values.extend([round(dx, 4), round(dy, 4)])
    return values


def screen_bone(name: str, screen_x: float, screen_y: float, parent: str = "root") -> dict:
    return {
        "name": name,
        "parent": parent,
        "x": round(screen_x - WIDTH / 2, 3),
        "y": round(HEIGHT / 2 - screen_y, 3),
    }


def skeleton(
    images: dict[str, Image.Image], crowd_positions: dict[str, tuple[float, float]]
) -> dict:
    character_x = 489.0
    character_bottom = 287.0
    gift_x = 378.0
    gift_y = 178.0
    title_x = 166.0
    title_y = 88.0

    bones = [
        {"name": "root"},
        {"name": "background", "parent": "root"},
        screen_bone("flare_left", 358, 118),
        screen_bone("flare_right", 565, 62),
        screen_bone("kicker", 103, 18),
        screen_bone("title", title_x, title_y),
        {"name": "title_glint", "parent": "title"},
        screen_bone("character", character_x, character_bottom),
        {
            "name": "gift",
            "parent": "character",
            "x": gift_x - character_x,
            "y": character_bottom - gift_y,
        },
        {"name": "gift_glow", "parent": "gift"},
        *[
            screen_bone(name, position[0], position[1])
            for name, position in crowd_positions.items()
        ],
        screen_bone("bonus", 76, 220),
        screen_bone("cta", 215, 226),
    ]

    slots = [
        {"name": "background", "bone": "background", "attachment": "background"},
        {
            "name": "flare_left",
            "bone": "flare_left",
            "attachment": "flare",
            "blend": "additive",
        },
        {
            "name": "flare_right",
            "bone": "flare_right",
            "attachment": "flare",
            "blend": "additive",
        },
        {"name": "kicker", "bone": "kicker", "attachment": "kicker"},
        {"name": "title", "bone": "title", "attachment": "title"},
        {
            "name": "title_glint",
            "bone": "title_glint",
            "attachment": "title_glint_0",
            "blend": "additive",
        },
        {"name": "character", "bone": "character", "attachment": "character"},
        {
            "name": "gift_glow",
            "bone": "gift_glow",
            "attachment": "flare",
            "blend": "additive",
        },
        {"name": "gift", "bone": "gift", "attachment": "gift_view_0"},
        {"name": "crowd_left", "bone": "crowd_left", "attachment": "crowd_left"},
        {
            "name": "crowd_center",
            "bone": "crowd_center",
            "attachment": "crowd_center",
        },
        {"name": "crowd_right", "bone": "crowd_right", "attachment": "crowd_right"},
        {"name": "bonus", "bone": "bonus", "attachment": "bonus"},
        {"name": "cta", "bone": "cta", "attachment": "cta"},
    ]

    attachments = {
        "background": {"background": region("background", images["background"])},
        "flare_left": {
            "flare": region("flare", images["flare"], width=126, height=126)
        },
        "flare_right": {
            "flare": region("flare", images["flare"], width=92, height=92)
        },
        "kicker": {"kicker": region("kicker", images["kicker"])},
        "title": {"title": region("title", images["title"])},
        "title_glint": {
            f"title_glint_{index}": region(
                f"title_glint_{index}",
                images[f"title_glint_{index}"],
                width=images["title"].width / TEXTURE_SCALE,
                height=images["title"].height / TEXTURE_SCALE,
            )
            for index in range(8)
        },
        "character": {"character": character_mesh(images["character"])},
        "gift_glow": {"flare": region("flare", images["flare"], width=110, height=110)},
        "gift": {
            f"gift_view_{index}": region(f"gift_view_{index}", images[f"gift_view_{index}"])
            for index in range(8)
        },
        "crowd_left": {"crowd_left": region("crowd_left", images["crowd_left"])},
        "crowd_center": {
            "crowd_center": region("crowd_center", images["crowd_center"])
        },
        "crowd_right": {"crowd_right": region("crowd_right", images["crowd_right"])},
        "bonus": {"bonus": region("bonus", images["bonus"])},
        "cta": {"cta": region("cta", images["cta"])},
    }

    animation = {
        "slots": {
            "title_glint": {
                "attachment": [
                    {"time": round(0.07 + index * 0.10, 3), "name": f"title_glint_{index}"}
                    for index in range(8)
                ]
            },
            "flare_left": {
                "color": [
                    {"color": "ffffff22"},
                    {"time": 0.32, "color": "ffffff72"},
                    {"time": DURATION, "color": "ffffff22"},
                ]
            },
            "flare_right": {
                "color": [
                    {"color": "ffffff64"},
                    {"time": 0.55, "color": "ffffff18"},
                    {"time": DURATION, "color": "ffffff64"},
                ]
            },
            "gift_glow": {
                "color": [
                    {"color": "ffffffa8"},
                    {"time": 0.24, "color": "ffffff20"},
                    {"time": 0.485, "color": "ffffffff"},
                    {"time": 0.72, "color": "ffffff20"},
                    {"time": DURATION, "color": "ffffffa8"},
                ]
            },
            "gift": {
                "attachment": [
                    {"time": 0.000, "name": "gift_view_0"},
                    {"time": 0.120, "name": "gift_view_1"},
                    {"time": 0.240, "name": "gift_view_2"},
                    {"time": 0.360, "name": "gift_view_3"},
                    {"time": 0.485, "name": "gift_view_4"},
                    {"time": 0.600, "name": "gift_view_5"},
                    {"time": 0.720, "name": "gift_view_6"},
                    {"time": 0.840, "name": "gift_view_7"},
                    {"time": DURATION, "name": "gift_view_0"},
                ]
            },
        },
        "bones": {
            "background": {
                "scale": [
                    {"x": 1.02, "y": 1.02},
                    {"time": 0.48, "x": 1.045, "y": 1.045},
                    {"time": DURATION, "x": 1.02, "y": 1.02},
                ],
                "translate": [
                    {"x": -1.5, "y": 0},
                    {"time": 0.48, "x": 1.5, "y": 0.8},
                    {"time": DURATION, "x": -1.5, "y": 0},
                ],
            },
            "flare_left": {
                "scale": [
                    {"x": 0.88, "y": 0.88},
                    {"time": 0.32, "x": 1.08, "y": 1.08},
                    {"time": DURATION, "x": 0.88, "y": 0.88},
                ]
            },
            "flare_right": {
                "scale": [
                    {"x": 1.06, "y": 1.06},
                    {"time": 0.55, "x": 0.82, "y": 0.82},
                    {"time": DURATION, "x": 1.06, "y": 1.06},
                ]
            },
            "title": {
                "scale": [
                    {"x": 0.985, "y": 0.985},
                    {"time": 0.16, "x": 1.035, "y": 1.035},
                    {"time": 0.42, "x": 1.0, "y": 1.0},
                    {"time": DURATION, "x": 0.985, "y": 0.985},
                ],
                "translate": [
                    {"x": 0, "y": -1},
                    {"time": 0.16, "x": 0, "y": 1},
                    {"time": DURATION, "x": 0, "y": -1},
                ],
            },
            "character": {
                "rotate": [
                    {"angle": 0},
                    {"time": 0.5, "angle": -0.65},
                    {"time": DURATION, "angle": 0},
                ]
            },
            "gift_glow": {
                "scale": [
                    {"x": 1.0, "y": 1.0},
                    {"time": 0.24, "x": 0.34, "y": 0.82},
                    {"time": 0.485, "x": 1.08, "y": 1.08},
                    {"time": 0.72, "x": 0.34, "y": 0.82},
                    {"time": DURATION, "x": 1.0, "y": 1.0},
                ],
                "rotate": [
                    {"angle": 0},
                    {"time": DURATION, "angle": 0},
                ],
            },
            "crowd_left": {
                "translate": [
                    {"x": 0, "y": -4},
                    {"time": 0.23, "x": 0, "y": 7},
                    {"time": 0.5, "x": 0, "y": -3},
                    {"time": 0.73, "x": 0, "y": 5},
                    {"time": DURATION, "x": 0, "y": -4},
                ],
                "rotate": [
                    {"angle": -2.4},
                    {"time": 0.5, "angle": 3.1},
                    {"time": DURATION, "angle": -2.4},
                ],
            },
            "crowd_center": {
                "translate": [
                    {"x": 0, "y": 5},
                    {"time": 0.26, "x": 0, "y": -5},
                    {"time": 0.53, "x": 0, "y": 7},
                    {"time": 0.78, "x": 0, "y": -4},
                    {"time": DURATION, "x": 0, "y": 5},
                ],
                "rotate": [
                    {"angle": 2.1},
                    {"time": 0.5, "angle": -2.8},
                    {"time": DURATION, "angle": 2.1},
                ],
            },
            "crowd_right": {
                "translate": [
                    {"x": 0, "y": -2},
                    {"time": 0.18, "x": 0, "y": 8},
                    {"time": 0.46, "x": 0, "y": -4},
                    {"time": 0.7, "x": 0, "y": 6},
                    {"time": DURATION, "x": 0, "y": -2},
                ],
                "rotate": [
                    {"angle": -1.8},
                    {"time": 0.46, "angle": 2.7},
                    {"time": DURATION, "angle": -1.8},
                ],
            },
            "bonus": {
                "scale": [
                    {"x": 0.97, "y": 0.97},
                    {"time": 0.18, "x": 1.065, "y": 1.065},
                    {"time": DURATION, "x": 0.97, "y": 0.97},
                ]
            },
            "cta": {
                "scale": [
                    {"x": 0.98, "y": 0.98},
                    {"time": 0.28, "x": 1.06, "y": 1.06},
                    {"time": 0.58, "x": 1.0, "y": 1.0},
                    {"time": DURATION, "x": 0.98, "y": 0.98},
                ]
            },
        },
        "deform": {
            "default": {
                "character": {
                    "character": [
                        {"vertices": hand_deform(0.0)},
                        {"time": 0.22, "vertices": hand_deform(0.42)},
                        {"time": 0.53, "vertices": hand_deform(1.0)},
                        {"time": 0.76, "vertices": hand_deform(0.33)},
                        {"time": DURATION, "vertices": hand_deform(0.0)},
                    ]
                }
            }
        },
    }

    return {
        "skeleton": {
            "hash": "codex-gift-goddess-turntable-v5",
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
        "skins": [{"name": "default", "attachments": attachments}],
        "animations": {"animation": animation},
    }


def write_static_qa(
    images: dict[str, Image.Image], crowd_positions: dict[str, tuple[float, float]]
) -> None:
    s = TEXTURE_SCALE
    preview = images["background"].copy()

    def composite(name: str, center_x: float, center_y: float) -> None:
        layer = images[name]
        preview.alpha_composite(
            layer,
            (
                round(center_x * s - layer.width / 2),
                round(center_y * s - layer.height / 2),
            ),
        )

    # Stationary background flares are subtle; the runtime only pulses them.
    flare_left = images["flare"].resize((126 * s, 126 * s), Image.Resampling.LANCZOS)
    flare_right = images["flare"].resize((92 * s, 92 * s), Image.Resampling.LANCZOS)
    preview.alpha_composite(flare_left, (round((358 - 63) * s), round((118 - 63) * s)))
    preview.alpha_composite(flare_right, (round((565 - 46) * s), round((62 - 46) * s)))
    composite("kicker", 103, 18)
    composite("title", 166, 88)

    character = images["character"]
    character_preview = character.resize(
        (
            round(character.width * TEXTURE_SCALE / CHARACTER_TEXTURE_SCALE),
            round(character.height * TEXTURE_SCALE / CHARACTER_TEXTURE_SCALE),
        ),
        Image.Resampling.LANCZOS,
    )
    preview.alpha_composite(
        character_preview,
        (
            round(489 * s - character_preview.width / 2),
            round(287 * s - character_preview.height),
        ),
    )
    composite("flare", 378, 178)
    composite("gift_view_0", 378, 178)

    for name, position in crowd_positions.items():
        composite(name, position[0], position[1])
    composite("bonus", 76, 220)
    composite("cta", 215, 226)
    preview.save(QA_DIR / "gift-goddess-connected-static.png", optimize=True)

    matte = Image.new("RGBA", (preview.width * 2, preview.height), (4, 8, 18, 255))
    matte.alpha_composite(preview, (0, 0))
    grey = Image.new("RGBA", preview.size, (78, 80, 88, 255))
    character_only = Image.new("RGBA", preview.size, (0, 0, 0, 0))
    character_only.alpha_composite(
        character_preview,
        (
            round(489 * s - character_preview.width / 2),
            round(287 * s - character_preview.height),
        ),
    )
    grey.alpha_composite(character_only)
    matte.alpha_composite(grey, (preview.width, 0))
    matte.save(QA_DIR / "gift-goddess-connected-matte.png", optimize=True)


def main() -> None:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    QA_DIR.mkdir(parents=True, exist_ok=True)

    images, crowd_positions = prepare_images()
    (IMAGES_DIR / "gift.png").unlink(missing_ok=True)
    for name, image in images.items():
        image.save(IMAGES_DIR / f"{name}.png", optimize=True)
    atlas_width, atlas_height = pack_atlas(images)

    data = skeleton(images, crowd_positions)
    encoded = json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n"
    (RUNTIME_DIR / "banner.json").write_text(encoded, encoding="utf-8")
    write_static_qa(images, crowd_positions)

    report = {
        "atlas": f"{atlas_width}x{atlas_height}",
        "atlas_bytes": (RUNTIME_DIR / "banner.png").stat().st_size,
        "json_bytes": (RUNTIME_DIR / "banner.json").stat().st_size,
        "texture_scale": TEXTURE_SCALE,
        "single_connected_character_mesh": True,
        "separate_arm_attachment": False,
        "mid_gifts_layer_removed": True,
        "character_sequence_frames": 0,
        "title_glint_overlays": 8,
        "independent_crowd_groups": 3,
        "gift_y_axis_turn_degrees": 360,
        "gift_turntable_views": 8,
    }
    (QA_DIR / "build-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
