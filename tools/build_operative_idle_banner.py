#!/usr/bin/env python3
"""Build a portable Spine 3.8 banner with one continuous idle character mesh."""

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
OUT = ROOT / "assets/banners/champions-league-2026/series/10-operative-idle"
SOURCE = OUT / "source"
IMAGES = OUT / "spine-3.8/images"
RUNTIME = OUT / "spine-3.8/runtime"
QA = OUT / "qa"

WIDTH, HEIGHT = 620, 272
S = 2
DURATION = 2.8
CHARACTER_HEIGHT = 260
MESH_COLUMNS = 15
MESH_ROWS = 19
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


def crop_cover(image: Image.Image, width: int, height: int, bias_x: float = 0.5) -> Image.Image:
    source_ratio = image.width / image.height
    target_ratio = width / height
    if source_ratio > target_ratio:
        crop_width = round(image.height * target_ratio)
        left = round((image.width - crop_width) * bias_x)
        image = image.crop((left, 0, left + crop_width, image.height))
    else:
        crop_height = round(image.width / target_ratio)
        top = max(0, (image.height - crop_height) // 2)
        image = image.crop((0, top, image.width, top + crop_height))
    return image.resize((width, height), Image.Resampling.LANCZOS)


def alpha_layer(mask: Image.Image, colour: tuple[int, int, int, int]) -> Image.Image:
    layer = Image.new("RGBA", mask.size, colour)
    layer.putalpha(ImageChops.multiply(mask, Image.new("L", mask.size, colour[3])))
    return layer


def render_text_mask(text: str, size: int, max_width: int) -> Image.Image:
    scratch = Image.new("L", (480 * S, 100 * S), 0)
    font = cjk(size * S)
    draw = ImageDraw.Draw(scratch)
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=S)
    draw.text((16 * S - bbox[0], 8 * S - bbox[1]), text, font=font, fill=255, stroke_width=S, stroke_fill=255)
    glyph = scratch.crop(scratch.getbbox())
    if glyph.width > max_width * S:
        glyph = glyph.resize((max_width * S, round(glyph.height * max_width * S / glyph.width)), Image.Resampling.LANCZOS)
    return glyph


def render_title() -> tuple[Image.Image, list[Image.Image]]:
    canvas = Image.new("RGBA", (330 * S, 126 * S), (0, 0, 0, 0))
    face = Image.new("L", canvas.size, 0)
    line1 = render_text_mask("王牌特勤", 56, 276)
    line2 = render_text_mask("补给限时送", 34, 276)
    face.paste(line1, (26 * S, 2 * S))
    face.paste(line2, (28 * S, 69 * S))

    for offset in range(9, 2, -1):
        shifted = Image.new("L", canvas.size, 0)
        shifted.paste(face, (offset * S, offset * S))
        canvas.alpha_composite(alpha_layer(shifted.filter(ImageFilter.MaxFilter(5)), (0, 10, 36, 250)))
    canvas.alpha_composite(alpha_layer(face.filter(ImageFilter.MaxFilter(17)), (2, 35, 67, 255)))
    canvas.alpha_composite(alpha_layer(face.filter(ImageFilter.MaxFilter(11)), (10, 223, 241, 255)))
    canvas.alpha_composite(alpha_layer(face.filter(ImageFilter.MaxFilter(5)), (255, 213, 56, 255)))

    canvas.alpha_composite(material_fill(face, 1))

    bevel = ImageChops.subtract(
        face,
        face.transform(face.size, Image.Transform.AFFINE, (1, 0, -2 * S, 0, 1, -2 * S), resample=Image.Resampling.BILINEAR),
    )
    canvas.alpha_composite(alpha_layer(bevel, (255, 255, 255, 150)))
    title, bbox = crop_alpha(canvas, 8 * S)
    title_face = face.crop(bbox)
    glints: list[Image.Image] = []
    for index in range(7):
        center = -28 * S + (title.width + 56 * S) * index / 6
        stripe = Image.new("L", title.size, 0)
        ImageDraw.Draw(stripe).polygon(
            [(center - 9 * S, 0), (center + 3 * S, 0), (center + 45 * S, title.height), (center + 28 * S, title.height)],
            fill=150,
        )
        clipped = ImageChops.multiply(title_face, stripe.filter(ImageFilter.GaussianBlur(2 * S))).point(lambda value: round(value * 0.40))
        glint = Image.new("RGBA", title.size, (255, 255, 232, 0))
        glint.putalpha(clipped)
        glints.append(glint)
    return title, glints


def draw_centered(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, font: ImageFont.FreeTypeFont, **kwargs: object) -> None:
    stroke = int(kwargs.get("stroke_width", 0))
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke)
    left, top, right, bottom = box
    x = left + (right - left - (bbox[2] - bbox[0])) / 2 - bbox[0]
    y = top + (bottom - top - (bbox[3] - bbox[1])) / 2 - bbox[1]
    draw.text((round(x), round(y)), text, font=font, **kwargs)


def render_kicker() -> Image.Image:
    image = Image.new("RGBA", (220 * S, 24 * S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.text((4 * S, -2 * S), "TACTICAL REWARD", font=ImageFont.truetype(FONT_LATIN, 21 * S), fill=(94, 236, 255, 255), stroke_width=S, stroke_fill=(0, 26, 58, 255))
    return crop_alpha(image, 2 * S)[0]


def render_subtitle() -> Image.Image:
    image = Image.new("RGBA", (276 * S, 39 * S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((2 * S, 2 * S, 274 * S, 37 * S), radius=17 * S, fill=(2, 19, 43, 238), outline=(60, 232, 242, 255), width=2 * S)
    draw_centered(draw, (7 * S, 2 * S, 269 * S, 37 * S), "登录即领 · 稀有作战装备", cjk(18 * S), fill=(241, 252, 255, 255), stroke_width=S, stroke_fill=(0, 20, 42, 255))
    return image


def render_cta() -> Image.Image:
    image = Image.new("RGBA", (182 * S, 48 * S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    outer = [(13*S,2*S),(169*S,2*S),(180*S,24*S),(169*S,46*S),(13*S,46*S),(2*S,24*S)]
    draw.polygon([(x + 3 * S, y + 3 * S) for x, y in outer], fill=(0, 4, 18, 235))
    draw.polygon(outer, fill=(255, 207, 47, 255))
    draw.line(outer + [outer[0]], fill=(255, 250, 184, 255), width=2 * S)
    inner = [(18*S,7*S),(164*S,7*S),(173*S,24*S),(163*S,40*S),(18*S,40*S),(9*S,24*S)]
    draw.polygon(inner, fill=(0, 139, 164, 255))
    draw.line(inner + [inner[0]], fill=(38, 240, 248, 255), width=2 * S)
    draw.line((28*S,11*S,154*S,11*S), fill=(222, 255, 255, 255), width=2 * S)
    draw_centered(draw, (14*S,6*S,168*S,42*S), "立即领取", cjk(24 * S), fill=(255, 250, 210, 255), stroke_width=2*S, stroke_fill=(0, 28, 42, 255))
    return image


def prepare_images() -> dict[str, Image.Image]:
    background = crop_cover(Image.open(SOURCE / "background-master.png").convert("RGB"), WIDTH * S, HEIGHT * S, 0.5).convert("RGBA")
    operative, _ = crop_alpha(Image.open(SOURCE / "operative-master.png"), 2)
    target_height = CHARACTER_HEIGHT * S
    target_width = round(operative.width * target_height / operative.height)
    operative = operative.resize((target_width, target_height), Image.Resampling.LANCZOS)
    title, glints = render_title()
    images = {
        "background": background,
        "operative": operative,
        "title": title,
        "kicker": render_kicker(),
        "subtitle": render_subtitle(),
        "cta": render_cta(),
    }
    images.update({f"title_glint_{index}": glint for index, glint in enumerate(glints)})
    return images


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
    used_width = max(left + width + padding for _, left, _, width, _ in placements)
    used_height = max(top + height + padding for _, _, top, _, height in placements)
    atlas_width, atlas_height = next_power(used_width), next_power(used_height)
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
        result = subprocess.run([pngquant, "--force", "--strip", "--speed", "1", "--quality", "72-95", "--output", str(quantized), str(atlas_path)], check=False, capture_output=True)
        if result.returncode == 0 and quantized.exists():
            quantized.replace(atlas_path)
        elif quantized.exists():
            quantized.unlink()
    digest = hashlib.sha256(atlas_path.read_bytes()).hexdigest()[:12]
    lines = [f"banner.png?asset={digest}", f"size: {atlas_width},{atlas_height}", "format: RGBA8888", "filter: Linear,Linear", "repeat: none"]
    for name, left, top, width, height in placements:
        lines += [name, "  rotate: false", f"  xy: {left}, {top}", f"  size: {width}, {height}", f"  orig: {width}, {height}", "  offset: 0, 0", "  index: -1"]
    (RUNTIME / "banner.atlas").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return atlas_width, atlas_height


def region(path: str, width: float, height: float) -> dict[str, object]:
    return {"path": path, "width": round(width, 3), "height": round(height, 3)}


def mesh(image: Image.Image, columns: int = MESH_COLUMNS, rows: int = MESH_ROWS) -> dict[str, object]:
    width, height = image.width / S, image.height / S
    vertices: list[float] = []
    uvs: list[float] = []
    triangles: list[int] = []
    for row in range(rows):
        v = row / (rows - 1)
        for column in range(columns):
            u = column / (columns - 1)
            vertices.extend([round((u - 0.5) * width, 4), round((1 - v) * height, 4)])
            uvs.extend([round(u, 5), round(v, 5)])
    for row in range(rows - 1):
        for column in range(columns - 1):
            a = row * columns + column
            b, c, d = a + 1, a + columns, a + columns + 1
            triangles.extend([a, c, b, b, c, d])
    return {"type": "mesh", "path": "operative", "uvs": uvs, "triangles": triangles, "vertices": vertices, "hull": (columns * 2 + rows * 2 - 4) * 2, "width": round(width, 3), "height": round(height, 3)}


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def rotate_delta(x: float, y: float, pivot_x: float, pivot_y: float, angle: float) -> tuple[float, float]:
    radians = math.radians(angle)
    dx, dy = x - pivot_x, y - pivot_y
    rx = pivot_x + dx * math.cos(radians) - dy * math.sin(radians)
    ry = pivot_y + dx * math.sin(radians) + dy * math.cos(radians)
    return rx - x, ry - y


def idle_deform(image: Image.Image, breath: float, head_angle: float, weapon_angle: float, weight_shift: float, columns: int = MESH_COLUMNS, rows: int = MESH_ROWS) -> list[float]:
    """Subtle human idle: fixed feet, chest breathing, head turn and arm/weapon follow-through."""
    width, height = image.width / S, image.height / S
    offsets: list[float] = []
    for row in range(rows):
        v = row / (rows - 1)
        y = (1 - v) * height
        for column in range(columns):
            u = column / (columns - 1)
            x = (u - 0.5) * width
            foot_lock = clamp((0.94 - v) / 0.14)
            torso = clamp(1 - abs(v - 0.38) / 0.25) * clamp(1 - abs(u - 0.5) / 0.48)
            shoulders = clamp(1 - abs(v - 0.30) / 0.20)
            head = clamp((0.25 - v) / 0.15) * clamp(1 - abs(u - 0.5) / 0.48)
            weapon = clamp(1 - abs(v - 0.46) / 0.22) * clamp(1 - abs(u - 0.54) / 0.52)
            hips = clamp(1 - abs(v - 0.62) / 0.18)

            dx = weight_shift * (0.35 + 0.65 * (1 - v)) * foot_lock
            dy = breath * 2.35 * torso * foot_lock
            dx += (u - 0.5) * breath * 4.6 * torso

            hx, hy = rotate_delta(x, y, 0, height * 0.74, head_angle)
            dx += hx * head
            dy += hy * head
            wx, wy = rotate_delta(x, y, 0, height * 0.58, weapon_angle)
            dx += wx * weapon * shoulders
            dy += wy * weapon * shoulders
            dx -= weight_shift * 0.24 * hips * foot_lock
            offsets.extend([round(dx, 4), round(dy, 4)])
    return offsets


def screen_bone(name: str, x: float, y: float, parent: str = "root") -> dict[str, object]:
    return {"name": name, "parent": parent, "x": round(x - WIDTH / 2, 3), "y": round(HEIGHT / 2 - y, 3)}


def build_skeleton(images: dict[str, Image.Image]) -> dict[str, object]:
    title_width, title_height = images["title"].width / S, images["title"].height / S
    operative_width = images["operative"].width / S
    bones = [
        {"name": "root"},
        {"name": "background", "parent": "root"},
        screen_bone("operative", 498, 271),
        screen_bone("kicker", 164, 14),
        screen_bone("title", 169, 84),
        {"name": "title_glint", "parent": "title"},
        screen_bone("subtitle", 169, 174),
        screen_bone("cta", 169, 228),
    ]
    slots = [
        {"name": "background", "bone": "background", "attachment": "background"},
        {"name": "operative", "bone": "operative", "attachment": "operative"},
        {"name": "kicker", "bone": "kicker", "attachment": "kicker"},
        {"name": "title", "bone": "title", "attachment": "title"},
        {"name": "title_glint", "bone": "title_glint", "attachment": "title_glint_0", "blend": "additive", "color": "ffffff62"},
        {"name": "subtitle", "bone": "subtitle", "attachment": "subtitle"},
        {"name": "cta", "bone": "cta", "attachment": "cta"},
    ]
    attachments = {
        "background": {"background": region("background", WIDTH, HEIGHT)},
        "operative": {"operative": mesh(images["operative"])},
        "kicker": {"kicker": region("kicker", images["kicker"].width / S, images["kicker"].height / S)},
        "title": {"title": region("title", title_width, title_height)},
        "title_glint": {f"title_glint_{index}": region(f"title_glint_{index}", title_width, title_height) for index in range(7)},
        "subtitle": {"subtitle": region("subtitle", images["subtitle"].width / S, images["subtitle"].height / S)},
        "cta": {"cta": region("cta", images["cta"].width / S, images["cta"].height / S)},
    }
    deform_keys = [
        {"vertices": idle_deform(images["operative"], 0.0, 0.0, 0.0, 0.0)},
        {"time": 0.70, "vertices": idle_deform(images["operative"], 1.0, 0.85, -0.45, 1.2)},
        {"time": 1.40, "vertices": idle_deform(images["operative"], 0.0, 0.0, 0.0, 0.0)},
        {"time": 2.10, "vertices": idle_deform(images["operative"], -0.72, -0.65, 0.38, -0.9)},
        {"time": DURATION, "vertices": idle_deform(images["operative"], 0.0, 0.0, 0.0, 0.0)},
    ]
    animation = {
        "slots": {
            "title_glint": {
                "attachment": [
                    {"time": round(0.46 + index * 0.11, 3), "name": f"title_glint_{index}"}
                    for index in range(7)
                ]
            }
        },
        "bones": {
            "operative": {
                "translate": [{}, {"time": 0.70, "x": 1.1, "y": 0.85}, {"time": 1.40}, {"time": 2.10, "x": -0.8, "y": -0.62}, {"time": DURATION}],
                "rotate": [{}, {"time": 0.70, "angle": 0.22}, {"time": 1.40}, {"time": 2.10, "angle": -0.18}, {"time": DURATION}],
            },
            "title": {"translate": [{}, {"time": 0.72, "x": 1}, {"time": 1.4}, {"time": DURATION}]},
            "cta": {"scale": [{}, {"time": 0.72, "x": 1.045, "y": 1.045}, {"time": 1.0}, {"time": 2.10, "x": 1.025, "y": 1.025}, {"time": DURATION}]},
        },
        "deform": {"default": {"operative": {"operative": deform_keys}}},
    }
    return {
        "skeleton": {"hash": "codex-operative-idle-v1", "spine": "3.8.99", "x": -310, "y": -136, "width": WIDTH, "height": HEIGHT, "images": "./images/"},
        "bones": bones,
        "slots": slots,
        "skins": [{"name": "default", "attachments": attachments}],
        "animations": {"animation": animation},
    }


def static_preview(images: dict[str, Image.Image]) -> None:
    preview = images["background"].copy()

    def paste_center(name: str, x: float, y: float, bottom: bool = False) -> None:
        layer = images[name]
        left = round(x * S - layer.width / 2)
        top = round(y * S - layer.height if bottom else y * S - layer.height / 2)
        preview.alpha_composite(layer, (left, top))

    paste_center("operative", 498, 271, bottom=True)
    paste_center("kicker", 164, 14)
    paste_center("title", 169, 84)
    paste_center("subtitle", 169, 174)
    paste_center("cta", 169, 228)
    QA.mkdir(parents=True, exist_ok=True)
    preview.save(QA / "operative-idle-static.png", optimize=True)

    matte = Image.new("RGBA", (preview.width * 2, preview.height), (24, 25, 29, 255))
    matte.alpha_composite(preview, (0, 0))
    white = Image.new("RGBA", preview.size, (238, 238, 238, 255))
    white.alpha_composite(images["operative"], (round(498 * S - images["operative"].width / 2), round(271 * S - images["operative"].height)))
    matte.alpha_composite(white, (preview.width, 0))
    matte.save(QA / "operative-idle-matte.png", optimize=True)


def main() -> None:
    for directory in (IMAGES, RUNTIME, QA):
        directory.mkdir(parents=True, exist_ok=True)
    images = prepare_images()
    for name, image in images.items():
        image.save(IMAGES / f"{name}.png", optimize=True)
    atlas_width, atlas_height = pack(images)
    skeleton = build_skeleton(images)
    (RUNTIME / "banner.json").write_text(json.dumps(skeleton, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    static_preview(images)
    report = {
        "atlas": f"{atlas_width}x{atlas_height}",
        "atlas_bytes": (RUNTIME / "banner.png").stat().st_size,
        "duration": DURATION,
        "mesh_vertices": MESH_COLUMNS * MESH_ROWS,
        "single_continuous_character": True,
        "idle_motion": ["breathing", "weight_shift", "head_turn", "weapon_sway"],
        "background_motion": False,
        "scale_animation": False,
        "portable": True,
    }
    (QA / "build-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "README.md").write_text(
        "# 10 · 王牌特勤\n\n单一连续人物 Mesh 原地待机：呼吸、重心移动、微转头与武器跟随。\n\n完整可搬移 HTML 位于项目根目录 `banners/10-operative-idle/`。\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
