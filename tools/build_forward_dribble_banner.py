#!/usr/bin/env python3
"""Build an original continuous-forward-dribble Spine 3.8 banner."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/banners/champions-league-2026/series/08-forward-dribble"
SOURCE = OUT / "source"
IMAGES = OUT / "spine-3.8/images"
RUNTIME = OUT / "spine-3.8/runtime"
QA = OUT / "qa"

WIDTH, HEIGHT = 620, 272
S = 2
DURATION = 1.20
PLAYER_DISPLAY_HEIGHT = 270
BALL_DISPLAY = 58
RUNNER_FRAME_COUNT = 8
RUNNER_FRAME_SIZE = (320, 384)
FONT_CJK = "/System/Library/Fonts/Hiragino Sans GB.ttc"
FONT_LATIN = "/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf"
PLAYER_LAYOUT: dict[str, tuple[int, int, int, int]] = {}
PLAYER_FULL_SIZE = (0, 0)
PLAYER_FULL_PREVIEW: Image.Image | None = None


def cjk(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_CJK, size, index=2)


def crop_alpha(image: Image.Image, threshold: int = 4) -> Image.Image:
    image = image.convert("RGBA")
    bbox = image.getchannel("A").point(
        lambda value: 255 if value >= threshold else 0
    ).getbbox()
    if not bbox:
        raise RuntimeError("empty alpha layer")
    return image.crop(bbox)


def blue_key(image: Image.Image) -> Image.Image:
    """Remove the uniform royal-blue screen and neutralise blue spill."""
    source = image.convert("RGB")
    result = Image.new("RGBA", source.size)
    output: list[tuple[int, int, int, int]] = []
    background = (5, 38, 245)
    for red, green, blue in source.getdata():
        dominance = blue - max(red, green)
        screen_score = dominance + max(0, blue - 190) * 0.35
        if screen_score >= 162:
            alpha = 0
        elif screen_score <= 54:
            alpha = 255
        else:
            alpha = round(255 * (162 - screen_score) / 108)
        if alpha <= 3:
            output.append((0, 0, 0, 0))
            continue
        amount = alpha / 255
        clean = []
        for value, back in zip((red, green, blue), background):
            corrected = (value - (1 - amount) * back) / max(0.03, amount)
            clean.append(max(0, min(255, round(corrected))))
        output.append((*clean, alpha))
    result.putdata(output)
    return crop_alpha(result)


def magenta_key(image: Image.Image) -> Image.Image:
    """Extract a photographic subject from the generated magenta plate."""
    source = image.convert("RGB")
    result = Image.new("RGBA", source.size)
    output: list[tuple[int, int, int, int]] = []
    background = (241, 13, 223)
    for red, green, blue in source.getdata():
        score = min(red, blue) - green
        if red > 175 and blue > 155 and score >= 130:
            alpha = 0
        elif red <= 145 or blue <= 125 or score <= 52:
            alpha = 255
        else:
            alpha = round(255 * (130 - score) / 78)
        if alpha <= 3:
            output.append((0, 0, 0, 0))
            continue
        amount = alpha / 255
        clean = []
        for value, back in zip((red, green, blue), background):
            corrected = (value - (1 - amount) * back) / max(0.04, amount)
            clean.append(max(0, min(255, round(corrected))))
        output.append((*clean, alpha))
    result.putdata(output)
    return result


def prepare_run_frames(contact_sheet: Image.Image) -> dict[str, Image.Image]:
    """Build eight fixed-registration full-body frames from a 4x2 plate."""
    global PLAYER_FULL_PREVIEW
    keyed = magenta_key(contact_sheet)
    cell_w = keyed.width // 4
    cell_h = keyed.height // 2
    canvas_w, canvas_h = RUNNER_FRAME_SIZE
    figures: list[Image.Image] = []
    for index in range(RUNNER_FRAME_COUNT):
        col = index % 4
        row = index // 4
        cell = keyed.crop((col * cell_w, row * cell_h, (col + 1) * cell_w, (row + 1) * cell_h))
        figures.append(crop_alpha(cell, threshold=10))

    # One shared scale is essential: fitting every pose separately makes wide
    # strides shrink and compact poses grow, which looks like zooming.
    common_scale = min(
        (canvas_h - 20) / max(figure.height for figure in figures),
        (canvas_w - 18) / max(figure.width for figure in figures),
    )
    frames: dict[str, Image.Image] = {}
    for index, figure in enumerate(figures):
        figure = figure.resize(
            (
                max(1, round(figure.width * common_scale)),
                max(1, round(figure.height * common_scale)),
            ),
            Image.Resampling.LANCZOS,
        )
        frame = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        frame.alpha_composite(figure, ((canvas_w - figure.width) // 2, canvas_h - figure.height - 8))
        frames[f"runner_{index}"] = frame
    PLAYER_FULL_PREVIEW = frames["runner_0"].copy()
    return frames


def resize_height(image: Image.Image, height: int) -> Image.Image:
    image = crop_alpha(image)
    width = round(image.width * height / image.height)
    return image.resize((width, height), Image.Resampling.LANCZOS)


def split_player_layers(player: Image.Image) -> dict[str, Image.Image]:
    """Split the purpose-built neutral master into clean articulated limbs."""
    global PLAYER_FULL_SIZE, PLAYER_FULL_PREVIEW
    PLAYER_FULL_SIZE = player.size
    PLAYER_FULL_PREVIEW = player.copy()
    width, height = player.size
    alpha = player.getchannel("A")

    def scaled(points: list[tuple[float, float]]) -> list[tuple[int, int]]:
        return [(round(x * width / 571), round(y * height / 1000)) for x, y in points]

    def extract(name: str, mask: Image.Image) -> Image.Image:
        clipped = ImageChops.multiply(alpha, mask)
        bbox = clipped.getbbox()
        if not bbox:
            raise RuntimeError(f"empty player layer: {name}")
        layer = player.copy()
        layer.putalpha(clipped)
        PLAYER_LAYOUT[name] = bbox
        # Crop only transparent padding, then keep the visible pixels at 2x
        # display density. PLAYER_LAYOUT preserves the original common canvas
        # registration so every segment still rotates around the measured joint.
        cropped = layer.crop(bbox)
        pixel_scale = PLAYER_DISPLAY_HEIGHT / height * S
        target_w = max(1, round(cropped.width * pixel_scale))
        target_h = max(1, round(cropped.height * pixel_scale))
        return cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)

    def polygon_mask(points: list[tuple[float, float]]) -> Image.Image:
        mask = Image.new("L", player.size, 0)
        ImageDraw.Draw(mask).polygon(scaled(points), fill=255)
        return mask

    # Arms are widely separated in the new master. Each is split again at the
    # elbow so the hand follows a real two-bone running arc.
    rear_arm_mask = polygon_mask([
        (176,168),(270,194),(257,292),(219,356),(187,446),(142,535),
        (76,554),(66,477),(104,375),(132,276)
    ])
    front_arm_mask = polygon_mask([
        (357,208),(449,221),(468,291),(501,348),(541,399),(571,422),
        (571,515),(530,503),(482,458),(441,406),(401,347),(369,286)
    ])

    body_mask = polygon_mask([
        (310,0),(438,0),(461,112),(446,209),(422,299),(407,438),
        (416,556),(394,664),(245,664),(209,558),(218,433),(229,320),
        (198,250),(215,146),(268,65)
    ])
    body_mask = ImageChops.subtract(
        body_mask,
        ImageChops.lighter(rear_arm_mask, front_arm_mask).filter(ImageFilter.MaxFilter(9)),
    )

    shoulder_mask = Image.new("L", player.size, 0)
    shoulder_draw = ImageDraw.Draw(shoulder_mask)
    shoulder_draw.polygon(scaled([
        (168,157),(278,180),(282,274),(222,310),(170,238)
    ]), fill=255)
    shoulder_draw.polygon(scaled([
        (350,199),(455,211),(471,305),(406,337),(356,276)
    ]), fill=255)

    pelvis_mask = Image.new("L", player.size, 0)
    ImageDraw.Draw(pelvis_mask).rectangle(
        (round(width * .37), round(height * .51), round(width * .72), round(height * .68)),
        fill=255,
    )

    rear_leg_mask = polygon_mask([
        (205,548),(334,548),(317,684),(249,806),(178,1000),
        (0,1000),(78,824),(151,676)
    ])
    front_leg_mask = polygon_mask([
        (296,548),(426,548),(467,684),(514,844),(571,1000),
        (384,1000),(358,817),(345,690)
    ])

    def band(mask: Image.Image, top: float, bottom: float) -> Image.Image:
        limiter = Image.new("L", player.size, 0)
        ImageDraw.Draw(limiter).rectangle(
            (0, round(height * top), width, round(height * bottom)), fill=255
        )
        return ImageChops.multiply(mask, limiter)

    return {
        "player_body": extract("player_body", body_mask),
        "shoulder_overlay": extract("shoulder_overlay", shoulder_mask),
        "rear_upper_arm": extract("rear_upper_arm", band(rear_arm_mask, .16, .40)),
        "rear_forearm": extract("rear_forearm", band(rear_arm_mask, .34, .56)),
        "front_upper_arm": extract("front_upper_arm", band(front_arm_mask, .20, .40)),
        "front_forearm": extract("front_forearm", band(front_arm_mask, .34, .52)),
        "pelvis_overlay": extract("pelvis_overlay", pelvis_mask),
        "rear_thigh": extract("rear_thigh", band(rear_leg_mask, .55, .76)),
        "rear_shin": extract("rear_shin", band(rear_leg_mask, .69, 1.0)),
        "front_thigh": extract("front_thigh", band(front_leg_mask, .55, .76)),
        "front_shin": extract("front_shin", band(front_leg_mask, .69, 1.0)),
    }


def render_player_afterimage(player: Image.Image) -> Image.Image:
    """Bake a soft directional trail as a real PNG effect layer."""
    target_h = PLAYER_DISPLAY_HEIGHT * S
    target_w = round(player.width * target_h / player.height)
    source = player.resize((target_w, target_h), Image.Resampling.LANCZOS)
    alpha = source.getchannel("A")

    # Keep the entire upper body sharp; only the stride receives a restrained
    # photographic smear. A full cyan duplicate reads as a ghost, not speed.
    vertical = Image.new("L", source.size, 0)
    ImageDraw.Draw(vertical).rectangle(
        (0, round(target_h * .47), target_w, target_h), fill=255
    )
    alpha = ImageChops.multiply(
        alpha, vertical.filter(ImageFilter.GaussianBlur(7 * S))
    )

    trail = Image.new("RGBA", source.size, (0, 0, 0, 0))
    for shift, opacity in ((4, 30), (10, 22), (18, 13)):
        ghost = source.copy()
        ghost.putalpha(alpha.point(
            lambda value, amount=opacity: round(value * amount / 255)
        ))
        trail.alpha_composite(ghost, (-shift * S, 0))
    return trail.filter(ImageFilter.GaussianBlur(3 * S))


def alpha_layer(mask: Image.Image, colour: tuple[int, int, int, int]) -> Image.Image:
    layer = Image.new("RGBA", mask.size, colour)
    layer.putalpha(ImageChops.multiply(mask, Image.new("L", mask.size, colour[3])))
    return layer


def gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    image = Image.new("RGBA", size)
    draw = ImageDraw.Draw(image)
    for y in range(size[1]):
        t = y / max(1, size[1] - 1)
        colour = tuple(round(a + (b - a) * t) for a, b in zip(top, bottom))
        draw.line((0, y, size[0], y), fill=(*colour, 255))
    return image


def dense_text_mask(text: str, size: int, max_width: int) -> Image.Image:
    # Build the glyphs on an oversized source canvas. Cropping only after all
    # shaping prevents the first character from being shaved by the texture.
    scratch = Image.new("L", (460 * S, 96 * S), 0)
    font = cjk(size * S)
    draw = ImageDraw.Draw(scratch)
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=S)
    draw.text(
        (28 * S - bbox[0], 16 * S - bbox[1]),
        text,
        font=font,
        fill=255,
        stroke_width=S,
        stroke_fill=255,
    )
    raw_bbox = scratch.getbbox()
    source_pad = 10 * S
    raw_bbox = (
        max(0, raw_bbox[0] - source_pad),
        max(0, raw_bbox[1] - source_pad),
        min(scratch.width, raw_bbox[2] + source_pad),
        min(scratch.height, raw_bbox[3] + source_pad),
    )
    glyph = scratch.crop(raw_bbox).filter(ImageFilter.MaxFilter(3))
    target_w = min(max_width * S, glyph.width)
    glyph = glyph.resize((target_w, glyph.height), Image.Resampling.LANCZOS)
    safe = 12 * S
    result = Image.new("L", (glyph.width + safe * 2, glyph.height + safe * 2), 0)
    result.paste(glyph, (safe, safe))
    return result


def render_title() -> tuple[Image.Image, list[Image.Image]]:
    canvas = Image.new("RGBA", (354 * S, 142 * S), (0, 0, 0, 0))
    face = Image.new("L", canvas.size, 0)
    top = dense_text_mask("带球狂飙", 46, 286)
    bottom = dense_text_mask("向前冲！", 45, 248)
    face.paste(top, (12 * S, -4 * S), top)
    face.paste(bottom, (38 * S, 62 * S), bottom)

    # Deep stadium-advertising extrusion and black silhouette.
    shadow = face.filter(ImageFilter.MaxFilter(27)).filter(ImageFilter.GaussianBlur(2 * S))
    shifted_shadow = Image.new("L", canvas.size, 0)
    shifted_shadow.paste(shadow, (8 * S, 10 * S))
    canvas.alpha_composite(alpha_layer(shifted_shadow, (0, 6, 15, 245)))
    extrusion = face.filter(ImageFilter.MaxFilter(19))
    for offset in range(10, 0, -1):
        shifted = Image.new("L", canvas.size, 0)
        shifted.paste(extrusion, (offset * S, offset * S))
        depth = 46 + offset * 5
        canvas.alpha_composite(alpha_layer(shifted, (depth, 25 + offset * 2, 2, 252)))
    canvas.alpha_composite(alpha_layer(face.filter(ImageFilter.MaxFilter(23)), (4, 6, 10, 255)))
    canvas.alpha_composite(alpha_layer(face.filter(ImageFilter.MaxFilter(13)), (112, 61, 4, 255)))
    canvas.alpha_composite(alpha_layer(face.filter(ImageFilter.MaxFilter(7)), (255, 205, 75, 255)))
    fill = gradient(canvas.size, (255, 248, 187), (190, 105, 8))
    fill.putalpha(face)
    canvas.alpha_composite(fill)

    # Top-left bevel and lower-right amber shade create the metal face.
    highlight = ImageChops.subtract(
        face,
        face.transform(
            face.size,
            Image.Transform.AFFINE,
            (1, 0, -2 * S, 0, 1, -2 * S),
            resample=Image.Resampling.BILINEAR,
        ),
    )
    canvas.alpha_composite(alpha_layer(highlight, (255, 255, 235, 205)))
    shade = ImageChops.subtract(
        face,
        face.transform(
            face.size,
            Image.Transform.AFFINE,
            (1, 0, 2 * S, 0, 1, 2 * S),
            resample=Image.Resampling.BILINEAR,
        ),
    )
    canvas.alpha_composite(alpha_layer(shade, (92, 38, 0, 150)))
    bbox = canvas.getchannel("A").getbbox()
    raw_title = canvas.crop(bbox)
    raw_face = face.crop(bbox)
    # Spine's linear filtering samples just outside the packed region. Real
    # transparent padding prevents the first and last glyph outlines clipping.
    edge_pad = 12 * S
    title = Image.new(
        "RGBA",
        (raw_title.width + edge_pad * 2, raw_title.height + edge_pad * 2),
        (0, 0, 0, 0),
    )
    title.alpha_composite(raw_title, (edge_pad, edge_pad))
    title_face = Image.new("L", title.size, 0)
    title_face.paste(raw_face, (edge_pad, edge_pad))

    glints: list[Image.Image] = []
    for index in range(7):
        centre = -20 * S + (title.width + 50 * S) * index / 6
        stripe = Image.new("L", title.size, 0)
        ImageDraw.Draw(stripe).polygon(
            [(centre - 8 * S, 0), (centre + 3 * S, 0), (centre + 40 * S, title.height), (centre + 26 * S, title.height)],
            fill=105,
        )
        stripe = stripe.filter(ImageFilter.GaussianBlur(2 * S))
        clipped = ImageChops.multiply(title_face, stripe)
        glint = Image.new("RGBA", title.size, (255, 255, 234, 0))
        glint.putalpha(clipped)
        glints.append(glint.resize((title.width // 2, title.height // 2), Image.Resampling.LANCZOS))
    return title, glints


def draw_centered(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, font: ImageFont.FreeTypeFont, **kwargs: object) -> None:
    stroke = int(kwargs.get("stroke_width", 0))
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke)
    left, top, right, bottom = box
    x = left + (right - left - (bbox[2] - bbox[0])) / 2 - bbox[0]
    y = top + (bottom - top - (bbox[3] - bbox[1])) / 2 - bbox[1]
    draw.text((round(x), round(y)), text, font=font, **kwargs)


def render_cta() -> Image.Image:
    image = Image.new("RGBA", (166 * S, 48 * S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    outer = [(13*S,2*S),(153*S,2*S),(164*S,24*S),(153*S,45*S),(13*S,45*S),(2*S,24*S)]
    draw.polygon([(x+2*S,y+3*S) for x,y in outer], fill=(0, 12, 24, 245))
    draw.polygon(outer, fill=(255, 188, 20, 255))
    draw.line(outer+[outer[0]], fill=(255, 252, 177, 255), width=2*S)
    inner = [(16*S,7*S),(150*S,7*S),(157*S,24*S),(149*S,39*S),(17*S,39*S),(9*S,24*S)]
    draw.polygon(inner, fill=(0, 134, 140, 255))
    draw.line(inner+[inner[0]], fill=(95, 255, 237, 255), width=2*S)
    draw.line((22*S,10*S,144*S,10*S), fill=(255,255,220,245), width=2*S)
    draw_centered(draw,(12*S,7*S,154*S,40*S),"立即挑战",cjk(22*S),fill=(255,255,225,255),stroke_width=2*S,stroke_fill=(0,42,55,255))
    return image


def render_badge() -> Image.Image:
    image = Image.new("RGBA", (194*S, 38*S), (0,0,0,0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((2*S,2*S,192*S,36*S), radius=17*S, fill=(0,27,46,230), outline=(48,238,217,255), width=2*S)
    draw_centered(draw,(6*S,2*S,188*S,36*S),"连续带球挑战",cjk(19*S),fill=(231,255,244,255),stroke_width=S,stroke_fill=(0,48,61,255))
    return image


def render_speed_lines() -> Image.Image:
    image = Image.new("RGBA", (WIDTH*S, HEIGHT*S), (0,0,0,0))
    draw = ImageDraw.Draw(image)
    lines = [(330,66,520,51,5),(360,94,612,84,3),(310,139,566,126,4),(342,189,618,180,5),(286,225,516,218,3)]
    for x1,y1,x2,y2,w in lines:
        draw.line((x1*S,y1*S,x2*S,y2*S),fill=(81,255,231,190),width=w*S)
        draw.ellipse(((x2-4)*S,(y2-4)*S,(x2+4)*S,(y2+4)*S),fill=(255,235,120,210))
    return image.filter(ImageFilter.GaussianBlur(2*S))


def render_shadow() -> Image.Image:
    image = Image.new("RGBA", (90*S, 24*S), (0,0,0,0))
    mask = Image.new("L", image.size, 0)
    ImageDraw.Draw(mask).ellipse((6*S,6*S,84*S,19*S), fill=170)
    mask = mask.filter(ImageFilter.GaussianBlur(5*S))
    image.putalpha(mask)
    return image


def render_contact_flash() -> Image.Image:
    """Compact accent that appears only when the shoe touches the ball."""
    image = Image.new("RGBA", (92*S, 64*S), (0,0,0,0))
    draw = ImageDraw.Draw(image)
    draw.arc((10*S,15*S,76*S,59*S), 188, 342, fill=(255,231,92,235), width=3*S)
    draw.arc((18*S,20*S,68*S,54*S), 190, 338, fill=(70,255,232,225), width=2*S)
    for x1,y1,x2,y2 in [(8,45,0,48),(18,35,4,28),(69,34,86,25),(74,44,91,45)]:
        draw.line((x1*S,y1*S,x2*S,y2*S), fill=(158,255,238,220), width=2*S)
    for x,y,r in [(14,51,3),(25,57,2),(73,52,3),(84,48,2)]:
        draw.ellipse(((x-r)*S,(y-r)*S,(x+r)*S,(y+r)*S),fill=(255,224,78,230))
    return image.filter(ImageFilter.GaussianBlur(S))


def prepare_images() -> dict[str, Image.Image]:
    background = Image.open(SOURCE / "background.png").convert("RGB").resize((WIDTH*S, HEIGHT*S), Image.Resampling.LANCZOS).convert("RGBA")
    runner_frames = prepare_run_frames(
        Image.open(SOURCE / "player-run-cycle-v4-magenta.png")
    )
    ball = resize_height(blue_key(Image.open(SOURCE / "ball-blue.png")), 380)
    title, glints = render_title()
    images = {
        "background": background,
        "ball": ball,
        "title": title,
        "cta": render_cta(),
        "badge": render_badge(),
        "speed_lines": render_speed_lines(),
        "ball_shadow": render_shadow(),
        "contact_flash": render_contact_flash(),
        **runner_frames,
    }
    for i, glint in enumerate(glints):
        images[f"title_glint_{i}"] = glint
    return images


def next_power(value: int) -> int:
    return 1 << math.ceil(math.log2(max(1, value)))


def pack(images: dict[str, Image.Image]) -> tuple[int, int]:
    padding, max_width = 6, 2048
    placements: list[tuple[str,int,int,int,int]] = []
    x = padding
    y = padding
    row_h = 0
    for name, image in sorted(images.items(), key=lambda item: item[1].height, reverse=True):
        if x + image.width + padding > max_width:
            x = padding
            y += row_h + padding
            row_h = 0
        placements.append((name, x, y, image.width, image.height))
        x += image.width + padding
        row_h = max(row_h, image.height)
    used_w = max(px + w + padding for _, px, _, w, _ in placements)
    used_h = max(py + h + padding for _, _, py, _, h in placements)
    aw, ah = next_power(used_w), next_power(used_h)
    if aw > 2048 or ah > 2048:
        raise RuntimeError(f"atlas too large {aw}x{ah}")
    atlas = Image.new("RGBA", (aw, ah), (0,0,0,0))
    for name, px, py, _, _ in placements:
        atlas.alpha_composite(images[name], (px, py))
    path = RUNTIME / "banner.png"
    atlas.save(path, optimize=True)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()[:12]
    lines = [f"banner.png?asset={digest}", f"size: {aw},{ah}", "format: RGBA8888", "filter: Linear,Linear", "repeat: none"]
    for name, px, py, w, h in placements:
        lines += [name, "  rotate: false", f"  xy: {px}, {py}", f"  size: {w}, {h}", f"  orig: {w}, {h}", "  offset: 0, 0", "  index: -1"]
    (RUNTIME / "banner.atlas").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return aw, ah


def region(path: str, width: float, height: float) -> dict:
    return {"path": path, "width": round(width, 3), "height": round(height, 3)}


def mesh(image: Image.Image, columns: int = 13, rows: int = 17) -> dict:
    height = float(PLAYER_DISPLAY_HEIGHT)
    width = image.width * height / image.height
    vertices: list[float] = []
    uvs: list[float] = []
    triangles: list[int] = []
    for row in range(rows):
        v = row / (rows - 1)
        for col in range(columns):
            u = col / (columns - 1)
            vertices += [round((u - .5) * width, 4), round((1 - v) * height, 4)]
            uvs += [round(u, 5), round(v, 5)]
    for row in range(rows - 1):
        for col in range(columns - 1):
            a = row * columns + col
            b = a + 1
            c = a + columns
            d = c + 1
            triangles += [a, c, b, b, c, d]
    return {"type":"mesh", "path":"player", "uvs":uvs, "triangles":triangles, "vertices":vertices, "hull":(columns*2+rows*2-4)*2, "width":round(width,3), "height":height}


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def rotate_delta(x: float, y: float, cx: float, cy: float, angle: float) -> tuple[float, float]:
    radians = math.radians(angle)
    dx, dy = x - cx, y - cy
    return (
        cx + dx * math.cos(radians) - dy * math.sin(radians) - x,
        cy + dx * math.sin(radians) + dy * math.cos(radians) - y,
    )


def player_deform(image: Image.Image, phase: float, columns: int = 13, rows: int = 17) -> list[float]:
    """Visible connected-mesh running stride with stable torso and joints."""
    height = float(PLAYER_DISPLAY_HEIGHT)
    width = image.width * height / image.height
    offsets: list[float] = []
    stride = math.sin(phase * math.tau)
    settle = math.cos(phase * math.tau)
    for row in range(rows):
        v = row / (rows - 1)
        y = (1 - v) * height
        for col in range(columns):
            u = col / (columns - 1)
            x = (u - .5) * width
            dx = 0.0
            dy = 1.5 * settle * clamp((v - .18) / .30) * clamp((.78 - v) / .28)

            rear_leg = clamp((.60 - u) / .34) * clamp((v - .48) / .28)
            front_leg = clamp((u - .43) / .34) * clamp((v - .48) / .28)
            rx, ry = rotate_delta(x, y, (.47-.5)*width, (1-.49)*height, 7.0 * stride)
            fx, fy = rotate_delta(x, y, (.56-.5)*width, (1-.49)*height, -8.5 * stride)
            dx += rx * rear_leg + fx * front_leg
            dy += ry * rear_leg + fy * front_leg

            rear_foot = clamp((.58-u)/.32) * clamp((v-.72)/.22)
            front_foot = clamp((u-.49)/.34) * clamp((v-.70)/.24)
            dx += (-5.0 * stride) * rear_foot + (10.0 * stride) * front_foot
            dy += (2.0 * abs(stride)) * (rear_foot + front_foot)

            rear_arm = clamp((.48 - u) / .30) * clamp((v - .13) / .18) * clamp((.49 - v) / .20)
            front_arm = clamp((u - .53) / .28) * clamp((v - .16) / .16) * clamp((.48 - v) / .18)
            ax, ay = rotate_delta(x, y, (.48-.5)*width, (1-.25)*height, -5.0 * stride)
            bx, by = rotate_delta(x, y, (.56-.5)*width, (1-.27)*height, 4.5 * stride)
            dx += ax * rear_arm + bx * front_arm
            dy += ay * rear_arm + by * front_arm
            offsets += [round(dx, 4), round(dy, 4)]
    return offsets


def screen_bone(name: str, x: float, y: float, parent: str = "root") -> dict:
    return {"name":name, "parent":parent, "x":round(x-WIDTH/2,3), "y":round(HEIGHT/2-y,3)}


def build_skeleton(images: dict[str, Image.Image]) -> dict:
    title_w, title_h = images["title"].width/S, images["title"].height/S
    bones = [
        {"name":"root"},
        {"name":"background","parent":"root"},
        {"name":"speed_lines","parent":"root"},
        screen_bone("title", 177, 76),
        {"name":"title_glint","parent":"title"},
        screen_bone("badge", 156, 170),
        screen_bone("cta", 180, 224),
        screen_bone("player", 487, 278),
        screen_bone("ball_root", 555, 243),
        {"name":"ball_shadow","parent":"ball_root","x":0,"y":-28},
        {"name":"contact_flash","parent":"ball_root","x":0,"y":-21},
        {"name":"ball","parent":"ball_root"},
    ]
    slots = [
        {"name":"background","bone":"background","attachment":"background"},
        {"name":"speed_lines","bone":"speed_lines","attachment":"speed_lines","blend":"additive","color":"ffffff00"},
        {"name":"title","bone":"title","attachment":"title"},
        {"name":"title_glint","bone":"title_glint","attachment":"title_glint_0","blend":"additive","color":"ffffff38"},
        {"name":"badge","bone":"badge","attachment":"badge"},
        {"name":"cta","bone":"cta","attachment":"cta"},
        {"name":"ball_shadow","bone":"ball_shadow","attachment":"ball_shadow"},
        {"name":"runner","bone":"player","attachment":"runner_0"},
        {"name":"contact_flash","bone":"contact_flash","attachment":"contact_flash","blend":"additive","color":"ffffff00"},
        {"name":"ball","bone":"ball","attachment":"ball"},
    ]
    attachments = {
        "background":{"background":region("background", WIDTH+22, HEIGHT+12)},
        "speed_lines":{"speed_lines":region("speed_lines", WIDTH, HEIGHT)},
        "title":{"title":region("title", title_w, title_h)},
        "title_glint":{f"title_glint_{i}":region(f"title_glint_{i}", title_w, title_h) for i in range(7)},
        "badge":{"badge":region("badge", images["badge"].width/S, images["badge"].height/S)},
        "cta":{"cta":region("cta", images["cta"].width/S, images["cta"].height/S)},
        "ball_shadow":{"ball_shadow":region("ball_shadow", 76, 16)},
        "runner":{
            f"runner_{i}":{
                **region(
                    f"runner_{i}",
                    RUNNER_FRAME_SIZE[0] * PLAYER_DISPLAY_HEIGHT / RUNNER_FRAME_SIZE[1],
                    PLAYER_DISPLAY_HEIGHT,
                ),
                "y": PLAYER_DISPLAY_HEIGHT / 2,
            }
            for i in range(RUNNER_FRAME_COUNT)
        },
        "contact_flash":{"contact_flash":region("contact_flash", 76, 52)},
        "ball":{"ball":region("ball", BALL_DISPLAY, BALL_DISPLAY)},
    }
    animation = {
        "slots":{
            "title_glint":{"attachment":[{"time":round(.08+i*.12,3),"name":f"title_glint_{i}"} for i in range(7)]},
            "runner":{"attachment":[
                {"time":round(i * DURATION / RUNNER_FRAME_COUNT, 3), "name":f"runner_{i}"}
                for i in range(RUNNER_FRAME_COUNT)
            ]},
            "speed_lines":{"color":[
                {"color":"ffffff00"},
                {"time":.14,"color":"ffffffff"},
                {"time":.88,"color":"ffffffff"},
                {"time":DURATION,"color":"ffffff00"},
            ]},
            "contact_flash":{"color":[
                {"color":"ffffffff"},{"time":.10,"color":"ffffff00"},
                {"time":.56,"color":"ffffff00"},{"time":.60,"color":"ffffffff"},
                {"time":.70,"color":"ffffff00"},{"time":DURATION,"color":"ffffff00"}
            ]},
        },
        "bones":{
            "background":{"translate":[{"x":7},{"time":DURATION,"x":-7}],"scale":[{"x":1.02,"y":1.02},{"time":DURATION,"x":1.045,"y":1.045}]},
            "speed_lines":{"translate":[{"x":90},{"time":DURATION,"x":-90}]},
            "title":{"translate":[{}, {"time":.24,"x":-3,"y":4},{"time":.60},{"time":.90,"x":-3,"y":4},{"time":DURATION}]},
            "badge":{"scale":[{}, {"time":.60,"x":1.04,"y":1.04},{"time":DURATION}]},
            "cta":{"scale":[{}, {"time":.24,"x":.95,"y":.95},{"time":.60},{"time":.90,"x":.95,"y":.95},{"time":DURATION}]},
            "player":{
                "translate":[
                    {"x":-3},{"time":.15,"x":0,"y":-2},{"time":.30,"x":3,"y":2},
                    {"time":.45,"x":5,"y":-3},{"time":.60,"x":0},
                    {"time":.75,"x":2,"y":-2},{"time":.90,"x":5,"y":2},
                    {"time":1.05,"x":7,"y":-3},{"time":DURATION,"x":-3}
                ],
            },
            "ball_root":{"translate":[
                {"x":5},{"time":.20,"x":22,"y":3},{"time":.40,"x":30,"y":1},
                {"time":.60,"x":-50},{"time":.80,"x":-18,"y":3},{"time":1.00,"x":18,"y":1},{"time":DURATION,"x":5}
            ]},
            "ball":{"rotate":[{}, {"time":.30,"angle":-180},{"time":.60,"angle":-360},{"time":.90,"angle":-540},{"time":DURATION,"angle":-720}]},
            "ball_shadow":{"scale":[{"x":1,"y":1},{"time":.34,"x":.78,"y":.78},{"time":.50,"x":1,"y":1},{"time":.60,"x":1,"y":1},{"time":.90,"x":.78,"y":.78},{"time":1.10,"x":1,"y":1},{"time":DURATION,"x":1,"y":1}]},
        },
    }
    return {
        "skeleton":{"hash":"codex-forward-dribble-v2-sequence","spine":"3.8.99","x":-310,"y":-136,"width":620,"height":272,"images":"./images/"},
        "bones":bones,
        "slots":slots,
        "skins":[{"name":"default","attachments":attachments}],
        "animations":{"animation":animation},
    }


def static_preview(images: dict[str, Image.Image]) -> None:
    preview = images["background"].copy()

    def paste_display(name: str, x: float, y: float, width: float | None = None, height: float | None = None, bottom: bool = False) -> None:
        layer = images[name]
        if height is not None:
            target_h = round(height*S)
            target_w = round(layer.width*target_h/layer.height)
        elif width is not None:
            target_w = round(width*S)
            target_h = round(layer.height*target_w/layer.width)
        else:
            target_w, target_h = layer.size
        if (target_w,target_h) != layer.size:
            layer = layer.resize((target_w,target_h), Image.Resampling.LANCZOS)
        left = round(x*S-target_w/2)
        top = round(y*S-target_h if bottom else y*S-target_h/2)
        preview.alpha_composite(layer,(left,top))

    paste_display("speed_lines", WIDTH/2, HEIGHT/2)
    paste_display("title", 177, 76)
    paste_display("badge", 156, 170)
    paste_display("cta", 180, 224)
    paste_display("ball_shadow", 555, 271, width=76)
    if PLAYER_FULL_PREVIEW is None:
        raise RuntimeError("runner preview was not prepared")
    player_preview = PLAYER_FULL_PREVIEW.resize(
        (
            round(PLAYER_FULL_PREVIEW.width * PLAYER_DISPLAY_HEIGHT * S / PLAYER_FULL_PREVIEW.height),
            PLAYER_DISPLAY_HEIGHT * S,
        ),
        Image.Resampling.LANCZOS,
    )
    preview.alpha_composite(player_preview,(round(487*S-player_preview.width/2),round(278*S-player_preview.height)))
    paste_display("contact_flash", 555, 264, width=76)
    paste_display("ball", 545, 243, height=BALL_DISPLAY)
    preview.save(QA/"forward-dribble-static.png", optimize=True)

    matte = Image.new("RGBA", (preview.width*2, preview.height), (24,25,29,255))
    matte.alpha_composite(preview,(0,0))
    white = Image.new("RGBA", preview.size, (238,238,238,255))
    white.alpha_composite(player_preview,(round(487*S-player_preview.width/2),round(278*S-player_preview.height)))
    matte.alpha_composite(white,(preview.width,0))
    matte.save(QA/"forward-dribble-matte.png", optimize=True)


def main() -> None:
    for directory in (IMAGES,RUNTIME,QA):
        directory.mkdir(parents=True,exist_ok=True)
    images = prepare_images()
    for obsolete in (
        "player.png", "leg_back.png", "leg_front.png", "rear_arm.png", "front_arm.png",
        "player_blur.png", "player_body.png", "shoulder_overlay.png", "pelvis_overlay.png",
        "rear_upper_arm.png", "rear_forearm.png", "front_upper_arm.png", "front_forearm.png",
        "rear_thigh.png", "rear_shin.png", "front_thigh.png", "front_shin.png",
    ):
        (IMAGES/obsolete).unlink(missing_ok=True)
    for name,image in images.items():
        image.save(IMAGES/f"{name}.png",optimize=True)
    aw,ah = pack(images)
    skeleton = build_skeleton(images)
    (RUNTIME/"banner.json").write_text(json.dumps(skeleton,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    static_preview(images)
    print(json.dumps({"atlas":f"{aw}x{ah}","atlas_bytes":(RUNTIME/"banner.png").stat().st_size,"duration":DURATION,"runner_sequence_frames":RUNNER_FRAME_COUNT,"alternating_feet":True,"whole_body_frames":True,"ball_rotation_degrees":720},indent=2))


if __name__ == "__main__":
    main()
